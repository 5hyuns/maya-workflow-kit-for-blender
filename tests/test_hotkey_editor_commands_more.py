"""The kit Hotkey Editor lists the Hypershade, Dope Sheet and Trax Editor commands (Editors > Hypershade / Dope Sheet /
Trax Editor) like Maya's Hotkey Editor, each running the kit editor menu item that does the same; a command whose menu
item has an option box has its "(Option)" command too."""

from importlib import import_module

import kit


def m(name):
    return import_module(f"{kit.MODULE}.{name}")


def _by_command(prefix):
    return {r["command"]: r for r in m("ui.hotkey_editor").rows() if r["category"].startswith(prefix)}


def test_hypershade_commands_are_listed():
    by = _by_command("Editors > Hypershade")
    assert len(by) >= 30, len(by)
    for command, label, category in (
            ("HypershadeDeleteUnusedNodes", "Delete Unused Nodes", "Editors > Hypershade > Edit"),
            ("HypershadeDeleteAllLights", "Delete All Lights", "Editors > Hypershade > Edit > DeleteByType"),
            ("HypershadeDisplayAsLargeSwatches", "As Large Swatches", "Editors > Hypershade > View"),
            ("HypershadeSortByType", "Sort By Type", "Editors > Hypershade > View"),
            ("HypershadeOpenUVEditorWindow", "UV Editor", "Editors > Hypershade > Window")):
        r = by.get(command)
        assert r is not None, command
        assert (r["label"], r["category"]) == (label, category), r
        assert r["editable"] and r["status"] == "KIT", r


def test_dope_sheet_and_trax_commands_are_listed():
    by = {**_by_command("Editors > Dope Sheet"), **_by_command("Editors > Trax Editor")}
    for command, label, option in (("DopeSheetAddInbetween", "Add Inbetween", False),
                                   ("DopeSheetBakeChannelOptions", "Bake Channel (Option)", True),
                                   ("DopeSheetInsertKeysTool", "Insert Keys Tool", False),
                                   ("CreateClip", "Create Clip", False),
                                   ("CreateClipOptions", "Create Clip (Option)", True)):
        r = by.get(command)
        assert r is not None, command
        assert r["label"] == label and r["option"] is option, r
        assert r["editable"] and r["status"] == "KIT", r


def test_every_path_is_a_kit_editor_item():
    emm = m("ui.editor_menu_map")
    emd = m("ui.editor_menu_data")
    rows = [c for c in m("keymap.hotkey_data").COMMANDS
            if c[2].startswith(("Editors.Hypershade", "Editors.Dope Sheet", "Editors.Trax Editor"))]
    assert rows
    missing = sorted({c[3] for c in rows if c[3] not in emm.MAP})
    assert not missing, missing
    assert all(not c[4] or c[3] in emd.OPTION_BOXES for c in rows)
