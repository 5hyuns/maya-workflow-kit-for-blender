"""#481: the Channel Box SHAPES rows of a camera, a light and a locator are Maya's shape channels in Maya's order with
Maya's names: camera Horizontal / Vertical Film Aperture (inches), Focal Length, Lens Squeeze Ratio, F Stop, Focus
Distance, Shutter Angle, Center Of Interest, Locator Scale (no clip planes); point / directional / spot lights Color
R / G / B, the intensity row, Use Ray Trace Shadows, Shad Color R / G / B, Use Depth Map Shadows, Dmap Bias (spot: Cone
Angle, Penumbra Angle, Dropoff); a locator's locatorShape1 Local Position X / Y / Z and Local Scale X / Y / Z."""

from importlib import import_module

import bpy

import kit

cb = import_module(kit.MODULE + ".ui.channel_box")
cb_inputs = import_module(kit.MODULE + ".ui.cb_inputs")

CAMERA_ROWS = ["Horizontal Film Aperture", "Vertical Film Aperture", "Focal Length", "Lens Squeeze Ratio", "F Stop",
               "Focus Distance", "Shutter Angle", "Center Of Interest", "Locator Scale"]
SHADOW_ROWS = ["Use Ray Trace Shadows", "Shad Color R", "Shad Color G", "Shad Color B", "Use Depth Map Shadows",
               "Dmap Bias"]
LOCATOR_ROWS = ["Local Position X", "Local Position Y", "Local Position Z", "Local Scale X", "Local Scale Y",
                "Local Scale Z"]


def _new(kind):
    bpy.ops.wm.read_homefile(use_empty=True)
    assert bpy.ops.allset.create(kind=kind) == {'FINISHED'}
    cb.set_selected_channels([])
    return bpy.context.active_object


def _shape_keys(ob):
    return {cb.channel_label(k): k for k in cb.drawn_keys(ob) if k.startswith("sh:")}


def _shape_labels(ob):
    return [cb.channel_label(k) for k in cb.drawn_keys(ob) if k.startswith("sh:")]


def _close(a, b, eps=1e-6):
    return abs(a - b) < eps


def test_camera_shape_rows():
    ob = _new('CAMERA')
    labels = _shape_labels(ob)
    assert labels == CAMERA_ROWS, labels


def test_camera_shape_values_and_typing():
    ob = _new('CAMERA')
    cam = ob.data
    get = _shape_keys(ob)
    assert _close(cb.get_value(ob, get["Horizontal Film Aperture"]), 36.0 / 25.4)
    assert _close(cb.get_value(ob, get["F Stop"]), cam.dof.aperture_fstop)
    cb.set_value(ob, get["Vertical Film Aperture"], 1.0)
    assert abs(cam.sensor_height - 25.4) < 1e-4
    cb.set_value(ob, get["F Stop"], 8.0)
    assert _close(cam.dof.aperture_fstop, 8.0)


def test_camera_kept_rows():
    """Lens Squeeze Ratio 1, Shutter Angle 144 and Center Of Interest 5 on a new camera, typed values kept."""
    ob = _new('CAMERA')
    get = _shape_keys(ob)
    for label, start, typed in (("Lens Squeeze Ratio", 1.0, 2.0), ("Shutter Angle", 144.0, 180.0),
                                ("Center Of Interest", 5.0, 12.5)):
        assert _close(cb.get_value(ob, get[label]), start), (label, cb.get_value(ob, get[label]))
        cb.set_value(ob, get[label], typed)
        assert _close(cb.get_value(ob, get[label]), typed), label
    assert _close(ob.data.allset_shutter_angle, 180.0)


def test_camera_shape_rows_key():
    ob = _new('CAMERA')
    get = _shape_keys(ob)
    cb.set_selected_channels([get["Horizontal Film Aperture"], get["F Stop"], get["Shutter Angle"]])
    bpy.context.scene.frame_set(1)
    assert bpy.ops.allset.cb_key_selected() == {'FINISHED'}
    paths = sorted(f.data_path for f in kit.fcurves(ob.data))
    assert paths == ["allset_shutter_angle", "dof.aperture_fstop", "sensor_width"], paths


def test_light_shape_rows():
    for kind in ('POINT_LIGHT', 'DIRECTIONAL_LIGHT', 'SPOT_LIGHT'):
        ob = _new(kind)
        labels = _shape_labels(ob)
        power = "Strength" if kind == 'DIRECTIONAL_LIGHT' else "Power"      # Blender's, where Maya has Intensity
        want = ["Color R", "Color G", "Color B", power] + SHADOW_ROWS
        if kind == 'SPOT_LIGHT':
            want += ["Cone Angle", "Penumbra Angle", "Dropoff"]
        assert labels == want, (kind, labels)


def test_light_shadow_row():
    for kind in ('POINT_LIGHT', 'DIRECTIONAL_LIGHT', 'SPOT_LIGHT'):
        ob = _new(kind)
        key = _shape_keys(ob)["Use Ray Trace Shadows"]
        cb.set_value(ob, key, False)
        assert ob.data.use_shadow is False, kind


def test_light_kept_rows():
    """Shad Color 0 / 0 / 0, Use Depth Map Shadows off, Dmap Bias 0.001, Dropoff 0 on a new light; typed values kept
    and Shad Color keys its own colour channel."""
    ob = _new('SPOT_LIGHT')
    get = _shape_keys(ob)
    for label, start in (("Shad Color R", 0.0), ("Shad Color G", 0.0), ("Shad Color B", 0.0),
                         ("Use Depth Map Shadows", False), ("Dmap Bias", 0.001), ("Dropoff", 0.0)):
        v = cb.get_value(ob, get[label])
        assert _close(float(v), float(start)), (label, v)
    cb.set_value(ob, get["Shad Color G"], 0.5)
    cb.set_value(ob, get["Use Depth Map Shadows"], True)
    cb.set_value(ob, get["Dmap Bias"], 0.01)
    cb.set_value(ob, get["Dropoff"], 3.0)
    light = ob.data
    assert _close(light.allset_shadow_color[1], 0.5) and _close(light.allset_shadow_color[0], 0.0)
    assert light.allset_use_depth_map_shadows is True
    assert _close(light.allset_dmap_bias, 0.01) and _close(light.allset_dropoff, 3.0)
    cb.set_selected_channels([get["Shad Color G"]])
    bpy.context.scene.frame_set(1)
    assert bpy.ops.allset.cb_key_selected() == {'FINISHED'}
    curves = sorted((f.data_path, f.array_index) for f in kit.fcurves(light))
    assert curves == [("allset_shadow_color", 1)], curves


def test_area_light_rows():
    """An area light has the point light's rows: Color R / G / B, the intensity row and the shadow rows."""
    ob = _new('AREA_LIGHT')
    labels = _shape_labels(ob)
    assert labels == ["Color R", "Color G", "Color B", "Power"] + SHADOW_ROWS, labels
    get = _shape_keys(ob)
    cb.set_value(ob, get["Shad Color B"], 0.25)
    assert _close(ob.data.allset_shadow_color[2], 0.25)


def test_value_limits():
    """Dmap Bias takes a negative value; Lens Squeeze Ratio and Center Of Interest stay above 0."""
    ob = _new('POINT_LIGHT')
    get = _shape_keys(ob)
    cb.set_value(ob, get["Dmap Bias"], -0.5)
    assert _close(ob.data.allset_dmap_bias, -0.5), ob.data.allset_dmap_bias
    cam = _new('CAMERA')
    get = _shape_keys(cam)
    for label, prop in (("Lens Squeeze Ratio", "allset_lens_squeeze_ratio"),
                        ("Center Of Interest", "allset_center_of_interest")):
        cb.set_value(cam, get[label], -2.0)
        v = getattr(cam.data, prop)
        assert 0.0 < v < 1e-6, (label, v)


def test_locator_shape_rows():
    ob = _new('LOCATOR')
    assert cb_inputs.shape_data(ob) is ob
    labels = _shape_labels(ob)
    assert labels == LOCATOR_ROWS, labels
    get = _shape_keys(ob)
    for label in LOCATOR_ROWS:
        want = 1.0 if "Scale" in label else 0.0
        assert _close(cb.get_value(ob, get[label]), want), (label, cb.get_value(ob, get[label]))


def test_locator_local_position_and_scale():
    ob = _new('LOCATOR')
    get = _shape_keys(ob)
    size = ob.empty_display_size
    cb.set_value(ob, get["Local Position Y"], 2.0)
    assert _close(ob.delta_location[1], 2.0) and _close(ob.location[1], 0.0)
    cb.set_value(ob, get["Local Scale X"], 3.0)
    assert _close(cb.get_value(ob, get["Local Scale X"]), 3.0)
    assert _close(cb.get_value(ob, get["Local Scale Y"]), 1.0)
    assert _close(ob.empty_display_size, size * 3.0, 1e-5), ob.empty_display_size
    cb.set_value(ob, get["Local Scale X"], 0.0)
    cb.set_value(ob, get["Local Scale X"], 1.0)
    assert _close(ob.empty_display_size, size, 1e-5), ob.empty_display_size
    assert tuple(ob.scale) == (1.0, 1.0, 1.0)


def test_plain_empty_has_no_shapes():
    bpy.ops.wm.read_homefile(use_empty=True)
    bpy.ops.object.empty_add()
    ob = bpy.context.active_object
    assert cb_inputs.shape_data(ob) is None
    assert _shape_labels(ob) == []
