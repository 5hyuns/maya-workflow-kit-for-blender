"""Step 257 (Issue #151): new keys get Maya 2026's Auto tangents (research/maya/re/060_modeling_anim.md B3).

Maya truth = tests/maya257_tangent_data.py (mayapy setKeyframe with factory auto / auto tangents, whole-frame samples)."""

from importlib import import_module

import bpy

import kit
from maya257_tangent_data import CURVES, IK_BOUNCE

cb = import_module(kit.MODULE + ".ui.channel_box")
mt = import_module(kit.MODULE + ".operators.maya_tangents")
time_keys = import_module(kit.MODULE + ".operators.time_keys")
compat = import_module(kit.MODULE + ".compat")


def _fresh(name):
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    ob = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def _key(ob, frames, values):
    sc = bpy.context.scene
    for f, v in zip(frames, values):
        sc.frame_set(f)
        ob.location.z = v
        assert cb.keyframe(ob, "tz")
    return next(fc for fc in compat.id_fcurves(ob) if fc.data_path == "location" and fc.array_index == 2)


def test_auto_slopes_match_maya_rule():
    # spec B3 measured checks (slope per frame)
    assert abs(mt.slopes([1, 13, 25], [0, 1, 1.01])[1] - 0.0025) < 1e-9
    assert abs(mt.slopes([1, 13, 25], [0, 1, 1.15])[1] - 0.0375) < 1e-9
    assert abs(mt.slopes([1, 13, 25], [0, 1, 1.2])[1] - 0.05) < 1e-9
    s = mt.slopes([1, 4, 10, 18, 25], [0, 1, 3, 3.5, 6])
    for a, b in zip(s, [0, 1 / 3, 0.178571, 0.1875, 0]):
        assert abs(a - b) < 1e-6, s
    assert abs(mt.slopes([1, 13, 25], [2, 1, -3])[1] + 0.208333) < 1e-6
    assert mt.slopes([1, 13, 25], [0, 1.5, 0]) == [0.0, 0.0, 0.0]          # extreme = flat
    assert mt.slopes([1], [3]) == [0.0]


def test_kit_keys_follow_maya_auto_curves():
    worst = {}
    for name, c in CURVES.items():
        ob = _fresh(name)
        fc = _key(ob, c["frames"], c["values"])
        for kp in fc.keyframe_points:
            assert mt.is_auto(kp) and kp.interpolation == 'BEZIER'
        worst[name] = max(abs(fc.evaluate(float(t)) - v) for t, v in c["samples"].items())
    bad = {k: v for k, v in worst.items() if v > 2e-5}
    assert not bad, bad


def test_ik_bounce_like_maya():
    ob = _fresh("ikHandle1")
    fc = _key(ob, [1, 12, 24], [0.0, 1.5, 0.0])
    err = max(abs(fc.evaluate(float(t)) - v) for t, v in IK_BOUNCE.items())
    assert err < 2e-5, err


def test_key_order_does_not_matter_and_neighbours_update():
    # Maya recomputes auto tangents when a neighbour key changes (spec B3: editing the last key 3 -> 1 made the
    # middle key flat)
    ob = _fresh("order")
    c = CURVES["c_five"]
    order = [2, 0, 4, 1, 3]
    fc = _key(ob, [c["frames"][i] for i in order], [c["values"][i] for i in order])
    err = max(abs(fc.evaluate(float(t)) - v) for t, v in c["samples"].items())
    assert err < 2e-5, err
    ob2 = _fresh("edit")
    fc = _key(ob2, [1, 13, 25], [0, 1, 3])
    assert fc.keyframe_points[1].handle_right.y > 1.0
    fc = _key(ob2, [25], [1])
    mid = fc.keyframe_points[1]
    assert abs(mid.handle_left.y - 1) < 1e-6 and abs(mid.handle_right.y - 1) < 1e-6


def test_delete_key_recomputes_and_other_tangents_kept():
    ob = _fresh("del")
    fc = _key(ob, [1, 13, 25, 37], [0, 1, 1.15, 2])
    # a Linear key is left alone
    time_keys.apply_tangent(fc.keyframe_points[2], "LINEAR")
    fc.update()
    mt.apply(fc)
    assert fc.keyframe_points[2].interpolation == 'LINEAR'
    sc = bpy.context.scene
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    n = time_keys.delete_keys(bpy.context, 37, 37)
    assert n == 1, n
    last = fc.keyframe_points[-1]
    assert abs(last.co.x - 25) < 1e-6
    first = fc.keyframe_points[0]
    assert abs(first.handle_right.y) < 1e-9                      # first key flat


def test_auto_tangent_button_writes_maya_shape():
    ob = _fresh("button")
    fc = _key(ob, [1, 2, 25], [0, 1, 3])
    for kp in fc.keyframe_points:
        time_keys.apply_tangent(kp, "LINEAR")
    fc.update()
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    time_keys.set_tangent(bpy.context, 1, 25, "AUTO")
    c = CURVES["c_uneven_short"]
    err = max(abs(fc.evaluate(float(t)) - v) for t, v in c["samples"].items())
    assert err < 2e-5, err
