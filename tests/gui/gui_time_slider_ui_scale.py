"""The Maya layout's Time Slider at UI scales 1.0, 1.25, 1.5 and 2.0 (a new scene at that scale, the kit's cursor
fit on like in a real session): its ruler is at least Maya's (32 px x the scale; the template's 36 px stays at 1.0),
the frame numbers and the current frame number sit inside it, and the Range Slider row under it draws its bar inside
the header. Blender 5.x snaps a moved edge to an animation editor's "header + time scrub" height, which used to pull
the fitted Time Slider back to a 29 px ruler at 1.25 and 2 px at 2.0. Shots ``gui_time_slider_ui_scale_*.png`` with
``--shots``."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, load_maya_layout, run, screenshot, setup, step, win  # noqa: E402

GUI_TIMEOUT = 600
SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def mod(name):
    return import_module(MODULE + name)


def slider():
    return next(a for a in win().screen.areas if a.type == 'DOPESHEET_EDITOR' and a.ui_type == 'TIMELINE'
                and mod(".ui.time_slider").has_slider_panel(a.spaces.active))


def region(area, kind):
    return next(r for r in area.regions if r.type == kind)


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


@step
def s_setup():
    setup()
    prefs = bpy.context.preferences
    C["view0"] = prefs.view.ui_scale
    C["base"] = prefs.system.ui_scale / prefs.view.ui_scale      # the display's own scale
    os.environ["ALLSET_FIT_WARP"] = "1"


def at(scale):
    tag = f"UI scale {scale}"

    @step
    def set_scale():
        bpy.context.preferences.view.ui_scale = scale / C["base"]
        redraw()

    @step
    def settle():
        redraw()

    @step
    def load():
        load_maya_layout()
        sc = bpy.context.scene
        sc.frame_start, sc.frame_end = 1, 120
        sc.use_preview_range = False
        sc.frame_set(1)
        redraw()

    for _i in range(14):          # the fit timer (0.5 s) + the cursor fit's ticks (columns, shelf, Time Slider)
        step(redraw)

    @step
    def look():
        import blf
        ruler_mod = mod(".ui.time_slider_ruler")
        s = bpy.context.preferences.system.ui_scale
        area = slider()
        win_r, hdr_r = region(area, 'WINDOW'), region(area, 'HEADER')
        h = win_r.height
        print(f"GUI INFO {tag}: effective {s:.2f}, Time Slider area {area.height} px = ruler {h} + Range Slider row "
              f"{hdr_r.height}", flush=True)
        if abs(s - 1.0) < 0.01:
            check(f"{tag}: the template's ruler stays ({h} px, 36)", abs(h - 36) <= 2)
        check(f"{tag}: the ruler is at least Maya's ({h} px >= {round(32 * s)})", h >= round(32 * s) - 2)
        check(f"{tag}: and not far over the kit's {round(36 * s)} px ({h})", h <= round(36 * s) + hdr_r.height)
        blf.size(0, ruler_mod.label_font_size(h, s))
        th = blf.dimensions(0, "120")[1]
        l0 = ruler_mod._rows("label", h, ruler_mod.ROWS, s)[0]
        c0 = ruler_mod._rows("current_label", h, ruler_mod.ROWS, s)[0]
        check(f"{tag}: the frame numbers sit inside the ruler (top {l0 + th:.1f} of {h})", l0 + th <= h + 0.5)
        check(f"{tag}: the current frame number too (top {c0 + th:.1f})", c0 + th <= h + 0.5)
        check(f"{tag}: the numbers are drawn at the UI scale ({ruler_mod.label_font_size(h, s):.1f} = "
              f"{ruler_mod.RULER_FONT_SIZE * s:.1f})", abs(ruler_mod.label_font_size(h, s) - ruler_mod.RULER_FONT_SIZE * s)
              < 0.01)
        bar = mod(".ui.range_bar")._bars.get(area.as_pointer())
        check(f"{tag}: the Range Slider bar is drawn in the row under it ({bar and (bar['y0'], bar['y1'])}, row "
              f"{hdr_r.height} px)", bar is not None and 0 <= bar["y0"] and bar["y1"] <= hdr_r.height)
        if SHOTS:
            screenshot(os.path.join(SHOTS, f"gui_time_slider_ui_scale_{scale}.png"))


for _s in (1.0, 1.25, 1.5, 2.0):
    at(_s)


@step
def s_restore():
    os.environ.pop("ALLSET_FIT_WARP", None)
    bpy.context.preferences.view.ui_scale = C["view0"]


run()
