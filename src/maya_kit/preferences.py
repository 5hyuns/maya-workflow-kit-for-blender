# SPDX-License-Identifier: GPL-3.0-or-later
"""Add-on preferences (Preferences > Add-ons > Maya Kit).

Options backed by docs/user_decisions.md: Maya units (#1) and parent mode (#2)
from step 10, layout install buttons (#3) from step 5.
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

    def _update_undo(self, context):
        from . import prefs_preset
        if self.use_maya_undo:
            prefs_preset.apply(context.preferences, self, "undo")
        else:
            prefs_preset.restore(context.preferences, self, "undo")

    use_maya_undo: bpy.props.BoolProperty(
        name="Maya Undo Queue",
        description="Keep as many undo steps as Blender allows (256; Maya's queue is infinite). "
                    "Turning it off restores your previous value",
        default=True, update=_update_undo)
    undo_backup: bpy.props.StringProperty(options={'HIDDEN'})
    # Edit-mode marquee/lasso also selects occluded components (Maya selectPrefUseDepth false).
    select_through: bpy.props.BoolProperty(
        name="Marquee Selects Hidden Components",
        description="In mesh edit mode, box and lasso selection also pick vertices, edges and faces "
                    "behind the surface, like Maya (Camera based selection off). X-ray is switched "
                    "on only while dragging",
        default=True)
    # Maya preSelectHilite true (research/maya/interaction.md:73).
    preselect_highlight: bpy.props.BoolProperty(
        name="Pre-selection Highlight",
        description="In mesh edit mode with a select tool, highlight the vertex, edge or face "
                    "under the mouse before clicking (Maya)",
        default=True)
    # First start (docs/steps/step_42.md): welcome dialog shown once; Maya look options.
    welcome_done: bpy.props.BoolProperty(options={'HIDDEN'})

    def _update_theme(self, context):
        from . import theme
        if self.maya_theme:
            theme.apply()
        else:
            theme.restore()

    maya_theme: bpy.props.BoolProperty(
        name="Maya Theme",
        description="Maya 2022 colours for the whole interface. Your theme is backed up and comes "
                    "back when this is turned off or the add-on is disabled",
        default=False, update=_update_theme)

    def _update_splash(self, context):
        from . import prefs_preset
        if self.maya_hide_splash:
            prefs_preset.apply(context.preferences, self, "splash")
        else:
            prefs_preset.restore(context.preferences, self, "splash")

    maya_hide_splash: bpy.props.BoolProperty(
        name="No Splash Screen",
        description="Start without Blender's splash screen, like Maya. Turning it off restores "
                    "your previous setting",
        default=False, update=_update_splash)
    splash_backup: bpy.props.StringProperty(options={'HIDDEN'})

    # Widget feel (docs/steps/step_44.md): Maya density, Maya font, aliased wires. Global Blender
    # preferences: backed up, restored when turned off or the add-on is disabled (prefs_preset).
    def _update_group(group, option):
        def update(self, context):
            from . import prefs_preset
            if getattr(self, option):
                prefs_preset.apply(context.preferences, self, group)
            else:
                prefs_preset.restore(context.preferences, self, group)
        return update

    maya_density: bpy.props.BoolProperty(
        name="Maya Density",
        description="Interface scale that gives Maya 2022's pixel sizes on this display (11 px text, "
                    "20 px rows: Maya ignores the Windows display scale). Turning it off restores "
                    "your previous Resolution Scale",
        default=False, update=_update_group("density", "maya_density"))
    density_backup: bpy.props.StringProperty(options={'HIDDEN'})
    maya_font: bpy.props.BoolProperty(
        name="Maya Font (Segoe UI)",
        description="Use the Windows Segoe UI font for the interface, like Maya (Windows only, the "
                    "installed system font). Turning it off restores your previous font",
        default=False, update=_update_group("font", "maya_font"))
    font_backup: bpy.props.StringProperty(options={'HIDDEN'})
    maya_wire: bpy.props.BoolProperty(
        name="Aliased Wireframes",
        description="Draw viewport wireframes as hard 1 px lines like Maya (no line smoothing). "
                    "Turning it off restores your previous setting",
        default=False, update=_update_group("wire", "maya_wire"))
    wire_backup: bpy.props.StringProperty(options={'HIDDEN'})
    del _update_group

    start_in_maya_layout: bpy.props.BoolProperty(
        name="Start in Maya Layout",
        description="When Blender starts without a file, open a new file with the Maya layout "
                    "(needs the Maya layout installed)",
        default=False)

    # JSON of Blender preferences changed by Maya keys (= / - gizmo size), restored on disable.
    runtime_backup: bpy.props.StringProperty(options={'HIDDEN'})
    lock_ortho_tumble: bpy.props.BoolProperty(
        name="Lock Tumble in Ortho Views",
        description="Alt+LMB does nothing in top/front/side orthographic views (Maya)",
        default=True)

    # Channel Box virtual slider (research/maya/channel_box.md:83-91).
    cb_speed: bpy.props.EnumProperty(
        name="Slider Speed", default='MEDIUM',
        items=(('SLOWEST', "Slowest", "x0.01"), ('SLOW', "Slow", "x0.1"),
               ('MEDIUM', "Medium", "x1"), ('FAST', "Fast", "x10")))
    cb_hyperbolic: bpy.props.BoolProperty(
        name="Hyperbolic", description="Value change accelerates with drag distance")

    # Top UI (docs/steps/step_7.md; Maya Windows > UI Elements, research/maya/ui_layout.md:190-191).
    maya_top_bar: bpy.props.BoolProperty(
        name="Maya Menu Bar",
        description="Top bar shows the Maya menus, menu sets and Status Line instead of "
                    "Blender's menus and workspace tabs (Blender menus stay as submenus)",
        default=True)
    # Maya view furniture (docs/steps/step_46.md), in views whose Blender navigation gizmo is off.
    maya_viewcube: bpy.props.BoolProperty(
        name="ViewCube", description="Maya ViewCube in the top right of the view (click a face to look "
                                     "along it)", default=True)
    maya_camera_names: bpy.props.BoolProperty(
        name="Camera Names", description="Maya camera name (persp, top -Z, ...) at the bottom of the view",
        default=True)
    def _update_selection_wire(self, context):
        for window in context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()

    # Maya wireframe on selected objects over shading (docs/steps/step_47.md).
    maya_selection_wire: bpy.props.BoolProperty(
        name="Selection Wireframe", description="Selected objects show their wireframe over shading, like "
                                                "Maya (lead light green, others white with the Maya theme)",
        default=True, update=_update_selection_wire)
    maya_view_axis: bpy.props.BoolProperty(
        name="View Axis", description="Maya axis triad in the bottom left of the view", default=True)
    maya_panel_menus: bpy.props.BoolProperty(
        name="Panel Menus",
        description="3D View headers show Maya's panel menus (View, Shading, Lighting, Show, Renderer, "
                    "Panels) instead of Blender's (Blender menus stay as a submenu)",
        default=True)
    menu_set: bpy.props.EnumProperty(
        name="Menu Set", description="Maya menu set: which menus follow the common ones",
        items=lambda self, context: _menu_set_items(), default=0)
    show_status_line: bpy.props.BoolProperty(
        name="Status Line", description="Maya Status Line icons in the top bar", default=True)
    # Maya layout parity (docs/steps/step_49.md).
    maya_toolbox: bpy.props.BoolProperty(
        name="Maya Tool Box", description="3D View toolbars show Maya's Tool Box in every mode: Select, Lasso, "
                                          "Paint Select, Move, Rotate, Scale, the last other tool and quick layout "
                                          "buttons (other tools stay on keys, menus and the shelf)",
        default=True, update=_update_selection_wire)
    maya_dock_only: bpy.props.BoolProperty(
        name="Channel Box Dock Only", description="3D View sidebars show only the Maya dock (Channel Box / "
                                                  "Layer Editor, Attribute Editor), not Item / Tool / View tabs",
        default=True, update=_update_selection_wire)
    show_command_line: bpy.props.BoolProperty(
        name="Command Line", description="Python command line in the status bar", default=True)
    show_help_line: bpy.props.BoolProperty(
        name="Help Line", description="Maya-style help for the active tool in the status bar",
        default=True)

    # Marking menus and hotbox (docs/steps/step_9.md).
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
                                               "the current one (Maya's default, step 52)",
        default=True)

    # Shelf (docs/steps/step_12.md): current tab (factory file name or "USER:<name>").
    shelf_current: bpy.props.StringProperty(options={'HIDDEN'})

    # Scene concepts (docs/steps/step_10.md; docs/user_decisions.md #1, #2).
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
    # Maya manipSmartDuplicate 1 (research/maya/interaction.md:107, PREF:371-374).
    smart_duplicate: bpy.props.BoolProperty(
        name="Smart Duplicate", description="Shift+drag a Move/Rotate/Scale manipulator "
                                            "duplicates the selection and transforms the copy",
        default=True)
    # Maya manipSmartExtrude 1 (research/maya/interaction.md:107, PREF:371-374).
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
        box = layout.box()
        row = box.row()
        row.scale_y = 1.4
        row.operator("maya_kit.make_maya", icon='CHECKMARK')
        row.operator("maya_kit.revert_maya", icon='LOOP_BACK')
        row = box.row()
        row.prop(self, "maya_theme")
        row.prop(self, "maya_hide_splash")
        row.prop(self, "start_in_maya_layout")
        row = box.row()
        row.prop(self, "maya_density")
        from . import prefs_preset
        sub = row.row()
        sub.enabled = prefs_preset.font_available() or self.maya_font
        sub.prop(self, "maya_font")
        row.prop(self, "maya_wire")
        kcs = context.window_manager.keyconfigs
        row = layout.row()
        active = kcs.active.name if kcs.active else "-"
        row.label(text=f"Active keymap: {active}")
        if active != keymap.KEYCONFIG_NAME:
            row.operator("maya_kit.keymap_activate")
        col = layout.column()
        col.prop(self, "use_maya_navigation")
        col.prop(self, "lock_ortho_tumble")
        col.prop(self, "use_maya_undo")
        col.prop(self, "select_through")
        col.prop(self, "preselect_highlight")

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
        row.prop(self, "maya_panel_menus")
        row.prop(self, "menu_set", text="")
        row = box.row()
        row.prop(self, "marking_menu_style")
        row.prop(self, "hotbox_style", text="")
        row.prop(self, "hotbox_all_sets")
        row = box.row()
        row.prop(self, "show_status_line")
        row.prop(self, "show_command_line")
        row.prop(self, "show_help_line")
        row = box.row()
        row.prop(self, "maya_toolbox")
        row.prop(self, "maya_dock_only")
        row = box.row()
        row.prop(self, "maya_viewcube")
        row.prop(self, "maya_camera_names")
        row.prop(self, "maya_view_axis")
        row.prop(self, "maya_selection_wire")

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
