"""#518: the UV Editor Smudge tool has Maya's "Middle mouse initiates" option (off at the start): when on, a
middle-mouse drag smudges and a left-mouse drag does nothing; when off, the reverse."""

from importlib import import_module

import bpy

import kit

brush = import_module(kit.MODULE + ".operators.uv_brush")
tools = import_module(kit.MODULE + ".ui.uv_brush_tools")


def test_setting_and_keymap():
    s = bpy.context.scene.allset_uv_brush
    assert s.smudge_middle is False
    km = bpy.context.window_manager.keyconfigs.addon.keymaps.get("Image Editor Tool: Uv, Smudge")
    items = [k for k in km.keymap_items if k.type == 'MIDDLEMOUSE' and k.idname == "allset.uv_brush_stroke"]
    assert len(items) == 1 and items[0].properties.mode == 'SMUDGE' and items[0].properties.middle, items
    for other in ("Pin", "Smear", "Unfold"):
        km = bpy.context.window_manager.keyconfigs.addon.keymaps.get(f"Image Editor Tool: Uv, {other}")
        assert not [k for k in km.keymap_items if k.type == 'MIDDLEMOUSE' and k.idname == "allset.uv_brush_stroke"]
