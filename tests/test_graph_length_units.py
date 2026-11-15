"""Graph Editor value axis in the scene's length unit: Blender 5.3 draws length curves in the scene's length unit (Unit
Scale included), 5.2 draws them as stored. The kit's key, tangent and curve drawing, its key tools and its framing
map values the same way Blender draws them (compat.graph_length_factor), and the kit's own value relabel is left out
where Blender already shows lengths in the scene's unit."""

import math
from importlib import import_module

import bpy
import kit

compat = import_module(kit.MODULE + ".compat")
graph_units = import_module(kit.MODULE + ".ui.graph_units")
graph_layers = import_module(kit.MODULE + ".ui.graph_layers")
graph_move = import_module(kit.MODULE + ".operators.graph_move")

# (system, length unit, unit scale) -> display value per stored value of a length curve where Blender draws lengths
# in the scene's unit
CASES = ((("METRIC", "CENTIMETERS", 1.0), 100.0), (("METRIC", "MILLIMETERS", 1.0), 1000.0),
         (("METRIC", "METERS", 1.0), 1.0), (("METRIC", "ADAPTIVE", 1.0), 1.0),
         (("METRIC", "CENTIMETERS", 2.0), 200.0), (("METRIC", "ADAPTIVE", 2.0), 2.0),
         (("IMPERIAL", "INCHES", 1.0), 1 / 0.0254), (("IMPERIAL", "ADAPTIVE", 1.0), 1 / 0.3048),
         (("NONE", None, 1.0), 1.0), (("NONE", None, 2.0), 1.0))


def _units(system, length, scale):
    us = bpy.context.scene.unit_settings
    us.system = system
    if length is not None:
        us.length_unit = length
    us.scale_length = scale
    return us


def _keyed():
    ob = bpy.data.objects.new("glu", None)
    bpy.context.scene.collection.objects.link(ob)
    for f, v in ((1, 0.0), (10, 0.05)):
        ob.location.x = v
        ob.rotation_euler.x = v
        ob.scale.x = 1.0 + v
        for path in ("location", "rotation_euler", "scale"):
            ob.keyframe_insert(path, index=0, frame=f)
    fcs = {fc.data_path: fc for fc in compat.id_fcurves(ob) if fc.array_index == 0}
    return ob, fcs


def test_length_factor_follows_the_scene_units():
    us = bpy.context.scene.unit_settings
    old = (us.system, us.length_unit, us.scale_length)
    try:
        for (system, length, scale), want in CASES:
            got = compat.graph_length_factor(_units(system, length, scale))
            expect = want if compat.GRAPH_LENGTH_UNITS else 1.0
            assert abs(got - expect) < 1e-6 * max(1.0, expect), ((system, length, scale), got, expect)
    finally:
        _units(old[0], old[1], old[2])


def test_curve_mapping_uses_the_length_factor():
    us = bpy.context.scene.unit_settings
    old = (us.system, us.length_unit, us.scale_length, us.system_rotation)
    ob, fcs = _keyed()
    try:
        _units("METRIC", "CENTIMETERS", 1.0)
        us.system_rotation = 'DEGREES'
        length = 100.0 if compat.GRAPH_LENGTH_UNITS else 1.0
        assert graph_units.curve_unit(fcs["location"]) == 'LENGTH'
        assert graph_units.curve_unit(fcs["rotation_euler"]) == 'ROTATION'
        # drawing: display = stored x factor
        assert abs(graph_layers.value_factor(bpy.context.scene, fcs["location"]) - length) < 1e-9
        assert abs(graph_layers.value_factor(bpy.context.scene, fcs["rotation_euler"]) - 180.0 / math.pi) < 1e-9
        assert graph_layers.value_factor(bpy.context.scene, fcs["scale"]) == 1.0
        # key tools: stored value per display value
        scales = graph_move._value_scales(bpy.context, [fcs["location"], fcs["rotation_euler"], fcs["scale"]])
        assert abs(scales[0] - 1.0 / length) < 1e-12, scales
        assert abs(scales[1] - math.pi / 180.0) < 1e-12, scales
        assert scales[2] == 1.0, scales
        # metres: lengths are drawn as stored on every version
        _units("METRIC", "METERS", 1.0)
        assert graph_layers.value_factor(bpy.context.scene, fcs["location"]) == 1.0
        assert graph_move._value_scales(bpy.context, [fcs["location"]])[0] == 1.0
    finally:
        bpy.data.objects.remove(ob)
        _units(old[0], old[1], old[2])
        us.system_rotation = old[3]
