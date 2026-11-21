"""Another workflow add-on that makes its own layout from the window's workspace while Maya mode is on and puts its own
editors in it (#423): its copy carries the kit's workspace keys, but the switch to Blender leaves it alone (not deleted, not switched away
from), the kit's own Maya layout still goes, and Maya mode on again from that layout appends the Maya layout.
The sample add-on is a few lines inside the test. Headless part: tests/test_issue423_tool_tab_addon.py."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, run, step, tap  # noqa: E402
import sim  # noqa: E402

SAMPLE = "Sample Layout"
C = {}


def sw():
    return import_module(MODULE + ".switch")


def win():
    return bpy.context.window_manager.windows[0]


def wait(fn, cond, limit=40):
    """Run ``fn``'s checks once ``cond()`` holds (or after ``limit`` ticks)."""
    def again():
        C[fn] = C.get(fn, 0) + 1
        if not cond() and C[fn] < limit:
            sim._steps.insert(0, again)
            return
        fn()
    return again


@step
def s_setup():
    tap('ESC')
    import addon_utils
    addon_utils.enable(MODULE, default_set=True)
    C["user_ws"] = win().workspace.name
    bpy.ops.allset.switch_mode(mode='MAYA')


def maya_on():
    ws = win().workspace
    check(f"Maya mode on, Maya layout shown ({ws.name})", sw().is_on() and sw().is_maya_workspace(ws))
    C["maya_ws"] = ws.name
    # the sample add-on turns on: its own layout made from the window's workspace (Blender's Duplicate), shown
    before = set(bpy.data.workspaces)
    with bpy.context.temp_override(window=win(), screen=win().screen):
        bpy.ops.workspace.duplicate()
    new = next(w for w in bpy.data.workspaces if w not in before)
    new.name = SAMPLE
    win().workspace = new


def rebuild():
    # ... and builds its own editors in it: the Maya Status Line / Shelf rows become its own panels
    for area in win().screen.areas:
        if area.type == 'IMAGE_EDITOR':
            area.type = 'PROPERTIES'


step(wait(maya_on, lambda: sw().is_on() and sw().is_maya_workspace(win().workspace)))


step(wait(rebuild, lambda: win().workspace.name == SAMPLE and win().screen in bpy.data.workspaces[SAMPLE].screens[:]))


@step
def s_copy():
    ws = bpy.data.workspaces[SAMPLE]
    check(f"the copy carries the kit's keys ({sorted(k for k in ws.keys() if k.startswith('allset_'))})",
          sw().PREV_KEY in ws)
    check("the copy is not one of the kit's Maya workspaces", not sw().is_maya_workspace(ws) and sw().is_copy(ws))
    check(f"the window shows the copy ({win().workspace.name})", win().workspace.name == SAMPLE)
    bpy.ops.allset.switch_mode(mode='BLENDER')


def blender():
    names = [w.name for w in bpy.data.workspaces]
    ws = bpy.data.workspaces.get(SAMPLE)
    check(f"Blender mode: the sample add-on's layout is kept ({names})", not sw().is_on() and ws is not None)
    check(f"and still shown ({win().workspace.name})", win().workspace.name == SAMPLE)
    check(f"and has none of the kit's keys ({list(ws.keys()) if ws else None})",
          ws is not None and not any(k.startswith("allset_") for k in ws.keys()))
    check(f"the kit's Maya layout is removed ({C['maya_ws']} not in {names})", C["maya_ws"] not in names)
    bpy.ops.allset.switch_mode(mode='MAYA')


step(wait(blender, lambda: not sw().is_on() and C.get("maya_ws") not in bpy.data.workspaces))


def maya_again():
    ws = win().workspace
    check(f"Maya mode on again from the sample layout: the Maya layout appended ({ws.name}, back to "
          f"{ws.get(sw().PREV_KEY)})", sw().is_on() and sw().is_maya_workspace(ws) and ws.get(sw().PREV_KEY) == SAMPLE)
    bpy.ops.allset.switch_mode(mode='BLENDER')


step(wait(maya_again, lambda: sw().is_on() and sw().is_maya_workspace(win().workspace)))


def end():
    names = [w.name for w in bpy.data.workspaces]
    check(f"Blender mode again: back on the sample layout, no Maya layout left ({win().workspace.name}, {names})",
          win().workspace.name == SAMPLE and not any(sw().is_maya_workspace(w) for w in bpy.data.workspaces))


step(wait(end, lambda: not sw().is_on() and not any(sw().is_maya_workspace(w) for w in bpy.data.workspaces)))

run()
