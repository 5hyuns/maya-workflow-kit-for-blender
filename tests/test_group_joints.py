"""Edit > Group (Ctrl+G) with joints selected: a skinned skeleton grouped by its root joint moves with the group and
the skin follows, like Maya (group1 becomes the root joint's parent). A joint inside a chain can't get a group
parent here: Group warns and changes nothing. Freeze / Delete History on the group keep the bind.
GUI: tests/gui/gui_group_joints.py."""

from importlib import import_module
from math import radians

import bpy
from mathutils import Matrix, Vector

import kit

joints = import_module(kit.MODULE + ".operators.joints")
skin = import_module(kit.MODULE + ".operators.skin")
group = import_module(kit.MODULE + ".operators.group")
cb = import_module(kit.MODULE + ".ui.channel_box")
follow = import_module(kit.MODULE + ".operators.skin_follow")


def _clear():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for arm in list(bpy.data.armatures):
        bpy.data.armatures.remove(arm)
    for me in list(bpy.data.meshes):
        bpy.data.meshes.remove(me)


def _skinned(offset=(0.0, 0.0, 0.0)):
    """skeleton joint1 > joint2 > joint3 up Z, a subdivided box bound to it; object mode, nothing selected."""
    o = Vector(offset)
    arm = joints.new_skeleton(bpy.context)
    parent = None
    names = []
    for z in (0.0, 1.0, 2.0):
        parent = joints.add_joint(arm, o + Vector((0, 0, z)), parent, length=0.5)
        names.append(parent)
    joints.finish(bpy.context, arm, names)
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=o + Vector((0, 0, 1.0)), scale=(0.3, 0.3, 1.2))
    box = bpy.context.active_object
    with bpy.context.temp_override(object=box, active_object=box):
        box.modifiers.new("sub", 'SUBSURF').levels = 2
        bpy.ops.object.modifier_apply(modifier="sub")
    skin.bind_skin(bpy.context, arm, [box])
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in bpy.context.selected_objects:
        ob.select_set(False)
    assert skin.armature_modifier(box) is not None
    return arm, box, names


def _pick_joints(arm, names):
    """Maya: click a joint = the skeleton in pose mode with that joint selected."""
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in bpy.context.selected_objects:
        ob.select_set(False)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='POSE')
    for pb in arm.pose.bones:
        cb.set_bone_selected(pb, pb.name in names)
    arm.data.bones.active = arm.data.bones[names[-1]]


def _skin_points(box):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = box.evaluated_get(dg)
    me = ev.to_mesh()
    pts = [box.matrix_world @ v.co for v in me.vertices]
    ev.to_mesh_clear()
    return pts


def _assert_follows(before, after, m, what):
    worst = max((m @ a - b).length for a, b in zip(before, after))
    assert worst < 1e-4, f"{what}: skin off the moved group by {worst}"


def _move_group(grp, box, what):
    """Translate + turn the group: every skin point must move rigidly with it."""
    bpy.context.view_layer.update()
    before = _skin_points(box)
    old = grp.matrix_world.copy()
    grp.location = Vector(grp.location) + Vector((2.0, -1.0, 0.5))
    grp.rotation_euler = (0.0, 0.0, radians(30))
    bpy.context.view_layer.update()
    delta = grp.matrix_world @ old.inverted()
    _assert_follows(before, _skin_points(box), delta, what)


def test_group_root_joint_moves_skin():
    _clear()
    arm, box, names = _skinned()
    _pick_joints(arm, [names[0]])
    assert bpy.ops.allset.group('EXEC_DEFAULT') == {'FINISHED'}
    grp = bpy.data.objects["group1"]
    assert grp.type == 'EMPTY' and arm.parent == grp, arm.parent
    assert box.parent is None, "the skin stays where it is in the hierarchy (Maya)"
    assert bpy.context.mode == 'OBJECT'
    assert bpy.context.active_object == grp and grp.select_get() and not arm.select_get()
    assert grp.matrix_world == Matrix.Identity(4), "pivot at the origin (Maya Group default)"
    _move_group(grp, box, "Ctrl+G on joint1")


def test_group_from_menu_item():
    _clear()
    arm, box, names = _skinned(offset=(1.0, 2.0, 0.0))
    _pick_joints(arm, [names[0]])
    assert bpy.ops.allset.menu_item('EXEC_DEFAULT', item="Edit/Group") == {'FINISHED'}
    grp = bpy.data.objects.get("group1")
    assert grp is not None and arm.parent == grp
    _move_group(grp, box, "Edit > Group on joint1")


def test_group_option_window_world_center():
    """Group Options (Center pivot) also takes joints."""
    _clear()
    arm, box, names = _skinned(offset=(1.0, 0.0, 0.0))
    _pick_joints(arm, [names[0]])
    assert bpy.ops.allset.opt_group('EXEC_DEFAULT', pivot="Center") == {'FINISHED'}
    grp = bpy.data.objects["group1"]
    assert arm.parent == grp
    _move_group(grp, box, "Group Options on joint1")


def test_group_joint_and_object_together():
    _clear()
    arm, box, names = _skinned()
    bpy.ops.object.empty_add(location=(3, 0, 0))
    loc = bpy.context.active_object
    _pick_joints(arm, [names[0]])
    loc.select_set(True)
    assert bpy.ops.allset.group('EXEC_DEFAULT') == {'FINISHED'}
    grp = bpy.data.objects["group1"]
    assert arm.parent == grp and loc.parent == grp
    assert (loc.matrix_world.translation - Vector((3, 0, 0))).length < 1e-6


def test_group_child_joint_warns_and_does_nothing():
    _clear()
    arm, box, names = _skinned()
    _pick_joints(arm, [names[1]])
    count = len(bpy.data.objects)
    assert bpy.ops.allset.group('EXEC_DEFAULT') == {'CANCELLED'}
    assert len(bpy.data.objects) == count and arm.parent is None
    assert bpy.context.mode == 'POSE', "the joint selection stays"
    assert group.CHILD_JOINT_WARNING.startswith("Cannot group joint")


def test_group_some_roots_of_a_skeleton_warns():
    """Two root joints in one skeleton: grouping only one of them can't move it alone."""
    _clear()
    arm = joints.new_skeleton(bpy.context)
    a = joints.add_joint(arm, Vector((0, 0, 0)), None)
    b = joints.add_joint(arm, Vector((2, 0, 0)), None)
    joints.finish(bpy.context, arm, [a, b])
    bpy.ops.object.mode_set(mode='OBJECT')
    _pick_joints(arm, [a])
    assert bpy.ops.allset.group('EXEC_DEFAULT') == {'CANCELLED'}
    assert arm.parent is None
    _pick_joints(arm, [a, b])
    assert bpy.ops.allset.group('EXEC_DEFAULT') == {'FINISHED'}
    assert arm.parent == bpy.data.objects["group1"]


def test_group_then_freeze_and_delete_history_keep_the_bind():
    _clear()
    arm, box, names = _skinned()
    _pick_joints(arm, [names[0]])
    assert bpy.ops.allset.group('EXEC_DEFAULT') == {'FINISHED'}
    grp = bpy.data.objects["group1"]
    grp.location = (1.0, 0.5, 0.0)
    bpy.context.view_layer.update()
    rest = _skin_points(box)
    # Freeze Transformations on group1 (its hierarchy: the skeleton too)
    assert bpy.ops.allset.freeze_transform('EXEC_DEFAULT') == {'FINISHED'}
    bpy.context.view_layer.update()
    _assert_follows(rest, _skin_points(box), Matrix.Identity(4), "Freeze on group1")
    assert skin.armature_modifier(box) is not None
    # Delete History on group1 leaves the skin alone (the skin is on the mesh, not under the group)
    assert bpy.ops.allset.delete_history('EXEC_DEFAULT') == {'FINISHED'}
    assert skin.armature_modifier(box) is not None, "Delete History on the group removed the skin"
    _move_group(grp, box, "after Freeze / Delete History")
    # the joints still bend the skin
    bpy.context.view_layer.update()
    before = _skin_points(box)
    _pick_joints(arm, [names[1]])
    arm.pose.bones[names[1]].rotation_euler = (radians(40), 0, 0)
    bpy.context.view_layer.update()
    after = _skin_points(box)
    assert max((a - b).length for a, b in zip(before, after)) > 0.1, "the skin no longer follows its joints"


def test_ctrl_g_in_pose_mode_keymap():
    kc = kit.maya_kc()
    for km in ("Pose", "Armature", "Object Mode", "Outliner"):
        items = [it for it in kc.keymaps[km].keymap_items
                 if it.idname == "allset.group" and it.type == 'G' and it.ctrl and not it.shift and it.active]
        assert items, f"{km}: no Ctrl+G Group"


def test_moving_the_skeleton_object_moves_the_skin():
    """The skin reads the joints' world matrices, so it follows its skeleton however that moves."""
    _clear()
    arm, box, names = _skinned()
    assert len(follow.follows(box)) == 1 and follow.follows(box)[0].target == arm
    assert cb.constraints(box) == [], "the follow is part of the skin, not a Maya constraint node"
    assert not cb.constrained_keys(box)
    _move_group(arm, box, "skeleton object moved")
    assert tuple(box.location) == (0.0, 0.0, 1.0), "the mesh's own channels stay"


def test_group_adds_the_follow_to_older_binds():
    _clear()
    arm, box, names = _skinned()
    for con in follow.follows(box):
        box.constraints.remove(con)
    _pick_joints(arm, [names[0]])
    assert bpy.ops.allset.group('EXEC_DEFAULT') == {'FINISHED'}
    _move_group(bpy.data.objects["group1"], box, "older bind grouped")


def test_group_from_skeleton_edit_mode():
    """The Move tool picks joints in skeleton edit mode: Ctrl+G groups the same way."""
    _clear()
    arm, box, names = _skinned()
    _pick_joints(arm, [names[0]])
    bpy.ops.object.mode_set(mode='EDIT')
    for eb in arm.data.edit_bones:
        eb.select = eb.select_head = eb.select_tail = eb.name == names[0]
    arm.data.edit_bones.active = arm.data.edit_bones[names[0]]
    assert bpy.ops.allset.group('EXEC_DEFAULT') == {'FINISHED'}
    assert arm.parent == bpy.data.objects["group1"] and bpy.context.mode == 'OBJECT'


def _moved_skin():
    _clear()
    arm, box, names = _skinned()
    arm.location = (1.0, 0.0, 0.0)
    arm.pose.bones[names[1]].rotation_euler = (radians(30), 0, 0)
    bpy.context.view_layer.update()
    return arm, box, _skin_points(box)


def _only(ob):
    for other in bpy.context.selected_objects:
        other.select_set(False)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob


def test_unbind_bake_keeps_the_shape_and_drops_the_follow():
    arm, box, shown = _moved_skin()
    skin.unbind(bpy.context, box, history="BAKE")
    bpy.context.view_layer.update()
    assert not follow.follows(box) and skin.armature_modifier(box) is None
    _assert_follows(shown, _skin_points(box), Matrix.Identity(4), "Unbind (bake history)")
    assert tuple(box.location) == (0.0, 0.0, 1.0)


def test_unbind_delete_goes_back_to_the_bind_place():
    arm, box, shown = _moved_skin()
    skin.unbind(bpy.context, box, history="DELETE")
    bpy.context.view_layer.update()
    assert not follow.follows(box)
    assert (box.matrix_world.translation - Vector((0, 0, 1))).length < 1e-6


def test_delete_history_on_the_skin_keeps_the_shape():
    arm, box, shown = _moved_skin()
    _only(box)
    assert bpy.ops.allset.delete_history('EXEC_DEFAULT') == {'FINISHED'}
    bpy.context.view_layer.update()
    assert skin.armature_modifier(box) is None and not follow.follows(box)
    _assert_follows(shown, _skin_points(box), Matrix.Identity(4), "Delete History on the skin")
    arm.location = (3.0, 0.0, 0.0)
    bpy.context.view_layer.update()
    _assert_follows(shown, _skin_points(box), Matrix.Identity(4), "baked skin no longer follows")


def test_non_deformer_history_keeps_the_follow():
    arm, box, shown = _moved_skin()
    _only(box)
    assert bpy.ops.allset.delete_history('EXEC_DEFAULT', non_deformer=True) == {'FINISHED'}
    assert skin.armature_modifier(box) is not None and follow.follows(box)
