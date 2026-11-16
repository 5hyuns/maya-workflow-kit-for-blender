"""One Blender session of the kept key edits round trip (run by test_issue363_user_keys.py, not a test file).

    blender -b --python tests/i363_session.py -- <out.json> <action> [<action> ...]

Runs with a sandbox BLENDER_USER_CONFIG (the caller creates it under tmp/), WITHOUT --factory-startup so the saved
preferences of the previous session are read. Actions: enable, edit, take381 (test_issue381_hotkey_conflict.py),
untick_ctrl_z, keys_again (test_issue381_blender_keys.py), maya_off, maya_on, disable, save.
Writes {"state": ...} after the actions.
"""

import json
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit  # noqa: E402
from rt60_dump import populate  # noqa: E402

assert os.path.abspath(bpy.utils.user_resource('CONFIG')).replace("\\", "/").find("/tmp/") > 0, \
    bpy.utils.user_resource('CONFIG')


def mod(name):
    from importlib import import_module
    return import_module(f"{kit.MODULE}.{name}")


def _props(kmi):
    p = kmi.properties
    return {k: getattr(p, k) for k in p.bl_rna.properties.keys()
            if k != "rna_type" and p.is_property_set(k)} if p is not None else {}


def observe():
    kcs = bpy.context.window_manager.keyconfigs
    km = kcs.user.keymaps["Object Mode"]
    keys = sorted((k.idname, k.type, int(k.ctrl), json.dumps(_props(k), sort_keys=True), k.is_user_defined)
                  for k in km.keymap_items if k.type in ('F7', 'F8'))
    # kit keys in the user keymaps; tool keymaps left out (Blender keeps the user copy of an unregistered
    # tool's keymap until a restart) and so is the Maya / Blender switch shortcut (always there)
    kit_user = sorted(k.idname for km in kcs.user.keymaps if "Tool:" not in km.name for k in km.keymap_items
                      if k.idname.startswith("allset.") and k.idname != "allset.switch_mode")
    on = kit.is_enabled() and mod("switch").is_on()
    prefs = bpy.context.preferences.addons[kit.MODULE].preferences if kit.is_enabled() else None
    return {"maya_mode": on, "keys": keys, "kit_items": len(kit_user),
            "kept": prefs.user_keys if prefs is not None else None, "y": hotkeys_381() if on else None,
            "ctrl_z": sorted([k.idname, bool(k.active), bool(k.is_user_modified)]
                             for k in kcs.user.keymaps["Screen"].keymap_items
                             if k.type == 'Z' and k.ctrl and not k.shift and not k.alt and k.idname == "ed.undo")}


def untick_ctrl_z():
    """#381: the Maya Ctrl+Z (Screen Undo) unticked in Preferences > Keymap."""
    kcs = bpy.context.window_manager.keyconfigs
    kcs.update()
    addon = kcs.addon.keymaps["Screen"]
    base = next(k for k in addon.keymap_items if k.idname == "ed.undo" and k.type == 'Z' and k.ctrl and not k.shift)
    kcs.user.keymaps["Screen"].keymap_items.find_match(addon, base).active = False


def keys_again():
    """The Maya keys out and in again over the filled keyconfig (Blender's own items switched off, as in the UI)."""
    keymap = mod("keymap")
    keymap.deactivate()
    keymap.activate()


def _row381(command, maya_key):
    he = mod("ui.hotkey_editor")
    return next(r for r in he.rows() if r["command"] == command and r["maya_key"] == maya_key)


def hotkeys_381():
    """#381: the Hotkey Editor's keys of the second Undo row and of NonSacredTool (Last Tool)."""
    he = mod("ui.hotkey_editor")
    text = lambda r: he.kit_text(bpy.context, r).replace(" *", "")      # noqa: E731
    return {"undo": text(_row381("Undo", "Ctrl+Z")), "last_tool": text(_row381("NonSacredTool", "Y"))}


def take381():
    """#381: the second Undo row (Ctrl+Z) given Y in the Hotkey Editor: Last Tool loses Y."""
    kcs = bpy.context.window_manager.keyconfigs
    kcs.update()
    ok, taken = mod("ui.hotkey_editor").assign(bpy.context, _row381("Undo", "Ctrl+Z"), {"type": "Y"})
    assert ok and taken, taken


def edit():
    """The user's edits in Maya mode: a Maya key moved to Ctrl+F7, a kit command added on F8."""
    kcs = bpy.context.window_manager.keyconfigs
    kcs.update()
    addon = kcs.addon.keymaps["Object Mode"]
    user = kcs.user.keymaps["Object Mode"]
    item = next(k for k in addon.keymap_items if k.idname == "allset.smooth_preview" and k.type == 'NUMPAD_3')
    u = user.keymap_items.find_match(addon, item)
    u.type = 'F7'
    u.ctrl = 1
    n = user.keymap_items.new("allset.smooth_preview", 'F8', 'PRESS')
    n.properties.level = 2
    kcs.update()


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    out, actions = argv[0], argv[1:]
    populate()
    states = {"start": observe()}
    for action in actions:
        if action == "enable":
            kit.enable()
        elif action == "disable":
            kit.disable()
        elif action == "edit":
            edit()
        elif action == "take381":
            take381()
        elif action == "untick_ctrl_z":
            untick_ctrl_z()
        elif action == "keys_again":
            keys_again()
        elif action == "maya_off":
            mod("switch").set_mode(False, layout=False)
        elif action == "maya_on":
            mod("switch").set_mode(True, layout=False)
        elif action == "save":
            bpy.ops.wm.save_userpref()
        bpy.context.window_manager.keyconfigs.update()
        states[action] = observe()
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(states, fh)


main()
