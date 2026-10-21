"""Audit 128 repro (issue #1): B hold + MIDDLE mouse drag must change the soft select radius like B + LMB, and the
B release after such a drag must not toggle soft select (Maya: research/maya/interaction.md:156 "B + LMB/MMB drag").
Today MMB is not handled by allset.tap_hold (operators/taphold.py modal: only LEFTMOUSE starts a drag), so the
MMB drag passes through (view navigation) and the B release counts as a TAP -> soft select flips.
PASSES when fixed."""

import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sim import check, ev, run, setup, step, view3d, win  # noqa: E402

C = {}


def ts():
    return bpy.context.scene.tool_settings


def in_v3d(fn, *a, **kw):
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        return fn(*a, **kw)


@step
def s_setup():
    C["x"], C["y"] = setup()
    in_v3d(bpy.ops.object.mode_set, mode='EDIT')
    ts().use_proportional_edit = True        # user turned soft select on (tap B)
    ts().proportional_size = 2.0
    rv3d = view3d()[0].spaces.active.region_3d
    C["view"] = [tuple(r) for r in rv3d.view_matrix]
    ev('B', 'PRESS')


@step
def s_mmb_press():
    ev('MIDDLEMOUSE', 'PRESS', x=C["x"], y=C["y"])


@step
def s_mmb_move():
    ev('MOUSEMOVE', 'NOTHING', x=C["x"] + 50, y=C["y"])


@step
def s_mmb_move2():
    ev('MOUSEMOVE', 'NOTHING', x=C["x"] + 100, y=C["y"])


@step
def s_mmb_check():
    C["size"] = ts().proportional_size
    rv3d = view3d()[0].spaces.active.region_3d
    C["view_moved"] = [tuple(r) for r in rv3d.view_matrix] != C["view"]
    ev('MIDDLEMOUSE', 'RELEASE', x=C["x"] + 100, y=C["y"])


@step
def s_b_release():
    ev('B', 'RELEASE')


@step
def s_after():
    print("AUDIT size", C["size"], "view moved", C["view_moved"], "soft on", ts().use_proportional_edit)
    check(f"B + MMB drag 100 px -> radius x2 (2 -> 4), got {C['size']:.3f}", abs(C["size"] - 4.0) < 1e-2)
    check(f"B + MMB drag does not navigate the view (moved={C['view_moved']})", not C["view_moved"])
    check(f"B release after an MMB drag does not toggle soft select (on={ts().use_proportional_edit})",
          ts().use_proportional_edit)


run()
