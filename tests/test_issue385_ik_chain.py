"""#385: an IK handle on a 4-joint chain inside a 20-row cylinder (Joint Tool, Bind Skin, IK Handle from the first to
the last joint), the handle moved. Like Maya's RP solver: a perfectly straight chain has no bend to start from, so
it stays straight and only turns at the start joint; a chain with a small bend, or a straight one whose in-between
joints were turned a little and given Set Preferred Angle, bends and its end joint reaches the handle."""

import json
import math
from importlib import import_module

import bpy
from mathutils import Matrix, Vector

import kit

create = import_module(kit.MODULE + ".operators.create")
ik_rp = import_module(kit.MODULE + ".operators.ik_rp")
rig_maya = import_module(kit.MODULE + ".operators.rig_maya")
joint_frames = import_module(kit.MODULE + ".operators.joint_frames")
cb = import_module(kit.MODULE + ".ui.channel_box")

# Joint Tool clicks (Blender world), along the cylinder's axis
CHAINS = {
    "straight": [(0, 0, -1), (0, 0, -1 / 3), (0, 0, 1 / 3), (0, 0, 1)],
    "tiny": [(0, 0, -1), (0.01, 0, -1 / 3), (0.01, 0, 1 / 3), (0, 0, 1)],
    "clicked": [(0, 0, -1), (0.08, 0, -0.35), (-0.05, 0, 0.32), (0.02, 0, 1)],
    "bowed": [(0, 0, -1), (0.15, 0, -1 / 3), (0.15, 0, 1 / 3), (0, 0, 1)],
}
GOALS = [(1.0, 0, 0.5), (0.8, 0, 0.0), (0.5, 0.5, 0.6), (1.5, 0, -0.2)]


def _clean():
    if bpy.context.object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    ik_rp._solvers.clear()


def _turn_maya_z(arm, name, deg):
    """Turn a joint about its own (Maya) Z axis, like typing Rotate Z in the Channel Box."""
    pb = arm.pose.bones[name]
    a = joint_frames._maya_axes(pb.bone).normalized()
    pb.rotation_mode = 'XYZ'
    pb.rotation_euler = (a @ Matrix.Rotation(math.radians(deg), 3, 'Z') @ a.inverted()).to_euler('XYZ')


def build(points, prefer=None):
    """Cylinder (20 height rows), joints at ``points``, Bind Skin, IK handle first -> last joint. ``prefer``: None,
    or "zero" / "keep" = before binding, the in-between joints turned 10 degrees, Set Preferred Angle on the
    skeleton, the turn taken back (zero) or kept."""
    _clean()
    cyl = create.create(bpy.context, 'CYLINDER', overrides={"subdivisionsHeight": 20})
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    assert bpy.ops.allset.joint_tool(points=json.dumps(points)) == {'FINISHED'}
    arm = bpy.context.active_object
    assert arm.type == 'ARMATURE', arm
    bpy.ops.object.mode_set(mode='OBJECT')
    names = [b.name for b in arm.data.bones]
    assert len(names) == 4, names
    if prefer is not None:
        for n in names[1:3]:
            _turn_maya_z(arm, n, 10.0)
        rig_maya.set_preferred([arm.pose.bones[names[0]]], True)
        if prefer == "zero":
            for n in names:
                arm.pose.bones[n].rotation_euler = (0.0, 0.0, 0.0)
    for ob in bpy.context.selected_objects:
        ob.select_set(False)
    arm.select_set(True)
    cyl.select_set(True)
    bpy.context.view_layer.objects.active = arm
    assert bpy.ops.allset.bind_skin() == {'FINISHED'}
    for ob in bpy.context.selected_objects:
        ob.select_set(False)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='POSE')
    for pb in arm.pose.bones:
        cb.set_bone_selected(pb, pb.name in (names[0], names[-1]))
    arm.data.bones.active = arm.data.bones[names[-1]]
    assert bpy.ops.allset.ik_handle() == {'FINISHED'}
    handle = bpy.context.active_object
    assert handle.get(ik_rp.MULTI) == 1, "the kit solves the 3-bone RP chain"
    return cyl, arm, handle, names


def move_handle(handle, goal):
    handle.location = goal
    for _ in range(3):
        bpy.context.view_layer.update()
        ik_rp.update_handle(handle)
    bpy.context.view_layer.update()


def joint_points(arm):
    """World positions of the four joints."""
    return [arm.matrix_world @ pb.head for pb in arm.pose.bones]


def bends(pts):
    """Angle (degrees) between the bones at each in-between joint."""
    return [math.degrees((pts[i] - pts[i - 1]).angle(pts[i + 1] - pts[i])) for i in range(1, len(pts) - 1)]


def test_straight_chain_stays_straight_and_turns_at_the_start_joint():
    _cyl, arm, handle, _names = build(CHAINS["straight"])
    start = Vector(CHAINS["straight"][0])
    for goal in GOALS:
        move_handle(handle, Vector(goal))
        pts = joint_points(arm)
        assert max(bends(pts)) < 1e-3, (goal, bends(pts))
        aim = (Vector(goal) - start).normalized()
        assert ((pts[-1] - start).normalized() - aim).length < 1e-4, (goal, tuple(pts[-1]))
        assert abs((pts[-1] - start).length - 2.0) < 1e-4, "the chain keeps its length"


def test_bent_chains_bend_and_reach_the_handle():
    for name in ("tiny", "clicked", "bowed"):
        _cyl, arm, handle, _names = build(CHAINS[name])
        for goal in GOALS:
            move_handle(handle, Vector(goal))
            pts = joint_points(arm)
            assert (pts[-1] - Vector(goal)).length < 1e-4, (name, goal, tuple(pts[-1]))
            assert min(bends(pts)) > 20.0, (name, goal, bends(pts))


def test_preferred_angle_lets_a_straight_chain_bend():
    for prefer in ("zero", "keep"):
        _cyl, arm, handle, names = build(CHAINS["straight"], prefer)
        assert rig_maya.PREFERRED_PROP in arm.pose.bones[names[1]]
        for goal in GOALS:
            move_handle(handle, Vector(goal))
            pts = joint_points(arm)
            assert (pts[-1] - Vector(goal)).length < 1e-4, (prefer, goal, tuple(pts[-1]))
            assert min(bends(pts)) > 20.0, (prefer, goal, bends(pts))


def test_skinned_cylinder_follows_the_chain():
    cyl, arm, handle, _names = build(CHAINS["clicked"])
    top = max(cyl.data.vertices, key=lambda v: v.co.z).index
    before = (cyl.matrix_world @ cyl.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.vertices[top].co).copy()
    move_handle(handle, Vector(GOALS[0]))
    after = cyl.matrix_world @ cyl.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.vertices[top].co
    assert (after - before).length > 0.3, (tuple(before), tuple(after))
