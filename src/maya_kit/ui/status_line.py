# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya top bar (menu bar) and Status Line.

research/maya/ui_layout.md §4.1-4.2 (menu bar, Status Line groups, :170-217);
research/blender/api_limits.md #10 (:80-81); $S\startup\bl_ui\space_topbar.py:14-62.
Design: docs/steps/step_7.md 「계획」 1 and 3.

``TOPBAR_HT_upper_bar.draw_left`` / ``draw_right`` are swapped for Maya
versions while the add-on is enabled and put back on unregister; the
originals still run when the "Maya Menu Bar" preference is off. Maya has the
Status Line on its own row under the menus; one TOPBAR row can't hold both
(measured at 1600 px, docs/steps/step_7.md 「한 것」), so the Status Line is
drawn first in the tool header of the largest 3D View.
"""

import bpy
from bpy.props import EnumProperty

from . import menu_sets

# --- 3D View helpers ----------------------------------------------------------------

def main_view3d(screen=None):
    """(area, WINDOW region) of the largest 3D View in ``screen`` (or the active screen)."""
    screen = screen or bpy.context.screen
    best = None
    for area in (screen.areas if screen else ()):
        if area.type == 'VIEW_3D' and (best is None or area.width * area.height > best.width * best.height):
            best = area
    if best is None:
        return None, None
    return best, next((r for r in best.regions if r.type == 'WINDOW'), None)


def all_view3d_spaces():
    """Every 3D View space in every screen (Maya selection masks are global)."""
    for screen in bpy.data.screens:
        for area in screen.areas:
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    yield space


# --- selection masks (ui_layout.md:201-205) -------------------------------------------

# Maya object mask -> Blender SpaceView3D.show_object_select_<type>; None = no equivalent.
OBJECT_MASKS = (
    ("HANDLES", "Select by handle object type", 'RESTRICT_SELECT_OFF', None),
    ("JOINTS", "Select by joint object type (armatures)", 'OUTLINER_OB_ARMATURE', ("armature",)),
    ("CURVES", "Select by curve object type", 'OUTLINER_OB_CURVE', ("curve", "font", "curves")),
    ("SURFACES", "Select by surface object type (meshes, NURBS)", 'OUTLINER_OB_MESH',
     ("mesh", "surf", "meta", "pointcloud", "volume")),
    ("DEFORMERS", "Select by deformation object type (lattices)", 'OUTLINER_OB_LATTICE', ("lattice",)),
    ("DYNAMICS", "Select by dynamic object type", 'OUTLINER_OB_FORCE_FIELD', None),
    ("RENDERING", "Select by rendering object type (cameras, lights)", 'OUTLINER_OB_LIGHT',
     ("camera", "light")),
    ("MISC", "Select by miscellaneous object type (locators, empties)", 'OUTLINER_OB_EMPTY',
     ("empty", "speaker", "light_probe", "grease_pencil")),
)
_MASK_TYPES = {m[0]: m[3] for m in OBJECT_MASKS}


def mask_on(space, group):
    return all(getattr(space, f"show_object_select_{t}") for t in _MASK_TYPES[group])


def set_mask(group, value):
    for space in all_view3d_spaces():
        for t in _MASK_TYPES[group]:
            setattr(space, f"show_object_select_{t}", value)


class MAYAKIT_OT_select_mask(bpy.types.Operator):
    """Toggle whether this kind of object can be selected (all 3D Views)"""
    bl_idname = "maya_kit.select_mask"
    bl_label = "Selection Mask"
    bl_options = {'INTERNAL'}

    group: EnumProperty(items=[(m[0], m[0].title(), m[1]) for m in OBJECT_MASKS if m[3]])

    @classmethod
    def description(cls, context, props):
        return next(m[1] for m in OBJECT_MASKS if m[0] == props.group)

    def execute(self, context):
        area, _r = main_view3d(context.screen)
        spaces = [area.spaces.active] if area else list(all_view3d_spaces())[:1]
        if not spaces:
            return {'CANCELLED'}
        set_mask(self.group, not mask_on(spaces[0], self.group))
        return {'FINISHED'}


# --- selection mode (ui_layout.md:200) -----------------------------------------------

class MAYAKIT_OT_select_mode(bpy.types.Operator):
    """Maya selection mode: Object (object mode) or Component (edit mode)"""
    bl_idname = "maya_kit.select_mode"
    bl_label = "Selection Mode"
    bl_options = {'REGISTER', 'UNDO'}

    mode: EnumProperty(items=(("OBJECT", "Object", "Select by object type (object mode)"),
                              ("COMPONENT", "Component", "Select by component type (edit mode)")))

    @classmethod
    def description(cls, context, props):
        return {"OBJECT": "Select by object type (Object Mode)",
                "COMPONENT": "Select by component type (Edit Mode)"}[props.mode]

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        target = 'OBJECT' if self.mode == "OBJECT" else 'EDIT'
        if context.active_object.mode != target:
            bpy.ops.object.mode_set(mode=target)
        return {'FINISHED'}


# --- snapping (ui_layout.md:207; hold keys share these settings: operators/hold.py) ----

SNAPS = (
    ("GRID", "Snap to grids (hold X)", 'SNAP_GRID', {'GRID'}),
    ("CURVE", "Snap to curves (hold C)", 'SNAP_EDGE', {'EDGE'}),
    ("POINT", "Snap to points (hold V)", 'SNAP_VERTEX', {'VERTEX'}),
    ("PLANE", "Snap to view planes", 'VIEW_PERSPECTIVE', None),
    ("LIVE", "Snap to the surface under the cursor (Make Live)", 'SNAP_FACE', {'FACE_PROJECT'}),
)
_SNAP_ELEMENTS = {s[0]: s[3] for s in SNAPS}


def snap_on(ts, name):
    return ts.use_snap and _SNAP_ELEMENTS[name] <= set(ts.snap_elements)


def toggle_snap(ts, name):
    """Status Line snap button: add/remove its element; snapping off when none is left."""
    current = set(ts.snap_elements) if ts.use_snap else set()
    elements = _SNAP_ELEMENTS[name]
    new = current - elements if snap_on(ts, name) else current | elements
    if new:
        ts.snap_elements = new
        ts.use_snap = True
    else:
        ts.use_snap = False


class MAYAKIT_OT_snap_toggle(bpy.types.Operator):
    """Toggle a Maya snap mode"""
    bl_idname = "maya_kit.snap_toggle"
    bl_label = "Snap Toggle"
    bl_options = {'INTERNAL', 'UNDO'}

    snap: EnumProperty(items=[(s[0], s[0].title(), s[1]) for s in SNAPS if s[3]])

    @classmethod
    def description(cls, context, props):
        return next(s[1] for s in SNAPS if s[0] == props.snap)

    def execute(self, context):
        toggle_snap(context.scene.tool_settings, self.snap)
        return {'FINISHED'}


# --- symmetry (ui_layout.md:207 group 8; operators/symmetry.py, docs/steps/step_36.md) ------

class MAYAKIT_MT_symmetry(bpy.types.Menu):
    """Maya symmetry modes (Status Line ▾ list)"""
    bl_idname = "MAYAKIT_MT_symmetry"
    bl_label = "Symmetry"

    def draw(self, context):
        from ..operators import symmetry
        current = symmetry.mode_of(symmetry.state(context.scene))
        layout = self.layout
        for mode, text in symmetry.MODES:
            layout.operator("maya_kit.symmetry", text=text,
                            icon='RADIOBUT_ON' if mode == current else 'RADIOBUT_OFF').mode = mode


def draw_symmetry(layout, context):
    """▾ list with the mode text + a toggle that is blue (pressed) while symmetry is on.

    Maya: LMB ▾ = list, MMB = toggle, the text box turns blue when on (statusLine.mel:1909-1925,
    2941-2986). A Blender menu button has no MMB action, so the toggle is its own button.
    """
    from ..operators import symmetry
    sym = symmetry.state(context.scene)
    row = layout.row(align=True)
    row.operator("maya_kit.symmetry", text="", icon='MOD_MIRROR', depress=sym.on).mode = "TOGGLE"
    sub = row.row(align=True)
    sub.ui_units_x = 6
    sub.menu(MAYAKIT_MT_symmetry.bl_idname, text=symmetry.label(sym), icon='DOWNARROW_HLT')


TRANSFORM_TOOLS = ("builtin.move", "builtin.rotate", "builtin.scale", "builtin.transform",
                   "builtin.select", "builtin.select_box", "builtin.select_circle", "builtin.select_lasso")


def draw_tool_symmetry(self, context):
    """Maya Move/Rotate/Scale Tool Settings 「Symmetry Settings」 (edit mesh only)."""
    if context.mode != 'EDIT_MESH':
        return
    tool = context.workspace.tools.from_space_view3d_mode(context.mode, create=False)
    if tool is None or tool.idname not in TRANSFORM_TOOLS:
        return
    layout = self.layout
    layout.separator()
    layout.label(text="Symmetry Settings")
    draw_symmetry(layout, context)


# --- render (ui_layout.md:210) -----------------------------------------------------------

def _properties_area(screen):
    return next((a for a in (screen.areas if screen else ()) if a.type == 'PROPERTIES'), None)


def show_properties(screen, context_name):
    """Switch a Properties editor to a tab; False if the screen has none."""
    area = _properties_area(screen)
    if area is None:
        return False
    try:
        area.spaces.active.context = context_name
    except TypeError:  # tab not available (no active object etc.)
        return False
    return True


class MAYAKIT_OT_render_settings(bpy.types.Operator):
    """Open the render settings (Maya Render Settings window)"""
    bl_idname = "maya_kit.render_settings"
    bl_label = "Render Settings"

    def execute(self, context):
        if not show_properties(context.screen, 'RENDER'):
            # Maya's Render Settings is a window of its own; the MayaKit layout has no Properties
            # editor (step 49), so open one in a new window.
            return bpy.ops.maya_kit.open_editor(ui_type='PROPERTIES', tab='RENDER')
        return {'FINISHED'}


class MAYAKIT_OT_ipr_toggle(bpy.types.Operator):
    """IPR: interactive render in the main viewport (toggle Rendered shading)"""
    bl_idname = "maya_kit.ipr_toggle"
    bl_label = "IPR Render"

    def execute(self, context):
        area, _r = main_view3d(context.screen)
        if area is None:
            return {'CANCELLED'}
        shading = area.spaces.active.shading
        shading.type = 'SOLID' if shading.type == 'RENDERED' else 'RENDERED'
        return {'FINISHED'}


class MAYAKIT_OT_hypershade(bpy.types.Operator):
    """Hypershade: switch to the Shading workspace"""
    bl_idname = "maya_kit.hypershade"
    bl_label = "Hypershade"

    def execute(self, context):
        ws = bpy.data.workspaces.get("Shading")
        if ws is None:
            self.report({'WARNING'}, "No 'Shading' workspace in this file")
            return {'CANCELLED'}
        context.window.workspace = ws
        return {'FINISHED'}


# --- editor toggles (ui_layout.md:213-216) -----------------------------------------------

EDITORS = (
    ("ATTRIBUTE", "Show the Attribute Editor (the dock's AE, or a Properties editor's Object tab)", 'PROPERTIES'),
    ("TOOL_SETTINGS", "Show the Tool Settings of the active tool", 'TOOL_SETTINGS'),
    ("CHANNEL_BOX", "Show or hide the Channel Box / Layer Editor (3D View sidebar)", 'MENU_PANEL'),
)


def editor_shown(screen, editor):
    area, _r = main_view3d(screen)
    if editor == "ATTRIBUTE":
        props = _properties_area(screen)
        if props is None:   # the dock's Attribute Editor (step 49: no Properties column)
            return (area is not None and area.spaces.active.show_region_ui
                    and getattr(bpy.context.window_manager, "maya_kit_dock", "") == 'ATTRIBUTE_EDITOR')
        return props.spaces.active.context == 'OBJECT'
    if area is None or editor == "TOOL_SETTINGS":  # a popup, never "shown"
        return False
    return area.spaces.active.show_region_ui


class MAYAKIT_OT_editor_toggle(bpy.types.Operator):
    """Show or hide a Maya editor"""
    bl_idname = "maya_kit.editor_toggle"
    bl_label = "Toggle Editor"
    bl_options = {'INTERNAL'}

    editor: EnumProperty(items=[(e[0], e[0].title(), e[1]) for e in EDITORS])

    @classmethod
    def description(cls, context, props):
        return next(e[1] for e in EDITORS if e[0] == props.editor)

    def execute(self, context):
        screen = context.screen
        if self.editor == "ATTRIBUTE" and _properties_area(screen) is None:
            area, region = main_view3d(screen)
            if area is None:
                return {'CANCELLED'}
            with context.temp_override(window=context.window, area=area, region=region):
                return bpy.ops.maya_kit.ae_toggle()
        if self.editor == "ATTRIBUTE":
            if not show_properties(screen, 'OBJECT'):
                self.report({'WARNING'}, "No Properties editor (or no active object)")
                return {'CANCELLED'}
            return {'FINISHED'}
        area, region = main_view3d(screen)
        if area is None:
            return {'CANCELLED'}
        if self.editor == "TOOL_SETTINGS":
            # The sidebar Tool tab's panel as a popup (needs a 3D View context).
            with context.temp_override(window=context.window, area=area, region=region):
                bpy.ops.wm.call_panel(name="VIEW3D_PT_active_tool", keep_open=True)
        else:
            area.spaces.active.show_region_ui = not area.spaces.active.show_region_ui
        return {'FINISHED'}


# --- drawing --------------------------------------------------------------------

# Maya Status Line groups each start with an "openBar" collapse handle that hides the group
# (research/maya/ui_layout.md:194-195, statusLine.mel toggleFileIcons ... toggleInputField). Kept for the
# session only (Maya keeps them in optionVars; delegated).
GROUPS = (
    ("FILE", "File: New, Open, Save, Undo, Redo"),
    ("SELECT_MODE", "Selection mode: hierarchy, object, component"),
    ("MASKS", "Selection masks"),
    ("SNAP", "Snap toggles"),
    ("SYMMETRY", "Symmetry"),
    ("RENDER", "Render"),
    ("EDITORS", "Editor toggles"),
)
_collapsed = set()


class MAYAKIT_OT_status_group(bpy.types.Operator):
    """Show or hide this Status Line group (Maya collapse handle)"""
    bl_idname = "maya_kit.status_group"
    bl_label = "Status Line Group"
    bl_options = {'INTERNAL'}

    group: EnumProperty(items=[(g, g.replace("_", " ").title(), d) for g, d in GROUPS])

    @classmethod
    def description(cls, context, props):
        desc = next(d for g, d in GROUPS if g == props.group)
        return f"{'Show' if props.group in _collapsed else 'Hide'}: {desc}"

    def execute(self, context):
        _collapsed.symmetric_difference_update({self.group})
        for window in context.window_manager.windows:
            for area in window.screen.areas:
                area.tag_redraw()
        return {'FINISHED'}


def _group(layout, group):
    """The collapse handle of ``group``; True when the group's buttons should be drawn."""
    open_ = group not in _collapsed
    sub = layout.row(align=True)
    sub.ui_units_x = 0.6
    sub.operator(MAYAKIT_OT_status_group.bl_idname, text="", emboss=False,
                 icon='GRIP_V' if open_ else 'TRIA_RIGHT').group = group
    return open_


def draw_status_line(layout, context):
    """The Maya Status Line groups, left to right (ui_layout.md:196-217), each after its collapse handle."""
    screen = context.screen
    ts = context.scene.tool_settings
    area, _r = main_view3d(screen)
    space = area.spaces.active if area else None

    if _group(layout, "FILE"):
        row = layout.row(align=True)
        row.operator("wm.read_homefile", text="", icon='FILE_NEW')
        row.operator("wm.open_mainfile", text="", icon='FILE_FOLDER')
        row.operator("wm.save_mainfile", text="", icon='FILE_TICK')
        row = layout.row(align=True)
        row.operator("ed.undo", text="", icon='LOOP_BACK')
        row.operator("ed.redo", text="", icon='LOOP_FORWARDS')

    if _group(layout, "SELECT_MODE"):
        editing = context.mode != 'OBJECT' and context.mode.startswith('EDIT')
        row = layout.row(align=True)
        row.operator(menu_sets.MAYAKIT_OT_menu_unavailable.bl_idname, text="",
                     icon='OUTLINER_OB_GROUP_INSTANCE').item = "Status Line/Select by hierarchy"
        row.operator(MAYAKIT_OT_select_mode.bl_idname, text="", icon='OBJECT_DATAMODE',
                     depress=not editing).mode = "OBJECT"
        row.operator(MAYAKIT_OT_select_mode.bl_idname, text="", icon='EDITMODE_HLT',
                     depress=editing).mode = "COMPONENT"

    if _group(layout, "MASKS"):
        row = layout.row(align=True)
        if context.mode == 'EDIT_MESH':
            for i, icon in enumerate(('VERTEXSEL', 'EDGESEL', 'FACESEL')):
                row.prop(ts, "mesh_select_mode", index=i, text="", icon=icon)
        else:
            for group, _desc, icon, types in OBJECT_MASKS:
                if types is None:
                    row.operator(menu_sets.MAYAKIT_OT_menu_unavailable.bl_idname, text="",
                                 icon=icon).item = f"Status Line/{_desc}"
                else:
                    row.operator(MAYAKIT_OT_select_mask.bl_idname, text="", icon=icon,
                                 depress=bool(space) and mask_on(space, group)).group = group

    if _group(layout, "SNAP"):
        row = layout.row(align=True)
        for name, desc, icon, elements in SNAPS:
            if elements is None:
                row.operator(menu_sets.MAYAKIT_OT_menu_unavailable.bl_idname, text="",
                             icon=icon).item = f"Status Line/{desc}"
            else:
                row.operator(MAYAKIT_OT_snap_toggle.bl_idname, text="", icon=icon,
                             depress=snap_on(ts, name)).snap = name

    if _group(layout, "SYMMETRY"):
        draw_symmetry(layout, context)

    if _group(layout, "RENDER"):
        row = layout.row(align=True)
        row.operator("render.view_show", text="", icon='RENDER_RESULT')
        row.operator("render.render", text="", icon='RENDER_STILL')
        row.operator(MAYAKIT_OT_ipr_toggle.bl_idname, text="", icon='SHADING_RENDERED',
                     depress=bool(space) and space.shading.type == 'RENDERED')
        row.operator(MAYAKIT_OT_render_settings.bl_idname, text="", icon='OPTIONS')
        row.operator(MAYAKIT_OT_hypershade.bl_idname, text="", icon='NODE_MATERIAL')

    if _group(layout, "EDITORS"):
        row = layout.row(align=True)
        for editor, _desc, icon in EDITORS:
            row.operator(MAYAKIT_OT_editor_toggle.bl_idname, text="", icon=icon,
                         depress=editor_shown(screen, editor)).editor = editor


_orig = {}


def _maya_bar(context):
    from .. import preferences
    try:
        return preferences.get(context).maya_top_bar
    except KeyError:
        return False


def draw_left(self, context):
    if not _maya_bar(context):
        return _orig["draw_left"](self, context)
    layout = self.layout
    if context.area.show_menus:
        menu_sets.draw_menu_bar(layout.row(align=True), context)
    else:
        layout.menu(menu_sets.MAYAKIT_MT_menu_bar.bl_idname, text="", icon='COLLAPSEMENU')
    if context.screen.show_fullscreen:
        layout.separator()
        layout.operator("screen.back_to_previous", icon='SCREEN_BACK', text="Back to Previous")


def draw_right(self, context):
    if not _maya_bar(context):
        return _orig["draw_right"](self, context)
    layout = self.layout
    window = context.window
    if not context.screen.show_statusbar:  # as space_topbar.py:46-49
        layout.template_reports_banner()
        layout.template_running_jobs()
    # Workspace selector at the far right, as Maya's (ui_layout.md:217).
    # Kept narrow so the Maya menus fit (1600 px window: docs/steps/step_7.md 「한 것」).
    row = layout.row()
    row.ui_units_x = 6
    row.template_ID(window, "workspace")
    if len(bpy.data.scenes) > 1:  # Maya has one scene per file; show only when needed
        row = layout.row()
        row.ui_units_x = 6
        row.template_ID(window, "scene", new="scene.new")


def draw_tool_header(self, context):
    """Status Line at the start of the main 3D View's tool header row."""
    from .. import preferences
    try:
        if not preferences.get(context).show_status_line:
            return
    except KeyError:
        return
    area, _r = main_view3d(context.screen)
    if area is None or context.area != area:  # one Status Line, not one per 3D View
        return
    from .shelf import strip_area
    if strip_area(context.screen) is not None:  # drawn in the Maya strip (step 12)
        return
    draw_status_line(self.layout, context)
    self.layout.separator(type='LINE')


def patch_topbar():
    cls = bpy.types.TOPBAR_HT_upper_bar
    if not _orig:
        _orig["draw_left"] = cls.draw_left
        _orig["draw_right"] = cls.draw_right
    cls.draw_left = draw_left
    cls.draw_right = draw_right


def unpatch_topbar():
    cls = bpy.types.TOPBAR_HT_upper_bar
    if _orig:
        cls.draw_left = _orig.pop("draw_left")
        cls.draw_right = _orig.pop("draw_right")


classes = (MAYAKIT_OT_select_mask, MAYAKIT_OT_select_mode, MAYAKIT_OT_snap_toggle, MAYAKIT_MT_symmetry,
           MAYAKIT_OT_render_settings, MAYAKIT_OT_ipr_toggle, MAYAKIT_OT_hypershade,
           MAYAKIT_OT_editor_toggle, MAYAKIT_OT_status_group)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    patch_topbar()
    bpy.types.VIEW3D_HT_tool_header.prepend(draw_tool_header)
    bpy.types.VIEW3D_PT_active_tool.append(draw_tool_symmetry)


def unregister():
    bpy.types.VIEW3D_PT_active_tool.remove(draw_tool_symmetry)
    bpy.types.VIEW3D_HT_tool_header.remove(draw_tool_header)
    unpatch_topbar()
    _collapsed.clear()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
