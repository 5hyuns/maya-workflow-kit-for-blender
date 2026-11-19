"""#383 in a real UI: Ctrl+drag on a Move manipulator axis moves in the plane of the other two axes and makes that
plane the active handle, like Maya; with the Ctrl+Drag Snaps preference on it moves along the axis with grid
snapping; Ctrl+drag on a Scale axis scales the other two axes."""

import os
import sys
from importlib import import_module

import bpy
from bpy_extras.view3d_utils import location_3d_to_region_2d, region_2d_to_location_3d
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, step, setup, view3d, win, scale, load_maya_layout  # noqa: E402

C = {}
STEPS = 8


def mod(name):
    return import_module(f"{MODULE}.{name}")


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


def ob1():
    return bpy.data.objects["pCube1"]


def screen(world):
    _area, region = view3d()
    p = location_3d_to_region_2d(region, region.data, world)
    return Vector((region.x + p.x, region.y + p.y))


def px_world(at):
    _area, region = view3d()
    p = location_3d_to_region_2d(region, region.data, at)
    w = region_2d_to_location_3d(region, region.data, p + Vector((1, 0)), at)
    return (w - at).length


def handle_point(axis, frac):
    c = ob1().matrix_world.translation
    n = mod("ui.manipulator").ARROW_PX * bpy.context.preferences.view.gizmo_size / 75.0 * scale()
    return screen(c + Vector(axis) * n * frac * px_world(c))


def hover(p):
    ev('MOUSEMOVE', 'NOTHING', x=int(p.x), y=int(p.y))
    ev('MOUSEMOVE', 'NOTHING', x=int(p.x) + 1, y=int(p.y))


def set_tool(name):
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.wm.tool_set_by_id(name=name)
    redraw()


def ctrl_drag(start, end):
    """Steps: hover, Ctrl key + press, moves, release + Ctrl up."""
    def s1():
        hover(start())

    def s2():
        ev('LEFT_CTRL', 'PRESS', ctrl=True)
        C["a"], C["b"] = start(), end()
        ev('LEFTMOUSE', 'PRESS', x=int(C["a"].x), y=int(C["a"].y), ctrl=True)

    def s3():
        a, b = C["a"], C["b"]
        q = a + (b - a) * (2 / STEPS)
        ev('MOUSEMOVE', 'NOTHING', x=int(q.x), y=int(q.y), ctrl=True)

    def s3b():
        a, b = C["a"], C["b"]
        for i in range(3, STEPS + 1):
            q = a + (b - a) * (i / STEPS)
            ev('MOUSEMOVE', 'NOTHING', x=int(q.x), y=int(q.y), ctrl=True)

    def s4():
        ev('LEFTMOUSE', 'RELEASE', x=int(C["b"].x), y=int(C["b"].y), ctrl=True)
        ev('LEFT_CTRL', 'RELEASE')
    for s in (s1, s2, s3, s3b, s4):
        step(s)


def x_arrow():
    return handle_point((1, 0, 0), 0.6)


def x_arrow_end():
    return handle_point((1, 0, 0), 0.6) + Vector((-60, 70))


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_cube():
    bpy.ops.allset.keymap_activate()
    view3d()[1].data.view_distance *= 2.0
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.allset.create(kind='CUBE')
    set_tool("builtin.move")
    C["start"] = ob1().location.copy()


ctrl_drag(x_arrow, x_arrow_end)


@step
def s_plane_check():
    d = ob1().location - C["start"]
    h = mod("operators.manip").HANDLES.get('TRANSLATE')
    check(f"Ctrl+X arrow drag moves in YZ, X kept ({d.x:.4f}, {d.y:.4f}, {d.z:.4f})",
          abs(d.x) < 1e-6 and (abs(d.y) > 1e-3 or abs(d.z) > 1e-3))
    check(f"the YZ plane is the active handle ({h})",
          h is not None and tuple(h["constraint_axis"]) == (False, True, True))
    C["l1"] = ob1().location.copy()
    mod("preferences").get(bpy.context).manip_ctrl_snap = True


ctrl_drag(x_arrow, x_arrow_end)


@step
def s_snap_check():
    d = ob1().location - C["l1"]
    k = mod("operators.units").maya_unit()
    cm = d.x / k
    check(f"Ctrl+Drag Snaps on: X only, whole cm ({d.x / k:.3f}, {d.y / k:.3f}, {d.z / k:.3f} cm)",
          abs(cm) > 0.5 and abs(cm - round(cm)) < 1e-3 and abs(d.y) < 1e-6 and abs(d.z) < 1e-6)
    mod("preferences").get(bpy.context).manip_ctrl_snap = False
    set_tool("builtin.scale")
    C["s0"] = ob1().scale.copy()


ctrl_drag(lambda: handle_point((1, 0, 0), 0.8), lambda: handle_point((1, 0, 0), 0.8) + Vector((60, 60)))


@step
def s_scale_check():
    s = ob1().scale
    check(f"Scale tool Ctrl+X: X kept, Y and Z scaled ({s.x:.3f}, {s.y:.3f}, {s.z:.3f})",
          abs(s.x - C["s0"].x) < 1e-6 and abs(s.y - C["s0"].y) > 1e-3 and abs(s.y - s.z) < 1e-6)


run()
