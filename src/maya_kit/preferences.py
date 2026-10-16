# SPDX-License-Identifier: GPL-3.0-or-later
"""Add-on preferences (Preferences > Add-ons > Maya Kit).

Options backed by : Maya units (#1) and parent mode (#2)
from step 10, layout install buttons (#3) from step 5.
"""

import bpy


class MAYAKIT_AddonPreferences(bpy.types.AddonPreferences):
    # Must equal the top-level package name: "bl_ext.<repo>.maya_kit" as an
    # extension, "maya_kit" as a legacy add-on.
    bl_idname = __package__

    # Set once "Maya" was activated automatically on first enable, so later
    # starts respect a different keymap the user picked.
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
    # JSON of the user's values before the Maya preset.
    prefs_backup: bpy.props.StringProperty(options={'HIDDEN'})
    # JSON of Blender preferences changed by Maya keys (= / - gizmo size), restored on disable.
    runtime_backup: bpy.props.StringProperty(options={'HIDDEN'})
    lock_ortho_tumble: bpy.props.BoolProperty(
        name="Lock Tumble in Ortho Views",
        description="Alt+LMB does nothing in top/front/side orthographic views (Maya)",
        default=True)

    # Channel Box virtual slider ().
    cb_speed: bpy.props.EnumProperty(
        name="Slider Speed", default='MEDIUM',
        items=(('SLOWEST', "Slowest", "x0.01"), ('SLOW', "Slow", "x0.1"),
               ('MEDIUM', "Medium", "x1"), ('FAST', "Fast", "x10")))
    cb_hyperbolic: bpy.props.BoolProperty(
        name="Hyperbolic", description="Value change accelerates with drag distance")

    # Top UI.
    maya_top_bar: bpy.props.BoolProperty(
        name="Maya Menu Bar",
        description="Top bar shows the Maya menus, menu sets and Status Line instead of "
                    "Blender's menus and workspace tabs (Blender menus stay as submenus)",
        default=True)
    menu_set: bpy.props.EnumProperty(
        name="Menu Set", description="Maya menu set: which menus follow the common ones",
        items=lambda self, context: _menu_set_items(), default=0)
    show_status_line: bpy.props.BoolProperty(
        name="Status Line", description="Maya Status Line icons in the top bar", default=True)
    show_command_line: bpy.props.BoolProperty(
        name="Command Line", description="Python command line in the status bar", default=True)
    show_help_line: bpy.props.BoolProperty(
        name="Help Line", description="Maya-style help for the active tool in the status bar",
        default=True)

    # Marking menus and hotbox.
    marking_menu_style: bpy.props.EnumProperty(
        name="Marking Menus",
        description="How Maya marking menus are shown",
        items=(('ENGINE', "Maya Engine", "Maya-style marking menus: drag, flick, in-place submenus, "
                                          "option boxes"),
               ('PIE', "Blender Pies", "Blender pie menus (8 slots, submenus open new pies)")),
        default='ENGINE')
    hotbox_style: bpy.props.EnumProperty(
        name="Hotbox Style",
        items=(('ALL', "Zones and Menu Rows", ""), ('ZONES', "Zones Only", ""),
               ('CENTER', "Center Zone Only", "")),
        default='ALL')
    hotbox_all_sets: bpy.props.BoolProperty(
        name="Show All Menu Sets", description="Hotbox shows the menus of every menu set, not only "
                                               "the current one")

    # Shelf: current tab (factory file name or "USER:<name>").
    shelf_current: bpy.props.StringProperty(options={'HIDDEN'})

    # Scene concepts.
    parent_mode: bpy.props.EnumProperty(
        name="Parent Mode", description="What P (Parent) does to the child's values",
        items=(('MAYA', "Maya", "Keep the world position and recompute the local values "
                                "relative to the parent (parent inverse = identity)"),
               ('BLENDER', "Blender", "Keep the local values; Blender stores a hidden parent "
                                      "inverse matrix")),
        default='MAYA')
    maya_naming: bpy.props.BoolProperty(
        name="Maya Naming", description="Create menu names objects pCube1 / pCubeShape1 "
                                        "(otherwise Blender names)",
        default=True)
    # Maya manipSmartDuplicate 1 (, PREF:371-374).
    smart_duplicate: bpy.props.BoolProperty(
        name="Smart Duplicate", description="Shift+drag a Move/Rotate/Scale manipulator "
                                            "duplicates the selection and transforms the copy",
        default=True)
    # Maya manipSmartExtrude 1 (, PREF:371-374).
    smart_extrude: bpy.props.BoolProperty(
        name="Smart Extrude", description="Shift+drag a Move/Rotate/Scale manipulator on faces "
                                          "or edges extrudes them and transforms the new ones",
        default=True)

    def _update_units(self, context):
        from .operators import units
        if self.maya_units:
            units.apply_file()
        else:
            units.restore_file()

    maya_units: bpy.props.BoolProperty(
        name="Maya Units (1 BU = 1 cm)",
        description="Scene unit scale 0.01 with centimetres and Maya camera clipping "
                    "(0.1 - 10000) for this file and new files. Physics, light falloff and "
                    "importers assume 1 BU = 1 m. Turning it off restores the previous values",
        default=False, update=_update_units)

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

        box = layout.box()
        box.label(text="Scene Concepts")
        row = box.row()
        row.prop(self, "parent_mode")
        row.prop(self, "maya_naming")
        row = box.row()
        row.prop(self, "maya_units")
        row.prop(self, "smart_duplicate")
        row.prop(self, "smart_extrude")

        box = layout.box()
        box.label(text="UI Elements")
        row = box.row()
        row.prop(self, "maya_top_bar")
        row.prop(self, "menu_set", text="")
        row = box.row()
        row.prop(self, "marking_menu_style")
        row.prop(self, "hotbox_style", text="")
        row.prop(self, "hotbox_all_sets")
        row = box.row()
        row.prop(self, "show_status_line")
        row.prop(self, "show_command_line")
        row.prop(self, "show_help_line")

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


_SET_ITEMS = []


def _menu_set_items():
    # Kept in a module list: Blender needs the enum item strings to stay referenced.
    if not _SET_ITEMS:
        from .ui import menu_sets
        _SET_ITEMS.extend(menu_sets.SET_ITEMS)
    return _SET_ITEMS


classes = (MAYAKIT_AddonPreferences,)

register, unregister = bpy.utils.register_classes_factory(classes)


def get(context=None):
    """Return this add-on's preferences instance."""
    context = context or bpy.context
    return context.preferences.addons[__package__].preferences
