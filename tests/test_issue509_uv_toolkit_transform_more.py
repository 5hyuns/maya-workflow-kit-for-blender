"""#509: UV Toolkit Transform like Maya: preset values for the Move step (1 / 0.1 / 0.01), the Rotate angle
(15 / 45 / 90 / 180) and the Scale factor (2 / 4); a Step Snap row per area (Move / Rotate: on / off and the step;
Scale: on / off); Retain Component Spacing for typed U / V values; Distribute along U / V; the Rotate buttons' right-click
menu turns by 45 or 15; Rotate turns in the image's pixels (a non-square image keeps its shapes)."""

import math
from importlib import import_module

import bmesh
import bpy

import kit

tr = import_module(kit.MODULE + ".operators.uv_transform")
snap_align = import_module(kit.MODULE + ".operators.snap_align")


def _grid(n=4):
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


def test_presets():
    assert tr.PRESETS == {"nudge": (1.0, 0.1, 0.01), "rotate_angle": (15.0, 45.0, 90.0, 180.0),
                          "scale_factor": (2.0, 4.0), "texel_density": (8.0, 16.0, 32.0)}
    for prop in tr.PRESETS:
        assert hasattr(bpy.types, f"ALLSET_MT_uvtk_preset_{prop}"), prop
    tk = bpy.context.scene.allset_uv_toolkit
    bpy.ops.wm.context_set_float(data_path="scene.allset_uv_toolkit.rotate_angle", value=45.0)
    assert tk.rotate_angle == 45.0
    tk.rotate_angle = 90.0


def test_step_snap_values():
    tk = bpy.context.scene.allset_uv_toolkit
    ts = bpy.context.scene.tool_settings
    assert (round(tk.move_snap_value, 6), round(tk.rotate_snap_value, 6), tk.retain_spacing, tk.distribute_axis) == \
        (0.1, 15.0, True, 'U')
    tk.rotate_snap_value = 45.0
    assert abs(math.degrees(ts.snap_angle_increment_2d) - 45.0) < 1e-4, "the Rotate step = Blender's 2D angle step"
    tk.rotate_snap_value = 15.0
    for kind in ('TRANSLATE', 'ROTATE', 'RESIZE'):
        snap_align.set_uv_step_snap(ts, kind, True)
        assert snap_align.uv_step_snap_on(ts, kind)
        snap_align.set_uv_step_snap(ts, kind, False)


def test_rotate_keeps_shapes_on_a_wide_image():
    ob = _grid()
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.active
    loops = [l for f in bm.faces for l in f.loops]
    found = [(ob, bm, uv, loops)]
    before = {l.index: tuple(l[uv].uv) for l in loops}
    tr.rotate(found, (0.0, 0.0), 90.0, aspect=2.0)
    for l in loops:
        u0, v0 = before[l.index]
        u, v = l[uv].uv
        # in pixels (u * 2, v): a quarter turn maps (x, y) to (-y, x)
        assert abs(u * 2.0 - (-v0)) < 1e-5 and abs(v - u0 * 2.0) < 1e-5, (before[l.index], (u, v))


def test_retain_spacing_off_puts_every_uv_on_the_value():
    ob = _grid()
    tk = bpy.context.scene.allset_uv_toolkit
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.active
    found = [(ob, bm, uv, [l for f in bm.faces for l in f.loops])]
    tk.retain_spacing = False
    try:
        orig_picked = tr.picked
        tr.picked = lambda context: found
        tr.position_set(0)(tk, 0.3)
    finally:
        tr.picked = orig_picked
        tk.retain_spacing = True
    us = {round(l[uv].uv.x, 6) for f in bm.faces for l in f.loops}
    assert us == {0.3}, us


def test_rotate_button_menu_registered():
    funcs = getattr(bpy.types.UI_MT_button_context_menu, "_dyn_ui_initialize", lambda: [])()
    assert tr.rotate_button_menu in funcs, "the Rotate buttons' right-click items"
    assert "angle" in bpy.ops.allset.uv_rotate_step.get_rna_type().properties.keys()
    assert hasattr(bpy.ops.allset, "uv_distribute_toolkit")
