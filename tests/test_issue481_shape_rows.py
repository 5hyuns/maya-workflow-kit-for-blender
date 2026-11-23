"""#481: the Channel Box SHAPES rows of a camera and a light are the Maya shape channels that Blender has a setting
for (Maya names), not Blender-named rows: camera Horizontal / Vertical Film Aperture (inches), Focal Length,
F Stop, Focus Distance, Locator Scale (no clip planes); lights also Use Ray Trace Shadows."""

from importlib import import_module

import bpy

import kit

cb = import_module(kit.MODULE + ".ui.channel_box")


def _new(kind):
    bpy.ops.wm.read_homefile(use_empty=True)
    assert bpy.ops.allset.create(kind=kind) == {'FINISHED'}
    cb.set_selected_channels([])
    return bpy.context.active_object


def _shape_labels(ob):
    return [cb.channel_label(k) for k in cb.drawn_keys(ob) if k.startswith("sh:")]


def test_camera_shape_rows():
    ob = _new('CAMERA')
    labels = _shape_labels(ob)
    assert labels == ["Horizontal Film Aperture", "Vertical Film Aperture", "Focal Length", "F Stop",
                      "Focus Distance", "Locator Scale"], labels


def test_camera_shape_values_and_typing():
    ob = _new('CAMERA')
    cam = ob.data
    get = {cb.channel_label(k): k for k in cb.drawn_keys(ob) if k.startswith("sh:")}
    assert abs(cb.get_value(ob, get["Horizontal Film Aperture"]) - 36.0 / 25.4) < 1e-6
    assert abs(cb.get_value(ob, get["F Stop"]) - cam.dof.aperture_fstop) < 1e-6
    cb.set_value(ob, get["Vertical Film Aperture"], 1.0)
    assert abs(cam.sensor_height - 25.4) < 1e-4
    cb.set_value(ob, get["F Stop"], 8.0)
    assert abs(cam.dof.aperture_fstop - 8.0) < 1e-6


def test_camera_shape_rows_key():
    ob = _new('CAMERA')
    get = {cb.channel_label(k): k for k in cb.drawn_keys(ob) if k.startswith("sh:")}
    cb.set_selected_channels([get["Horizontal Film Aperture"], get["F Stop"]])
    bpy.context.scene.frame_set(1)
    assert bpy.ops.allset.cb_key_selected() == {'FINISHED'}
    paths = sorted(f.data_path for f in kit.fcurves(ob.data))
    assert paths == ["dof.aperture_fstop", "sensor_width"], paths


def test_light_shadow_row():
    for kind in ('POINT_LIGHT', 'DIRECTIONAL_LIGHT', 'SPOT_LIGHT'):
        ob = _new(kind)
        labels = _shape_labels(ob)
        power = "Strength" if kind == 'DIRECTIONAL_LIGHT' else "Power"      # Blender's, where Maya has Intensity
        assert labels[:4] == ["Color R", "Color G", "Color B", power], (kind, labels)
        assert "Use Ray Trace Shadows" in labels, (kind, labels)
        key = next(k for k in cb.drawn_keys(ob) if cb.channel_label(k) == "Use Ray Trace Shadows")
        cb.set_value(ob, key, False)
        assert ob.data.use_shadow is False, kind
