"""Bind Skin keeps the mesh where it is (#230): Maya binds in the current pose, so binding a mesh to a chain that an
IK handle / pole vector (or a hand pose) has bent away from its rest shape doesn't move a single vertex."""

from importlib import import_module

import bpy
from mathutils import Vector

import kit

skin = import_module(kit.MODULE + ".operators.skin")


def _scene(posed):
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    arm_data = bpy.data.armatures.new("skeleton1")
    arm = bpy.data.objects.new("skeleton1", arm_data)
    bpy.context.scene.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='EDIT')
    a = arm_data.edit_bones.new("joint1")
    a.head, a.tail = (0, 0, 0), (2, 0, 0.0)
    b = arm_data.edit_bones.new("joint2")
    b.head, b.tail, b.parent, b.use_connect = (2, 0, 0.0), (4, 0, 0), a, True
    bpy.ops.object.mode_set(mode='OBJECT')
    if posed == "IK":
        target = bpy.data.objects.new("ikHandle1", None)
        bpy.context.scene.collection.objects.link(target)
        target.location = (3, 0, 1.5)
        con = arm.pose.bones["joint2"].constraints.new('IK')
        con.target, con.chain_count = target, 2
    elif posed == "ROT":
        arm.pose.bones["joint1"].rotation_mode = 'XYZ'
        arm.pose.bones["joint1"].rotation_euler = (0, -0.6, 0)
    bpy.ops.mesh.primitive_cube_add(size=1)
    mesh = bpy.context.active_object
    mesh.scale = (4, 0.5, 0.5)
    mesh.location = (2, 0, 0)
    bpy.ops.object.transform_apply(scale=True, location=False)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.subdivide(number_cuts=6)
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.update()
    return arm, mesh


def _world(mesh):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = mesh.evaluated_get(dg)
    return [ev.matrix_world @ v.co for v in ev.data.vertices]


def _bind_and_measure(posed):
    arm, mesh = _scene(posed)
    before = _world(mesh)
    skin.bind_skin(bpy.context, arm, [mesh])
    bpy.context.view_layer.update()
    after = _world(mesh)
    return max((p - q).length for p, q in zip(before, after))


def test_bind_at_rest_keeps_the_mesh():
    assert _bind_and_measure(None) < 1e-4


def test_bind_with_a_hand_pose_keeps_the_mesh():
    d = _bind_and_measure("ROT")
    assert d < 1e-4, f"the mesh moved {d:.4f} on bind"


def test_bind_with_an_ik_bent_chain_keeps_the_mesh():
    d = _bind_and_measure("IK")
    assert d < 1e-4, f"the mesh moved {d:.4f} on bind"
