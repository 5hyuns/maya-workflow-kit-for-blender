"""In a real UI (#450): asking for a kit editor window that is already open brings it to the front, like Maya.

The Shelf Editor and the Hotkey Editor are opened, the main window is put in front of them (Windows only: through
the OS, else the order is not checked), then the Shelf Editor, the Hotkey Editor, the Hypergraph (its pan and zoom
kept) and the Reference Editor are asked for again: each shows in a new window on top, at the same place and size,
the same editor, the old window closed, the other windows untouched, and nothing reopens again by itself."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, run, setup, step, win, load_maya_layout  # noqa: E402

GUI_TIMEOUT = 240
C = {}
SLACK = 2           # px a reopened window may differ from the old one


def rect(w):
    return (w.x, w.y, w.width, w.height)


# --- the OS window order (Windows only; as in gui_issue417_float_front.py) ---------------------------------------

def _user32():
    if sys.platform != "win32":
        return None
    import ctypes
    return ctypes.windll.user32


def _hwnds():
    """Visible top-level windows of this process with their client rect in Blender's screen px (bottom-left)."""
    import ctypes
    from ctypes import wintypes
    user32 = _user32()
    pid = os.getpid()
    screen_h = user32.GetSystemMetrics(1)
    out = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    def each(hwnd, _lparam):
        owner = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
        if owner.value == pid and user32.IsWindowVisible(hwnd):
            r = wintypes.RECT()
            user32.GetClientRect(hwnd, ctypes.byref(r))
            p = wintypes.POINT(0, 0)
            user32.ClientToScreen(hwnd, ctypes.byref(p))
            out.append((hwnd, (p.x, screen_h - p.y - r.bottom, r.right, r.bottom)))
        return True
    user32.EnumWindows(each, 0)
    return out


def hwnd_of(window):
    """The OS window of a Blender window: the one with its size whose place is nearest (None if unsure)."""
    want = rect(window)
    best = None
    for hwnd, r in _hwnds():
        if abs(r[2] - want[2]) <= 2 and abs(r[3] - want[3]) <= 2:
            d = abs(r[0] - want[0]) + abs(r[1] - want[1])
            if best is None or d < best[0]:
                best = (d, hwnd)
    return best[1] if best is not None and best[0] <= 40 else None


def above(a, b):
    """True when OS window ``a`` is above ``b`` (EnumWindows lists top-level windows top to bottom)."""
    order = [h for h, _r in _hwnds()]
    return a in order and b in order and order.index(a) < order.index(b)


def main_to_front():
    """Put the main window above every other window. True when the OS did it."""
    user32 = _user32()
    if user32 is None:
        return False
    main = hwnd_of(win())
    if main is None:
        return False
    user32.SetWindowPos(main, 0, 0, 0, 0, 0, 0x0013)     # HWND_TOP, SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE
    user32.SetForegroundWindow(main)
    return all(above(main, hwnd_of(w)) for w in wm().windows if w != win() and hwnd_of(w) is not None)


def top_check(label, w):
    """Windows: the reopened window is the top one of Blender's windows."""
    if _user32() is None:
        return
    mine = [hwnd_of(x) for x in wm().windows]
    new_h = hwnd_of(w)
    if new_h is None or None in mine:
        print(f"GUI note: {label}: OS windows not matched, the order is not checked", flush=True)
        return
    order = [h for h, _r in _hwnds() if h in mine]
    check(f"{label}: the new window is the top Blender window ({order.index(new_h)} of {len(order)})",
          order and order[0] == new_h)


def mod(name):
    return import_module(MODULE + name)


def mw():
    return mod(".ui.marked_window")


def wm():
    return bpy.context.window_manager


def redraw():
    for w in wm().windows:
        for a in w.screen.areas:
            a.tag_redraw()


def snapshot():
    return {w.as_pointer(): rect(w) for w in wm().windows}


def v3d():
    area = max((a for a in win().screen.areas if a.type == 'VIEW_3D'), key=lambda a: a.width * a.height)
    return area, next(r for r in area.regions if r.type == 'WINDOW')


def in_v3d(fn, *a, **kw):
    area, region = v3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        return fn(*a, **kw)


EDITORS = {     # name -> (operator, the editor's window)
    "Shelf Editor": ("shelf_editor_open", lambda: mw().find_window(bpy.context, mod(".ui.shelf_editor").KIND)),
    "Hotkey Editor": ("hotkey_editor", lambda: mw().find_window(bpy.context, mod(".ui.hotkey_editor").KIND)),
    "Hypergraph": ("hypergraph", lambda: mw().find_window(bpy.context, mod(".ui.hypergraph").KIND)),
    "Reference Editor": ("reference_editor", lambda: mod(".ui.reference_editor").find_window(bpy.context)),
}


def is_editor(name, window):
    area = window.screen.areas[0]
    if name == "Reference Editor":
        return mod(".ui.reference_editor").is_pane(area)
    return mw().kind_of(area) is not None and window == EDITORS[name][1]()


def open_step(name):
    def f():
        in_v3d(getattr(bpy.ops.allset, EDITORS[name][0]))
    f.__name__ = "open_" + name
    return f


def ask_step(name):
    def f():
        w = EDITORS[name][1]()
        check(f"the {name} is open", w is not None)
        if w is None:
            C[name] = None
            return
        others = {p: r for p, r in snapshot().items() if p != w.as_pointer()}
        C[name] = (w.as_pointer(), rect(w), others, main_to_front())
        if name == "Hypergraph":
            area = w.screen.areas[0]
            view = mod(".ui.hypergraph").VIEWS.get(area.as_pointer())
            C["view"] = view
            check("the Hypergraph has a view", view is not None)
        in_v3d(getattr(bpy.ops.allset, EDITORS[name][0]))
    f.__name__ = "ask_" + name
    return f


def check_step(name):
    def f():
        if C.get(name) is None:
            return
        old_ptr, old_rect, others, os_order = C[name]
        w = EDITORS[name][1]()
        now = snapshot()
        check(f"{name}: asked again, it shows in a new window, the old one closed "
              f"({w is not None and w.as_pointer() != old_ptr}, {old_ptr not in now})",
              w is not None and w.as_pointer() != old_ptr and old_ptr not in now)
        if w is None:
            return
        check(f"{name}: same place and size {rect(w)} vs {old_rect}",
              all(abs(a - b) <= SLACK for a, b in zip(rect(w), old_rect)))
        check(f"{name}: the window still shows the {name} alone",
              len(w.screen.areas) == 1 and is_editor(name, w))
        check(f"{name}: the other windows are untouched",
              all(now.get(p) == r for p, r in others.items()) and len(now) == len(others) + 1)
        if os_order:
            check(f"{name}: the new window is above the main window", above(hwnd_of(w), hwnd_of(win())))
        top_check(name, w)
        if name == "Hypergraph":
            view = mod(".ui.hypergraph").VIEWS.get(w.screen.areas[0].as_pointer())
            check("the Hypergraph keeps its pan and zoom", view is not None and view is C["view"])
        C["stable"] = snapshot()
    f.__name__ = "check_" + name
    return f


@step
def s_setup():
    setup()
    load_maya_layout()


for _i in range(6):        # the layout is fitted to the UI scale in the first seconds after a load
    step(redraw)

for _name in EDITORS:
    step(open_step(_name))
    for _i in range(5):    # a window may first carve its remembered place (a few ticks)
        step(redraw)


@step
def s_all_open():
    for name, (_op, find) in EDITORS.items():
        check(f"{name} opened", find() is not None)


for _name in ("Shelf Editor", "Hotkey Editor", "Shelf Editor", "Hypergraph", "Reference Editor"):
    step(ask_step(_name))
    step(redraw)
    step(redraw)
    step(check_step(_name))
    step(redraw)


step(redraw)
step(redraw)


@step
def s_no_loop():
    check("nothing reopens by itself while the windows redraw", snapshot() == C.get("stable"))


run()
