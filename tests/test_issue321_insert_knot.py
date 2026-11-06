"""#321: Curves > Insert Knot (menu and shelf) inserts knots at the selected curve points and keeps the curve shape,
like Maya: Insert location At selection / Between selections, Multiplicity Increase by / Set to, Keep original.
A selected NURBS CV stands for the curve point where it pulls most; a Bezier / poly point gives the middle between
it and the next point; a curve end changes nothing, like Maya. With no curve point selected it warns and changes
nothing."""

from importlib import import_module

import bpy

import kit

cmaya = import_module(kit.MODULE + ".operators.curves_maya")
cm = import_module(kit.MODULE + ".operators.curves_math")
menu_map = import_module(kit.MODULE + ".ui.menu_map")
shelf_map = import_module(kit.MODULE + ".ui.shelf_map")

ARCH = [(0, 0, 0), (1, 2, 0), (3, 2, 0), (4, 0, 0)]       # one cubic span, parameter 0 .. 1


def _clear():
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)


def _curve(points=ARCH, degree=3):
    _clear()
    ob = cmaya.make_cv_curve(bpy.context, points, degree)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    return ob


def _edit(ob, selected):
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.curve.select_all(action='DESELECT')
    sp = ob.data.splines[0]
    for i, p in enumerate(sp.bezier_points if sp.type == 'BEZIER' else sp.points):
        if sp.type == 'BEZIER':
            p.select_control_point = i in selected
        else:
            p.select = i in selected


def _count(ob):
    sp = ob.data.splines[0]
    return len(sp.bezier_points if sp.type == 'BEZIER' else sp.points)


def _same_shape(before, sp, knots_after):
    """The written spline ``sp`` follows the curve ``before`` exactly: Bezier segment j runs over the parameters
    between the j-th and (j+1)-th distinct knot of ``knots_after``."""
    after = cmaya.read_spline(sp)
    us = sorted(set(knots_after))
    worst = 0.0
    for j, (u0, u1) in enumerate(zip(us, us[1:])):
        for s in range(11):
            t = s / 10
            a = cm.evaluate(before.cvs, before.knots, before.degree, u0 + (u1 - u0) * t)
            b = cm.evaluate(after.cvs, after.knots, after.degree, after.knots[0] + j + t)
            worst = max(worst, cm.norm(cm.sub(a, b)))
    assert worst < 1e-5, worst


def _arch_curve():
    return cmaya.MCurve(ARCH, [0.0, 0.0, 0.0, 1.0, 1.0, 1.0], 3)


def test_mapped():
    assert menu_map.MAP["Curves/Insert Knot"] == "allset.curve_insert_knot"
    assert shelf_map.BY_COMMAND["InsertKnot"][0] == "allset.curve_insert_knot"


def test_knot_insertion_keeps_shape_and_parameters():
    c = _arch_curve()
    n = cmaya.apply_knots(c, [(0.5, 1)])
    assert n.knots == [0, 0, 0, 0.5, 1, 1, 1], n.knots
    want = [(0, 0, 0), (0.5, 1, 0), (2, 2, 0), (3.5, 1, 0), (4, 0, 0)]
    assert all(cm.norm(cm.sub(a, b)) < 1e-9 for a, b in zip(n.cvs, want)), n.cvs
    for times in (2, 3):
        m = cmaya.apply_knots(c, [(0.5, times)])
        assert len(m.cvs) == 4 + times
        for i in range(41):
            u = i / 40
            assert cm.norm(cm.sub(cm.evaluate(c.cvs, c.knots, 3, u), cm.evaluate(m.cvs, m.knots, 3, u))) < 1e-9


def test_knot_targets_like_maya():
    c = _arch_curve()
    kt = cmaya.knot_targets
    p = [0.3, 0.7]
    assert kt(c, p, [0, 1]) == [(0.3, 1), (0.7, 1)]
    assert kt(c, [0.5], [0], number=2) == [(0.5, 2)]
    assert kt(c, [0.5], [0], number=5) == [(0.5, 3)], "never more than the degree"
    assert kt(c, [0.5], [0], number=1, set_to=True) == [(0.5, 1)]
    got = kt(c, p, [0, 1], between=True)
    assert [round(u, 6) for u, _ in got] == [0.3, 0.5, 0.7], got
    got = kt(c, p, [0, 1], between=True, number=3)
    assert [round(u, 6) for u, _ in got] == [0.3, 0.4, 0.5, 0.6, 0.7], got
    got = kt(c, [0.2, 0.4, 0.9], [0, 1, 2], between=True)
    assert [round(u, 6) for u, _ in got] == [0.2, 0.3, 0.4, 0.65, 0.9], got
    assert kt(c, p, [0], between=True) == kt(c, p, [0]), "one point: like At selection"
    # a curve end gives no knot, like Maya
    assert kt(c, [0.0, 0.5, 1.0], [0]) == []
    assert kt(c, [0.0, 0.5, 1.0], [2]) == []
    assert kt(c, [0.0, 0.5, 1.0], [0, 1]) == [(0.5, 1)]


def test_set_to_counts_the_knots_there():
    c = cmaya.MCurve([(0, 0, 0), (1, 1, 0), (2, 0, 0), (3, 1, 0), (4, 0, 0)], [0, 0, 0, 1, 2, 2, 2], 3)
    kt = cmaya.knot_targets
    assert kt(c, [1.0], [0], number=2, set_to=True) == [(1.0, 1)], "one knot there already"
    assert kt(c, [1.0], [0], number=1, set_to=True) == []
    assert kt(c, [1.0], [0], number=1) == [(1.0, 1)]


def test_between_two_cvs_in_the_scene():
    """The ends of a one-span curve: one knot in the middle = Maya's Insert Knot at 0.5 (the knots stay uniform,
    so the curve stays a NURBS curve)."""
    ob = _curve()
    _edit(ob, {0, 3})
    assert bpy.ops.allset.curve_insert_knot(location='BETWEEN') == {'FINISHED'}
    assert bpy.context.mode == 'EDIT_CURVE', "stays in edit mode"
    bpy.ops.object.mode_set(mode='OBJECT')
    assert len(ob.data.splines) == 1
    sp = ob.data.splines[0]
    assert sp.type == 'NURBS' and sp.use_endpoint_u and sp.order_u == 4, sp.type
    got = [tuple(round(c, 6) for c in p.co[:3]) for p in sp.points]
    assert got == [(0, 0, 0), (0.5, 1, 0), (2, 2, 0), (3.5, 1, 0), (4, 0, 0)], got
    assert [p.select for p in sp.points] == [False, False, True, False, False], "the CV at the new knot"


def test_non_uniform_knots_become_bezier():
    ob = _curve()
    before = cmaya.read_spline(ob.data.splines[0])
    _edit(ob, {0, 3})
    assert bpy.ops.allset.curve_insert_knot(location='BETWEEN', number=2) == {'FINISHED'}
    bpy.ops.object.mode_set(mode='OBJECT')
    sp = ob.data.splines[0]
    assert sp.type == 'NURBS' and len(sp.points) == 6, "1/3 and 2/3: still uniform"
    _clear()
    ob = _curve()
    _edit(ob, {1})
    assert bpy.ops.allset.curve_insert_knot(mode='SET', number=2) == {'FINISHED'}
    bpy.ops.object.mode_set(mode='OBJECT')
    sp = ob.data.splines[0]
    assert sp.type == 'BEZIER' and len(sp.bezier_points) == 3, (sp.type, _count(ob))
    _same_shape(before, sp, [0, 0, 0, 1 / 3, 1 / 3, 1, 1, 1])
    assert [p.select_control_point for p in sp.bezier_points] == [False, True, False]


def test_at_one_cv_and_increase_by():
    for number in (1, 3):
        ob = _curve()
        before = cmaya.read_spline(ob.data.splines[0])
        _edit(ob, {1})                      # this CV pulls most at u = 1/3
        assert bpy.ops.allset.curve_insert_knot(number=number) == {'FINISHED'}
        bpy.ops.object.mode_set(mode='OBJECT')
        sp = ob.data.splines[0]
        assert sp.type == 'BEZIER' and len(sp.bezier_points) == 3, _count(ob)
        _same_shape(before, sp, [0, 0, 0, 1 / 3, 1, 1, 1])


def test_keep_original():
    ob = _curve()
    _edit(ob, {1})
    assert bpy.ops.allset.curve_insert_knot(keep_original=True) == {'FINISHED'}
    bpy.ops.object.mode_set(mode='OBJECT')
    assert ob.data.splines[0].type == 'NURBS' and _count(ob) == 4, "the original is left as it was"
    new = [o for o in bpy.data.objects if o is not ob]
    assert len(new) == 1 and "insertedKnotCurve" in new[0].name, [o.name for o in bpy.data.objects]
    assert bpy.context.view_layer.objects.active is new[0] and not ob.select_get()
    assert _count(new[0]) == 3


def test_bezier_and_poly_points():
    _clear()
    bpy.ops.curve.primitive_bezier_curve_add()
    ob = bpy.context.active_object
    before = cmaya.read_spline(ob.data.splines[0])
    _edit(ob, {0})                          # a curve end: nothing changes, like Maya
    assert bpy.ops.allset.curve_insert_knot() == {'CANCELLED'}
    bpy.ops.object.mode_set(mode='OBJECT')
    assert _count(ob) == 2
    _edit(ob, {0, 1})                       # between the two ends: one knot in the middle
    assert bpy.ops.allset.curve_insert_knot(location='BETWEEN') == {'FINISHED'}
    bpy.ops.object.mode_set(mode='OBJECT')
    assert _count(ob) == 3
    _same_shape(before, ob.data.splines[0], [0, 0, 0, 0.5, 0.5, 0.5, 1, 1, 1])
    _edit(ob, {0, 2})
    assert bpy.ops.allset.curve_insert_knot(location='BETWEEN', number=2) == {'FINISHED'}
    bpy.ops.object.mode_set(mode='OBJECT')
    assert _count(ob) == 5, _count(ob)

    ob = _curve([(0, 0, 0), (1, 0, 0), (1, 1, 0)], degree=1)
    _edit(ob, {1})
    assert bpy.ops.allset.curve_insert_knot() == {'FINISHED'}
    bpy.ops.object.mode_set(mode='OBJECT')
    pts = [tuple(round(x, 6) for x in p.co[:3]) for p in ob.data.splines[0].points]
    assert pts == [(0, 0, 0), (1, 0, 0), (1, 0.5, 0), (1, 1, 0)], pts


def test_curve_end_changes_nothing():
    for end in (0, 3):
        ob = _curve()
        before = [tuple(p.co) for p in ob.data.splines[0].points]
        _edit(ob, {end})
        assert bpy.ops.allset.curve_insert_knot() == {'CANCELLED'}
        bpy.ops.object.mode_set(mode='OBJECT')
        assert [tuple(p.co) for p in ob.data.splines[0].points] == before and ob.data.splines[0].type == 'NURBS'


def test_nothing_selected_or_object_mode():
    ob = _curve()
    assert bpy.ops.allset.curve_insert_knot() == {'CANCELLED'}
    _edit(ob, set())
    assert bpy.ops.allset.curve_insert_knot() == {'CANCELLED'}
    bpy.ops.object.mode_set(mode='OBJECT')
    assert _count(ob) == 4


def test_curve_option_boxes():
    """Insert Knot ❒ runs it with its settings in Adjust Last Operation; degree / spans of new and existing curves
    are in the CV / EP Curve Tool and Rebuild option windows."""
    menu_sets = import_module(kit.MODULE + ".ui.menu_sets")
    assert menu_sets.option_kind("Curves/Insert Knot") == "redo"
    for path in ("Create/Curve Tools/CV Curve Tool", "Create/Curve Tools/EP Curve Tool", "Curves/Rebuild"):
        assert menu_sets.option_kind(path) == "window", path
