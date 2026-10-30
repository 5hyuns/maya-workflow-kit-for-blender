"""Issue #255: Panels > Tear Off Copy... and Tear Off... in a Maya layout view open the view in a new window
(a copy keeps the view's camera)."""

import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, load_maya_layout, run, setup, step, win  # noqa: E402

C = {}


def views():
    out = []
    for area in win().screen.areas:
        if area.type == 'VIEW_3D':
            out.append(area)
    return out


def new_windows():
    return [w for w in bpy.context.window_manager.windows if w.as_pointer() not in C["before"]]


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_tear_copy():
    C["before"] = {w.as_pointer() for w in bpy.context.window_manager.windows}
    # the biggest 3D View of the main window (not the Tool Box column)
    area = max(views(), key=lambda a: a.width * a.height)
    rv = area.spaces.active.region_3d
    C["view"] = (tuple(round(v, 3) for v in rv.view_rotation), round(rv.view_distance, 3))
    region = next(r for r in area.regions if r.type == 'WINDOW')
    header = next(r for r in area.regions if r.type == 'HEADER')
    with bpy.context.temp_override(window=win(), area=area, region=header):
        try:
            res = bpy.ops.allset.panel_run(op="allset.panel_tear_off", props='{}')
        except RuntimeError as ex:
            res = str(ex)
    C["res"] = res
    print("TEAR OFF result", res, "region", region.width, region.height)


@step
def s_wait():
    pass


@step
def s_check():
    new = new_windows()
    print("TEAR OFF new windows", [(w.width, w.height, [a.type for a in w.screen.areas]) for w in new])
    check(f"Tear Off Copy opened a window ({C['res']})", len(new) == 1)
    if new:
        area = new[0].screen.areas[0]
        check(f"... showing a 3D View ({area.type})", area.type == 'VIEW_3D')
        if area.type == 'VIEW_3D':
            rv = area.spaces.active.region_3d
            got = (tuple(round(v, 3) for v in rv.view_rotation), round(rv.view_distance, 3))
            check(f"... with the same view ({got} == {C['view']})", got == C["view"])
        for w in new:
            with bpy.context.temp_override(window=w):
                bpy.ops.wm.window_close()


run()
