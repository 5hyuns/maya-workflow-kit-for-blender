"""#334: windows on monitors with different display scaling. Blender keeps one UI scale for all its windows and sets
it to a window's own each time that window draws or moves, so a timer reads the scale of whichever window drew last.
Here the Graph Editor window (Windows > Animation Editors > Graph Editor) is opened as a window Windows scales from
100 % (made DPI-unaware) while the main window has the monitor's scaling: the same two scales as a Graph Editor on a
100 % monitor next to a main window on a 125 % one. While the two windows draw in turn, while the Graph Editor window
is dragged (the move state Windows gives a title-bar drag) and after it, the kit must not refit the main window's Maya
layout for the Graph Editor's scale nor move the pointer to the main window. A change of the main window's own scale
is still fitted. Windows only; on a 100 % monitor both windows have the same scale and the file says so."""

import ctypes
import ctypes.wintypes as wt
import os
import sys
import threading
import time
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sim  # noqa: E402
from sim import MODULE, check, load_maya_layout, run, setup, step, view3d, win  # noqa: E402

GUI_TIMEOUT = 300
u32 = ctypes.WinDLL("user32", use_last_error=True)
u32.SetThreadDpiAwarenessContext.restype = ctypes.c_void_p
u32.SetThreadDpiAwarenessContext.argtypes = [ctypes.c_void_p]
u32.GetDpiForWindow.argtypes = [wt.HWND]
u32.GetDpiForWindow.restype = ctypes.c_uint
u32.SendMessageW.argtypes = [wt.HWND, ctypes.c_uint, wt.WPARAM, wt.LPARAM]
u32.SetWindowPos.argtypes = [wt.HWND, wt.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint]
DPI_UNAWARE = -1
WM_ENTERSIZEMOVE, WM_EXITSIZEMOVE = 0x0231, 0x0232
SWP_NOSIZE, SWP_NOZORDER, SWP_NOACTIVATE = 0x0001, 0x0004, 0x0010
C = {"warps": [], "moves": [], "scales": [], "drag_ms": []}


def mod(name):
    return import_module(MODULE + name)


def others():
    return [w for w in bpy.context.window_manager.windows if w != win()]


def os_windows():
    """(handle, rect, DPI) of this process's visible top-level windows wider than 200 px, smallest first."""
    found = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, wt.HWND, wt.LPARAM)
    def each(h, _lp):
        pid = wt.DWORD()
        u32.GetWindowThreadProcessId(h, ctypes.byref(pid))
        if pid.value == os.getpid() and u32.IsWindowVisible(h):
            r = wt.RECT()
            u32.GetWindowRect(h, ctypes.byref(r))
            if r.right - r.left > 200:
                found.append((h, (r.left, r.top, r.right, r.bottom), u32.GetDpiForWindow(h)))
        return True
    u32.EnumWindows(each, 0)
    return sorted(found, key=lambda f: (f[1][2] - f[1][0]) * (f[1][3] - f[1][1]))


def layout():
    return sorted((a.type, a.x, a.y, a.width, a.height) for a in win().screen.areas)


def column():
    return next(a for a in win().screen.areas if a.type == 'VIEW_3D' and mod(".ui.toolbox_column").is_toolbox(a.spaces.active))


def phase(name):
    C["phase"] = name


@step
def s_setup():
    setup()
    load_maya_layout()
    os.environ["ALLSET_FIT_WARP"] = "1"         # the cursor fit as in a real session
    lf = mod(".ui.layout_fit")
    warp, move_edge, fit = lf._warp, lf._move_edge, lf.fit_columns

    def warp_log(window, x, y):
        C["warps"].append((C.get("phase"), window.as_pointer() == win().as_pointer(), x, y))
        return warp(window, x, y)

    def move_log(window, area, x, y, delta, edge, pending):
        if window.as_pointer() == win().as_pointer():
            C["moves"].append((C.get("phase"), area.type, delta))
        return move_edge(window, area, x, y, delta, edge, pending)

    def fit_log(start_fit=True):
        if start_fit:
            C["scales"].append((C.get("phase"), bpy.context.preferences.system.ui_scale))
        return fit(start_fit)
    lf._warp, lf._move_edge, lf.fit_columns = warp_log, move_log, fit_log
    wp = mod(".ui.window_places")
    wp.place("")
    wp._places.clear()          # no remembered place: the window opens at once
    phase("load")


for _i in range(10):            # 4 s: the layout's own load fit is over (3 s)
    step(lambda: None)


@step
def s_open():
    prev = u32.SetThreadDpiAwarenessContext(ctypes.c_void_p(DPI_UNAWARE))
    try:
        area, region = view3d()
        with bpy.context.temp_override(window=win(), area=area, region=region):
            bpy.ops.allset.open_editor(ui_type='FCURVES')
    finally:
        if prev:
            u32.SetThreadDpiAwarenessContext(ctypes.c_void_p(prev))


for _i in range(3):
    step(lambda: None)


@step
def s_scales():
    check("Graph Editor opened one window", len(others()) == 1)
    found = os_windows()
    C["dpi"] = sorted({f[2] for f in found})
    C["mixed"] = len(found) == 2 and found[0][2] != found[1][2]
    print(f"GUI INFO window DPIs (Graph Editor, main): {[f[2] for f in found]}", flush=True)
    if C["mixed"]:
        C["hwnd"] = found[0][0]
        r = found[0][1]          # Windows resizes a window that crosses to another scaling (warp fits allowed again)
        u32.SetWindowPos(C["hwnd"], None, r[0], r[1], r[2] - r[0] - 60, r[3] - r[1] - 40, SWP_NOZORDER | SWP_NOACTIVATE)
    C["layout"] = layout()
    phase("idle")


def in_turn(i):
    """The user works in the Graph Editor window, then in the main window, and so on: each draws in turn."""
    def f():
        if not others():
            return
        if i % 2 == 0:
            others()[0].screen.areas[0].tag_redraw()
        else:
            view3d()[0].tag_redraw()
    return f


for _i in range(20):
    step(in_turn(_i))


def report(name):
    scales = sorted({s for p, s in C["scales"] if p == name})
    moves = [m for m in C["moves"] if m[0] == name]
    warps = [w for w in C["warps"] if w[0] == name]
    print(f"GUI INFO {name}: UI scales the fit saw {scales}, main-window edge moves {moves}, warps {warps}", flush=True)
    return scales, moves, warps


@step
def s_idle_check():
    if not C["mixed"]:
        check(f"two windows of different scaling (both {C['dpi']} DPI here: monitor at 100 %, not checked)", True)
        return
    scales, moves, warps = report("idle")
    check(f"the fit saw both windows' UI scales ({scales})", len(scales) == 2)
    check("the main window's layout is not refitted for the Graph Editor window's scale", not moves)
    check("the pointer is never moved to the main window", not warps)
    check("the main window's layout keeps its sizes", layout() == C["layout"])
    phase("drag")

    def drag():
        h = C["hwnd"]
        r = wt.RECT()
        u32.GetWindowRect(h, ctypes.byref(r))
        u32.SendMessageW(h, WM_ENTERSIZEMOVE, 0, 0)       # Windows' move state, as in a title-bar drag
        for i in range(60):                                 # 2400 px to the right, over to the next monitor
            t0 = time.perf_counter()
            u32.SetWindowPos(h, None, r.left + 40 * i, r.top + 2 * (i % 3), 0, 0,
                             SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE)
            C["drag_ms"].append((time.perf_counter() - t0) * 1000)
            time.sleep(0.016)
        u32.SendMessageW(h, WM_EXITSIZEMOVE, 0, 0)
        C["dragged"] = True
    threading.Thread(target=drag, daemon=True).start()


@step
def s_wait_drag():
    """The drag thread moves the window meanwhile (a few seconds; one move can take a second): wait until it is
    done, at most 60 ticks."""
    C["wait"] = C.get("wait", 0) + 1
    if C.get("mixed") and not C.get("dragged") and C["wait"] < 60:
        sim._steps.insert(0, s_wait_drag)


@step
def s_drag_check():
    if not C["mixed"]:
        return
    ms = sorted(C["drag_ms"])
    if ms:
        print(f"GUI INFO one move during the drag: median {ms[len(ms) // 2]:.1f} ms, max {ms[-1]:.1f} ms", flush=True)
    check("the drag moved the Graph Editor window 60 times", C.get("dragged") and len(ms) == 60)
    _scales, moves, warps = report("drag")
    check("no main-window refit and no pointer warp during the drag", not moves and not warps)
    phase("after")


for _i in range(12):
    step(in_turn(_i))


@step
def s_after_check():
    if not C["mixed"]:
        return
    _scales, moves, warps = report("after")
    check("no main-window refit and no pointer warp after the drag", not moves and not warps)
    check("the main window's layout still keeps its sizes", layout() == C["layout"])
    phase("rescale")
    C["scale0"] = bpy.context.preferences.view.ui_scale
    bpy.context.preferences.view.ui_scale = C["scale0"] * 0.8     # the main window's own scale changes too


for _i in range(14):
    step(in_turn(_i))


@step
def s_rescale_check():
    if not C["mixed"]:
        return
    lf = mod(".ui.layout_fit")
    own = lf._drawn.get(win().as_pointer())
    want = None
    if own is not None:
        tc = mod(".ui.toolbox_column")
        want = round(tc.TOOLBAR_PX * own[0]) + tc.RETINA_EXTRA_PX * max(0, int(own[1]) - 1)
    report("rescale")
    print(f"GUI INFO main window's own scale {own}, Tool Box column {column().width} px (fitted: {want})", flush=True)
    check("the main window's own scale change is still fitted (Tool Box column one toolbar column wide)",
          want is not None and abs(column().width - want) <= 1)
    bpy.context.preferences.view.ui_scale = C["scale0"]
    os.environ.pop("ALLSET_FIT_WARP", None)


run()
