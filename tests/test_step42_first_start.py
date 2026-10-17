"""Step 42: Make Blender Maya in one action, its revert, the theme option and add-on safety.

The welcome dialog and the start-in-Maya-layout switch need a GUI (tools/look_shots.py,
); here: what make/revert change and that nothing leaks.
"""

import os
from importlib import import_module

import addon_utils
import bpy

import kit

app_template = import_module(kit.MODULE + ".app_template")
theme = import_module(kit.MODULE + ".theme")
preferences = import_module(kit.MODULE + ".preferences")
first_start = import_module(kit.MODULE + ".first_start")
OTHER = "node_wrangler"   # a core add-on the "user" had on before installing the kit


def _theme_hash():
    return kit._struct_hash(bpy.context.preferences.themes[0])


def _addons():
    return set(bpy.context.preferences.addons.keys())


def test_runs_sandboxed():
    # Make Blender Maya saves the preferences: never let that reach the real config (step 42).
    cfg = os.path.normcase(bpy.utils.user_resource('CONFIG'))
    assert os.path.normcase(os.path.join("tmp", "test_env")) in cfg, cfg


def test_theme_option_comes_back_on_disable():
    h0 = _theme_hash()
    preferences.get().maya_theme = True
    assert _theme_hash() != h0 and theme.has_backup()
    grad = bpy.context.preferences.themes[0].view_3d.space.gradients
    assert grad.background_type == 'SINGLE_COLOR'
    kit.disable()
    assert _theme_hash() == h0, "disabling the add-on restores the user's theme"
    assert not theme.has_backup()
    kit.enable()
    assert _theme_hash() == h0


def test_make_maya_keeps_user_addons_and_reverts():
    addon_utils.enable(OTHER, default_set=True)
    before_addons = _addons()
    h0 = _theme_hash()
    splash0 = bpy.context.preferences.view.show_splash
    assert splash0, "factory default shows the splash"

    # The operator opens the layout from a timer (never runs in -b): call what it runs.
    first_start.make(bpy.context, open_layout=True)
    prefs = preferences.get()
    assert bpy.context.preferences.app_template == app_template.TEMPLATE_ID
    assert app_template.is_installed()
    assert prefs.maya_theme and prefs.maya_hide_splash and prefs.start_in_maya_layout and prefs.welcome_done
    assert not bpy.context.preferences.view.show_splash
    assert _theme_hash() != h0
    assert _addons() == before_addons, (_addons() ^ before_addons)   # nothing switched off or on
    assert OTHER in _addons()
    # the layout template ships its splash, no userpref.blend (would replace the add-on list)
    files = os.listdir(app_template.installed_dir())
    assert "splash.png" in files and "userpref.blend" not in files, files

    assert bpy.ops.maya_kit.revert_maya() == {'FINISHED'}
    prefs = preferences.get()
    assert not (prefs.maya_theme or prefs.maya_hide_splash or prefs.start_in_maya_layout)
    assert _theme_hash() == h0
    assert bpy.context.preferences.view.show_splash == splash0
    assert not app_template.is_installed()
    assert OTHER in _addons()
    addon_utils.disable(OTHER, default_set=True)


def test_make_without_opening_keeps_the_file():
    bpy.ops.mesh.primitive_cube_add()
    name = bpy.context.active_object.name
    template = bpy.context.preferences.app_template
    assert bpy.ops.maya_kit.make_maya(open_layout=False) == {'FINISHED'}
    assert name in bpy.data.objects, "open_layout=False leaves the open file alone"
    assert bpy.context.preferences.app_template == template
    bpy.ops.maya_kit.revert_maya()
