"""#517: UV Editor > Tools > Grab and Pinch are the kit's UV brush tools like the other Maya UV brushes: Grab moves the
UVs under the brush with the mouse (weighted by the brush falloff and the Strength in percent, along U / V only with
Direction, turned with Ctrl+drag and Twist); Pinch pulls the UVs under the stroke toward it (Ctrl pushes them away);
size / strength from the sidebar, B / M + drag and the middle mouse; pinned UVs stay."""

from importlib import import_module

import bpy
import numpy as np

import kit

brush = import_module(kit.MODULE + ".operators.uv_brush")
bmath = import_module(kit.MODULE + ".operators.uv_brush_math")
editor_map = import_module(kit.MODULE + ".ui.editor_menu_map")
menus = import_module(kit.MODULE + ".marking.menus")


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


def test_tools_and_menu():
    for mode, label in (("GRAB", "Grab"), ("PINCH", "Pinch")):
        assert mode in brush.MODES and brush.LABELS[mode] == label
        tid = brush.TOOL_IDS[mode]
        assert editor_map.MAP[f"UV Editor/Tools/{label}"] == \
            ("wm.tool_set_by_id", {"name": tid, "space_type": 'IMAGE_EDITOR'})
        km = bpy.context.window_manager.keyconfigs.addon.keymaps.get(f"Image Editor Tool: Uv, {label} UV")
        assert km is not None, label
        ids = {(k.type, k.idname) for k in km.keymap_items}
        assert {('LEFTMOUSE', "allset.uv_brush_stroke"), ('B', "allset.tap_hold"), ('M', "allset.tap_hold"),
                ('MIDDLEMOUSE', "allset.uv_brush_mmb")} <= ids, (label, ids)
        assert not any(i.startswith("sculpt.") for _t, i in ids), "not mixed with Blender's UV sculpt tool keys"
    assert menus.MENUS["UV_BRUSH"].radial["SE"] == ("Grab UV Tool", ("item", "UV Editor/Tools/Grab"))
    s = bpy.context.scene.allset_uv_brush
    assert (round(s.grab_size, 6), round(s.grab_strength, 6), s.grab_direction, s.grab_twist) == \
        (0.1, 80.0, 'UV', False)
    assert (round(s.pinch_size, 6), round(s.pinch_strength, 6)) == (0.1, 10.0)
    assert brush.FALLOFF_MODES >= {"GRAB", "PINCH"} and brush.MMB_STRENGTH >= {"GRAB", "PINCH"}


def test_grab_math():
    U = np.array([[0.5, 0.5], [0.55, 0.5], [0.7, 0.5]])
    w = bmath.sculpt_weights(U, (0.5, 0.5), 0.1) * 0.8
    out = bmath.grab(U, w, (0.5, 0.5), (0.1, 0.0))
    assert abs(out[0, 0] - 0.58) < 1e-9, "the UV at the centre follows Strength 80 % of the move"
    assert 0.5 < out[1, 0] < 0.63 and out[2, 0] == 0.7, out
    turned = bmath.grab(U, np.ones(3), (0.5, 0.5), (0, 0), twist=np.pi / 2)
    assert np.allclose(turned[1], (0.5, 0.55)), "a quarter turn counterclockwise about the centre"


def test_pinch_math():
    U = np.array([[0.55, 0.5], [0.5, 0.56], [0.8, 0.8]])
    out = bmath.pinch(U, (0.5, 0.5), 0.1, 0.1)
    d0 = np.hypot(*(U[:2] - 0.5).T)
    d1 = np.hypot(*(out[:2] - 0.5).T)
    assert (d1 < d0).all() and np.allclose(out[2], U[2]), "pulled toward the centre, the far UV stays"
    away = bmath.pinch(U, (0.5, 0.5), 0.1, 0.1, invert=True)
    assert (np.hypot(*(away[:2] - 0.5).T) > d0).all(), "Ctrl pushes away"


def test_on_a_mesh():
    ob = _grid()
    m = brush.MeshUVs(ob, True)
    pinned = (np.abs(m.U[:, 0] - 0.5) < 1e-6) & (np.abs(m.U[:, 1] - 0.6) < 1e-6)
    m.write_pins(pinned)
    U0 = m.U.copy()
    brush.apply_dab("PINCH", m, (0.5, 0.5), 0.15, 0.3, falloff="SURFACE_VOLUME")
    moved = np.abs(m.U - U0).max(axis=1) > 1e-9
    assert moved.any() and not moved[pinned].any(), "Pinch moves the UVs under the brush, not the pinned one"
    centre = (np.abs(U0[:, 0] - 0.5) < 1e-6) & (np.abs(U0[:, 1] - 0.5) < 1e-6)
    assert not moved[centre].any(), "the UV at the centre stays"
