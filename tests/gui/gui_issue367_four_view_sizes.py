"""Issue #367 follow-up: the four view keeps its panel sizes, like Maya's panel layout.

The four view gets uneven proportions (rows 35 / 65, top row 62 / 38, bottom row 41 / 59). They stay the same (within
a pixel or two) after a Space tap round trip, after a Cube option window opened from the persp panel, after the Tool
Settings window opened from the four view (its place is carved out of the view folded into one panel for a moment) and after the Channel Box tab stack is hidden and shown
(a dock beside the whole view). A fast timer measures how long the view is folded each time: two ticks for a dock,
a few for a window's carve (printed; the bound is loose, a tick is one redraw of the layout)."""

import os
import sys
import time
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sim  # noqa: E402
from sim import MODULE, check, ev, load_maya_layout, run, setup, step, win  # noqa: E402

GUI_TIMEOUT = 240
C = {}
WANT = [0.35, 0.62, 0.41]           # bottom row share, top row's left share, bottom row's left share


def mod(name):
    return import_module(f"{MODULE}.{name}")


def fv():
    return mod("ui.four_view")


def redraw():
    for w in bpy.context.window_manager.windows:
        for a in w.screen.areas:
            a.tag_redraw()


def wait(n=3):
    for _ in range(n):
        step(redraw)


def props():
    b = fv().block(win().screen)
    return fv().proportions(b) if len(b) == 4 else None


def near(a, b, tol=0.015):
    return a is not None and b is not None and all(abs(x - y) <= tol for x, y in zip(a, b))


def override(area, kind='WINDOW'):
    region = next(r for r in area.regions if r.type == kind)
    return bpy.context.temp_override(window=win(), screen=win().screen, area=area, region=region)


def space_over(get):
    def move():
        area = get()
        reg = next(r for r in area.regions if r.type == 'WINDOW')
        C["xy"] = (reg.x + reg.width // 2, reg.y + reg.height // 2)
        ev('MOUSEMOVE', 'NOTHING', x=C["xy"][0], y=C["xy"][1])

    def key():
        x, y = C["xy"]
        ev('MOUSEMOVE', 'NOTHING', x=x + 1, y=y)
        ev('SPACE', 'PRESS', x=x, y=y)
        ev('SPACE', 'RELEASE', x=x, y=y)
    step(move)
    step(key)
    step(redraw)
    step(redraw)


def _watch():
    if not C.get("watch"):
        return None
    folded = len(fv().block(win().screen)) != 4 or fv().busy(win())
    now = time.perf_counter()
    if folded:
        C["folded"] = C.get("folded", 0.0) + (now - C["last"])
    C["last"] = now
    return 0.002


def watch_on():
    C["folded"], C["last"], C["watch"] = 0.0, time.perf_counter(), True
    bpy.app.timers.register(_watch, first_interval=0.0)


def watch_off():
    C["watch"] = False
    return round(1000 * C.get("folded", 0.0))


@step
def s_setup():
    setup()
    load_maya_layout()


wait(8)                     # the layout is fitted to the UI scale in the first seconds after a load
space_over(lambda: sim.view3d()[0])
space_over(lambda: fv().roles(win().screen)["persp"])


@step
def s_uneven():
    st = fv().state(win().screen)
    st["split"] = WANT
    fv()._save_state(win().screen, st)


space_over(lambda: fv().single(win().screen))


@step
def s_uneven_check():
    C["p0"] = props()
    check(f"the four view comes back with its proportions ({C['p0']} vs {WANT})", near(C["p0"], WANT, 0.02))


space_over(lambda: fv().roles(win().screen)["side"])
space_over(lambda: fv().single(win().screen))


@step
def s_space_check():
    check(f"a Space tap round trip keeps them ({props()} vs {C['p0']})", near(props(), C["p0"]))
    watch_on()
    with override(fv().roles(win().screen)["persp"]):
        bpy.ops.allset.option_editor_open(key='poly_cube')


wait(6)


@step
def s_option_check():
    ms = watch_off()
    print(f"FOLDED option window: {ms} ms", flush=True)
    check(f"a window carved from the persp panel keeps them ({props()} vs {C['p0']})", near(props(), C["p0"]))
    check(f"... the view is folded only for a few ticks ({ms} ms)", ms <= 600)
    w = mod("ui.option_editor").find(bpy.context, 'poly_cube')
    if w is not None:
        with bpy.context.temp_override(window=w):
            bpy.ops.wm.window_close()
    watch_on()
    mod("ui.tool_dock").set_docked(False)
    with override(fv().roles(win().screen)["persp"]):
        bpy.ops.allset.editor_toggle(editor='TOOL_SETTINGS')      # Maya's floating Tool Settings window


wait(8)


@step
def s_tool_settings_check():
    ms = watch_off()
    print(f"FOLDED Tool Settings window: {ms} ms", flush=True)
    win_ts, area = mod("ui.tool_dock").find_any()
    check(f"the Tool Settings window opened ({win_ts})", win_ts is not None and win_ts != win())
    check(f"a window carved out of the folded view keeps them ({props()} vs {C['p0']})", near(props(), C["p0"]))
    check(f"... the view is folded only for a few ticks ({ms} ms)", ms <= 600)
    if win_ts is not None and win_ts != win():
        with bpy.context.temp_override(window=win_ts):
            bpy.ops.wm.window_close()
    watch_on()
    with override(fv().roles(win().screen)["persp"]):
        bpy.ops.allset.editor_toggle(editor='CHANNEL_BOX')        # the tab stack goes


wait(4)


@step
def s_stack_hidden():
    ms = watch_off()
    print(f"FOLDED stack hidden: {ms} ms", flush=True)
    check(f"hiding the tab stack keeps them ({props()} vs {C['p0']})", near(props(), C["p0"]))
    check(f"... the view is folded for two ticks ({ms} ms)", ms <= 300)
    watch_on()
    with override(fv().roles(win().screen)["persp"]):
        bpy.ops.allset.editor_toggle(editor='CHANNEL_BOX')        # and comes back


wait(4)


@step
def s_stack_shown():
    ms = watch_off()
    print(f"FOLDED stack shown: {ms} ms", flush=True)
    check(f"showing the tab stack keeps them ({props()} vs {C['p0']})", near(props(), C["p0"]))
    check(f"... the view is folded for two ticks ({ms} ms)", ms <= 300)
    check("the tab stack is back", mod("ui.maya_dock").find_stack(win().screen) is not None)


run()
