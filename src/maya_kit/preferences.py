# SPDX-License-Identifier: GPL-3.0-or-later
"""Add-on preferences (Preferences > Add-ons > Maya Kit).

Options backed by docs/user_decisions.md (Maya units, parent mode, layout
install buttons) are added by the steps that implement them.
"""

import bpy


class MAYAKIT_AddonPreferences(bpy.types.AddonPreferences):
    # Must equal the top-level package name: "bl_ext.<repo>.maya_kit" as an
    # extension, "maya_kit" as a legacy add-on.
    bl_idname = __package__

    # Set once "Maya" was activated automatically on first enable, so later
    # starts respect a different keymap the user picked (docs/steps/step_2.md).
    keymap_auto_activated: bpy.props.BoolProperty(options={'HIDDEN'})

    def _update_navigation(self, context):
        from . import prefs_preset
        if self.use_maya_navigation:
            prefs_preset.apply(context.preferences, self)
        else:
            prefs_preset.restore(context.preferences, self)

    use_maya_navigation: bpy.props.BoolProperty(
        name="Maya Navigation Preferences",
        description="Set Blender's view navigation preferences to Maya behaviour "
                    "(turntable, no zoom to mouse, horizontal dolly, ...). "
                    "Turning it off restores your previous values",
        default=True, update=_update_navigation)
    # JSON of the user's values before the Maya preset (docs/steps/step_4.md).
    prefs_backup: bpy.props.StringProperty(options={'HIDDEN'})
    lock_ortho_tumble: bpy.props.BoolProperty(
        name="Lock Tumble in Ortho Views",
        description="Alt+LMB does nothing in top/front/side orthographic views (Maya)",
        default=True)

    def draw(self, context):
        from . import keymap
        layout = self.layout
        kcs = context.window_manager.keyconfigs
        row = layout.row()
        active = kcs.active.name if kcs.active else "-"
        row.label(text=f"Active keymap: {active}")
        if active != keymap.KEYCONFIG_NAME:
            row.operator("maya_kit.keymap_activate")
        col = layout.column()
        col.prop(self, "use_maya_navigation")
        col.prop(self, "lock_ortho_tumble")

        from . import app_template
        box = layout.box()
        box.label(text="Maya Layout (application template)")
        row = box.row()
        if app_template.is_installed():
            row.operator("maya_kit.layout_open", icon='FILE_NEW')
            row.operator("maya_kit.layout_install", text="Reinstall")
            row.operator("maya_kit.layout_remove", icon='TRASH')
        else:
            row.operator("maya_kit.layout_install", icon='IMPORT')

        box = layout.box()
        box.label(text="Maya Theme")
        row = box.row()
        row.operator("maya_kit.theme_apply", icon='COLOR')
        row.operator("maya_kit.theme_restore", icon='LOOP_BACK')


classes = (MAYAKIT_AddonPreferences,)

register, unregister = bpy.utils.register_classes_factory(classes)


def get(context=None):
    """Return this add-on's preferences instance."""
    context = context or bpy.context
    return context.preferences.addons[__package__].preferences
