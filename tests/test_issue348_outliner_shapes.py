"""#348: Display > Shapes keeps the Maya Outliner (menu bar, dock handle, Shapes item), the root-joint label is
drawn only while Shapes is off, a plain Blender Outliner never gets the Maya header, and a joint picked while Shapes
is on is revealed in the Outliner tree (one-shot, on a selection change only).
GUI: tests/gui/gui_issue348_outliner.py."""

from importlib import import_module
from pathlib import Path
from types import SimpleNamespace

import bpy

import kit

maya_outliner = import_module(kit.MODULE + ".ui.maya_outliner")


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
            sp.show_restrict_column_render, sp.show_restrict_column_hide, sp.use_filter_children, sp.use_sort_alpha)


def _restore(sp, saved):
    (sp.display_mode, sp.use_filter_collection, sp.use_filter_object_content, sp.show_mode_column,
     sp.show_restrict_column_render, sp.show_restrict_column_hide, sp.use_filter_children, sp.use_sort_alpha) = saved


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
        assert maya_outliner.is_maya_outliner(sp), "a Maya Outliner (Shapes off)"
        assert maya_outliner.shows_dag_only(sp), "Shapes off: DAG rows only (the root-joint label is drawn)"
        sp.use_filter_object_content = True                      # Display > Shapes on
        assert maya_outliner.is_maya_outliner(sp), "Shapes on is still a Maya Outliner (menu bar stays)"
        assert not maya_outliner.shows_dag_only(sp), "Shapes on: Blender's rows show the bones, no root-joint label"
        assert maya_outliner.shapes_shown(sp)
        rec = _header(area)
        assert rec.texts("menu") == ["Display", "Show", "Help"], rec.log
        assert "filter_text" in rec.props(), "search field"
        sp.use_filter_object_content = False                     # Display > Shapes off again, same place
        assert maya_outliner.is_maya_outliner(sp) and maya_outliner.shows_dag_only(sp)
        assert not maya_outliner.shapes_shown(sp)
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
        assert not maya_outliner.shows_dag_only(sp)
        assert not maya_outliner.shapes_shown(sp)
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
        assert maya_outliner.is_maya_outliner(sp) and maya_outliner.shows_dag_only(sp)
    bpy.ops.wm.read_homefile(use_factory_startup=True)


def _skeleton():
    arm = bpy.data.armatures.new("skeleton348")
    ob = bpy.data.objects.new("skeleton348", arm)
    bpy.context.scene.collection.objects.link(ob)
    for o in bpy.context.view_layer.objects:
        o.select_set(o == ob)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT')
    prev = None
    for i in range(3):
        b = arm.edit_bones.new(f"joint{i + 1}")
        b.head, b.tail = (0, 0, i), (0, 0, i + 1)
        if prev:
            b.parent, b.use_connect = prev, True
        prev = b
    bpy.ops.object.mode_set(mode='POSE')
    return ob


def test_picked_joint_and_one_shot_reveal():
    ob = _skeleton()
    try:
        pose = ob.pose.bones
        for pb in pose:
            pb.select = False
        assert maya_outliner.picked_joint(bpy.context.view_layer) is None, "nothing picked"
        pose["joint3"].select = True
        ob.data.bones.active = ob.data.bones["joint3"]
        assert maya_outliner.picked_joint(bpy.context.view_layer) == (ob.name, 'POSE', "joint3")
        if bpy.app.timers.is_registered(maya_outliner._reveal):
            bpy.app.timers.unregister(maya_outliner._reveal)
        maya_outliner._last["key"] = None
        maya_outliner._on_depsgraph(bpy.context.scene, None)
        assert bpy.app.timers.is_registered(maya_outliner._reveal), "a new pick schedules one reveal"
        bpy.app.timers.unregister(maya_outliner._reveal)
        maya_outliner._on_depsgraph(bpy.context.scene, None)
        assert not bpy.app.timers.is_registered(maya_outliner._reveal), "the same pick again: nothing to do"
        assert maya_outliner.reveal(bpy.context) == 0, "no window Outliner with Shapes on in background mode"
        pose["joint3"].select = False
        assert maya_outliner.picked_joint(bpy.context.view_layer) is None, "active joint deselected: nothing picked"
        bpy.ops.object.mode_set(mode='EDIT')
        eb = ob.data.edit_bones["joint2"]
        for e in ob.data.edit_bones:
            e.select = e.select_head = e.select_tail = False
        eb.select = True
        ob.data.edit_bones.active = eb
        assert maya_outliner.picked_joint(bpy.context.view_layer) == (ob.name, 'EDIT', "joint2")
        bpy.ops.object.mode_set(mode='OBJECT')
        assert maya_outliner.picked_joint(bpy.context.view_layer) is None, "Object Mode: the object is picked, not a joint"
    finally:
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.data.objects.remove(ob)


def test_handler_follows_register():
    assert maya_outliner._on_depsgraph in bpy.app.handlers.depsgraph_update_post
    kit.disable()
    try:
        assert not any(getattr(f, "__module__", "") == maya_outliner.__name__
                   for f in bpy.app.handlers.depsgraph_update_post), "handler removed"
        assert not bpy.app.timers.is_registered(maya_outliner._reveal)
    finally:
        kit.enable()
