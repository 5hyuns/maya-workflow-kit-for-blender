"""Material, light and Render Settings defaults.

New materials are plain Principled BSDF materials (Blender's values); the Attribute Editor shows their inputs by
Blender's names. Lights: Blender's own power, cone, penumbra, area size and angle; resolution is Blender's
1920 x 1080."""

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


def test_new_lights_keep_blender_values():
    _clear()
    _cm()
    for kind, blender in (('POINT_LIGHT', 'POINT'), ('SPOT_LIGHT', 'SPOT'), ('AREA_LIGHT', 'AREA'),
                          ('DIRECTIONAL_LIGHT', 'SUN')):
        light = create.create(bpy.context, kind).data
        ref = _blender_light(blender)
        assert _close(light.energy, ref.energy), (kind, light.energy, ref.energy)
        if blender == 'SPOT':
            assert _close(light.spot_size, ref.spot_size) and _close(light.spot_blend, ref.spot_blend), "Blender's cone"
        if blender == 'AREA':
            assert _close(light.size, ref.size) and light.shape == ref.shape, "Blender's area light size"
        if blender == 'SUN':
            assert _close(light.angle, ref.angle), "Blender's angle"
        tree = light.node_tree
        assert tree is None or not [n for n in tree.nodes if n.type == 'LIGHT_FALLOFF'], kind


def test_ae_light_rows():
    for name, label in (("POINT", "Power"), ("SPOT", "Power"), ("AREA", "Power"), ("SUN", "Strength")):
        rows = _rows(name)
        assert ("prop", "data", "energy", label) in rows, name
        assert not any(r[0] == "prop" and r[2].startswith("allset_") for r in rows), name


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
