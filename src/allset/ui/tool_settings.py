# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya Tool Settings: Reset Tool and the dock's Maya sections (step 106).

Maya's Tool Settings window has the tool name, Reset Tool / Tool Help above the active tool's options
(, Maya-55). Since step 106 the kit's Tool Settings is a dock
left of the viewport (``ui/tool_dock.py``: a Properties editor on its Tool tab) that draws ``ALLSET_PT_tool_settings``:
the head row, then for the Move / Rotate / Scale tools Maya's sections in Maya's order with Maya's rows bound to kit
state (checked in Maya 2022: ; rows the kit can't do are greyed with a tooltip).
Other tools keep Blender's tool panels under the head row; the Reset Tool row is also prepended to
``VIEW3D_PT_active_tool`` for Blender's own Tool tab / popups.
Reset = the active tool's operator options back to their defaults (every operator of the tool's keymap) and, for
the Move / Rotate / Scale tools, Maya's factory tool options: axis World / Object / Object (
pivot_snap.md P12), the manipulator at the lead object's pivot (P11, step 59), Step Snap off and rotate step 15
degrees (S3), Smart Duplicate / Smart Extrude at their defaults (Move tool, step 22 / 26).
"""

import math

import bpy

from .manipulator import KINDS, SLOT, active_tool

# Maya factory axis per tool (pivot_snap.md P12); the same values tools/make_startup.py writes into the template.
MAYA_AXIS = {'TRANSLATE': 'GLOBAL', 'ROTATE': 'LOCAL', 'RESIZE': 'LOCAL'}
MAYA_PIVOT = 'ACTIVE_ELEMENT'
MAYA_ROTATE_STEP = math.radians(15.0)
# A tool whose keymap name can't be resolved still resets its main operator.
TOOL_OPERATORS = {"builtin.move": ("transform.translate",), "builtin.rotate": ("transform.rotate",),
                  "builtin.scale": ("transform.resize",)}


def tool_operators(context, tool):
    """Operator idnames of the tool's keymap (``ToolDef.keymap``), else ``TOOL_OPERATORS``."""
    ids = list(TOOL_OPERATORS.get(tool.idname, ()))
    try:
        from bl_ui.space_toolsystem_common import ToolSelectPanelHelper
        cls = ToolSelectPanelHelper._tool_class_from_space_type('VIEW_3D')
        item, _index = cls._tool_get_by_id(context, tool.idname)
    except (AttributeError, TypeError):
        item = None
    names = getattr(item, "keymap", None) or ()
    keymaps = context.window_manager.keyconfigs.active.keymaps if context.window_manager.keyconfigs.active else {}
    for name in names if isinstance(names, (tuple, list)) else ():
        km = keymaps.get(name) if isinstance(name, str) else None
        for kmi in (km.keymap_items if km else ()):
            if kmi.idname not in ids:
                ids.append(kmi.idname)
    return ids


def reset_operator_properties(props):
    """Unset every option: the operator uses its defaults again. Returns how many were set."""
    n = 0
    for prop in props.bl_rna.properties:
        name = prop.identifier
        if name == "rna_type" or prop.is_readonly:
            continue
        if props.is_property_set(name):
            props.property_unset(name)
            n += 1
    return n


def reset_maya_options(context, kind):
    """Maya's factory options of the Move / Rotate / Scale tool."""
    from ..operators import snap_align
    scene = context.scene
    ts = scene.tool_settings
    scene.transform_orientation_slots[SLOT[kind]].type = MAYA_AXIS[kind]
    ts.transform_pivot_point = MAYA_PIVOT
    snap_align.set_step_snap(ts, kind, 'OFF')
    if kind == 'ROTATE':
        ts.snap_angle_increment_3d = MAYA_ROTATE_STEP
    if kind == 'TRANSLATE':
        from .. import preferences
        prefs = preferences.get(context)
        for name in ("smart_duplicate", "smart_extrude"):
            setattr(prefs, name, prefs.bl_rna.properties[name].default)


def reset_tool(context):
    """Reset the active tool. Returns (tool idname, number of operator options unset) or None without a tool."""
    tool = active_tool(context)
    if tool is None:
        return None
    n = 0
    for idname in tool_operators(context, tool):
        try:
            props = tool.operator_properties(idname)
        except (RuntimeError, TypeError, ValueError):
            continue
        n += reset_operator_properties(props)
    kind = KINDS.get(tool.idname)
    if kind is not None:
        reset_maya_options(context, kind)
    return tool.idname, n


class ALLSET_OT_reset_tool(bpy.types.Operator):
    """Put the active tool's options back to their defaults (Maya Tool Settings: Reset Tool)"""
    bl_idname = "allset.reset_tool"
    bl_label = "Reset Tool"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return active_tool(context) is not None

    def execute(self, context):
        got = reset_tool(context)
        if got is None:
            return {'CANCELLED'}
        self.report({'INFO'}, f"Reset {got[0].split('.')[-1].replace('_', ' ').title()} tool")
        for area in context.screen.areas if context.screen else ():
            area.tag_redraw()
        return {'FINISHED'}


def draw_reset_row(self, context):
    """Prepended to the active tool panel: Maya's Reset Tool button above the tool's options (not in the Tool
    Settings dock, whose own head row has it)."""
    if active_tool(context) is None or in_dock(context):
        return
    self.layout.operator(ALLSET_OT_reset_tool.bl_idname, icon='LOOP_BACK')


# --- Tool Settings dock: Maya sections ------------------------------------
# Section order, default open state and rows checked in Maya 2022 (
# move / rotate / scale, *_ts_full0.png). Rows without kit state are greyed with a tooltip (TS_NOTICES).

TOOL_NAMES = {'TRANSLATE': "Move Tool", 'ROTATE': "Rotate Tool", 'RESIZE': "Scale Tool"}
SETTINGS = {'TRANSLATE': "Move Settings", 'ROTATE': "Rotate Settings", 'RESIZE': "Scale Settings"}
# (key, title, open by default, kinds that have it)
SECTIONS = (
    ("settings", None, True, ('TRANSLATE', 'ROTATE', 'RESIZE')),
    ("joint_orient", "Joint Orient Settings", False, ('TRANSLATE',)),
    ("move_snap", "Move Snap Settings", False, ('TRANSLATE',)),
    ("selection", "Common Selection Options", False, ('TRANSLATE', 'ROTATE', 'RESIZE')),
    ("soft", "Soft Selection", False, ('TRANSLATE', 'ROTATE', 'RESIZE')),
    ("symmetry", "Symmetry Settings", False, ('TRANSLATE', 'ROTATE', 'RESIZE')),
    ("smart_duplicate", "Smart Duplicate Settings", False, ('TRANSLATE', 'ROTATE', 'RESIZE')),
)
# Maya Rotate / Scale Center (rotate_ts / scale_ts) -> Blender pivot point (delegated: Default = the manipulator at
# the lead's pivot, the kit's Maya default MAYA_PIVOT; Object = each object's own pivot; Manip = where the component
# pivot edit put the manipulator, the 3D cursor (step 77); Selection = the selection's centre).
CENTERS = {'ROTATE': (("Default", 'ACTIVE_ELEMENT'), ("Object", 'INDIVIDUAL_ORIGINS'), ("Manip", 'CURSOR'),
                      ("Selection", 'BOUNDING_BOX_CENTER')),
           'RESIZE': (("Default", 'ACTIVE_ELEMENT'), ("Object", 'INDIVIDUAL_ORIGINS'), ("Manip", 'CURSOR'))}

TS = "Tool Settings"
TS_NOTICES = {
    f"{TS}/Tool Help": ("Blender's tool tooltips", "Hover a tool for its help; Blender's manual is under Help"),
    f"{TS}/Bake Pivot Orientation": ("Modify > Bake Pivot",
                                     "The kit keeps a turned pivot as the Maya Pivot orientation; bake it from the menu"),
    f"{TS}/Show Orientation Handle": ("always shown", "The kit's pivot edit always shows its orientation ring"),
    f"{TS}/Transform Constraint": ("Edge / Vertex Slide (G G)",
                                   "Blender's move has no edge / surface constraint; slide components with G twice"),
    f"{TS}/Tweak Mode": ("the Tweak select tool",
                         "Blender's Tweak tool (Q) drags the component under the mouse without selecting it first"),
    f"{TS}/Automatically Orient Joints": ("Skeleton > Orient Joint",
                                          "Bones are not re-oriented while they move; orient them afterwards"),
    f"{TS}/Retain component spacing": ("always on", "Blender snapping always keeps the selection's spacing"),
    f"{TS}/Snap to live polygon": ("Make Live", "Blender snaps to the live surface with the Face snap"),
    f"{TS}/Drag": ("Select Box / Lasso tools", "Blender has no paint-drag selection style for the Move tool"),
    f"{TS}/Automatic camera-based selection": ("Camera-based selection",
                                               "Turn camera-based selection on or off yourself"),
    f"{TS}/Highlight backfaces": ("X-ray (Alt+Z)", "Blender highlights only what it can select"),
    f"{TS}/Highlight affected": ("Soft Select falloff circle", "Blender draws the soft selection radius, not colours"),
    f"{TS}/Selection Constraint": ("Select > Select Loops / Linked", "No selection constraint in Blender"),
    f"{TS}/Geometry Type": ("Copy", "Shift+drag always makes a copy (Duplicate Special makes instances)"),
    f"{TS}/Modify Translation": ("off", "Blender's rotate never moves the objects' positions"),
    f"{TS}/Free Rotate": ("the white ring / trackball",
                          "Blender's rotate manipulator has the free trackball rotation built in"),
    f"{TS}/Prevent Negative Scale": ("off", "Blender lets scale go negative"),
}


def in_dock(context):
    """A Properties Tool tab that isn't a Maya panel's dock area (ui/maya_dock.py, step 116)."""
    space = getattr(context, "space_data", None)
    if space is None or space.type != 'PROPERTIES':
        return False
    from . import maya_dock
    return maya_dock.area_role(context) is None


def tool_kind(context):
    """'TRANSLATE' / 'ROTATE' / 'RESIZE' when the active tool has Maya sections (Move / Rotate / Scale)."""
    tool = active_tool(context)
    return KINDS.get(tool.idname) if tool is not None else None


def tool_label(context, tool):
    """(label, icon_value) of a tool as its toolbar button shows it."""
    kind = KINDS.get(tool.idname)
    try:
        from bl_ui.space_toolsystem_common import ToolSelectPanelHelper
        cls = ToolSelectPanelHelper._tool_class_from_space_type('VIEW_3D')
        item, _index = cls._tool_get_by_id(context, tool.idname)
        icon = ToolSelectPanelHelper._icon_value_from_icon_handle(item.icon) if item and item.icon else 0
        label = item.label if item else ""
    except (AttributeError, TypeError):
        label, icon = "", 0
    if kind is not None:
        label = TOOL_NAMES[kind]
    elif label and not label.endswith("Tool"):
        label += " Tool"
    return label or tool.idname.split(".")[-1].replace("_", " ").title(), icon


def _grey(layout, item, text="", check=None, icon=None):
    """A Maya row the kit can't do: shown greyed, its tooltip says why (TS_NOTICES)."""
    row = layout.row(align=True)
    row.enabled = False
    flat = check is not None or icon is not None
    if flat:
        row.alignment = 'LEFT'          # Maya check boxes: box and text from the left
    if icon is None:
        icon = 'NONE' if check is None else ('CHECKBOX_HLT' if check else 'CHECKBOX_DEHLT')
    row.operator("allset.menu_unavailable", text=text or item, icon=icon, emboss=not flat).item = f"{TS}/{item}"
    return row


def _labelled(layout, label):
    """Maya's label column (right-aligned text, then the control)."""
    split = layout.split(factor=0.42, align=True)
    left = split.row()
    left.alignment = 'RIGHT'
    left.label(text=label)
    return split.row(align=True)


def _check_op(layout, op, text, on, **props):
    row = layout.row(align=True)
    row.alignment = 'LEFT'
    o = row.operator(op, text=text, icon='CHECKBOX_HLT' if on else 'CHECKBOX_DEHLT', emboss=False)
    for k, v in props.items():
        setattr(o, k, v)
    return o


def draw_head(layout, context, tool):
    """Maya's Tool Settings head: tool icon + name, Reset Tool, Tool Help (c02_tool_settings_move_win1.png)."""
    label, icon = tool_label(context, tool)
    row = layout.row(align=True)
    name = row.row()
    if icon:
        name.label(text=label, icon_value=icon)
    else:
        name.label(text=label)
    btn = row.row(align=True)
    btn.operator(ALLSET_OT_reset_tool.bl_idname, text="Reset Tool")
    _grey(btn, "Tool Help")


def draw_settings(layout, context, kind):
    """Move / Rotate / Scale Settings (move_ts_full0.png rows)."""
    from ..operators import pivot_menu, snap_align
    scene = context.scene
    ts = scene.tool_settings
    _labelled(layout, "Axis Orientation:").prop(scene.transform_orientation_slots[SLOT[kind]], "type", text="")
    layout.separator(factor=0.5)
    row = _labelled(layout, "Pivot:")
    editing = pivot_menu.pivot_editing(context)
    row.operator("allset.pivot_toggle", text="Edit Pivot", depress=editing)
    if context.mode == 'OBJECT':
        row.operator("allset.reset_pivot", text="Reset")
    else:
        row.operator("allset.pivot_reset", text="Reset")
    col = _labelled(layout, "").column(align=True)
    for option, text in (("SNAP_POS", "Position"), ("SNAP_ORI", "Orientation"), ("PIN", "Pin Component Pivot")):
        _check_op(col, "allset.pivot_option", text, pivot_menu.option(option, context), option=option)
    _grey(col, "Bake Pivot Orientation", check=False)
    _grey(col, "Show Orientation Handle", check=True)
    if kind in CENTERS:
        row = _labelled(layout, "Rotate Center:" if kind == 'ROTATE' else "Scale Center:")
        grid = row.grid_flow(row_major=True, columns=2, even_columns=True, align=True)
        for text, value in CENTERS[kind]:
            op = grid.operator("wm.context_set_enum", text=text, depress=ts.transform_pivot_point == value)
            op.data_path, op.value = "scene.tool_settings.transform_pivot_point", value
        if kind == 'ROTATE':
            _grey(_labelled(layout, ""), "Modify Translation", check=False)
    layout.separator(factor=0.5)
    row = _labelled(layout, "Transform Constraint:")
    _grey(row, "Transform Constraint", text="Off")
    row = _labelled(layout, "Step Snap:")
    mode = snap_align.step_snap_mode(ts, kind)
    for m in ('OFF', 'RELATIVE', 'ABSOLUTE'):
        op = row.operator("allset.step_snap", text=m.title(), depress=mode == m)
        op.kind, op.mode = kind, m
    if kind == 'ROTATE':
        _labelled(layout, "").prop(ts, "snap_angle_increment_3d", text="Step")
    else:
        # Blender's increment is the grid step: 1 Maya unit in the Allset template (step 25).
        _labelled(layout, "").label(text="Step: one grid unit", icon='SNAP_INCREMENT')
    _labelled(layout, "Preserve Children:").prop(ts, "use_transform_skip_children", text="")
    _labelled(layout, "Preserve UVs:").prop(ts, "use_transform_correct_face_attributes", text="")
    _grey(_labelled(layout, "Tweak Mode:"), "Tweak Mode", text=" ", check=False)
    if kind == 'ROTATE':
        _grey(_labelled(layout, "Free Rotate:"), "Free Rotate", text=" ", check=True)
    if kind == 'RESIZE':
        _grey(_labelled(layout, "Prevent Negative Scale:"), "Prevent Negative Scale", text=" ", check=True)


def draw_selection(layout, context):
    """Common Selection Options (Marquee / Drag, camera-based selection, highlights, selection constraint)."""
    wm = context.window_manager
    row = _labelled(layout, "Selection Style:")
    row.label(text="Marquee", icon='RADIOBUT_ON')
    _labelled(layout, "").prop(wm, "allset_mtk_camera_based", text="Camera-based selection")
    _grey(_labelled(layout, ""), "Drag", icon='RADIOBUT_OFF')
    col = _labelled(layout, "").column(align=True)
    _grey(col, "Automatic camera-based selection", check=False)
    _grey(col, "Highlight backfaces", check=True)
    col.prop(wm, "allset_mtk_nearest", text="Highlight nearest component")
    _grey(col, "Highlight affected", check=False)
    _grey(_labelled(layout, "Selection Constraint:"), "Selection Constraint", text="Off")


def draw_symmetry_section(layout, context):
    from .status_line import draw_symmetry
    row = _labelled(layout, "Symmetry:")
    draw_symmetry(row, context)
    row.operator("allset.symmetry", text="Reset").mode = "OFF"


def draw_smart_duplicate(layout, context):
    from .. import preferences
    prefs = preferences.get(context)
    col = _labelled(layout, "").column(align=True)
    col.prop(prefs, "smart_extrude", text="Shift+Drag to Extrude Components")
    col.prop(prefs, "smart_duplicate", text="Shift+Drag to Duplicate Objects")
    _grey(_labelled(layout, "Geometry Type:"), "Geometry Type", text="Copy")


def draw_section(layout, context, key, kind):
    if key == "settings":
        draw_settings(layout, context, kind)
    elif key == "joint_orient":
        _grey(layout, "Automatically Orient Joints", check=False)
    elif key == "move_snap":
        _grey(_labelled(layout, ""), "Retain component spacing", check=True)
        _grey(_labelled(layout, "Snap to live polygon:"), "Snap to live polygon", text="Face center", check=False)
    elif key == "selection":
        draw_selection(layout, context)
    elif key == "soft":
        from .modeling_toolkit import draw_soft
        draw_soft(layout, context)
    elif key == "symmetry":
        draw_symmetry_section(layout, context)
    elif key == "smart_duplicate":
        draw_smart_duplicate(layout, context)


def sections(kind):
    """[(key, title, open)] of the tool kind, in Maya's order."""
    return [(key, title or SETTINGS[kind], is_open) for key, title, is_open, kinds in SECTIONS if kind in kinds]


def draw_dock(layout, context):
    tool = active_tool(context)
    if tool is None:
        layout.label(text="No tool settings in this mode")
        return
    draw_head(layout, context, tool)
    kind = KINDS.get(tool.idname)
    if kind is None:
        return    # Blender's own tool panels follow (dock_tabs hides them only for Move / Rotate / Scale)
    for key, title, is_open in sections(kind):
        header, body = layout.panel(f"allset_ts_{key}", default_closed=not is_open)
        header.label(text=title)
        if body is not None:
            draw_section(body.column(), context, key, kind)


class ALLSET_PT_tool_settings(bpy.types.Panel):
    """Maya Tool Settings (the Properties Tool tab of the dock, ui/tool_dock.py)"""
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Tool"
    bl_label = "Tool Settings"
    bl_options = {'HIDE_HEADER'}
    bl_order = -100

    @classmethod
    def poll(cls, context):
        return in_dock(context)    # never in a 3D View sidebar (the Maya dock there is the Channel Box / AE)

    def draw(self, context):
        from . import maya_dock, tool_dock
        if tool_dock.is_dock(context.area):     # the kit's dock (not a user's Properties editor): Maya's handle
            maya_dock.draw_handle(self.layout)
        draw_dock(self.layout, context)


def hides_blender_panels(context):
    """True in the Tool Settings dock while the Maya sections replace Blender's tool panels (dock_tabs)."""
    return in_dock(context) and tool_kind(context) is not None


classes = (ALLSET_OT_reset_tool, ALLSET_PT_tool_settings)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.VIEW3D_PT_active_tool.prepend(draw_reset_row)
    from . import notices
    notices.PANEL_NOTICES.update(TS_NOTICES)


def unregister():
    from . import notices
    for key in TS_NOTICES:
        notices.PANEL_NOTICES.pop(key, None)
    bpy.types.VIEW3D_PT_active_tool.remove(draw_reset_row)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
