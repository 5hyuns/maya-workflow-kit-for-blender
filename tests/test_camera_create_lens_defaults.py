"""Create > Cameras > Camera starts with F Stop 5.6, Focus Distance 5 and Orthographic Width 30 (Maya units), like
Maya's camera; the camera command keeps its own Orthographic Width 10."""

from importlib import import_module

import bpy

import kit

create = import_module(kit.MODULE + ".operators.create")
units = import_module(kit.MODULE + ".operators.units")


def _reset():
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)


def test_create_camera_lens_and_ortho_values():
    _reset()
    cam = create.create(bpy.context, 'CAMERA')
    k = units.maya_unit()
    assert abs(cam.data.dof.aperture_fstop - 5.6) < 1e-5, cam.data.dof.aperture_fstop
    assert abs(cam.data.dof.focus_distance / k - 5.0) < 1e-5, cam.data.dof.focus_distance
    assert abs(cam.data.ortho_scale / k - 30.0) < 1e-5, cam.data.ortho_scale
    assert not cam.data.dof.use_dof


def test_create_camera_scales_with_the_maya_unit():
    _reset()
    scene = bpy.context.scene
    old = scene.unit_settings.scale_length, scene.unit_settings.length_unit
    scene.unit_settings.length_unit = 'CENTIMETERS'
    scene.unit_settings.scale_length = 0.01
    try:
        k = units.maya_unit()
        cam = create.create(bpy.context, 'CAMERA')
        assert abs(cam.data.ortho_scale - 30.0 * k) < 1e-6 * max(1.0, k), (cam.data.ortho_scale, k)
        assert abs(cam.data.dof.focus_distance - 5.0 * k) < 1e-6 * max(1.0, k), (cam.data.dof.focus_distance, k)
    finally:
        scene.unit_settings.scale_length, scene.unit_settings.length_unit = old


def test_camera_command_keeps_its_ortho_width():
    _reset()
    cmds = import_module(kit.MODULE + ".command_line.cmds_shim")
    name = cmds.camera()[0]
    ob = bpy.data.objects[name]
    k = units.maya_unit()
    assert abs(ob.data.ortho_scale / k - 10.0) < 1e-5, ob.data.ortho_scale
    assert abs(ob.data.dof.aperture_fstop - 5.6) < 1e-5
