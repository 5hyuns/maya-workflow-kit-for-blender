"""#334: while a window is dragged, Blender redraws every window at each step of the drag. In the Maya layout the
shelf row, the Outliner rows, the dock tint and tab strip and the Time Slider make the calls of their last full draw
again at such a step instead of working out their shapes, colours and texts anew: the main window looks the same as
when it is drawn in full, and a full draw at a drag step makes the same calls as before the drag. While an animation
plays the Time Slider draws in full; a selection changed during the drag shows once the windows stand still.
Windows only (the drag is the move state Windows gives a title-bar drag)."""

import ctypes
import ctypes.wintypes as wt
import os
import sys
import tempfile
import threading
import time
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sim  # noqa: E402
from sim import MODULE, check, load_maya_layout, run, setup, step, view3d, win  # noqa: E402

GUI_TIMEOUT = 400
u32 = ctypes.WinDLL("user32", use_last_error=True)
u32.SendMessageW.argtypes = [wt.HWND, ctypes.c_uint, wt.WPARAM, wt.LPARAM]
u32.SetWindowPos.argtypes = [wt.HWND, wt.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint]
WM_ENTERSIZEMOVE, WM_EXITSIZEMOVE = 0x0231, 0x0232
SWP_NOSIZE, SWP_NOZORDER, SWP_NOACTIVATE = 0x0001, 0x0004, 0x0010
MOVES = 30
KINDS = ("shelf", "outliner", "dock draw", "time slider")
C = {"again": {}, "full": {}}
SHOTS = tempfile.mkdtemp(prefix="allset_reuse_")


def mod(name):
    return import_module(MODULE + name)


wm_ = mod(".ui.window_motion")
dr = mod(".ui.draw_replay")


def others():
    return [w for w in bpy.context.window_manager.windows if w != win()]


def main_regions():
    return {r.as_pointer() for a in win().screen.areas for r in a.regions}


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


def counts(name):
    return {k: C[name].get(k, 0) for k in KINDS}


def reset():
    C["again"].clear()
    C["full"].clear()


def norm(calls):
    """A kept call list as names and plain values (GPU objects by their type: batches are made per draw)."""
    out = []
    for fn, args in calls:
        name = getattr(fn, "__qualname__", None) or getattr(fn, "__name__", "") or type(fn).__name__
        out.append((name, tuple(a if isinstance(a, (int, float, str, tuple, type(None))) else type(a).__name__
                                for a in args)))
    return out


def kept_main():
    """{kind: normalised calls} of the main window's kept draws."""
    regions = main_regions()
    out = {}
    for key, (_sig, calls) in wm_._kept.items():
        if isinstance(key, tuple) and key[0] in KINDS and key[1] in regions:
            out.setdefault(key[0], []).append(norm(calls))
    return {k: sorted(v) for k, v in out.items()}


def redraw_main():
    for a in win().screen.areas:
        a.tag_redraw()


def drag():
    h = graph_hwnd()
    C["dragged"] = False
    C["wait"] = 0
    if h is None:
        C["dragged"] = True
        return False

    def moves():
        r = wt.RECT()
        u32.GetWindowRect(h, ctypes.byref(r))
        u32.SendMessageW(h, WM_ENTERSIZEMOVE, 0, 0)       # Windows' move state, as in a title-bar drag
        for i in range(MOVES):
            u32.SetWindowPos(h, None, r.left + 12 * ((i % 15) + 1), r.top + 2 * (i % 3), 0, 0,
                             SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE)
            time.sleep(0.016)
        u32.SendMessageW(h, WM_EXITSIZEMOVE, 0, 0)
        C["dragged"] = True
    threading.Thread(target=moves, daemon=True).start()
    return True


def wait_drag():
    """The drag thread moves the window meanwhile: wait until it is done, at most 60 ticks."""
    C["wait"] += 1
    if not C.get("dragged") and C["wait"] < 60:
        sim._steps.insert(0, wait_drag)


def pixels(path):
    import numpy as np
    img = bpy.data.images.load(path)
    try:
        arr = np.empty(img.size[0] * img.size[1] * img.channels, dtype=np.float32)
        img.pixels.foreach_get(arr)
        return arr.reshape(img.size[1], img.size[0], img.channels)
    finally:
        bpy.data.images.remove(img)


@step
def s_setup():
    setup()
    load_maya_layout()
    for name, x in (("reuseA", -2.0), ("reuseB", 2.0)):
        ob = bpy.data.objects.new(name, bpy.data.meshes.new(name + "Shape"))
        ob.location.x = x
        bpy.context.scene.collection.objects.link(ob)
    C["real_again"], C["real_keep"] = dr.again, wm_.keep

    def again(key, sig):
        done = C["real_again"](key, sig)
        if done and key[1] in main_regions():
            C["again"][key[0]] = C["again"].get(key[0], 0) + 1
        return done

    def keep(key, sig, value):
        if isinstance(key, tuple) and key[1] in main_regions():
            C["full"][key[0]] = C["full"].get(key[0], 0) + 1
        return C["real_keep"](key, sig, value)
    dr.again, wm_.keep = again, keep
    mod(".ui.window_places")._places.clear()     # no remembered place: the window opens at once
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.allset.open_editor(ui_type='FCURVES')


for _i in range(8):
    step(lambda: None)


@step
def s_before():
    check("Graph Editor opened one window", len(others()) == 1)
    reset()
    redraw_main()


@step
def s_drag():
    full = counts("full")
    check(f"a redraw of the main window draws each kit drawing in full {full}", all(full.values()))
    C["before"] = kept_main()
    C["kit rects"] = kit_rects()
    check(f"the kit drawings' regions {C['kit rects']}", len(C["kit rects"]) >= len(KINDS))
    C["settle"] = wm_._settle_later
    wm_._settle_later = lambda: None        # the last drag step stays on screen for the screenshot
    reset()
    check("the Graph Editor window's OS handle", drag())


step(wait_drag)


@step
def s_drag_check():
    again, full = counts("again"), counts("full")
    print(f"GUI INFO drag: {MOVES} moves, drawn again {again}, in full {full}", flush=True)
    check(f"at the drag steps the main window's kit drawings make their last calls again {again}",
          all(n >= MOVES // 2 for n in again.values()))
    check(f"... and are not worked out anew at each step {full}", all(n <= 2 for n in full.values()))
    reset()
    sim.screenshot(os.path.join(SHOTS, "drag.png"))
    C["shot_drew"] = sum(counts("full").values())
    wm_._settle_later = C["settle"]
    redraw_main()


@step
def s_full_shot():
    sim.screenshot(os.path.join(SHOTS, "full.png"))


def kit_rects():
    """(x, y, width, height) in the main window of the regions whose kit drawings are drawn again at a drag step."""
    regions = {key[1] for key in wm_._kept if isinstance(key, tuple) and key[0] in KINDS}
    return [(r.x, r.y, r.width, r.height) for a in win().screen.areas for r in a.regions
            if r.as_pointer() in regions]


def differ(a, b):
    """Pixels that differ between two screenshots of the main window inside those regions (the area edges between
    them are Blender's), -1 for another size."""
    a, b = pixels(os.path.join(SHOTS, a)), pixels(os.path.join(SHOTS, b))
    if a.shape != b.shape:
        return -1
    out = 0
    for x, y, w, h in C["kit rects"]:
        out += int((abs(a[y:y + h, x:x + w] - b[y:y + h, x:x + w]).max(axis=2) > 1e-6).sum())
    return out


@step
def s_after():
    check(f"the screenshot shows the drag step as drawn ({C['shot_drew']} kit drawings drawn for it)",
          C["shot_drew"] == 0)
    check("a full redraw after the drag makes the same calls as before it", kept_main() == C["before"])
    C["real_kept"] = wm_.kept

    def full(key, sig):           # every drag step drawn in full
        wm_._look(key)
        return None
    wm_.kept = full
    reset()
    drag()


step(wait_drag)


@step
def s_full_drag_check():
    wm_.kept = C["real_kept"]
    full = counts("full")
    check(f"drawn in full at every drag step {full}", all(n >= MOVES // 2 for n in full.values()))
    check("a full draw at a drag step makes the same calls as before the drag", kept_main() == C["before"])
    sim.screenshot(os.path.join(SHOTS, "drag_full.png"))
    diff = differ("drag.png", "drag_full.png")
    print(f"GUI INFO last drag step drawn again vs drawn in full: {diff} pixels differ; vs a redraw after the drag: "
          f"{differ('drag.png', 'full.png')}", flush=True)
    check(f"the main window at a drag step looks the same drawn again as drawn in full ({diff} pixels differ)",
          diff == 0)
    with bpy.context.temp_override(window=win()):
        bpy.ops.screen.animation_play()
    reset()
    drag()


step(wait_drag)


@step
def s_play_check():
    again, full = counts("again"), counts("full")
    check(f"while an animation plays the Time Slider draws in full at the drag steps (again {again['time slider']},"
          f" full {full['time slider']})", again["time slider"] == 0 and full["time slider"] >= MOVES // 2)
    with bpy.context.temp_override(window=win()):
        bpy.ops.screen.animation_cancel(restore_frame=True)
    C["outliner0"] = kept_main().get("outliner")

    def pick():
        for ob in bpy.context.scene.objects:
            ob.select_set(ob.name == "reuseB")
        return None
    bpy.app.timers.register(pick, first_interval=0.15)      # a change while the window moves
    reset()
    drag()


step(wait_drag)
step(lambda: None)


@step
def s_settled():
    full = counts("full")
    shown = kept_main().get("outliner")
    check(f"once the windows stand still the kit drawings draw in full again {full}", all(full.values()))
    check("the Outliner shows the selection made during the drag", shown is not None and shown != C["outliner0"])
    C["shown"] = shown
    redraw_main()


@step
def s_fresh():
    check("... as a fresh redraw draws it", kept_main().get("outliner") == C["shown"])
    dr.again, wm_.keep = C["real_again"], C["real_keep"]
    for x in others():
        with bpy.context.temp_override(window=x):
            bpy.ops.wm.window_close()


run()
