"""In a real UI (#417): asking for a panel that already floats brings its window to the front, like Maya.

The Channel Box and the Attribute Editor are torn off the tab stack, the main window is put in front of them (Windows
only: through the OS, else the order is not checked), then Windows > General Editors > Channel Box / Layer Editor,
Ctrl+A (twice) and the Status Line's show-only path each give the panel a new window on top: the same place and size,
the same panel, the old window closed, the other windows untouched, and nothing reopens again by itself. The Status
Line button still hides a shown panel (Maya's toggle), the raised window still docks back by its handle, and the
floating Tool Settings comes to the front from Windows > General Editors > Tool Settings and keeps its remembered
place."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, setup, step, win, load_maya_layout  # noqa: E402

GUI_TIMEOUT = 240
C = {}
SLACK = 2           # px a reopened window may differ from the old one


def mod(name):
    return import_module(MODULE + name)


def md():
    return mod(".ui.maya_dock")


def wm():
    return bpy.context.window_manager


def floating(kind):
    return md().floating_window(kind)


def rect(w):
    return (w.x, w.y, w.width, w.height)


def v3d():
    area = max((a for a in win().screen.areas if a.type == 'VIEW_3D'), key=lambda a: a.width * a.height)
    return area, next(r for r in area.regions if r.type == 'WINDOW')


def in_v3d(fn, *a, **kw):
    area, region = v3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        return fn(*a, **kw)


def redraw():
    for w in wm().windows:
        for a in w.screen.areas:
            a.tag_redraw()


# --- the OS window order (Windows only) --------------------------------------------------------------------------

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
    """Put the main window above every floating window. True when the OS did it."""
    user32 = _user32()
    if user32 is None:
        return False
    main = hwnd_of(win())
    if main is None:
        return False
    user32.SetWindowPos(main, 0, 0, 0, 0, 0, 0x0013)     # HWND_TOP, SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE
    user32.SetForegroundWindow(main)
    return all(above(main, hwnd_of(w)) for w in wm().windows if w != win() and hwnd_of(w) is not None)


# --- steps ---------------------------------------------------------------------------------------------------------

@step
def s_setup():
    setup()
    load_maya_layout()


for _i in range(6):        # the layout is fitted to the UI scale in the first seconds after a load
    step(redraw)


def tear(kind):
    wm().allset_dock = kind
    stack = md().find_stack(win().screen)
    region = next(r for r in stack.regions if r.type == 'WINDOW')
    with bpy.context.temp_override(window=win(), screen=win().screen, area=stack, region=region):
        bpy.ops.allset.dock_handle('EXEC_DEFAULT')


@step
def s_tear_cb():
    bpy.ops.allset.keymap_activate()
    C["main"] = win().as_pointer()
    tear('CHANNEL_BOX')


step(redraw)


@step
def s_tear_ae():
    check("the Channel Box floats", floating('CHANNEL_BOX') is not None)
    tear('ATTRIBUTE_EDITOR')


step(redraw)
step(redraw)


def snapshot():
    return {w.as_pointer(): rect(w) for w in wm().windows}


def raised(label, kind, old_ptr, old_rect, others):
    """Checks after asking for ``kind`` that floated in window ``old_ptr``."""
    w = floating(kind)
    now = snapshot()
    check(f"{label}: the {kind} shows in a new window, the old one closed "
          f"({old_ptr in now}, {w is not None and w.as_pointer() != old_ptr})",
          w is not None and w.as_pointer() != old_ptr and old_ptr not in now)
    if w is None:
        return None
    got = rect(w)
    check(f"{label}: same place and size {got} vs {old_rect}",
          all(abs(a - b) <= SLACK for a, b in zip(got, old_rect)))
    check(f"{label}: the panel is the same ({md().role(w.screen.areas[0])}), the window holds only it",
          md().role(w.screen.areas[0]) == kind and len(w.screen.areas) == 1)
    check(f"{label}: the other windows are untouched ({len(now)} windows)",
          all(now.get(p) == r for p, r in others.items()) and len(now) == len(others) + 1)
    if C.get("os_order"):
        new_h, main_h = hwnd_of(w), hwnd_of(win())
        check(f"{label}: the new window is above the main window ({new_h}, {main_h})",
              new_h is not None and main_h is not None and above(new_h, main_h))
    top_check(label, w)
    return w


def top_check(label, w):
    """Windows: the reopened window is the top one of Blender's windows (the OS lists them top to bottom)."""
    if _user32() is None:
        return
    mine = [hwnd_of(x) for x in wm().windows]
    print("GUI note: windows", [(rect(x), h) for x, h in zip(wm().windows, mine)], "os", _hwnds(), flush=True)
    new_h = hwnd_of(w)
    if new_h is None or None in mine:
        print(f"GUI note: {label}: OS windows not matched, the order is not checked", flush=True)
        return
    order = [h for h, _r in _hwnds() if h in mine]
    check(f"{label}: the new window is the top Blender window ({order.index(new_h)} of {len(order)})",
          order and order[0] == new_h)


def ask(kind):
    """Record the floating ``kind``'s window and the others, put the main window in front."""
    w = floating(kind)
    C["old"] = (w.as_pointer(), rect(w)) if w is not None else (0, None)
    C["others"] = {p: r for p, r in snapshot().items() if p != C["old"][0]}
    C["os_order"] = main_to_front()
    if C["os_order"]:
        check(f"the main window is in front of the floating {kind}", True)


@step
def s_menu_cb():
    check("the Attribute Editor floats too, the main window is the same",
          floating('ATTRIBUTE_EDITOR') is not None and win().as_pointer() == C["main"])
    ask('CHANNEL_BOX')
    if not C["os_order"]:
        print("GUI note: the OS window order is not checked here", flush=True)
    in_v3d(bpy.ops.allset.menu_item, item="Windows/General Editors/Channel Box / Layer Editor")


step(redraw)


@step
def s_menu_cb_check():
    raised("Windows > General Editors > Channel Box", 'CHANNEL_BOX', *C["old"], C["others"])
    C["stable"] = snapshot()


step(redraw)
step(redraw)
step(redraw)


@step
def s_no_loop():
    check("nothing reopens by itself while the windows redraw", snapshot() == C["stable"])
    # Ctrl+A over the viewport: the dock's tab is the Channel Box now, so the Attribute Editor is asked for
    ask('ATTRIBUTE_EDITOR')
    _area, region = v3d()
    x, y = region.x + region.width // 2, region.y + region.height // 2
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('LEFT_CTRL', 'PRESS', x=x, y=y)
    ev('A', 'PRESS', x=x, y=y, ctrl=True)
    ev('A', 'RELEASE', x=x, y=y, ctrl=True)
    ev('LEFT_CTRL', 'RELEASE', x=x, y=y)


step(redraw)


@step
def s_ctrl_a_check():
    raised("Ctrl+A", 'ATTRIBUTE_EDITOR', *C["old"], C["others"])
    ask('CHANNEL_BOX')
    _area, region = v3d()
    x, y = region.x + region.width // 2, region.y + region.height // 2
    ev('LEFT_CTRL', 'PRESS', x=x, y=y)
    ev('A', 'PRESS', x=x, y=y, ctrl=True)
    ev('A', 'RELEASE', x=x, y=y, ctrl=True)
    ev('LEFT_CTRL', 'RELEASE', x=x, y=y)


step(redraw)


@step
def s_ctrl_a2_check():
    raised("Ctrl+A again", 'CHANNEL_BOX', *C["old"], C["others"])
    ask('ATTRIBUTE_EDITOR')
    in_v3d(bpy.ops.allset.editor_toggle, editor='ATTRIBUTE', show=True)


step(redraw)


@step
def s_show_only_check():
    raised("show only", 'ATTRIBUTE_EDITOR', *C["old"], C["others"])
    C["ae"] = floating('ATTRIBUTE_EDITOR').as_pointer()
    in_v3d(bpy.ops.allset.editor_toggle, editor='ATTRIBUTE')          # the Status Line button


step(redraw)


@step
def s_status_hides():
    check("the Status Line button hides the shown Attribute Editor (Maya's toggle)",
          floating('ATTRIBUTE_EDITOR') is None and C["ae"] not in snapshot())
    w = floating('CHANNEL_BOX')
    with bpy.context.temp_override(window=w, screen=w.screen, area=w.screen.areas[0]):
        md().dock(bpy.context, w)                                    # the handle's Dock


step(redraw)
step(redraw)


@step
def s_docked():
    stack = md().find_stack(win().screen)
    check(f"the raised Channel Box docks back by its handle ({floating('CHANNEL_BOX')}, {stack is not None})",
          floating('CHANNEL_BOX') is None and stack is not None and wm().allset_dock == 'CHANNEL_BOX')
    in_v3d(bpy.ops.allset.menu_item, item="Windows/General Editors/Tool Settings")


step(redraw)
step(redraw)
step(redraw)


@step
def s_ts_open():
    window, area = mod(".ui.tool_dock").find_any()
    check("Windows > General Editors > Tool Settings opens the floating Tool Settings",
          area is not None and md().is_floating(window))
    if window is None:
        return
    C["ts"] = (window.as_pointer(), rect(window))
    C["others"] = {p: r for p, r in snapshot().items() if p != C["ts"][0]}
    C["os_order"] = main_to_front()
    in_v3d(bpy.ops.allset.menu_item, item="Windows/General Editors/Tool Settings")


step(redraw)


@step
def s_ts_front():
    tool_dock, places = mod(".ui.tool_dock"), mod(".ui.window_places")
    window, area = tool_dock.find_any()
    old_ptr, old_rect = C["ts"]
    now = snapshot()
    check(f"asked again, the Tool Settings shows in a new window ({window and window.as_pointer() != old_ptr}), "
          f"the old one closed ({old_ptr not in now})",
          window is not None and window.as_pointer() != old_ptr and old_ptr not in now)
    if window is None:
        return
    check(f"the Tool Settings keeps its place and size {rect(window)} vs {old_rect}",
          all(abs(a - b) <= SLACK for a, b in zip(rect(window), old_rect)))
    check("it is still the Tool Settings", tool_dock.is_dock(area) and len(window.screen.areas) == 1)
    check("the other windows are untouched", all(now.get(p) == r for p, r in C["others"].items()))
    check(f"its place is still remembered under its name ({places._tracked.get(window.as_pointer())})",
          places._tracked.get(window.as_pointer()) == tool_dock.KIND)
    if C.get("os_order"):
        check("the Tool Settings is above the main window", above(hwnd_of(window), hwnd_of(win())))
    top_check("Tool Settings", window)


run()
