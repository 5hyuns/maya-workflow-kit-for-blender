"""#290 in every Maya workspace the kit carries: two real clicks on the Outliner button of the left toolbar (the Tool
Box column, or the main view's toolbar where a workspace has no column) hide the docked Outliner and dock it back (or
dock one and hide it again where the workspace starts without one); no click opens a window. The same in the Maya
layout's four view (Space tap first). Shots ``gui_issue290_*.png`` with ``--shots``."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import (MODULE, check, ev, find_button, load_maya_layout, run, screenshot, setup, step,  # noqa: E402
                 view3d, win)

GUI_TIMEOUT = 1200
SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def mod(name):
    return import_module(MODULE + name)


def toolbar():
    """(area, TOOLS region) holding the Outliner button: the Tool Box column, else the largest 3D View's toolbar."""
    tb = mod(".ui.toolbox")
    areas = [a for a in win().screen.areas if a.type == 'VIEW_3D']
    col = next((a for a in areas if tb.is_toolbox(a.spaces.active)), None)
    if col is None:
        col = max(areas, key=lambda a: a.width * a.height)
    return col, next(r for r in col.regions if r.type == 'TOOLS')


def state():
    wm = bpy.context.window_manager
    return len(wm.windows), len([a for a in win().screen.areas if a.type == 'OUTLINER'])


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


def shot(name):
    if SHOTS:
        screenshot(os.path.join(SHOTS, name))


def is_outliner_button(_path, cmd):
    return "toggle_outliner" in (cmd or "")


def case(tag, prepare):
    key = "btn_" + tag

    @step
    def start():
        prepare()
        redraw()

    @step
    def settle():
        redraw()
        C[tag] = state()
        print(f"GUI INFO {tag}: workspace {win().workspace.name}, (windows, docked Outliners) {C[tag]}", flush=True)

    step(find_button(toolbar, is_outliner_button, C, key, step_px=6, x_frac=0.5, start_frac=0.2))

    def click_steps(n):
        @step
        def press():
            pos = C.get(key)
            if n == 1:
                area, region = toolbar()
                shown = area.spaces.active.show_region_toolbar and region.width > 1
                check(f"{tag}: the left toolbar shows the Outliner button ({pos}, toolbar shown {shown})",
                      pos is not None or not shown)
            if pos:
                ev('MOUSEMOVE', 'NOTHING', x=pos[0], y=pos[1])
                ev('LEFTMOUSE', 'PRESS', x=pos[0], y=pos[1])
                ev('LEFTMOUSE', 'RELEASE', x=pos[0], y=pos[1])

        @step
        def wait():
            redraw()

        @step
        def wait2():
            redraw()

        @step
        def look():
            if not C.get(key):
                return
            got = state()
            before = C[tag]
            want_docked = (1 if before[1] == 0 else 0) if n == 1 else before[1]
            check(f"{tag}: click {n} keeps one window and {'hides' if want_docked == 0 else 'docks'} the Outliner "
                  f"(windows, docked {got}; before {before})", got == (1, want_docked))
            if n == 1:
                shot(f"gui_issue290_{tag.replace(' ', '_')}.png")
            # off the button between the clicks (a held hover would read as one long press)
            ev('MOUSEMOVE', 'NOTHING', x=C[key][0], y=C[key][1] + 3)

    click_steps(1)
    click_steps(2)


def workspace(name):
    def prepare():
        with bpy.context.temp_override(window=win()):
            bpy.ops.allset.maya_workspace(name=name)
    return prepare


@step
def s_setup():
    setup()
    load_maya_layout()


case("Maya Classic", lambda: None)
for _name in ("Modeling - Standard", "Modeling - Expert", "Sculpting", "UV Editing", "Rigging", "Animation",
              "Rendering - Standard"):
    case(_name, workspace(_name))


@step
def s_back():
    with bpy.context.temp_override(window=win()):
        bpy.ops.allset.maya_workspace(name="General")
    redraw()


@step
def s_back_wait():
    redraw()


@step
def s_space_hover():
    _area, region = view3d()
    C["xy"] = (region.x + region.width // 2, region.y + region.height // 2)
    ev('MOUSEMOVE', 'NOTHING', x=C["xy"][0] + 1, y=C["xy"][1])


@step
def s_space_tap():
    ev('SPACE', 'PRESS', x=C["xy"][0], y=C["xy"][1])
    ev('SPACE', 'RELEASE', x=C["xy"][0], y=C["xy"][1])


@step
def s_space_wait():
    redraw()
    n = len(mod(".ui.four_view").block(win().screen))
    check(f"Maya Classic: a Space tap gives the four view ({n} panels)", n == 4)


case("Maya Classic four view", lambda: None)


@step
def s_four_check():
    n = len(mod(".ui.four_view").block(win().screen))
    check(f"Maya Classic four view: still the four view after the clicks ({n} panels)", n == 4)


run()
