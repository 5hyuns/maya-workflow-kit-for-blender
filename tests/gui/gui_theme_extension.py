"""In a real UI: the Maya Workflow Kit Theme (src/allset_theme, a separate theme extension) picked from Blender's
theme menu, with the add-on in Maya mode. Screen pixels: menu bar, shelf row, Channel Box dock and Outliner in
Maya's greys, and the kit's own rows (shelf tab strip) still dimmed like Maya's. Blender's default theme comes back
from the same menu. Screenshots before / with / after for the side-by-side with Maya."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, load_maya_layout, run, screenshot, setup, step, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
THEME_DIR = os.path.join(ROOT, "src", "allset_theme")
MENU = "USERPREF_MT_interface_theme_presets"
C = {}


def mod(name):
    return import_module(f"{MODULE}.{name}")


def theme_xml():
    return next(os.path.join(THEME_DIR, f) for f in os.listdir(THEME_DIR) if f.endswith(".xml"))


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


def shot(name):
    path = os.path.join(SHOTS or bpy.app.tempdir, f"gui_theme_{name}.png")
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
    out = []
    top = max(scr.areas, key=lambda a: a.y + a.height)       # the Maya menu bar row
    out.append(("menu bar", top.x + int(top.width * 0.68), top.y + top.height - 3))
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
def s_setup():
    setup()
    load_maya_layout()


@step
def s_wait():
    redraw()


@step
def s_factory():
    C["factory_hash"] = hash(tuple(tuple(bpy.context.preferences.themes[0].user_interface.wcol_regular.inner)))
    C["factory"] = shot("factory")


@step
def s_pick():
    bpy.ops.script.execute_preset(filepath=theme_xml(), menu_idname=MENU)
    redraw()


@step
def s_wait2():
    redraw()


@step
def s_theme():
    path = shot("maya_theme")
    want = {"menu bar": "444444", "shelf row": "444444", "Outliner": "373737", "dock": "444444"}
    found = spots()
    check(f"every spot found ({[n for n, _x, _y in found]})", {n for n, _x, _y in found} == set(want))
    for name, x, y in found:
        p = pixel(path, x, y)
        check(f"{name} at ({x}, {y}) is Maya's #{want[name]} with the theme: #{p[0]:02x}{p[1]:02x}{p[2]:02x}",
              near(p, want[name]))
    tabs = mod("ui.shelf_paint").TAB_DIM
    check(f"the kit's shelf tab strip keeps Maya's dimming over the theme header ({tabs:.3f})",
          abs((1 - tabs) * 0x44 - 0x37) < 0.5)


@step
def s_back():
    bpy.ops.preferences.reset_default_theme()
    redraw()


@step
def s_wait3():
    redraw()


@step
def s_after():
    path = shot("factory_again")
    same = hash(tuple(tuple(bpy.context.preferences.themes[0].user_interface.wcol_regular.inner))) == \
        C["factory_hash"]
    check("Blender's default theme is back", same)
    for name, x, y in spots():
        a, b = pixel(C["factory"], x, y), pixel(path, x, y)
        check(f"{name} looks as before the theme: {a} / {b}", all(abs(i - j) <= 2 for i, j in zip(a, b)))


run()
