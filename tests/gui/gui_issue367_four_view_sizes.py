"""Issue #367 follow-up: the four view keeps its panel sizes and barely changes on screen while a kit window opens or
a dock is put beside it, like Maya's panel layout.

The four view gets uneven proportions (rows 35 / 65, top row 62 / 38, bottom row 41 / 59). They stay the same (within
a pixel or two) after a Space tap round trip, after the Tool Settings window opens at a size that fits in the panel
(its place is cut out of that panel alone: the other three panels never change), after it opens at a remembered size
bigger than the panel (cut out of the whole view, folded into one panel for a moment, so the window keeps its size)
and after the Channel Box tab stack is hidden and shown (a dock beside the whole view). A fast timer records every
tick in which the screen shows something else than four whole panels and which panels changed; the times are printed
(a tick is one redraw of the layout) and loosely bounded. A Space tap still works after each."""

import os
import sys
import time
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sim  # noqa: E402
from sim import MODULE, check, ev, load_maya_layout, run, setup, step, win  # noqa: E402

GUI_TIMEOUT = 300
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


def space_round_trip(label):
    space_over(lambda: fv().roles(win().screen)["side"])

    def one():
        check(f"{label}: Space keeps one panel", fv().single(win().screen) is not None
              and len(fv().panes(win().screen)) == 1)
    step(one)
    space_over(lambda: fv().single(win().screen))

    def four():
        check(f"{label}: Space brings the four view back with its proportions ({props()} vs {C['p0']})",
              len(fv().block(win().screen)) == 4 and near(props(), C["p0"]))
    step(four)


def _rects():
    return {fv().rect(a) for a in win().screen.areas if a.type == 'VIEW_3D'}


def _watch():
    """Every tick: what the screen shows differs from four whole panels -> which of the first panels are gone."""
    if not C.get("watch"):
        return None
    now = time.perf_counter()
    whole = len(fv().block(win().screen)) == 4 and not fv().busy(win())
    if not whole:
        C["ms"] += now - C["last"]
        C["ticks"] += 1
        C["changed"] |= C["panes"] - _rects()
    C["last"] = now
    return 0.0


def _drawn():
    """A draw of the main window: when the screen it draws is not four whole panels, that frame shows the change."""
    if C.get("watch") and bpy.context.window == win() and len(fv().block(win().screen)) != 4:
        C["drawn"].append(time.perf_counter())


def frames(times, gap=0.04):
    """Draw passes among draw callback times (one pass draws many regions within a few ms)."""
    n, last = 0, None
    for t in sorted(times):
        if last is None or t - last > gap:
            n += 1
        last = t
    return n


def watch_on():
    C.update(ms=0.0, ticks=0, changed=set(), last=time.perf_counter(), watch=True, drawn=[],
             panes={fv().rect(a) for a in fv().block(win().screen).values()})
    if "handles" not in C:
        C["handles"] = [(cls, cls.draw_handler_add(_drawn, (), 'WINDOW', 'POST_PIXEL'))
                        for cls in (bpy.types.SpaceView3D, bpy.types.SpaceInfo, bpy.types.SpaceProperties,
                                    bpy.types.SpaceOutliner)]
    bpy.app.timers.register(_watch, first_interval=0.0)


def watch_off(label):
    C["watch"] = False
    ms, panes, shown = round(1000 * C["ms"]), len(C["changed"]), frames(C["drawn"])
    print(f"CHANGED {label}: {ms} ms busy ({C['ticks']} ticks), {shown} frames drawn with the change, {panes} panels",
          flush=True)
    return ms, panes


def ts_open(remember=None):
    def go():
        wp = mod("ui.window_places")
        wp._places.pop(mod("ui.tool_dock").KIND, None)
        if remember:
            w = win()
            top = fv().roles(w.screen)["top"]
            wp.remember(mod("ui.tool_dock").KIND, (w.x + top.x, w.y + top.y, *remember))
        mod("ui.tool_dock").set_docked(False)
        watch_on()
        with override(fv().roles(win().screen)["persp"]):
            bpy.ops.allset.editor_toggle(editor='TOOL_SETTINGS')      # Maya's floating Tool Settings window
    return go


def ts_close():
    win_ts, _area = mod("ui.tool_dock").find_any()
    if win_ts is not None and win_ts != win():
        with bpy.context.temp_override(window=win_ts):
            bpy.ops.wm.window_close()
    return win_ts


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


space_round_trip("round trip")

# --- the Tool Settings window at a size that fits in the top panel: only that panel is cut ------------------------
step(ts_open())
wait(8)


@step
def s_fit_check():
    ms, panes = watch_off("Tool Settings window that fits in the panel")
    w = ts_close()
    check(f"the Tool Settings window opened ({w and (w.width, w.height)})", w is not None and w != win())
    check(f"its place was cut out of one panel only ({panes} panels changed, {ms} ms)", panes <= 1 and ms <= 400)
    check(f"... the proportions stay ({props()} vs {C['p0']})", near(props(), C["p0"]))


space_round_trip("after a window that fits")

# --- a remembered size bigger than the panel: the whole view folds for a moment, the window keeps its size --------
step(ts_open((360, 600)))
wait(8)


@step
def s_big_check():
    ms, panes = watch_off("Tool Settings window bigger than the panel")
    w = ts_close()
    check(f"the window keeps its remembered size ({w and (w.width, w.height)} vs (360, 600))",
          w is not None and w != win() and abs(w.width - 360) <= 8 and abs(w.height - 600) <= 8)
    check(f"... the proportions stay ({props()} vs {C['p0']})", near(props(), C["p0"]))
    check(f"... folded only for a few ticks ({ms} ms)", ms <= 600)


space_round_trip("after a bigger window")


# --- a dock beside the whole view ---------------------------------------------------------------------------------
@step
def s_stack_hide():
    watch_on()
    with override(fv().roles(win().screen)["persp"]):
        bpy.ops.allset.editor_toggle(editor='CHANNEL_BOX')        # the tab stack goes


wait(4)


@step
def s_stack_hidden():
    ms, panes = watch_off("tab stack hidden")
    check(f"hiding the tab stack keeps them ({props()} vs {C['p0']}), folded {ms} ms",
          near(props(), C["p0"]) and ms <= 300)
    watch_on()
    with override(fv().roles(win().screen)["persp"]):
        bpy.ops.allset.editor_toggle(editor='CHANNEL_BOX')        # and comes back


wait(4)


@step
def s_stack_shown():
    ms, panes = watch_off("tab stack shown")
    check(f"showing the tab stack keeps them ({props()} vs {C['p0']}), folded {ms} ms",
          near(props(), C["p0"]) and ms <= 300)
    check("the tab stack is back", mod("ui.maya_dock").find_stack(win().screen) is not None)


space_round_trip("after the dock")

run()
