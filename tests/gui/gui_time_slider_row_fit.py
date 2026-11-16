"""The Maya layout's Range Slider row (the Timeline header, with the current time field and the transport buttons at
its right end on Blender 5.x) shows every control at UI scales 1.0 - 2.0 in windows 1280 - 1920 px wide: the last
transport button (go to end) sits at the right edge, not scrolled out of the header, and the range bar is drawn
inside it. Windows only (the OS sizes the window). Shots ``gui_time_slider_row_fit_*.png`` with ``--shots``."""

import ctypes
import ctypes.wintypes as wt
import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, button_under_mouse, check, ev, load_maya_layout, run, screenshot, setup, step, win  # noqa: E402

GUI_TIMEOUT = 900
SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}
WIDTHS = (1280, 1600, 1920)
SCALES = (1.0, 1.25, 1.5, 2.0)


def mod(name):
    return import_module(MODULE + name)


def slider():
    return next(a for a in win().screen.areas if a.type == 'DOPESHEET_EDITOR' and a.ui_type == 'TIMELINE'
                and mod(".ui.time_slider").has_slider_panel(a.spaces.active))


def header(area):
    return next(r for r in area.regions if r.type == 'HEADER')


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


def main_hwnd():
    u32 = ctypes.WinDLL("user32", use_last_error=True)
    found = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, wt.HWND, wt.LPARAM)
    def each(h, _lp):
        pid = wt.DWORD()
        u32.GetWindowThreadProcessId(h, ctypes.byref(pid))
        if pid.value == os.getpid() and u32.IsWindowVisible(h):
            r = wt.RECT()
            u32.GetClientRect(h, ctypes.byref(r))
            found.append((h, r.right - r.left, r.bottom - r.top))
        return True

    u32.EnumWindows(each, 0)
    w = win()
    match = [h for h, cw, ch in found if abs(cw - w.width) <= 2 and abs(ch - w.height) <= 2]
    return match[0] if match else None


def size_window(width):
    hwnd = main_hwnd()
    if hwnd is None:
        return False
    u32 = ctypes.WinDLL("user32", use_last_error=True)
    SWP_NOZORDER, SWP_NOACTIVATE = 0x0004, 0x0010
    return bool(u32.SetWindowPos(hwnd, None, 0, 0, width, round(width * 9 / 16), SWP_NOZORDER | SWP_NOACTIVATE))


@step
def s_setup():
    setup()
    prefs = bpy.context.preferences
    C["view0"] = prefs.view.ui_scale
    C["base"] = prefs.system.ui_scale / prefs.view.ui_scale      # the display's own scale


def case(width, scale, frames=None):
    tag = f"{width} px, UI {scale}" + (f", frames {frames[0]}-{frames[1]}" if frames else "")

    @step
    def size():
        if C.get("width") != width:
            check(f"{width} px: the OS sized the window", size_window(width))
            C["width"] = width
        bpy.context.preferences.view.ui_scale = scale / C["base"]
        redraw()

    @step
    def load():
        load_maya_layout()
        if frames:
            sc = bpy.context.scene
            sc.frame_start, sc.frame_end = frames
            sc.frame_set(frames[0])
        redraw()

    for _i in range(5):
        step(redraw)

    @step
    def hover():
        area = slider()
        hdr = header(area)
        unit = 20 * bpy.context.preferences.system.ui_scale
        C["probe"] = (hdr.x + hdr.width - round(unit * 0.6), hdr.y + hdr.height // 2)
        ev('MOUSEMOVE', 'NOTHING', x=C["probe"][0], y=C["probe"][1])

    @step
    def look():
        area = slider()
        hdr = header(area)
        _path, cmd = button_under_mouse(area, hdr)
        units = hdr.width / (20 * bpy.context.preferences.system.ui_scale)
        print(f"GUI INFO {tag}: window {win().width} px, header {hdr.width} px = {units:.1f} units, "
              f"right edge button {cmd!r}", flush=True)
        check(f"{tag}: the go-to-end button sits at the row's right edge ({cmd!r})",
              "frame_jump" in (cmd or "") and "end=True" in (cmd or ""))
        bar = mod(".ui.range_bar")._bars.get(area.as_pointer())
        check(f"{tag}: the range bar is drawn in the row ({bar and (bar['x0'], bar['x1'])}, {hdr.width} px)",
              bar is not None and 0 <= bar["x0"] < bar["x1"] <= hdr.width)
        th = mod(".ui.time_slider_header")
        sc = bpy.context.scene
        s = bpy.context.preferences.system.ui_scale
        with bpy.context.temp_override(window=win(), area=area, region=hdr):
            plan = th._row_plan(bpy.context)
        need = th.field_floor((sc.frame_start, sc.frame_end, sc.frame_current), s)
        check(f"{tag}: the fields keep room for their numbers ({plan[2]:.2f} >= {need:.2f} units, icons x"
              f"{plan[3]:.2f}, current time field {plan[4]:.2f})",
              plan[2] >= need - 1e-6 and plan[3] >= th.ICON_FLOOR - 1e-6 and (plan[4] == 0 or plan[4] >= need - 1e-6))
        if width >= 1600 or scale < 2.0:
            check(f"{tag}: the current time field is shown ({plan[4]:.2f} units)", plan[4] > 0)
        if SHOTS:
            name = f"{width}_{scale}" + (f"_{frames[0]}" if frames else "")
            screenshot(os.path.join(SHOTS, f"gui_time_slider_row_fit_{name}.png"))
        ev('MOUSEMOVE', 'NOTHING', x=hdr.x + hdr.width // 2, y=hdr.y + hdr.height + 20)


for _w in WIDTHS:
    for _s in SCALES:
        case(_w, _s)
for _w in (1280, 1600):           # four-digit frame numbers (a shot range) in the narrowest rows
    case(_w, 2.0, (1001, 1250))


@step
def s_restore():
    bpy.context.preferences.view.ui_scale = C["view0"]
    size_window(1600)


run()
