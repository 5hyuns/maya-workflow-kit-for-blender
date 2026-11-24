"""In a real UI (#541): the Hotkey Editor's Custom Scripts > Windows commands toggle an editor window. Run once, the
UV Editor / Dope Sheet / Graph Editor / Hypershade opens in a window of its own; run again (from the main window, and
from inside the editor's own window), that window closes and the main window stays."""

import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, run, setup, step, win, load_maya_layout  # noqa: E402

GUI_TIMEOUT = 240
C = {}
CASES = (("ToggleUVEditorWindow", 'UV_EDITOR', "main"), ("ToggleDopeSheetWindow", 'DOPE_SHEET', "own"),
         ("ToggleGraphEditorWindow", 'GRAPH_EDITOR', "main"), ("ToggleHypershadeWindow", 'HYPERSHADE', "main"))


def floating(key):
    from importlib import import_module
    return import_module(MODULE + ".operators.window_toggle").floating(bpy.context, key)


def v3d_run(command):
    area = max((a for a in win().screen.areas if a.type == 'VIEW_3D'), key=lambda a: a.width * a.height)
    region = next(r for r in area.regions if r.type == 'WINDOW')
    with bpy.context.temp_override(window=win(), area=area, region=region):
        return bpy.ops.allset.hotkey_command(item=command)


def own_run(command, w):
    area = max(w.screen.areas, key=lambda a: a.width * a.height)
    region = next(r for r in area.regions if r.type == 'WINDOW')
    with bpy.context.temp_override(window=w, area=area, region=region):
        return bpy.ops.allset.hotkey_command(item=command)


@step
def s_setup():
    setup()
    load_maya_layout()


def nothing():
    pass


for _cmd, _key, _from in CASES:
    def opened(cmd=_cmd, key=_key):
        C["windows"] = len(bpy.context.window_manager.windows)
        for w in floating(key):          # a docked editor stays; a left-over window of it would make this a close
            check(f"{cmd}: no window of it before", False)
        res = v3d_run(cmd)
        check(f"{cmd}: runs ({res})", res == {'FINISHED'})

    def is_open(cmd=_cmd, key=_key):
        check(f"{cmd}: its window opened", len(floating(key)) == 1)

    def closed(cmd=_cmd, key=_key, where=_from):
        found = floating(key)
        if not found:
            return
        res = v3d_run(cmd) if where == "main" else own_run(cmd, found[0])
        check(f"{cmd} again from the {where} window: runs ({res})", res == {'FINISHED'})

    def is_closed(cmd=_cmd, key=_key):
        check(f"{cmd}: its window closed, the main window stays",
              not floating(key) and win() is not None and len(bpy.context.window_manager.windows) == C["windows"])

    for f in (opened, nothing, nothing, is_open, closed, nothing, nothing, is_closed):
        step(f)

run()
