"""The Attribute Editor opens wide enough to read, like Maya (its tab stack is about 480 px at UI scale 1, the Channel
Box's about 280 px): through Windows > UI Elements on Blender's own screen (the stack is made then) and Ctrl+A / back
there, with Ctrl+A when the layout has no stack (a floating window), and with Ctrl+A / back in the Maya layout (the
stack follows the tab). The edge moves through the kit's cursor fit, which an event-simulated session runs only with
ALLSET_FIT_WARP=1."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sim  # noqa: E402
from sim import MODULE, check, ev, load_maya_layout, run, screenshot, setup, step, view3d, win  # noqa: E402

os.environ["ALLSET_FIT_WARP"] = "1"     # the cursor fit runs like in a real session
C = {}
SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
GUI_TIMEOUT = 300
TRIES = 25          # ticks a resize may take (the cursor fit waits a few ticks on the edge)


def md():
    return import_module(MODULE + ".ui.maya_dock")


def shot(name):
    if SHOTS:
        screenshot(os.path.join(SHOTS, name))


def want(kind):
    s = bpy.context.preferences.system
    return import_module(MODULE + ".ui.layout_fit").dock_width(s.ui_scale, s.pixel_size, kind=kind)


def stack_width():
    st = md().find_stack(win().screen)
    return None if st is None else st.width


def ctrl_a():
    _area, r = view3d()
    x, y = r.x + r.width // 2, r.y + r.height // 2
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('A', 'PRESS', ctrl=True, x=x, y=y)
    ev('A', 'RELEASE', ctrl=True, x=x, y=y)


def expect_width(tag, label, kind, then=None, shot_name=None):
    """A step that waits (up to TRIES ticks) for the stack to reach ``kind``'s width, then checks it."""
    state = {"n": 0}

    def wait():
        w = stack_width()
        if (w is None or abs(w - want(kind)) > 4) and state["n"] < TRIES:
            state["n"] += 1
            sim._steps.insert(0, wait)
            return
        C[tag] = w
        print("DBG", tag, w, "after", state["n"], "ticks", flush=True)
        if shot_name:
            shot(shot_name)
        check(f"{label} ({w} px, want {want(kind)})", w is not None and abs(w - want(kind)) <= 4)
        if then is not None:
            then()
    wait.__name__ = f"s_{tag}"
    step(wait)


# Blender's own screen (Maya mode, no tab stack): Windows > UI Elements > Attribute Editor makes the stack
@step
def s_setup():
    setup()


@step
def s_ui_elements_ae():
    with bpy.context.temp_override(window=win()):
        bpy.ops.allset.editor_toggle(editor='ATTRIBUTE')


expect_width("ui_ae", "Windows > UI Elements > Attribute Editor on Blender's screen opens the stack at the AE's width",
             'ATTRIBUTE_EDITOR', then=ctrl_a, shot_name="dock_ae_ui_elements.png")
expect_width("ui_cb", "then Ctrl+A gives that stack the Channel Box's width", 'CHANNEL_BOX', then=ctrl_a)
expect_width("ui_ae2", "and Ctrl+A again the AE's width", 'ATTRIBUTE_EDITOR')


@step
def s_hide():
    with bpy.context.temp_override(window=win()):
        bpy.ops.allset.editor_toggle(editor='ATTRIBUTE')      # hide it again: the stack closes


@step
def s_no_stack_ctrl_a():
    check(f"the stack is closed ({stack_width()})", stack_width() is None)
    bpy.context.window_manager.allset_dock = 'CHANNEL_BOX'   # Ctrl+A raises the Attribute Editor next
    ctrl_a()


@step
def s_float_wait():
    pass


@step
def s_float_check():
    f = [(w.width, w.height) for w in bpy.context.window_manager.windows if w != win()]
    shot("dock_ae_floating.png")
    check(f"Ctrl+A without a stack opens the Attribute Editor in a window wide enough ({f}, want >= "
          f"{want('ATTRIBUTE_EDITOR') - 4})", bool(f) and f[0][0] >= want('ATTRIBUTE_EDITOR') - 4
          and bpy.context.window_manager.allset_dock == 'ATTRIBUTE_EDITOR')
    for w in list(bpy.context.window_manager.windows):
        if w != win():
            with bpy.context.temp_override(window=w):
                bpy.ops.wm.window_close()


# the Maya layout: the stack shows the Channel Box; Ctrl+A widens it to the AE's width and back
@step
def s_maya_layout():
    bpy.context.window_manager.allset_dock = 'CHANNEL_BOX'
    load_maya_layout()


expect_width("ml_cb", "Maya layout: the stack has the Channel Box's width", 'CHANNEL_BOX', then=ctrl_a)
expect_width("ml_ae", "Maya layout: Ctrl+A widens the stack to the AE's width", 'ATTRIBUTE_EDITOR', then=ctrl_a,
             shot_name="dock_ae_maya_layout.png")
expect_width("ml_back", "Maya layout: Ctrl+A again gives the Channel Box its width back", 'CHANNEL_BOX')


run()
