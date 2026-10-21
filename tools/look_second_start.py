"""In-Blender part of tools/look_compare.py: the second GUI start in the same sandbox.

After "Make Blender Maya" in the first run (tools/look_shots.py), Blender started without a file must come up in
Maya mode with the Maya layout (docs/steps/step_42.md; since step 130 the layout is the bundled startup.blend read as
a new untitled file by ``first_start``'s load_post hook, not an app template, and Blender's splash is left alone).
Writes the checks to the result file given after ``--`` and quits.
"""

import json
import sys
from importlib import import_module

import bpy

RESULT = sys.argv[sys.argv.index("--") + 1]


def _check():
    prefs = bpy.context.preferences
    module = next((m for m in prefs.addons.keys() if m.endswith("allset")), None)
    addon = prefs.addons[module].preferences if module else None
    switch = import_module(module + ".switch") if module else None
    win = bpy.context.window_manager.windows[0]
    results = [
        {"name": "second start: Maya mode still on", "ok": bool(switch and switch.is_on())},
        {"name": "second start opens the Maya layout (new untitled file)",
         "ok": bool(switch and switch.is_maya_workspace(win.workspace)) and not bpy.data.filepath},
        {"name": "no welcome dialog again", "ok": bool(addon and addon.welcome_done)},
    ]
    with open(RESULT, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=1)
    bpy.ops.wm.quit_blender()
    return None


bpy.app.timers.register(_check, first_interval=4.0, persistent=True)   # survives the layout file load
