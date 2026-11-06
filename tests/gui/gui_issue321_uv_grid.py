"""#321: UV Editor > View > Grid ❒ (UV Grid Options) sets how many UDIM tiles the UV Editor's grid shows across and
up; Apply reaches every open UV Editor."""

import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, run, screenshot, setup, step, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


@step
def s_setup():
    setup()


@step
def s_uv_editor():
    area = min((a for a in win().screen.areas if a.type != 'VIEW_3D'), key=lambda a: -a.width * a.height)
    area.ui_type = 'UV'
    C["area"] = area


@step
def s_apply():
    res = bpy.ops.allset.opt_uv_grid('EXEC_DEFAULT', tiles_u=3, tiles_v=2)
    C["res"] = res


@step
def s_check():
    sp = C["area"].spaces.active
    shape = tuple(sp.uv_editor.tile_grid_shape)
    check(f"UV Grid Options ({C['res']}): the UV Editor shows 3 x 2 UDIM tiles ({shape})", shape == (3, 2))
    if SHOTS:
        screenshot(os.path.join(SHOTS, "gui_issue321_uv_grid.png"))


run()
