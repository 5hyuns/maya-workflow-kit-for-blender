"""Maya Edit > Duplicate (Ctrl+D) on picked joints: each picked joint is copied with the joints below it, in place
under the same parent (a root joint's copy is a new root), the top copy takes the next joint number, the copies keep
their joint attributes and display layers but no animation, and the copies of the picked joints are picked after —
in Pose Mode and in joint Edit Mode (the Move tool on an unskinned skeleton). A joint picked below another picked one
is copied once, with its parent's subtree.

Duplicate with Transform (Shift+D) adds the change between the last copy and its joint once more to each new copy;
Duplicate Special (Ctrl+Shift+D) makes several copies, each moved / turned in world space and scaled along its own
axes once more than the one before, under the parent or as new top joints; Smart Duplicate (Shift+press on the
manipulator) copies them for the drag and takes the copies back when nothing moved."""

from importlib import import_module

import bpy
from math import radians

from mathutils import Matrix, Vector

import kit

joints = import_module(kit.MODULE + ".operators.joints")
js = import_module(kit.MODULE + ".operators.joint_selection")
cb = import_module(kit.MODULE + ".ui.channel_box")
le = import_module(kit.MODULE + ".ui.layer_editor")
lj = import_module(kit.MODULE + ".ui.layer_joints")
jd = import_module(kit.MODULE + ".operators.joint_duplicate")
manip = import_module(kit.MODULE + ".operators.manip")


def _object_mode():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')


def _chain(keyed=True):
    """joint1 (0, 0, 0) > joint2 (0, 0, 2) > joint3 (1, 0, 4); joint2 Radius 2, keyed (``keyed``: else the skeleton is
    unanimated, so the Move tool edits its joints in Edit Mode); joint2 in layer1, joint3 in layer2. Object Mode,
    nothing selected."""
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
    for f, v in ((1, 0.0), (10, 0.7)) if keyed else ():
        pb.rotation_euler.z = v
        pb.keyframe_insert("rotation_euler", index=2, frame=f)
    scene.frame_set(1)                       # the channels hold the keyed values of the current frame
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


def test_a_posed_joint_is_copied_where_it_stands():
    """Maya: the copy takes the joint's current values (here a key's), not its rest; the keys stay with the source."""
    arm, (j1, j2, j3), _layers = _chain()
    bpy.context.scene.frame_set(10)                    # joint2 keyed at 0.7 rad
    _pose_pick(arm, j2)
    assert bpy.ops.allset.duplicate() == {'FINISHED'}
    bpy.context.view_layer.update()
    pbs = arm.pose.bones
    for src, copy in ((j2, "joint4"), (j3, "joint5")):
        a = arm.matrix_world @ pbs[src].matrix
        b = arm.matrix_world @ pbs[copy].matrix
        assert max(abs(a[i][k] - b[i][k]) for i in range(4) for k in range(4)) < 1e-5, (src, copy)
    assert abs(pbs["joint4"].rotation_euler.z - 0.7) < 1e-5
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()
    assert abs(pbs["joint4"].rotation_euler.z - 0.7) < 1e-5 and abs(pbs[j2].rotation_euler.z) < 1e-5, \
        "no keys on the copy"


# --- Duplicate with Transform / Duplicate Special / Smart Duplicate ------------------------------------------------

def _world(arm, name):
    return arm.matrix_world @ arm.pose.bones[name].matrix


def _close(a, b, eps=1e-4):
    return max(abs(a[i][k] - b[i][k]) for i in range(4) for k in range(4)) < eps


def _picked_pose(arm):
    return [pb.name for pb in arm.pose.bones if cb.bone_selected(pb)]


def _turn(arm, name, move, angle):
    """Move joint ``name`` by ``move`` and turn it by ``angle`` about the world Y axis through it (Pose Mode)."""
    bpy.context.view_layer.update()
    w = _world(arm, name)
    h = w.translation.copy()
    m = Matrix.Translation(Vector(move) + h) @ Matrix.Rotation(angle, 4, 'Y') @ Matrix.Translation(-h) @ w
    arm.pose.bones[name].matrix = arm.matrix_world.inverted() @ m
    bpy.context.view_layer.update()


def test_shift_d_repeats_the_change_in_pose_mode():
    arm, (j1, j2, j3), (l1, l2) = _chain()
    jd.PAIRS.clear()
    _pose_pick(arm, j2)
    assert bpy.ops.allset.duplicate_with_transform() == {'FINISHED'}
    bpy.context.view_layer.update()
    assert _picked_pose(arm) == ["joint4"] and _close(_world(arm, "joint4"), _world(arm, j2)), \
        "the first time: a copy in place"
    _turn(arm, "joint4", (0, 0, 0), radians(20))
    delta = _world(arm, "joint4") @ _world(arm, j2).inverted()
    assert bpy.ops.allset.duplicate_with_transform() == {'FINISHED'}
    bpy.context.view_layer.update()
    assert _picked_pose(arm) == ["joint6"], _picked_pose(arm)
    assert _close(_world(arm, "joint6"), delta @ _world(arm, "joint4")), "the same change once more"
    assert bpy.ops.allset.duplicate_with_transform() == {'FINISHED'}
    bpy.context.view_layer.update()
    assert _close(_world(arm, "joint8"), delta @ _world(arm, "joint6")), "and again"
    par = _parents(arm)
    assert [par[n] for n in ("joint4", "joint6", "joint8")] == [j1, j1, j1], par
    assert [par[n] for n in ("joint5", "joint7", "joint9")] == ["joint4", "joint6", "joint8"], par
    for top, child in (("joint6", "joint7"), ("joint8", "joint9")):
        assert lj.layer_of(arm.pose.bones[top]) == l1 and lj.layer_of(arm.pose.bones[child]) == l2, top
    assert arm.mode == 'POSE'


def test_shift_d_moves_a_root_copy_in_pose_mode():
    arm, (j1, j2, j3), _layers = _chain()
    jd.PAIRS.clear()
    _pose_pick(arm, j1)
    bpy.ops.allset.duplicate_with_transform()
    assert _parents(arm)["joint4"] is None
    _turn(arm, "joint4", (1.0, 0.0, 0.5), radians(10))
    delta = _world(arm, "joint4") @ _world(arm, j1).inverted()
    bpy.ops.allset.duplicate_with_transform()
    bpy.context.view_layer.update()
    assert _parents(arm)["joint7"] is None and _picked_pose(arm) == ["joint7"]
    assert _close(_world(arm, "joint7"), delta @ _world(arm, "joint4"))
    assert _close(_world(arm, "joint9"), delta @ _world(arm, "joint6")), "the joints below come along"


def test_shift_d_repeats_a_joint_move_in_edit_mode():
    """Unanimated skeleton: the Move tool moves joints in Edit Mode, so the repeated move goes to the joints."""
    arm, (j1, j2, j3), (l1, l2) = _chain(keyed=False)
    jd.PAIRS.clear()
    js.select_edit(bpy.context, arm, j2)
    assert bpy.ops.allset.duplicate_with_transform() == {'FINISHED'}
    assert arm.mode == 'EDIT' and [eb.name for eb in js._edit_picked(arm)] == ["joint4"]
    ebs = arm.data.edit_bones
    ebs["joint4"].use_connect = False
    move = Vector((1.0, 0.0, 0.0))
    ebs["joint4"].head += move
    ebs["joint4"].tail += move                  # joint5's head (connected) goes along
    ebs["joint5"].tail += move
    assert bpy.ops.allset.duplicate_with_transform() == {'FINISHED'}
    assert arm.mode == 'EDIT' and [eb.name for eb in js._edit_picked(arm)] == ["joint6"]
    ebs = arm.data.edit_bones
    assert (ebs["joint6"].head - ebs["joint4"].head - Vector((1, 0, 0))).length < 1e-5
    assert (ebs["joint7"].head - ebs["joint5"].head - Vector((1, 0, 0))).length < 1e-5
    assert ebs["joint6"].parent.name == j1 and not ebs["joint6"].use_connect
    bpy.ops.object.mode_set(mode='POSE')
    assert lj.layer_of(arm.pose.bones["joint6"]) == l1
    assert _close(arm.pose.bones["joint6"].matrix_basis, Matrix.Identity(4)), "the joint moved, not its channels"


def test_shift_d_without_a_pair_and_undo():
    arm, (j1, j2, j3), _layers = _chain()
    jd.PAIRS.clear()
    _pose_pick(arm, j3)
    bpy.ops.ed.undo_push(message="pick")
    bpy.ops.allset.duplicate_with_transform()
    bpy.ops.ed.undo_push(message="Duplicate with Transform")
    name = arm.name
    assert _parents(arm)["joint4"] == j2
    bpy.context.view_layer.update()
    assert _close(_world(arm, "joint4"), _world(arm, j3)), "no earlier copy: in place"
    bpy.ops.allset.duplicate_with_transform()
    bpy.ops.ed.undo_push(message="Duplicate with Transform")
    assert len(bpy.data.objects[name].data.bones) == 5
    bpy.ops.ed.undo()
    assert len(bpy.data.objects[name].data.bones) == 4, "one undo step each"


def _maya_axis(arm, name, axis):
    """World direction of joint ``name``'s Maya orient axis (Maya X / Y / Z = bone Y / Z / X; the parent unposed)."""
    bone_axis = {"X": Vector((0, 1, 0)), "Y": Vector((0, 0, 1)), "Z": Vector((1, 0, 0))}[axis]
    return (arm.matrix_world.to_3x3() @ arm.data.bones[name].matrix_local.to_3x3() @ bone_axis).normalized()


def test_duplicate_special_copies_offsets_and_picks_them():
    """Translate X 1 (world) and Rotate Z 10 (about the joint's orient Z), 3 copies: each one adds the change again."""
    arm, (j1, j2, j3), (l1, l2) = _chain()
    jd.PAIRS["x"] = "y"
    _pose_pick(arm, j2)
    bpy.context.view_layer.update()
    src = _world(arm, j2)
    # the operator takes Maya Rotate X / Y / Z as X / -Z / Y
    assert bpy.ops.allset.duplicate_special(copies=3, translate=(1.0, 0.0, 0.0),
                                            rotate=(0.0, radians(-10), 0.0)) == {'FINISHED'}
    bpy.context.view_layer.update()
    h = src.translation
    turn = Matrix.Rotation(radians(10), 4, _maya_axis(arm, j2, "Z"))
    d = Matrix.Translation(Vector((1, 0, 0)) + h) @ turn @ Matrix.Translation(-h)
    dk = Matrix.Identity(4)
    for top in ("joint4", "joint6", "joint8"):
        dk = d @ dk
        assert _close(_world(arm, top), dk @ src), top
    assert _picked_pose(arm) == ["joint4", "joint6", "joint8"], _picked_pose(arm)
    par = _parents(arm)
    assert [par[n] for n in ("joint4", "joint6", "joint8")] == [j1, j1, j1], par
    assert all(lj.layer_of(arm.pose.bones[n]) == l1 for n in ("joint4", "joint6", "joint8"))
    assert all(lj.layer_of(arm.pose.bones[n]) == l2 for n in ("joint5", "joint7", "joint9"))
    assert not arm.data.bones["joint4"].use_connect, "a moved copy leaves its parent's tip"
    assert not jd.PAIRS, "several copies: Duplicate with Transform has nothing to repeat"


def test_duplicate_special_rotate_x_turns_about_the_joint():
    """Rotate X turns the copy about the joint's own X (down the joint): the joint below stays where it is."""
    arm, (j1, j2, j3), _layers = _chain()
    _pose_pick(arm, j2)
    bpy.context.view_layer.update()
    w2, w3 = _world(arm, j2), _world(arm, j3)
    assert bpy.ops.allset.duplicate_special(rotate=(radians(30), 0.0, 0.0)) == {'FINISHED'}
    bpy.context.view_layer.update()
    h = w2.translation
    turn = Matrix.Translation(h) @ Matrix.Rotation(radians(30), 4, _maya_axis(arm, j2, "X")) @ Matrix.Translation(-h)
    assert _close(_world(arm, "joint4"), turn @ w2)
    assert (_world(arm, "joint5").translation - w3.translation).length < 1e-4


def test_duplicate_special_scales_along_the_joint():
    arm, (j1, j2, j3), _layers = _chain()
    _pose_pick(arm, j2)
    bpy.context.view_layer.update()
    h, child = _world(arm, j2).translation.copy(), _world(arm, j3).translation.copy()
    # Maya Scale X = down the joint (the window passes Maya X / Z / Y as X / Y / Z)
    assert bpy.ops.allset.duplicate_special(scale=(2.0, 1.0, 1.0)) == {'FINISHED'}
    bpy.context.view_layer.update()
    assert (Vector(arm.pose.bones["joint4"].scale) - Vector((1, 2, 1))).length < 1e-5
    assert (_world(arm, "joint5").translation - (h + 2 * (child - h))).length < 1e-4


def test_duplicate_special_world_makes_top_joints_where_they_stand():
    arm, (j1, j2, j3), (l1, _l2) = _chain()
    bpy.context.scene.frame_set(10)                    # joint2 keyed at 0.7 rad
    _pose_pick(arm, j2)
    bpy.context.view_layer.update()
    w2, w3 = _world(arm, j2), _world(arm, j3)
    assert bpy.ops.allset.duplicate_special(group_under='WORLD') == {'FINISHED'}
    bpy.context.view_layer.update()
    par = _parents(arm)
    assert par["joint4"] is None and par["joint5"] == "joint4", par
    assert _close(_world(arm, "joint4"), w2) and _close(_world(arm, "joint5"), w3)
    assert lj.layer_of(arm.pose.bones["joint4"]) == l1 and _picked_pose(arm) == ["joint4"]


def test_duplicate_special_in_edit_mode_moves_the_joints():
    arm, (j1, j2, j3), _layers = _chain(keyed=False)
    js.select_edit(bpy.context, arm, j2)
    ebs = arm.data.edit_bones
    h2, h3 = ebs[j2].head.copy(), ebs[j3].head.copy()
    assert bpy.ops.allset.duplicate_special(copies=2, translate=(1.0, 0.0, 0.0)) == {'FINISHED'}
    assert arm.mode == 'EDIT'
    ebs = arm.data.edit_bones
    assert (ebs["joint4"].head - h2 - Vector((1, 0, 0))).length < 1e-5
    assert (ebs["joint5"].head - h3 - Vector((1, 0, 0))).length < 1e-5
    assert (ebs["joint6"].head - h2 - Vector((2, 0, 0))).length < 1e-5
    assert sorted(eb.name for eb in js._edit_picked(arm)) == ["joint4", "joint6"]
    bpy.ops.object.mode_set(mode='POSE')
    assert all(_close(arm.pose.bones[n].matrix_basis, Matrix.Identity(4)) for n in ("joint4", "joint6"))


def test_duplicate_special_instance_and_new_group_copy_under_the_parent():
    for opts in ({"geometry_type": 'INSTANCE'}, {"group_under": 'NEW_GROUP'}):
        arm, (j1, j2, j3), _layers = _chain()
        n = len(bpy.data.objects)
        _pose_pick(arm, j2)
        assert bpy.ops.allset.duplicate_special(**opts) == {'FINISHED'}, opts
        par = _parents(arm)
        assert par["joint4"] == j1 and par["joint5"] == "joint4", (opts, par)
        assert len(bpy.data.objects) == n, "no group object"


def test_pose_and_armature_keys():
    kc = kit.maya_kc()
    for km in ("Pose", "Armature"):
        items = {(k.shift, k.ctrl, k.alt): k.idname for k in kc.keymaps[km].keymap_items
                 if k.active and k.type == 'D' and k.value == 'PRESS'}
        assert items.get((True, False, False)) == "allset.duplicate_with_transform", (km, items)
        assert items.get((True, True, False)) == "allset.duplicate_special", (km, items)
        assert items.get((False, True, False)) == "allset.duplicate", (km, items)


def test_smart_duplicate_copies_and_takes_back_an_unmoved_copy():
    arm, (j1, j2, j3), _layers = _chain()
    shown = manip.from_xform_gizmo
    manip.from_xform_gizmo = lambda _context: True
    try:
        _pose_pick(arm, j2)
        assert manip.kind(bpy.context) == 'DUPLICATE_JOINTS'
        state = manip.start_duplicate_joints(bpy.context)
        assert _parents(arm)["joint4"] == j1 and _picked_pose(arm) == ["joint4"]
        assert not manip.moved(state)
        manip.revert(state)                            # a Shift+click: no copy left
        assert len(arm.data.bones) == 3 and arm.mode == 'POSE' and _picked_pose(arm) == [j2]
        state = manip.start_duplicate_joints(bpy.context)
        arm.pose.bones["joint4"].rotation_euler.x = 0.3   # the drag turned it
        assert manip.moved(state)

        arm, (j1, j2, j3), _layers = _chain(keyed=False)
        js.select_edit(bpy.context, arm, j2)
        assert manip.kind(bpy.context) == 'DUPLICATE_JOINTS'
        state = manip.start_duplicate_joints(bpy.context)
        assert arm.mode == 'EDIT' and [eb.name for eb in js._edit_picked(arm)] == ["joint4"]
        assert not manip.moved(state)
        manip.revert(state)
        assert arm.mode == 'EDIT' and len(arm.data.edit_bones) == 3
        assert [eb.name for eb in js._edit_picked(arm)] == [j2]
        # a Shift+click that went on to selection may leave Edit Mode before the copy is taken back
        state = manip.start_duplicate_joints(bpy.context)
        bpy.ops.object.mode_set(mode='OBJECT')
        assert not manip.moved(state), "the same place, read in another mode"
        manip.revert(state)
        assert arm.mode == 'OBJECT' and len(arm.data.bones) == 3
        bpy.ops.object.mode_set(mode='EDIT')
        js.clear(bpy.context)
        assert manip.kind(bpy.context) is None, "nothing picked"
    finally:
        manip.from_xform_gizmo = shown
