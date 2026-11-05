"""Issue #314: with Preferences > Input > Invert Zoom Direction (Mouse) on, the Maya Alt+RMB drag zooms the same way
as Blender's own drag zoom (Ctrl+MMB): drag up = out, drag down = in."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, setup, step, view3d  # noqa: E402

C = {}


def rv3d():
    return view3d()[0].spaces.active.region_3d


def centre():
    _a, r = view3d()
    return r.x + r.width // 2, r.y + r.height // 2


def drag(button, dy, **mods):
    x, y = centre()
    names = {"alt": "LEFT_ALT", "ctrl": "LEFT_CTRL"}
    for m in mods:
        ev(names[m], 'PRESS', x=x, y=y)
    ev(button, 'PRESS', x=x, y=y, **mods)
    for i in range(1, 11):
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y + dy * i // 10, **mods)
    ev(button, 'RELEASE', x=x, y=y + dy, **mods)
    for m in mods:
        ev(names[m], 'RELEASE', x=x, y=y + dy)


@step
def s_setup():
    setup()
    bpy.context.preferences.inputs.invert_mouse_zoom = True
    r = rv3d()
    r.view_perspective = 'PERSP'
    r.view_location, r.view_distance = (0, 0, 0), 20.0
    C["d0"] = r.view_distance
    drag('RIGHTMOUSE', 120, alt=True)


@step
def s_maya_up():
    d = rv3d().view_distance
    check(f"Maya mode, invert on: Alt+RMB drag up zooms out ({C['d0']:.2f} -> {d:.2f})", d > C["d0"] + 0.5)
    C["d0"] = d
    drag('RIGHTMOUSE', -120, alt=True)


@step
def s_maya_down():
    d = rv3d().view_distance
    check(f"... drag down zooms in ({C['d0']:.2f} -> {d:.2f})", d < C["d0"] - 0.5)
    rv3d().view_distance = 20.0
    import_module(MODULE + ".switch").set_mode(False, layout=False)
    C["b0"] = rv3d().view_distance
    drag('MIDDLEMOUSE', 120, ctrl=True)


@step
def s_blender_up():
    d = rv3d().view_distance
    check(f"Blender mode, invert on: Ctrl+MMB drag up zooms out too ({C['b0']:.2f} -> {d:.2f})", d > C["b0"] + 0.5)
    bpy.context.preferences.inputs.invert_mouse_zoom = False


run()
