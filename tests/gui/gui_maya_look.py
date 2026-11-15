"""In a real UI: Maya mode puts Maya's interface look into the theme (maya_look.py) and Maya mode off puts the
user's theme back. Screen pixels with the Maya layout: menu bar, shelf row, Channel Box dock and Outliner in Maya's
greys. Save Preferences while on: the kit's once-a-second check writes the file again with the user's theme.
Screenshots on / off for the side-by-side with Maya."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, load_maya_layout, run, screenshot, setup, step, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def mod(name):
    return import_module(f"{MODULE}.{name}")


def theme_hash():
    th = bpy.context.preferences.themes[0]
    return (tuple(th.user_interface.wcol_regular.inner), tuple(th.properties.space.back),
            tuple(th.outliner.space.back), round(th.user_interface.panel_roundness, 4))


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


def shot(name):
    path = os.path.join(SHOTS or bpy.app.tempdir, f"gui_maya_look_{name}.png")
    screenshot(path)
    return path


def pixel(path, x, y):
    """Window pixel (x, y from the bottom, like area / region coordinates) of a screenshot."""
    img = bpy.data.images.load(path, check_existing=False)
    try:
        w, _h = img.size
        i = (y * w + x) * 4
        return tuple(round(v * 255) for v in img.pixels[i:i + 3])
    finally:
        bpy.data.images.remove(img)


def near(p, hex_rgb, tol=3):
    want = tuple(int(hex_rgb[i:i + 2], 16) for i in (0, 2, 4))
    return all(abs(a - b) <= tol for a, b in zip(p, want))


def spots():
    """Empty-background points: (name, x, y) in window pixels."""
    scr = win().screen
    top = max(scr.areas, key=lambda a: a.y + a.height)       # the Maya menu bar row
    out = [("menu bar", top.x + int(top.width * 0.68), top.y + top.height - 3)]
    row = mod("ui.shelf").shelf_row_area(scr)
    if row is not None:
        out.append(("shelf row", row.x + row.width - 4, row.y + 3))
    outl = [a for a in scr.areas if a.type == 'OUTLINER']
    if outl:
        a = max(outl, key=lambda a: a.height)
        r = next(r for r in a.regions if r.type == 'WINDOW')
        out.append(("Outliner", r.x + r.width // 2, r.y + 6))
    props = [a for a in scr.areas if a.type == 'PROPERTIES']
    if props:
        a = max(props, key=lambda a: a.height)
        r = next(r for r in a.regions if r.type == 'WINDOW')
        out.append(("dock", r.x + 8, r.y + int(r.height * 0.55)))     # the Channel Box's empty part
    return out


@step
def s_before():
    C["user"] = theme_hash()           # Blender's theme as the session started (the user's)


@step
def s_setup():
    setup()                            # the add-on enabled, Maya mode on
    load_maya_layout()


@step
def s_wait():
    redraw()


@step
def s_on():
    check("Maya mode on puts Maya's look into the theme", theme_hash() != C["user"] and mod("maya_look").is_applied())
    path = shot("on")
    want = {"menu bar": "444444", "shelf row": "444444", "Outliner": "373737", "dock": "444444"}
    found = spots()
    check(f"every spot found ({[n for n, _x, _y in found]})", {n for n, _x, _y in found} == set(want))
    for name, x, y in found:
        p = pixel(path, x, y)
        check(f"{name} at ({x}, {y}) is Maya's #{want[name]}: #{p[0]:02x}{p[1]:02x}{p[2]:02x}", near(p, want[name]))


@step
def s_save():
    look = mod("maya_look")
    C["mtime"] = look._userpref_mtime()
    bpy.ops.wm.save_userpref()         # the user saves while Maya mode is on
    C["user_save"] = look._userpref_mtime()


@step
def s_wait_check():
    pass


@step
def s_wait_check2():
    pass


@step
def s_after_save():
    look = mod("maya_look")
    state = look.read_state()
    check("the user's save wrote the file", C["user_save"] != C["mtime"])
    check("the kit wrote it again with the user's theme within a second",
          state is not None and state["saved"] == look._userpref_mtime() and state["saved"] != C["user_save"])
    check("Maya's look still on screen", look.is_applied() and theme_hash() != C["user"])


@step
def s_off():
    mod("switch").set_mode(False, layout=False)
    redraw()


@step
def s_wait2():
    redraw()


@step
def s_off_check():
    shot("off")
    check("Maya mode off puts the user's theme back", theme_hash() == C["user"])
    check("nothing kept any more", not mod("maya_look").is_applied())


run(interval=0.6)
