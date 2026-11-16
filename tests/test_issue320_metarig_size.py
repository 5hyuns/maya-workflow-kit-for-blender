"""Issue #320: the joints of a Rigify human metarig and of its generated rig draw at a normal size in Maya mode, in a
metre scene and in a centimetre scene: a Radius 1 joint (a new joint's Radius) is 10 cm across in a metre scene
(Joint Size in Metre Scenes 10) and 1 cm in a centimetre scene, so on a 2 m character the joints stay small, and
scaling the armature object scales them with it. Stick / Wire skeletons draw lines (no spheres)."""

from importlib import import_module

import addon_utils
import bpy

import kit

mj = import_module(kit.MODULE + ".ui.maya_joints")
shapes = import_module(kit.MODULE + ".ui.maya_joints_shapes")


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


def test_metarig_joints_are_small_in_a_metre_scene():
    scene = bpy.context.scene
    us = scene.unit_settings
    scene.property_unset("allset_joint_size")
    for unit, want in (('METERS', 0.05), ('CENTIMETERS', 0.005)):
        us.system, us.length_unit, us.scale_length = 'METRIC', unit, 1.0
        meta = _metarig()
        h = _height(meta)
        assert 1.5 < h < 2.5, ("a human-sized metarig", h)
        radii = {round(shapes.drawn_radius(b, scene), 6) for b in meta.data.bones}
        assert radii == {want}, (unit, radii)
        assert 2 * want / h < 0.06, ("a joint is a small part of the character", unit, 2 * want / h)
        meta.scale = (5.0, 5.0, 5.0)        # a 10 m character: the joints scale with the armature object
        bpy.context.view_layer.update()
        b = meta.data.bones[0]
        got = shapes.drawn_radius(b, scene, max(meta.matrix_world.to_scale()))
        assert abs(got - 5 * want) < 1e-6, (unit, got)


def test_generated_rig_and_stick_display():
    scene = bpy.context.scene
    us = scene.unit_settings
    us.system, us.length_unit, us.scale_length = 'METRIC', 'METERS', 1.0
    scene.property_unset("allset_joint_size")
    meta = _metarig()
    bpy.ops.pose.rigify_generate()
    rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE' and o is not meta)
    radii = {round(shapes.drawn_radius(b, scene), 6) for b in rig.data.bones if not rig.pose.bones[b.name].custom_shape}
    assert radii and max(radii) <= 0.05 + 1e-9, radii
    # Stick / Wire draw thin lines (no Maya joint spheres); B-Bone / Envelope Blender's shapes as wire
    assert {'STICK', 'WIRE'} <= set(mj.STICK_TYPES) and {'BBONE', 'ENVELOPE'} <= set(mj.SHAPE_TYPES)
    assert 'OCTAHEDRAL' not in set(mj.STICK_TYPES) | set(mj.SHAPE_TYPES), "Octahedral (new skeletons) = Maya joints"
