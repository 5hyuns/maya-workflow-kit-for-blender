"""Material, light and Render Settings defaults.

New materials are plain Principled BSDF materials (Blender's values); the Attribute Editor shows their inputs by
Blender's names. Lights: intensity 1, Decay Rate No Decay;
cone, penumbra, area size and angle are Blender's; resolution is Blender's 1920 x 1080. Light power rule and its renders: operators/lights.py."""

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


def test_new_material_keeps_blender_values():
    _clear()
    b, ref = _bsdf(material.new_material()), _blender_bsdf()
    for name in ("Base Color", "Roughness", "Specular IOR Level", "Specular Tint", "Anisotropic",
                 "Coat Roughness", "Emission Color"):
        got, want = b.inputs[name].default_value, ref.inputs[name].default_value
        if hasattr(got, "__len__"):
            got, want = tuple(got), tuple(want)
        assert _close(got, want), (name, got, want)


def test_ae_rows_take_blender_input_names():
    rows = _rows(ae_layout.PRINCIPLED_TYPE)
    assert ("socket", "Base Color", "Base Color") in rows
    assert ("socket", "Roughness", "Roughness") in rows
    assert ("socket", "Specular IOR Level", "IOR Level") in rows
    assert ("socket", "Emission Color", "Color") in rows
    assert not any(r[0] == "maya" and r[1] != "allset_diffuse" for r in rows), rows
    assert not hasattr(bpy.types.Material, "allset_eccentricity")
    assert not hasattr(bpy.types.Material, "allset_cosine_power")


def test_ae_draws_the_material_property_row():
    """A "maya" row draws its Material property (an older material's Diffuse), not the socket."""
    _clear()
    mat = material.new_material()
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

    attribute_editor.draw_row(Rec(), bpy.context, None, mat, ("maya", "allset_diffuse", "Diffuse", "Roughness"))
    assert calls == [(mat, "allset_diffuse", "Diffuse")], calls


# --- lights --------------------------------------------------------------------------------------------------------

def _blender_light(kind):
    """The light data Blender's Add menu makes."""
    bpy.ops.object.light_add(type=kind)
    ob = bpy.context.active_object
    data = ob.data
    bpy.data.objects.remove(ob)
    return data


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
    ref = _blender_light('SPOT')
    assert _close(spot.spot_size, ref.spot_size) and _close(spot.spot_blend, ref.spot_blend), "Blender's cone"


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
    ref = _blender_light('AREA')
    assert area.allset_decay == 'NO_DECAY' and _close(area.size, ref.size) and area.shape == ref.shape, \
        "Blender's area light size"
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

def test_template_resolution_is_blenders():
    with bpy.data.libraries.load(app_template.STARTUP) as (src, dst):
        dst.scenes = list(src.scenes)
    try:
        for sc in dst.scenes:
            r = sc.render
            assert (r.resolution_x, r.resolution_y, r.resolution_percentage) == (1920, 1080, 100), \
                (sc.name, r.resolution_x, r.resolution_y, r.resolution_percentage)
            assert (r.pixel_aspect_x, r.pixel_aspect_y) == (1.0, 1.0)
    finally:
        for sc in dst.scenes:
            bpy.data.scenes.remove(sc)
