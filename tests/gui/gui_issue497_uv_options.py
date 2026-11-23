"""#497 / #498 / #502: UV Editor > Modify > Unfold ❒, Layout ❒ and Optimize ❒ open the Unfold UVs Options, Layout UVs
Options and Optimize UVs Options windows
(fields, the greyed fields Blender has no counterpart for, the command button); Cut/Sew > Auto Seams ❒, Move and Sew ❒
and Modify > Normalize ❒, Straighten Border ❒ open theirs; Stitch Together ❒ and Flip ❒ (#503, #506) too. Screenshots with ALLSET_GUI_SHOTS (or
--shots)."""

import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, ev, run, screenshot, setup, step, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def uv_ctx():
    area = C["area"]
    region = next(r for r in area.regions if r.type == 'WINDOW')
    return bpy.context.temp_override(window=win(), area=area, region=region)


def centre():
    area = C["area"]
    return area.x + area.width // 2, area.y + area.height // 2


@step
def s_setup():
    setup()


@step
def s_uv_editor():
    area = max((a for a in win().screen.areas if a.type != 'VIEW_3D'), key=lambda a: a.width * a.height)
    area.ui_type = 'UV'
    C["area"] = area
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)
    bpy.ops.mesh.primitive_cube_add(size=2)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')


def opener(op, key):
    def s_open():
        x, y = centre()
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
        with uv_ctx():
            C[key] = getattr(bpy.ops.allset, op)('INVOKE_DEFAULT')
    s_open.__name__ = f"s_open_{key}"
    step(s_open)
    step(lambda: None)
    step(lambda: None)

    def s_shot():
        check(f"{op} opens its window ({C[key]})", C[key] == {'RUNNING_MODAL'})
        if SHOTS:
            screenshot(os.path.join(SHOTS, f"gui_issue497_{key}.png"))
        ev('ESC', 'PRESS')
        ev('ESC', 'RELEASE')
    s_shot.__name__ = f"s_shot_{key}"
    step(s_shot)
    step(lambda: None)


opener("opt_uv_unfold", "unfold")
opener("opt_uv_layout", "layout")
opener("opt_uv_optimize", "optimize")      # #498
# #502: Cut/Sew and Modify windows
opener("opt_uv_auto_seams", "auto_seams")
opener("opt_uv_move_sew", "move_sew")
opener("opt_uv_normalize", "normalize")
opener("opt_uv_straighten_border", "straighten_border")
# #503 / #506: Stitch Together and Flip windows
opener("opt_uv_stitch_together", "stitch_together")
opener("opt_uv_flip", "flip")


@step
def s_end():
    check("done", True)


run()
