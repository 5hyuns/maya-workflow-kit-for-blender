"""#381: the Hotkey Editor's duplicate rows and keys that another command uses (ui/hotkey_editor.py).

- A command with two Maya hotkeys (Undo: z and Ctrl+Z) has a row per hotkey: the second reads "Undo (2nd hotkey)"
  and each row changes only its own key, whatever keys the rows were given before.
- A Maya hotkey bound in several object modes (Y = Last Tool in Object Mode and in Mesh) is one row: a new key
  changes it in every mode.
- Like Maya, a key belongs to one command of a context: giving Undo the key Y takes Y from the kit keys that use it
  where Undo runs (Last Tool in Object Mode and Mesh, Mesh Split, ...), so Y undoes in the 3D View; Restore gives
  the Maya key back (taking it from a key the user gave another command), Restore All gives every key back.
- The edits survive Maya mode off / on and restarts (#363).
Background Blender leaves the default keyconfig empty, so it is filled from Blender's keymap data first and the Maya
keys are put on again (Blender's own items of those keymaps switched off, as in the UI)."""

import json
import os
import shutil
import subprocess
from importlib import import_module

import bpy

import kit
from rt60_dump import populate

HERE = os.path.dirname(os.path.abspath(__file__))
VIEWPORT = ("Object Mode", "Mesh", "Curve", "Armature", "Pose", "3D View", "Object Non-modal", "Screen", "Window")


def m(name):
    return import_module(f"{kit.MODULE}.{name}")


def _he():
    return m("ui.hotkey_editor")


def _kcs():
    return bpy.context.window_manager.keyconfigs


def _row(command, maya_key):
    return next(r for r in _he().rows() if r["command"] == command and r["maya_key"] == maya_key)


def _text(command, maya_key):
    return _he().kit_text(bpy.context, _row(command, maya_key))


def _on(type, **mods):
    """{keymap: [idname]} of the active items on this key in the keymaps the 3D View runs."""
    out = {}
    for name in VIEWPORT:
        km = _kcs().user.keymaps.get(name)
        for k in (km.keymap_items if km is not None else ()):
            if k.active and k.type == type and all(bool(getattr(k, x)) == bool(mods.get(x))
                                                   for x in ("ctrl", "alt", "shift", "oskey")):
                out.setdefault(name, []).append(k.idname)
    return out


def _setup():
    populate()
    keymap = m("keymap")
    keymap.deactivate()          # the Maya keys again over the filled keyconfig (its own items switched off)
    keymap.activate()
    _kcs().update()
    _he().restore_all(bpy.context)
    assert not any(km.is_user_modified for km in _kcs().user.keymaps)


def test_duplicate_rows_are_told_apart_and_keep_their_own_key():
    _setup()
    he, ctx = _he(), bpy.context
    labels = [(r["label"], r["maya_key"]) for r in he.rows() if r["command"] == "Undo"]
    assert labels == [("Undo", "Z"), ("Undo (2nd hotkey)", "Ctrl+Z")], labels
    wm = ctx.window_manager
    wm.allset_hk_by, wm.allset_hk_category, wm.allset_hk_search = "NAME", "ALL", "undo"
    shown = [(r.command, r.maya_key) for r in wm.allset_hk_rows]
    assert ("Undo (2nd hotkey)", "Ctrl+Z") in shown, shown
    wm.allset_hk_search = ""
    dups = {}
    for r in he.rows():
        if r["command"] and r["editable"]:
            dups.setdefault((r["command"], r["context"]), []).append(r)
    dups = [rs for rs in dups.values() if len(rs) > 1]
    assert len(dups) >= 9, len(dups)
    key = m("keymap.hotkey_rows").event_text
    for first, second, *_rest in dups:
        a, b = he.find_item(ctx, first)[1], he.find_item(ctx, second)[1]
        assert a is not None and b is not None and a.as_pointer() != b.as_pointer(), first["command"]
        ok, _taken = he.assign(ctx, second, {"type": "F9", "ctrl": True, "alt": True, "shift": True})
        assert ok, second["command"]
        assert he.kit_text(ctx, first) == key(first["event"]), (first["command"], he.kit_text(ctx, first))
        assert he.kit_text(ctx, second) == "Ctrl+Alt+Shift+F9 *", (second["command"], he.kit_text(ctx, second))
        # the first row moved too: still two rows, two keys (the old lookup by key mixed them up here)
        he.assign(ctx, first, {"type": "F10", "ctrl": True, "alt": True, "shift": True})
        assert he.kit_text(ctx, first) == "Ctrl+Alt+Shift+F10 *", first["command"]
        assert he.kit_text(ctx, second) == "Ctrl+Alt+Shift+F9 *", second["command"]
        assert he.restore(ctx, second) and he.kit_text(ctx, second) == key(second["event"]), second["command"]
        assert he.kit_text(ctx, first) == "Ctrl+Alt+Shift+F10 *", first["command"]
        assert he.restore_all(ctx) >= 1
    assert not he.changed_rows(ctx)


def test_one_row_for_a_key_of_every_object_mode():
    _setup()
    he, ctx = _he(), bpy.context
    nst = _row("NonSacredTool", "Y")
    assert [km.name for km, _k in he.row_items(ctx, nst)] == ["Object Mode", "Mesh"]
    assert he.kit_name(nst) == "Last Tool"
    found = m("keymap.hotkey_rows").search(he.rows(), "last tool", names={nst["index"]: [he.kit_name(nst)]})
    assert nst in found, [r["command"] for r in found]
    ok, taken = he.assign(ctx, nst, {"type": "F9", "ctrl": True, "alt": True})
    assert ok and not taken, taken
    assert _on("Y").get("Object Mode") is None and "allset.last_tool" not in _on("Y").get("Mesh", []), _on("Y")
    assert _on("F9", ctrl=True, alt=True) == {"Object Mode": ["allset.last_tool"], "Mesh": ["allset.last_tool"]}, \
        _on("F9", ctrl=True, alt=True)
    assert he.restore(ctx, nst) and he.kit_text(ctx, nst) == "Y"
    assert not any(km.is_user_modified for km in _kcs().user.keymaps)


def test_undo_on_y_takes_y_from_the_last_tool_keys():
    _setup()
    he, ctx = _he(), bpy.context
    undo2 = _row("Undo", "Ctrl+Z")
    before = _on("Y")
    assert before["Object Mode"] == ["allset.last_tool"] and "allset.last_tool" in before["Mesh"], before
    clash = he.conflicts(ctx, undo2, {"type": "Y"})
    assert ("Object Mode", "NonSacredTool") in clash and ("Mesh", "NonSacredTool") in clash, clash
    assert he.describe(clash).startswith("NonSacredTool (Object Mode, Mesh)"), he.describe(clash)
    ok, taken = he.assign(ctx, undo2, {"type": "Y"})
    assert ok and ("Object Mode", "NonSacredTool") in taken and ("Mesh", "NonSacredTool") in taken, taken
    after = _on("Y")
    assert after == {"Screen": ["ed.undo"]}, after         # Y reaches Screen's Undo in every mode
    assert (_text("Undo", "Ctrl+Z"), _text("Undo", "Z"), _text("NonSacredTool", "Y")) == ("Y *", "Z", "— *")
    assert not he.conflicts(ctx, undo2, {"type": "Y"})
    assert "ed.undo" not in _on("Z", ctrl=True).get("Screen", []), _on("Z", ctrl=True)
    assert {r["command"] for r in he.changed_rows(ctx)} >= {"Undo", "NonSacredTool"}
    # an editor's key leaves the global keys alone (the editor's item runs first there, like Maya)
    graph = next(r for r in he.rows() if r["editable"] and r["context"] == "graphEditor")
    assert "Screen" not in he.scope(graph) and "Graph Editor" in he.scope(graph), he.scope(graph)

    # Maya mode off / on keeps both edits (#363)
    sw = m("switch")
    for _n in (1, 2):
        sw.set_mode(False, layout=False)
        _kcs().update()
        sw.set_mode(True, layout=False)
        _kcs().update()
        assert _on("Y") == {"Screen": ["ed.undo"]}, _on("Y")
        assert _text("NonSacredTool", "Y") == "— *" and _text("Undo", "Ctrl+Z") == "Y *"

    # Restore on NonSacredTool: Y is Last Tool again and the Undo row the user gave Y loses it
    assert he.restore(ctx, _row("NonSacredTool", "Y"))
    assert _text("NonSacredTool", "Y") == "Y" and _text("Undo", "Ctrl+Z") == "— *", \
        (_text("NonSacredTool", "Y"), _text("Undo", "Ctrl+Z"))
    assert "ed.undo" not in _on("Y").get("Screen", []) and _on("Y")["Object Mode"] == ["allset.last_tool"]
    # Remove From Others (the button under "Also used by"): Undo's item given Y again in Preferences > Keymap
    # (no take there) meets Last Tool's Y; the button takes Y from Last Tool
    he.find_item(ctx, undo2)[1].type = 'Y'
    _kcs().update()
    assert he.conflicts(ctx, undo2, {"type": "Y"}), "both on Y"
    assert bpy.ops.allset.hotkey_take(row=undo2["index"]) == {'FINISHED'}
    assert not he.conflicts(ctx, undo2, {"type": "Y"}) and _on("Y") == {"Screen": ["ed.undo"]}, _on("Y")
    # Restore All: every key back, nothing user-modified
    assert he.restore_all(ctx) >= 3
    assert _text("Undo", "Ctrl+Z") == "Ctrl+Z" and _text("NonSacredTool", "Y") == "Y"
    assert not any(km.is_user_modified for km in _kcs().user.keymaps)


def test_a_taken_key_leaves_blender_mode_alone():
    """Ctrl+Z given to SelectToggleMode takes it from Undo, a kit key with the same item in Blender's own keymap
    (switched off while the Maya keys are on). Blender mode keeps Blender's Ctrl+Z = Undo; Maya mode again keeps the
    edit."""
    _setup()
    he, ctx = _he(), bpy.context
    ok, taken = he.assign(ctx, _row("SelectToggleMode", "F8"), {"type": "Z", "ctrl": True})
    assert ok and ("Screen", "Undo (2nd hotkey)") in taken, taken
    assert _text("Undo", "Ctrl+Z") == "— *" and _text("SelectToggleMode", "F8") == "Ctrl+Z *"
    sw = m("switch")
    sw.set_mode(False, layout=False)
    _kcs().update()
    screen = _kcs().user.keymaps["Screen"]
    undo = [(k.active, k.is_user_modified) for k in screen.keymap_items
            if k.idname == "ed.undo" and k.type == 'Z' and k.ctrl and not k.shift]
    assert undo == [(True, False)], undo                    # Blender's own Ctrl+Z, untouched
    sw.set_mode(True, layout=False)
    _kcs().update()
    assert _text("Undo", "Ctrl+Z") == "— *" and _text("SelectToggleMode", "F8") == "Ctrl+Z *"
    assert _on("Z", ctrl=True).get("Object Non-modal") == ["allset.toggle_sel_mode"], _on("Z", ctrl=True)
    assert "ed.undo" not in _on("Z", ctrl=True).get("Screen", []), _on("Z", ctrl=True)
    assert he.restore_all(ctx) >= 2
    assert _text("Undo", "Ctrl+Z") == "Ctrl+Z" and _text("SelectToggleMode", "F8") == "F8"
    assert not any(km.is_user_modified for km in _kcs().user.keymaps)


def test_capture_asks_before_taking_a_used_key():
    """The Assign New Hotkey capture: a used key waits for Return (Maya warns first); a free key is assigned."""
    _setup()
    he, ctx = _he(), bpy.context
    op_cls = he.ALLSET_OT_hotkey_assign
    wm = ctx.window_manager

    class Ev:
        def __init__(self, type, value='PRESS'):
            self.type, self.value = type, value
            self.ctrl = self.alt = self.shift = self.oskey = False

    class Op:                                   # the operator's methods on a plain object (no modal in -b)
        row, key, ctrl, alt, shift, oskey = _row("Undo", "Ctrl+Z")["index"], "", False, False, False, False

        def report(self, *_a):
            pass
    for name in ("_row", "_event", "execute", "_end", "modal"):
        setattr(Op, name, getattr(op_cls, name))
    op = Op()
    wm.allset_hk_capture = True
    assert op.modal(ctx, Ev('Y')) == {'RUNNING_MODAL'}
    assert wm.allset_hk_capture and "NonSacredTool (Object Mode, Mesh)" in wm.allset_hk_pending, \
        wm.allset_hk_pending
    assert _text("Undo", "Ctrl+Z") == "Ctrl+Z", "nothing changes before Return"
    assert op.modal(ctx, Ev('RET')) == {'FINISHED'}
    assert not wm.allset_hk_capture and not wm.allset_hk_pending
    assert _text("Undo", "Ctrl+Z") == "Y *" and _text("NonSacredTool", "Y") == "— *"
    # Esc after a used key: nothing changes
    op2 = Op()
    op2.row = _row("Redo", "Shift+Z")["index"]
    wm.allset_hk_capture = True
    assert op2.modal(ctx, Ev('T')) == {'RUNNING_MODAL'} and wm.allset_hk_pending
    assert op2.modal(ctx, Ev('ESC')) == {'CANCELLED'} and not wm.allset_hk_capture
    assert _text("Redo", "Shift+Z") == "Shift+Z" and _text("ShowManipulators", "T") == "T"
    he.restore_all(ctx)


def test_settings_file_keeps_each_row_and_a_taken_key():
    """Export / Import (#275) name the Maya key too, so the second Undo row's key lands on that row, and a key
    taken by another command stays taken."""
    _setup()
    he, ctx = _he(), bpy.context
    sio = m("settings_io")
    he.assign(ctx, _row("Undo", "Ctrl+Z"), {"type": "Y"})
    data = sio.export_hotkeys(ctx)
    by = {(h["command"], h["maya_key"]): h for h in data}
    assert by[("Undo", "Ctrl+Z")]["key"]["type"] == "Y" and ("Undo", "Z") not in by, data
    assert by[("NonSacredTool", "Y")].get("removed") is True, data
    he.restore_all(ctx)
    done, skipped = sio.import_hotkeys(ctx, json.loads(json.dumps(data)))
    assert not skipped, skipped
    assert (_text("Undo", "Ctrl+Z"), _text("Undo", "Z"), _text("NonSacredTool", "Y")) == ("Y *", "Z", "— *")
    he.restore_all(ctx)
    assert not any(km.is_user_modified for km in _kcs().user.keymaps)


def test_taken_key_survives_restarts():
    root = os.path.abspath(os.path.join(bpy.utils.user_resource('CONFIG'), "..", "i381"))
    assert "tmp" in root.replace("\\", "/").split("/"), root
    if os.path.isdir(root):
        shutil.rmtree(root)
    cfg = os.path.join(root, "config")
    os.makedirs(cfg)          # Blender ignores a BLENDER_USER_CONFIG that doesn't exist
    backup = os.path.join(bpy.utils.extension_path_user(kit.MODULE, create=False), "preferences_backup.json")
    old = open(backup, "rb").read() if os.path.isfile(backup) else None
    try:
        given = {"undo": "Y", "last_tool": "—"}
        a = _session(cfg, "a", "enable", "take381", "save")
        assert a["take381"]["y"] == given, a["take381"]
        b = _session(cfg, "b", "maya_off", "save")         # starts in Maya mode, quits in Blender mode
        assert b["start"]["maya_mode"] and b["start"]["y"] == given, b["start"]
        c = _session(cfg, "c", "maya_on", "save")          # starts in Blender mode
        assert c["maya_on"]["y"] == given, c["maya_on"]
        d = _session(cfg, "d")                             # starts in Maya mode again
        assert d["start"]["y"] == given, d["start"]
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
