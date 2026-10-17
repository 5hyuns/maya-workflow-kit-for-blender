# SPDX-License-Identifier: GPL-3.0-or-later
"""First start: "Make Blender Maya" in one action, its revert, the welcome dialog and
starting Blender in the Maya layout (docs/steps/step_42.md).

- ``maya_kit.make_maya``: install the layout template, Maya theme on, Blender splash off,
  Maya density / font / aliased wires on (step 44),
  start-in-Maya-layout on, save the preferences, open a new file with the Maya layout.
- ``maya_kit.revert_maya``: all of it off again (theme and splash setting restored), the
  template removed; the open file is left alone.
- ``maya_kit.welcome``: shown once on the first GUI start after the add-on is enabled
  (its confirm button = make_maya). Not in background runs; GUI tests set
  ``MAYA_KIT_NO_WELCOME=1``.
- Start in the Maya layout: armed on register, the first load_post (Blender's startup file,
  loaded right after the add-ons register) switches to the template when Blender started
  without a file; the first timer tick disarms it, so File > New later is left alone.

Switching templates reloads the saved preferences (docs/steps/step_13.md), so make_maya
saves them first; the template has no userpref.blend of its own (it would replace the
user's add-on list, measured in step 42). The reload also unregisters and registers the
add-on, so operators never switch templates themselves (Blender crashed reporting an
operator whose class was re-registered meanwhile): ``open_layout_later`` does it from a
timer after the operator has returned.
"""

import os

import bpy
from bpy.app.handlers import persistent

from . import app_template, preferences, prefs_preset

# Square art made by tools/make_splash.py (icons are square; the 2:1 splash would letterbox).
WELCOME_IMAGE = os.path.join(os.path.dirname(__file__), "welcome.png")
_previews = None
_armed = [False]


def _splash_icon():
    global _previews
    if not os.path.isfile(WELCOME_IMAGE):
        return 0
    if _previews is None:
        import bpy.utils.previews
        _previews = bpy.utils.previews.new()
    if "splash" not in _previews:
        _previews.load("splash", WELCOME_IMAGE, 'IMAGE')
    return _previews["splash"].icon_id


def make(context, open_layout=True):
    """Everything "Make Blender Maya" does; returns the installed template folder."""
    prefs = preferences.get(context)
    dst = app_template.install()
    prefs.maya_theme = True
    prefs.maya_hide_splash = True
    # Widget feel (step 44): Maya pixel density, Segoe UI where installed, aliased wires.
    prefs.maya_density = True
    prefs.maya_font = prefs_preset.font_available()
    prefs.maya_wire = True
    prefs.start_in_maya_layout = True
    prefs.welcome_done = True
    # Loading a template reloads the saved preferences: keep these choices.
    bpy.ops.wm.save_userpref()
    if open_layout:
        bpy.ops.wm.read_homefile(app_template=app_template.TEMPLATE_ID)
    return dst


def open_layout_later():
    """Open a new file with the Maya layout once the calling operator has finished."""
    if not bpy.app.timers.is_registered(_open_layout):
        bpy.app.timers.register(_open_layout, first_interval=0.01)


def revert(context):
    """Undo make(): theme and splash setting restored, start option off, template removed."""
    prefs = preferences.get(context)
    prefs.maya_theme = False
    prefs.maya_hide_splash = False
    prefs.maya_density = False
    prefs.maya_font = False
    prefs.maya_wire = False
    prefs.start_in_maya_layout = False
    removed = app_template.remove() if app_template.is_installed() else False
    context.preferences.is_dirty = True
    return removed


class MAYAKIT_OT_make_maya(bpy.types.Operator):
    """Maya layout, Maya theme and density, no splash screen and start Blender in the Maya layout.
    Opens a new file with the Maya layout"""
    bl_idname = "maya_kit.make_maya"
    bl_label = "Make Blender Maya"
    bl_options = {'INTERNAL'}

    open_layout: bpy.props.BoolProperty(name="Open Maya Layout", default=True, options={'SKIP_SAVE'})

    def invoke(self, context, event):
        if self.open_layout and bpy.data.is_dirty:
            return context.window_manager.invoke_confirm(
                self, event, title="Make Blender Maya",
                message="A new file with the Maya layout replaces the open file (unsaved changes are lost)")
        return self.execute(context)

    def execute(self, context):
        try:
            make(context, open_layout=False)
        except (OSError, RuntimeError) as ex:
            self.report({'ERROR'}, str(ex))
            return {'CANCELLED'}
        if self.open_layout:
            open_layout_later()
        return {'FINISHED'}


class MAYAKIT_OT_revert_maya(bpy.types.Operator):
    """Turn off the Maya theme, splash and start options and remove the Maya layout template.
    The open file is not changed"""
    bl_idname = "maya_kit.revert_maya"
    bl_label = "Revert Maya Look"
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        try:
            revert(context)
        except (OSError, RuntimeError) as ex:
            self.report({'ERROR'}, str(ex))
            return {'CANCELLED'}
        self.report({'INFO'}, "Maya look reverted")
        return {'FINISHED'}


class MAYAKIT_OT_welcome(bpy.types.Operator):
    """Maya Kit first start"""
    bl_idname = "maya_kit.welcome"
    bl_label = "Welcome to Maya Kit"
    bl_options = {'INTERNAL'}

    def invoke(self, context, event):
        preferences.get(context).welcome_done = True    # asked once, never again
        context.preferences.is_dirty = True
        return context.window_manager.invoke_props_dialog(
            self, width=600, title="Welcome to Maya Kit", confirm_text="Make Blender Maya")

    def draw(self, context):
        row = self.layout.row()
        icon = _splash_icon()
        if icon:
            row.template_icon(icon_value=icon, scale=7.0)
        col = row.column()
        col.label(text="Maya Kit")
        for line in ("The Maya keymap is on: Alt+mouse, QWER, Space hotbox,",
                     "marking menus, Maya keys.",
                     "",
                     "Make Blender Maya adds the Maya layout and colours,",
                     "starts Blender in the Maya layout and hides the splash.",
                     "Preferences > Add-ons > Maya Kit turns any of it off."):
            col.label(text=line)

    def execute(self, context):
        try:
            make(context, open_layout=False)
        except (OSError, RuntimeError) as ex:
            self.report({'ERROR'}, str(ex))
            return {'CANCELLED'}
        open_layout_later()
        return {'FINISHED'}


def _window():
    wm = bpy.context.window_manager
    return wm.windows[0] if wm and wm.windows else None


def _show_welcome():
    try:
        prefs = preferences.get()
    except KeyError:
        return None
    if prefs.welcome_done:
        return None
    win = _window()
    if win is None:
        return 0.5
    with bpy.context.temp_override(window=win, screen=win.screen):
        bpy.ops.maya_kit.welcome('INVOKE_DEFAULT')
    return None


@persistent
def _on_load_post(*_args):
    if not _armed[0]:
        return
    _armed[0] = False
    try:
        prefs = preferences.get()
    except KeyError:
        return
    if (prefs.start_in_maya_layout and not bpy.data.filepath and not bpy.app.background
            and bpy.context.preferences.app_template == "" and app_template.is_installed()):
        bpy.app.timers.register(_open_layout, first_interval=0.01)


def _open_layout():
    win = _window()
    if win is None:
        return 0.1
    with bpy.context.temp_override(window=win, screen=win.screen):
        bpy.ops.wm.read_homefile(app_template=app_template.TEMPLATE_ID)
    return None


def _disarm():
    _armed[0] = False
    return None


classes = (MAYAKIT_OT_make_maya, MAYAKIT_OT_revert_maya, MAYAKIT_OT_welcome)
_timers = (_show_welcome, _open_layout, _disarm)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.app.handlers.load_post.append(_on_load_post)
    if bpy.app.background:
        return
    _armed[0] = True
    bpy.app.timers.register(_disarm, first_interval=0.0)
    if os.environ.get("MAYA_KIT_NO_WELCOME") != "1":
        bpy.app.timers.register(_show_welcome, first_interval=0.5)


def unregister():
    global _previews
    for fn in _timers:
        if bpy.app.timers.is_registered(fn):
            bpy.app.timers.unregister(fn)
    if _on_load_post in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_on_load_post)
    _armed[0] = False
    if _previews is not None:
        bpy.utils.previews.remove(_previews)
        _previews = None
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
