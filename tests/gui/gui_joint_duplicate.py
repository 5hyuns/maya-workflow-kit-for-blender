"""In a real UI: Ctrl+D on a joint picked with the Move tool (joint Edit Mode) duplicates that joint with the joints
below it, like Maya's Duplicate: joint1 > joint2 > joint3, joint2 picked, Ctrl+D -> joint4 (under joint1, where
joint2 is) > joint5, joint4 picked, still Edit Mode; joint2 in a display layer -> joint4 in it too. Then Pose Mode
(another tool): Ctrl+D on joint3 -> joint6 under joint2."""

import os
import sys
from importlib import import_module

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, load_maya_layout, run, setup, step, view3d  # noqa: E402

GUI_TIMEOUT = 200
C = {}


def mod(name):
    return import_module(MODULE + name)


def parents():
    arm = bpy.data.objects[C["arm"]]
    bones = arm.data.edit_bones if arm.mode == 'EDIT' else arm.data.bones
    return {b.name: (b.parent.name if b.parent else None) for b in bones}


def ctrl_d():
    def press():
        x, y = C["xy"]
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
        ev('D', 'PRESS', ctrl=True, x=x, y=y)
        ev('D', 'RELEASE', ctrl=True, x=x, y=y)
    press.__name__ = f"s_ctrl_d_{len(C.setdefault('presses', [])) }"
    C["presses"].append(1)
    step(press)


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_scene():
    bpy.ops.allset.keymap_activate()
    joints = mod(".operators.joints")
    arm = joints.new_skeleton(bpy.context)
    names, parent = [], None
    for z in (0.0, 2.0, 4.0):
        parent = joints.add_joint(arm, Vector((0.0, 0.0, z)), parent, length=0.5)
        names.append(parent)
    joints.finish(bpy.context, arm, names)
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    le, lj = mod(".ui.layer_editor"), mod(".ui.layer_joints")
    coll = le.new_layer(bpy.context.scene)
    lj.set_layer(arm.pose.bones[names[1]], coll)
    C.update(arm=arm.name, names=names, layer=coll.name)
    for o in bpy.context.scene.objects:
        o.select_set(False)
    mod(".operators.joint_selection").select_edit(bpy.context, arm, names[1])   # the Move tool's pick
    _area, region = view3d()
    C["xy"] = (region.x + region.width // 2, region.y + region.height // 2)


ctrl_d()


@step
def s_edit_done():
    arm = bpy.data.objects[C["arm"]]
    j1, j2, j3 = C["names"]
    par = parents()
    check(f"Ctrl+D in joint Edit Mode copies joint2 with joint3 under joint1 ({par})",
          par.get("joint4") == j1 and par.get("joint5") == "joint4" and len(par) == 5)
    js = mod(".operators.joint_selection")
    picked = [eb.name for eb in js._edit_picked(arm)] if arm.mode == 'EDIT' else []
    check(f"still Edit Mode with the copy picked ({arm.mode}, {picked})", arm.mode == 'EDIT' and picked == ["joint4"])
    bpy.ops.object.mode_set(mode='POSE')
    lj = mod(".ui.layer_joints")
    layer = lj.layer_of(arm.pose.bones["joint4"])
    check(f"the copy is in joint2's display layer ({layer.name if layer else None})",
          layer is not None and layer.name == C["layer"])
    cb = mod(".ui.channel_box")
    for pb in arm.pose.bones:
        cb.set_bone_selected(pb, pb.name == j3)
    arm.data.bones.active = arm.data.bones[j3]
    arm["allset_joint_pose_pin"] = True          # F8: stay in Pose Mode with the Move tool


ctrl_d()


@step
def s_pose_done():
    arm = bpy.data.objects[C["arm"]]
    par = parents()
    check(f"Ctrl+D in Pose Mode copies joint3 under joint2 ({par})", par.get("joint6") == C["names"][1])
    cb = mod(".ui.channel_box")
    check(f"the copy is picked ({arm.mode})",
          arm.mode == 'POSE' and [pb.name for pb in arm.pose.bones if cb.bone_selected(pb)] == ["joint6"])


run()
