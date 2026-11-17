"""The Time Slider's bookmark strip in the Maya Workflow Kit layout, driven by simulated mouse events (like Maya):

- the mouse over a bookmark shows its name and range; it goes when the mouse moves below the strip or out of the
  Time Slider;
- a click on a bookmark leaves the time where it is, a click below the coloured bar (still on the strip) moves it;
- a second Ctrl click on a bookmark (a Ctrl double-click) highlights the bookmark's range;
- a right-click on the strip opens the bookmark menu for the frame under the mouse, below the strip the Time Slider
  menu.
"""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, screenshot, setup, step, win, load_maya_layout  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def timeline():
    for area in win().screen.areas:
        if area.type == 'DOPESHEET_EDITOR' and area.spaces.active.mode == 'TIMELINE':
            return area, next(r for r in area.regions if r.type == 'WINDOW')
    raise LookupError("no timeline")


def tsb():
    return import_module(MODULE + ".ui.time_slider_bookmarks")


def at(frame, row):
    """Window (x, y) of ``frame`` in a strip row: 'BAR' (the coloured bar), 'STRIP' (the strip under the bar) or
    'RULER' (the ruler under the strip)."""
    _a, r = timeline()
    s = bpy.context.preferences.system.ui_scale or 1.0
    strip, bar = tsb().strip_rows(r, s)
    y = {"BAR": bar[0] + 1, "STRIP": (strip[0] + bar[0]) / 2, "RULER": strip[0] - 6 * s}[row]
    x = r.view2d.view_to_region(frame, 0, clip=False)[0]
    return int(r.x + x), int(r.y + y)


def move(frame, row):
    x, y = at(frame, row)
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)


def click(frame, row, **mods):
    x, y = at(frame, row)
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('LEFTMOUSE', 'PRESS', x=x, y=y, **mods)
    ev('LEFTMOUSE', 'RELEASE', x=x, y=y, **mods)


def shown():
    a, _r = timeline()
    return tsb().hovered(a)


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_scene():
    bpy.ops.allset.keymap_activate()
    scene = bpy.context.scene
    scene.frame_start, scene.frame_end = 1, 100
    scene.use_preview_range = False
    bm = import_module(MODULE + ".operators.bookmarks")
    scene.timeline_markers.clear()
    bm.create(bpy.context, "alpha", 20, 40, (0.8, 0.1, 0.1))
    bm.create(bpy.context, "beta", 60, 70, (0.1, 0.2, 0.9))
    scene.frame_current = 1
    bpy.context.window_manager.allset_time_range_on = False


def _idle(n=2):
    for _ in range(n):
        step(lambda: None)


_idle(3)
step(lambda: move(30, 'BAR'))
_idle()
step(lambda: check(f"over alpha its name shows ({shown()})", shown() is not None and shown()[0] == "alpha"))
step(lambda: SHOTS and screenshot(os.path.join(SHOTS, "time_slider_bookmark_hover.png")))
step(lambda: move(65, 'BAR'))
_idle()
step(lambda: check(f"over beta: beta ({shown()})", shown() is not None and shown()[0] == "beta"))
step(lambda: move(65, 'RULER'))
_idle()
step(lambda: check(f"below the strip nothing shows ({shown()})", shown() is None))
step(lambda: move(30, 'BAR'))
_idle()


@step
def s_leave():
    C["before_leave"] = shown()
    a, _r = timeline()
    other = max((x for x in win().screen.areas if x != a), key=lambda x: x.width * x.height)
    ev('MOUSEMOVE', 'NOTHING', x=other.x + other.width // 2, y=other.y + other.height // 2)


_idle()
step(lambda: check(f"one move out of the Time Slider drops the name ({C['before_leave']} -> {shown()})",
                   C["before_leave"] is not None and shown() is None))


@step
def s_click_bar():
    bpy.context.scene.frame_current = 1
    click(30, 'BAR')


_idle()
step(lambda: check(f"a click on a bookmark keeps the time ({bpy.context.scene.frame_current})",
                   bpy.context.scene.frame_current == 1))


@step
def s_click_strip():
    click(30, 'STRIP')


_idle()
step(lambda: check(f"a click under the coloured bar moves the time ({bpy.context.scene.frame_current})",
                   bpy.context.scene.frame_current == 30))


@step
def s_ctrl_double():
    bpy.context.scene.frame_current = 1
    bpy.context.window_manager.allset_time_range_on = False
    click(30, 'BAR', ctrl=True)
    click(30, 'BAR', ctrl=True)


_idle()


@step
def s_ctrl_double_check():
    wm = bpy.context.window_manager
    got = (wm.allset_time_range_on, tuple(wm.allset_time_range), bpy.context.scene.frame_current)
    check(f"Ctrl double-click on a bookmark highlights its range ({got})", got == (True, (20, 40), 1))
    wm.allset_time_range_on = False


@step
def s_rmb_strip():
    tsb()._menu_at.clear()
    x, y = at(65, 'STRIP')
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('RIGHTMOUSE', 'PRESS', x=x, y=y)
    ev('RIGHTMOUSE', 'RELEASE', x=x, y=y)


_idle()


@step
def s_rmb_strip_check():
    check(f"right-click on the strip: the bookmark menu at frame 65 ({tsb().menu_frame()})", tsb().menu_frame() == 65)
    x, y = at(65, 'STRIP')
    ev('ESC', 'PRESS', x=x, y=y)
    ev('ESC', 'RELEASE', x=x, y=y)


_idle()


@step
def s_rmb_ruler():
    tsb()._menu_at.clear()
    x, y = at(30, 'RULER')
    ev('RIGHTMOUSE', 'PRESS', x=x, y=y)
    ev('RIGHTMOUSE', 'RELEASE', x=x, y=y)


_idle()


@step
def s_rmb_ruler_check():
    check(f"right-click below the strip: not the bookmark menu ({tsb().menu_frame()})", tsb().menu_frame() is None)
    x, y = at(30, 'RULER')
    ev('ESC', 'PRESS', x=x, y=y)
    ev('ESC', 'RELEASE', x=x, y=y)


_idle()
run()
