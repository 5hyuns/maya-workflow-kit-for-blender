"""Step 198 (#105): Graph Editor Retime Tool — time map against Maya 2022
and its application to real F-curves."""

from importlib import import_module

import bpy

import kit

rt = import_module(kit.MODULE + ".operators.graph_retime")

KEYS = [1, 5, 10, 15, 20, 30]
VALUES = [0, 2, 5, 3, 8, 1]


def _close(got, want, tol=1e-6):
    assert len(got) == len(want) and all(abs(g - w) <= tol for g, w in zip(got, want)), (got, want)


def _retime(markers, index, new_time, snap=False):
    b = rt.clamp_target(markers, index, new_time, snap)
    return rt.retime_times(KEYS, markers, index, b)


def test_measured_cases():
    _close(_retime([5, 15], 1, 20), [1, 5, 12.5, 20, 25, 35])
    _close(_retime([5, 15], 1, 12), [1, 5, 8.5, 12, 17, 27])
    _close(_retime([5, 15], 0, 3), [-1, 3, 9, 15, 20, 30])
    _close(_retime([5, 15, 25], 1, 18), [1, 5, 11.5, 18, 21.5, 30])
    _close(_retime([10], 0, 14), [5, 9, 14, 19, 24, 34])


def test_snap_on_frame():
    # Maya: Snap On Frame, drag 15 -> 17.47 lands on 17
    _close(_retime([5, 15], 1, 17.47, snap=True), [1, 5, 11, 17, 22, 32])
    # off: continuous
    _close(_retime([5, 15], 1, 17.5), [1, 5, 11.25, 17.5, 22.5, 32.5])


def test_lone_marker_shifts_everything():
    _close(_retime([3], 0, -2), [t - 5 for t in KEYS])
    _close(_retime([100], 0, 104), [t + 4 for t in KEYS])


def test_first_and_last_ripple():
    # first marker of three: keys before ripple, after the second marker stay
    _close(_retime([5, 15, 25], 0, 7), [3, 7, 11, 15, 20, 30])
    # last marker of three: keys after ripple, before the second marker stay
    _close(_retime([5, 15, 25], 2, 27), [1, 5, 10, 15, 21, 32])


def test_inner_marker_keeps_outside_keys():
    got = _retime([5, 15, 25], 1, 10)
    assert got[0] == 1 and got[1] == 5 and got[5] == 30, got


def test_clamping():
    m = [5, 15, 25]
    assert rt.clamp_target(m, 1, 40) == 25 - rt.MIN_GAP
    assert rt.clamp_target(m, 1, -3) == 5 + rt.MIN_GAP
    assert rt.clamp_target(m, 1, 40, snap=True) == 24.0
    assert rt.clamp_target(m, 0, -100) == -100       # first marker: free to the left
    assert rt.clamp_target(m, 2, 1000) == 1000       # last marker: free to the right
    # the map stays monotonic at the clamp
    got = rt.retime_times(KEYS, m, 1, rt.clamp_target(m, 1, 40))
    assert all(a < b for a, b in zip(got, got[1:])), got


def test_pure_function_needs_no_blender_data():
    f = rt.retime_map((0.0, 10.0), 1, 20.0)
    assert f(5.0) == 10.0 and f(10.0) == 20.0 and f(12.0) == 22.0 and f(-1.0) == -1.0


def _cube_curve():
    bpy.ops.wm.read_homefile(use_empty=True)
    me = bpy.data.meshes.new("pCubeShape1")
    ob = bpy.data.objects.new("pCube1", me)
    bpy.context.scene.collection.objects.link(ob)
    for t, v in zip(KEYS, VALUES):
        ob.location.x = v
        ob.keyframe_insert("location", index=0, frame=t)
    return ob, next(fc for fc in kit.fcurves(ob) if fc.data_path == "location" and fc.array_index == 0)


def test_fcurve_retime_measured():
    ob, fc = _cube_curve()
    b = rt.retime_curves([fc], [5, 15], 1, 20)
    assert b == 20
    _close([kp.co.x for kp in fc.keyframe_points], [1, 5, 12.5, 20, 25, 35])
    _close([kp.co.y for kp in fc.keyframe_points], VALUES)
    for t, v in [(12.5, 5), (20, 3), (35, 1)]:
        assert abs(fc.evaluate(t) - v) < 1e-5, (t, fc.evaluate(t))


def test_handles_follow():
    ob, fc = _cube_curve()
    for kp in fc.keyframe_points:
        kp.handle_left_type = kp.handle_right_type = 'FREE'
    before = [(kp.handle_left.x, kp.co.x, kp.handle_right.x, kp.handle_left.y, kp.handle_right.y)
              for kp in fc.keyframe_points]
    f = rt.retime_map([5, 15], 1, 20)
    rt.apply(rt.snapshot([fc]), f)
    for kp, (hl, co, hr, hly, hry) in zip(fc.keyframe_points, before):
        assert abs(kp.handle_left.x - f(hl)) < 1e-5 and abs(kp.handle_right.x - f(hr)) < 1e-5, (kp.co.x,)
        assert kp.handle_left.x < kp.co.x < kp.handle_right.x
        assert abs(kp.handle_left.y - hly) < 1e-6 and abs(kp.handle_right.y - hry) < 1e-6
    # restore = the snapshot times back
    snap = [(fc, [(hl, co, hr) for hl, co, hr, _a, _b in before])]
    rt.restore(snap)
    _close([kp.co.x for kp in fc.keyframe_points], KEYS)


def test_operator_registered():
    assert hasattr(bpy.types, "ALLSET_OT_retime_tool")
    assert bpy.types.ALLSET_OT_retime_tool.bl_options == {'UNDO'}
    assert not bpy.ops.allset.retime_tool.poll()          # no Graph Editor in background


def test_hit_parts():
    xs, h, s = [100.0, 200.0], 400, 1.0
    assert rt.hit([5, 15], xs, 102, 200, h, s) == (0, 'HANDLE')
    assert rt.hit([5, 15], xs, 198, 340, h, s) == (1, 'LINE')
    assert rt.hit([5, 15], xs, 200, 12, h, s) == (1, 'DELETE')
    assert rt.hit([5, 15], xs, 150, 200, h, s) == (None, None)
