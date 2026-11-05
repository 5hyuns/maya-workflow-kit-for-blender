"""Graph Editor List > Bookmarks like Maya: Bookmark Current Objects keeps the listed objects under a name, Bookmark
Selected Curves keeps the selected curves, choosing a bookmark loads it, Remove All Bookmarks deletes them."""

from importlib import import_module

import bpy

import kit
from test_remove_keys import Editor, _scene

gb = import_module(kit.MODULE + ".operators.graph_bookmarks")
ec = import_module(kit.MODULE + ".ui.editor_chrome")
menu_map = import_module(kit.MODULE + ".ui.editor_menu_map")


def _shown():
    sp = bpy.context.space_data
    return sorted(ob.name for ob in ec.listed_objects(bpy.context, sp))


def test_menu_item():
    assert menu_map.MAP["Graph Editor/List/Bookmarks"] == ("menu", "ALLSET_MT_graph_bookmarks")


def test_bookmark_objects_load_and_remove():
    a, b = _scene()
    sc = bpy.context.scene
    with Editor():
        bpy.context.space_data.dopesheet.show_only_selected = False     # Auto Load off: Load works
        for ob in (a, b):
            ob.select_set(ob is a)
        bpy.context.view_layer.objects.active = a
        assert bpy.ops.allset.graph_list(action='LOAD') == {'FINISHED'}
        assert _shown() == ["A"]
        assert gb.next_name(sc) == "Bookmark1"
        assert bpy.ops.allset.graph_bookmark(action='OBJECTS', name="") == {'FINISHED'}
        assert [m["name"] for m in gb.bookmarks(sc)] == ["Bookmark1"]
        assert list(gb.bookmarks(sc)[0]["objects"]) == ["A"]
        a.select_set(False)
        b.select_set(True)
        bpy.ops.allset.graph_list(action='LOAD')
        assert _shown() == ["B"]
        assert bpy.ops.allset.graph_bookmark(action='OBJECTS', name="mine") == {'FINISHED'}
        assert bpy.ops.allset.graph_bookmark(action='LOAD', index=0) == {'FINISHED'}
        assert _shown() == ["A"], "loading the bookmark lists its objects again"
        assert not ec.auto_load(bpy.context.space_data)
        assert [m["name"] for m in gb.bookmarks(sc)] == ["Bookmark1", "mine"]
        assert bpy.ops.allset.graph_bookmark(action='REMOVE_ALL') == {'FINISHED'}
        assert gb.bookmarks(sc) == [] and gb.STORE not in sc


def test_bookmark_selected_curves():
    a, b = _scene()
    sc = bpy.context.scene
    fcs = kit.fcurves(a)
    for fc in fcs:
        fc.select = fc.array_index == 1
    for fc in kit.fcurves(b):
        fc.select = False
    with Editor():
        bpy.context.space_data.dopesheet.filter_collection = None
        bpy.context.space_data.dopesheet.show_only_selected = True      # Auto Load: the selected A and B
        assert bpy.ops.allset.graph_bookmark(action='CURVES') == {'FINISHED'}
        mark = gb.bookmarks(sc)[-1]
        assert mark["curves"] == [("A", "location", 1)], mark["curves"]
        assert mark["name"] == "Bookmark1"
        assert bpy.ops.allset.graph_bookmark(action='LOAD', index=0) == {'FINISHED'}
        assert _shown() == ["A"]
        assert [fc.hide for fc in sorted(fcs, key=lambda f: f.array_index)] == [True, False]
        bpy.ops.allset.graph_bookmark(action='REMOVE_ALL')
    for fc in fcs:
        fc.hide = False


def test_menu_lists_the_bookmarks():
    import types
    from test_step56_time_keys import Recorder
    sc = bpy.context.scene
    sc[gb.STORE] = [{"name": "walk", "objects": ["A"], "bones": [], "curves": []}]
    rec = Recorder()
    gb.ALLSET_MT_graph_bookmarks.draw(types.SimpleNamespace(layout=rec), bpy.context)
    assert rec.texts() == ["Bookmark Current Objects", "Bookmark Selected Curves", "Remove All Bookmarks", "walk"]
    del sc[gb.STORE]
