"""#514: the UV Editor Pin tool has Maya's Paint Method (Paint / Smooth) and Shift+drag smoothing. Blender's UV pins
are on or off, so smoothing takes the majority of each UV and its UV-edge neighbours under the brush: a lone pin goes,
a hole in pinned UVs fills, a straight pin border stays; Paint pins (Ctrl unpins), Smooth smooths (Ctrl too)."""

from importlib import import_module

import bpy
import numpy as np

import kit

brush = import_module(kit.MODULE + ".operators.uv_brush")
bmath = import_module(kit.MODULE + ".operators.uv_brush_math")


def _grid(n=10):
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=n, y_subdivisions=n, size=2, calc_uvs=True)
    ob = bpy.context.active_object
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.scene.tool_settings.use_uv_select_sync = True
    bpy.ops.mesh.select_all(action='SELECT')
    return ob


def _at(m, u, v):
    return int(np.nonzero((np.abs(m.U[:, 0] - u) < 1e-6) & (np.abs(m.U[:, 1] - v) < 1e-6))[0][0])


def test_setting_and_keys():
    s = bpy.context.scene.allset_uv_brush
    assert s.pin_method == 'PAINT'
    km = bpy.context.window_manager.keyconfigs.addon.keymaps.get("Image Editor Tool: Uv, Pin")
    shift = [k for k in km.keymap_items if k.type == 'LEFTMOUSE' and k.shift and k.idname == "allset.uv_brush_stroke"]
    assert len(shift) == 1 and shift[0].properties.smooth, shift


def test_smooth_math():
    ob = _grid()
    m = brush.MeshUVs(ob, True)
    arr = m.edge_arrays()
    everywhere = np.ones(len(m.U), bool)
    lone = np.zeros(len(m.U), bool)
    lone[_at(m, 0.5, 0.5)] = True
    assert not bmath.smooth_pins(lone, arr["a"], arr["b"], everywhere).any(), "a lone pin goes"
    hole = np.ones(len(m.U), bool)
    hole[_at(m, 0.5, 0.5)] = False
    assert bmath.smooth_pins(hole, arr["a"], arr["b"], everywhere).all(), "a hole fills"
    half = m.U[:, 0] < 0.45
    out = bmath.smooth_pins(half, arr["a"], arr["b"], everywhere)
    assert (out == half).all(), "a straight pin border stays"
    outside = np.zeros(len(m.U), bool)
    assert (bmath.smooth_pins(lone, arr["a"], arr["b"], outside) == lone).all(), "only UVs under the brush change"


def test_smooth_dab_and_method():
    ob = _grid()
    m = brush.MeshUVs(ob, True)
    pins = np.zeros(len(m.U), bool)
    pins[_at(m, 0.5, 0.5)] = True
    pins[_at(m, 0.9, 0.9)] = True
    m.write_pins(pins)
    assert brush.apply_dab("PIN_SMOOTH", m, (0.5, 0.5), 0.15, 1.0, falloff="VOLUME")
    assert not m.pinned[_at(m, 0.5, 0.5)] and m.pinned[_at(m, 0.9, 0.9)], "the pin under the brush went, not the far one"
