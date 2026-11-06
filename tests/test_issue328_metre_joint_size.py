"""Issue #328: a joint Radius is centimetres in every scene unit (like Maya), so in a metre scene a Radius 1 joint
next to metre-sized objects was a thread. Until Display > Animation > Joint Size sets one for the scene, a scene
in metres (or larger) draws joints with the add-on preference Joint Size in Metre Scenes (default 10)."""

from importlib import import_module

import bpy

import kit

jd = import_module(kit.MODULE + ".operators.joint_display")
mj = import_module(kit.MODULE + ".ui.maya_joints")
preferences = import_module(kit.MODULE + ".preferences")


def _scene(unit, system='METRIC'):
    sc = bpy.data.scenes.new(f"S_{unit}")
    sc.unit_settings.system = system
    if system != 'NONE':
        sc.unit_settings.length_unit = unit
    return sc


def _prefs():
    return preferences.get(bpy.context)


def test_default_is_ten_in_metre_scenes():
    assert abs(_prefs().metre_joint_size - 10.0) < 1e-9
    assert abs(jd.joint_size(_scene('METERS')) - 10.0) < 1e-9
    assert abs(jd.joint_size(_scene('KILOMETERS')) - 10.0) < 1e-9


def test_centimetre_and_unitless_scenes_stay_one_like_maya():
    for sc in (_scene('CENTIMETERS'), _scene('MILLIMETERS'), _scene('METERS', system='NONE')):
        assert abs(jd.joint_size(sc) - 1.0) < 1e-9, sc.unit_settings.length_unit


def test_scene_joint_size_wins():
    sc = _scene('METERS')
    sc.allset_joint_size = 2.0          # Display > Animation > Joint Size
    assert abs(jd.joint_size(sc) - 2.0) < 1e-9
    sc.allset_joint_size = 1.0          # set back to 1 on purpose: still the scene's choice
    assert abs(jd.joint_size(sc) - 1.0) < 1e-9


def test_drawn_radius_uses_it():
    sc = _scene('METERS')
    bpy.ops.object.armature_add()
    bone = bpy.context.active_object.data.bones[0]
    r10 = mj.drawn_radius(bone, sc)
    _prefs().metre_joint_size = 1.0
    try:
        r1 = mj.drawn_radius(bone, sc)
    finally:
        _prefs().metre_joint_size = 10.0
    assert abs(r10 / r1 - 10.0) < 1e-6, (r10, r1)
    assert abs(r1 - 0.5 * 0.01) < 1e-9, r1        # Radius 1 x Joint Size 1 = 1 cm across in a metre scene


def test_preference_listed_with_range():
    p = _prefs().bl_rna.properties["metre_joint_size"]
    assert abs(p.hard_min - 0.01) < 1e-6 and abs(p.hard_max - 100.0) < 1e-6, (p.hard_min, p.hard_max)
