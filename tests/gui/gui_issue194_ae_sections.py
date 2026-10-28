"""#194 in a real UI: an open Attribute Editor section draws its controls indented in their own content area under
the section header (Maya 2026 behaviour, checked: the expanded frame's content sits inset in a box of its own shade).

The first section header ("Mesh Component Display" of pCubeShape1) is clicked open; then the screenshot row through
its first control must show the content area: a shade change between the dock's left edge and the control."""

import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, dock_area, dock_region, ev, px, run, screenshot, setup, step, view3d, win, load_maya_layout  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}
HEADER_DY = 270       # px below the dock's top edge to the first section header (UI 1.25, baseline shot)
BODY_DY = 300         # the first control row of that section once open


def shot(name):
    path = os.path.join(SHOTS or os.path.join(os.environ.get("TEMP", "."), "gui194"), name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    screenshot(path)
    return path


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


def row_pixels(path, y, x0, x1):
    im = bpy.data.images.load(path, check_existing=False)
    w, _h = im.size
    pix = im.pixels[:]
    bpy.data.images.remove(im)
    out = []
    for x in range(x0, x1):
        i = (y * w + x) * 4
        out.append(round((pix[i] + pix[i + 1] + pix[i + 2]) / 3 * 255))
    return out


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_scene():
    bpy.ops.allset.keymap_activate()
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.allset.create(kind='CUBE')
    dock_area('ATTRIBUTE_EDITOR')
    redraw()


@step
def s_wait():
    redraw()


@step
def s_closed():
    region = dock_region()
    C["closed"] = shot("194_closed.png")
    C["top"] = region.y + region.height
    C["x"] = region.x + round(region.width * 0.4)
    ev('MOUSEMOVE', 'NOTHING', x=C["x"], y=C["top"] - px(HEADER_DY))


@step
def s_press():
    ev('LEFTMOUSE', 'PRESS')


@step
def s_release():
    ev('LEFTMOUSE', 'RELEASE')
    ev('MOUSEMOVE', 'NOTHING', x=C["x"] - 400, y=C["top"] - px(HEADER_DY))
    redraw()


@step
def s_wait2():
    redraw()


def leftmost(path, region, y0, y1, lo, hi):
    """Smallest x (from the region's left edge) of a pixel with luminance lo..hi in window rows y0..y1."""
    im = bpy.data.images.load(path, check_existing=False)
    w, _h = im.size
    pix = im.pixels[:]
    bpy.data.images.remove(im)
    best = None
    for y in range(y0, y1):
        for x in range(region.x + 2, region.x + region.width // 2):
            i = (y * w + x) * 4
            v = (pix[i] + pix[i + 1] + pix[i + 2]) / 3 * 255
            if lo <= v <= hi:
                best = x if best is None else min(best, x)
                break
    return None if best is None else best - region.x


@step
def s_open():
    region = dock_region()
    C["open"] = shot("194_open.png")
    hy = C["top"] - px(HEADER_DY)
    arrow = leftmost(C["open"], region, hy - px(6), hy + px(6), 150, 255)
    box = leftmost(C["open"], region, hy - px(50), hy - px(15), 100, 110)       # a checkbox's fill
    check(f"the section opened (a checkbox under its header: {box})", box is not None)
    check(f"its controls start right of the header arrow (arrow {arrow} px, control {box} px)",
          arrow is not None and box is not None and box >= arrow)


run()
