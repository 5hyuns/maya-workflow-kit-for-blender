"""Step 35 in a real UI: Ctrl+Alt+LMB box zoom (left→right in, right→left out), Ctrl+T,
Ctrl+Shift+X then W then Y, F3 = Rigging menu set (screenshot), Return opens no popover."""

import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, step, setup, screenshot, tap, view3d, win  # noqa: E402

SHOTS = os.environ.get("MAYA_KIT_GUI_SHOTS", "")
C = {}


def shot(name):
    if SHOTS:
        screenshot(os.path.join(SHOTS, name))


def dist():
    return view3d()[1].data.view_distance


def tool():
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        return bpy.context.workspace.tools.from_space_view3d_mode(bpy.context.mode).idname


def drag(x0, y0, x1, y1):
    """Three steps: press, moves, release (step 28: one tick each)."""
    @step
    def press():
        ev('MOUSEMOVE', 'NOTHING', x=x0(), y=y0())
        ev('LEFTMOUSE', 'PRESS', x=x0(), y=y0(), ctrl=True, alt=True)

    @step
    def move():
        ev('MOUSEMOVE', 'NOTHING', x=(x0() + x1()) // 2, y=(y0() + y1()) // 2, ctrl=True, alt=True)
        ev('MOUSEMOVE', 'NOTHING', x=x1(), y=y1(), ctrl=True, alt=True)

    @step
    def release():
        ev('LEFTMOUSE', 'RELEASE', x=x1(), y=y1(), ctrl=True, alt=True)


@step
def s_setup():
    C["x"], C["y"] = setup()
    C["d0"] = dist()
    C["sel0"] = sorted(o.name for o in bpy.context.selected_objects)


drag(lambda: C["x"] - 80, lambda: C["y"] - 60, lambda: C["x"] + 80, lambda: C["y"] + 60)


@step
def s_zoom_in():
    check(f"Ctrl+Alt+drag left→right zooms in ({C['d0']:.3f} -> {dist():.3f})", dist() < C["d0"] * 0.9)
    check("box zoom does not change the selection",
          sorted(o.name for o in bpy.context.selected_objects) == C["sel0"])
    C["d1"] = dist()


drag(lambda: C["x"] + 80, lambda: C["y"] + 60, lambda: C["x"] - 80, lambda: C["y"] - 60)


@step
def s_zoom_out():
    check(f"Ctrl+Alt+drag right→left zooms out ({C['d1']:.3f} -> {dist():.3f})", dist() > C["d1"] * 1.1)
    ev('MOUSEMOVE', 'NOTHING', x=C["x"], y=C["y"])
    ev('T', 'PRESS', ctrl=True)
    ev('T', 'RELEASE', ctrl=True)


@step
def s_ctrl_t():
    check(f"Ctrl+T -> Universal Manipulator / Transform tool ({tool()})", tool() == "builtin.transform")
    ev('X', 'PRESS', ctrl=True, shift=True)
    ev('X', 'RELEASE', ctrl=True, shift=True)


@step
def s_multicut():
    check(f"Ctrl+Shift+X -> Multi-Cut (knife) in edit mode ({bpy.context.mode}, {tool()})",
          bpy.context.mode == 'EDIT_MESH' and tool() == "builtin.knife")
    tap('W')


@step
def s_wait_watch():   # the last-tool timer ticks every 0.25 s
    check(f"W -> Move ({tool()})", tool() == "builtin.move")


@step
def s_y():
    tap('Y')


@step
def s_y_done():
    check(f"Y -> back to the last non-QWER tool ({tool()})", tool() == "builtin.knife")
    tap('W')
    bpy.ops.object.mode_set(mode='OBJECT')
    ev('MOUSEMOVE', 'NOTHING', x=C["x"], y=C["y"])
    tap('F3')


@step
def s_f3():
    prefs = bpy.context.preferences.addons[MODULE].preferences
    check(f"F3 -> Rigging menu set ({prefs.menu_set})", prefs.menu_set == 'riggingMenuSet')
    ev('MOUSEMOVE', 'NOTHING', x=800, y=win().height - 12)   # redraw the top bar (global area)


@step
def s_f3_shot():
    shot("gui_step35_f3_rigging.png")
    ev('MOUSEMOVE', 'NOTHING', x=C["x"], y=C["y"])
    tap('F2')


@step
def s_f2():
    prefs = bpy.context.preferences.addons[MODULE].preferences
    check(f"F2 -> Modeling menu set ({prefs.menu_set})", prefs.menu_set == 'modelingMenuSet')
    C["ops0"] = len(bpy.context.window_manager.operators)
    tap('RET')


@step
def s_ret_wait():
    pass


@step
def s_ret_shot():
    shot("gui_step35_return.png")
    check("Return in the 3D View opens no rename popover",
          not any(w.screen.is_temporary for w in bpy.context.window_manager.windows))


run()
