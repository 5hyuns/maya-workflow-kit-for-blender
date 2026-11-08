"""Graph Editor List > Bookmarks like Maya: Bookmark Current Objects makes a set (Bookmark, Bookmark1, ...) of the listed
objects without asking a name, Bookmark Selected Curves a set that remembers the selected curves, selecting a
bookmark set selects its objects, the List > Bookmarks menu loads one, Remove All Bookmarks deletes them."""

from importlib import import_module

import bpy

import kit
from test_remove_keys import Editor, _scene

gb = import_module(kit.MODULE + ".operators.graph_bookmarks")
sets = import_module(kit.MODULE + ".operators.sets")
ec = import_module(kit.MODULE + ".ui.editor_chrome")
menu_map = import_module(kit.MODULE + ".ui.editor_menu_map")


def _shown():
    sp = bpy.context.space_data
    return sorted(ob.name for ob in ec.listed_objects(bpy.context, sp))


def _clear():
    for coll in gb.bookmarks():
        sets.delete(coll)


def test_menu_item():
    assert menu_map.MAP["Graph Editor/List/Bookmarks"] == ("menu", "ALLSET_MT_graph_bookmarks")


def test_bookmark_objects_sets_load_and_remove():
    _clear()
    a, b = _scene()
    with Editor():
        bpy.context.space_data.dopesheet.show_only_selected = False     # Auto Load off: Load works
        for ob in (a, b):
            ob.select_set(ob is a)
        bpy.context.view_layer.objects.active = a
        assert bpy.ops.allset.graph_list(action='LOAD') == {'FINISHED'}
        assert _shown() == ["A"]
        assert bpy.ops.allset.graph_bookmark(action='OBJECTS') == {'FINISHED'}
        a.select_set(False)
        b.select_set(True)
        bpy.ops.allset.graph_list(action='LOAD')
        assert bpy.ops.allset.graph_bookmark(action='OBJECTS') == {'FINISHED'}
        marks = gb.bookmarks()
        assert [c.name for c in marks] == ["Bookmark", "Bookmark1"], "named like Maya, no name asked"
        assert all(sets.is_set(c) for c in marks), "a bookmark is a set (Outliner set row)"
        assert [o.name for o in marks[0].objects] == ["A"] and [o.name for o in marks[1].objects] == ["B"]
        assert bpy.ops.allset.graph_bookmark(action='LOAD', name="Bookmark") == {'FINISHED'}
        assert _shown() == ["A"], "loading the bookmark lists its objects again"
        rows = ec.listed_nodes(bpy.context, bpy.context.space_data)
        assert [(k, n.name) for k, n, _c in rows][:2] == [("SET", "Bookmark"), ("OBJECT", "A")],             "the bookmark's set row first, its objects below (Maya lists a selected set)"
        assert not ec.auto_load(bpy.context.space_data)
        sets.select_members(bpy.context, marks[1])
        assert [o.name for o in bpy.context.selected_objects] == ["B"], "selecting the set selects its objects"
        bpy.ops.allset.graph_list(action='LOAD')
        rows = ec.listed_nodes(bpy.context, bpy.context.space_data)
        assert [k for k, _n, _c in rows].count("SET") == 0, "another list: no bookmark row"
        assert bpy.ops.allset.graph_bookmark(action='REMOVE_ALL') == {'FINISHED'}
        assert gb.bookmarks() == []


def test_bookmark_selected_curves():
    _clear()
    a, b = _scene()
    fcs = kit.fcurves(a)
    for fc in fcs:
        fc.select = fc.array_index == 1
    for fc in kit.fcurves(b):
        fc.select = False
    with Editor():
        bpy.context.space_data.dopesheet.filter_collection = None
        bpy.context.space_data.dopesheet.show_only_selected = True      # Auto Load: the selected A and B
        assert bpy.ops.allset.graph_bookmark(action='CURVES') == {'FINISHED'}
        mark = gb.bookmarks()[-1]
        assert mark.name == "Bookmark" and gb.curves_of(mark) == [("A", "location", 1)], gb.curves_of(mark)
        assert [o.name for o in mark.objects] == ["A"]
        assert bpy.ops.allset.graph_bookmark(action='LOAD', name="Bookmark") == {'FINISHED'}
        assert _shown() == ["A"]
        assert [fc.hide for fc in sorted(fcs, key=lambda f: f.array_index)] == [True, False]
        bpy.ops.allset.graph_bookmark(action='REMOVE_ALL')
    for fc in fcs:
        fc.hide = False


def test_menu_lists_the_bookmarks():
    import types
    from test_step56_time_keys import Recorder
    _clear()
    gb.make([], ())
    rec = Recorder()
    gb.ALLSET_MT_graph_bookmarks.draw(types.SimpleNamespace(layout=rec), bpy.context)
    assert rec.texts() == ["Bookmark Current Objects", "Bookmark Selected Curves", "Remove All Bookmarks", "Bookmark"]
    _clear()


def test_tooltip_names_each_action():
    """The menu items' tooltips come from the action's own text (no error while the tooltip is built)."""
    props = bpy.context.window_manager.operator_properties_last("allset.graph_bookmark")
    texts = {}
    for action in ("OBJECTS", "CURVES", "LOAD", "REMOVE_ALL"):
        props.action = action
        texts[action] = gb.ALLSET_OT_graph_bookmark.description(bpy.context, props)
    assert texts["OBJECTS"].startswith("Keep the objects"), texts
    assert texts["REMOVE_ALL"].startswith("Delete every"), texts
    assert len(set(texts.values())) == 4, texts
