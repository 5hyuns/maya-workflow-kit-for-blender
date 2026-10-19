# SPDX-License-Identifier: GPL-3.0-or-later
"""The opt-in: nothing changes until the user asks for Maya.

Part of CORE (registered whenever the extension is enabled, also in Blender mode). Enabling the extension only adds
the Maya | Blender switch, an Edit menu item, Ctrl+Alt+Shift+M and, once in a GUI session, this welcome dialog. Its
confirm button "Make Blender feel like Maya" (also in the add-on preferences) turns on Maya mode and Make Blender
Maya (``first_start.make``: layout template, theme, splash, density, start option). Cancelling changes nothing.

Not in background runs; GUI tests and tools set ``ALLSET_NO_WELCOME=1`` (the dialog would eat simulated events).
"""

import os

import bpy

from . import preferences

# Square art made by tools/make_splash.py (icons are square; the 2:1 splash would letterbox).
WELCOME_IMAGE = os.path.join(os.path.dirname(__file__), "welcome.png")
_previews = None


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


def _window():
    wm = bpy.context.window_manager
    return wm.windows[0] if wm and wm.windows else None


def opt_in(open_layout=True):
    """Everything "Make Blender feel like Maya" does. Runs from a timer (switching registers the Maya mode
    modules, which an operator of theirs must not do while it runs; )."""
    from . import switch
    switch.set_mode(True, layout=False)
    from . import first_start
    first_start.make(bpy.context, open_layout=False)
    window = _window()
    if not open_layout or bpy.app.background or window is None:
        return
    if not bpy.data.is_dirty and not bpy.data.filepath:
        first_start.open_layout_later()     # an untouched new file: start over in the template file
    else:
        switch.enter_layout(window)         # the user's file: append the layout workspace, keep the data


class ALLSET_OT_welcome(bpy.types.Operator):
    """Turn on the Maya-style keymap, layout, menus, theme and Maya preferences (asks first).
    Ctrl+Alt+Shift+M or the Maya / Blender switch turns it off again and restores your settings"""
    bl_idname = "allset.welcome"
    bl_label = "Make Blender feel like Maya"
    bl_options = {'INTERNAL'}

    open_layout: bpy.props.BoolProperty(name="Open Maya Layout", default=True, options={'SKIP_SAVE'})

    def invoke(self, context, event):
        preferences.get(context).welcome_done = True    # asked once, never again
        return context.window_manager.invoke_props_dialog(
            self, width=600, title="Welcome to Allset for Maya Users", confirm_text="Make Blender feel like Maya")

    def draw(self, context):
        row = self.layout.row()
        icon = _splash_icon()
        if icon:
            row.template_icon(icon_value=icon, scale=7.0)
        col = row.column()
        col.label(text="Allset for Maya Users")
        for line in ("The whole Maya workflow in Blender, in one install.",
                     "",
                     "Nothing has changed yet. Make Blender feel like Maya turns on",
                     "the Maya-style keymap: Alt+mouse, QWER, Space hotbox, marking menus;",
                     "the Maya layout, menus, Channel Box and shelf; the Maya colours;",
                     "Maya navigation, undo and panel preferences.",
                     "",
                     "Your settings are kept: the Maya | Blender switch at the top right",
                     "or Ctrl+Alt+Shift+M brings them back at any time."):
            col.label(text=line)

    def execute(self, context):
        preferences.get(context).welcome_done = True
        open_layout = self.open_layout
        bpy.app.timers.register(lambda: opt_in(open_layout), first_interval=0.0)
        return {'FINISHED'}


def _show_welcome():
    try:
        prefs = preferences.get()
    except KeyError:
        return None
    if prefs.welcome_done or prefs.maya_mode:
        return None
    win = _window()
    if win is None:
        return 0.5
    with bpy.context.temp_override(window=win, screen=win.screen):
        bpy.ops.allset.welcome('INVOKE_DEFAULT')
    return None


classes = (ALLSET_OT_welcome,)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    if not bpy.app.background and os.environ.get("ALLSET_NO_WELCOME") != "1":
        bpy.app.timers.register(_show_welcome, first_interval=0.5)


def unregister():
    global _previews
    if bpy.app.timers.is_registered(_show_welcome):
        bpy.app.timers.unregister(_show_welcome)
    if _previews is not None:
        bpy.utils.previews.remove(_previews)
        _previews = None
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
