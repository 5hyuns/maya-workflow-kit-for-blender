# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya UV workflow on Blender's UV Editor.

- Opening the UV Editor (Maya UV > UV Editor) enters edit mode with UV Sync Selection on, so the object's UVs show at once
  (, :60-63). Maya's UV / UV Shell components are UVs picked apart from the mesh
  vertices: Blender needs sync off for that (and then draws only the selected faces' UVs, so every face is selected).
- UV Shell = Blender UV island (uv.md:130). Blender's island operators group UVs by shared coordinates and ignore seams
  (checked, step 66: pack_islands / average_islands_scale), only unwrap reads seams. So Cut = seam + the smaller side moved
  2e-4 off the cut (a real split that still looks in place), Sew = seam cleared + the smaller shell moved onto the edge.
- Unfold = Blender Unwrap (Minimum Stretch) on the chosen shells with their borders kept as seams, each shell put back where
  it was; Layout = Pack Islands with Maya's shell padding in pixels of the map; Texel Density = px per Maya unit (uv.md:141-142).
"""

import math

import bmesh
import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, IntProperty, PointerProperty
from mathutils import Vector

from . import units

EPS = 1e-5           # UVs closer than this are one UV
NUDGE = 2e-4         # how far Cut moves the smaller side (0.2 px on a 1024 map)
MAYA_MAP_SIZE = 1024
MAYA_SHELL_PADDING = 2   # px  (uv.md:140)
NOTICE_UNFOLD = "Unfold uses Blender Unwrap (Minimum Stretch), not Unfold3D: shapes can differ from Maya."


class ALLSET_PG_uv(bpy.types.PropertyGroup):
    map_size: IntProperty(name="Map Size", default=MAYA_MAP_SIZE, min=1, soft_max=8192,
                          description="Texture size in pixels for Texel Density and Layout padding")
    texel_density: FloatProperty(name="Texel Density", default=0.0, min=0.0, precision=3,
                                 description="Pixels per Maya unit (px/cm in the Allset template)")
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


# --- selection and islands (bmesh) ------------------------------------------------------------------

def _same(a, b):
    return abs(a.x - b.x) <= EPS and abs(a.y - b.y) <= EPS


def _uv_at(face, vert, uv):
    for loop in face.loops:
        if loop.vert is vert:
            return loop[uv].uv
    return None


def islands(bm, uv, faces=None, seams=False):
    """Lists of faces that share UVs across their edges (Blender's islands; ``seams``: a seam also splits)."""
    faces = list(bm.faces if faces is None else faces)
    index = {f: i for i, f in enumerate(faces)}
    parent = list(range(len(faces)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for e in {e for f in faces for e in f.edges}:
        if seams and e.seam:
            continue
        fs = [f for f in e.link_faces if f in index]
        for i in range(1, len(fs)):
            a, b = fs[0], fs[i]
            if all(_same(_uv_at(a, v, uv), _uv_at(b, v, uv)) for v in e.verts):
                ra, rb = find(index[a]), find(index[b])
                if ra != rb:
                    parent[rb] = ra
    groups = {}
    for f, i in index.items():
        groups.setdefault(find(i), []).append(f)
    return list(groups.values())


def sync(context):
    return context.scene.tool_settings.use_uv_select_sync


def selected_faces(bm, uv, synced):
    if synced:
        return [f for f in bm.faces if f.select and not f.hide]
    return [f for f in bm.faces if f.select and not f.hide and all(l[uv].select for l in f.loops)]


def selected_edges(bm, uv, synced):
    if synced:
        return [e for e in bm.edges if e.select and not e.hide]
    out = set()
    for f in bm.faces:
        if f.hide or not f.select:
            continue
        for loop in f.loops:
            if loop[uv].select_edge:
                out.add(loop.edge)
    return list(out)


def target_islands(bm, uv, synced):
    """Shells touched by the selection (faces, else any selected UV), or every shell."""
    every = islands(bm, uv, [f for f in bm.faces if not f.hide])
    if synced:
        picked = {f for f in bm.faces if f.select}
    else:
        picked = {f for f in bm.faces if f.select and any(l[uv].select for l in f.loops)}
    chosen = [isl for isl in every if picked & set(isl)]
    return chosen or every


def _island_loops(island):
    return [loop for f in island for loop in f.loops]


def uv_centre(island, uv):
    loops = _island_loops(island)
    return sum((l[uv].uv for l in loops), Vector((0.0, 0.0))) / max(len(loops), 1)


def uv_bounds(island, uv):
    us = [l[uv].uv for l in _island_loops(island)]
    lo = Vector((min(u.x for u in us), min(u.y for u in us)))
    hi = Vector((max(u.x for u in us), max(u.y for u in us)))
    return lo, hi


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
    for e in edges:
        fs = [f for f in e.link_faces if f in owner]
        if len(fs) != 2 or owner[fs[0]] == owner[fs[1]]:
            continue
        split += 1
        small = min(fs, key=lambda f: len(groups[owner[f]]))
        isl = groups[owner[small]]
        centre = uv_centre(isl, uv)
        for v in e.verts:
            key = (owner[small], v.index)
            if key in moved:
                continue
            moved.add(key)
            c = _uv_at(small, v, uv).copy()
            d = centre - c
            d = d.normalized() * NUDGE if d.length > 1e-9 else Vector((NUDGE, 0.0))
            for loop in _island_loops(isl):
                if loop.vert is v and _same(loop[uv].uv, c):
                    loop[uv].uv = c + d
    return split


def sew(bm, uv, edges):
    """Maya Sew UVs: clear the seams; a shell on the other side of an edge is moved (rotated, scaled) onto it,
    the smaller shell onto the bigger one. Returns the number of edges sewn."""
    for e in edges:
        e.seam = False
    sewn = 0
    for e in edges:
        fs = [f for f in e.link_faces if not f.hide]
        if len(fs) != 2:
            continue
        groups = islands(bm, uv, [f for f in bm.faces if not f.hide])
        where = {f: i for i, isl in enumerate(groups) for f in isl}
        a, b = fs
        v, w = e.verts
        if where[a] == where[b]:
            shell = set(groups[where[a]])
            for vert in (v, w):     # a slit inside one shell: weld the two sides half-way
                pa, pb = _uv_at(a, vert, uv).copy(), _uv_at(b, vert, uv).copy()
                mid = (pa + pb) / 2
                for loop in vert.link_loops:
                    if loop.face in shell and (_same(loop[uv].uv, pa) or _same(loop[uv].uv, pb)):
                        loop[uv].uv = mid.copy()
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
        for vert, q in ((v, q_v), (w, q_w)):
            for loop in vert.link_loops:
                if loop.face in set(groups[where[small]]) and (loop[uv].uv - q).length < 1e-4:
                    loop[uv].uv = q.copy()
        sewn += 1
    return sewn


# --- Unfold / Layout (Blender operators with the selection set up) -----------------------------------

def _with_faces(context, ob, faces, call):
    """Run ``call`` with UV sync on and exactly ``faces`` selected (Blender's unwrap / pack use that), then put the
    selection and sync back."""
    ts = context.scene.tool_settings
    bm = bmesh.from_edit_mesh(ob.data)
    old_sync = ts.use_uv_select_sync
    for seq in (bm.verts, bm.edges, bm.faces):
        seq.index_update()
    old = [[el.index for el in seq if el.select] for seq in (bm.verts, bm.edges, bm.faces)]
    old_mode = tuple(ts.mesh_select_mode)
    want = {f.index for f in faces}
    ts.use_uv_select_sync = True
    for f in bm.faces:
        f.select_set(False)
    for f in bm.faces:
        if f.index in want:
            f.select_set(True)
    bmesh.update_edit_mesh(ob.data)
    try:
        return call()
    finally:
        bm = bmesh.from_edit_mesh(ob.data)
        for seq, keep in zip((bm.verts, bm.edges, bm.faces), old):
            seq.ensure_lookup_table()
            for el in seq:
                el.select = False
            for i in keep:
                if i < len(seq):
                    seq[i].select = True
        ts.mesh_select_mode = old_mode
        ts.use_uv_select_sync = old_sync
        bmesh.update_edit_mesh(ob.data)


def mark_shell_borders(bm, uv, faces):
    """Seams on the borders of the shells of ``faces`` (keeps them apart through an unwrap)."""
    where = {f: i for i, isl in enumerate(islands(bm, uv, [f for f in bm.faces if not f.hide])) for f in isl}
    fs = set(faces)
    for e in {e for f in faces for e in f.edges}:
        linked = [f for f in e.link_faces if not f.hide]
        if len(linked) == 2 and (where[linked[0]] != where[linked[1]] or (linked[0] in fs) != (linked[1] in fs)):
            e.seam = True


def unfold(context, ob):
    """Maya Unfold on the target shells of ``ob``: Blender Unwrap (Minimum Stretch), each shell back in its place."""
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.verify()
    bm.faces.index_update()
    shells = target_islands(bm, uv, sync(context))
    faces = [f for isl in shells for f in isl]
    mark_shell_borders(bm, uv, faces)
    before = [([f.index for f in isl], sum(uv_bounds(isl, uv), Vector((0, 0))) / 2) for isl in shells]
    bmesh.update_edit_mesh(ob.data)
    _with_faces(context, ob, faces, lambda: bpy.ops.uv.unwrap(method='MINIMUM_STRETCH', margin=0.0))
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.verify()
    bm.faces.ensure_lookup_table()
    for idx, centre in before:
        isl = [bm.faces[i] for i in idx]
        lo, hi = uv_bounds(isl, uv)
        d = centre - (lo + hi) / 2
        for loop in _island_loops(isl):
            loop[uv].uv = loop[uv].uv + d
    bmesh.update_edit_mesh(ob.data)
    return len(shells)


def layout(context, ob, padding_px, map_size):
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.verify()
    shells = target_islands(bm, uv, sync(context))
    faces = [f for isl in shells for f in isl]
    margin = padding_px / max(map_size, 1)
    _with_faces(context, ob, faces, lambda: bpy.ops.uv.pack_islands(
        rotate=True, margin_method='FRACTION', margin=margin))
    return len(shells)


# --- Texel Density -----------------------------------------------------------------------------------

def _uv_area(face, uv):
    pts = [l[uv].uv for l in face.loops]
    return abs(sum(pts[i].x * pts[i - 1].y - pts[i - 1].x * pts[i].y for i in range(len(pts)))) / 2


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


def _edit_meshes(context):
    return [o for o in getattr(context, "objects_in_mode_unique_data", ()) if o.type == 'MESH']


# --- operators ---------------------------------------------------------------------------------------

def _uv_poll(context):
    return context.mode == 'EDIT_MESH'


class ALLSET_OT_uv_cut(bpy.types.Operator):
    """Cut the UVs along the selected edges (Maya Cut UV Edges): a seam, and the shells separate in place"""
    bl_idname = "allset.uv_cut"
    bl_label = "Cut UV Edges"
    bl_options = {'REGISTER', 'UNDO'}

    # 3D Cut and Sew tool x (step 79): the edges selected in the 3D View, whatever the UV sync setting
    mesh_select: BoolProperty(name="3D View Edges", default=False, options={'SKIP_SAVE'})

    poll = classmethod(lambda cls, context: _uv_poll(context))

    def execute(self, context):
        done = 0
        for ob in _edit_meshes(context):
            bm = bmesh.from_edit_mesh(ob.data)
            uv = bm.loops.layers.uv.verify()
            edges = selected_edges(bm, uv, sync(context) or self.mesh_select)
            if edges:
                cut(bm, uv, edges)
                bmesh.update_edit_mesh(ob.data)
                done += len(edges)
        if not done:
            self.report({'WARNING'}, "Select edges to cut")
            return {'CANCELLED'}
        return {'FINISHED'}


class ALLSET_OT_uv_sew(bpy.types.Operator):
    """Sew the UVs along the selected edges (Maya Sew UV Edges): the smaller shell moves onto the bigger one"""
    bl_idname = "allset.uv_sew"
    bl_label = "Sew UV Edges"
    bl_options = {'REGISTER', 'UNDO'}

    mesh_select: BoolProperty(name="3D View Edges", default=False, options={'SKIP_SAVE'})   # step 79 tool s

    poll = classmethod(lambda cls, context: _uv_poll(context))

    def execute(self, context):
        done = 0
        for ob in _edit_meshes(context):
            bm = bmesh.from_edit_mesh(ob.data)
            uv = bm.loops.layers.uv.verify()
            edges = selected_edges(bm, uv, sync(context) or self.mesh_select)
            if edges:
                done += sew(bm, uv, edges)
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
        n = sum(unfold(context, ob) for ob in _edit_meshes(context))
        if not n:
            return {'CANCELLED'}
        self.report({'INFO'}, NOTICE_UNFOLD)
        return {'FINISHED'}


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
        n = sum(layout(context, ob, self.shell_padding, self.map_size) for ob in _edit_meshes(context))
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
        for ob in _edit_meshes(context):
            bm = bmesh.from_edit_mesh(ob.data)
            uv = bm.loops.layers.uv.verify()
            faces = [f for isl in target_islands(bm, uv, sync(context)) for f in isl]
            uva += sum(_uv_area(f, uv) for f in faces)
            wa += sum(_world_area(f, ob.matrix_world) for f in faces) / (unit * unit)
        if wa <= 1e-12:
            return {'CANCELLED'}
        s.texel_density = math.sqrt(uva * s.map_size ** 2 / wa)
        self.report({'INFO'}, f"Texel density {s.texel_density:.3f} px per unit (map {s.map_size})")
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
        for ob in _edit_meshes(context):
            bm = bmesh.from_edit_mesh(ob.data)
            uv = bm.loops.layers.uv.verify()
            for isl in target_islands(bm, uv, sync(context)):
                d = density(isl, uv, ob.matrix_world, s.map_size, unit)
                if d > 0:
                    scale_island(isl, uv, s.texel_density / d)
                    done += 1
            bmesh.update_edit_mesh(ob.data)
        return {'FINISHED'} if done else {'CANCELLED'}


# --- UV Editor and UV components --------------------------------------------------------------------

COMPONENTS = (('VERTEX', "Vertex", "Mesh vertices (UV Sync Selection on)"),
              ('EDGE', "Edge", "Mesh edges (UV Sync Selection on)"),
              ('FACE', "Face", "Mesh faces (UV Sync Selection on)"),
              ('UV', "UV", "UVs picked apart from the mesh (UV Sync Selection off)"),
              ('SHELL', "UV Shell", "Whole UV shells = Blender UV islands (UV Sync Selection off)"),
              ('OPEN', "Open", "Only open the UV Editor"))


def find_uv_editor(context):
    for win in context.window_manager.windows:
        for area in win.screen.areas:
            if area.ui_type == 'UV':
                return win, area
    return None, None


def prepare(context):
    """Edit mode on the active mesh with UV Sync Selection on (the UVs show in the UV Editor at once)."""
    ob = context.view_layer.objects.active
    if ob is None or ob.type != 'MESH':
        return False
    if ob.mode != 'EDIT':
        if not ob.select_get():
            ob.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
    context.scene.tool_settings.use_uv_select_sync = True
    return True


def set_component(context, mode):
    ts = context.scene.tool_settings
    if mode in ('VERTEX', 'EDGE', 'FACE'):
        ts.use_uv_select_sync = True
        ts.mesh_select_mode = (mode == 'VERTEX', mode == 'EDGE', mode == 'FACE')
    elif mode in ('UV', 'SHELL'):
        ts.use_uv_select_sync = False
        ts.uv_select_mode = 'ISLAND' if mode == 'SHELL' else 'VERTEX'
        # without sync Blender draws only the selected faces' UVs: Maya shows them all
        for ob in _edit_meshes(context):
            bm = bmesh.from_edit_mesh(ob.data)
            for f in bm.faces:
                if not f.hide:
                    f.select_set(True)
            bmesh.update_edit_mesh(ob.data)


class ALLSET_OT_uv_component(bpy.types.Operator):
    """Maya UV components: open the UV Editor (once) and pick Vertex / Edge / Face / UV / UV Shell there.
    Blender picks UVs in the UV Editor only"""
    bl_idname = "allset.uv_component"
    bl_label = "UV Component"
    bl_options = {'REGISTER', 'UNDO'}

    mode: EnumProperty(items=COMPONENTS, name="Component", default='UV')

    @classmethod
    def poll(cls, context):
        ob = context.view_layer.objects.active if context.view_layer else None
        target = getattr(context.window_manager, "allset_mm_target", "")
        return (ob is not None and ob.type == 'MESH') or bool(target)

    def execute(self, context):
        target = bpy.data.objects.get(getattr(context.window_manager, "allset_mm_target", "") or "")
        if target is not None and target.type == 'MESH' and context.mode == 'OBJECT':
            for o in context.selected_objects:
                if o is not target:
                    o.select_set(False)
            target.select_set(True)
            context.view_layer.objects.active = target
        if not prepare(context):
            self.report({'WARNING'}, "Select a mesh")
            return {'CANCELLED'}
        if self.mode != 'OPEN':
            set_component(context, self.mode)
        if find_uv_editor(context)[1] is None and context.window is not None and not bpy.app.background:
            bpy.ops.allset.open_editor(ui_type='UV')
        return {'FINISHED'}


classes = (ALLSET_OT_uv_cut, ALLSET_OT_uv_sew, ALLSET_OT_uv_unfold, ALLSET_OT_uv_layout, ALLSET_OT_uv_texel_get,
           ALLSET_OT_uv_texel_set, ALLSET_OT_uv_component)
