"""#334: the kit never moves the mouse pointer while a window is being dragged. In the Maya layout (the cursor fit of
the layout on, as in a real session) a Graph Editor window (Windows > Animation Editors > Graph Editor) is moved by
the OS step by step, like a title-bar drag towards a monitor with other display scaling: when it crosses, Blender's
UI scale changes (here: the Resolution Scale) and the window is resized. While the window keeps moving the kit warps
the pointer nowhere; once every window stands still it fits the Maya layout to the new scale (which may use the
pointer). Windows only (the OS moves the window)."""

import ctypes
import ctypes.wintypes as wt
import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, load_maya_layout, run, setup, step, view3d, win  # noqa: E402

GUI_TIMEOUT = 300
C = {"warps": []}


def mod(name):
    return import_module(MODULE + name)


def others():
    return [w for w in bpy.context.window_manager.windows if w != win()]


def hwnd_of(window):
    """The OS handle of ``window``: this process's visible top-level window with the same client size."""
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
    match = [h for h, w, hgt in found if abs(w - window.width) <= 2 and abs(hgt - window.height) <= 2]
    return match[0] if len(match) == 1 else None


def move_by_os(hwnd, x, y, w, h):
    u32 = ctypes.WinDLL("user32", use_last_error=True)
    SWP_NOZORDER, SWP_NOACTIVATE = 0x0004, 0x0010
    return bool(u32.SetWindowPos(hwnd, None, x, y, w, h, SWP_NOZORDER | SWP_NOACTIVATE))


@step
def s_setup():
    setup()
    load_maya_layout()
    os.environ["ALLSET_FIT_WARP"] = "1"         # the cursor fit as in a real session
    lf = mod(".ui.layout_fit")
    orig = lf._warp

    def warp(window, x, y):
        C["warps"].append((C.get("phase"), window.as_pointer() == win().as_pointer(), x, y))
        return orig(window, x, y)
    lf._warp = warp
    wp = mod(".ui.window_places")
    wp.place("")
    wp._places.clear()          # no remembered place: the window opens at once
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.allset.open_editor(ui_type='FCURVES')


for _i in range(10):            # 4 s: the layout's own load fit is over (3 s)
    step(lambda: None)


@step
def s_start():
    new = others()
    check("Graph Editor opened one window", len(new) == 1)
    C["hwnd"] = hwnd_of(new[0]) if new else None
    check("its OS window is found", C["hwnd"] is not None)
    C["warps"].clear()
    C["phase"] = "drag"
    C["scale0"] = bpy.context.preferences.view.ui_scale


def drag_step(i):
    def move():
        if C.get("hwnd") is None:
            return
        if i == 3:              # the window crosses to the other monitor: Blender's UI scale and the size change
            bpy.context.preferences.view.ui_scale = C["scale0"] * 1.25
        size = (900, 600) if i < 3 else (1125, 750)
        move_by_os(C["hwnd"], 200 + 180 * i, 80 + 10 * i, *size)
    return move


for _i in range(12):            # 12 moves 0.4 s apart: a drag that goes on well past the scale change
    step(drag_step(_i))


@step
def s_drag_check():
    during = [w for w in C["warps"] if w[0] == "drag"]
    check(f"no pointer warp while the window is being dragged ({during})", not during)
    C["phase"] = "still"


for _i in range(10):            # the window stands still: the layout may be fitted now
    step(lambda: None)


@step
def s_still_check():
    still = [w for w in C["warps"] if w[0] == "still"]
    print(f"GUI INFO warps once the windows stood still: {still}", flush=True)
    w = others()[0] if others() else None
    check("the Graph Editor window is still open", w is not None)
    lf = mod(".ui.layout_fit")
    with bpy.context.temp_override(window=win()):
        left = lf.fit_columns(start_fit=False)
    print(f"GUI INFO edges still to fit: {[e for _w, e in left.values()]}", flush=True)
    check(f"once the windows stand still the layout is fitted to the new scale (edges left {len(left)})",
          not left)
    bpy.context.preferences.view.ui_scale = C["scale0"]
    os.environ.pop("ALLSET_FIT_WARP", None)


run()
