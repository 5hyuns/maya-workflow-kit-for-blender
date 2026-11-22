"""Issue #472: Linear Pre / Post Infinity continues the curve along the end key's outer tangent (flat for an Auto or
a Linear end key), and each side keeps its own infinity type, like Maya."""

from importlib import import_module

import bpy

import kit

mt = import_module(kit.MODULE + ".operators.maya_tangents")
compat = import_module(kit.MODULE + ".compat")

KEYS = ((1, 0.0), (10, 5.0), (20, 2.0))


def _fc(ob):
    return next(fc for fc in compat.id_fcurves(ob) if fc.data_path == "location" and fc.array_index == 0)


def _curve(kind=None):
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for act in list(bpy.data.actions):
        bpy.data.actions.remove(act)
    ob = bpy.data.objects.new("n", None)
    bpy.context.scene.collection.objects.link(ob)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    for f, v in KEYS:
        ob.location.x = v
        ob.keyframe_insert("location", index=0, frame=f)
    fc = _fc(ob)
    mt.apply(fc)
    if kind is not None:
        for kp in fc.keyframe_points:
            kp.select_control_point = True
        _graph(lambda: bpy.ops.allset.set_tangent(kind=kind))
    return ob


def _graph(call):
    area = bpy.context.window_manager.windows[0].screen.areas[0]
    old = area.ui_type
    area.ui_type = 'FCURVES'
    region = next(r for r in area.regions if r.type == 'WINDOW')
    try:
        with bpy.context.temp_override(area=area, region=region):
            return call()
    finally:
        area.ui_type = old


def _infinity(ob, side, mode):
    fc = _fc(ob)
    with bpy.context.temp_override(selected_editable_fcurves=[fc], editable_fcurves=[fc]):
        assert bpy.ops.allset.curve_infinity(side=side, mode=mode) == {'FINISHED'}
    return _fc(ob)


def _secant(i, j):
    (ta, va), (tb, vb) = KEYS[i], KEYS[j]
    return (vb - va) / (tb - ta)


def test_auto_end_keys_stay_flat_with_linear_infinity():
    ob = _curve()
    _infinity(ob, 'POST', 'LINEAR')
    fc = _infinity(ob, 'PRE', 'LINEAR')
    assert fc.extrapolation == 'LINEAR'
    for t in (-20, -5, 0):
        assert abs(fc.evaluate(t) - KEYS[0][1]) < 1e-5, (t, fc.evaluate(t))
    for t in (21, 30, 45):
        assert abs(fc.evaluate(t) - KEYS[-1][1]) < 1e-5, (t, fc.evaluate(t))
    # Blender recomputing the handles (a Graph Editor edit) and the kit writing them again keeps the ends flat
    fc.update()
    mt.apply(fc)
    assert abs(fc.evaluate(-10) - KEYS[0][1]) < 1e-5 and abs(fc.evaluate(30) - KEYS[-1][1]) < 1e-5


def test_linear_end_keys_are_flat_outside():
    ob = _curve("LINEAR")
    _infinity(ob, 'PRE', 'LINEAR')
    fc = _infinity(ob, 'POST', 'LINEAR')
    assert abs(fc.evaluate(-10) - KEYS[0][1]) < 1e-5, fc.evaluate(-10)
    assert abs(fc.evaluate(30) - KEYS[-1][1]) < 1e-5, fc.evaluate(30)


def test_each_side_keeps_its_own_infinity():
    ob = _curve("SPLINE")          # Spline end keys: the outer tangent is the secant to the neighbour
    fc = _infinity(ob, 'POST', 'LINEAR')
    post = KEYS[-1][1] + _secant(1, 2) * 10
    assert abs(fc.evaluate(30) - post) < 1e-4, (fc.evaluate(30), post)
    assert abs(fc.evaluate(-9) - KEYS[0][1]) < 1e-5, ("pre stays constant", fc.evaluate(-9))
    fc = _infinity(ob, 'PRE', 'LINEAR')
    pre = KEYS[0][1] - _secant(0, 1) * 10
    assert abs(fc.evaluate(-9) - pre) < 1e-4, (fc.evaluate(-9), pre)
    assert abs(fc.evaluate(30) - post) < 1e-4
    fc = _infinity(ob, 'POST', 'CONSTANT')
    assert abs(fc.evaluate(30) - KEYS[-1][1]) < 1e-5, ("post constant", fc.evaluate(30))
    assert abs(fc.evaluate(-9) - pre) < 1e-4, ("pre stays linear", fc.evaluate(-9))
    # the inside of the curve is not touched by the infinity
    mid = fc.evaluate(5)
    _infinity(ob, 'PRE', 'CONSTANT')
    fc = _infinity(ob, 'POST', 'LINEAR')
    assert abs(fc.evaluate(5) - mid) < 1e-6
    assert abs(fc.evaluate(-9) - KEYS[0][1]) < 1e-5 and abs(fc.evaluate(30) - post) < 1e-4
    # Blender recomputing the handles, then the kit: the sides stay as set
    fc.update()
    mt.apply(fc)
    assert abs(fc.evaluate(-9) - KEYS[0][1]) < 1e-5 and abs(fc.evaluate(30) - post) < 1e-4


def test_cycle_on_one_side_and_linear_on_the_other():
    ob = _curve("SPLINE")
    _infinity(ob, 'PRE', 'CYCLE')
    fc = _infinity(ob, 'POST', 'LINEAR')
    assert abs(fc.evaluate(-4) - fc.evaluate(15)) < 1e-4, "pre cycles"
    post = KEYS[-1][1] + _secant(1, 2) * 10
    assert abs(fc.evaluate(30) - post) < 1e-4, (fc.evaluate(30), post)
    fc = _infinity(ob, 'POST', 'CONSTANT')
    assert fc.extrapolation == 'CONSTANT' and abs(fc.evaluate(30) - KEYS[-1][1]) < 1e-5
