"""#479: a camera from Create > Cameras (and the camera command) starts not renderable with the same Gate Mask
Opacity as a new Maya camera; a new directional light starts with Light Angle 0. The startup persp stays
renderable."""

from importlib import import_module

import bpy

import kit

create = import_module(kit.MODULE + ".operators.create")
render_cameras = import_module(kit.MODULE + ".operators.render_cameras")
cmds = import_module(kit.MODULE + ".command_line.cmds_shim")


def _new(kind):
    bpy.ops.wm.read_homefile(use_empty=True)
    assert bpy.ops.allset.create(kind=kind) == {'FINISHED'}
    return bpy.context.active_object


def test_create_camera_not_renderable():
    for kind in ('CAMERA', 'CAMERA_AIM', 'CAMERA_AIM_UP'):
        ob = _new(kind)
        cam = ob if ob.type == 'CAMERA' else next(o for o in bpy.data.objects if o.type == 'CAMERA')
        assert cam.data.allset_renderable is False, kind
        assert not render_cameras.is_renderable(cam), kind
        assert abs(cam.data.passepartout_alpha - create.MAYA_GATE_MASK_OPACITY) < 1e-6, kind


def test_camera_command_not_renderable():
    bpy.ops.wm.read_homefile(use_empty=True)
    name = cmds.camera()[0]
    assert bpy.data.objects[name].data.allset_renderable is False


def test_renderable_can_be_turned_on():
    ob = _new('CAMERA')
    ob.data.allset_renderable = True
    assert render_cameras.is_renderable(ob)


def test_camera_made_outside_the_kit_stays_renderable():
    bpy.ops.wm.read_homefile(use_empty=True)
    bpy.ops.object.camera_add()
    assert bpy.context.active_object.data.allset_renderable is True


def test_directional_light_angle_zero():
    ob = _new('DIRECTIONAL_LIGHT')
    assert ob.data.type == 'SUN' and ob.data.angle == 0.0
