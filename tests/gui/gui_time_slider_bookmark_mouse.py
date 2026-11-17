"""The Time Slider's bookmark strip in the Maya Workflow Kit layout, driven by simulated mouse events (like Maya):

- the mouse over a bookmark shows its name and range; it goes when the mouse moves below the strip or out of the
  Time Slider;
- a click on a bookmark leaves the time where it is, a click below the coloured bar (still on the strip) moves it;
- a second Ctrl click on a bookmark (a Ctrl double-click) highlights the bookmark's range;
- a right-click on the strip opens the bookmark menu for the frame under the mouse, below the strip the Time Slider
  menu;
- Ctrl + drag on a bookmark moves it, pressed at its start or end it moves that end; the time ends at the frame under
  the mouse; one undo step puts the bookmark back.
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
def _reset():
    bm = import_module(MODULE + ".operators.bookmarks")
    scene = bpy.context.scene
    bm.set_range(scene.timeline_markers["alpha"], 20, 40)
    scene.frame_current = 1
    bpy.ops.ed.undo_push(message="test reset")


def _alpha():
    bm = import_module(MODULE + ".operators.bookmarks")
    scene = bpy.context.scene
    return bm.bookmark_range(scene, scene.timeline_markers["alpha"])


def _ctrl_drag(name, f0, f1, row, want, frame, undo=False):
    def press():
        _reset()
        x, y = at(f0, row)
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y, ctrl=True)
        ev('LEFTMOUSE', 'PRESS', x=x, y=y, ctrl=True)
    step(press)
    for i in range(1, 7):
        def mv(i=i):
            x0, y = at(f0, row)
            x1, _y = at(f1, row)
            ev('MOUSEMOVE', 'NOTHING', x=int(x0 + (x1 - x0) * i / 6), y=y, ctrl=True)
        step(mv)
    step(lambda: C.__setitem__("mid_" + name, _alpha()))
    step(lambda: SHOTS and screenshot(os.path.join(SHOTS, f"time_slider_bookmark_{name}.png")))
    step(lambda: ev('LEFTMOUSE', 'RELEASE', x=at(f1, row)[0], y=at(f1, row)[1], ctrl=True))
    _idle()

    def verify():
        got = (_alpha(), bpy.context.scene.frame_current)
        check(f"{name}: alpha during the drag {C['mid_' + name]}, after {got} (want {want}, frame {frame})",
              C["mid_" + name] == want and got == (want, frame))
        if undo:
            bpy.ops.ed.undo()
    step(verify)
    if undo:
        _idle()
        step(lambda: check(f"{name}: one undo puts alpha back ({_alpha()})", _alpha() == (20, 40)))


_ctrl_drag("ctrl_drag_move", 30, 40, 'BAR', (30, 50), 40, undo=True)
_ctrl_drag("ctrl_drag_start", 20, 15, 'STRIP', (15, 40), 15)
_ctrl_drag("ctrl_drag_end", 39, 44, 'BAR', (20, 45), 44)
_ctrl_drag("ctrl_drag_ruler_nothing", 30, 40, 'RULER', (20, 40), 1)


@step
def s_leave_to_buttons():
    """From a bookmark straight onto the buttons next to the Time Slider (another region, whose buttons take the
    mouse moves): the name goes."""
    move(30, 'BAR')


_idle()


@step
def s_leave_to_buttons_move():
    C["before_buttons"] = shown()
    a, r = timeline()
    others = [x for x in a.regions if x.type != 'WINDOW' and x.width > 4 and x.height > 4]
    C["buttons_region"] = others[0].type if others else None
    if others:
        o = others[0]
        ev('MOUSEMOVE', 'NOTHING', x=o.x + min(o.width - 2, 12), y=o.y + o.height // 2)
    else:     # the Maya layout's Time Slider has no header: the area above it
        ev('MOUSEMOVE', 'NOTHING', x=r.x + 12, y=r.y + r.height + 12)


_idle()
step(lambda: check(f"onto the {C['buttons_region']} region next to the Time Slider the name goes "
                   f"({C['before_buttons']} -> {shown()})", C["before_buttons"] is not None and shown() is None))


@step
def s_hover_lines():
    _reset()
    move(30, 'BAR')


_idle()
step(lambda: SHOTS and screenshot(os.path.join(SHOTS, "time_slider_bookmark_hover_lines.png")))
step(lambda: check(f"over alpha again its name shows ({shown()})", shown() is not None and shown()[0] == "alpha"))


run()
