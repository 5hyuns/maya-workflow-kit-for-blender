"""Issue #320: the joints of a Rigify human metarig and of its generated rig draw at a normal size in Maya mode, in a
metre scene and in a centimetre scene: a Radius 1 joint (a new joint's Radius) is 10 cm across in a metre scene
(Joint Size in Metre Scenes 10) and 1 cm in a centimetre scene, so on a 2 m character the joints stay small.
Stick / Wire skeletons draw lines (no spheres).

The armature object's own scale leaves the joints at their Radius size, like Maya, where a joint's own scale doesn't
change its sphere and the joints below keep their size (Segment Scale Compensate): a metarig added at its 2 unit
height in a scene with Unit Scale 0.01 and scaled up to fit the character keeps small joints. A scaled object the
skeleton is parented to scales them, like a scaled Maya group above a skeleton."""

from importlib import import_module

import addon_utils
import bpy
import numpy as np

import kit

mj = import_module(kit.MODULE + ".ui.maya_joints")
shapes = import_module(kit.MODULE + ".ui.maya_joints_shapes")
arrays = import_module(kit.MODULE + ".ui.maya_joints_arrays")
jd = import_module(kit.MODULE + ".operators.joint_display")
joint_tool = import_module(kit.MODULE + ".operators.joint_tool")


def _metarig():
    addon_utils.enable("rigify", default_set=True)
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    bpy.ops.object.armature_human_metarig_add()
    meta = bpy.context.object
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    return meta


def _height(arm):
    zs = [(arm.matrix_world @ b.head_local).z for b in arm.data.bones]
    zs += [(arm.matrix_world @ b.tail_local).z for b in arm.data.bones]
    return max(zs) - min(zs)


def _units(unit, scale_length=1.0):
    us = bpy.context.scene.unit_settings
    us.system, us.length_unit, us.scale_length = 'METRIC', unit, scale_length


def _drawn_radii(ob):
    """World radii of the joint spheres as Object Mode draws them (one read of the pose for all joints) and as the
    joint-by-joint path builds them."""
    scene = bpy.context.scene
    bpy.context.view_layer.update()
    jl = mj.joint_list(ob)
    k = arrays._pose_raw(ob, scene, jl)[3]
    batch = {round(float(r), 6) for r in jl.raw * k}
    single = {round(j.radius, 6) for j in mj.skeleton(ob, scene).values()}
    return batch, single


def _drawn_extent(ob):
    """(drawn lines' extent, bones' extent) in world units."""
    bpy.context.view_layer.update()
    parts = mj._parts(ob, bpy.context.scene, bpy.context.evaluated_depsgraph_get())
    pts = np.concatenate([a for part in (parts[0], parts[2]) for a in part[0] if a is not None and len(a)])
    mw = ob.matrix_world
    ends = np.array([tuple(mw @ v) for b in ob.data.bones for v in (b.head_local, b.tail_local)])
    return float(np.linalg.norm(pts.max(0) - pts.min(0))), float(np.linalg.norm(ends.max(0) - ends.min(0)))


def test_metarig_joints_are_small_in_a_metre_scene():
    scene = bpy.context.scene
    scene.property_unset("allset_joint_size")
    for unit, want in (('METERS', 0.05), ('CENTIMETERS', 0.005)):
        _units(unit)
        meta = _metarig()
        h = _height(meta)
        assert 1.5 < h < 2.5, ("a human-sized metarig", h)
        radii = {round(shapes.drawn_radius(b, scene), 6) for b in meta.data.bones}
        assert radii == {want}, (unit, radii)
        assert 2 * want / h < 0.06, ("a joint is a small part of the character", unit, 2 * want / h)
        meta.scale = (5.0, 5.0, 5.0)        # a 10 m character: the joints keep their Radius size
        batch, single = _drawn_radii(meta)
        assert batch == single == {want}, (unit, batch, single)


def test_metarig_scaled_to_fit_keeps_small_joints():
    """Unit Scale 0.01: the metarig comes in 2 cm tall (metres shown: 2 cm too) and is scaled up 100 times to fit a 2 m
    character; its joints are the same size as on a metarig made at that size."""
    scene = bpy.context.scene
    scene.property_unset("allset_joint_size")
    for unit, want_cm in (('METERS', 5.0), ('CENTIMETERS', 0.5), ('MILLIMETERS', 0.5)):
        _units(unit, 0.01)
        meta = _metarig()
        meta.scale = (100.0, 100.0, 100.0)
        bpy.context.view_layer.update()
        h_m = _height(meta) * scene.unit_settings.scale_length
        assert 1.5 < h_m < 2.5, ("fits a 2 m character", unit, h_m)
        batch, single = _drawn_radii(meta)
        want = want_cm / 100.0 / scene.unit_settings.scale_length        # Blender units
        assert batch == single == {round(want, 6)}, (unit, batch, single, want)
        drawn, bones = _drawn_extent(meta)
        assert drawn < 1.1 * bones, ("the joints stay inside the character", unit, drawn, bones)
    scene.unit_settings.scale_length = 1.0


def test_scaled_parent_scales_the_joints():
    scene = bpy.context.scene
    scene.property_unset("allset_joint_size")
    _units('CENTIMETERS')
    meta = _metarig()
    group = bpy.data.objects.new("group", None)
    scene.collection.objects.link(group)
    meta.parent = group
    group.scale = (3.0, 3.0, 3.0)
    meta.scale = (2.0, 2.0, 2.0)            # its own scale: no change
    batch, single = _drawn_radii(meta)
    assert batch == single == {round(3 * 0.005, 6)}, (batch, single)
    bpy.data.objects.remove(group)


def test_joint_tool_click_sphere_ignores_the_armature_scale():
    scene = bpy.context.scene
    scene.property_unset("allset_joint_size")
    _units('CENTIMETERS')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    assert bpy.ops.allset.joint_tool('EXEC_DEFAULT', points="[[0, 0, 0], [0, 0, 1], [0, 0, 2]]") == {'FINISHED'}
    arm = bpy.context.object
    bone = arm.data.bones[0]
    before = joint_tool.joint_sphere_radius(arm, bone)
    assert before > 0.0
    arm.scale = (50.0, 50.0, 50.0)
    bpy.context.view_layer.update()
    assert abs(joint_tool.joint_sphere_radius(arm, bone) - before) < 1e-9
    assert abs(jd.skeleton_scale(arm) - 1.0) < 1e-9


def test_generated_rig_and_stick_display():
    scene = bpy.context.scene
    _units('METERS')
    scene.property_unset("allset_joint_size")
    meta = _metarig()
    bpy.ops.pose.rigify_generate()
    rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE' and o is not meta)
    radii = {round(shapes.drawn_radius(b, scene), 6) for b in rig.data.bones if not rig.pose.bones[b.name].custom_shape}
    assert radii and max(radii) <= 0.05 + 1e-9, radii
    # Stick / Wire draw thin lines (no Maya joint spheres); B-Bone / Envelope Blender's shapes as wire
    assert {'STICK', 'WIRE'} <= set(mj.STICK_TYPES) and {'BBONE', 'ENVELOPE'} <= set(mj.SHAPE_TYPES)
    assert 'OCTAHEDRAL' not in set(mj.STICK_TYPES) | set(mj.SHAPE_TYPES), "Octahedral (new skeletons) = Maya joints"
