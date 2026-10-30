"""Main menu bar widths follow the translated label (#249: Japanese labels were cut off)."""

import blf
import bpy


def _ms():
    from bl_ext.user_default.allset.ui import menu_sets
    return menu_sets


def test_width_measures_translated_label():
    ms = _ms()
    view = bpy.context.preferences.view
    old = (view.language, view.use_translate_interface)
    try:
        view.language = 'ja_JP'
        view.use_translate_interface = True
        shown = bpy.app.translations.pgettext_iface("Edit")
        assert shown != "Edit", "no Japanese translation for 'Edit' in this Blender"
        prefs = bpy.context.preferences
        scale = prefs.system.ui_scale or 1.0
        blf.size(0, prefs.ui_styles[0].widget.points * scale)
        want = (blf.dimensions(0, shown)[0] + ms.MENU_PAD_PX * scale) / (20.0 * scale)
        assert abs(ms.menu_width_units("Edit", bpy.context) - want) < 1e-6
    finally:
        view.language, view.use_translate_interface = old


def test_width_untranslated_unchanged():
    ms = _ms()
    prefs = bpy.context.preferences
    assert not prefs.view.use_translate_interface or prefs.view.language in ('en_US', 'DEFAULT')
    scale = prefs.system.ui_scale or 1.0
    blf.size(0, prefs.ui_styles[0].widget.points * scale)
    want = (blf.dimensions(0, "Windows")[0] + ms.MENU_PAD_PX * scale) / (20.0 * scale)
    assert abs(ms.menu_width_units("Windows", bpy.context) - want) < 1e-6
