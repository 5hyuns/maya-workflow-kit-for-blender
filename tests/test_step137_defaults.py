"""Material, light and Render Settings defaults.

New materials are plain Principled BSDF materials (Blender's values); the Attribute Editor's Eccentricity /
Cosine Power rows read and write the Roughness as Maya's numbers. Lights: intensity 1, Decay Rate No Decay;
resolution 960 x 540. Light power rule and its renders: operators/lights.py."""

import math
from importlib import import_module

import bpy

import kit

material = import_module(kit.MODULE + ".operators.material")
create = import_module(kit.MODULE + ".operators.create")
lights = import_module(kit.MODULE + ".operators.lights")
ae_layout = import_module(kit.MODULE + ".ui.ae_layout")
attribute_editor = import_module(kit.MODULE + ".ui.attribute_editor")
app_template = import_module(kit.MODULE + ".app_template")
compat = import_module(kit.MODULE + ".compat")

PI2 = math.pi ** 2


def _clear():
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for coll in (bpy.data.meshes, bpy.data.lights, bpy.data.materials):
        for d in list(coll):
            coll.remove(d)


def _cm():
    us = bpy.context.scene.unit_settings
    us.system, us.length_unit, us.scale_length = 'METRIC', 'CENTIMETERS', 1.0
    return 0.01


def _bsdf(mat):
    return next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')


def _close(a, b, eps=1e-4):
    if isinstance(a, (int, float)):
        return abs(a - b) < eps
    return all(abs(x - y) < eps for x, y in zip(a, b))


def _rows(name):
    return [row for _d, sec in ae_layout.walk(ae_layout.BY_KIND[name][0]) for row in sec.rows]


# --- materials -----------------------------------------------------------------------------------------------------

def _blender_bsdf():
    ref = bpy.data.materials.new("blender_ref")
    ref.use_nodes = True
    return _bsdf(ref)


def test_blinn_eccentricity_reads_roughness():
    _clear()
    mat = material.new_material('BLINN')
    b, ref = _bsdf(mat), _blender_bsdf()
    for name in ("Base Color", "Emission Color", "Specular IOR Level", "Specular Tint", "Roughness"):
        got, want = b.inputs[name].default_value, ref.inputs[name].default_value
        if hasattr(got, "__len__"):
            got, want = tuple(got), tuple(want)
        assert _close(got, want), (name, "a plain Principled BSDF")
    # the AE Eccentricity row shows the Roughness as Maya's number (GGX alpha = eccentricity)
    assert _close(mat.allset_eccentricity, b.inputs["Roughness"].default_value ** 2), mat.allset_eccentricity
    mat.allset_eccentricity = 0.6
    assert _close(b.inputs["Roughness"].default_value, math.sqrt(0.6)) and _close(mat.allset_eccentricity, 0.6)
    rows = _rows("blinn")
    assert ("maya", "allset_eccentricity", "Eccentricity", "Roughness") in rows
    assert ("socket", "Specular IOR Level", "Specular Roll Off") in rows
    assert ("socket", "Emission Color", "Incandescence") in rows
    assert ("socket", "Specular Tint", "Specular Color") in rows


def test_phong_cosine_power_reads_roughness():
    _clear()
    mat = material.new_material('PHONG')
    b = _bsdf(mat)
    assert _close(b.inputs["Roughness"].default_value, _blender_bsdf().inputs["Roughness"].default_value)
    r = b.inputs["Roughness"].default_value
    assert _close(mat.allset_cosine_power, 2.0 / r ** 4 - 2.0, 1e-3), mat.allset_cosine_power
    mat.allset_cosine_power = 50.0
    assert _close(mat.allset_cosine_power, 50.0, 1e-2), mat.allset_cosine_power
    assert _close(b.inputs["Roughness"].default_value, (2 / 52) ** 0.25)
    assert ("maya", "allset_cosine_power", "Cosine Power", "Roughness") in _rows("phong")
    # Blinn eccentricity 0.3 and Phong cosine power 20 give about the same highlight: both near 0.55 here
    assert abs(material.eccentricity_roughness(0.3) - material.cosine_power_roughness(20.0)) < 0.01


def test_other_kinds_keep_blender_values():
    _clear()
    ref = _blender_bsdf()
    for kind in ('LAMBERT', 'PHONG_E', 'ANISOTROPIC', 'STANDARD_SURFACE', 'AI_STANDARD_SURFACE'):
        b = _bsdf(material.new_material(kind))
        for name in ("Base Color", "Roughness", "Specular IOR Level", "Specular Tint", "Anisotropic",
                     "Coat Roughness", "Emission Color"):
            got, want = b.inputs[name].default_value, ref.inputs[name].default_value
            if hasattr(got, "__len__"):
                got, want = tuple(got), tuple(want)
            assert _close(got, want), (kind, name, got, want)
    # Ramp / Layered: no glow colour in their Incandescence rows
    for kind in ('RAMP', 'LAYERED'):
        b = _bsdf(material.new_material(kind))
        assert _close(b.inputs["Emission Color"].default_value, (0, 0, 0, 1)), kind


def test_ae_draws_maya_numbers():
    """The AE row draws the Material property (Maya's number), not the Roughness socket."""
    _clear()
    mat = material.new_material('BLINN')
    calls = []

    class Rec:
        def row(self, **_kw):
            return self

        def prop(self, owner, attr, text=""):
            calls.append((owner, attr, text))

        def operator(self, *_a, **_kw):
            class P:
                pass
            return P()

        def label(self, text=""):
            calls.append((None, None, text))

    attribute_editor.draw_row(Rec(), bpy.context, None, mat, ("maya", "allset_eccentricity", "Eccentricity",
                                                                 "Roughness"))
    assert calls == [(mat, "allset_eccentricity", "Eccentricity")], calls


# --- lights --------------------------------------------------------------------------------------------------------

def _falloff(light):
    tree = light.node_tree
    node = tree.nodes.get(lights.FALLOFF_NODE) if tree is not None else None
    if node is None:
        return None, None
    em = next(n for n in tree.nodes if n.type == 'EMISSION')
    link = em.inputs["Strength"].links[0] if em.inputs["Strength"].is_linked else None
    return (link.from_socket.name if link else None), node.inputs["Strength"].default_value


def test_new_point_spot_lights_no_decay():
    _clear()
    k = _cm()
    for kind in ('POINT_LIGHT', 'SPOT_LIGHT'):
        ob = create.create(bpy.context, kind)
        light = ob.data
        assert light.allset_decay == 'NO_DECAY' and _close(light.allset_intensity, 1.0), (kind, light.allset_decay)
        assert _close(light.energy, 4 * PI2 * 100 * k * k, 1e-6), light.energy
        out, strength = _falloff(light)
        assert out == "Constant" and _close(strength, 1 / (10 * k) ** 2, 1e-3), (out, strength)
    spot = bpy.data.objects["spotLight1"].data
    assert _close(math.degrees(spot.spot_size), 40.0) and spot.spot_blend == 0.0, "Maya cone 40, penumbra 0"


def test_decay_rate_changes_keep_intensity():
    _clear()
    k = _cm()
    light = create.create(bpy.context, 'POINT_LIGHT').data
    light.allset_intensity = 2.0
    light.allset_decay = 'LINEAR'
    assert _close(light.allset_intensity, 2.0) and _close(light.energy, 2 * 4 * PI2 * 10 * k * k, 1e-6)
    out, strength = _falloff(light)
    assert out == "Linear" and _close(strength, 1 / (10 * k)), (out, strength)
    light.allset_decay = 'QUADRATIC'
    assert _falloff(light) == (None, None), "Blender's own law: no falloff node"
    assert _close(light.energy, 2 * 4 * PI2 * k * k, 1e-8) and _close(light.allset_intensity, 2.0)
    if not compat.LIGHT_ALWAYS_NODES:
        assert not light.use_nodes, "nodes the kit turned on are turned off again"
    assert lights.exact(light)
    light.allset_decay = 'CUBIC'
    assert not lights.exact(light) and "cubic" in lights.decay_notice(light)
    light.allset_decay = 'NO_DECAY'
    assert _falloff(light)[0] == "Constant" and _close(light.allset_intensity, 2.0)


def test_area_and_directional_lights():
    _clear()
    k = _cm()
    area = create.create(bpy.context, 'AREA_LIGHT').data
    assert area.allset_decay == 'NO_DECAY' and _close(area.size, 2 * k), "Maya area light 2 x 2 units"
    assert _close(area.energy, PI2 * lights.AREA_FAR * k * k, 1e-8) and _falloff(area) == (None, None)
    area.allset_decay = 'LINEAR'
    assert not lights.exact(area) and _close(area.allset_intensity, 1.0)
    sun = create.create(bpy.context, 'DIRECTIONAL_LIGHT').data
    assert _close(sun.energy, math.pi) and _close(sun.allset_intensity, 1.0)
    # a light made in Blender reads with Blender's own law
    plain = bpy.data.lights.new("plain", 'POINT')
    plain.energy = 10.0
    assert plain.allset_decay == 'QUADRATIC' and _close(plain.allset_intensity, 10.0 / (4 * PI2 * k * k), 1e-3)


def test_ae_light_rows():
    for name in ("POINT", "SPOT", "AREA"):
        rows = _rows(name)
        assert ("prop", "data", "allset_intensity", "Intensity") in rows and ("draw", "light_decay") in rows, name
    assert "light_decay" in attribute_editor.DRAWERS


# --- Render Settings -----------------------------------------------------------------------------------------------

def test_template_resolution_960_540():
    with bpy.data.libraries.load(app_template.STARTUP) as (src, dst):
        dst.scenes = list(src.scenes)
    try:
        for sc in dst.scenes:
            r = sc.render
            assert (r.resolution_x, r.resolution_y, r.resolution_percentage) == (960, 540, 100), \
                (sc.name, r.resolution_x, r.resolution_y, r.resolution_percentage)
            assert (r.pixel_aspect_x, r.pixel_aspect_y) == (1.0, 1.0)
    finally:
        for sc in dst.scenes:
            bpy.data.scenes.remove(sc)
