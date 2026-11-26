"""Script joints (``cmds.joint(p=...)``) keep jointOrient 0: their axes are the parent joint's, a root joint's the
world's, and a parent keeps its axes when its bone turns toward a new child. The drawn joint (rings and local axes)
follows those axes."""

from importlib import import_module

import bpy
from mathutils import Matrix

import kit

cmds = import_module(kit.MODULE + ".command_line.cmds_shim")
maya_joints = import_module(kit.MODULE + ".ui.maya_joints")
joint_frames = import_module(kit.MODULE + ".operators.joint_frames")


def _close(a, b, eps=1e-4):
    return all(abs(a[i][j] - b[i][j]) < eps for i in range(3) for j in range(3))


def _frames():
    arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    bpy.context.view_layer.update()
    return {n: j.frame for n, j in maya_joints.skeleton(arm, bpy.context.scene).items()}


def test_chain_axes_follow_the_world():
    bpy.ops.wm.read_homefile(use_empty=True)
    for p in ((-3, 0, 0), (0, 2, 0), (3, 0, 0)):
        cmds.joint(p=p)
    frames = _frames()
    for name in ("joint1", "joint2", "joint3"):
        assert _close(frames[name], joint_frames.MAYA_WORLD), (name, frames[name])
        assert cmds.getAttr(name + ".jointOrient") == [(0.0, 0.0, 0.0)]


def test_child_takes_an_oriented_parents_axes():
    bpy.ops.wm.read_homefile(use_empty=True)
    cmds.joint(p=(0, 0, 0))
    arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    turn = Matrix.Rotation(0.6, 3, 'Z') @ joint_frames.MAYA_WORLD
    bpy.ops.object.mode_set(mode='EDIT')
    joint_frames.set_maya_frame(arm, arm.data.edit_bones["joint1"], turn)
    bpy.ops.object.mode_set(mode='POSE')
    cmds.select("joint1")
    cmds.joint(p=(4, 1, 0))
    frames = _frames()
    assert _close(frames["joint1"], turn), frames["joint1"]
    assert _close(frames["joint2"], turn), frames["joint2"]
