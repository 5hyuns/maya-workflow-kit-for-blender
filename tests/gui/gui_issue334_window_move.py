"""#334: a kit window (Windows > Animation Editors > Graph Editor) moved to another monitor stays there. The kit
cannot move a window and never tries: once the window is open, the only thing the kit does with it is read its place
for the next time. Here the window is moved through the OS (Windows only), as a title-bar drag ends; then no
window opens or closes, the window is where the OS put it, the remembered and saved place is that place, and a
reopen (which can only land over the Blender window) carves its place once and leaves the main layout as it was."""
import ctypes
import ctypes.wintypes as wt
import json
import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, run, setup, step, view3d, win  # noqa: E402

C = {}
MON2_X = 2048          # left edge of a second monitor to the right (off the first monitor on a single screen too)
TOL = 4


def mod(name):
    return import_module(MODULE + name)


def wp():
    return mod(".ui.window_places")


def live():
    return mod(".live_refs")


def others():
    return [w for w in bpy.context.window_manager.windows if w != win()]


def rect(w):
    return (w.x, w.y, w.width, w.height)


def layout():
    return sorted((a.type, a.x, a.y, a.width, a.height) for a in win().screen.areas)


def in_view(fn, **kw):
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        return fn(**kw)


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


def move_by_os(window, x, y, w, h):
    hwnd = hwnd_of(window)
    if hwnd is None:
        return False
    u32 = ctypes.WinDLL("user32", use_last_error=True)
    SWP_NOZORDER, SWP_NOACTIVATE = 0x0004, 0x0010
    return bool(u32.SetWindowPos(hwnd, None, x, y, w, h, SWP_NOZORDER | SWP_NOACTIVATE))


def saved_place():
    p = wp().path()
    try:
        with open(p, encoding="utf-8") as fh:
            return json.load(fh).get("editor:FCURVES")
    except (OSError, ValueError, TypeError):
        return None


@step
def s_setup():
    setup()
    C["layout"] = layout()
    w = wp()
    w.place("")                   # loads the places earlier files saved ...
    w._places.clear()             # ... and forgets them: the first open copies the viewport area at once
    C["before"] = {x.as_pointer() for x in bpy.context.window_manager.windows}
    in_view(bpy.ops.allset.open_editor, ui_type='FCURVES')


for _i in range(3):
    step(lambda: None)


@step
def s_move():
    new = others()
    check("Graph Editor opened one window", len(new) == 1)
    if not new:
        return
    C["ptr"] = new[0].as_pointer()
    C["rect0"] = rect(new[0])
    C["moved"] = move_by_os(new[0], MON2_X + 120, 80, 900, 600)
    check("the OS moved it to the second monitor", C["moved"])


for _i in range(6):       # 2.4 s: the place timer (0.5 s) looks at the window several times
    step(lambda: None)


@step
def s_stays():
    w = live().window(C.get("ptr"))
    check("the window is still open and no other window opened", w is not None and len(others()) == 1)
    if w is None:
        return
    r = rect(w)
    check(f"it stays where the OS put it {r} (was {C['rect0']})", r[0] >= MON2_X and r != C["rect0"])
    check(f"the kit remembers that place ({wp().place('editor:FCURVES')})", wp().place("editor:FCURVES") == list(r))
    check(f"and saved it ({saved_place()})", saved_place() == list(r))
    C["rect1"] = r


for _i in range(6):       # 2.4 s more
    step(lambda: None)


@step
def s_still_there():
    w = live().window(C.get("ptr"))
    check("5 s later nothing moved it back or reopened it",
          w is not None and rect(w) == C.get("rect1") and len(others()) == 1)
    for x in others():
        with bpy.context.temp_override(window=x):
            bpy.ops.wm.window_close()


@step
def s_reopen():
    check("the place on the other monitor stays remembered after the close",
          wp().place("editor:FCURVES") == list(C.get("rect1", ())))
    w = wp()
    C["carves"] = 0
    C["Carve"] = w._Carve

    class Counting(w._Carve):
        def __init__(self, *a, **k):
            C["carves"] += 1
            super().__init__(*a, **k)

    w._Carve = Counting
    C["before"] = {x.as_pointer() for x in bpy.context.window_manager.windows}
    in_view(bpy.ops.allset.open_editor, ui_type='FCURVES')


for _i in range(6):       # the place is carved one split per tick, then the window opens
    step(lambda: None)


@step
def s_reopened():
    wp()._Carve = C["Carve"]
    new = others()
    check(f"reopened once: one window, the place applied once ({C['carves']} carve)", len(new) == 1 and C["carves"] == 1)
    if new:
        w, m = new[0], win()
        inside = m.x <= w.x and w.x + w.width <= m.x + m.width and m.y <= w.y and w.y + w.height <= m.y + m.height
        check(f"it comes back over the Blender window {rect(w)} at the size it had", inside
              and abs(w.width - C["rect1"][2]) <= TOL and abs(w.height - C["rect1"][3]) <= TOL)
    check("main layout as before", layout() == C["layout"])
    for x in new:
        with bpy.context.temp_override(window=x):
            bpy.ops.wm.window_close()


run()
