"""Issue #344: dragging a rig control (move / rotate / scale in Pose or Object Mode) in Maya mode.

While a transform runs only poses and object transforms change, so the Maya joints keep each skeleton's joint list
and its controls' shapes like they do during playback: a depsgraph update during the drag only redraws the lines
(which follow the pose), and the first update after the drag reads everything again. The Time Slider keeps the F-curves
it found for a selected bone, and Draw Label joints keep their list, while playback or a drag runs."""

import math
from importlib import import_module
from types import SimpleNamespace

import bpy
import numpy as np
from mathutils import Vector

import kit

mj = import_module(kit.MODULE + ".ui.maya_joints")
joints = import_module(kit.MODULE + ".operators.joints")
cb = import_module(kit.MODULE + ".ui.channel_box")
ts = import_module(kit.MODULE + ".ui.time_slider")
time_keys = import_module(kit.MODULE + ".operators.time_keys")


def _clear():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)


def _circle(name, n=16, r=0.2):
    me = bpy.data.meshes.new(name)
    me.from_pydata([(r * math.cos(2 * math.pi * i / n), r * math.sin(2 * math.pi * i / n), 0.0) for i in range(n)],
                   [(i, (i + 1) % n) for i in range(n)], [])
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def _rig(count=20):
    """A chain of ``count`` joints, every other one a control with a circle shape, posed into Pose Mode."""
    _clear()
    arm = joints.new_skeleton(bpy.context)
    made = [joints.add_joint(arm, Vector((0, 0, 0)), None, length=0.3)]
    for i in range(1, count):
        made.append(joints.add_joint(arm, Vector((0.2 * math.sin(i), 0.1 * (i % 3), 0.25 * i)), made[-1],
                                     length=0.1))
    joints.finish(bpy.context, arm, made)
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    circle = _circle("ctrl")
    for i, pb in enumerate(arm.pose.bones):
        if i % 2:
            pb.custom_shape = circle
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    bpy.ops.object.mode_set(mode='POSE')
    return arm


def _view(objects):
    space = next(a.spaces.active for s in bpy.data.screens for a in s.areas if a.type == 'VIEW_3D')
    return SimpleNamespace(space_data=space, region_data=SimpleNamespace(is_perspective=True),
                           scene=bpy.context.scene, view_layer=bpy.context.view_layer, visible_objects=objects,
                           mode='POSE', screen=None)


def _reference(ob):
    """Every line of ``ob`` joint by joint (``skeleton`` + ``shape_lines`` + spheres / bones), as rows."""
    js = mj.skeleton(ob, bpy.context.scene)
    sel, lead = mj.selection(ob, js)
    col = mj.colours(js, sel, lead)
    dg = bpy.context.evaluated_depsgraph_get()
    pts, cols = [], []

    def add(segs, colour):
        pts.extend(tuple(v) for v in segs)
        cols.extend([(*colour, 1.0)] * len(segs))

    for n, j in js.items():
        if j.shape is not None:
            add(mj.shape_lines(j.shape[0], j.shape[1], dg), col[n])
            continue
        add(mj.sphere_lines(j.centre, j.frame, j.radius), col[n])
        for cn in j.children:
            if js[cn].shape is None:
                add(mj.bone_lines(j, js[cn]), col[n])
        if n in sel:
            for i in range(3):
                add([j.centre, j.centre + j.frame.col[i] * j.radius], mj.AXIS_COLORS[i])
    return _rows(pts, cols)


def _rows(pts, cols):
    if not len(pts):
        return np.zeros((0, 10))
    return np.concatenate((np.asarray(pts, np.float64).reshape(-1, 6),
                           np.asarray(cols, np.float64).reshape(-1, 2, 4)[:, 0]), axis=1)


def _gap(a, b):
    d = np.abs(a[:, None, :] - b[None, :, :]).max(axis=2)
    return float(max(d.min(axis=1).max(), d.min(axis=0).max()))


def test_dragging_a_pose_keeps_the_joint_list_and_the_control_shapes():
    """A drag in Pose Mode: every step's depsgraph update redraws the lines (they follow the pose and equal the
    per-joint lines) but reads neither the joint list nor the control shapes again; the update after the drag
    (no transform running) reads the joint list again (a pose doesn't change the shapes' own geometry)."""
    arm = _rig()
    pb = arm.pose.bones[3]
    cb.set_bone_selected(pb, True)
    arm.data.bones.active = pb.bone
    pb.rotation_mode = 'XYZ'
    view = _view([arm])
    reads, lists = [], []
    real_read, real_list, real_moving = mj._read_widget, mj._joint_list, mj.transforming
    mj._read_widget = lambda shape, dg: reads.append(shape.name) or real_read(shape, dg)
    mj._joint_list = lambda ob: lists.append(ob.name) or real_list(ob)
    mj.transforming = lambda: True                    # a move / rotate / scale runs
    try:
        mj.changed()
        mj._joined(view)                              # the drag's first redraw reads everything
        assert lists and reads, "the first redraw reads the joints and the shapes"
        edits = mj._EDITS[0]
        prev = None
        for step in range(1, 5):
            reads.clear()
            lists.clear()
            gen = mj._GEN[0]
            pb.rotation_euler = (0.2 * step, 0.0, 0.1 * step)     # connected joints turn, they don't move
            bpy.context.view_layer.update()           # the depsgraph update of this drag step
            assert mj._GEN[0] > gen, f"step {step}: the lines are redrawn"
            assert mj._EDITS[0] == edits, f"step {step}: no edit counted while dragging"
            got = mj._joined(view)
            assert not reads and not lists, f"step {step}: nothing read again ({lists}, {reads})"
            drawn = _rows(got[0], got[1])
            ref = _reference(arm)
            assert drawn.shape == ref.shape and _gap(drawn, ref) < 1e-4, f"step {step}: the per-joint lines"
            assert prev is None or _gap(drawn, prev) > 1e-3, f"step {step}: the lines follow the pose"
            prev = drawn
        mj.transforming = lambda: False               # the drag ends: its last update counts as an edit
        pb.rotation_euler = (0.0, 0.0, 0.0)
        bpy.context.view_layer.update()
        assert mj._EDITS[0] > edits, "the update after the drag counts as an edit"
        mj._joined(view)
        assert lists and not reads, "after the drag the joints are read again, the shapes stay"
    finally:
        mj._read_widget, mj._joint_list, mj.transforming = real_read, real_list, real_moving
        bpy.ops.object.mode_set(mode='OBJECT')


def test_edit_mode_transforms_still_count_as_edits():
    """Moving bones in Edit Mode changes the joints themselves: every update is an edit even while a transform runs."""
    arm = _rig(6)
    bpy.ops.object.mode_set(mode='EDIT')
    real = mj.transforming
    mj.transforming = lambda: True
    try:
        edits = mj._EDITS[0]
        arm.data.edit_bones[2].head.x += 0.1
        bpy.context.view_layer.update()
        assert mj._EDITS[0] > edits, "an Edit Mode move is an edit"
    finally:
        mj.transforming = real
        bpy.ops.object.mode_set(mode='OBJECT')


def test_time_slider_keeps_a_bones_curves_while_playing_or_dragging():
    """A selected bone's keys on the Time Slider: the same frames whether its curves are kept or found again; kept
    curves are found once, a new curve on the skeleton finds them again, and keys moved in the meantime show."""
    arm = _rig(6)
    pb = arm.pose.bones[2]
    other = arm.pose.bones[4]
    for f in (1, 8, 15):
        pb.location = (0.01 * f, 0, 0)
        pb.keyframe_insert("location", frame=f)
        other.keyframe_insert("rotation_quaternion", frame=f + 1)
    looks = []
    real = time_keys.node_fcurves
    time_keys.node_fcurves = lambda node: looks.append(node.name) or real(node)
    try:
        want = ts.key_frames([pb])
        assert [f for f, _b in want] == [1, 8, 15]
        looks.clear()
        for _i in range(3):
            assert ts.key_frames([pb], keep=True) == want
        assert len(looks) == 1, f"kept: the bone's curves are found once ({len(looks)})"
        fc = next(c for c in time_keys.node_fcurves(pb) if c.array_index == 0)
        fc.keyframe_points[1].co.x = 9.0
        bpy.context.view_layer.update()         # as before every redraw: the moved key updates its Action
        looks.clear()
        assert [f for f, _b in ts.key_frames([pb], keep=True)] == [1, 8, 9, 15], "a moved key shows at once"
        assert not looks, "the curves are still the kept ones"
        pb.keyframe_insert("rotation_quaternion", frame=4)            # new curves on the skeleton
        assert [f for f, _b in ts.key_frames([pb], keep=True)] == [1, 4, 8, 9, 15], "new curves are found"
        assert ts.key_frames([pb]) == ts.key_frames([pb], keep=True)
    finally:
        time_keys.node_fcurves = real
        bpy.ops.object.mode_set(mode='OBJECT')


def test_time_slider_holds_the_keys_while_a_move_runs():
    """While a move runs in Pose Mode (no playback) the Time Slider finds the selected bones' keys once; keys moved
    meanwhile (an animation editor's drag updates their Action) are found again; during playback, or with no move
    running, the keys are found on every redraw."""
    arm = _rig(6)
    bones = [arm.pose.bones[i] for i in (1, 2, 3)]
    for f in (1, 8, 15):
        for pb in bones:
            pb.location = (0.01 * f, 0, 0)
            pb.keyframe_insert("location", frame=f)
    bpy.context.view_layer.update()
    calls = []
    real_frames, real_nodes, real_moving = ts.key_frames, ts.tick_nodes, mj.transforming
    ts.key_frames = lambda nodes, keep=False: calls.append(keep) or real_frames(nodes, keep)
    ts.tick_nodes = lambda _context: bones
    screen = SimpleNamespace(is_animation_playing=False)
    ctx = SimpleNamespace(screen=screen, mode='POSE')
    region = SimpleNamespace(as_pointer=lambda: 7)
    try:
        mj.transforming = lambda: True
        want = ts._shown_keys(ctx, region)
        assert [f for f, _b in want] == [1, 8, 15]
        for _i in range(3):
            assert ts._shown_keys(ctx, region) == want
        assert calls == [True], f"held while the move runs ({calls})"
        fc = time_keys.node_fcurves(bones[0])[0]
        fc.keyframe_points[1].co.x = 9.0
        fc.update()
        arm.animation_data.action.update_tag()
        bpy.context.view_layer.update()
        assert [f for f, _b in ts._shown_keys(ctx, region)] == [1, 8, 9, 15], "a moved key shows"
        assert len(calls) == 2
        screen.is_animation_playing = True
        ts._shown_keys(ctx, region)
        ts._shown_keys(ctx, region)
        assert len(calls) == 4, "during playback the keys are read every time"
        screen.is_animation_playing = False
        mj.transforming = lambda: False
        ts._shown_keys(ctx, region)
        ts._shown_keys(ctx, region)
        assert len(calls) == 6 and calls[-1] is False and not ts._HELD, "no move: read every time, nothing held"
    finally:
        ts.key_frames, ts.tick_nodes, mj.transforming = real_frames, real_nodes, real_moving
        ts._HELD.clear()
        bpy.ops.object.mode_set(mode='OBJECT')


def test_channel_box_holds_the_rows_key_states_while_a_move_runs():
    """While a move runs in Pose Mode (no playback) the Channel Box finds each row's key state once; a key moved
    meanwhile (its Action updated) is found again; with no move running, or during playback, every redraw finds it.
    The "+N" beside the lead's name counts the targets without listing them."""
    arm = _rig(6)
    pb = arm.pose.bones[1]
    for f in (1, 8):
        pb.location = (0.01 * f, 0, 0)
        pb.keyframe_insert("location", frame=f)
    bpy.context.scene.frame_set(8)
    bpy.context.view_layer.update()
    calls = []
    real_state, real_moving = cb.channel_state, mj.transforming
    cb.channel_state = lambda ob, key, frame=None: calls.append(key) or real_state(ob, key, frame)
    screen = SimpleNamespace(is_animation_playing=False)
    ctx = SimpleNamespace(screen=screen, mode='POSE')
    try:
        assert not cb._holds_states(ctx), "no move running"
        cb.row_state(pb, "tx")
        cb.row_state(pb, "tx")
        assert len(calls) == 2, "no move: found on every redraw"
        mj.transforming = lambda: True
        cb._holding[0] = cb._holds_states(ctx)               # what the Channel Box draw does
        assert cb._holding[0]
        calls.clear()
        for _i in range(4):
            assert cb.row_state(pb, "tx") == 'KEYED'
            assert cb.row_state(pb, "ty") == 'KEYED'
        assert calls == ["tx", "ty"], f"held while the move runs ({calls})"
        fc = time_keys.node_fcurves(pb)[0]
        fc.keyframe_points[1].co.x = 9.0
        fc.update()
        arm.animation_data.action.update_tag()
        bpy.context.view_layer.update()
        assert cb.row_state(pb, "tx") == 'ANIMATED', "a key moved off the frame shows"
        assert calls[-1] == "tx" and len(calls) == 3
        screen.is_animation_playing = True
        assert not cb._holds_states(ctx), "during playback a move can key: found every time"
    finally:
        cb.channel_state, mj.transforming = real_state, real_moving
        cb._held_states.clear()
        cb._holding[0] = False
    # the "+N" count
    for i, b in enumerate(arm.pose.bones):
        cb.set_bone_selected(b, i in (1, 2, 4))
    arm.pose.bones[4].hide = True                            # a hidden bone isn't a target
    arm.data.bones.active = arm.data.bones[arm.pose.bones[2].name]
    bpy.context.view_layer.update()
    assert cb.target_count(bpy.context) == len(cb.targets(bpy.context)) == 2
    bpy.ops.object.mode_set(mode='OBJECT')
    other = _circle("other")
    other.select_set(True)
    arm.select_set(False)                                     # the active object, not selected: still a target
    assert cb.target_count(bpy.context) == len(cb.targets(bpy.context)) == 2
    arm.select_set(True)
    assert cb.target_count(bpy.context) == len(cb.targets(bpy.context)) == 2
    bpy.context.view_layer.objects.active = None
    assert cb.target_count(bpy.context) == len(cb.targets(bpy.context)) == 2


def test_draw_label_joints_are_found_once_while_dragging():
    labels = import_module(kit.MODULE + ".operators.joint_labels")
    arm = _rig(6)
    labels.set_label(arm.data.bones[3], side=labels.LEFT, type=labels.T_KNEE, draw=True)
    real = mj.transforming
    mj.transforming = lambda: True
    labels._labelled.clear()
    try:
        ctx = SimpleNamespace(screen=None, view_layer=bpy.context.view_layer)
        pts = labels.label_points(ctx)
        assert len(pts) == 1
        kept = labels._labelled[arm.as_pointer()][1]
        arm.pose.bones[1].rotation_mode = 'XYZ'
        arm.pose.bones[1].rotation_euler = (0.6, 0.0, 0.0)   # the joint above turns
        bpy.context.view_layer.update()
        again = labels.label_points(ctx)
        assert labels._labelled[arm.as_pointer()][1] is kept, "dragging: the labelled joints are found once"
        assert (again[0][0] - pts[0][0]).length > 1e-4, "the label follows its joint"
    finally:
        mj.transforming = real
        labels._labelled.clear()
        bpy.ops.object.mode_set(mode='OBJECT')
