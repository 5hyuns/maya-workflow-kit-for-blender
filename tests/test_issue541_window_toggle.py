"""#541: the Hotkey Editor lists Custom Scripts > Windows commands that open an editor's window or close it when it
is open in a window of its own (UV Editor, Outliner, Hypershade, Graph Editor, ...). Each runs the editor's Windows
menu item when no window of it is open. GUI: tests/gui/gui_issue541_window_toggle.py."""

from importlib import import_module

import kit

kit_cmds = import_module(kit.MODULE + ".keymap.hotkey_kit")
toggle = import_module(kit.MODULE + ".operators.window_toggle")
menu_map = import_module(kit.MODULE + ".ui.menu_map")


def test_every_window_toggle_is_listed_and_runs_a_known_menu_item():
    listed = {c[4]["window"] for c in kit_cmds.COMMANDS if c[3] == "allset.window_toggle"}
    assert listed == set(toggle.WINDOWS), (listed, set(toggle.WINDOWS))
    assert all(c[2] == "Custom Scripts.Windows" for c in kit_cmds.COMMANDS if c[3] == "allset.window_toggle")
    for key, (label, item, _test) in toggle.WINDOWS.items():
        assert item in menu_map.MAP, (key, item)
        assert kit_cmds.BY_COMMAND[f"Toggle{label.replace(' ', '')}Window"][4] == {"window": key}


def test_no_floating_window_at_start():
    import bpy
    for key in toggle.WINDOWS:
        assert toggle.floating(bpy.context, key) == [], key
