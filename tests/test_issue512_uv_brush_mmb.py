"""#512: in the UV Editor brush tools a middle-mouse drag left / right changes the brush size and up / down its
strength, like Maya: the size grows by the drag in UV units, the strength (0-100) by a hundred times it; the drag
keeps the direction it starts in. Unfold / Optimize change only the size; Cut, Sew and Smudge pass the middle mouse
on (it changes nothing there)."""

from importlib import import_module

import bpy

import kit

brush = import_module(kit.MODULE + ".operators.uv_brush")


def test_values():
    assert abs(brush.mmb_value("PIN", 'X', 0.1, 0.185) - 0.285) < 1e-9
    assert brush.mmb_value("PIN", 'X', 0.1, -0.5) == 0.01, "the size stops at 0.01"
    assert brush.mmb_value("UNFOLD", 'X', 0.1, -0.5) == 0.0, "the Unfold brush size can reach 0"
    assert abs(brush.mmb_value("PIN", 'Y', 100.0, -0.185) - 81.5) < 1e-9
    assert abs(brush.mmb_value("SMEAR", 'Y', 0.05, 0.185) - 18.55) < 1e-9
    assert brush.mmb_value("SMEAR", 'Y', 0.05, -0.185) == 0.01, "the strength stops at 0.01"


def test_direction_is_kept():
    op = brush.ALLSET_OT_uv_brush_mmb
    fake = type("F", (), {"_mode": "PIN"})()
    assert op._pick_axis(fake, 2, 1) is None, "a few pixels pick nothing yet"
    assert op._pick_axis(fake, 10, -6) == 'X', "mostly sideways = size"
    assert op._pick_axis(fake, 2, 9) == 'Y'
    fake._mode = "UNFOLD"
    assert op._pick_axis(fake, 2, 9) == '', "Unfold / Optimize: up / down changes nothing"


def test_keymaps():
    for mode in brush.MODES:
        label = mode.title()
        km = bpy.context.window_manager.keyconfigs.addon.keymaps.get(f"Image Editor Tool: Uv, {label}")
        assert km is not None, label
        mmb = [k for k in km.keymap_items if k.type == 'MIDDLEMOUSE' and k.value == 'PRESS']
        ids = [k.idname for k in mmb]
        assert "allset.uv_brush_mmb" in ids, (label, ids)
        assert not any(k.ctrl or k.shift or k.alt for k in mmb), "Alt + MMB stays the view pan"
