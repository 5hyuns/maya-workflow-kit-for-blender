# SPDX-License-Identifier: GPL-3.0-or-later
"""Add-on preferences (Preferences > Add-ons > Maya Kit).

Options backed by  (Maya units, parent mode, layout
install buttons) are added by the steps that implement them.
"""

import bpy


class MAYAKIT_AddonPreferences(bpy.types.AddonPreferences):
    # Must equal the top-level package name: "bl_ext.<repo>.maya_kit" as an
    # extension, "maya_kit" as a legacy add-on.
    bl_idname = __package__

    # Set once "Maya" was activated automatically on first enable, so later
    # starts respect a different keymap the user picked.
    keymap_auto_activated: bpy.props.BoolProperty(options={'HIDDEN'})

    def draw(self, context):
        from . import keymap
        layout = self.layout
        kcs = context.window_manager.keyconfigs
        row = layout.row()
        active = kcs.active.name if kcs.active else "-"
        row.label(text=f"Active keymap: {active}")
        if active != keymap.KEYCONFIG_NAME:
            row.operator("maya_kit.keymap_activate")


classes = (MAYAKIT_AddonPreferences,)

register, unregister = bpy.utils.register_classes_factory(classes)


def get(context=None):
    """Return this add-on's preferences instance."""
    context = context or bpy.context
    return context.preferences.addons[__package__].preferences
