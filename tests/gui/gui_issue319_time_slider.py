"""#319 follow-up in a real UI: the Time Slider shows exactly the playback range (frame cells), a wheel over it
changes nothing, a half-width and a quarter-width timeline keep the Range Slider bar and the end fields inside
the header (no header scrollbar), and a right-click on a display layer's row (not a box) reaches the layer menu.
Shots ``gui_issue319_time_slider*.png`` with ``--shots``."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import (MODULE, check, dock_area, dock_region, ev, find_button, load_maya_layout, run,  # noqa: E402
                 setup, step, view3d, win)

GUI_TIMEOUT = 240
SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def ts():
    return import_module(f"{MODULE}.ui.time_slider")


def rb():
    return import_module(f"{MODULE}.ui.range_bar")


def timelines():
    tls = [a for a in win().screen.areas if a.type == 'DOPESHEET_EDITOR' and a.spaces.active.mode == 'TIMELINE']
    tls.sort(key=lambda a: a.x)
    return tls


def window_region(area):
    return next(r for r in area.regions if r.type == 'WINDOW')


def header_region(area):
    return next(r for r in area.regions if r.type == 'HEADER')


def redraw():
    for w in bpy.context.window_manager.windows:
        for a in w.screen.areas:
            a.tag_redraw()


def shot(name):
    if SHOTS:
        with bpy.context.temp_override(window=win()):
            bpy.ops.screen.screenshot(filepath=os.path.join(SHOTS, name))


def view_ok(area, lo, hi):
    r = window_region(area)
    got = ts().visible_range(r)
    ppf = r.width / max(hi - lo, 1e-6)
    return got, abs(got[0] - lo) * ppf <= 1.5 and abs(got[1] - hi) * ppf <= 1.5


@step
def s_setup():
    setup()
    bpy.ops.allset.make_maya(open_layout=False)
    load_maya_layout()


@step
def s_range():
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, 120
    rb().set_playback(sc, 10, 50)
    redraw()


@step
def s_wait():
    redraw()


@step
def s_view_check():
    area = timelines()[0]
    got, ok = view_ok(area, 9.5, 50.5)
    check(f"the Time Slider shows the playback range's cells 9.5-50.5 ({got[0]:.2f}-{got[1]:.2f})", ok)
    r = window_region(area)
    ev('MOUSEMOVE', 'NOTHING', x=r.x + r.width // 2, y=r.y + r.height // 2)


@step
def s_wheel():
    for _ in range(3):
        ev('WHEELUPMOUSE', 'PRESS')
        ev('WHEELUPMOUSE', 'RELEASE')


@step
def s_wheel_wait():
    redraw()


@step
def s_wheel_check():
    area = timelines()[0]
    got, ok = view_ok(area, 9.5, 50.5)
    check(f"a wheel over the Time Slider changes nothing ({got[0]:.2f}-{got[1]:.2f})", ok)
    # Blender's Frame All (what a Home key would run) drifts the view: the kit fits it back
    r = window_region(area)
    with bpy.context.temp_override(window=win(), screen=win().screen, area=area, region=r):
        bpy.ops.view2d.zoom_out(zoomfacx=0.4, zoomfacy=0.0)
    C["after_zoom"] = ts().visible_range(r)
    redraw()


@step
def s_zoom_wait():
    redraw()


@step
def s_zoom_check():
    area = timelines()[0]
    got, ok = view_ok(area, 9.5, 50.5)
    z = C["after_zoom"]
    check(f"a zoomed-out view ({z[0]:.1f}-{z[1]:.1f}) is fitted back to 9.5-50.5 ({got[0]:.2f}-{got[1]:.2f})", ok)
    shot("gui_issue319_time_slider_full.png")
    # half-width timeline
    r = window_region(area)
    with bpy.context.temp_override(window=win(), screen=win().screen, area=area, region=r):
        bpy.ops.screen.area_split(direction='VERTICAL', factor=0.5)
    redraw()


@step
def s_split_wait():
    redraw()


@step
def s_split2():
    area = timelines()[-1]
    r = window_region(area)
    with bpy.context.temp_override(window=win(), screen=win().screen, area=area, region=r):
        bpy.ops.screen.area_split(direction='VERTICAL', factor=0.5)
    redraw()


@step
def s_split_wait2():
    redraw()


@step
def s_split_wait3():
    redraw()


@step
def s_split_check():
    unit = round(20 * bpy.context.preferences.system.ui_scale)
    for area in timelines():
        hdr = header_region(area)
        bar = rb()._bars.get(area.as_pointer())
        got, ok = view_ok(area, 9.5, 50.5)
        check(f"timeline {hdr.width} px wide: view 9.5-50.5 ({got[0]:.2f}-{got[1]:.2f})", ok)
        units = hdr.width / unit
        if units < ts().ROW_CORE_UNITS + rb().MIN_BAR_UNITS:
            # narrower than the four range fields and the buttons: no Range Slider can fit (Maya's window has a
            # minimum width too); the view still follows the range
            check(f"timeline {hdr.width} px wide ({units:.0f} units): too short for the Range Slider row", True)
            continue
        check(f"timeline {hdr.width} px wide: the Range Slider bar is drawn ({bar is not None})", bar is not None)
        if bar is not None:
            # the two end fields (2 x 4.5 units) must fit after the bar: no header overflow / scrollbar
            room = hdr.width - bar["x1"]
            check(f"timeline {hdr.width} px: {room:.0f} px after the bar for the end fields (need {9 * unit})",
                  room >= 9 * unit)
    shot("gui_issue319_time_slider_narrow.png")


# --- the layer row ---------------------------------------------------------------------------------------

def le():
    return import_module(f"{MODULE}.ui.layer_editor")


def _dock():
    return dock_area(), dock_region()


def _record_menu(self, context):
    C["row_ctx"] = (le().is_layer_row(context), le().is_layer_button(context),
                    getattr(getattr(context, "button_prop", None), "identifier", None))


@step
def s_layers():
    area, reg = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=reg, space_data=area.spaces.active):
        bpy.ops.allset.create(kind='CUBE')
    sc = bpy.context.scene
    bpy.context.window_manager.allset_le_tab = 'DISPLAY'
    with bpy.context.temp_override(window=win()):
        bpy.ops.allset.layer_new(selected=True)
    C["layer"] = le().active_layer(bpy.context)
    dock_area('CHANNEL_BOX')
    redraw()


step(find_button(_dock, lambda _p, c: "layer_toggle" in c, C, "vbox", x_frac=0.1, step_px=4, start_frac=0.3))


@step
def s_row_hover():
    v = C.get("vbox")
    check(f"layer row V box found ({v})", v is not None)
    if v:
        _area, reg = _dock()
        bpy.types.UI_MT_button_context_menu.prepend(_record_menu)
        ev('MOUSEMOVE', 'NOTHING', x=reg.x + int(reg.width * 0.6), y=v[1])


@step
def s_row_rmb():
    if C.get("vbox"):
        ev('RIGHTMOUSE', 'PRESS')
        ev('RIGHTMOUSE', 'RELEASE')


@step
def s_row_check():
    if C.get("vbox"):
        shot("gui_issue319_time_slider_layer_row_menu.png")
        ev('ESC', 'PRESS')
        ev('ESC', 'RELEASE')
        bpy.types.UI_MT_button_context_menu.remove(_record_menu)
        got = C.get("row_ctx")
        check(f"right-click on the layer row (list row button) reaches the layer menu ({got})",
              got is not None and got[0] and got[1])


run()
