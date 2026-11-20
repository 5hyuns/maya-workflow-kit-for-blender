"""Issue #407: a posed skin whose Normalize Weights is Disable or Enable (Skin > Normalize Weights) keeps its pose in
vertex component mode (F9) like Maya: the kit draws and preselects its vertices on the posed mesh, and moving them
moves them where the view shows them."""

import os
import sys
from importlib import import_module
from math import radians

import bmesh
import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, load_maya_layout, run, screenshot, setup, step, win  # noqa: E402

GUI_TIMEOUT = 200
C = {}
SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")


def mod(name):
    return import_module(MODULE + name)


def main_view():
    toolbox = mod(".ui.toolbox")
    areas = [a for a in win().screen.areas if a.type == 'VIEW_3D' and not toolbox.is_toolbox(a.spaces.active)]
    area = max(areas, key=lambda a: a.width * a.height)
    return area, next(r for r in area.regions if r.type == 'WINDOW')


def override():
    area, r = main_view()
    return bpy.context.temp_override(window=win(), area=area, region=r)


def cyl():
    return bpy.data.objects["pCylinder1"]


def key(type_, **mods):
    _a, r = main_view()
    x, y = r.x + r.width // 2, r.y + r.height // 2
    ev(type_, 'PRESS', x=x, y=y, **mods)
    ev(type_, 'RELEASE', x=x, y=y, **mods)


def shown_positions():
    """Object-space positions of the mesh as the view shows it (the evaluated mesh, also in edit mode)."""
    c = cyl()
    ev_ob = c.evaluated_get(bpy.context.evaluated_depsgraph_get())
    me = ev_ob.to_mesh()
    try:
        return [v.co.copy() for v in me.vertices]
    finally:
        ev_ob.to_mesh_clear()


def far(a, b):
    return max((p - q).length for p, q in zip(a, b))


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_scene():
    joints = mod(".operators.joints")
    k = mod(".operators.units").maya_unit()
    C["k"] = k
    with override():
        bpy.ops.allset.create(kind='CYLINDER')
        c = bpy.context.active_object
        bm = bmesh.new()
        bm.from_mesh(c.data)
        vertical = [e for e in bm.edges if abs(e.verts[0].co.z - e.verts[1].co.z) > 1e-9]
        bmesh.ops.subdivide_edges(bm, edges=vertical, cuts=7, use_grid_fill=True)
        bm.to_mesh(c.data)
        bm.free()
        bpy.ops.object.select_all(action='DESELECT')
        sk = joints.new_skeleton(bpy.context)
        parent = None
        for z in (-1.0, 0.0, 1.0):
            parent = joints.add_joint(sk, Vector((0, 0, z * k)), parent, length=k)
        joints.finish(bpy.context, sk, ["joint1", "joint2", "joint3"])
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        sk.select_set(True)
        c.select_set(True)
        bpy.context.view_layer.objects.active = c
        bpy.ops.allset.bind_skin()
        sk.pose.bones["joint2"].rotation_mode = 'XYZ'
        sk.pose.bones["joint2"].rotation_euler = (radians(70), 0, 0)
        bpy.ops.object.select_all(action='DESELECT')
        c.select_set(True)
        bpy.context.view_layer.objects.active = c
        bpy.ops.allset.frame(selected=False)
    C["top"] = sorted(v.index for v in cyl().data.vertices if v.co.z > 0.7 * k)


def _mode_steps(mode):
    @step
    def s_mode():
        with override():
            if bpy.context.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.allset.skin_normalize_mode(mode=mode)           # Skin > Normalize Weights
        C["posed"] = shown_positions()

    @step
    def s_f9():
        key('F9')

    @step
    def s_component():
        c = cyl()
        k = C["k"]
        check(f"{mode}: F9 = vertex component mode ({bpy.context.mode})", bpy.context.mode == 'EDIT_MESH')
        bm = bmesh.from_edit_mesh(c.data)
        for v in bm.verts:
            v.select_set(v.index in C["top"])
        bm.select_flush_mode()
        bmesh.update_edit_mesh(c.data)
        st = mod(".ui.component_colors").state(c, bpy.context.evaluated_depsgraph_get(), faces=False,
                                               select_mode=(True, False, False))
        ok = st is not None and st.arrays is not None and len(st.arrays.co) == len(C["posed"])
        gap = max((Vector(st.arrays.co[i]) - C["posed"][i]).length for i in range(len(C["posed"]))) if ok else -1
        check(f"{mode}: the kit draws the vertices on the posed mesh ({gap / k:.4f})", ok and 0 <= gap < 1e-4 * k)

    @step
    def s_preselect():
        from bpy_extras.view3d_utils import location_3d_to_region_2d
        _area, r = main_view()
        c = cyl()
        rv = r.data
        eye = rv.view_matrix.inverted().translation
        near = min(C["top"], key=lambda i: (c.matrix_world @ C["posed"][i] - eye).length)
        p = location_3d_to_region_2d(r, rv, c.matrix_world @ C["posed"][near])
        with override():
            hit = mod(".operators.preselect").pick(bpy.context, r, rv, (p.x, p.y))
        check(f"{mode}: preselection under the posed vertex {near}: {hit[1:] if hit else None}",
              hit is not None and hit[1] == 'VERT' and hit[2] == near)

    @step
    def s_move():
        k = C["k"]
        before = shown_positions()
        with override():
            bpy.ops.transform.translate(value=(0.0, 0.0, 0.5 * k))
        after = shown_positions()
        worst = max(((after[i] - before[i]) - Vector((0.0, 0.0, 0.5 * k))).length for i in C["top"])
        check(f"{mode}: Move moves the posed vertices by the dragged amount ({worst / k:.3f} units off)",
              worst < 0.05 * k)
        with override():
            bpy.ops.transform.translate(value=(0.0, 0.0, -0.5 * k))


for _m in ("INTERACTIVE", "NONE", "POST"):
    _mode_steps(_m)

run()
