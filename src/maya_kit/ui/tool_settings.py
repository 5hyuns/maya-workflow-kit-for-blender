# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya Tool Settings "Reset Tool".

Maya's Tool Settings window has Reset Tool / Tool Help buttons above the active tool's options
(, Maya-55). The kit's Tool Settings are Blender's active tool
panel (``VIEW3D_PT_active_tool``, the Status Line / hotbox Tool Settings popup), so a Reset Tool row is prepended to
it. Reset = the active tool's operator options back to their defaults (every operator of the tool's keymap) and, for
the Move / Rotate / Scale tools, Maya's factory tool options: axis World / Object / Object (
pivot_snap.md P12), the manipulator at the lead object's pivot (P11, step 59), Step Snap off and rotate step 15
degrees (S3), Smart Duplicate / Smart Extrude at their defaults (Move tool, step 22 / 26). Tool Help is not added
(Blender's tool tooltips and manual cover it, delegated).
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


class MAYAKIT_OT_reset_tool(bpy.types.Operator):
    """Put the active tool's options back to their defaults (Maya Tool Settings: Reset Tool)"""
    bl_idname = "maya_kit.reset_tool"
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
    """Prepended to the active tool panel: Maya's Reset Tool button above the tool's options."""
    if active_tool(context) is None:
        return
    self.layout.operator(MAYAKIT_OT_reset_tool.bl_idname, icon='LOOP_BACK')


classes = (MAYAKIT_OT_reset_tool,)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.VIEW3D_PT_active_tool.prepend(draw_reset_row)


def unregister():
    bpy.types.VIEW3D_PT_active_tool.remove(draw_reset_row)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
