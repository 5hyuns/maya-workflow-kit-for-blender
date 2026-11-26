"""Hide / Show on joints (#568): Ctrl+H on a selected joint hides it and the joints below it (one visibility per
joint, inherited like Maya), Show Last Hidden (Ctrl+Shift+H, also from Object Mode), Show All, h / Shift+H and
Alt+H work on joints in Pose and skeleton Edit mode, a joint hidden in one mode stays hidden in the other, and a bone
other tools hid can be shown again. GUI (keys, undo, menu): tests/gui/gui_issue568_joint_hide.py."""

from importlib import import_module

import bpy
from mathutils import Vector

import kit

joints = import_module(kit.MODULE + ".operators.joints")
jv = import_module(kit.MODULE + ".operators.joint_visibility")


def _clear():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for arm in list(bpy.data.armatures):
        bpy.data.armatures.remove(arm)


def _chain():
    """joint1 > joint2 > joint3 > joint4, plus a branch joint5 under joint1; Pose mode, nothing selected."""
    _clear()
    arm = joints.new_skeleton(bpy.context)
    names, parent = [], None
    for z in (0.0, 1.0, 2.0, 3.0):
        parent = joints.add_joint(arm, Vector((0, 0, z)), parent, length=0.5)
        names.append(parent)
    joints.finish(bpy.context, arm, names)
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    branch = None
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='EDIT')
    eb = arm.data.edit_bones.new("branch")
    eb.head, eb.tail = (1.0, 0, 0), (1.5, 0, 0)
    eb.parent = arm.data.edit_bones[names[0]]
    branch = eb.name
    bpy.ops.object.mode_set(mode='POSE')
    _pick(arm, [])
    return arm, names + [branch]


def _pick(arm, picked):
    for pb in arm.pose.bones:
        pb.select = pb.name in picked


def _hidden(arm):
    """Hidden joints (both flags must agree)."""
    out = []
    for b in arm.data.bones:
        pb = arm.pose.bones[b.name]
        assert pb.hide == b.hide, f"{b.name}: pose hide {pb.hide} vs bone hide {b.hide}"
        if pb.hide:
            out.append(b.name)
    return sorted(out)


def _selected(arm):
    return sorted(pb.name for pb in arm.pose.bones if pb.select)


def _vis(action, **kw):
    return bpy.ops.allset.visibility(action=action, **kw)


def test_hide_selection_hides_the_joint_and_the_joints_below():
    arm, n = _chain()
    _pick(arm, [n[1]])
    assert _vis('HIDE') == {'FINISHED'}
    assert _hidden(arm) == sorted(n[1:4]), _hidden(arm)
    assert _selected(arm) == [], "hidden joints are deselected"


def test_show_last_hidden_brings_back_the_hidden_joint_selected():
    arm, n = _chain()
    _pick(arm, [n[2]])
    _vis('HIDE')
    _pick(arm, [n[4]])
    _vis('HIDE')                       # the newer hide is the last one
    assert _hidden(arm) == sorted([n[2], n[3], n[4]])
    _vis('SHOW_LAST')
    assert _hidden(arm) == sorted([n[2], n[3]]), _hidden(arm)
    assert n[4] in _selected(arm)


def test_show_last_hidden_from_object_mode():
    arm, n = _chain()
    _pick(arm, [n[1]])
    _vis('HIDE')
    bpy.ops.object.mode_set(mode='OBJECT')
    assert _vis('SHOW_LAST') == {'FINISHED'}
    assert _hidden(arm) == []


def test_object_hide_is_the_new_last_hidden():
    arm, n = _chain()
    _pick(arm, [n[1]])
    _vis('HIDE')
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.mesh.primitive_cube_add()
    cube = bpy.context.active_object
    _vis('HIDE')
    assert cube.hide_viewport
    _vis('SHOW_LAST')
    assert not cube.hide_viewport
    assert _hidden(arm) == sorted(n[1:4]), "the joints hidden before stay hidden"


def test_show_all_in_pose_and_object_mode():
    arm, n = _chain()
    _pick(arm, [n[1]])
    _vis('HIDE')
    _vis('SHOW_ALL')
    assert _hidden(arm) == []
    _pick(arm, [n[0]])
    _vis('HIDE')
    assert _hidden(arm) == sorted(n)
    bpy.ops.object.mode_set(mode='OBJECT')
    _vis('SHOW_ALL')
    assert _hidden(arm) == []
    _vis('SHOW_TYPE', kind='JOINTS')        # nothing hidden: no error


def test_show_joints_by_type_from_object_mode():
    arm, n = _chain()
    _pick(arm, [n[3]])
    _vis('HIDE')
    bpy.ops.object.mode_set(mode='OBJECT')
    _vis('SHOW_TYPE', kind='JOINTS')
    assert _hidden(arm) == []


def test_a_joint_hidden_in_pose_mode_stays_hidden_in_edit_mode_and_back():
    arm, n = _chain()
    _pick(arm, [n[2]])
    _vis('HIDE')
    bpy.ops.object.mode_set(mode='EDIT')
    assert sorted(b.name for b in arm.data.edit_bones if b.hide) == sorted(n[2:4])
    for eb in arm.data.edit_bones:
        eb.select = eb.select_head = eb.select_tail = eb.name == n[4]
    assert _vis('HIDE') == {'FINISHED'}
    assert sorted(b.name for b in arm.data.edit_bones if b.hide) == sorted(n[2:5])
    _vis('SHOW_LAST')
    assert sorted(b.name for b in arm.data.edit_bones if b.hide) == sorted(n[2:4])
    bpy.ops.object.mode_set(mode='POSE')
    assert _hidden(arm) == sorted(n[2:4])
    _vis('SHOW_ALL')
    assert _hidden(arm) == []


def test_toggle_and_show_selection():
    arm, n = _chain()
    _pick(arm, [n[3]])
    _vis('TOGGLE')
    assert _hidden(arm) == [n[3]]
    _vis('TOGGLE')                      # h again with nothing visible selected: the kept joint comes back
    assert _hidden(arm) == []
    assert _selected(arm) == [n[3]]
    _vis('TOGGLE')
    _vis('SHOW_SELECTED')               # Shift+H: the hidden-but-selected joint
    assert _hidden(arm) == []


def test_hide_unselected_keeps_the_selection_chain():
    arm, n = _chain()
    _pick(arm, [n[1]])
    _vis('HIDE_UNSELECTED')
    assert _hidden(arm) == [n[4]], _hidden(arm)
    _vis('SHOW_LAST')
    assert _hidden(arm) == []


def test_bones_hidden_by_other_tools_can_be_shown():
    arm, n = _chain()
    arm.pose.bones[n[2]].hide = True        # e.g. Blender's own hide, or an older file
    _vis('SHOW_ALL')
    assert _hidden(arm) == []
    arm.pose.bones[n[1]].hide = True
    _pick(arm, [n[0]])
    _vis('HIDE')
    arm.pose.bones[n[0]].hide = False       # shown again by another tool: its own flag goes
    arm.data.bones[n[0]].hide = False
    _vis('SHOW_LAST')
    assert _hidden(arm) == sorted(n[1:4]), "the joint other tools hid stays hidden (and the joints below it)"


def test_nothing_selected_hides_nothing():
    arm, n = _chain()
    assert _vis('HIDE') == {'FINISHED'}
    assert _hidden(arm) == []


def test_keys_in_pose_and_edit_mode():
    kc = kit.maya_kc()
    want = {("H", False, False, False): "TOGGLE", ("H", True, False, False): "HIDE",
            ("H", False, False, True): "HIDE_UNSELECTED", ("H", False, True, False): "SHOW_SELECTED",
            ("H", True, True, False): "SHOW_LAST"}
    for km in ("Pose", "Armature"):
        items = kc.keymaps[km].keymap_items
        for (key, ctrl, shift, alt), action in want.items():
            first = next((it for it in items if it.active and it.type == key and it.value == 'PRESS'
                          and bool(it.ctrl) == ctrl and bool(it.shift) == shift and bool(it.alt) == alt), None)
            assert first is not None and first.idname == "allset.visibility" and \
                first.properties.action == action, f"{km} {key} ctrl={ctrl} shift={shift} alt={alt}: " \
                f"{first and first.idname}"
