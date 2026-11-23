"""A light's power is Blender's own: the Channel Box and Attribute Editor show Blender's Power (a sun: Strength) where
Maya has Intensity, a key on that row keys the power, and the command line's ``intensity`` reads and writes the power
as it is (``decayRate`` is no attribute: Blender lights fall off with distance squared)."""

from importlib import import_module

import bpy

import kit

cb = import_module(kit.MODULE + ".ui.channel_box")
cmds = import_module(kit.MODULE + ".command_line.cmds_shim")


def _light(kind):
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    bpy.ops.allset.create(kind=kind)
    return bpy.context.active_object


def test_power_row_is_the_energy():
    ob = _light('POINT_LIGHT')
    assert "sh:energy" in cb.drawn_keys(ob)
    assert cb.channel_label("sh:energy") == "Power"
    cb.set_value(ob, "sh:energy", 250.0)
    assert abs(ob.data.energy - 250.0) < 1e-6 and abs(cb.get_value(ob, "sh:energy") - 250.0) < 1e-6
    cb.set_selected_channels(["sh:energy"])
    bpy.context.scene.frame_set(1)
    assert bpy.ops.allset.cb_key_selected() == {'FINISHED'}
    assert [(f.data_path, f.array_index) for f in kit.fcurves(ob.data)] == [("energy", 0)]
    sun = _light('DIRECTIONAL_LIGHT')
    assert "sh:energy" in cb.drawn_keys(sun)
    assert cb.shape_label(sun, "energy") == "Strength"


def test_command_line_intensity_is_the_power():
    ob = _light('POINT_LIGHT')
    shape = ob.data.name
    cmds.setAttr(f"{ob.name}.intensity", 75.0)
    assert abs(ob.data.energy - 75.0) < 1e-6, ob.data.energy
    assert abs(cmds.getAttr(f"{shape}.intensity") - 75.0) < 1e-6
    try:
        cmds.getAttr(f"{shape}.decayRate")
    except (RuntimeError, ValueError) as ex:
        print("expected:", ex)
    else:
        raise AssertionError("decayRate: no such attribute")
