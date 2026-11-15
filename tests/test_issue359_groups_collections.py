"""#359: Maya groups and Blender collections — a new group goes into the collection its members share, else into the
active collection (never into a kit set or a display layer); Outliner Display > Blender Collections shows the
collections with Blender's own rows and header, and the header's Maya Outliner goes back."""

from importlib import import_module
from types import SimpleNamespace

import bpy

import kit

maya_outliner = import_module(kit.MODULE + ".ui.maya_outliner")
outliner_tree = import_module(kit.MODULE + ".ui.outliner_tree")
group = import_module(kit.MODULE + ".operators.group")


class Recorder:
    """A stand-in UILayout that records (kind, text) of what a draw function adds."""

    def __init__(self, log=None):
        self.log = [] if log is None else log

    def __getattr__(self, name):
        if name in ("row", "column", "split", "box"):
            return lambda *a, **k: Recorder(self.log)
        if name in ("menu", "operator", "prop", "label"):
            def add(*args, **kw):
                self.log.append((name, kw.get("text", args[0] if args and name != "prop" else "")))
                return SimpleNamespace()
            return add
        return lambda *a, **k: None

    def texts(self, kind):
        return [t for k, t in self.log if k == kind]


def _fresh():
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)


def _coll(name, parent=None):
    c = bpy.data.collections.new(name)
    (parent or bpy.context.scene.collection).children.link(c)
    return c


def _obj(name, coll):
    ob = bpy.data.objects.new(name, bpy.data.meshes.new(name))
    coll.objects.link(ob)
    return ob


def _select(*obs):
    vl = bpy.context.view_layer
    vl.update()
    for o in vl.objects:
        o.select_set(o in obs)
    vl.objects.active = obs[0]


def _active(name):
    vl = bpy.context.view_layer
    vl.active_layer_collection = vl.layer_collection.children[name]


def _group():
    assert bpy.ops.allset.group() == {'FINISHED'}
    return bpy.context.view_layer.objects.active


def test_members_in_different_collections_go_to_the_active_one():
    _fresh()
    props, nested, groups = _coll("Props"), _coll("Nested"), _coll("Groups")
    a, b = _obj("chair", props), _obj("table", nested)
    _active("Groups")
    _select(a, b)
    grp = _group()
    assert [c.name for c in grp.users_collection] == ["Groups"], [c.name for c in grp.users_collection]
    assert grp.type == 'EMPTY' and set(grp.children) == {a, b}


def test_members_sharing_a_collection_keep_the_group_there():
    _fresh()
    props, other = _coll("Props"), _coll("Other")
    a, b = _obj("chair", props), _obj("table", props)
    _active("Other")
    _select(b, a)
    grp = _group()
    assert [c.name for c in grp.users_collection] == ["Props"]


def test_never_into_a_kit_set_or_an_excluded_collection():
    _fresh()
    props = _coll("Props")
    a, b = _obj("chair", props), _obj("table", props)
    kit_set = bpy.data.collections.new("set1")        # a kit set: a collection linked to no scene
    kit_set.use_fake_user = True
    hidden = _coll("Layers")                          # like the Display Layers collections: excluded
    bpy.context.view_layer.layer_collection.children["Layers"].exclude = True
    for ob in (a, b):
        kit_set.objects.link(ob)
        hidden.objects.link(ob)
    _active("Props")
    _select(a, b)
    grp = _group()
    assert [c.name for c in grp.users_collection] == ["Props"], [c.name for c in grp.users_collection]


def test_nothing_selected_goes_to_the_active_collection():
    _fresh()
    _coll("Props")
    groups = _coll("Groups")
    _active("Groups")
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    grp = _group()
    assert grp.users_collection[0] == groups and not grp.children


def _outliner():
    area = next(a for a in bpy.data.screens["Layout"].areas if a.type == 'OUTLINER')
    return area, area.spaces.active


def _filters(sp):
    return (sp.display_mode, sp.use_filter_collection, sp.use_filter_object, sp.use_filter_object_content,
            sp.show_mode_column, sp.show_restrict_column_render, sp.show_restrict_column_hide,
            sp.use_filter_children, outliner_tree.sort_alpha(sp))


def _restore(sp, saved):
    (sp.display_mode, sp.use_filter_collection, sp.use_filter_object, sp.use_filter_object_content,
     sp.show_mode_column, sp.show_restrict_column_render, sp.show_restrict_column_hide,
     sp.use_filter_children, alpha) = saved
    outliner_tree.set_sort_alpha(sp, alpha)


def _header(area):
    rec = Recorder()
    with bpy.context.temp_override(area=area, space_data=area.spaces.active):
        maya_outliner._draw(SimpleNamespace(layout=rec), bpy.context)
    return rec


def test_display_blender_collections_and_back():
    area, sp = _outliner()
    saved = _filters(sp)
    try:
        maya_outliner.setup(sp)
        assert maya_outliner.is_maya_outliner(sp) and outliner_tree.is_tree(sp)
        rec = Recorder()
        with bpy.context.temp_override(area=area, space_data=sp):
            maya_outliner.ALLSET_MT_outliner_display.draw(SimpleNamespace(layout=rec), bpy.context)
        assert "Blender Collections" in rec.texts("operator"), rec.log
        with bpy.context.temp_override(area=area, space_data=sp):
            assert bpy.ops.allset.outliner_collections(show=True) == {'FINISHED'}
        assert sp.use_filter_collection and sp.use_filter_object
        assert not maya_outliner.is_maya_outliner(sp) and not outliner_tree.is_tree(sp)
        assert maya_outliner.is_collection_view(sp)
        assert "Maya Outliner" in _header(area).texts("operator")
        with bpy.context.temp_override(area=area, space_data=sp):
            assert bpy.ops.allset.outliner_collections(show=False) == {'FINISHED'}
        assert maya_outliner.is_maya_outliner(sp) and outliner_tree.is_tree(sp)
        assert "Maya Outliner" not in _header(area).texts("operator")
    finally:
        _restore(sp, saved)
