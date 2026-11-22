"""#482: the Attribute Editor camera tab shows Horizontal / Vertical Film Aperture in inches, like Maya; typing a
value there sets Blender's sensor size (millimetres) to match."""

from importlib import import_module

import bpy

import kit

ae_layout = import_module(kit.MODULE + ".ui.ae_layout")


def _rows():
    out = {}
    for section in ae_layout.CAMERA:
        for row in section.rows:
            if row[0] == "prop":
                out[row[3]] = row[2]
    return out


def _camera():
    bpy.ops.wm.read_homefile(use_empty=True)
    assert bpy.ops.allset.create(kind='CAMERA') == {'FINISHED'}
    return bpy.context.active_object.data


def test_rows_use_inches():
    rows = _rows()
    assert rows["Horizontal Film Aperture"] == "allset_film_aperture_h", rows
    assert rows["Vertical Film Aperture"] == "allset_film_aperture_v", rows


def test_new_camera_aperture_in_inches():
    cam = _camera()
    assert abs(cam.allset_film_aperture_h - 36.0 / 25.4) < 1e-6
    assert abs(cam.allset_film_aperture_v - 24.0 / 25.4) < 1e-6


def test_typed_inches_set_sensor_mm():
    cam = _camera()
    cam.allset_film_aperture_h = 1.0
    cam.allset_film_aperture_v = 0.5
    assert abs(cam.sensor_width - 25.4) < 1e-4 and abs(cam.sensor_height - 12.7) < 1e-4
    cam.sensor_width = 50.8
    assert abs(cam.allset_film_aperture_h - 2.0) < 1e-6
