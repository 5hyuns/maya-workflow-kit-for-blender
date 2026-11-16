"""#381 follow-up: a Maya key switched off or removed in Preferences > Keymap never switches off Blender's own key.

Many Maya keys are the same keymap item as a Blender key (Undo on Ctrl+Z in "Screen"); the Maya keys switch
Blender's item off while they are on. Blender keeps a user's edit as "replace the item equal to this one" and applies
it to whichever equal item it finds: an unticked Maya Ctrl+Z (or a removed one) was applied to Blender's own Ctrl+Z
once the Maya keys went out, so Blender mode had no Ctrl+Z undo. Now Blender mode always has Blender's keys, and the
user's edit still comes back with the Maya keys (Maya mode off / on, restarts; #363). Background Blender leaves the
default keyconfig empty, so it is filled from Blender's keymap data first and the Maya keys are put on again (Blender's
own items switched off, as in the UI)."""

import json
import os
import shutil
import subprocess
from importlib import import_module

import bpy

import kit
from rt60_dump import populate

HERE = os.path.dirname(os.path.abspath(__file__))


def m(name):
    return import_module(f"{kit.MODULE}.{name}")


def _kcs():
    return bpy.context.window_manager.keyconfigs


def _screen():
    return _kcs().user.keymaps["Screen"]


def _undo_keys(**mods):
    """[(active, user-modified)] of the Screen Undo items on Z with these modifiers."""
    want = {"ctrl": False, "shift": False, "alt": False, **mods}
    return [(bool(k.active), bool(k.is_user_modified)) for k in _screen().keymap_items
            if k.idname == "ed.undo" and k.type == 'Z' and all(bool(getattr(k, x)) == v for x, v in want.items())]


def _kit_undo(**mods):
    """The user keymap item of the kit's Screen Undo on Z (None when Blender's keymap no longer shows it)."""
    want = {"ctrl": False, "shift": False, "alt": False, **mods}
    addon = _kcs().addon.keymaps["Screen"]
    base = next(k for k in addon.keymap_items if k.idname == "ed.undo" and k.type == 'Z'
                and all(bool(getattr(k, x)) == v for x, v in want.items()))
    return _screen().keymap_items.find_match(addon, base)


def _switch(on):
    m("switch").set_mode(on, layout=False)
    _kcs().update()


def _setup():
    populate()
    if not kit.is_enabled():
        kit.enable()
    _switch(True)
    keymap = m("keymap")
    keymap.deactivate()          # the Maya keys again over the filled keyconfig (its own items switched off)
    keymap.activate()
    _kcs().update()
    for km in _kcs().user.keymaps:
        if km.is_user_modified:
            km.restore_to_default()
    _kcs().update()
    assert _undo_keys(ctrl=True).count((True, False)) == 1, _undo_keys(ctrl=True)   # the Maya key; Blender's is off


def _blender_mode_has_ctrl_z():
    assert _undo_keys(ctrl=True) == [(True, False)], _undo_keys(ctrl=True)
    assert not _screen().is_user_modified, "nothing of the Maya keys' edits left in Blender mode"


def test_unticked_maya_key_leaves_blender_mode_alone():
    _setup()
    _kit_undo(ctrl=True).active = False          # Preferences > Keymap: the Maya Ctrl+Z unticked
    _kcs().update()
    assert (True, False) not in _undo_keys(ctrl=True) and (True, True) not in _undo_keys(ctrl=True), \
        _undo_keys(ctrl=True)
    for _n in (1, 2):
        _switch(False)
        _blender_mode_has_ctrl_z()
        _switch(True)
        on = [a for a, _mod in _undo_keys(ctrl=True)]
        assert True not in on, ("the Maya Ctrl+Z stays off", _undo_keys(ctrl=True))
        assert _undo_keys() == [(True, False)], "the other Maya Undo (z) is untouched"
    m("ui.hotkey_editor").restore_all(bpy.context)
    _screen().restore_to_default()
    _kcs().update()


def test_removed_maya_key_leaves_blender_mode_alone():
    _setup()
    _screen().keymap_items.remove(_kit_undo(ctrl=True))     # Preferences > Keymap: the Maya Ctrl+Z removed
    _kcs().update()
    assert True not in [a for a, _mod in _undo_keys(ctrl=True)], _undo_keys(ctrl=True)
    for _n in (1, 2):
        _switch(False)
        _blender_mode_has_ctrl_z()
        _switch(True)
        assert True not in [a for a, _mod in _undo_keys(ctrl=True)], ("removed stays removed", _undo_keys(ctrl=True))
    _screen().restore_to_default()
    _kcs().update()


def test_other_edits_of_that_keymap_stay():
    """The keymap that had a Maya key removed keeps the user's other edits through the round trip: another Maya
    key moved, a key the user added for a Blender command."""
    _setup()
    _screen().keymap_items.remove(_kit_undo(ctrl=True))
    _kit_undo().type = 'F7'                                   # the other Maya Undo moved to F7
    added = _screen().keymap_items.new("screen.region_toggle", 'F9', 'PRESS', ctrl=True, alt=True)
    added.properties.region_type = 'TOOLS'
    _kcs().update()
    for _n in (1, 2):
        _switch(False)
        mine = [k for k in _screen().keymap_items if k.idname == "screen.region_toggle" and k.type == 'F9']
        assert len(mine) == 1, "the added key stays in Blender mode"
        assert _undo_keys(ctrl=True) == [(True, False)], _undo_keys(ctrl=True)
        _switch(True)
        f7 = [k.idname for k in _screen().keymap_items if k.type == 'F7' and k.active]
        assert f7 == ["ed.undo"], ("the moved Maya key comes back", f7)
        assert True not in [a for a, _mod in _undo_keys(ctrl=True)], _undo_keys(ctrl=True)
        assert len([k for k in _screen().keymap_items if k.idname == "screen.region_toggle" and k.type == 'F9']) == 1
    _screen().restore_to_default()
    _kcs().update()


def test_restore_all_brings_them_back():
    """The Hotkey Editor's Restore All Maya Hotkeys gives back a Maya key switched off or removed in Preferences >
    Keymap, and leaves the user's other edits of that keymap."""
    _setup()
    he, ctx = m("ui.hotkey_editor"), bpy.context
    undo2 = next(r for r in he.rows() if r["command"] == "Undo" and r["maya_key"] == "Ctrl+Z")
    added = _screen().keymap_items.new("screen.region_toggle", 'F9', 'PRESS', ctrl=True, alt=True)
    added.properties.region_type = 'TOOLS'
    _kit_undo(ctrl=True).active = False
    _kcs().update()
    assert he.restore_all(ctx) >= 1
    assert _kit_undo(ctrl=True) is not None and _kit_undo(ctrl=True).active, _undo_keys(ctrl=True)
    assert he.kit_text(ctx, undo2) == "Ctrl+Z", he.kit_text(ctx, undo2)
    assert len([k for k in _screen().keymap_items if k.idname == "screen.region_toggle" and k.type == 'F9']) == 1
    _screen().keymap_items.remove(_kit_undo())                 # the Maya z removed
    _kcs().update()
    assert he.restore_all(ctx) >= 1
    assert _undo_keys() == [(True, False)], _undo_keys()
    _screen().restore_to_default()
    _kcs().update()


def test_hotkey_editor_shows_and_restores_a_key_off_in_preferences():
    """The Hotkey Editor shows a Maya key switched off (or removed) in Preferences > Keymap as "Ctrl+Z (off) *", and
    that row's Restore gives it back, leaving the other rows' changes of the keymap; Assign works on it too."""
    _setup()
    he, ctx = m("ui.hotkey_editor"), bpy.context
    row = lambda c, k: next(r for r in he.rows() if r["command"] == c and r["maya_key"] == k)  # noqa: E731
    undo1, undo2, nst = row("Undo", "Z"), row("Undo", "Ctrl+Z"), row("NonSacredTool", "Y")
    assert he.assign(ctx, undo1, {"type": "F7"})[0]          # another row of the same keymap, changed
    _kit_undo(ctrl=True).active = False                       # Preferences > Keymap
    _kcs().update()
    assert he.kit_text(ctx, undo2) == "Ctrl+Z (off) *", he.kit_text(ctx, undo2)
    assert undo2 in he.changed_rows(ctx)
    data = {(h["command"], h["maya_key"]): h for h in m("settings_io").export_hotkeys(ctx)}
    assert data[("Undo", "Ctrl+Z")].get("removed") is True, data
    assert he.restore(ctx, undo2)
    assert he.kit_text(ctx, undo2) == "Ctrl+Z" and _kit_undo(ctrl=True).active, he.kit_text(ctx, undo2)
    assert he.kit_text(ctx, undo1) == "F7 *", he.kit_text(ctx, undo1)
    # removed (X) shows the same and comes back the same; Assign on it gives the new key
    _screen().keymap_items.remove(_kit_undo(ctrl=True))
    _kcs().update()
    assert he.kit_text(ctx, undo2) == "Ctrl+Z (off) *", he.kit_text(ctx, undo2)
    assert he.assign(ctx, undo2, {"type": "F9", "ctrl": True, "alt": True})[0]
    assert he.kit_text(ctx, undo2) == "Ctrl+Alt+F9 *" and he.kit_text(ctx, undo1) == "F7 *"
    # a Maya key without a Blender twin switched off stays an item: "(off)", Restore gives it back
    for _km, k in he.row_items(ctx, nst):
        k.active = False
    _kcs().update()
    assert he.kit_text(ctx, nst) == "Y (off) *", he.kit_text(ctx, nst)
    assert he.restore(ctx, nst) and he.kit_text(ctx, nst) == "Y"
    assert he.restore_all(ctx) >= 2
    assert not any(km.is_user_modified for km in _kcs().user.keymaps)


def test_unticked_maya_key_across_restarts():
    root = os.path.abspath(os.path.join(bpy.utils.user_resource('CONFIG'), "..", "i381b"))
    assert "tmp" in root.replace("\\", "/").split("/"), root
    if os.path.isdir(root):
        shutil.rmtree(root)
    cfg = os.path.join(root, "config")
    os.makedirs(cfg)          # Blender ignores a BLENDER_USER_CONFIG that doesn't exist
    backup = os.path.join(bpy.utils.extension_path_user(kit.MODULE, create=False), "preferences_backup.json")
    old = open(backup, "rb").read() if os.path.isfile(backup) else None
    blender = [["ed.undo", True, False]]          # Blender's own Ctrl+Z, on, unedited
    try:
        a = _session(cfg, "a", "enable", "untick_ctrl_z", "save")
        assert not [x for x in a["untick_ctrl_z"]["ctrl_z"] if x[1]], a["untick_ctrl_z"]
        b = _session(cfg, "b", "keys_again", "maya_off", "save")     # starts in Maya mode, quits in Blender mode
        assert b["maya_off"]["ctrl_z"] == blender, b["maya_off"]
        c = _session(cfg, "c", "maya_on", "save")                    # starts in Blender mode
        assert c["start"]["ctrl_z"] == blender, c["start"]
        assert not [x for x in c["maya_on"]["ctrl_z"] if x[1]], c["maya_on"]
        d = _session(cfg, "d", "keys_again", "maya_off")             # starts in Maya mode again
        assert not [x for x in d["keys_again"]["ctrl_z"] if x[1]], d["keys_again"]
        assert d["maya_off"]["ctrl_z"] == blender, d["maya_off"]
    finally:                  # the sessions' disable wrote the backup: later test files must not read it
        if old is None:
            if os.path.isfile(backup):
                os.remove(backup)
        else:
            with open(backup, "wb") as fh:
                fh.write(old)
    shutil.rmtree(root)


def _session(cfg, name, *actions):
    out = os.path.join(cfg, "..", f"{name}.json")
    env = dict(os.environ)
    env["BLENDER_USER_CONFIG"] = cfg
    env["ALLSET_NO_WELCOME"] = "1"
    cmd = [bpy.app.binary_path, "-b", "--python", os.path.join(HERE, "i363_session.py"), "--", out, *actions]
    proc = subprocess.run(cmd, env=env, stdin=subprocess.DEVNULL, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=180)
    if not os.path.isfile(out):
        raise AssertionError(f"session {name} wrote nothing:\n{proc.stdout[-2000:]}\n{proc.stderr[-2000:]}")
    with open(out, encoding="utf-8") as fh:
        data = json.load(fh)
    os.remove(out)
    return data
