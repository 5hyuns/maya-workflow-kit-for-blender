"""Maya Edit > Duplicate (Ctrl+D) on picked joints: each picked joint is copied with the joints below it, in place
under the same parent (a root joint's copy is a new root), the top copy takes the next joint number, the copies keep
their joint attributes and display layers but no animation, and the copies of the picked joints are picked after —
in Pose Mode and in joint Edit Mode (the Move tool on an unskinned skeleton). A joint picked below another picked one
is copied once, with its parent's subtree."""

from importlib import import_module

import bpy
from mathutils import Vector

import kit

joints = import_module(kit.MODULE + ".operators.joints")
js = import_module(kit.MODULE + ".operators.joint_selection")
cb = import_module(kit.MODULE + ".ui.channel_box")
le = import_module(kit.MODULE + ".ui.layer_editor")
lj = import_module(kit.MODULE + ".ui.layer_joints")


def _object_mode():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')


def _chain():
    """joint1 (0, 0, 0) > joint2 (0, 0, 2) > joint3 (1, 0, 4); joint2 Radius 2, keyed; joint2 in layer1, joint3 in
    layer2. Object Mode, nothing selected."""
    _object_mode()
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for a in list(bpy.data.actions):
        bpy.data.actions.remove(a)
    scene = bpy.context.scene
    for coll in list(le.layers(scene)):
        bpy.data.collections.remove(coll)
    arm = joints.new_skeleton(bpy.context)
    made, parent = [], None
    for p in ((0, 0, 0), (0, 0, 2), (1, 0, 4)):
        parent = joints.add_joint(arm, Vector(p), parent, length=0.5)
        made.append(parent)
    joints.finish(bpy.context, arm, made)
    _object_mode()
    arm.data.bones[made[1]][joints.RADIUS] = 2.0
    pb = arm.pose.bones[made[1]]
    pb.rotation_mode = 'XYZ'
    for f, v in ((1, 0.0), (10, 0.7)):
        pb.rotation_euler.z = v
        pb.keyframe_insert("rotation_euler", index=2, frame=f)
    l1, l2 = le.new_layer(scene), le.new_layer(scene)
    lj.set_layer(arm.pose.bones[made[1]], l1)
    lj.set_layer(arm.pose.bones[made[2]], l2)
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    return arm, made, (l1, l2)


def _pose_pick(arm, *names):
    _object_mode()
    js.clear(bpy.context)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='POSE')
    for pb in arm.pose.bones:
        cb.set_bone_selected(pb, pb.name in names)
    arm.data.bones.active = arm.data.bones[names[-1]]


def _parents(arm):
    bones = arm.data.edit_bones if arm.mode == 'EDIT' else arm.data.bones
    return {b.name: (b.parent.name if b.parent else None) for b in bones}


def _head(arm, name):
    bones = arm.data.edit_bones if arm.mode == 'EDIT' else arm.data.bones
    b = bones[name]
    return b.head if arm.mode == 'EDIT' else b.head_local


def test_pose_mode_duplicate_copies_the_subtree_like_maya():
    arm, (j1, j2, j3), (l1, l2) = _chain()
    _pose_pick(arm, j2)
    assert bpy.ops.allset.duplicate() == {'FINISHED'}
    assert arm.mode == 'POSE'
    par = _parents(arm)
    assert par == {j1: None, j2: j1, j3: j2, "joint4": j1, "joint5": "joint4"}, par
    assert (_head(arm, "joint4") - _head(arm, j2)).length < 1e-6
    assert (_head(arm, "joint5") - _head(arm, j3)).length < 1e-6
    assert arm.data.bones["joint4"].get(joints.RADIUS) == 2.0, "joint attributes come along"
    assert lj.layer_of(arm.pose.bones["joint4"]) == l1 and lj.layer_of(arm.pose.bones["joint5"]) == l2
    fcurves = [fc.data_path for fc in kit.fcurves(arm)]
    assert fcurves and all('"joint2"' in p for p in fcurves), f"no animation is copied ({fcurves})"
    assert [pb.name for pb in arm.pose.bones if cb.bone_selected(pb)] == ["joint4"]
    assert arm.data.bones.active.name == "joint4"
    kids = joints._by_name(arm.data.bones[j1].children)
    assert [b.name for b in kids] == [j2, "joint4"], "the copy is the newest child"


def test_edit_mode_duplicate_keeps_the_picked_joint():
    """The Move tool picks a joint in Edit Mode with its subtree; Ctrl+D used to copy the children only."""
    arm, (j1, j2, j3), (l1, l2) = _chain()
    _object_mode()
    js.select_edit(bpy.context, arm, j2)
    assert arm.mode == 'EDIT'
    assert bpy.ops.allset.duplicate() == {'FINISHED'}
    assert arm.mode == 'EDIT'
    par = _parents(arm)
    assert par == {j1: None, j2: j1, j3: j2, "joint4": j1, "joint5": "joint4"}, par
    assert [eb.name for eb in js._edit_picked(arm)] == ["joint4"], "the copy is picked (with its subtree)"
    assert arm.data.edit_bones["joint5"].select
    bpy.ops.object.mode_set(mode='POSE')
    assert lj.layer_of(arm.pose.bones["joint4"]) == l1 and lj.layer_of(arm.pose.bones["joint5"]) == l2


def test_parent_and_child_picked_root_and_leaf():
    arm, (j1, j2, j3), _layers = _chain()
    _pose_pick(arm, j2, j3)
    assert bpy.ops.allset.duplicate() == {'FINISHED'}
    par = _parents(arm)
    assert par == {j1: None, j2: j1, j3: j2, "joint4": j1, "joint5": "joint4"}, f"copied once ({par})"
    assert sorted(pb.name for pb in arm.pose.bones if cb.bone_selected(pb)) == ["joint4", "joint5"]
    arm, (j1, j2, j3), _layers = _chain()
    _pose_pick(arm, j1)
    assert bpy.ops.allset.duplicate() == {'FINISHED'}
    par = _parents(arm)
    assert par["joint4"] is None and par["joint5"] == "joint4" and par["joint6"] == "joint5", par
    arm, (j1, j2, j3), _layers = _chain()
    _pose_pick(arm, j3)
    assert bpy.ops.allset.duplicate() == {'FINISHED'}
    assert _parents(arm)["joint4"] == j2 and len(arm.data.bones) == 4


def test_undo_takes_the_copies_back():
    arm, (j1, j2, j3), _layers = _chain()
    _pose_pick(arm, j2)
    bpy.ops.ed.undo_push(message="pick")
    bpy.ops.allset.duplicate()
    bpy.ops.ed.undo_push(message="Duplicate")
    name = arm.name
    assert len(bpy.data.objects[name].data.bones) == 5
    bpy.ops.ed.undo()
    assert len(bpy.data.objects[name].data.bones) == 3


def test_nothing_picked_warns():
    arm, (j1, j2, j3), _layers = _chain()
    _pose_pick(arm, j2)
    js.clear(bpy.context)
    assert bpy.ops.allset.duplicate() == {'CANCELLED'}
    assert len(arm.data.bones) == 3
