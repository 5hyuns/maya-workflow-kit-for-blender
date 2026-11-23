"""Issue #344: what the kit does on each played frame in Maya mode costs about the same with ten times more keys.

A skeleton whose every joint is keyed on its translate and rotate channels plays the same frames twice: with a key
every 10 frames and with a key on every frame. Per frame the kit's frame and depsgraph handlers run and the Channel
Box works out the state of each channel of the lead joint (keyed on this frame or not). Neither may grow with the
number of keys: the second run may cost at most twice the first (noise) and stays within a small budget."""

import time
from importlib import import_module

import bpy

import kit

JOINTS = 60
FRAMES = 200


def _m(name):
    return import_module(kit.MODULE + "." + name)


def _clear():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for act in list(bpy.data.actions):
        bpy.data.actions.remove(act)


def _scene(every):
    """A chain of JOINTS joints, every one keyed on location and rotation every ``every`` frames, all picked in Pose
    Mode (the lead is the last one)."""
    _clear()
    from mathutils import Vector
    joints = _m("operators.joints")
    arm = joints.new_skeleton(bpy.context)
    made = [joints.add_joint(arm, Vector((0, 0, 0)), None, length=0.2)]
    for i in range(1, JOINTS):
        made.append(joints.add_joint(arm, Vector((0, 0, 0.2 * i)), made[-1], length=0.2))
    joints.finish(bpy.context, arm, made)
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, FRAMES
    for pb in arm.pose.bones:
        pb.rotation_mode = 'XYZ'
        pb.keyframe_insert("location", frame=1)
        pb.keyframe_insert("rotation_euler", frame=1)
    frames = list(range(1, FRAMES + 1, every))
    for i, fc in enumerate(_m("compat").id_fcurves(arm)):
        fc.keyframe_points.clear()
        fc.keyframe_points.add(len(frames))
        co = []
        for f in frames:
            co += [f, 0.01 * ((f * 7 + i * 3) % 11)]
        fc.keyframe_points.foreach_set("co", co)
        fc.update()
    for ob in bpy.context.view_layer.objects:
        ob.select_set(False)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='POSE')
    cb = _m("ui.channel_box")
    for pb in arm.pose.bones:
        cb.set_bone_selected(pb, True)
    arm.data.bones.active = arm.data.bones[arm.pose.bones[-1].name]
    bpy.context.view_layer.update()
    return arm


def _kit(fn):
    return kit.MODULE.split(".")[-1] in (getattr(fn, "__module__", "") or "")


def _per_frame(arm):
    """ms per played frame of the kit's frame / depsgraph handlers and the lead's Channel Box channel states."""
    sc = bpy.context.scene
    values = _m("ui.cb_values")
    selection = _m("ui.cb_selection")
    lead = arm.pose.bones[-1]
    keys = selection._visible_channels(lead)
    assert len(keys) >= 6, f"the lead's channels ({keys})"
    spent = [0.0]
    lists = [bpy.app.handlers.frame_change_pre, bpy.app.handlers.frame_change_post,
             bpy.app.handlers.depsgraph_update_post]
    saved = [list(hs) for hs in lists]

    def timed(fn):
        def w(*a):
            t = time.perf_counter()
            try:
                return fn(*a)
            finally:
                spent[0] += time.perf_counter() - t
        return w
    for hs, real in zip(lists, saved):
        hs.clear()
        hs.extend(timed(f) if _kit(f) else f for f in real)
    try:
        sc.frame_set(1)
        best = None
        for _rep in range(3):
            spent[0] = 0.0
            for f in range(1, FRAMES + 1, 2):
                sc.frame_set(f)
                t = time.perf_counter()
                states = [values.channel_state(lead, k) for k in keys]
                spent[0] += time.perf_counter() - t
            assert 'KEYED' in states or 'ANIMATED' in states, states
            per = spent[0] / len(range(1, FRAMES + 1, 2)) * 1000
            best = per if best is None else min(best, per)
    finally:
        for hs, real in zip(lists, saved):
            hs.clear()
            hs.extend(real)
    sc.frame_set(1)
    return best


def test_kit_frame_cost_does_not_grow_with_keys():
    few = _per_frame(_scene(every=10))
    n_few = sum(len(fc.keyframe_points) for fc in _m("compat").id_fcurves(bpy.context.active_object))
    many = _per_frame(_scene(every=1))
    n_many = sum(len(fc.keyframe_points) for fc in _m("compat").id_fcurves(bpy.context.active_object))
    print(f"kit per-frame cost: {few:.3f} ms with {n_few} keys, {many:.3f} ms with {n_many} keys")
    assert n_many >= 9 * n_few, (n_few, n_many)
    assert many < max(2.0 * few, few + 0.05), f"{many:.3f} ms with {n_many} keys vs {few:.3f} ms with {n_few}"
    assert many < 1.5, f"kit per-frame cost {many:.3f} ms (budget 1.5)"
    _clear()
