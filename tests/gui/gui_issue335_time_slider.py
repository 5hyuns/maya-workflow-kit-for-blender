"""#335: in a real UI a double-click on the Time Slider highlights the whole visible range (Maya) and opens no
panel; a plain click afterwards drops the range. When Blender's own channel-editability toggle (what its
double-click item ran before) opens its redo panel over the Time Slider, the kit closes it."""

import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, ev, run, screenshot, setup, step, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def timeline():
    for area in win().screen.areas:
        if area.type == 'DOPESHEET_EDITOR' and area.spaces.active.mode == 'TIMELINE':
            return area, next(r for r in area.regions if r.type == 'WINDOW')
    raise LookupError("no timeline")


def tx(frame):
    _area, r = timeline()
    x = r.view2d.view_to_region(frame, 0, clip=False)[0]
    return r.x + int(x), r.y + r.height // 2


def hud_state():
    area, _r = timeline()
    hud = [r for r in area.regions if r.type == 'HUD']
    return bool(hud), area.spaces.active.show_region_hud


def hover_view():
    _a, r = view3d()
    ev('MOUSEMOVE', 'NOTHING', x=r.x + r.width // 2, y=r.y + r.height // 2)


@step
def s_setup():
    setup()
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, 48
    sc.use_preview_range = False
    sc.frame_set(1)
    area, r = timeline()
    with bpy.context.temp_override(window=win(), area=area, region=r):
        bpy.ops.anim.scene_range_frame()      # the Maya Time Slider shows the playback range
    bpy.context.window_manager.allset_time_range_on = False
    hover_view()


@step
def s_hover_24():
    C["t24"] = tx(24)
    ev('MOUSEMOVE', 'NOTHING', x=C["t24"][0], y=C["t24"][1])


@step
def s_double_click():
    x, y = C["t24"]
    for _ in range(2):                        # two press / release pairs in one tick = a double-click
        ev('LEFTMOUSE', 'PRESS', x=x, y=y)
        ev('LEFTMOUSE', 'RELEASE', x=x, y=y)


@step
def s_range_check():
    wm, sc = bpy.context.window_manager, bpy.context.scene
    rng = tuple(wm.allset_time_range)
    check(f"the first click moved the time to 24 ({sc.frame_current})", sc.frame_current == 24)
    check(f"double-click highlights the whole visible range 1-48 (on {wm.allset_time_range_on}, {rng})",
          wm.allset_time_range_on and rng == (1, 48))
    has_hud, shown = hud_state()
    check(f"no redo panel over the Time Slider (HUD region {has_hud}, shown {shown})", not has_hud or not shown)
    if SHOTS:
        screenshot(os.path.join(SHOTS, "gui_issue335_time_slider_range.png"))
    C["t30"] = tx(30)
    ev('MOUSEMOVE', 'NOTHING', x=C["t30"][0], y=C["t30"][1])


@step
def s_plain_click():
    x, y = C["t30"]
    ev('LEFTMOUSE', 'PRESS', x=x, y=y)
    ev('LEFTMOUSE', 'RELEASE', x=x, y=y)


@step
def s_plain_click_check():
    wm, sc = bpy.context.window_manager, bpy.context.scene
    check(f"a plain click drops the range and moves the time to 30 (on {wm.allset_time_range_on}, {sc.frame_current})",
          not wm.allset_time_range_on and sc.frame_current == 30)
    # Blender's channel-editability toggle, run the way its double-click item ran it, opens the redo panel
    area, r = timeline()
    with bpy.context.temp_override(window=win(), area=area, region=r):
        C["toggle"] = bpy.ops.anim.channels_editable_toggle('EXEC_DEFAULT', True)   # registered, as from a keymap
    area.tag_redraw()


@step
def s_wait():
    C["after_toggle"] = hud_state()
    area, _r = timeline()
    area.tag_redraw()


@step
def s_panel_closed():
    has_hud, shown = hud_state()
    opened = C["after_toggle"][0]
    check(f"Blender's toggle opened its redo panel ({C['toggle']}, HUD region {opened})", opened)
    check(f"the kit closed the redo panel over the Time Slider (HUD region {has_hud}, shown {shown})",
          has_hud and not shown)
    if SHOTS:
        screenshot(os.path.join(SHOTS, "gui_issue335_time_slider_no_panel.png"))


run()
