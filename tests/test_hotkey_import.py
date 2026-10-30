"""Hotkey Editor > Import... (#219): a hotkey set exported from Maya's Hotkey Editor (.mhk, MEL) — its key bindings
change the kit keys of the same commands; Maya keys already in place stay, unknown commands and keys are reported,
nothing in the file runs."""

import os
import tempfile
from importlib import import_module

import bpy

import kit
from rt60_dump import populate

hi = import_module(kit.MODULE + ".keymap.hotkey_import")

# a hand-written file in the exported layout: name commands, then hotkeys (one per editor context too)
SAMPLE = r'''
//Maya Preference 2026 (Release 1)
//
hotkeySet -source "Maya_Default" -current My_Set;
nameCommand -annotation "Duplicate the selection" -sourceType "mel" -command ("Duplicate") NameComDuplicate_Selected;
nameCommand -annotation "My own tool" -sourceType "python" -command ("print('hi'); x = 1") MyToolNameCommand;
hotkey -keyShortcut "j" -ctl -alt -name ("NameComDuplicate_Selected");
hotkey -keyShortcut "z" -ctl -name ("NameComUndo");
hotkey -keyShortcut "k" -sht -name ("MyToolNameCommand");
hotkey -keyShortcut "Strange_Key" -name ("NameComDuplicate_Selected");
hotkey -keyShortcut "q" -name ("");
'''


def test_parse_reads_bindings_and_name_commands():
    bindings, names = hi.parse(SAMPLE)
    assert names["NameComDuplicate_Selected"] == "Duplicate"
    assert names["MyToolNameCommand"] == "print('hi'); x = 1"
    keys = [(b["key"], tuple(b["modifiers"]), b["name"]) for b in bindings]
    assert ("j", ("ctl", "alt"), "NameComDuplicate_Selected") in keys
    assert ("k", ("sht",), "MyToolNameCommand") in keys
    assert ("q", (), "") in keys
    assert all(b["ctx"] == "global" for b in bindings)


def test_plan_keeps_maya_keys_and_reports_the_rest():
    he = import_module(kit.MODULE + ".ui.hotkey_editor")
    bindings, names = hi.parse(SAMPLE)
    changes, skipped = hi.plan(he.rows(), bindings, names)
    dup = [(r["command"], ev) for r, ev in changes]
    assert len(dup) == 1 and dup[0][0] == "Duplicate", dup      # Undo's Ctrl+Z is the Maya key: nothing to do
    ev = dup[0][1]
    assert ev["type"] == 'J' and ev.get("ctrl") and ev.get("alt") and not ev.get("shift"), ev
    reasons = {b["key"]: why for b, why in skipped}
    assert "the kit has no hotkey" in reasons["k"]
    assert "not read" in reasons["Strange_Key"]
    assert "emptied" in reasons["q"]


def test_import_changes_the_kit_key_and_restore_brings_it_back():
    populate()
    bpy.context.window_manager.keyconfigs.update()
    he = import_module(kit.MODULE + ".ui.hotkey_editor")
    row = next(r for r in he.rows() if r["command"] == "Duplicate" and r["context"] == "global" and r["editable"])
    assert he.kit_text(bpy.context, row).startswith("Ctrl D") or "D" in he.kit_text(bpy.context, row)
    path = os.path.join(tempfile.mkdtemp(), "my_set.mhk")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(SAMPLE)
    assert bpy.ops.allset.hotkey_import(filepath=path) == {'FINISHED'}
    _km, kmi = he.find_item(bpy.context, row)
    assert kmi is not None and kmi.type == 'J' and kmi.ctrl and kmi.alt and kmi.is_user_modified, kmi
    assert he.restore(bpy.context, row)
    _km, kmi = he.find_item(bpy.context, row)
    assert kmi.type == 'D' and not kmi.is_user_modified
