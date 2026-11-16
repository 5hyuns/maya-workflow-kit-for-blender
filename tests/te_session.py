"""One Blender session for tests/test_theme_extension.py (run by it in a sandbox of its own, never directly).

blender -b --python te_session.py -- <out.json> <action> ...

Actions: own_theme (a theme of the user's own, saved as a preset with Blender's preset "+"), install:<zip>
(Preferences > Get Extensions > Install from Disk), pick_own (the user's preset from the theme menu),
uninstall (Remove), kit_on (enable the add-on, Maya mode on), kit_off (Maya mode off, disable), save
(Save Preferences). The theme's values are written to the JSON after the actions.
"""

import json
import os
import sys

import addon_utils
import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kit  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:]
OUT, ACTIONS = argv[0], argv[1:]
cfg = bpy.utils.user_resource('CONFIG')
assert "tmp" in cfg.replace("\\", "/").split("/"), cfg
PRESET = "interface_theme"
MENU = "USERPREF_MT_interface_theme_presets"
THEME_ID = "allset_theme"
log = []


def _repo():
    return next(r for r in bpy.context.preferences.extensions.repos if r.module == "user_default")


def _own_preset():
    return os.path.join(bpy.utils.user_resource('SCRIPTS', path=os.path.join("presets", PRESET), create=True),
                        "My_Own.xml")


for action in ACTIONS:
    name, _, arg = action.partition(":")
    prefs = bpy.context.preferences
    if name == "own_theme":
        th = prefs.themes[0]
        th.user_interface.wcol_regular.inner = (0.5, 0.2, 0.2, 1.0)
        th.properties.space.back = (0.15, 0.25, 0.15)
        th.outliner.space.back = (0.25, 0.15, 0.25)
        th.user_interface.panel_roundness = 0.8
        import _rna_xml
        _rna_xml.xml_file_write(bpy.context, _own_preset(), getattr(bpy.types, MENU).preset_xml_map)
        th.filepath = _own_preset()
    elif name == "install":
        r = bpy.ops.extensions.package_install_files(repo=_repo().module, filepath=arg, enable_on_install=True)
        log.append(f"install {r}")
    elif name == "pick_own":
        bpy.ops.script.execute_preset(filepath=_own_preset(), menu_idname=MENU)
    elif name == "uninstall":
        r = bpy.ops.extensions.package_uninstall(repo_directory=_repo().directory, pkg_id=THEME_ID)
        log.append(f"uninstall {r}")
    elif name == "kit_on":
        kit.enable(maya=True)
    elif name == "kit_off":
        import importlib
        importlib.import_module(kit.MODULE + ".switch").set_mode(False, layout=False)
        addon_utils.disable(kit.MODULE, default_set=True)
    elif name == "save":
        bpy.ops.wm.save_userpref()
    else:
        raise ValueError(action)

theme = bpy.context.preferences.themes[0]
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump({"values": kit._walk(theme), "hash": kit._struct_hash(theme), "filepath": theme.filepath,
               "installed": os.path.isdir(os.path.join(_repo().directory, THEME_ID)), "log": log}, fh)
