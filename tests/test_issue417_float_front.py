"""#417: asking for a floating panel brings it to the front (the reopening itself: tests/gui/gui_issue417_float_front.py).
Headless: the menu item only shows the Tool Settings, and bringing a window to the front changes nothing without a GUI."""

from importlib import import_module

import bpy

import kit

menu_map = import_module(kit.MODULE + ".ui.menu_map")
maya_dock = import_module(kit.MODULE + ".ui.maya_dock")
window_places = import_module(kit.MODULE + ".ui.window_places")


def _rows():
    for name in dir(menu_map):
        table = getattr(menu_map, name)
        if isinstance(table, dict) and "General Editors/Tool Settings" in table:
            return table
    raise AssertionError("no menu table holds General Editors/Tool Settings")


def test_tool_settings_item_only_shows():
    action = _rows()["General Editors/Tool Settings"]
    assert action[0] == "allset.editor_toggle", action
    assert action[1] == {"editor": 'TOOL_SETTINGS', "show": True}, action


def test_to_front_without_gui_keeps_the_window():
    window = bpy.context.window_manager.windows[0]
    before = len(bpy.context.window_manager.windows)
    assert maya_dock.to_front(bpy.context, window) == window
    assert maya_dock.to_front(bpy.context, None) is None
    assert len(bpy.context.window_manager.windows) == before


def test_no_floating_window_in_one_window():
    for kind in maya_dock.KINDS:
        assert maya_dock.floating_window(kind) is None


def test_handed_on_keeps_the_name():
    class W:
        def __init__(self, ptr):
            self.ptr, self.x, self.y, self.width, self.height = ptr, 10, 20, 300, 400

        def as_pointer(self):
            return self.ptr
    old, new = W(1001), W(1002)
    window_places._tracked[old.ptr] = "test_kind"
    try:
        window_places.handed_on(old, new)
        assert window_places._tracked.get(new.ptr) == "test_kind"
        assert window_places.place("test_kind") == [10, 20, 300, 400]
        window_places.handed_on(W(1003), W(1004))          # an untracked window: nothing tracked
        assert 1004 not in window_places._tracked
    finally:
        for p in (1001, 1002):
            window_places._tracked.pop(p, None)
        window_places._places.pop("test_kind", None)
