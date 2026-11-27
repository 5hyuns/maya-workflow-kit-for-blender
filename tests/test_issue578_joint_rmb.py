"""#578: right-click with joints opens Maya's joint marking menu (Set / Assume Preferred Angle at W / E, Edit Joints at
N), over empty space with no joint selected Maya's Select All / Complete Tool menu, never Blender's Pose context menu.
GUI: tests/gui/gui_issue578_joint_rmb.py."""

import math
from importlib import import_module

import bpy

import kit

marking = import_module(kit.MODULE + ".marking")
mm = import_module(kit.MODULE + ".marking.menus")
rig = import_module(kit.MODULE + ".operators.rig_maya")


def _skeleton():
    """joint1 -> joint2 -> joint3 in pose mode, nothing selected."""
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    arm = bpy.data.armatures.new("skeleton")
    ob = bpy.data.objects.new("joint1", arm)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    parent = None
    for i in range(3):
        b = arm.edit_bones.new(f"joint{i + 1}")
        b.head, b.tail = (0, 0, i * 2.0), (0, 0, i * 2.0 + 2.0)
        if parent is not None:
            b.parent, b.use_connect = parent, True
        parent = b
    bpy.ops.object.mode_set(mode='POSE')
    for pb in ob.pose.bones:
        pb.select = False
    return ob


def _resolve(joint="", target=""):
    wm = bpy.context.window_manager
    wm.allset_mm_joint = joint
    wm.allset_mm_target = target
    return marking.resolve("RMB", bpy.context)


def test_pose_keymap_rmb_is_the_marking_menu():
    km = kit.maya_kc().keymaps["Pose"]
    rmb = [k for k in km.keymap_items if k.type == 'RIGHTMOUSE' and k.active]
    assert any(k.idname == "allset.marking_menu" and not (k.shift or k.ctrl or k.alt) for k in rmb), \
        [(k.idname, k.shift, k.ctrl) for k in rmb]
    assert not any(k.idname == "wm.call_menu" for k in rmb), "Blender's Pose context menu stays off RMB"


def test_joint_menu_over_a_joint_or_with_a_selected_joint():
    ob = _skeleton()
    joint = ("pie", marking.idname("RMB_JOINT"))
    assert _resolve() == ("pie", marking.idname("RMB_EMPTY")), "joints only, none selected, empty space"
    assert _resolve("joint2", ob.name) == joint, "over a joint"
    ob.pose.bones["joint2"].select = True
    assert _resolve() == joint, "a joint selected, empty space"
    bpy.ops.object.mode_set(mode='OBJECT')
    assert _resolve() == joint, "object mode, the skeleton is the lead"


def test_joint_menu_layout():
    m = mm.MENUS["RMB_JOINT"]
    assert {k: v[0] for k, v in m.radial.items()} == {"W": "Set Preferred Angle", "E": "Assume Preferred Angle",
                                                       "N": "Edit Joints"}
    sub = m.radial["N"][1]
    assert {k: v[0] for k, v in sub.radial.items()} == {"N": "Add", "W": "Insert", "E": "Remove"}
    labels = [e[0] for e in m.items if e != mm.DIVIDER]
    assert labels[:6] == [mm.OBJECT_TITLE, "Select", "Select All", "Deselect All", "Select Hierarchy",
                          "Invert Selection"], labels


def test_items_act_on_the_joint_under_the_mouse():
    ob = _skeleton()
    wm = bpy.context.window_manager
    wm.allset_mm_target, wm.allset_mm_joint = ob.name, "joint2"
    for pb in ob.pose.bones:
        pb.rotation_mode = 'XYZ'
        pb.rotation_euler = (0.3, 0, 0)
    assert bpy.ops.allset.mm_joint(action='SET_PREFERRED') == {'FINISHED'}
    got = {pb.name: rig.PREFERRED_PROP in pb for pb in ob.pose.bones}
    assert got == {"joint1": False, "joint2": True, "joint3": True}, got     # the joint and its children
    ob.pose.bones["joint3"].rotation_euler = (0, 0, 0)
    assert bpy.ops.allset.mm_joint(action='ASSUME_PREFERRED') == {'FINISHED'}
    assert math.isclose(ob.pose.bones["joint3"].rotation_euler[0], 0.3, abs_tol=1e-5)
    assert bpy.ops.allset.mm_joint(action='SELECT') == {'FINISHED'}
    assert [pb.name for pb in ob.pose.bones if pb.select] == ["joint2"]
    assert ob.data.bones.active.name == "joint2"
    assert bpy.ops.allset.mm_joint(action='HIERARCHY') == {'FINISHED'}
    assert [pb.name for pb in ob.pose.bones if pb.select] == ["joint2", "joint3"]
