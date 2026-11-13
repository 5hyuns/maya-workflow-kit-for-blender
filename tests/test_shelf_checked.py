"""A user shelf button's "checked" field names a kit preference (optionally "not ..."); no code is evaluated."""

from importlib import import_module

import bpy

import kit

shelf = import_module(kit.MODULE + ".ui.shelf")
preferences = import_module(kit.MODULE + ".preferences")


def test_checked_reads_a_preference_by_name():
    prefs = preferences.get(bpy.context)
    old = prefs.select_through
    try:
        for on in (True, False):
            prefs.select_through = on
            assert shelf._checked(bpy.context, {"checked": "select_through"}) is on
            assert shelf._checked(bpy.context, {"checked": "prefs.select_through"}) is on
            assert shelf._checked(bpy.context, {"checked": "not prefs.select_through"}) is (not on)
    finally:
        prefs.select_through = old


def test_checked_is_off_for_missing_unknown_or_code():
    for record in (None, {}, {"checked": ""}, {"checked": "no_such_pref"}, {"checked": "__class__"},
                   {"checked": "__import__('os').getcwd()"}, {"checked": "bpy.ops.wm.quit_blender()"}):
        assert shelf._checked(bpy.context, record) is False, record
