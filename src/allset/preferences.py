# SPDX-License-Identifier: GPL-3.0-or-later
"""Add-on preferences (Preferences > Add-ons > Maya Workflow Kit).

Options backed by docs/user_decisions.md: Maya units (#1) and parent mode (#2)
from step 10. Only this add-on's own settings live here: since step 130 (#13) no option writes Blender's
preferences (the navigation / undo / panel / auto key / theme / splash / density / font / wire presets are gone).
"""

import bpy


class ALLSET_AddonPreferences(bpy.types.AddonPreferences):
    # Must equal the top-level package name: "bl_ext.<repo>.allset" as an
    # extension, "allset" as a legacy add-on.
    bl_idname = __package__

    # Set once "Maya" was activated automatically on first enable, so later
    # starts respect a different keymap the user picked (docs/steps/step_2.md).
    keymap_auto_activated: bpy.props.BoolProperty(options={'HIDDEN'})

    # Maya mode on/off (switch.py, docs/steps/step_60.md), kept across restarts. Off after install: enabling the
    # extension changes nothing until the user opts in (welcome dialog / button / switch; docs/steps/step_115.md).
    maya_mode: bpy.props.BoolProperty(name="Maya Mode", default=False, options={'HIDDEN'})
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
        description="In mesh edit mode (select and Move / Rotate / Scale tools), highlight the vertex, edge or face "
                    "under the mouse before clicking (Maya)",
        default=True)
    # Maya selectPrefPriorityMode "animation", ignoreSelectionPriority false (research/maya/interaction.md:74).
    select_priority: bpy.props.BoolProperty(
        name="Selection Priority",
        description="In object mode, a click picks IK handles, then joints (armatures), then curves before meshes "
                    "under the mouse, like Maya's selection priority",
        default=True)
    # First start (docs/steps/step_42.md): welcome dialog shown once.
    welcome_done: bpy.props.BoolProperty(options={'HIDDEN'})

    start_in_maya_layout: bpy.props.BoolProperty(
        name="Start in Maya Layout",
        description="When Blender starts without a file in Maya mode, open a new scene in the Maya layout",
        default=False)

    # Step 138 (#63): Maya's UI doesn't come from the scene file (research/maya/ui_layout.md:15-77): opening a file
    # shows the Maya layout (ui/scene_carry.py).
    maya_layout_on_open: bpy.props.BoolProperty(
        name="Keep Maya Layout When Opening Files",
        description="In Maya mode, a file opened in another layout is shown in the Maya layout (its own Maya layout "
                    "workspace when it has one). The file's other workspaces stay",
        default=True)

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

    # Graph Editor View > Snap Time To Selection (Maya optionVar snapTimeToSelection, default off; Alt+/ toggles it;
    # research/maya/re/graph_editor_keys.md, docs/steps/step_92.md).
    snap_time_to_selection: bpy.props.BoolProperty(
        name="Snap Time To Selection",
        description="Selecting keys in the Graph Editor moves the current time to the earliest selected key")
    # Graph Editor View > Auto Frame / Auto Frame Time / Curve Name (Maya factory: on / off / Never;
    # research/maya/screens/editors104/_editors104.json, ui/graph_view.py, step 150).
    graph_auto_frame: bpy.props.BoolProperty(
        name="Auto Frame", default=True,
        description="When the selection changes, the Graph Editor frames the curves it shows (Maya View > Auto Frame)")
    graph_auto_frame_time: bpy.props.BoolProperty(
        name="Auto Frame Time",
        description="When the selection changes, the Graph Editor frames the keys along the time axis only "
                    "(Maya View > Auto Frame Time; Auto Frame wins when both are on)")
    graph_curve_names: bpy.props.EnumProperty(
        name="Curve Name", default='NEVER',
        description="Write each curve's Maya name (pCube1.translateX) beside its last key in the Graph Editor",
        items=(('ALWAYS', "Always", "Name every curve"), ('NEVER', "Never", "No curve names"),
               ('ACTIVE', "Active Only", "Name the selected curves")))

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
                                                "Maya (lead light green, others white); in wireframe shading "
                                                "unselected objects are Maya's dark blue",
        default=True, update=_update_selection_wire)
    # Maya component colours in mesh edit mode (docs/steps/step_134_sel.md).
    maya_component_colors: bpy.props.BoolProperty(
        name="Component Colors", description="Mesh edit mode shows Maya's component colors: light blue edges, "
                                              "purple / yellow vertices, orange edges and stippled faces",
        default=True, update=_update_selection_wire)
    maya_view_axis: bpy.props.BoolProperty(
        name="View Axis", description="Maya axis triad in the bottom left of the view", default=True)
    # Maya in-view messages (inViewMessageEnable 1, research/maya/interaction.md:30; docs/steps/step_72.md).
    in_view_messages: bpy.props.BoolProperty(
        name="In-View Messages", description="Short fading messages in the view when you group, hide, toggle "
                                             "object/component selection (F8), soft select or Make Live, like Maya",
        default=True)
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

    # Maya project (operators/project.py, docs/steps/step_69.md): Blender has no projects, so the current
    # project folder and the Recent Projects list live here, like Maya keeps the workspace in its prefs.
    project_root: bpy.props.StringProperty(name="Current Project", subtype='DIR_PATH',
                                           description="Maya Workflow Kit project folder: file dialogs open in its scenes "
                                                       "folder, renders go to its images folder")
    recent_projects: bpy.props.StringProperty(options={'HIDDEN'})   # newline-separated, newest first
    # Maya option window values (operators/option_windows.py, step 103): Maya keeps them in optionVars.
    option_settings: bpy.props.StringProperty(options={'HIDDEN'})   # JSON {window key: {field: value}}

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
        layout = self.layout
        draw_about(layout)
        box = layout.box()
        row = box.row()
        row.scale_y = 1.6
        if self.maya_mode:
            row.operator("allset.switch_mode", text="Switch to Blender", icon='BLENDER').mode = 'BLENDER'
        else:
            # Nothing is changed until the user asks for it (step 115): the same dialog as the first start.
            row.operator("allset.welcome", text="Make Blender feel like Maya", icon='EVENT_M')
            row.operator("allset.switch_mode", text="Maya Mode Only").mode = 'MAYA'
        box.label(text="Ctrl+Alt+Shift+M or the Maya / Blender switch at the right of the top bar switches at any time. "
                       "Blender's own preferences are never changed.", icon='INFO')
        hint = undo_hint(context)
        if hint:
            box.label(text="Recommended setup", icon='LOOP_BACK')
            _wrapped(box, hint)
        if not self.maya_mode:
            return
        box = layout.box()
        row = box.row()
        row.scale_y = 1.4
        row.operator("allset.new_maya_scene", icon='FILE_NEW')
        row.operator("allset.maya_layout_here", icon='WORKSPACE')
        box.prop(self, "start_in_maya_layout")
        box.prop(self, "maya_layout_on_open")
        col = layout.column()
        col.prop(self, "lock_ortho_tumble")
        col.prop(self, "select_through")
        col.prop(self, "preselect_highlight")
        col.prop(self, "select_priority")

        box = layout.box()
        box.label(text="Scene Concepts")
        row = box.row()
        row.prop(self, "parent_mode")
        row.prop(self, "maya_naming")
        row = box.row()
        row.prop(self, "maya_units")
        row.prop(self, "smart_duplicate")
        row.prop(self, "smart_extrude")
        box.prop(self, "project_root")

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
        row = box.row()
        row.prop(self, "maya_viewcube")
        row.prop(self, "maya_camera_names")
        row.prop(self, "maya_view_axis")
        row.prop(self, "maya_selection_wire")
        row.prop(self, "maya_component_colors")
        box.prop(self, "in_view_messages")


# Step 111 (decision 12, docs/distribution/naming.md, docs/distribution/extensions_audit.md 「필수 고지문」)
# Undo depth (step 141, B6): Maya's undo queue is infinite (research/maya/interaction.md:222), Blender keeps 32 steps
# by default and the kit may not write Blender's preferences (step 130), so the kit only tells the user (delegated).
UNDO_RECOMMENDED = 256      # Blender's maximum
UNDO_HINT = ("Maya's undo is unlimited; Blender keeps {steps} steps. For long Maya-style sessions raise Edit > "
             "Preferences > System > Memory & Limits > Undo Steps to 256 (Blender's maximum).")


def undo_hint(context=None):
    """The undo-depth hint while Blender's Undo Steps is below 256, else None (read only, nothing is written)."""
    steps = (context or bpy.context).preferences.edit.undo_steps
    return UNDO_HINT.format(steps=steps) if steps < UNDO_RECOMMENDED else None


ABOUT = ("Other tools give you one piece at a time: a pivot, a keymap, a shelf, a theme. Maya Workflow Kit brings the whole Maya "
         "workflow into Blender in one install: hotbox and marking menus, Channel Box, Attribute Editor, Outliner, "
         "menu sets, shelves, option windows, Freeze / History concepts, centimetre units and pCube1-style naming.")
TRADEMARK_NOTICE = (
    "Autodesk and Maya are registered trademarks or trademarks of Autodesk, Inc., and/or its subsidiaries and/or "
    "affiliates in the USA and/or other countries. This project is an independent, free and open-source (GPL) "
    "extension for Blender. It is not affiliated with, endorsed by, sponsored by, or otherwise approved by Autodesk, "
    "Inc. or the Blender Foundation. It contains no Autodesk code, icons, MEL scripts or other Autodesk assets; "
    "references to Maya are solely to describe compatibility and the intended audience.")


def _wrapped(layout, text, width=110):
    line = ""
    col = layout.column(align=True)
    for word in text.split():
        if line and len(line) + 1 + len(word) > width:
            col.label(text=line)
            line = word
        else:
            line = f"{line} {word}" if line else word
    if line:
        col.label(text=line)


def draw_about(layout):
    """The About box of the preferences: what Maya Workflow Kit is, and the trademark notice."""
    box = layout.box()
    box.label(text="Maya Workflow Kit: the whole Maya workflow in Blender, in one install", icon='INFO')
    _wrapped(box, ABOUT)
    sub = box.column()
    sub.scale_y = 0.8
    sub.enabled = False
    _wrapped(sub, TRADEMARK_NOTICE)


_SET_ITEMS = []


def _menu_set_items():
    # Kept in a module list: Blender needs the enum item strings to stay referenced.
    if not _SET_ITEMS:
        from .ui import menu_sets
        _SET_ITEMS.extend(menu_sets.SET_ITEMS)
    return _SET_ITEMS


classes = (ALLSET_AddonPreferences,)

register, unregister = bpy.utils.register_classes_factory(classes)


def get(context=None):
    """Return this add-on's preferences instance."""
    context = context or bpy.context
    return context.preferences.addons[__package__].preferences
