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

    def draw(self, context):
        self.layout.label(text="Maya Kit: options appear here as features are added.")


classes = (MAYAKIT_AddonPreferences,)

register, unregister = bpy.utils.register_classes_factory(classes)


def get(context=None):
    """Return this add-on's preferences instance."""
    context = context or bpy.context
    return context.preferences.addons[__package__].preferences
