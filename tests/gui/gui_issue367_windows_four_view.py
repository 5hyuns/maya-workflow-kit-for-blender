"""Issue #367 follow-up: kit windows and docks never split a panel of the four view, and a window's place is never
carved out of a 3D View.

Single view first: the carves that place the Tool Settings window and a Graph Editor window (at a remembered place)
run slowly here, and the areas they split off are never 3D Views (a gizmo tooltip waiting on a freed 3D View region
crashed Blender); the mouse rests over them meanwhile.
Then, in the four view (a fast timer records the layout on every tick: no area ever lies inside a panel): a Cube option
window opened from the persp panel, the Channel Box tab stack hidden and shown again (right of the whole view), the
Outliner hidden and shown again from the Tool Box (left of the whole view) and a floating Graph Editor docked at the
bottom (below the whole view). Each time the four view is four whole panels again, and a Space tap still keeps one
panel alone and brings the four back."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sim  # noqa: E402
from sim import MODULE, check, ev, load_maya_layout, run, setup, step, win  # noqa: E402

GUI_TIMEOUT = 300
C = {"split": [], "views": set()}


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


def toolbox_ptrs():
    tb = mod("ui.toolbox")
    return {a.as_pointer() for a in win().screen.areas if a.type == 'VIEW_3D' and tb.is_toolbox(a.spaces.active)}


def block_rect():
    b = fv().block(win().screen)
    return fv().union(fv().rect(a) for a in b.values()) if b else None


def _watch():
    """Every tick while watching: the screen shows four whole panels, or the four view is folded into one panel for
    a moment (``four_view.busy``). A split panel shows neither."""
    if not C.get("watch"):
        return None
    screen = win().screen
    for carve in list(mod("ui.window_places")._pending.values()):     # areas split off for a window's place
        for ptr in carve.made:
            a = next((x for x in screen.areas if x.as_pointer() == ptr), None)
            if a is not None:
                C["pieces"].append(a.type)
    if len(fv().block(screen)) != 4 and not getattr(fv(), "busy", lambda w: False)(win()):
        C["split"].append([(a.type, fv().rect(a)) for a in screen.areas if a.type in {'VIEW_3D', 'INFO', 'PROPERTIES'}
                           and a.as_pointer() not in toolbox_ptrs()])
    return 0.005


def watch_on():
    C["split"] = []
    C["pieces"] = []
    C["watch"] = True
    bpy.app.timers.register(_watch, first_interval=0.0)


def watch_off(label):
    C["watch"] = False
    b = fv().block(win().screen)
    check(f"{label}: no panel of the four view was split ({C['split'][:1]})", not C["split"])
    check(f"{label}: no area split off for a window's place is a 3D View ({sorted(set(C['pieces']))})",
          'VIEW_3D' not in C["pieces"])
    check(f"{label}: four whole panels again ({len(b)}, {len(fv().panes(win().screen))} 3D View panels)",
          len(b) == 4 and len(fv().panes(win().screen)) == 4)


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
    space_over(lambda: fv().roles(win().screen)["persp"])

    def one():
        check(f"{label}: Space keeps one panel ({len(fv().panes(win().screen))} 3D View panels)",
              fv().single(win().screen) is not None and len(fv().panes(win().screen)) == 1)
    step(one)
    space_over(lambda: fv().single(win().screen))

    def four():
        check(f"{label}: Space brings the four view back ({len(fv().block(win().screen))})",
              len(fv().block(win().screen)) == 4)
    step(four)


@step
def s_setup():
    setup()
    load_maya_layout()
    bpy.context.preferences.inputs.mouse_double_click_time = 2500


wait(8)          # the layout is fitted to the UI scale in the first seconds after a load


# --- single view: the carved pieces are never 3D Views ----------------------------------------------------------

@step
def s_slow_carve():
    wp = mod("ui.window_places")
    C["tick"] = wp.TICK_FAST
    wp.TICK_FAST = 0.5                   # one split every half second: the mouse can rest over a piece
    area = sim.view3d()[0]
    with override(area):
        bpy.ops.allset.create(kind='CUBE')
        bpy.ops.wm.tool_set_by_id(name="builtin.move")
    mod("ui.tool_dock").set_docked(False)
    with override(area):
        bpy.ops.allset.editor_toggle(editor='TOOL_SETTINGS')
    C["pieces"] = []


def _pieces():
    wp = mod("ui.window_places")
    for carve in list(wp._pending.values()):
        _rest_over(carve)


def _rest_over(carve):
    for ptr in carve.made:
        a = next((x for x in win().screen.areas if x.as_pointer() == ptr), None)
        if a is not None:
            C["pieces"].append(a.type)
            r = next((x for x in a.regions if x.type == 'WINDOW'), None)
            if r is not None and r.width > 4:            # rest the mouse over the piece (a gizmo would get a tooltip)
                ev('MOUSEMOVE', 'NOTHING', x=r.x + r.width // 2, y=r.y + r.height // 2)


for _i in range(8):
    step(_pieces)


@step
def s_slow_done():
    mod("ui.window_places").TICK_FAST = C["tick"]
    floats = [w for w in list(bpy.context.window_manager.windows)[1:]
              if mod("ui.tool_dock").is_dock(w.screen.areas[0])]
    check(f"the carved pieces are never 3D Views ({sorted(set(C['pieces']))})",
          C["pieces"] and 'VIEW_3D' not in C["pieces"])
    check(f"Blender is fine, the Tool Settings window opened ({len(floats)})", len(floats) == 1)
    for w in floats:
        with bpy.context.temp_override(window=w):
            bpy.ops.wm.window_close()
    # a Graph Editor window at a remembered place inside the viewport, carved slowly too
    wp = mod("ui.window_places")
    wp.TICK_FAST = 0.5
    area = sim.view3d()[0]
    w = win()
    wp.remember("editor:FCURVES", (w.x + area.x + 200, w.y + area.y + 150, 420, 260))
    C["pieces"] = []
    C["before"] = {x.as_pointer() for x in bpy.context.window_manager.windows}
    with override(area):
        bpy.ops.allset.open_editor(ui_type='FCURVES')


for _i in range(10):
    step(_pieces)


@step
def s_graph_slow_done():
    mod("ui.window_places").TICK_FAST = C["tick"]
    new = [w for w in bpy.context.window_manager.windows if w.as_pointer() not in C["before"]]
    check(f"Graph Editor carve: the pieces are never 3D Views ({sorted(set(C['pieces']))})",
          C["pieces"] and 'VIEW_3D' not in C["pieces"])
    check(f"Blender is fine, the Graph Editor window opened ({len(new)})", len(new) == 1)
    for w in new:
        with bpy.context.temp_override(window=w):
            bpy.ops.wm.window_close()


wait(2)
space_over(lambda: sim.view3d()[0])


@step
def s_four():
    check(f"the four view ({len(fv().block(win().screen))})", len(fv().block(win().screen)) == 4)
    C["rect4"] = block_rect()


# --- a window carved from a panel: the whole view, never the panel -----------------------------------------------

@step
def s_option_window():
    watch_on()
    persp = fv().roles(win().screen)["persp"]
    with override(persp):
        got = bpy.ops.allset.option_editor_open(key='poly_cube')
    C["opened"] = got


wait(6)


@step
def s_option_check():
    watch_off("Cube option window from the persp panel")
    w = mod("ui.option_editor").find(bpy.context, 'poly_cube')
    check(f"the option window opened ({C['opened']}, {w})", w is not None)
    if w is not None:
        with bpy.context.temp_override(window=w):
            bpy.ops.wm.window_close()


space_round_trip("after the option window")


# --- the Channel Box tab stack: hidden and shown beside the whole view ------------------------------------------

@step
def s_stack_hide():
    watch_on()
    with override(fv().roles(win().screen)["persp"]):
        bpy.ops.allset.editor_toggle(editor='CHANNEL_BOX')


wait(5)


@step
def s_stack_hidden():
    md = mod("ui.maya_dock")
    check(f"the tab stack is hidden ({md.find_stack(win().screen)})", md.find_stack(win().screen) is None)
    with override(fv().roles(win().screen)["persp"]):
        bpy.ops.allset.editor_toggle(editor='CHANNEL_BOX')


wait(6)


@step
def s_stack_shown():
    watch_off("Channel Box stack hidden and shown")
    stack = mod("ui.maya_dock").find_stack(win().screen)
    r = block_rect()
    check(f"the tab stack is right of the whole four view, as tall ({stack and fv().rect(stack)}, view {r})",
          stack is not None and r is not None and stack.x >= r[2] - 4 and abs(stack.y - r[1]) <= 4
          and abs(stack.y + stack.height - r[3]) <= 4)


space_round_trip("after the tab stack")


# --- the Outliner from the Tool Box: left of the whole view -----------------------------------------------------

@step
def s_outliner_hide():
    watch_on()
    with override(fv().roles(win().screen)["persp"]):
        bpy.ops.allset.toggle_outliner()


wait(3)


@step
def s_outliner_show():
    check("the Outliner is hidden", not any(a.type == 'OUTLINER' for a in win().screen.areas))
    with override(fv().roles(win().screen)["persp"]):
        bpy.ops.allset.toggle_outliner()


wait(6)


@step
def s_outliner_shown():
    watch_off("Outliner hidden and shown")
    out = next((a for a in win().screen.areas if a.type == 'OUTLINER'), None)
    r = block_rect()
    check(f"the Outliner is left of the whole four view, as tall ({out and fv().rect(out)}, view {r})",
          out is not None and r is not None and out.x + out.width <= r[0] + 4 and abs(out.y - r[1]) <= 4
          and abs(out.y + out.height - r[3]) <= 4)


space_round_trip("after the Outliner")


# --- a floating Graph Editor docked at the bottom: below the whole view -----------------------------------------

@step
def s_graph_open():
    C["before"] = {w.as_pointer() for w in bpy.context.window_manager.windows}
    with override(fv().roles(win().screen)["persp"]):
        bpy.ops.allset.open_editor(ui_type='FCURVES')


wait(6)


@step
def s_graph_dock():
    new = [w for w in bpy.context.window_manager.windows if w.as_pointer() not in C["before"]]
    check(f"a floating Graph Editor ({len(new)})", len(new) == 1)
    if not new:
        return
    watch_on()
    w = new[0]
    area = w.screen.areas[0]
    with bpy.context.temp_override(window=w, screen=w.screen, area=area,
                                   region=next(r for r in area.regions if r.type == 'WINDOW')):
        bpy.ops.allset.editor_dock(side='BOTTOM')


wait(6)


@step
def s_graph_docked():
    watch_off("Graph Editor docked at the bottom")
    graph = next((a for a in win().screen.areas if a.ui_type == 'FCURVES'), None)
    r = block_rect()
    check(f"the Graph Editor is below the whole four view, as wide ({graph and fv().rect(graph)}, view {r})",
          graph is not None and r is not None and graph.y + graph.height <= r[1] + 4 and abs(graph.x - r[0]) <= 4
          and abs(graph.x + graph.width - r[2]) <= 4)


space_round_trip("after docking the Graph Editor")

run()
