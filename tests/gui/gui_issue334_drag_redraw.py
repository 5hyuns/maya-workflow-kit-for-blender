"""#334: while a window is dragged, Blender redraws every window at each step of the drag. The Maya layout's dock tint
(the Layer Editor list left unlifted) and the Time Slider's Range Slider find their place in the drawn pixels, and a
framebuffer read waits for the GPU: at a drag step nothing in the main window moved, so they use what they found at
their previous draw and read nothing. A redraw of the main window outside a drag still reads, finds the same Layer
Editor list, and draws the same Range Slider. Windows only (the drag is the move state Windows gives a title-bar
drag)."""

import ctypes
import ctypes.wintypes as wt
import os
import sys
import threading
import time
from importlib import import_module

import bpy
import gpu

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sim  # noqa: E402
from sim import MODULE, check, load_maya_layout, run, setup, step, view3d, win  # noqa: E402

GUI_TIMEOUT = 300
u32 = ctypes.WinDLL("user32", use_last_error=True)
u32.SendMessageW.argtypes = [wt.HWND, ctypes.c_uint, wt.WPARAM, wt.LPARAM]
u32.SetWindowPos.argtypes = [wt.HWND, wt.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint]
WM_ENTERSIZEMOVE, WM_EXITSIZEMOVE = 0x0231, 0x0232
SWP_NOSIZE, SWP_NOZORDER, SWP_NOACTIVATE = 0x0001, 0x0004, 0x0010
MOVES = 30
C = {"reads": 0, "draws": 0, "holes": [], "bars": []}
_framebuffer = gpu.state.active_framebuffer_get


class _Counted:
    """The active framebuffer, counting its reads."""

    def __init__(self, fb):
        self._fb = fb

    def read_color(self, *args, **kw):
        C["reads"] += 1
        return self._fb.read_color(*args, **kw)

    def __getattr__(self, name):
        return getattr(self._fb, name)


def mod(name):
    return import_module(MODULE + name)


def others():
    return [w for w in bpy.context.window_manager.windows if w != win()]


def graph_hwnd():
    """The OS handle of the Graph Editor window: this process's smallest visible top-level window."""
    found = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, wt.HWND, wt.LPARAM)
    def each(h, _lp):
        pid = wt.DWORD()
        u32.GetWindowThreadProcessId(h, ctypes.byref(pid))
        if pid.value == os.getpid() and u32.IsWindowVisible(h):
            r = wt.RECT()
            u32.GetWindowRect(h, ctypes.byref(r))
            if r.right - r.left > 200:
                found.append(((r.right - r.left) * (r.bottom - r.top), h))
        return True
    u32.EnumWindows(each, 0)
    return min(found)[1] if len(found) == 2 else None


def bar():
    """The Range Slider as last drawn (x0, x1, y0, y1) of the main window's Time Slider."""
    for b in mod(".ui.range_bar")._bars.values():
        if b["window"] == win().as_pointer():
            return tuple(round(b[k]) for k in ("x0", "x1", "y0", "y1"))
    return None


def redraw_main():
    for a in win().screen.areas:
        a.tag_redraw()


@step
def s_setup():
    setup()
    load_maya_layout()
    gpu.state.active_framebuffer_get = lambda: _Counted(_framebuffer())
    tint = mod(".ui.maya_dock_tint")
    C["kept"] = tint._kept_hole

    def kept(context, region):
        hole = C["kept"](context, region)
        if context.window is not None and context.window.as_pointer() == win().as_pointer():
            C["draws"] += 1
            C["holes"].append(hole)
            C["bars"].append(bar())
        return hole
    tint._kept_hole = kept
    mod(".ui.window_places")._places.clear()     # no remembered place: the window opens at once
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.allset.open_editor(ui_type='FCURVES')


for _i in range(8):
    step(lambda: None)


@step
def s_before():
    check("Graph Editor opened one window", len(others()) == 1)
    C["reads"], C["draws"] = 0, 0
    C["holes"].clear()
    redraw_main()


@step
def s_drag():
    check(f"a redraw of the main window outside a drag reads its pixels ({C['reads']} reads, {C['draws']} dock draws)",
          C["reads"] >= 1 and C["draws"] >= 1)
    C["hole0"] = C["holes"][-1] if C["holes"] else None
    C["bar0"] = bar()
    check(f"the dock found the Layer Editor list {C['hole0']} and the Range Slider is drawn {C['bar0']}",
          C["hole0"] is not None and C["bar0"] is not None)
    C["reads"], C["draws"] = 0, 0
    C["holes"].clear()
    C["bars"].clear()
    h = graph_hwnd()
    check("the Graph Editor window's OS handle", h is not None)
    if h is None:
        C["dragged"] = True
        return

    def drag():
        r = wt.RECT()
        u32.GetWindowRect(h, ctypes.byref(r))
        u32.SendMessageW(h, WM_ENTERSIZEMOVE, 0, 0)       # Windows' move state, as in a title-bar drag
        for i in range(MOVES):
            u32.SetWindowPos(h, None, r.left + 12 * (i + 1), r.top + 2 * (i % 3), 0, 0,
                             SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE)
            time.sleep(0.016)
        u32.SendMessageW(h, WM_EXITSIZEMOVE, 0, 0)
        C["dragged"] = True
    threading.Thread(target=drag, daemon=True).start()


@step
def s_wait_drag():
    """The drag thread moves the window meanwhile: wait until it is done, at most 60 ticks."""
    C["wait"] = C.get("wait", 0) + 1
    if not C.get("dragged") and C["wait"] < 60:
        sim._steps.insert(0, s_wait_drag)


@step
def s_drag_check():
    reads, draws = C["reads"], C["draws"]
    print(f"GUI INFO drag: {MOVES} moves, {draws} main-window dock draws, {reads} framebuffer reads", flush=True)
    check(f"the main window redrew during the drag ({draws} dock draws)", draws >= MOVES // 2)
    check(f"no framebuffer read at the drag steps ({reads} reads)", reads == 0)
    check("the dock kept the Layer Editor list where it was found",
          C["holes"] and all(hole == C["hole0"] for hole in C["holes"]))
    check("the Range Slider stays where it was drawn", all(b == C["bar0"] for b in C["bars"]))
    C["reads"], C["draws"] = 0, 0
    C["holes"].clear()
    redraw_main()


@step
def s_after():
    check(f"after the drag a redraw reads again ({C['reads']} reads) and finds the same list and Range Slider",
          C["reads"] >= 1 and C["holes"] and C["holes"][-1] == C["hole0"] and bar() == C["bar0"])
    gpu.state.active_framebuffer_get = _framebuffer
    mod(".ui.maya_dock_tint")._kept_hole = C["kept"]
    for x in others():
        with bpy.context.temp_override(window=x):
            bpy.ops.wm.window_close()


run()
