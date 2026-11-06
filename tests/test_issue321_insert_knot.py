"""#321: Curves > Insert Knot (menu and shelf) inserts control points on the selected curve points: between two
neighbouring selected points, or after a point selected alone (before it at the end of an open curve). With no
curve point selected it warns and changes nothing."""

from importlib import import_module

import bpy

import kit

cmaya = import_module(kit.MODULE + ".operators.curves_maya")
menu_map = import_module(kit.MODULE + ".ui.menu_map")
shelf_map = import_module(kit.MODULE + ".ui.shelf_map")


def _curve():
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    ob = cmaya.make_cv_curve(bpy.context, [(0, 0, 0), (1, 1, 0), (2, 0, 0), (3, 1, 0), (4, 0, 0)])
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    return ob


def _edit(ob, selected):
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.curve.select_all(action='DESELECT')
    for i, p in enumerate(ob.data.splines[0].points):
        p.select = i in selected


def _count(ob):
    return len(ob.data.splines[0].points)


def test_knot_pairs():
    kp = cmaya.knot_pairs
    assert kp([1], 5, False) == {2}
    assert kp([4], 5, False) == {3}, "the last point of an open curve takes the one before"
    assert kp([4], 5, True) == {0}, "a closed curve wraps"
    assert kp([1, 2], 5, False) == set(), "neighbours already: nothing to add"
    assert kp([0, 3], 5, False) == {1, 4}
    assert kp([], 5, False) == set()


def test_mapped():
    assert menu_map.MAP["Curves/Insert Knot"] == "allset.curve_insert_knot"
    assert shelf_map.BY_COMMAND["InsertKnot"][0] == "allset.curve_insert_knot"


def test_one_point():
    ob = _curve()
    _edit(ob, {1})
    assert bpy.ops.allset.curve_insert_knot() == {'FINISHED'}
    bpy.ops.object.mode_set(mode='OBJECT')
    assert _count(ob) == 6, _count(ob)


def test_two_neighbours_and_number():
    ob = _curve()
    _edit(ob, {2, 3})
    assert bpy.ops.allset.curve_insert_knot(number=2) == {'FINISHED'}
    bpy.ops.object.mode_set(mode='OBJECT')
    assert _count(ob) == 7, _count(ob)


def test_nothing_selected_or_object_mode():
    ob = _curve()
    assert bpy.ops.allset.curve_insert_knot() == {'CANCELLED'}
    _edit(ob, set())
    assert bpy.ops.allset.curve_insert_knot() == {'CANCELLED'}
    bpy.ops.object.mode_set(mode='OBJECT')
    assert _count(ob) == 5


def test_curve_option_boxes():
    """Insert Knot ❒ runs it with its setting in Adjust Last Operation; degree / spans of new and existing curves
    are in the CV / EP Curve Tool and Rebuild option windows."""
    menu_sets = import_module(kit.MODULE + ".ui.menu_sets")
    assert menu_sets.option_kind("Curves/Insert Knot") == "redo"
    for path in ("Create/Curve Tools/CV Curve Tool", "Create/Curve Tools/EP Curve Tool", "Curves/Rebuild"):
        assert menu_sets.option_kind(path) == "window", path
