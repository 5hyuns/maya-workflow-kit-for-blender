"""#190 in a real UI: the Maya layout Time Slider made taller by dragging its top edge stays tidy: the frame numbers
keep their size, sit on the ruler and never run into each other (1-250 range like the report)."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, screenshot, setup, step, load_maya_layout  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def shot(name):
    path = os.path.join(SHOTS or os.path.join(os.environ.get("TEMP", "."), "gui190"), name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    screenshot(path)
    return path


def ts():
    return import_module(MODULE + ".ui.time_slider")


def slider():
    for area in bpy.context.window_manager.windows[0].screen.areas:
        if area.type == 'DOPESHEET_EDITOR' and ts().has_slider_panel(area.spaces.active):
            return area, next(r for r in area.regions if r.type == 'WINDOW')
    raise LookupError("no Time Slider")


def label_boxes(region):
    """(x0, x1) of every ruler label as _draw_ruler places them."""
    import blf
    mod = ts()
    s = bpy.context.preferences.system.ui_scale
    v2d = region.view2d

    def x_of(f):
        return v2d.view_to_region(f, 0, clip=False)[0]
    pxf = x_of(1.0) - x_of(0.0)
    start, end = mod.playback_range(bpy.context.scene)
    step_ = mod.tick_step(start, end, pxf, s)
    lo, hi = v2d.region_to_view(0, 0)[0], v2d.region_to_view(region.width, 0)[0]
    blf.size(0, mod.RULER_FONT_SIZE * s)
    off = 2 * s + 0.2 * pxf
    out = []
    for f in mod.ruler_ticks(step_, lo, hi):
        x = round(x_of(f - 0.5)) + off
        out.append((x, x + blf.dimensions(0, str(f))[0]))
    return out


def column(path, x, y0, y1):
    """Luminance 0-255 of window column x, rows y0..y1 (bottom-up) of a screenshot."""
    im = bpy.data.images.load(path, check_existing=False)
    w, _h = im.size
    pix = im.pixels[:]
    bpy.data.images.remove(im)
    return [round((pix[(y * w + x) * 4] + pix[(y * w + x) * 4 + 1] + pix[(y * w + x) * 4 + 2]) / 3 * 255)
            for y in range(y0, y1)]


def redraw():
    for a in bpy.context.window_manager.windows[0].screen.areas:
        a.tag_redraw()


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_scene():
    bpy.ops.allset.keymap_activate()
    sc = bpy.context.scene
    sc.use_preview_range = False
    sc.frame_start, sc.frame_end = 1, 250
    sc.frame_set(1)
    redraw()


@step
def s_before():
    area, region = slider()
    C["h0"] = region.height
    C["shot0"] = shot("190_before.png")
    # hover the gap above the Time Slider, then drag that edge up
    C["x"] = area.x + area.width // 3
    top = area.y + area.height
    above = [a.y for a in bpy.context.window_manager.windows[0].screen.areas
             if a.y >= top - 1 and a.x <= C["x"] <= a.x + a.width]
    C["gap"] = (top + min(above)) // 2 if above else top + 1
    ev('MOUSEMOVE', 'NOTHING', x=C["x"], y=C["gap"])


@step
def s_move_edge():
    area, _r = slider()
    w = bpy.context.window_manager.windows[0]
    print("GUI190 area", area.x, area.y, area.width, area.height, "gap", C["gap"],
          sorted((a.type, a.x, a.y, a.width, a.height) for a in w.screen.areas), flush=True)
    with bpy.context.temp_override(window=w, screen=w.screen, area=area):
        ok = bpy.ops.screen.area_move.poll()
        C["moved"] = ok and bpy.ops.screen.area_move(x=C["x"], y=C["gap"], delta=120) == {'FINISHED'}
    check(f"edge above the Time Slider moved (poll {ok})", C["moved"])
    redraw()


@step
def s_wait():
    redraw()


@step
def s_after():
    _area, region = slider()
    check(f"Time Slider taller ({C['h0']} -> {region.height})", region.height > C["h0"] + 60)
    C["shot1"] = shot("190_after.png")
    boxes = label_boxes(region)
    gaps = [b[0] - a[1] for a, b in zip(boxes, boxes[1:])]
    check(f"frame numbers never touch (smallest gap {min(gaps):.1f} px, {len(boxes)} labels)", min(gaps) >= 2)
    # Maya 2026: ticks keep to the lower part, under half the room below the frame numbers
    x = round(region.view2d.view_to_region(49.5, 0, clip=False)[0]) + region.x + 1
    col = column(C["shot1"], x, region.y, region.y + region.height)
    tick_rows = [region.y + i for i, v in enumerate(col) if v > 110]
    top = max(tick_rows) - region.y if tick_rows else None
    check(f"ticks stay in the lower half (tick top {top} of {region.height} px)",
          top is not None and top < region.height * 0.55)


@step
def s_narrow():
    # a narrow window: 3-digit numbers past 100 (the second report image)
    area, region = slider()
    with bpy.context.temp_override(window=bpy.context.window_manager.windows[0], area=area, region=region):
        v2d = region.view2d
        span = v2d.region_to_view(region.width, 0)[0] - v2d.region_to_view(0, 0)[0]
        bpy.ops.view2d.zoom(deltax=-span * 0.6, deltay=0.0)
    redraw()


@step
def s_narrow_check():
    _area, region = slider()
    shot("190_zoomed.png")
    boxes = label_boxes(region)
    gaps = [b[0] - a[1] for a, b in zip(boxes, boxes[1:])]
    check(f"zoomed out: frame numbers never touch (smallest gap {min(gaps):.1f} px)", min(gaps) >= 2)


run()
