"""Issue #471: a Linear tangent points that key's in / out tangent at the neighbouring key; a segment is a straight
line only when the keys at both of its ends are linear on the sides facing it, like Maya."""

from importlib import import_module

import bpy

import kit

mt = import_module(kit.MODULE + ".operators.maya_tangents")
graph_keys = import_module(kit.MODULE + ".operators.graph_keys")
compat = import_module(kit.MODULE + ".compat")

KEYS = ((1, 0.0), (10, 5.0), (20, 2.0))


def _curve():
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
    fc = next(fc for fc in compat.id_fcurves(ob) if fc.data_path == "location" and fc.array_index == 0)
    mt.apply(fc)
    return ob, fc


def _graph_area():
    area = bpy.context.window_manager.windows[0].screen.areas[0]
    old = area.ui_type
    area.ui_type = 'FCURVES'
    region = next(r for r in area.regions if r.type == 'WINDOW')
    return area, region, old


def _set(ob, frames, kind, side="BOTH"):
    fc = _fc(ob)
    for kp in fc.keyframe_points:
        kp.select_control_point = int(round(kp.co.x)) in frames
    area, region, old = _graph_area()
    try:
        with bpy.context.temp_override(area=area, region=region):
            assert bpy.ops.allset.set_tangent(kind=kind, side=side) == {'FINISHED'}
    finally:
        area.ui_type = old
    return _fc(ob)


def _fc(ob):
    return next(fc for fc in compat.id_fcurves(ob) if fc.data_path == "location" and fc.array_index == 0)


def _slopes(kp):
    lin = (kp.co.y - kp.handle_left.y) / (kp.co.x - kp.handle_left.x)
    rout = (kp.handle_right.y - kp.co.y) / (kp.handle_right.x - kp.co.x)
    return lin, rout


def _chord_gap(fc, a, b):
    """Largest distance of the curve from the straight line between the keys at frames a and b."""
    va, vb = fc.evaluate(a), fc.evaluate(b)
    gap = 0.0
    for i in range(1, 20):
        t = a + (b - a) * i / 20.0
        gap = max(gap, abs(fc.evaluate(t) - (va + (vb - va) * (t - a) / (b - a))))
    return gap


def _secant(i, j):
    (ta, va), (tb, vb) = KEYS[i], KEYS[j]
    return (vb - va) / (tb - ta)


def test_linear_on_one_key_keeps_both_segments_curved():
    ob, _fc0 = _curve()
    fc = _set(ob, {10}, "LINEAR")
    k = fc.keyframe_points
    lin, rout = _slopes(k[1])
    assert abs(lin - _secant(0, 1)) < 1e-4, ("in tangent points at the previous key", lin)
    assert abs(rout - _secant(1, 2)) < 1e-4, ("out tangent points at the next key", rout)
    # the neighbours keep their Auto tangents (flat end keys), so neither segment is straight
    assert _chord_gap(fc, 1, 10) > 0.2, _chord_gap(fc, 1, 10)
    assert _chord_gap(fc, 10, 20) > 0.2, _chord_gap(fc, 10, 20)
    assert abs(_slopes(k[0])[1]) < 1e-6 and abs(_slopes(k[2])[0]) < 1e-6, "Auto end keys stay flat"


def test_two_linear_keys_make_their_segment_straight():
    ob, _fc0 = _curve()
    _set(ob, {10}, "LINEAR")
    fc = _set(ob, {20}, "LINEAR")
    assert _chord_gap(fc, 10, 20) < 1e-4, _chord_gap(fc, 10, 20)
    assert _chord_gap(fc, 1, 10) > 0.2, _chord_gap(fc, 1, 10)
    # moving a key keeps the linear sides pointing at the neighbours
    k = fc.keyframe_points
    k[2].co.y = 4.0
    k[2].handle_left.y += 2.0
    k[2].handle_right.y += 2.0
    fc.update()
    mt.apply(fc)
    assert _chord_gap(fc, 10, 20) < 1e-4, _chord_gap(fc, 10, 20)


def test_in_or_out_only():
    ob, _fc0 = _curve()
    fc = _set(ob, {10}, "LINEAR", "IN")
    lin, rout = _slopes(fc.keyframe_points[1])
    assert abs(lin - _secant(0, 1)) < 1e-4 and abs(rout) < 1e-6, (lin, rout)
    assert _chord_gap(fc, 1, 10) > 0.2
    ob, _fc0 = _curve()
    fc = _set(ob, {10}, "LINEAR", "OUT")
    lin, rout = _slopes(fc.keyframe_points[1])
    assert abs(lin) < 1e-6 and abs(rout - _secant(1, 2)) < 1e-4, (lin, rout)
    assert _chord_gap(fc, 10, 20) > 0.2


def test_a_stepped_key_stays_stepped_next_to_a_linear_key():
    ob, _fc0 = _curve()
    _set(ob, {1}, "STEPPED")
    fc = _set(ob, {10}, "LINEAR")
    assert fc.keyframe_points[0].interpolation == 'CONSTANT'
    ob, _fc0 = _curve()
    _set(ob, {1}, "STEPPED")
    fc = _set(ob, {10}, "LINEAR", "IN")
    assert fc.keyframe_points[0].interpolation == 'CONSTANT', "an in tangent leaves the previous key's out tangent"


def test_all_linear_is_a_polyline():
    ob, _fc0 = _curve()
    fc = _set(ob, {1, 10, 20}, "LINEAR")
    assert _chord_gap(fc, 1, 10) < 1e-4 and _chord_gap(fc, 10, 20) < 1e-4
