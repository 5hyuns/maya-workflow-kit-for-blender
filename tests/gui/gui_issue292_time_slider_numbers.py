"""#292: the Time Slider's frame numbers stay those of the playback range, at the ruler's size. In the Maya layout
(range 1-120) every way a mouse, trackpad or key can zoom or scroll a Blender timeline is tried over the Time Slider
(wheel, Ctrl / Shift + wheel, Ctrl + middle drag, trackpad pinch and two-finger scroll, numpad +/-, Home): no redraw
shows numbers far past the range and the view stays on frames 1-120, while a plain middle click still moves the time.
The numbers and the current frame number stay inside a ruler shorter than Maya's (here the template's height at the
session's UI scale, then at UI scale 1.6), above its ticks. Shots ``gui_issue292_*.png`` with ``--shots``."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, load_maya_layout, run, screenshot, setup, step, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}
START, END = 1, 120


def ts():
    return import_module(MODULE + ".ui.time_slider")


def ruler():
    return import_module(MODULE + ".ui.time_slider_ruler")


def slider():
    """(area, WINDOW region) of the Maya layout's Time Slider."""
    for area in win().screen.areas:
        if area.type == 'DOPESHEET_EDITOR' and area.spaces.active.mode == 'TIMELINE' \
                and ts().has_slider_panel(area.spaces.active):
            return area, next(r for r in area.regions if r.type == 'WINDOW')
    raise LookupError("no Time Slider")


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


def shot(name):
    if SHOTS:
        screenshot(os.path.join(SHOTS, name))


def labels(region):
    """The frame numbers the ruler draws now (what ``_draw_ruler`` labels)."""
    s = bpy.context.preferences.system.ui_scale or 1.0
    v = region.view2d
    pxf = v.view_to_region(1.0, 0, clip=False)[0] - v.view_to_region(0.0, 0, clip=False)[0]
    lo, hi = ts().visible_range(region)
    step_ = ruler().tick_step(START, END, pxf, s)
    return step_, ruler().ruler_ticks(step_, lo, hi)


def check_view(tag):
    _area, r = slider()
    lo, hi = ts().visible_range(r)
    ppf = r.width / (END - START + 1)
    ok = abs(lo - (START - 0.5)) * ppf <= 1.5 and abs(hi - (END + 0.5)) * ppf <= 1.5
    check(f"{tag}: the Time Slider still shows frames {START}-{END} ({lo:.2f}-{hi:.2f})", ok)
    step_, frames = labels(r)
    check(f"{tag}: its numbers stay in the range (every {step_}, {min(frames)}..{max(frames)})",
          frames and min(frames) >= START - step_ and max(frames) <= END + 1)


def hover(y_frac=0.5):
    _area, r = slider()
    C["at"] = (r.x + r.width // 2, r.y + int(r.height * y_frac))
    ev('MOUSEMOVE', 'NOTHING', x=C["at"][0], y=C["at"][1])


def _seen_draw():
    """Every Time Slider redraw: widen C["seen"] by the frames it showed (what the user saw between the steps)."""
    region = bpy.context.region
    space = bpy.context.space_data
    if region is None or space is None or space.mode != 'TIMELINE' or not ts().has_slider_panel(space):
        return
    lo, hi = ts().visible_range(region)
    seen = C.get("seen")
    C["seen"] = (lo, hi) if seen is None else (min(seen[0], lo), max(seen[1], hi))


def check_seen(tag):
    """No redraw since the events were sent showed frame numbers far outside the range (10 frames past it)."""
    seen = C.get("seen") or (START - 0.5, END + 0.5)
    check(f"{tag}: no redraw showed numbers far past the range (widest {seen[0]:.1f}..{seen[1]:.1f})",
          seen[0] >= START - 10 and seen[1] <= END + 10)


@step
def s_setup():
    setup()
    load_maya_layout()
    C["handle"] = bpy.types.SpaceDopeSheetEditor.draw_handler_add(_seen_draw, (), 'WINDOW', 'POST_PIXEL')


@step
def s_range():
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = START, END
    sc.use_preview_range = False
    sc.frame_set(1)
    redraw()


@step
def s_settle():
    redraw()


@step
def s_first():
    check_view("new scene")
    hover()


def keys(tag, kind, n=8, y_frac=0.5, **mods):
    @step
    def send():
        hover(y_frac)
        C["seen"] = None
        for _ in range(n):
            ev(kind, 'PRESS', **mods)
            ev(kind, 'RELEASE', **mods)

    @step
    def wait():
        redraw()

    @step
    def look():
        check_view(tag)
        check_seen(tag)


keys("wheel down x8", 'WHEELDOWNMOUSE')
keys("wheel up x8", 'WHEELUPMOUSE')
keys("Ctrl + wheel down x8", 'WHEELDOWNMOUSE', ctrl=True)
keys("Ctrl + wheel up x8", 'WHEELUPMOUSE', ctrl=True)
keys("Shift + wheel down x8", 'WHEELDOWNMOUSE', shift=True)
keys("Home", 'HOME', n=1)
keys("numpad period", 'NUMPAD_PERIOD', n=1)
keys("numpad minus x4", 'NUMPAD_MINUS', n=4)
keys("numpad plus x4", 'NUMPAD_PLUS', n=4)


def drag(tag, **mods):
    @step
    def press():
        hover()
        x, y = C["at"]
        C["seen"] = None
        ev('MIDDLEMOUSE', 'PRESS', **mods)
        for dx in range(-20, -200, -20):
            ev('MOUSEMOVE', 'NOTHING', x=x + dx, y=y, **mods)

    @step
    def release():
        x, y = C["at"]
        ev('MIDDLEMOUSE', 'RELEASE', x=x - 180, y=y, **mods)
        redraw()

    @step
    def wait():
        redraw()

    @step
    def look():
        check_view(tag)
        check_seen(tag)


drag("Ctrl + middle drag", ctrl=True)
drag("Shift + middle drag", shift=True)


def trackpad(tag, kind, dx):
    @step
    def send():
        hover()
        x, y = C["at"]
        C["seen"] = None
        for i in range(1, 11):
            ev(kind, 'NOTHING', x=x + dx * i, y=y)

    @step
    def wait():
        redraw()

    @step
    def wait2():
        redraw()

    @step
    def look():
        check_view(tag)
        check_seen(tag)
        ev('MOUSEMOVE', 'NOTHING', x=C["at"][0], y=C["at"][1])


trackpad("trackpad pinch", 'TRACKPADZOOM', 30)
trackpad("trackpad two-finger scroll", 'TRACKPADPAN', 40)
trackpad("trackpad two-finger scroll back", 'TRACKPADPAN', -40)


@step
def s_trackpad_shot():
    shot("gui_issue292_time_slider_after_zoom.png")


def at_frame(frame, y_frac=0.5):
    _area, r = slider()
    return r.x + int(r.view2d.view_to_region(frame, 0, clip=False)[0]), r.y + int(r.height * y_frac)


def click(tag, button, frame, y_frac=0.5):
    @step
    def press():
        x, y = at_frame(frame, y_frac)
        C["seen"] = None
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
        ev(button, 'PRESS', x=x, y=y)
        ev(button, 'RELEASE', x=x, y=y)

    @step
    def wait():
        redraw()

    @step
    def look():
        sc = bpy.context.scene
        check(f"{tag}: the click moves the time to {frame} ({sc.frame_current})", sc.frame_current == frame)
        check_view(tag)
        check_seen(tag)


click("plain middle click", 'MIDDLEMOUSE', 40)


# --- the numbers inside the ruler ---------------------------------------------------------------------------

def text_rows(region):
    """(label bottom, label top, tick top, current-number top, region height) in region px as drawn."""
    import blf
    s = bpy.context.preferences.system.ui_scale or 1.0
    h = region.height
    rows = ruler().ROWS
    blf.size(0, ruler().label_font_size(h, s))
    th = blf.dimensions(0, "120")[1]
    l0 = ruler()._rows("label", h, rows, s)[0]
    t1 = ruler()._rows("tick", h, rows, s)[1]
    c0 = ruler()._rows("current_label", h, rows, s)[0]
    return l0, l0 + th, t1, c0 + th, h


def text_check(tag):
    _area, r = slider()
    s = bpy.context.preferences.system.ui_scale
    l0, ltop, t1, ctop, h = text_rows(r)
    print(f"GUI INFO {tag}: UI scale {s}, ruler {h} px, labels {l0:.1f}-{ltop:.1f}, ticks up to {t1:.1f}, "
          f"current number up to {ctop:.1f}", flush=True)
    check(f"{tag}: UI scale {s:.2f}, ruler {h} px: the frame numbers stay inside it (top {ltop:.1f})",
          ltop <= h + 0.5)
    check(f"{tag}: UI scale {s:.2f}, ruler {h} px: the frame numbers sit above the ticks ({l0:.1f} >= {t1:.1f})",
          l0 >= t1 - 0.5)
    check(f"{tag}: UI scale {s:.2f}, ruler {h} px: the current frame number stays inside it (top {ctop:.1f})",
          ctop <= h + 0.5)
    return h, s


@step
def s_short_ruler():
    # GUI tests own the mouse, so the kit's cursor fit of the layout is off here: the Time Slider keeps the
    # template's height, shorter than Maya's ruler at a UI scale above 1 (like one made shorter by hand)
    text_check("ruler as loaded")
    shot("gui_issue292_time_slider_short.png")


@step
def s_scale():
    C["scale0"] = bpy.context.preferences.view.ui_scale
    bpy.context.preferences.view.ui_scale = 1.6
    redraw()


for _i in range(4):            # the regions take a few redraws to settle at the new scale (the view is fitted after)
    step(redraw)


@step
def s_scale_check():
    # the window keeps its size, so the bigger header squeezes the Time Slider (a few px): only the numbers count
    text_check("UI scale 1.6")
    shot("gui_issue292_time_slider_scale.png")
    bpy.context.preferences.view.ui_scale = C["scale0"]
    bpy.types.SpaceDopeSheetEditor.draw_handler_remove(C["handle"], 'WINDOW')
    redraw()


run()
