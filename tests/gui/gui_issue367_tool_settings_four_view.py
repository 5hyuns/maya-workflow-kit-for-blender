"""Issue #367: Tool Settings and the four view.

In the Maya layout's four view a double-click on the Tool Box's Move tool opens the Tool Settings in a floating
window, like Maya: no panel of the four view is split for it. A Space tap over a panel keeps that panel alone and a
second tap brings the four view back, also while the window is open. Dock (the window's handle) puts the Tool
Settings left of the whole four view, never inside one panel; tearing it off again gives the four panels their width
back. Switching to Blender closes the Tool Settings window, and back in Maya the four view is back and the Space tap still works. Real Space key
events and Tool Box clicks. Shots with ``--shots``."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sim  # noqa: E402
from sim import MODULE, _steps, check, ev, find_button, load_maya_layout, run, screenshot, setup, step, win  # noqa: E402

GUI_TIMEOUT = 300
SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def mod(name):
    return import_module(f"{MODULE}.{name}")


def fv():
    return mod("ui.four_view")


def td():
    return mod("ui.tool_dock")


def redraw():
    for w in bpy.context.window_manager.windows:
        for a in w.screen.areas:
            a.tag_redraw()


def shot(name):
    if SHOTS:
        screenshot(os.path.join(SHOTS, f"gui_issue367_{name}.png"))


def layout():
    return [(a.type, a.x, a.y, a.width, a.height) for a in win().screen.areas]


def ts_windows():
    """Floating windows that show only the Tool Settings."""
    return [w for w in list(bpy.context.window_manager.windows)[1:]
            if len(w.screen.areas) == 1 and td().is_dock(w.screen.areas[0])]


def tool_tab_windows():
    """Floating windows showing a Properties editor on the Tool tab (what a left-over Tool Settings window is)."""
    out = []
    for w in list(bpy.context.window_manager.windows)[1:]:
        for a in w.screen.areas:
            if a.type == 'PROPERTIES' and a.spaces.active.context == 'TOOL':
                out.append(w)
    return out


def docked():
    return td().find(win().screen)


def block():
    return fv().block(win().screen)


def block_rect():
    b = block()
    return fv().union(fv().rect(a) for a in b.values()) if b else None


def toolbox():
    tb = mod("ui.toolbox")
    area = next(a for a in win().screen.areas if a.type == 'VIEW_3D' and tb.is_toolbox(a.spaces.active))
    return area, next(r for r in area.regions if r.type == 'TOOLS')


def toolbox_width():
    return toolbox()[0].width


def near(r, q, tol=4):
    return r is not None and q is not None and all(abs(a - b) <= tol for a, b in zip(r, q))


def space_over(get):
    """Space tap with the mouse over the area ``get()`` returns: the move in one tick, the key in the next, then
    redraw ticks (the top row of a new four view splits one tick later)."""
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


def role(name):
    return lambda: fv().roles(win().screen)[name]


def only():
    return fv().single(win().screen)


def wait(n=3):
    for _ in range(n):
        step(redraw)


def check_four(label):
    def fn():
        b = block()
        print("LAYOUT", label, layout(), flush=True)
        check(f"{label}: the four view ({len(b)} panels, {len(fv().panes(win().screen))} 3D View panels)",
              len(b) == 4 and len(fv().panes(win().screen)) == 4)
    step(fn)


def check_single(label, areas_key):
    def fn():
        print("LAYOUT", label, layout(), flush=True)
        one = only()
        n = len(win().screen.areas)
        check(f"{label}: one panel, not a four view inside a panel ({len(fv().panes(win().screen))} 3D View panels, "
              f"{n} areas vs {C[areas_key]})",
              one is not None and not fv().is_four(win().screen) and len(fv().panes(win().screen)) == 1
              and n == C[areas_key])
    step(fn)


# --- the four view, then a double-click on Move --------------------------------------------------------------------

@step
def s_setup():
    setup()
    load_maya_layout()
    # simulated clicks are one timer tick apart: give the double click room (sandbox preferences only)
    bpy.context.preferences.inputs.mouse_double_click_time = 2500


wait(8)          # the layout is fitted to the UI scale in the first seconds after a load


@step
def s_start():
    C["n1"] = len(win().screen.areas)
    C["tb_w"] = toolbox_width()
    check("Maya layout: one viewport panel, no Tool Settings", len(fv().panes(win().screen)) == 1
          and docked() is None and not ts_windows())


space_over(lambda: sim.view3d()[0])
check_four("Space over the viewport")


@step
def s_four():
    C["n4"] = len(win().screen.areas)
    C["rect4"] = block_rect()
    C["windows"] = len(bpy.context.window_manager.windows)


def _find_move():
    return find_button(toolbox, lambda path, cmd: '"builtin.move"' in cmd, C, "move", step_px=6, x_frac=0.5)


@step
def s_find():
    _steps.insert(0, _find_move())


@step
def s_hover():
    check(f"the Tool Box has the Move tool ({C.get('move')})", C.get("move") is not None)
    if C.get("move") is None:
        _steps.clear()
        return
    x, y = C["move"]
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)


@step
def s_click1():
    ev('LEFTMOUSE', 'PRESS')
    ev('LEFTMOUSE', 'RELEASE')


@step
def s_click2():
    x, y = C["move"]
    ev('MOUSEMOVE', 'NOTHING', x=x + 1, y=y)
    ev('LEFTMOUSE', 'PRESS')
    ev('LEFTMOUSE', 'RELEASE')


wait(6)


@step
def s_floating():
    print("LAYOUT after double-click", layout(), flush=True)
    floats = ts_windows()
    rect = block_rect()
    check(f"double-click Move in the four view: Tool Settings in a floating window ({len(floats)}), none docked "
          f"({docked()})", len(floats) == 1 and docked() is None)
    check(f"no panel was split for it: four panels, {len(win().screen.areas)} areas vs {C['n4']}, rect {rect} vs "
          f"{C['rect4']}", len(block()) == 4 and len(win().screen.areas) == C["n4"] and near(rect, C["rect4"]))
    if floats:
        w = floats[0]
        main = win()
        check(f"the window is a narrow Tool Settings window ({w.width} x {w.height}, main {main.width} x "
              f"{main.height})", w.width <= main.width * 0.45 and w.height >= 200)
    shot("01_four_floating")


space_over(role("persp"))
check_single("Space over persp with the Tool Settings window open", "n1")
space_over(only)
check_four("Space again")


# --- Dock from the window's handle: left of the whole four view ----------------------------------------------------

@step
def s_dock():
    floats = ts_windows()
    if not floats:
        check("a Tool Settings window to dock", False)
        _steps.clear()
        return
    w = floats[0]
    area = w.screen.areas[0]
    region = next(r for r in area.regions if r.type == 'WINDOW')
    with bpy.context.temp_override(window=w, screen=w.screen, area=area, region=region):
        got = bpy.ops.allset.dock_back(action='DOCK')
    check(f"Dock from the floating Tool Settings -> {got}", got == {'FINISHED'})


wait(8)


@step
def s_docked():
    print("LAYOUT docked", layout(), flush=True)
    d = docked()
    b = block()
    rect = block_rect()
    check(f"docked: the window is gone ({len(ts_windows())}), the dock is in the main window ({d})",
          not ts_windows() and d is not None)
    check(f"the four view is whole: {len(b)} panels", len(b) == 4)
    if d is not None and rect is not None:
        check(f"the dock is left of the whole four view, as tall as it (dock {fv().rect(d)}, four view {rect})",
              d.x + d.width <= rect[0] + 4 and abs(d.y - rect[1]) <= 4 and abs(d.y + d.height - rect[3]) <= 4)
    C["n4d"] = len(win().screen.areas)
    shot("02_four_docked")


space_over(role("side"))


@step
def s_single_docked():
    print("LAYOUT single docked", layout(), flush=True)
    one = only()
    check(f"Space over side with the dock: one panel ({len(fv().panes(win().screen))} 3D View panels, "
          f"{len(win().screen.areas)} areas vs {C['n1'] + 1}), the dock stays ({docked()})",
          one is not None and len(fv().panes(win().screen)) == 1 and len(win().screen.areas) == C["n1"] + 1
          and docked() is not None)


space_over(only)
check_four("Space again with the dock")


# --- tear the dock off again: the four view gets its width back ----------------------------------------------------

@step
def s_tear():
    d = docked()
    if d is None:
        check("a dock to tear off", False)
        _steps.clear()
        return
    region = next(r for r in d.regions if r.type == 'WINDOW')
    with bpy.context.temp_override(window=win(), screen=win().screen, area=d, region=region):
        got = bpy.ops.allset.dock_handle('EXEC_DEFAULT')
    check(f"the dock's handle tears it off -> {got}", got == {'FINISHED'})


wait(8)


@step
def s_torn():
    print("LAYOUT torn", layout(), flush=True)
    rect = block_rect()
    check(f"torn off: a floating Tool Settings window ({len(ts_windows())}), no dock ({docked()})",
          len(ts_windows()) == 1 and docked() is None)
    check(f"the four panels got the dock's width back: rect {rect} vs {C['rect4']}, {len(win().screen.areas)} areas "
          f"vs {C['n4']}, Tool Box {toolbox_width()} px vs {C['tb_w']}",
          len(block()) == 4 and near(rect, C["rect4"], 8) and len(win().screen.areas) == C["n4"]
          and abs(toolbox_width() - C["tb_w"]) <= 4)


space_over(role("front"))
check_single("Space over front after tearing the dock off", "n1")
space_over(only)
check_four("Space again after tearing the dock off")


# --- Maya -> Blender -> Maya ---------------------------------------------------------------------------------------

@step
def s_to_blender():
    check("a Tool Settings window before the switch", len(ts_windows()) == 1)
    with bpy.context.temp_override(window=win()):
        bpy.ops.allset.switch_mode(mode='BLENDER')


wait(6)


@step
def s_blender():
    left = tool_tab_windows()
    check(f"Blender mode: no Tool Settings window left behind ({len(left)}, {len(bpy.context.window_manager.windows)} "
          f"windows)", not left and len(bpy.context.window_manager.windows) == C["windows"])
    with bpy.context.temp_override(window=win()):
        bpy.ops.allset.switch_mode(mode='MAYA')


wait(8)


@step
def s_maya_again():
    print("LAYOUT maya again", layout(), flush=True)
    # the layout as it was before the switch: the four view (#458)
    check(f"Maya again: no stray window ({len(bpy.context.window_manager.windows)}), the four view is back "
          f"({len(block())} panels)",
          len(bpy.context.window_manager.windows) == C["windows"] and len(block()) == 4
          and len(win().screen.areas) == C["n4"])


space_over(role("top"))
check_single("Maya again: Space over top", "n1")
space_over(only)
check_four("Maya again: Space again")

run()
