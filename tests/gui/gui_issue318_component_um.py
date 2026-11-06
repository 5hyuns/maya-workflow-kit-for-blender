"""#318 Universal Manipulator on mesh components in a real UI: the cube in edit mode with six of its vertices selected
(top and +Y faces), Ctrl+T picks the kit tool in the component mode; the box surrounds the selected vertices; a corner
drag along one box axis scales those vertices only, the opposite face staying and the two unselected vertices still;
one Ctrl+Z gives them back. Screenshot: gui_issue318_component_um.png."""

import math
import os
import sys
from importlib import import_module

import bmesh
import bpy
from bpy_extras.view3d_utils import location_3d_to_region_2d
from mathutils import Euler, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, step, setup, screenshot, view3d, win, load_maya_layout  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}
STEPS = 8


def mod(name):
    return import_module(f"{MODULE}.{name}")


def um():
    return mod("operators.universal_manip")


def ob1():
    return bpy.data.objects["pCube1"]


def override():
    area, region = view3d()
    return bpy.context.temp_override(window=win(), area=area, region=region)


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


def screen(world):
    _area, region = view3d()
    p = location_3d_to_region_2d(region, region.data, world)
    return Vector((region.x + p.x, region.y + p.y))


def box():
    bpy.context.view_layer.update()
    with override():
        frame, lo, hi = um().box_of(bpy.context)
    return frame, lo.copy(), hi.copy()


def coords(selected):
    bm = bmesh.from_edit_mesh(ob1().data)
    return {v.index: v.co.copy() for v in bm.verts if v.select == selected}


def hover(p):
    ev('MOUSEMOVE', 'NOTHING', x=int(p.x), y=int(p.y))
    ev('MOUSEMOVE', 'NOTHING', x=int(p.x) + 1, y=int(p.y))
    ev('MOUSEMOVE', 'NOTHING', x=int(p.x), y=int(p.y))


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_cube():
    bpy.ops.allset.keymap_activate()
    ui = mod("ui.universal_manip")
    original = ui.ALLSET_GGT_universal_manip.draw_prepare

    def spy(self, context):
        original(self, context)
        C["group"] = self
    ui.ALLSET_GGT_universal_manip.draw_prepare = spy
    with override():
        bpy.ops.allset.create(kind='CUBE')
    ob = ob1()
    for o in bpy.context.view_layer.objects:
        o.select_set(o is ob)
    bpy.context.view_layer.objects.active = ob
    u = C["U"] = mod("operators.units").maya_unit(bpy.context.scene)
    with override():
        bpy.ops.object.mode_set('EXEC_DEFAULT', True, mode='EDIT')
    bpy.context.scene.tool_settings.mesh_select_mode = (True, False, False)
    bm = bmesh.from_edit_mesh(ob.data)
    for el in (*bm.faces, *bm.edges, *bm.verts):
        el.select = False
    for v in bm.verts:
        v.select = v.co.z > 0.0 or v.co.y > 0.0        # six of the eight corners
    bm.select_flush_mode()
    bmesh.update_edit_mesh(ob.data)
    C["sel0"], C["unsel0"] = coords(True), coords(False)
    _area, region = view3d()
    rv3d = region.data
    rv3d.view_perspective = 'PERSP'
    rv3d.view_location = (0, 0, 0)
    rv3d.view_rotation = Euler((math.radians(65), 0, math.radians(35))).to_quaternion()
    rv3d.view_distance = 5.0 * u
    with override():
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
    bpy.ops.ed.undo_push(message="selection made")
    redraw()


@step
def s_ctrl_t():
    _area, region = view3d()
    ev('MOUSEMOVE', 'NOTHING', x=region.x + region.width // 2, y=region.y + 40)
    ev('LEFT_CTRL', 'PRESS')
    ev('T', 'PRESS', ctrl=True)
    ev('T', 'RELEASE', ctrl=True)
    ev('LEFT_CTRL', 'RELEASE')


@step
def s_tool():
    with override():
        idname = bpy.context.workspace.tools.from_space_view3d_mode('EDIT_MESH').idname
    check(f"Ctrl+T in a component mode -> Universal Manipulator ({idname}, mode {bpy.context.mode})",
          idname == um().TOOL and bpy.context.mode == 'EDIT_MESH')
    redraw()


@step
def s_shown():
    g = C.get("group")
    check("the box manipulator draws around the components", g is not None)
    if g is None:
        return
    shown = [gz for gz in g.corners if not gz.hide]
    labels = [gz.text for gz in g.labels if not gz.hide]
    frame, lo, hi = box()
    u = C["U"]
    check(f"the box is the selected vertices' box 1 x 1 x 1 ({labels}, {len(shown)} corners)",
          labels == ["1.000", "1.000", "1.000"] and len(shown) == 7
          and all(abs(v) < 1e-4 for v in (hi - lo) - Vector((u, u, u))))
    if SHOTS:
        screenshot(os.path.join(SHOTS, "gui_issue318_component_um.png"))
    corners = [(i, screen(gz.matrix_basis.translation)) for i, gz in enumerate(g.corners) if not gz.hide]
    i, p = max(corners, key=lambda c: c[1].x + c[1].y)
    s = um().corner_signs(i)
    w = frame @ um().corner_point(lo, hi, i)
    dirs = [screen(w + frame.col[k] * s[k] * 0.2 * u) - p for k in range(3)]
    k = max(range(3), key=lambda a: dirs[a].length)
    C.update(corner=i, axis=k, dir=dirs[k].normalized(), lo=lo, hi=hi, w=w)
    print(f"UM318c corner {i} axis {k}", flush=True)


@step
def s_hover():
    a = screen(C["w"])
    C["a"] = a
    C["pts"] = [a + C["dir"] * 40 * j / STEPS for j in range(1, STEPS + 1)]
    hover(a)


@step
def s_press():
    a = C["a"]
    ev('LEFTMOUSE', 'PRESS', x=int(a.x), y=int(a.y))


@step
def s_first_move():
    q = C["pts"][0]
    ev('MOUSEMOVE', 'NOTHING', x=int(q.x), y=int(q.y))


@step
def s_moves():
    for q in C["pts"][1:]:
        ev('MOUSEMOVE', 'NOTHING', x=int(q.x), y=int(q.y))


@step
def s_release():
    C["modal"] = [op.bl_idname for op in win().modal_operators]
    q = C["pts"][-1]
    ev('LEFTMOUSE', 'RELEASE', x=int(q.x), y=int(q.y))


@step
def s_check():
    k = C["axis"]
    s = um().corner_signs(C["corner"])
    _f, lo, hi = box()
    sel, unsel = coords(True), coords(False)
    grew = (hi - lo)[k] > C["U"] * 1.05
    others = all(abs((hi - lo)[a] - C["U"]) < 1e-4 for a in range(3) if a != k)
    stay = lo[k] if s[k] > 0 else hi[k]
    was = C["lo"][k] if s[k] > 0 else C["hi"][k]
    check(f"corner drag scales the selected vertices along axis {k} only (box {tuple(round(v, 3) for v in hi - lo)}, "
          f"modal {C['modal']})", grew and others)
    check(f"the opposite face stays ({stay:.4f} = {was:.4f})", abs(stay - was) < 1e-4 * C["U"])
    check("the two unselected vertices did not move",
          all((unsel[i] - C["unsel0"][i]).length < 1e-6 for i in C["unsel0"]) and len(unsel) == 2)
    check("the object itself is untouched (scale 1, at the origin)",
          all(abs(v - 1.0) < 1e-6 for v in ob1().scale) and ob1().location.length < 1e-6)
    hover(screen(Vector((0, 0, 0))) + Vector((200, 120)))
    ev('LEFT_CTRL', 'PRESS')
    ev('Z', 'PRESS', ctrl=True)
    ev('Z', 'RELEASE', ctrl=True)
    ev('LEFT_CTRL', 'RELEASE')


@step
def s_undo():
    sel = coords(True)
    check(f"one Ctrl+Z after the drag gives the vertices back (mode {bpy.context.mode})",
          bpy.context.mode == 'EDIT_MESH' and len(sel) == 6
          and all((sel[i] - C["sel0"][i]).length < 1e-5 for i in C["sel0"]))


run()
