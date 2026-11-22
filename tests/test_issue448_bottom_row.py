"""#448: with Help Line and Command Line both off the bottom row goes, like Maya: no screen shows Blender's status bar
in its place. Turning either back on, or switching the kit to Blender, shows again only the status bars the kit
hid (one the user hid stays hidden)."""

from importlib import import_module

import bpy

import kit

AUTO_ENABLE = False     # the test turns Maya mode on and off itself


def _prefs():
    return bpy.context.preferences.addons[kit.MODULE].preferences


def _cl():
    return import_module(kit.MODULE + ".command_line")


def _shown():
    return {s.name: s.show_statusbar for s in bpy.data.screens}


def test_both_off_hides_the_status_bar_and_one_on_brings_it_back():
    kit.enable()
    prefs = _prefs()
    user_hidden = bpy.data.screens[0]
    try:
        user_hidden.show_statusbar = False             # hidden by the user: the kit leaves it alone
        others = [s for s in bpy.data.screens if s != user_hidden]
        assert others and all(s.show_statusbar for s in others)
        prefs.show_help_line = False
        assert all(s.show_statusbar for s in others), "Command Line still on: the row stays"
        prefs.show_command_line = False
        assert not any(_shown().values()), _shown()
        assert all(s.get(_cl().HIDDEN) for s in others) and not user_hidden.get(_cl().HIDDEN)
        prefs.show_command_line = True
        assert all(s.show_statusbar for s in others) and not user_hidden.show_statusbar, _shown()
        assert not any(s.get(_cl().HIDDEN) for s in bpy.data.screens)
        prefs.show_help_line = True
        assert all(s.show_statusbar for s in others), _shown()
    finally:
        prefs.show_help_line = prefs.show_command_line = True
        user_hidden.show_statusbar = True
        kit.disable()


def test_switch_to_blender_and_file_load():
    kit.enable()
    prefs = _prefs()
    switch = import_module(kit.MODULE + ".switch")
    try:
        prefs.show_help_line = prefs.show_command_line = False
        assert not any(_shown().values()), _shown()
        switch.set_mode(False, layout=False)              # Blender: the status bars come back
        assert all(_shown().values()), _shown()
        assert not any(s.get(_cl().HIDDEN) for s in bpy.data.screens)
        prefs.show_help_line = True                     # Maya mode off: the preferences change nothing on screen
        prefs.show_help_line = False
        assert all(_shown().values()), _shown()
        kit.maya_mode_on()                              # back on with both off: hidden again (on a timer)
        _cl()._sync_later()
        assert not any(_shown().values()), _shown()
        bpy.ops.wm.read_homefile(app_template="")       # a new file: its screens are hidden as well
        _cl()._sync_later()
        assert not any(_shown().values()), _shown()
    finally:
        prefs.show_help_line = prefs.show_command_line = True
        kit.disable()
        for s in bpy.data.screens:
            s.show_statusbar = True
