"""Step 44: Maya widget feel — square flat widgets (theme), Maya density, Segoe UI, aliased wires."""

import os
from importlib import import_module

import bpy

import kit

theme = import_module(kit.MODULE + ".theme")
preferences = import_module(kit.MODULE + ".preferences")
prefs_preset = import_module(kit.MODULE + ".prefs_preset")
first_start = import_module(kit.MODULE + ".first_start")
draw = import_module(kit.MODULE + ".marking.draw")
channel_box = import_module(kit.MODULE + ".ui.channel_box")


def test_theme_square_flat_widgets():
    preferences.get().maya_theme = True
    try:
        ui = bpy.context.preferences.themes[0].user_interface
        for prop in ui.bl_rna.properties:
            name = prop.identifier
            if name.startswith("wcol_") and name != "wcol_state":
                w = getattr(ui, name)
                assert w.roundness <= 0.1, (name, w.roundness)
                assert not w.show_shaded, name
        assert ui.widget_emboss[3] == 0.0, tuple(ui.widget_emboss)
        assert ui.panel_roundness == 0.0, ui.panel_roundness
        assert ui.menu_shadow_width == 0, ui.menu_shadow_width
    finally:
        preferences.get().maya_theme = False
    # Restored: Blender's default theme is rounded again.
    ui = bpy.context.preferences.themes[0].user_interface
    assert ui.wcol_regular.roundness > 0.1 and ui.widget_emboss[3] > 0.0


def test_maya_ui_scale_is_one_over_os_scale():
    p = bpy.context.preferences
    os_scale = prefs_preset.os_scale(p)
    assert abs(prefs_preset.maya_ui_scale(p) - round(1.0 / os_scale, 3)) < 1e-6, os_scale
    # Invariant under the preset itself: the OS scale is read back through view.ui_scale.
    before = p.view.ui_scale
    p.view.ui_scale = 1.3
    try:
        assert abs(prefs_preset.os_scale(p) - os_scale) < 0.01
    finally:
        p.view.ui_scale = before


def test_density_font_wire_backup_restore():
    p = bpy.context.preferences
    addon = preferences.get()
    p.view.ui_scale = 1.3
    p.view.font_path_ui = ""
    p.system.use_overlay_smooth_wire = True
    p.system.use_edit_mode_smooth_wire = True
    addon.maya_density = True
    addon.maya_font = True
    addon.maya_wire = True
    assert abs(p.view.ui_scale - prefs_preset.maya_ui_scale(p)) < 1e-3, p.view.ui_scale
    if prefs_preset.font_available():
        assert os.path.normcase(p.view.font_path_ui) == os.path.normcase(prefs_preset.SEGOE_UI), p.view.font_path_ui
    else:
        assert p.view.font_path_ui == ""
    assert not p.system.use_overlay_smooth_wire and not p.system.use_edit_mode_smooth_wire
    addon.maya_density = False
    addon.maya_font = False
    addon.maya_wire = False
    assert abs(p.view.ui_scale - 1.3) < 1e-6 and p.view.font_path_ui == ""
    assert p.system.use_overlay_smooth_wire and p.system.use_edit_mode_smooth_wire
    assert not (addon.density_backup or addon.font_backup or addon.wire_backup)
    p.view.ui_scale = 1.0


def test_disable_restores_density_font_wire():
    p = bpy.context.preferences
    p.view.ui_scale = 1.1
    addon = preferences.get()
    addon.maya_density = True
    addon.maya_font = True
    addon.maya_wire = True
    kit.disable()
    try:
        assert abs(p.view.ui_scale - 1.1) < 1e-6, p.view.ui_scale
        assert p.view.font_path_ui == ""
        assert p.system.use_overlay_smooth_wire
    finally:
        kit.enable()
        a = bpy.context.preferences.addons[kit.MODULE].preferences
        a.maya_density = a.maya_font = a.maya_wire = False
        p.view.ui_scale = 1.0


def test_make_and_revert_maya_switch_widget_feel():
    ctx = bpy.context
    addon = preferences.get()
    first_start.make(ctx, open_layout=False)
    try:
        assert addon.maya_density and addon.maya_wire
        assert addon.maya_font == prefs_preset.font_available()
    finally:
        first_start.revert(ctx)
    assert not (addon.maya_density or addon.maya_font or addon.maya_wire)
    assert ctx.preferences.view.font_path_ui == ""


def test_marking_menu_text_uses_interface_font():
    import blf
    p = bpy.context.preferences
    assert draw.font_size() == max(8, round(11 * p.system.ui_scale))
    if prefs_preset.font_available():
        p.view.font_path_ui = prefs_preset.SEGOE_UI
        try:
            # draw.py draws with blf font 0: the interface font is loaded as id 0, so loading the same
            # file again returns 0 (checked, ).
            assert blf.load(prefs_preset.SEGOE_UI) == 0
        finally:
            p.view.font_path_ui = ""


def test_channel_box_rows_are_maya_height():
    # 20 px Blender rows x 0.8 = 16 px channel rows at the Maya density.
    assert abs(20 * channel_box.ROW_SCALE - 16) < 1e-6
