"""#348: Display > Shapes keeps the Maya Outliner (menu bar, dock handle, Shapes item) and its kit-drawn rows, a
plain Blender Outliner never gets the Maya header, and the layout's Outliners start as kit trees with Shapes off.
The rows themselves: tests/test_outliner_tree.py; GUI: tests/gui/gui_issue348_outliner.py."""

from importlib import import_module
from pathlib import Path
from types import SimpleNamespace

import bpy

import kit

maya_outliner = import_module(kit.MODULE + ".ui.maya_outliner")
outliner_tree = import_module(kit.MODULE + ".ui.outliner_tree")


class Recorder:
    """A stand-in UILayout that records (kind, text, property name) of what a draw function adds."""

    def __init__(self, log=None):
        self.log = [] if log is None else log

    def __getattr__(self, name):
        if name in ("row", "column", "split", "box"):
            return lambda *a, **k: Recorder(self.log)
        if name in ("menu", "operator", "prop", "label", "popover"):
            def add(*args, **kw):
                prop = args[1] if name == "prop" and len(args) > 1 else ""
                self.log.append((name, kw.get("text", args[0] if args and name != "prop" else ""), prop))
                return SimpleNamespace()
            return add
        return lambda *a, **k: None

    def texts(self, kind):
        return [t for k, t, _p in self.log if k == kind]

    def props(self):
        return [p for k, _t, p in self.log if k == "prop"]


def _outliner():
    """The factory Layout screen's Outliner (a real SpaceOutliner) and its area."""
    area = next(a for a in bpy.data.screens["Layout"].areas if a.type == 'OUTLINER')
    return area, area.spaces.active


def _filters(sp):
    return (sp.display_mode, sp.use_filter_collection, sp.use_filter_object_content, sp.show_mode_column,
            sp.show_restrict_column_render, sp.show_restrict_column_hide, sp.use_filter_children, sp.use_sort_alpha,
            sp.show_restrict_column_enable)


def _restore(sp, saved):
    (sp.display_mode, sp.use_filter_collection, sp.use_filter_object_content, sp.show_mode_column,
     sp.show_restrict_column_render, sp.show_restrict_column_hide, sp.use_filter_children, sp.use_sort_alpha,
     sp.show_restrict_column_enable) = saved


def _header(area):
    rec = Recorder()
    self = SimpleNamespace(layout=rec)
    with bpy.context.temp_override(area=area, space_data=area.spaces.active):
        maya_outliner._draw(self, bpy.context)
    return rec


def test_shapes_on_keeps_the_maya_outliner():
    area, sp = _outliner()
    saved = _filters(sp)
    try:
        maya_outliner.setup(sp)
        assert maya_outliner.is_maya_outliner(sp) and outliner_tree.is_tree(sp), "a Maya Outliner (Shapes off)"
        sp.use_filter_object_content = True                      # Display > Shapes on
        assert maya_outliner.is_maya_outliner(sp), "Shapes on is still a Maya Outliner (menu bar stays)"
        assert outliner_tree.is_tree(sp), "Shapes on: still the kit's rows (shape rows added)"
        rec = _header(area)
        assert rec.texts("menu") == ["Display", "Show", "Help"], rec.log
        assert "filter_text" in rec.props(), "search field"
        sp.use_filter_object_content = False                     # Display > Shapes off again, same place
        assert maya_outliner.is_maya_outliner(sp) and outliner_tree.is_tree(sp)
        assert _header(area).texts("menu") == ["Display", "Show", "Help"]
    finally:
        _restore(sp, saved)


def test_display_menu_lists_shapes_while_on():
    area, sp = _outliner()
    saved = _filters(sp)
    try:
        maya_outliner.setup(sp)
        sp.use_filter_object_content = True
        rec = Recorder()
        with bpy.context.temp_override(area=area, space_data=sp):
            maya_outliner.ALLSET_MT_outliner_display.draw(SimpleNamespace(layout=rec), bpy.context)
        assert "Shapes" in rec.texts("prop"), rec.log
    finally:
        _restore(sp, saved)


def test_plain_blender_outliners_keep_blender_header():
    area, sp = _outliner()
    saved = _filters(sp)
    try:
        # the factory Outliner: collections, object contents, mode column and render toggle on
        assert not maya_outliner.is_maya_outliner(sp), _filters(sp)
        assert not outliner_tree.is_tree(sp)
        sp.use_filter_collection = False                         # the user hides collection rows only
        assert not maya_outliner.is_maya_outliner(sp), "a Blender Outliner without collection rows stays Blender's"
        sp.show_mode_column = False
        assert not maya_outliner.is_maya_outliner(sp), "... also without the mode column"
        sp.use_filter_collection, sp.show_mode_column = True, True
        sp.show_restrict_column_render = False
        sp.use_filter_object_content = False
        assert not maya_outliner.is_maya_outliner(sp), "collection rows shown: Blender's"
        sp.use_filter_collection = False
        sp.display_mode = 'SCENES'
        assert not maya_outliner.is_maya_outliner(sp), "Scenes display mode: Blender's"
    finally:
        _restore(sp, saved)


def test_template_outliners_start_without_shapes():
    path = Path(kit.ROOT) / "src" / "allset" / "app_template" / "Maya_Workflow_Kit" / "startup.blend"
    bpy.ops.wm.open_mainfile(filepath=str(path), load_ui=True)
    outliners = [a.spaces.active for ws in bpy.data.workspaces for s in ws.screens for a in s.areas
                 if a.type == 'OUTLINER']
    assert outliners
    for sp in outliners:
        assert not sp.use_filter_object_content, "Maya Outliner starts with Shapes off"
        assert maya_outliner.is_maya_outliner(sp) and outliner_tree.is_tree(sp), "the kit draws the rows"
    outliner_tree.show_all()
    bpy.ops.wm.read_homefile(use_factory_startup=True)
