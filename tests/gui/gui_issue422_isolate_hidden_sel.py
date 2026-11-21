"""#422 in a real UI: an object Isolate Select hides but that is selected (picked in the Outliner, or selected before)
leaves the selection like any other object in Maya: a click on empty space or on an isolated object, and a replacing
marquee or lasso, take it out of the selection; Shift keeps it. ALLSET_422_LAYOUT=maya: the Maya layout."""

import math
import os
import sys
from importlib import import_module

import bmesh
import bpy
from bpy_extras import view3d_utils
from mathutils import Euler, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, load_maya_layout, run, setup, step, view3d, win  # noqa: E402

MAYA_LAYOUT = os.environ.get("ALLSET_422_LAYOUT", "") == "maya"
C = {"u": 1.0}


def key(k, **mods):
    ev(k, 'PRESS', **mods)
    ev(k, 'RELEASE', **mods)


def space():
    return view3d()[0].spaces.active


def park():
    _a, r = view3d()
    ev('MOUSEMOVE', 'NOTHING', x=r.x + r.width // 2, y=r.y + int(r.height * 0.92))


def ctrl_one():
    park()
    ev('LEFT_CTRL', 'PRESS')
    key('ONE', ctrl=True)
    ev('LEFT_CTRL', 'RELEASE')


def screen_xy(co):
    area, region = view3d()
    p = view3d_utils.location_3d_to_region_2d(region, area.spaces.active.region_3d, Vector(co) * C["u"])
    return region.x + int(round(p.x)), region.y + int(round(p.y))


def click(xy, shift=False):
    ev('MOUSEMOVE', 'NOTHING', x=xy[0], y=xy[1])
    if shift:
        ev('LEFT_SHIFT', 'PRESS')
    ev('LEFTMOUSE', 'PRESS', x=xy[0], y=xy[1], shift=shift)
    ev('LEFTMOUSE', 'RELEASE', x=xy[0], y=xy[1], shift=shift)
    if shift:
        ev('LEFT_SHIFT', 'RELEASE')


def drag(a, b):
    ev('MOUSEMOVE', 'NOTHING', x=a[0], y=a[1])
    ev('LEFTMOUSE', 'PRESS', x=a[0], y=a[1])
    for i in range(1, 9):
        ev('MOUSEMOVE', 'NOTHING', x=a[0] + (b[0] - a[0]) * i // 8, y=a[1] + (b[1] - a[1]) * i // 8)
    ev('LEFTMOUSE', 'RELEASE', x=b[0], y=b[1])


def rel(fx, fy):
    _a, r = view3d()
    return r.x + int(r.width * fx), r.y + int(r.height * fy)


def selected():
    return sorted(o.name for o in bpy.context.scene.objects if o.type == 'MESH' and o.select_get())


def hidden_pick():
    """pCube3 (outside the isolation) selected too, as a click on it in the Outliner does."""
    bpy.data.objects["pCube3"].select_set(True)


def idle(n=1):
    for _ in range(n):
        step(lambda: None)


@step
def s_setup():
    setup()
    if MAYA_LAYOUT:
        load_maya_layout()


idle()


@step
def s_scene():
    for ob in list(bpy.data.objects):
        if ob.type == 'MESH':
            bpy.data.objects.remove(ob)
    sc = bpy.context.scene
    C["u"] = u = import_module(MODULE + ".operators.units").maya_unit(sc)
    for name, x in (("pCube1", -3.0), ("pCube2", 0.0), ("pCube3", 3.0)):
        me = bpy.data.meshes.new(name)
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=2.0 * u)
        bm.to_mesh(me)
        bm.free()
        ob = bpy.data.objects.new(name, me)
        ob.location.x = x * u
        sc.collection.objects.link(ob)
    rv3d = space().region_3d
    rv3d.view_perspective = 'PERSP'
    rv3d.view_rotation = Euler((math.radians(70), 0, math.radians(20))).to_quaternion()
    rv3d.view_location = (0, 0, 0)
    rv3d.view_distance = 16.0 * u
    for o in sc.objects:
        o.select_set(o.name in ("pCube1", "pCube2"))
    bpy.context.view_layer.objects.active = sc.objects["pCube2"]


idle()
step(ctrl_one)
idle()


@step
def s_iso():
    sp = space()
    shown = sorted(o.name for o in bpy.context.scene.objects if sp.local_view and o.local_view_get(sp))
    check(f"Ctrl+1 isolates pCube1 + pCube2 ({shown})", shown == ["pCube1", "pCube2"])
    hidden_pick()
    click(rel(0.08, 0.9))           # empty space


idle()


@step
def s_empty():
    check(f"a click on empty space clears the whole selection, also the hidden pCube3 ({selected()})",
          selected() == [])
    hidden_pick()
    click(screen_xy((0, 0, 1)))     # pCube2


idle()


@step
def s_click_obj():
    check(f"a click on pCube2 selects only it ({selected()})", selected() == ["pCube2"])
    hidden_pick()
    drag(rel(0.03, 0.97), rel(0.97, 0.03))


idle()


@step
def s_marquee():
    check(f"a marquee replaces the selection with the isolated cubes ({selected()})",
          selected() == ["pCube1", "pCube2"])
    hidden_pick()
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.wm.tool_set_by_id(name="builtin.select_lasso")
    a, b = rel(0.03, 0.97), rel(0.97, 0.03)
    pts = [a, (b[0], a[1]), b, (a[0], b[1]), (a[0], a[1] - 2)]
    ev('MOUSEMOVE', 'NOTHING', x=a[0], y=a[1])
    ev('LEFTMOUSE', 'PRESS', x=a[0], y=a[1])
    for p, q in zip(pts, pts[1:]):
        for i in range(1, 7):
            ev('MOUSEMOVE', 'NOTHING', x=p[0] + (q[0] - p[0]) * i // 6, y=p[1] + (q[1] - p[1]) * i // 6)
    ev('LEFTMOUSE', 'RELEASE', x=pts[-1][0], y=pts[-1][1])


idle()


@step
def s_lasso():
    check(f"a lasso replaces the selection with the isolated cubes ({selected()})",
          selected() == ["pCube1", "pCube2"])
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
    for o in bpy.context.scene.objects:
        o.select_set(False)
    hidden_pick()
    click(screen_xy((0, 0, 1)), shift=True)


idle()


@step
def s_shift():
    check(f"shift+click adds pCube2 and keeps pCube3 ({selected()})", selected() == ["pCube2", "pCube3"])
    ctrl_one()


idle()


@step
def s_left():
    check(f"Ctrl+1 again leaves Isolate Select ({space().local_view is None})", space().local_view is None)


run()
