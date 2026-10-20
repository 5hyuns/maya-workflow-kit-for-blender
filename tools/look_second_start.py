"""In-Blender part of tools/look_compare.py: the second GUI start in the same sandbox.

After "Make Blender Maya" in the first run (tools/look_shots.py), Blender started without a file
must come up in the Maya layout with the Maya theme and without its splash
(docs/steps/step_42.md). Writes the checks to the result file given after ``--`` and quits.
"""

import json
import os
import sys

import bpy

RESULT = sys.argv[sys.argv.index("--") + 1]


def _check():
    prefs = bpy.context.preferences
    module = next((m for m in prefs.addons.keys() if m.endswith("allset")), None)
    addon = prefs.addons[module].preferences if module else None
    results = [
        {"name": "second start opens the Maya layout (app template Maya_Workflow_Kit)",
         "ok": prefs.app_template == "Maya_Workflow_Kit"},
        {"name": "Maya theme still on", "ok": bool(addon and addon.maya_theme)
         and prefs.themes[0].name == "Studio Grey (Maya-inspired)"},
        {"name": "Blender splash off", "ok": not prefs.view.show_splash},
        {"name": "no welcome dialog again", "ok": bool(addon and addon.welcome_done)},
    ]
    with open(RESULT, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=1)
    bpy.ops.wm.quit_blender()
    return None


bpy.app.timers.register(_check, first_interval=4.0, persistent=True)   # survives the template switch
