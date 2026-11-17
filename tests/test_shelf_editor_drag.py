"""Shelf Editor Drag (a preference, off by default): the Shelf Contents rows get a grip only while it is on, and a
drag puts the picked button at the row it is dropped on."""

from importlib import import_module
from types import SimpleNamespace

import bpy

import kit

drag = import_module(kit.MODULE + ".ui.shelf_editor_drag")
shelf_editor = import_module(kit.MODULE + ".ui.shelf_editor")
preferences = import_module(kit.MODULE + ".preferences")


def test_moved():
    order = ["A", "B", "C", "D"]
    assert drag.moved(order, 0, 2) == ["B", "C", "A", "D"]
    assert drag.moved(order, 3, 0) == ["D", "A", "B", "C"]
    assert drag.moved(order, 1, 1) == order and order == ["A", "B", "C", "D"], "the original list stays"


def test_off_by_default():
    prefs = preferences.get()
    assert prefs.bl_rna.properties["shelf_editor_drag"].default is False
    assert hasattr(bpy.types, "ALLSET_OT_shelf_editor_drag_button")


class _Layout:
    def __init__(self, log):
        self.log = log

    def operator(self, idname, **kw):
        self.log.append((idname, kw.get("icon")))
        return SimpleNamespace()

    def __getattr__(self, name):
        return lambda *a, **k: _Layout(self.log)


def _drawn():
    log = []
    wm = SimpleNamespace(allset_se_index=-1)
    item = SimpleNamespace(is_factory=False, icon='SCRIPT', label="A", button_index=0)
    shelf_editor.ALLSET_UL_shelf_editor_contents.draw_item(None, bpy.context, _Layout(log), wm, item, 0, wm, "")
    return log


def test_grip_drawn_only_while_on():
    prefs = preferences.get()
    prefs.shelf_editor_drag = False
    try:
        assert ("allset.shelf_editor_drag_button", 'GRIP') not in _drawn()
        prefs.shelf_editor_drag = True
        assert _drawn()[0] == ("allset.shelf_editor_drag_button", 'GRIP'), _drawn()
    finally:
        prefs.shelf_editor_drag = False


def test_row_height_follows_the_interface_scale():
    ctx = SimpleNamespace(preferences=SimpleNamespace(system=SimpleNamespace(ui_scale=1.0, pixel_size=1)))
    assert drag.row_px(ctx) == 20
    ctx.preferences.system.ui_scale = 2.0
    assert drag.row_px(ctx) == 38
