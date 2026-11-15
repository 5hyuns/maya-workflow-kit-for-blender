# SPDX-License-Identifier: GPL-3.0-or-later
"""UV projections: Maya UV > Automatic (``auto_project``: plane choice, shells and their packed layout, with
operators/autoproj_layout.py; ``allset.uv_automatic``) and its editable polyAutoProj node (the ``AUTOPROJ`` spec of
operators/extrude_spec.py, ``allset.uv_automatic_edit``), and UV > Contour Stretch (``allset.uv_contour``: Follow Active
Quads, then 0-1). From object mode both act on every face of the selected meshes (``_ObjectFaces``).
"""

import math

import bmesh
import bpy
from bpy.props import EnumProperty, FloatProperty, IntProperty
from mathutils import Vector

from .. import undo_steps
from . import units
from .uv_islands import _with_faces


# --- Automatic / Contour Stretch -------------------

def auto_planes(count):
    """Projection directions of Maya's Automatic mapping (object space). 3 and 6 = the six axis planes (Maya 3 planes
    also gives 6 shells on a cube / sphere); 4 / 8 / 12 = tetrahedron / octahedron / dodecahedron faces,
    5 = top, bottom and three around (a kit choice). Order = Maya X, Y, Z (Blender X, Z, -Y):
    a face that ties goes to the earlier plane (a Maya cylinder's 45-degree sides go to X)."""
    count = int(count)
    if count in (3, 6):
        return [Vector(d) for d in ((1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1), (0, -1, 0), (0, 1, 0))]
    if count == 4:
        return [Vector(d).normalized() for d in ((1, 1, 1), (1, -1, -1), (-1, 1, -1), (-1, -1, 1))]
    if count == 5:
        ring = [Vector((math.cos(a), math.sin(a), 0.0)) for a in (0.0, 2 * math.pi / 3, 4 * math.pi / 3)]
        return [Vector((0, 0, 1)), Vector((0, 0, -1))] + ring
    if count == 8:
        return [Vector((x, y, z)).normalized() for x in (1, -1) for z in (1, -1) for y in (-1, 1)]
    g = (1 + math.sqrt(5)) / 2       # 12: icosahedron vertices = dodecahedron face normals
    dirs = []
    for a, b in ((1, g), (-1, g), (1, -g), (-1, -g)):
        dirs += [Vector((0, a, b)), Vector((a, b, 0)), Vector((b, 0, a))]
    return [d.normalized() for d in dirs]


def _basis(d):
    """(U, V) of a projection plane seen from outside along ``-d``: V = up (Blender Z, Y for the top / bottom)."""
    up = Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((0, 1, 0)) * (1 if d.z > 0 else -1)
    u = (-d).cross(up).normalized()
    return u, d.cross(u).normalized()


def _maya_shells(faces, k_unit, optimize=True):
    """6 planes: Maya's own plane choice and shells (autoproj_layout.assign_planes, Fewer pieces on = the default),
    fed with the faces in index order and the points in Maya axes and units (Blender (x, y, z) =
    Maya (x, -z, y)). Returns ``[(projector, faces)]``; a projector maps a Blender point to the plane's (u, v)."""
    from . import autoproj_layout
    faces = sorted(faces, key=lambda f: f.index)
    ids = {}
    for f in faces:
        for v in f.verts:
            ids.setdefault(v, len(ids))
    points = [(v.co.x * k_unit, v.co.z * k_unit, -v.co.y * k_unit) for v in ids]
    shells = autoproj_layout.assign_planes(points, [[ids[v] for v in f.verts] for f in faces], optimize=optimize)
    out = []
    for plane, group in shells:
        _n, mu, mv = autoproj_layout.PLANES6[plane]
        # Maya (x, y, z) of a Blender point = (x, z, -y): the frame vectors in Blender axes
        u = Vector((mu[0], -mu[2], mu[1])) * k_unit
        v = Vector((mv[0], -mv[2], mv[1])) * k_unit
        out.append(((lambda co, u=u, v=v: (co.dot(u), co.dot(v))), [faces[i] for i in group]))
    return out


def auto_project(bm, uv, faces, planes=6, spacing=0.2, unit=1.0, optimize=True):
    """Maya polyAutoProjection on ``faces`` (object space, -ws 0) with the default options: 6 planes assign faces
    and build shells Maya's way (``_maya_shells``: candidate planes within 60 degrees, seeds by fewest candidates,
    flood fill that stops where a shell would overlap itself); other
    plane counts give every face the plane its normal faces most. Shells are laid out in 0-1 at one scale with
    ``spacing`` percent between them (default 0.2 %) by Maya's packed "Into square"
    layout (operators/autoproj_layout.py). ``unit`` = Blender length of one Maya unit
    (``units.maya_unit``): Maya projects and packs in Maya units. Returns the shell count."""
    from . import autoproj_layout
    faces = [f for f in faces if not f.hide]
    k_unit = 1.0 / (unit or 1.0)
    if int(planes) == 6:
        shells = _maya_shells(faces, k_unit, optimize)
        # Maya's shell order for the layout = ascending lowest face index
        shells.sort(key=lambda s: min(f.index for f in s[1]))
        flat = [{lp: proj(lp.vert.co) for g in group for lp in g.loops} for proj, group in shells]
        if not flat:
            return 0
        lay = autoproj_layout.layout([autoproj_layout.bbox_of(pts.values()) for pts in flat], max(0.0, spacing))
        for i, pts in enumerate(flat):
            for lp, (x, y) in pts.items():
                lp[uv].uv = lay.transform(i, x, y)
        return len(flat)
    dirs = auto_planes(planes)
    which = {}
    for f in faces:
        dots = [f.normal.dot(d) for d in dirs]
        top = max(dots)
        which[f] = next(i for i, x in enumerate(dots) if x >= top - 1e-6)
    seen, shells = set(), []
    # Maya's shell order = ascending lowest face index (faces visited in index order)
    for f in sorted(faces, key=lambda f: f.index):
        if f in seen:
            continue
        seen.add(f)
        group, todo = [], [f]
        while todo:
            g = todo.pop()
            group.append(g)
            for e in g.edges:
                for n in e.link_faces:
                    if n not in seen and n in which and which[n] == which[f]:
                        seen.add(n)
                        todo.append(n)
        shells.append((which[f], group))
    flat = []
    for k, group in shells:
        u, v = _basis(dirs[k])
        flat.append({lp: (lp.vert.co.dot(u) * k_unit, lp.vert.co.dot(v) * k_unit) for g in group for lp in g.loops})
    if not flat:
        return 0
    lay = autoproj_layout.layout([autoproj_layout.bbox_of(pts.values()) for pts in flat], max(0.0, spacing))
    for i, pts in enumerate(flat):
        for lp, (x, y) in pts.items():
            lp[uv].uv = lay.transform(i, x, y)
    return len(shells)


def fit_unit(loops, uv):
    """Stretch the UVs of ``loops`` to fill 0-1 (Maya Contour Stretch: a strip of faces fills the square)."""
    pts = [lp[uv].uv.copy() for lp in loops]
    if not pts:
        return
    x0, y0 = min(p.x for p in pts), min(p.y for p in pts)
    w = (max(p.x for p in pts) - x0) or 1.0
    h = (max(p.y for p in pts) - y0) or 1.0
    for lp, p in zip(loops, pts):
        lp[uv].uv = ((p.x - x0) / w, (p.y - y0) / h)


class _ObjectFaces:
    """From object mode: the selected meshes in edit mode with every face selected (Maya converts an object selection
    to its faces for UV projections), back to
    object mode afterwards. In edit mode: nothing."""

    def __init__(self, context):
        self.context = context
        self.entered = False

    def __enter__(self):
        context = self.context
        if context.mode == 'EDIT_MESH':
            return [o for o in context.objects_in_mode_unique_data if o.type == 'MESH']
        meshes = [o for o in context.selected_objects if o.type == 'MESH']
        if not meshes:
            return []
        if context.view_layer.objects.active not in meshes:
            context.view_layer.objects.active = meshes[0]
        bpy.ops.object.mode_set(mode='EDIT')
        self.entered = True
        bpy.ops.mesh.select_mode(type='FACE')
        bpy.ops.mesh.select_all(action='SELECT')
        return [o for o in bpy.context.objects_in_mode_unique_data if o.type == 'MESH']

    def __exit__(self, *exc):
        if self.entered:
            bpy.ops.object.mode_set(mode='OBJECT')
        return False


def _mesh_poll(context):
    if context.mode == 'EDIT_MESH':
        return True
    return context.mode == 'OBJECT' and any(o.type == 'MESH' for o in context.selected_objects)


PLANE_ITEMS = [(n, n, f"{n} projection planes") for n in ("3", "4", "5", "6", "8", "12")]


class ALLSET_OT_uv_automatic(bpy.types.Operator):
    """Project UVs from several planes at once (Maya UV > Automatic): the selected faces, or every face of the
    selected meshes in object mode"""
    bl_idname = "allset.uv_automatic"
    bl_label = "Automatic"
    bl_options = {'REGISTER', 'UNDO'}

    planes: EnumProperty(name="Planes", items=PLANE_ITEMS, default="6")
    spacing: FloatProperty(name="Percentage Space", default=0.2, min=0.0, max=5.0)

    poll = classmethod(lambda cls, context: _mesh_poll(context))

    def execute(self, context):
        n = 0
        from . import extrude
        unit = units.maya_unit(context.scene)
        params = dict(AUTOPROJ.defaults, planes=int(self.planes), percentage_space=self.spacing)
        made = []
        object_mode = context.mode == 'OBJECT'
        with _ObjectFaces(context) as obs:
            for ob in obs:
                bm = bmesh.from_edit_mesh(ob.data)
                if not any(f.select and not f.hide for f in bm.faces):
                    continue
                # the polyAutoProj history node (#150): Channel Box INPUTS / AE, editable values
                if extrude.record_new(context, ob, bm, AUTOPROJ, params, unit) is not None:
                    n += 1
                    made.append(ob)
        if object_mode:
            for ob in made:
                note_object_state(ob)
        if not n:
            self.report({'WARNING'}, "Select faces (or a mesh) to project.")
            return {'CANCELLED'}
        return {'FINISHED'}


# --- polyAutoProj history node (Issue #150) ------------------------------------------------
# Maya's UV > Automatic leaves a polyAutoProj node whose Channel Box INPUTS rows can be edited
# (Planes, Optimize, Layout, Percentage Space, Scale Mode, Layout Method
# after the projection's Translate / Rotate / Scale / Pivot). The kit's node shows the rows it rebuilds with
# (Planes, Optimize = 1 Fewer pieces / 0 Less distortion, Percentage Space); the others stay at their
# defaults (Into square, Uniform, Bounding box, no projection transform). Like the kit's extrude / bevel
# nodes it is the last kit operation on the mesh (operators/extrude_record.py records); a UV > Automatic run from object
# mode stays editable there while the mesh's UVs are the ones it made.

PLANE_COUNTS = (3, 4, 5, 6, 8, 12)


def _build_autoproj(bm, params, unit):
    faces = [f for f in bm.faces if f.select and not f.hide]
    if not faces:
        return []
    planes = min(PLANE_COUNTS, key=lambda n: abs(n - int(round(params["planes"]))))
    uv = bm.loops.layers.uv.verify()
    auto_project(bm, uv, faces, planes, max(0.0, params["percentage_space"]), unit,
                 optimize=int(round(params["optimize"])) >= 1)
    return list({v for f in faces for v in f.verts})


def _uv_state(me):
    import numpy as np
    layer = me.uv_layers.active
    if layer is None:
        return None
    a = np.empty(len(layer.data) * 2, dtype=np.float32)
    layer.data.foreach_get("uv", a)
    return (len(me.vertices), len(me.polygons), layer.name, hash(a.tobytes()))


def note_object_state(ob):
    """Remember the UVs a UV > Automatic left on ``ob`` (object mode): its node stays while they are unchanged."""
    from . import extrude
    rec = extrude.RECORDS.get(ob.name)
    if rec is not None and rec.spec is AUTOPROJ:
        rec.object_state = _uv_state(ob.data)


def object_state_ok(ob, rec):
    st = getattr(rec, "object_state", None)
    return st is not None and st == _uv_state(ob.data)


def _autoproj_spec():
    from . import extrude
    return extrude.add_spec(extrude.Spec(
        'AUTOPROJ', "polyAutoProj", ("planes", "optimize", "percentage_space"),
        {"planes": "Planes", "optimize": "Optimize", "percentage_space": "Percentage Space"},
        {"planes": 6, "optimize": 1.0, "percentage_space": 0.2},
        {"planes": "INT", "optimize": "NONE", "percentage_space": "NONE"},
        None, "uv_automatic_edit", _build_autoproj, in_view=False, object_check=object_state_ok,
        object_note=note_object_state, pre_uv=True))


AUTOPROJ = _autoproj_spec()


@undo_steps.no_redo_panel      # no Adjust Last Operation (Maya has none)
class ALLSET_OT_uv_automatic_edit(bpy.types.Operator):
    """Change the last UV > Automatic (Maya: edit the polyAutoProj node). Blender keeps no history, so only the
    last one can be changed"""
    bl_idname = "allset.uv_automatic_edit"
    bl_label = "polyAutoProj"
    bl_options = {'REGISTER', 'UNDO'}

    planes: IntProperty(name="Planes", default=6, min=3, max=12, options={'SKIP_SAVE'})
    optimize: FloatProperty(name="Optimize", default=1.0, min=0.0, max=1.0, options={'SKIP_SAVE'},
                            description="1 = Fewer pieces, 0 = Less distortion")
    percentage_space: FloatProperty(name="Percentage Space", default=0.2, min=0.0, max=5.0, options={'SKIP_SAVE'})

    @classmethod
    def poll(cls, context):
        return context.mode in {'EDIT_MESH', 'OBJECT'}

    def execute(self, context):
        from . import extrude
        unit = units.maya_unit(context.scene)
        params = {"planes": self.planes, "optimize": self.optimize, "percentage_space": self.percentage_space}
        if context.mode == 'EDIT_MESH':
            done = 0
            for ob in context.objects_in_mode_unique_data:
                rec = extrude.RECORDS.get(ob.name)
                if rec is not None and rec.spec is AUTOPROJ and rec.pre is not None and (
                        rec.live or extrude.current(ob) is not None):
                    done += bool(extrude.run(ob, rec, params, unit))
            return {'FINISHED'} if done else {'CANCELLED'}
        ob = context.active_object
        rec = extrude.object_record(ob)
        if rec is None or rec.spec is not AUTOPROJ:
            return {'CANCELLED'}
        sel = list(context.selected_objects)
        for o in sel:
            o.select_set(o == ob)
        bpy.ops.object.mode_set(mode='EDIT')
        try:
            ok = extrude.run(ob, rec, params, unit)
        finally:
            bpy.ops.object.mode_set(mode='OBJECT')
            for o in sel:
                o.select_set(True)
        note_object_state(ob)
        return {'FINISHED'} if ok else {'CANCELLED'}


class ALLSET_OT_uv_contour(bpy.types.Operator):
    """Lay the selected faces out along their quad grid and stretch them to fill 0-1 (Maya UV > Contour Stretch;
    Blender Follow Active Quads): every face of the selected meshes in object mode"""
    bl_idname = "allset.uv_contour"
    bl_label = "Contour Stretch"
    bl_options = {'REGISTER', 'UNDO'}

    poll = classmethod(lambda cls, context: _mesh_poll(context))

    def execute(self, context):
        done = 0
        with _ObjectFaces(context) as obs:
            for ob in obs:
                bm = bmesh.from_edit_mesh(ob.data)
                uv = bm.loops.layers.uv.verify()
                faces = [f for f in bm.faces if f.select and not f.hide]
                quads = [f for f in faces if len(f.verts) == 4]
                if not quads:
                    continue
                if bm.faces.active not in quads:
                    bm.faces.active = quads[0]
                bmesh.update_edit_mesh(ob.data)
                with context.temp_override(active_object=ob, object=ob, edit_object=ob,
                                           objects_in_mode=[ob], objects_in_mode_unique_data=[ob]):
                    try:
                        _with_faces(context, ob, faces, lambda: bpy.ops.uv.follow_active_quads(mode='LENGTH_AVERAGE'))
                    except RuntimeError:
                        continue
                bm = bmesh.from_edit_mesh(ob.data)
                uv = bm.loops.layers.uv.verify()
                fit_unit([lp for f in bm.faces if f.select and not f.hide for lp in f.loops], uv)
                bmesh.update_edit_mesh(ob.data)
                done += 1
        if not done:
            self.report({'WARNING'}, "Select quad faces (or a mesh) for Contour Stretch.")
            return {'CANCELLED'}
        return {'FINISHED'}
