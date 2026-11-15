"""One Blender session for tests/test_maya_look.py (run by it in a sandbox of its own, never directly).

blender -b --python ml_session.py -- <out.json> <action> ...

The look is put in place in this headless Blender too (ALLSET_MAYA_LOOK_BACKGROUND=1 from the test). Actions:
own_theme (theme values of the user's own), enable (the add-on, Maya mode as saved), maya_on / maya_off, save
(a script's own wm.save_userpref), save_ui (Save Preferences from the UI), tick (the kit's once-a-second look at userpref.blend), edit (a theme edit by the user),
factory (Load Factory Preferences), uninstall (Remove from inside Blender), crash (end without quitting).
The theme's values, the add-on state and the kit's kept-values file are written to the JSON after the actions.
"""

import json
import os
import sys
from importlib import import_module

import addon_utils
import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kit  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:]
OUT, ACTIONS = argv[0], argv[1:]
cfg = bpy.utils.user_resource('CONFIG')
assert "tmp" in cfg.replace("\\", "/").split("/"), cfg
OWN = {"user_interface.wcol_regular.inner": (0.5, 0.2, 0.2, 1.0), "properties.space.back": (0.15, 0.25, 0.15),
       "outliner.space.back": (0.25, 0.15, 0.25), "user_interface.panel_roundness": 0.8}
EDIT = ("graph_editor.space.header", (0.6, 0.1, 0.6, 1.0))


def _set(path, value):
    struct, _, prop = path.rpartition(".")
    setattr(bpy.context.preferences.themes[0].path_resolve(struct), prop, value)


def _look():
    return import_module(kit.MODULE + ".maya_look")


def _dump():
    theme = bpy.context.preferences.themes[0]
    state = None
    if kit.MODULE in bpy.context.preferences.addons:
        state = _look().read_state() is not None
    folder = os.path.join(bpy.utils.user_resource('EXTENSIONS'), ".user", "user_default", "allset")
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump({"values": {k: v for k, v in kit._walk(theme).items() if k not in ("filepath", "name")},
                   "kit": kit.MODULE in bpy.context.preferences.addons, "state": state,
                   "state_file": os.path.isfile(os.path.join(folder, "maya_look.json"))}, fh)


for action in ACTIONS:
    prefs = bpy.context.preferences
    if action == "own_theme":
        for p, v in OWN.items():
            _set(p, v)
    elif action == "enable":
        addon_utils.enable(kit.MODULE, default_set=True)
    elif action == "maya_on":
        import_module(kit.MODULE + ".switch").set_mode(True, layout=False)
    elif action == "maya_off":
        import_module(kit.MODULE + ".switch").set_mode(False, layout=False)
    elif action == "save":
        bpy.ops.wm.save_userpref()
    elif action == "save_ui":
        bpy.ops.allset.save_userpref()       # what Blender's save button / Save & Load menu item run in Maya mode
    elif action == "tick":
        _look().check_saved()
    elif action == "edit":
        _set(*EDIT)
    elif action == "factory":
        bpy.ops.wm.read_factory_userpref()
    elif action == "uninstall":
        repo = next(r for r in prefs.extensions.repos if r.module == "user_default")
        bpy.ops.extensions.package_uninstall(repo_directory=repo.directory, pkg_id="allset")
    elif action == "crash":
        _dump()
        sys.stdout.flush()
        os._exit(0)
    else:
        raise ValueError(action)

_dump()
