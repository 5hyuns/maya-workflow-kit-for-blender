# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya UV workflow on Blender's UV Editor.

- Opening the UV Editor (Maya UV > UV Editor) enters edit mode with UV Sync Selection on, so the object's UVs show at
  once. Maya's UV / UV Shell components are UVs picked apart from the mesh
  vertices: Blender needs sync off for that (and then draws only the selected faces' UVs, so every face is selected).
- UV Shell = Blender UV island. Blender's island operators group UVs by shared coordinates and ignore seams
  (pack_islands / average_islands_scale), only unwrap reads seams. So Cut = seam + the smaller side moved
  2e-4 off the cut (a real split that still looks in place), Sew = seam cleared + the UVs on the edge joined half-way.
- Unfold = Blender Unwrap (Minimum Stretch) on the chosen shells with their borders kept as seams, each shell put back where
  it was; Layout = Pack Islands with Maya's shell padding in pixels of the map; Texel Density = px per Maya unit.

Code: uv_islands (shells, UV selection), uv_components (UV component mode, UV Editor), uv_projection (Automatic,
Contour Stretch, Cylindrical, Spherical); this module keeps the UV settings, Cut / Sew, Unfold / Layout, Texel Density and their operators,
the classes tuple and re-exports.
"""

import math

import bmesh
import bpy
from bpy.props import BoolProperty, FloatProperty, IntProperty, PointerProperty
from mathutils import Vector

from .. import results
from .. import undo_steps
from . import units
from .uv_islands import (EPS, NUDGE, _edit_meshes, _island_loops, _picked_faces, _same, _uv_area,  # noqa: F401
                         _uv_at, _with_faces, islands, picked_anywhere, selected_edges, selected_faces, sync,
                         target_islands, uv_bounds, uv_centre)
from .uv_components import (COMPONENTS, UV_SELECT_MODES, _MESH_SELECTION, _UV_MODE,  # noqa: F401
                            ALLSET_OT_uv_component, _in_uv_editor, find_uv_editor, forget_mesh_selection,
                            forget_uv_mode, in_uv_mode, leave_uv_mode, mesh_selection_wanted, prepare,
                            remember_mesh_selection, set_component)
from .uv_projection import (AUTOPROJ, PLANE_ITEMS, ALLSET_OT_uv_automatic,  # noqa: F401
                            ALLSET_OT_uv_automatic_edit, ALLSET_OT_uv_contour, ALLSET_OT_uv_cylindrical,
                            ALLSET_OT_uv_spherical, auto_planes, auto_project, fit_unit,
                            note_object_state, object_state_ok)

MAYA_MAP_SIZE = 1024
MAYA_SHELL_PADDING = 2   # px
NOTICE_UNFOLD = "Unfold uses Blender Unwrap (Minimum Stretch), not Unfold3D: shapes can differ from Maya."


class ALLSET_PG_uv(bpy.types.PropertyGroup):
    map_size: IntProperty(name="Map Size", default=MAYA_MAP_SIZE, min=1, soft_max=8192,
                          description="Texture size in pixels for Texel Density and Layout padding")
    texel_density: FloatProperty(name="Texel Density", default=0.0, min=0.0, precision=3,
                                 description="Pixels per Maya unit (px/cm in the Maya Workflow Kit template)")
    shell_padding: FloatProperty(name="Shell Padding", default=MAYA_SHELL_PADDING, min=0.0, soft_max=64.0,
                                 description="Pixels between UV shells (Layout)")


def settings(context):
    return context.scene.allset_uv


def register_props():
    bpy.utils.register_class(ALLSET_PG_uv)
    bpy.types.Scene.allset_uv = PointerProperty(type=ALLSET_PG_uv)


def unregister_props():
    del bpy.types.Scene.allset_uv
    bpy.utils.unregister_class(ALLSET_PG_uv)


# --- Cut / Sew ---------------------------------------------------------------------------------------

def cut(bm, uv, edges):
    """Maya Cut UVs: seams on ``edges``; where that splits a shell, the smaller side moves NUDGE off the cut.
    Returns the number of edges that now separate two shells."""
    for e in edges:
        e.seam = True
    groups = islands(bm, uv, [f for f in bm.faces if not f.hide], seams=True)
    owner = {f: i for i, isl in enumerate(groups) for f in isl}
    moved = set()
    split = 0
    centres = {}      # island -> UV centre, taken before its first nudge (each nudge is NUDGE)
    for e in edges:
        fs = [f for f in e.link_faces if f in owner]
        if len(fs) != 2 or owner[fs[0]] == owner[fs[1]]:
            continue
        split += 1
        small = min(fs, key=lambda f: len(groups[owner[f]]))
        side = owner[small]
        if side not in centres:
            centres[side] = uv_centre(groups[side], uv)
        centre = centres[side]
        for v in e.verts:
            key = (side, v.index)
            if key in moved:
                continue
            moved.add(key)
            c = _uv_at(small, v, uv).copy()
            d = centre - c
            d = d.normalized() * NUDGE if d.length > 1e-9 else Vector((NUDGE, 0.0))
            # the island's loops at v are v's own loops in that island: no scan of the whole island per vertex
            # (that made Cut UV Edges O(edges x island), 36 s on 48 k faces)
            for loop in v.link_loops:
                if owner.get(loop.face) == side and _same(loop[uv].uv, c):
                    loop[uv].uv = c + d
    return split


def weld_edge(e, a, b, uv):
    """Join the two UVs at each end of ``e`` (one from face ``a``, one from face ``b``) half-way; every UV of the
    vertex sitting on either of them follows (they are the same UV). Returns whether a UV moved."""
    moved = False
    for vert in e.verts:
        pa, pb = _uv_at(a, vert, uv).copy(), _uv_at(b, vert, uv).copy()
        if _same(pa, pb):
            continue
        moved = True
        mid = (pa + pb) / 2
        for loop in vert.link_loops:
            if not loop.face.hide and (_same(loop[uv].uv, pa) or _same(loop[uv].uv, pb)):
                loop[uv].uv = mid.copy()
    return moved


def sew(bm, uv, edges, move=False):
    """Maya Sew UVs: clear the seams and join the UVs on each edge, every pair meeting half-way; the shells stay
    where they are. ``move`` (the 3D Cut and Sew tool) first moves (rotates, scales) the smaller shell on the other
    side of an edge onto it. Returns the number of edges sewn."""
    for e in edges:
        e.seam = False
    sewn = 0
    groups = where = None
    for e in edges:
        fs = [f for f in e.link_faces if not f.hide]
        if len(fs) != 2:
            continue
        a, b = fs
        if not move:
            weld_edge(e, a, b, uv)
            sewn += 1
            continue
        if groups is None:     # islands change only when a shell moves onto another (once per edge was
            groups = islands(bm, uv, [f for f in bm.faces if not f.hide])      # O(edges x mesh))
            where = {f: i for i, isl in enumerate(groups) for f in isl}
        v, w = e.verts
        if where[a] == where[b]:
            weld_edge(e, a, b, uv)      # a slit inside one shell: weld the two sides half-way
            sewn += 1
            continue
        big, small = (a, b) if len(groups[where[a]]) >= len(groups[where[b]]) else (b, a)
        p_v, p_w = _uv_at(small, v, uv).copy(), _uv_at(small, w, uv).copy()
        q_v, q_w = _uv_at(big, v, uv).copy(), _uv_at(big, w, uv).copy()
        zp, zq = complex(*(p_w - p_v)), complex(*(q_w - q_v))
        k = zq / zp if abs(zp) > 1e-12 else 1.0
        for loop in _island_loops(groups[where[small]]):
            z = complex(*(loop[uv].uv - p_v)) * k
            loop[uv].uv = q_v + Vector((z.real, z.imag))
        moved_shell = set(groups[where[small]])
        for vert, q in ((v, q_v), (w, q_w)):
            for loop in vert.link_loops:
                if loop.face in moved_shell and (loop[uv].uv - q).length < 1e-4:
                    loop[uv].uv = q.copy()
        groups = None          # the two shells are one now
        sewn += 1
    return sewn


# --- Unfold / Layout (Blender operators with the selection set up) -----------------------------------

def mark_shell_borders(bm, uv, faces):
    """Seams on the borders of the shells of ``faces`` and on the cuts inside a shell (an edge whose two faces have
    different UVs there): an unwrap keeps all of them apart."""
    where = {f: i for i, isl in enumerate(islands(bm, uv, [f for f in bm.faces if not f.hide])) for f in isl}
    fs = set(faces)
    for e in {e for f in faces for e in f.edges}:
        linked = [f for f in e.link_faces if not f.hide]
        if len(linked) != 2:
            continue
        a, b = linked
        if where[a] != where[b] or (a in fs) != (b in fs) or \
                not all(_same(_uv_at(a, v, uv), _uv_at(b, v, uv)) for v in e.verts):
            e.seam = True


def unfold(context, ob, fallback=True):
    """Maya Unfold on the target shells of ``ob``: Blender Unwrap (Minimum Stretch), each shell back in its place."""
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.verify()
    bm.faces.index_update()
    shells = target_islands(bm, uv, sync(context), fallback=fallback)
    if not shells:
        return 0
    faces = [f for isl in shells for f in isl]
    mark_shell_borders(bm, uv, faces)
    # Maya Unfold (Unfold3D) keeps each shell's UV area and the mean of its UVs
    # (Unfold); its solver turn can't be reproduced, Blender's unwrap orientation stays.
    before = [([f.index for f in isl], _point_mean(isl, uv), sum(_uv_area(f, uv) for f in isl)) for isl in shells]
    bmesh.update_edit_mesh(ob.data)
    _with_faces(context, ob, faces, lambda: bpy.ops.uv.unwrap(method='MINIMUM_STRETCH', margin=0.0))
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.verify()
    bm.faces.ensure_lookup_table()
    # one factor for all unfolded shells: Maya's rule keeps the *total* area (one-shell cases), and a common
    # factor keeps the even texel density Blender's unwrap gives the shells (sweep M66-3: Unfold then Layout)
    area = sum(a for _i, _m, a in before)
    now = sum(_uv_area(bm.faces[i], uv) for idx, _m, _a in before for i in idx)
    k = math.sqrt(area / now) if now > 1e-12 and area > 1e-12 else 1.0
    for idx, mean, _area in before:
        isl = [bm.faces[i] for i in idx]
        c = _point_mean(isl, uv)
        for loop in _island_loops(isl):
            loop[uv].uv = mean + (loop[uv].uv - c) * k
    bmesh.update_edit_mesh(ob.data)
    return len(shells)


def _point_mean(island, uv):
    """Mean of the shell's UV positions, each UV (vertex + coordinate) once. A vertex's UVs are compared only
    with that vertex's own UVs: comparing with every UV of the shell froze Blender for minutes on dense shells."""
    by_vert = {}
    total = Vector((0.0, 0.0))
    n = 0
    for loop in _island_loops(island):
        p = loop[uv].uv
        seen = by_vert.setdefault(loop.vert, [])
        if not any(_same(q, p) for q in seen):
            q = p.copy()
            seen.append(q)
            total += q
            n += 1
    return total / max(n, 1)


def layout(context, ob, padding_px, map_size, fallback=True):
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.verify()
    shells = target_islands(bm, uv, sync(context), fallback=fallback)
    if not shells:
        return 0
    faces = [f for isl in shells for f in isl]
    margin = padding_px / max(map_size, 1)
    _with_faces(context, ob, faces, lambda: bpy.ops.uv.pack_islands(
        rotate=True, margin_method='FRACTION', margin=margin))
    return len(shells)


# --- Texel Density -----------------------------------------------------------------------------------

def _world_area(face, mw):
    pts = [mw @ v.co for v in face.verts]
    area = Vector()
    for i in range(1, len(pts) - 1):
        area += (pts[i] - pts[0]).cross(pts[i + 1] - pts[0])
    return area.length / 2


def density(faces, uv, mw, map_size, unit):
    """Pixels per Maya unit of ``faces``: sqrt(UV area * map^2 / world area in Maya units^2)."""
    uva = sum(_uv_area(f, uv) for f in faces)
    wa = sum(_world_area(f, mw) for f in faces) / (unit * unit)
    return math.sqrt(uva * map_size * map_size / wa) if wa > 1e-12 and uva > 0 else 0.0


def scale_island(island, uv, factor):
    c = uv_centre(island, uv)
    for loop in _island_loops(island):
        loop[uv].uv = c + (loop[uv].uv - c) * factor


# --- operators ---------------------------------------------------------------------------------------

def _uv_poll(context):
    return context.mode == 'EDIT_MESH'


@undo_steps.no_redo_panel      # no Adjust Last Operation (Maya has none)
class ALLSET_OT_uv_cut(bpy.types.Operator):
    """Cut the UVs along the selected edges (Maya Cut UV Edges): a seam, and the shells separate in place"""
    bl_idname = "allset.uv_cut"
    bl_label = "Cut UV Edges"
    bl_options = {'REGISTER', 'UNDO'}

    # 3D Cut and Sew tool x: the edges selected in the 3D View, whatever the UV sync setting
    mesh_select: BoolProperty(name="3D View Edges", default=False, options={'SKIP_SAVE'})

    poll = classmethod(lambda cls, context: _uv_poll(context))

    def execute(self, context):
        done = 0
        mesh = self.mesh_select or mesh_selection_wanted(context)
        for ob in _edit_meshes(context):
            bm = bmesh.from_edit_mesh(ob.data)
            uv = bm.loops.layers.uv.verify()
            edges = selected_edges(bm, uv, mesh)
            if edges:
                cut(bm, uv, edges)
                bmesh.update_edit_mesh(ob.data)
                done += len(edges)
        if not done:
            self.report({'WARNING'}, "Select edges to cut")
            return {'CANCELLED'}
        return {'FINISHED'}


@undo_steps.no_redo_panel      # no Adjust Last Operation (Maya has none)
class ALLSET_OT_uv_sew(bpy.types.Operator):
    """Sew the UVs along the selected edges (Maya Sew UV Edges): the UVs on each edge meet half-way"""
    bl_idname = "allset.uv_sew"
    bl_label = "Sew UV Edges"
    bl_options = {'REGISTER', 'UNDO'}

    mesh_select: BoolProperty(name="3D View Edges", default=False, options={'SKIP_SAVE'})   # 3D Cut and Sew tool

    poll = classmethod(lambda cls, context: _uv_poll(context))

    def execute(self, context):
        done = 0
        mesh = self.mesh_select or mesh_selection_wanted(context)
        for ob in _edit_meshes(context):
            bm = bmesh.from_edit_mesh(ob.data)
            uv = bm.loops.layers.uv.verify()
            edges = selected_edges(bm, uv, mesh)
            if edges:
                done += sew(bm, uv, edges, move=self.mesh_select)
                bmesh.update_edit_mesh(ob.data)
        if not done:
            self.report({'WARNING'}, "Select edges between UV shells to sew")
            return {'CANCELLED'}
        return {'FINISHED'}


class ALLSET_OT_uv_unfold(bpy.types.Operator):
    """Unfold the selected UV shells (all when none are selected), keeping their borders and places
    (Maya Unfold; Blender Unwrap, Minimum Stretch)"""
    bl_idname = "allset.uv_unfold"
    bl_label = "Unfold"
    bl_options = {'REGISTER', 'UNDO'}

    poll = classmethod(lambda cls, context: _uv_poll(context))

    def execute(self, context):
        fb = not picked_anywhere(context)
        n = sum(unfold(context, ob, fb) for ob in _edit_meshes(context))
        if not n:
            return {'CANCELLED'}
        results.result(self, NOTICE_UNFOLD)
        return {'FINISHED'}


@undo_steps.no_redo_panel      # no Adjust Last Operation (Maya has none)
class ALLSET_OT_uv_layout(bpy.types.Operator):
    """Lay the selected UV shells (all when none are selected) out in 0-1 (Maya Layout; Blender Pack Islands)"""
    bl_idname = "allset.uv_layout"
    bl_label = "Layout"
    bl_options = {'REGISTER', 'UNDO'}

    shell_padding: FloatProperty(name="Shell Padding (px)", default=MAYA_SHELL_PADDING, min=0.0, soft_max=64.0)
    map_size: IntProperty(name="Map Size", default=MAYA_MAP_SIZE, min=1)

    poll = classmethod(lambda cls, context: _uv_poll(context))

    def invoke(self, context, event):
        s = settings(context)
        self.shell_padding, self.map_size = s.shell_padding, s.map_size
        return self.execute(context)

    def execute(self, context):
        fb = not picked_anywhere(context)
        n = sum(layout(context, ob, self.shell_padding, self.map_size, fb) for ob in _edit_meshes(context))
        return {'FINISHED'} if n else {'CANCELLED'}


class ALLSET_OT_uv_texel_get(bpy.types.Operator):
    """Measure the texel density of the selected UV shells (all when none are selected): pixels per Maya unit"""
    bl_idname = "allset.uv_texel_get"
    bl_label = "Get Texel Density"
    bl_options = {'REGISTER', 'INTERNAL'}

    poll = classmethod(lambda cls, context: _uv_poll(context))

    def execute(self, context):
        s = settings(context)
        unit = units.maya_unit(context.scene)
        uva = wa = 0.0
        fb = not picked_anywhere(context)
        for ob in _edit_meshes(context):
            bm = bmesh.from_edit_mesh(ob.data)
            uv = bm.loops.layers.uv.verify()
            faces = [f for isl in target_islands(bm, uv, sync(context), fb) for f in isl]
            uva += sum(_uv_area(f, uv) for f in faces)
            wa += sum(_world_area(f, ob.matrix_world) for f in faces) / (unit * unit)
        if wa <= 1e-12:
            return {'CANCELLED'}
        s.texel_density = math.sqrt(uva * s.map_size ** 2 / wa)
        results.result(self, f"Texel density {s.texel_density:.3f} px per unit (map {s.map_size})")
        return {'FINISHED'}


class ALLSET_OT_uv_texel_set(bpy.types.Operator):
    """Scale the selected UV shells (all when none are selected) to the texel density (pixels per Maya unit)"""
    bl_idname = "allset.uv_texel_set"
    bl_label = "Set Texel Density"
    bl_options = {'REGISTER', 'UNDO'}

    poll = classmethod(lambda cls, context: _uv_poll(context))

    def execute(self, context):
        s = settings(context)
        if s.texel_density <= 0:
            self.report({'WARNING'}, "Get a texel density first (or type one)")
            return {'CANCELLED'}
        unit = units.maya_unit(context.scene)
        done = 0
        fb = not picked_anywhere(context)
        for ob in _edit_meshes(context):
            bm = bmesh.from_edit_mesh(ob.data)
            uv = bm.loops.layers.uv.verify()
            for isl in target_islands(bm, uv, sync(context), fb):
                d = density(isl, uv, ob.matrix_world, s.map_size, unit)
                if d > 0:
                    scale_island(isl, uv, s.texel_density / d)
                    done += 1
            bmesh.update_edit_mesh(ob.data)
        return {'FINISHED'} if done else {'CANCELLED'}


classes = (ALLSET_OT_uv_cut, ALLSET_OT_uv_sew, ALLSET_OT_uv_unfold, ALLSET_OT_uv_layout, ALLSET_OT_uv_texel_get,
           ALLSET_OT_uv_texel_set, ALLSET_OT_uv_component, ALLSET_OT_uv_automatic, ALLSET_OT_uv_automatic_edit,
           ALLSET_OT_uv_contour, ALLSET_OT_uv_cylindrical, ALLSET_OT_uv_spherical)
