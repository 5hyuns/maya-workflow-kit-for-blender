"""Issue #214: a Space tap maximizes / restores the panel under the mouse like Maya, whatever editor it is.

Four view -> side panel turned into a Graph Editor, front panel into a render view (Image Editor) -> Space over persp
keeps persp alone, Space again brings the four panels back with the Graph Editor / render view kept; Space over the
Graph Editor panel keeps it alone and brings the four back; a pane maximized by Blender (Ctrl+Space) comes back with
Space; the Tool Box quick layouts never split the four view again. Real Space key events (the hotbox tap).
Shots with ``--shots``."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sim  # noqa: E402
from sim import MODULE, check, load_maya_layout, run, screenshot, setup, step, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def fv():
    return import_module(f"{MODULE}.ui.four_view")


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


def shot(name):
    screenshot(os.path.join(SHOTS or bpy.app.tempdir, f"gui_step294_{name}.png"))


def count():
    return len(win().screen.areas)


def space_over(get):
    """Space tap with the mouse over the area ``get()`` returns: the move in one tick, the key in the next (event
    simulation loses a key sent in the tick of a layout change), then two redraw ticks (the top row splits one tick
    later)."""
    def move():
        area = get()
        reg = next(r for r in area.regions if r.type == 'WINDOW')
        C["xy"] = (reg.x + reg.width // 2, reg.y + reg.height // 2)
        sim.ev('MOUSEMOVE', 'NOTHING', x=C["xy"][0], y=C["xy"][1])

    def key():
        x, y = C["xy"]
        sim.ev('MOUSEMOVE', 'NOTHING', x=x + 1, y=y)
        sim.ev('SPACE', 'PRESS', x=x, y=y)
        sim.ev('SPACE', 'RELEASE', x=x, y=y)
    step(move)
    step(key)
    step(redraw)
    step(redraw)


def quick(layout):
    def go():
        with bpy.context.temp_override(window=win(), screen=win().screen):
            C["quick"] = bpy.ops.allset.quick_layout(layout=layout)
    step(go)
    step(redraw)
    step(redraw)


def role(name):
    return lambda: fv().roles(win().screen)[name]


def only():
    """The one panel left (by the recorded rect)."""
    return fv().single(win().screen)


@step
def s_setup():
    setup()
    load_maya_layout()


for _i in range(5):
    step(redraw)


@step
def s_start():
    C["n0"] = count()
    C["main"] = view3d()[0]
    check(f"Maya layout: one viewport panel ({C['n0']} areas)", len(fv().panes(win().screen)) == 1)


space_over(lambda: C["main"])


@step
def s_four():
    screen = win().screen
    check(f"Space over the viewport -> four view ({count()} areas)", fv().is_four(screen) and count() == C["n0"] + 3)
    placed = fv().roles(screen)
    placed["side"].ui_type = 'FCURVES'
    placed["front"].ui_type = 'IMAGE_EDITOR'
    redraw()


step(redraw)


@step
def s_mixed():
    screen = win().screen
    kinds = {r: a.ui_type for r, a in fv().roles(screen).items()}
    check(f"a Graph Editor and a render view panel: still the four view {kinds}", fv().is_four(screen)
          and kinds == {"top": 'VIEW_3D', "persp": 'VIEW_3D', "front": 'IMAGE_EDITOR', "side": 'FCURVES'})
    shot("01_four_mixed")


space_over(role("persp"))


@step
def s_persp_alone():
    one = only()
    check(f"Space over persp: persp alone, no new split ({count()} areas)",
          count() == C["n0"] and one is not None and one.type == 'VIEW_3D' and not fv().is_four(win().screen)
          and one.spaces.active.region_3d.view_perspective == 'PERSP')
    shot("02_persp_alone")


space_over(only)


@step
def s_four_again():
    screen = win().screen
    kinds = {r: a.ui_type for r, a in fv().roles(screen).items()}
    check(f"Space again: the four panels with the Graph Editor / render view kept ({count()}, {kinds})",
          count() == C["n0"] + 3 and kinds.get("side") == 'FCURVES' and kinds.get("front") == 'IMAGE_EDITOR'
          and kinds.get("persp") == 'VIEW_3D' and kinds.get("top") == 'VIEW_3D')


space_over(role("side"))


@step
def s_graph_alone():
    one = only()
    check(f"Space over the Graph Editor panel: it stays alone ({count()} areas, {one and one.ui_type})",
          count() == C["n0"] and one is not None and one.ui_type == 'FCURVES')
    shot("03_graph_alone")


space_over(only)


@step
def s_back_from_graph():
    screen = win().screen
    kinds = {r: a.ui_type for r, a in fv().roles(screen).items()}
    check(f"Space over it again: the four view back ({count()}, {kinds})", count() == C["n0"] + 3
          and kinds == {"top": 'VIEW_3D', "persp": 'VIEW_3D', "front": 'IMAGE_EDITOR', "side": 'FCURVES'})
    shot("04_back")
    C["screen"] = screen.name
    persp = fv().roles(screen)["persp"]
    reg = next(r for r in persp.regions if r.type == 'WINDOW')
    with bpy.context.temp_override(window=win(), area=persp, region=reg):
        bpy.ops.screen.screen_full_area()          # Ctrl+Space
    redraw()


step(redraw)


@step
def s_maximized():
    check(f"Ctrl+Space maximizes persp ({win().screen.name})", win().screen.show_fullscreen)


space_over(lambda: max(win().screen.areas, key=lambda a: a.width * a.height))


@step
def s_restored():
    screen = win().screen
    check(f"Space in the maximized pane: back to the four view ({screen.name}, {count()})",
          screen.name == C["screen"] and not screen.show_fullscreen and fv().is_four(screen)
          and count() == C["n0"] + 3)


quick('FOUR')


@step
def s_quick_four():
    check(f"quick layout Four on the four view: no split ({count()} areas)",
          count() == C["n0"] + 3 and fv().is_four(win().screen))


quick('SINGLE')


@step
def s_quick_single():
    one = only()
    check(f"quick layout Single: the persp panel alone ({count()} areas)", count() == C["n0"]
          and one is not None and one.type == 'VIEW_3D'
          and one.spaces.active.region_3d.view_perspective == 'PERSP')


quick('SINGLE')


@step
def s_quick_single_again():
    check(f"quick layout Single again: nothing changes ({count()} areas)", count() == C["n0"])


quick('FOUR')


@step
def s_quick_four_again():
    kinds = {r: a.ui_type for r, a in fv().roles(win().screen).items()}
    check(f"quick layout Four: the four view with its panels ({count()} areas, {kinds})",
          count() == C["n0"] + 3 and kinds.get("side") == 'FCURVES')


quick('FOUR')


@step
def s_quick_four_twice():
    check(f"quick layout Four twice: no split ({count()} areas)", count() == C["n0"] + 3)
    shot("05_quick")


run()
