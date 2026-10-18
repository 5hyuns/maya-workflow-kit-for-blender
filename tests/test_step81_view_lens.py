"""Step 81: the MayaKit persp view has Maya's field of view — Blender viewport lens 70 (72 mm sensor) = Maya persp
35 mm on a 36 mm film back; Create > Camera is Maya's 35 mm camera; Camera from View keeps the angle.
Plan: docs/steps/step_81.md."""

import importlib.util
import math
from importlib import import_module
from pathlib import Path

import bpy

import kit

ROOT = Path(__file__).resolve().parent.parent
create = import_module(kit.MODULE + ".operators.create")
key_batch = import_module(kit.MODULE + ".operators.key_batch")


def _tool(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tools" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_template_lens_is_mayas_angle():
    startup = _tool("make_startup")
    look = _tool("look_data")
    # Maya: f_px = (width / 2) / (film / 2 / focal); Blender viewport: f_px = width * lens / 72 (step 41)
    width = 1000.0
    maya = (width / 2) / (look.MAYA_APERTURE_MM / 2 / look.MAYA_FOCAL_MM)
    kit_f = width * startup.MAYA_LENS / key_batch.VIEW_SENSOR
    assert abs(maya - kit_f) < 1e-6, (maya, kit_f)
    fov = math.degrees(2 * math.atan(key_batch.VIEW_SENSOR / 2 / startup.MAYA_LENS))
    assert abs(fov - 54.43) < 0.05, fov


def test_create_camera_is_mayas_35mm():
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    cam = create.create(bpy.context, 'CAMERA')
    assert (cam.data.lens, cam.data.sensor_width) == (35.0, 36.0)


def test_camera_from_view_lens_rule():
    # the camera keeps the view's angle: view lens 70 on the 72 mm viewport sensor = 35 mm on 36 mm
    assert 70.0 * create.MAYA_FILM_MM / key_batch.VIEW_SENSOR == 35.0
