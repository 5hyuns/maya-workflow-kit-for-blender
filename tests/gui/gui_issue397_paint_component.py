"""Issue #397: Paint Skin Weights on a posed skin shows its wireframe (Maya's Show wireframe is on), and switching to
vertex component mode (F9) while painting keeps the pose like Maya: the mesh, its vertices and the kit's component
drawing stay where the posed mesh is, the vertices selected in Select mode stay selected, and painting again (the
shelf button) still shows the pose."""

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
        C["rest"] = [v.co.copy() for v in c.data.vertices]
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
        bpy.ops.allset.paint_skin_weights()                    # the Rigging shelf's Paint Skin Weights
        bpy.ops.allset.skin_paint_mode(mode='SELECT')
    area, _r = main_view()
    check(f"Paint Skin Weights shows the wireframe ({area.spaces.active.overlay.show_paint_wire})",
          area.spaces.active.overlay.show_paint_wire)
    c = cyl()
    C["top"] = sorted(v.index for v in c.data.vertices if v.co.z > 0.7 * k)
    wp = mod(".operators.weight_paint")
    wp.set_vertex_selection(c, C["top"])
    c.data.update()
    C["posed"] = shown_positions()
    check(f"posed while painting ({far(C['posed'], C['rest']) / k:.2f} units from rest)",
          far(C["posed"], C["rest"]) > 0.5 * k)


@step
def s_f9():
    key('F9')


@step
def s_component():
    c = cyl()
    k = C["k"]
    check(f"F9: vertex component mode ({bpy.context.mode}, {tuple(bpy.context.tool_settings.mesh_select_mode)})",
          bpy.context.mode == 'EDIT_MESH' and tuple(bpy.context.tool_settings.mesh_select_mode) == (True, False, False))
    now = shown_positions()
    check(f"the mesh keeps its pose ({far(now, C['posed']) / k:.3f} units from the posed mesh)",
          len(now) == len(C["posed"]) and far(now, C["posed"]) < 1e-4 * k)
    bm = bmesh.from_edit_mesh(c.data)
    sel = sorted(v.index for v in bm.verts if v.select)
    check(f"the Select mode vertices stay selected ({len(sel)} vs {len(C['top'])})", sel == C["top"])
    st = mod(".ui.component_colors").state(c, bpy.context.evaluated_depsgraph_get(), faces=False,
                                           select_mode=(True, False, False))
    ok = st is not None and st.arrays is not None and len(st.arrays.co) == len(C["posed"])
    gap = max((Vector(st.arrays.co[i]) - C["posed"][i]).length for i in range(len(C["posed"]))) if ok else -1
    check(f"the kit draws the vertices on the posed mesh ({gap / k:.4f})", ok and gap < 1e-4 * k)
    if SHOTS:
        screenshot(os.path.join(SHOTS, "gui_issue397_component.png"))


@step
def s_preselect():
    """The kit's preselection highlight finds a vertex where the posed mesh shows it."""
    from bpy_extras.view3d_utils import location_3d_to_region_2d
    area, r = main_view()
    c = cyl()
    rv = r.data
    eye = rv.view_matrix.inverted().translation
    near = min(C["top"], key=lambda i: (c.matrix_world @ C["posed"][i] - eye).length)
    p = location_3d_to_region_2d(r, rv, c.matrix_world @ C["posed"][near])
    with override():
        hit = mod(".operators.preselect").pick(bpy.context, r, rv, (p.x, p.y))
    check(f"preselection under the posed vertex {near}: {hit[1:] if hit else None}",
          hit is not None and hit[1] == 'VERT' and hit[2] == near)


@step
def s_paint_again():
    with override():
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.allset.paint_skin_weights()
    check(f"painting again ({bpy.context.mode}) still shows the pose",
          bpy.context.mode == 'PAINT_WEIGHT' and far(shown_positions(), C["posed"]) < 1e-4 * C["k"])


run()
