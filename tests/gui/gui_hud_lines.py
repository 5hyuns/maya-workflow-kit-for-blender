"""Display > Heads Up Display > Current Frame / Focal Length / Scene Timecode draw their lines in the bottom right of
the view: the view's draw handler keeps running with them on (a draw error would remove it), and the bottom right
corner shows text only while they are on (screenshot)."""

import os
import sys
import tempfile
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, run, step, setup, screenshot, win, load_maya_layout  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
PREFS = ("maya_hud_current_frame", "maya_hud_focal_length", "maya_hud_scene_timecode")


def prefs():
    return bpy.context.preferences.addons[MODULE].preferences


def area3d():
    return max((a for a in win().screen.areas if a.type == 'VIEW_3D'), key=lambda a: a.width * a.height)


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


def corner_ink(name):
    """Bright pixels in the bottom right 220 x 60 px of the main view (window pixels, like the screenshot)."""
    path = os.path.join(SHOTS or tempfile.gettempdir(), name)
    screenshot(path)
    img = bpy.data.images.load(path)
    w, _h = img.size
    px = img.pixels[:]
    bpy.data.images.remove(img)
    area = area3d()
    x1 = area.x + area.width - 30
    return sum(1 for y in range(area.y + 4, area.y + 64) for x in range(x1 - 220, x1)
               if px[(y * w + x) * 4] > 0.7 and px[(y * w + x) * 4 + 1] > 0.7)


@step
def s_setup():
    setup()
    load_maya_layout()
    bpy.context.scene.frame_set(37)
    redraw()


@step
def s_off():
    redraw()


@step
def s_off_shot():
    C["off"] = corner_ink("gui_hud_lines_off.png")
    for name in PREFS:
        setattr(prefs(), name, True)
    redraw()


@step
def s_on():
    redraw()


@step
def s_check():
    vf = import_module(MODULE + ".ui.view_furniture")
    on = corner_ink("gui_hud_lines_on.png")
    check(f"the view's HUD draw handler is still there with the three lines on ({len(vf._handle)})",
          len(vf._handle) == 1)
    lines = vf.hud_lines(prefs(), bpy.context.scene, 37.0, 35.0)
    check(f"three lines, bottom first: {[a for a, _b in lines]}",
          [a for a, _b in lines] == ["Frame:", "Focal Length:", "Scene Timecode:"])
    check(f"text in the bottom right corner only while the lines are on ({C['off']} -> {on} bright pixels)",
          on > C["off"] + 50)
    for name in PREFS:
        setattr(prefs(), name, False)


C = {}
run()
