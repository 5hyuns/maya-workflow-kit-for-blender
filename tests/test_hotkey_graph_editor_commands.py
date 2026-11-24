"""The kit Hotkey Editor lists the Graph Editor's commands (Editors > Graph Editor: tangents, infinity, key tools, view
modes, buffer curves ...) like Maya's Hotkey Editor, each running the kit Graph Editor menu item that does the same;
a command whose menu item has an option box has its "(Option)" command too."""

from importlib import import_module

import kit


def m(name):
    return import_module(f"{kit.MODULE}.{name}")


def _rows():
    return [r for r in m("ui.hotkey_editor").rows() if r["category"] == "Editors > Graph Editor"]


def test_graph_editor_commands_are_listed():
    rows = _rows()
    assert len(rows) >= 90, len(rows)
    by = {r["command"]: r for r in rows}
    for command, label in (("TangentLinear", "Linear (Tangents)"), ("InTangentFlat", "Flat (In Tangent)"),
                           ("PostInfinityCycleOffset", "Post Infinity Cycle with Offset"),
                           ("BakeChannel", "Bake Channel"), ("SculptKeysGrabTool", "Grab Tool"),
                           ("GraphSnapOptions", "Snap (Option)"), ("ToggleShowBufferCurves", "Show Buffer Curves")):
        r = by.get(command)
        assert r is not None, command
        assert r["label"] == label and r["editable"] and r["status"] == "KIT", r


def test_every_path_is_a_kit_graph_editor_item():
    emm = m("ui.editor_menu_map")
    emd = m("ui.editor_menu_data")
    rows = [c for c in m("keymap.hotkey_data").COMMANDS if c[2] == "Editors.Graph Editor"]
    missing = sorted({c[3] for c in rows if c[3] not in emm.MAP})
    assert not missing, missing
    assert all(not c[4] or c[3] in emd.OPTION_BOXES for c in rows)
