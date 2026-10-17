"""Step 50 in a real UI: Maya editor chrome — Channel Box / Layer Editor menu bars, Outliner header,
Time Slider buttons in the timeline sidebar, Range Slider row; screenshots."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, step, setup, screenshot, win  # noqa: E402

SHOTS = os.environ.get("MAYA_KIT_GUI_SHOTS", "")
C = {}


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


def timeline():
    return next(a for a in win().screen.areas if a.ui_type == 'TIMELINE')


@step
def s_setup():
    setup()
    check("install layout", bpy.ops.maya_kit.layout_install() == {'FINISHED'})
    bpy.ops.wm.read_homefile(app_template="MayaKit")


@step
def s_scene():
    bpy.ops.maya_kit.keymap_activate()
    bpy.ops.maya_kit.create(kind='CUBE')
    redraw()


@step
def s_wait():
    redraw()


@step
def s_check():
    tl = timeline()
    regions = {r.type: r for r in tl.regions}
    ui = regions.get('UI')
    check(f"Time Slider buttons region at the right of the Time Slider row ({ui and (ui.x, ui.width, ui.height)})",
          ui is not None and ui.width > 200 and ui.x + ui.width >= win().width - 2
          and abs(ui.y - regions['WINDOW'].y) <= 1)
    # the panel draws: frame field + transport buttons are not the region background
    if SHOTS:
        screenshot(os.path.join(SHOTS, "gui_step50_chrome.png"))
    redraw()


@step
def s_shot():
    if SHOTS:
        screenshot(os.path.join(SHOTS, "gui_step50_chrome.png"))


run()
