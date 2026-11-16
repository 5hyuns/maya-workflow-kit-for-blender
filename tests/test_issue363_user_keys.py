"""#363: the user's own key edits survive Maya mode off / on and restarts (keymap/user_keys.py).

The Maya keys are add-on keymap items whose operators exist only in Maya mode; Blender's items of the keymaps the
Maya keys replace are switched off while they are on. Edits of either kind were lost by a round trip:
- a Maya key with operator properties (Smooth Mesh Preview 3 = ``allset.smooth_preview(level=3)``) moved to
  another key came back on its own key after Maya mode off / on;
- a Blender key changed in Blender mode came back unchanged after a key of the same keymap changed in Maya mode.
Background Blender leaves the default keyconfig empty, so it is filled from Blender's keymap data first
(rt60_dump.populate)."""

import json
import os
import shutil
import subprocess
from importlib import import_module

import bpy

import kit
from rt60_dump import populate

AUTO_ENABLE = False
HERE = os.path.dirname(os.path.abspath(__file__))
KM = "Object Mode"


def _kcs():
    return bpy.context.window_manager.keyconfigs


def _mod(name):
    return import_module(f"{kit.MODULE}.{name}")


def _prefs():
    return bpy.context.preferences.addons[kit.MODULE].preferences


def _props(kmi):
    p = kmi.properties
    if p is None:
        return {}
    return {k: getattr(p, k) for k in p.bl_rna.properties.keys() if k != "rna_type" and p.is_property_set(k)}


def _user():
    return _kcs().user.keymaps[KM]


def _kit_item(idname, type):
    addon = _kcs().addon.keymaps[KM]
    item = next(k for k in addon.keymap_items if k.idname == idname and k.type == type)
    return _user().keymap_items.find_match(addon, item)


def _on(type, **mods):
    """(idname, properties, active) of the user Object Mode items on this key."""
    return sorted((k.idname, json.dumps(_props(k), sort_keys=True), k.active) for k in _user().keymap_items
                  if k.type == type and all(bool(getattr(k, m)) == bool(mods.get(m)) for m in ("ctrl", "alt", "shift")))


def _switch(on):
    _mod("switch").set_mode(on, layout=False)
    _kcs().update()


def _operator_churn():
    """Another add-on's operator registered and gone in Blender mode (Blender then drops the properties of keymap
    items whose operator is missing)."""
    class TMP_OT_issue363(bpy.types.Operator):
        bl_idname = "tmp.issue363"
        bl_label = "Issue 363"

        def execute(self, context):
            return {'FINISHED'}
    for _n in range(2):
        bpy.utils.register_class(TMP_OT_issue363)
        _kcs().update()
        bpy.utils.unregister_class(TMP_OT_issue363)
        _kcs().update()


def _setup():
    populate()
    if not kit.is_enabled():
        kit.enable(maya=False)
    _switch(True)


def test_maya_key_edits_survive_maya_mode_off_on():
    _setup()
    # moved: Smooth Mesh Preview 3 (Numpad 3) to Ctrl+F7; switched off: Smooth Mesh Preview 2 (Numpad 2);
    # removed: Numpad 0; added: a kit command with a property on F8
    moved = _kit_item("allset.smooth_preview", 'NUMPAD_3')
    moved.type = 'F7'
    moved.ctrl = 1
    _kit_item("allset.smooth_preview", 'NUMPAD_2').active = False
    _user().keymap_items.remove(_kit_item("allset.smooth_preview", 'NUMPAD_0'))
    _user().keymap_items.new("allset.smooth_preview", 'F8', 'PRESS').properties.level = 2
    _kcs().update()
    want = {"F7": _on('F7', ctrl=True), "F8": _on('F8'), "NUMPAD_2": _on('NUMPAD_2'), "NUMPAD_0": _on('NUMPAD_0'),
            "NUMPAD_3": _on('NUMPAD_3')}
    assert want["F7"] == [("allset.smooth_preview", '{"level": 3}', True)], want
    assert want["F8"] == [("allset.smooth_preview", '{"level": 2}', True)], want
    assert ("allset.smooth_preview", '{"level": 2}', False) in want["NUMPAD_2"], want
    assert not want["NUMPAD_0"] and not want["NUMPAD_3"], want
    assert not _prefs().user_keys, "nothing kept while the Maya keys are on"

    for n in (1, 2):
        _switch(False)
        assert _prefs().user_keys, "the edits are kept in the add-on preferences"
        assert not [k for k in _user().keymap_items if k.idname.startswith("allset.")], \
            "no kit key edit left in Blender mode's keymap"
        _operator_churn()
        _switch(True)
        got = {"F7": _on('F7', ctrl=True), "F8": _on('F8'), "NUMPAD_2": _on('NUMPAD_2'),
               "NUMPAD_0": _on('NUMPAD_0'), "NUMPAD_3": _on('NUMPAD_3')}
        assert got == want, (n, got, want)
        assert not _prefs().user_keys, "given back: nothing kept"
        assert _user().is_user_modified

    # Restore All (Preferences > Keymap): the kit's keys as they come, nothing kept after another round trip
    _user().restore_to_default()
    _kcs().update()
    _switch(False)
    _switch(True)
    assert _on('NUMPAD_3') == [("allset.smooth_preview", '{"level": 3}', True)], _on('NUMPAD_3')
    assert not _on('F7', ctrl=True) and not _on('F8'), (_on('F7', ctrl=True), _on('F8'))
    assert not _prefs().is_property_set("user_keys")
    assert not _user().is_user_modified


def test_keyboard_choice_blender_and_back():
    """Keyboard: Blender (Maya mode stays, the Maya keys go) and back keeps the edit too."""
    _setup()
    moved = _kit_item("allset.smooth_preview", 'NUMPAD_1')
    moved.type = 'F7'
    _kcs().update()
    p = _prefs()
    p.keymap_set = 'BLENDER'
    _mod("keymap").sync()
    _kcs().update()
    assert not _on('F7'), _on('F7')
    p.keymap_set = 'MAYA'
    _mod("keymap").sync()
    _kcs().update()
    assert _on('F7') == [("allset.smooth_preview", '{"level": 1}', True)], _on('F7')
    _user().restore_to_default()
    _kcs().update()


def test_blender_key_edit_survives_a_maya_edit():
    """A Blender key changed in Blender mode, then another key of that keymap changed in Maya mode."""
    _setup()
    _switch(False)
    delete = next(k for k in _user().keymap_items if k.idname == "object.delete" and k.type == 'X')
    delete.type = 'F9'
    _kcs().update()
    _switch(True)
    _kit_item("allset.smooth_preview", 'NUMPAD_1').type = 'F7'
    _kcs().update()
    _switch(False)
    assert [i for i, _p, _a in _on('F9')] == ["object.delete"], _on('F9')
    assert "object.delete" not in [i for i, _p, _a in _on('X')], _on('X')
    assert "blender" not in json.loads(_prefs().user_keys), "given back: nothing kept of Blender's keys"
    _switch(True)
    assert _on('F7') == [("allset.smooth_preview", '{"level": 1}', True)], _on('F7')
    _switch(False)
    assert [i for i, _p, _a in _on('F9')] == ["object.delete"], _on('F9')
    _user().restore_to_default()
    _kcs().update()


def test_disable_leaves_no_kit_edit():
    """Disable (an update, Remove) in Maya mode: no edit of a kit key stays in Blender's keymap (the edit is kept
    with the add-on preferences, see test_edits_survive_restarts)."""
    _setup()
    _kit_item("allset.smooth_preview", 'NUMPAD_3').type = 'F7'
    _kcs().update()
    kit.disable()
    _kcs().update()
    assert not [k for k in _user().keymap_items if k.idname.startswith("allset.")]
    assert not _user().is_user_modified


# --- across restarts -----------------------------------------------------------------------------------------------

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


def _backup_file():
    """The kit's preferences backup in the extension's user folder (a disable in a session writes it)."""
    return os.path.join(bpy.utils.extension_path_user(kit.MODULE, create=False), "preferences_backup.json")


def test_edits_survive_restarts():
    root = os.path.abspath(os.path.join(bpy.utils.user_resource('CONFIG'), "..", "i363"))
    assert "tmp" in root.replace("\\", "/").split("/"), root
    if os.path.isdir(root):
        shutil.rmtree(root)
    cfg = os.path.join(root, "config")
    os.makedirs(cfg)          # Blender ignores a BLENDER_USER_CONFIG that doesn't exist
    backup = _backup_file()
    old = open(backup, "rb").read() if os.path.isfile(backup) else None
    try:
        _restarts(cfg)
    finally:                  # the sessions' disable wrote the backup: later test files must not read it
        if old is None:
            if os.path.isfile(backup):
                os.remove(backup)
        else:
            with open(backup, "wb") as fh:
                fh.write(old)
    shutil.rmtree(root)


def _restarts(cfg):
    edited = [["allset.smooth_preview", "F7", 1, '{"level": 3}', False],
              ["allset.smooth_preview", "F8", 0, '{"level": 2}', True]]
    a = _session(cfg, "a", "enable", "edit", "save")
    assert a["edit"]["keys"] == edited, a["edit"]
    b = _session(cfg, "b", "maya_off", "save")             # starts in Maya mode, quits in Blender mode
    assert b["start"]["maya_mode"] and b["start"]["keys"] == edited, b["start"]
    assert not b["maya_off"]["maya_mode"] and not b["maya_off"]["keys"] and b["maya_off"]["kept"], b["maya_off"]
    c = _session(cfg, "c", "maya_on", "save")              # starts in Blender mode
    assert not c["start"]["maya_mode"] and not c["start"]["kit_items"] and c["start"]["kept"], c["start"]
    assert c["maya_on"]["keys"] == edited and not c["maya_on"]["kept"], c["maya_on"]
    d = _session(cfg, "d", "disable", "enable")            # starts in Maya mode again; disable + enable
    assert d["start"]["maya_mode"] and d["start"]["keys"] == edited and not d["start"]["kept"], d["start"]
    assert not d["disable"]["kit_items"] and not d["disable"]["keys"], d["disable"]
    assert d["enable"]["maya_mode"] and d["enable"]["keys"] == edited and not d["enable"]["kept"], d["enable"]
