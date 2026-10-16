# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya Smart Duplicate: Shift+drag a Move/Rotate/Scale manipulator duplicates the
selection and the drag transforms the copies (research/maya/interaction.md:107,
``manipSmartDuplicate 1``, PREF:371-374).

Blender's transform gizmo is C (research/blender/api_limits.md:62). Its keymap
(``Generic Gizmo Maybe Drag``) runs ``gizmogroup.gizmo_tweak`` for any Shift; the
Maya keyconfig puts ``maya_kit.manip_duplicate`` in front of it
(keymap/maya_patches.py 21). This operator duplicates and always passes the event
on, so the gizmo then moves the selection, which is the copies. Plan:
docs/steps/step_22.md 「계획」.
"""

import bpy

from . import duplicate

# Object-mode tools that show the transform gizmo.
TOOLS = {"builtin.move", "builtin.rotate", "builtin.scale", "builtin.transform"}


def _smart_duplicate(context):
    from .. import preferences
    try:
        return preferences.get(context).smart_duplicate
    except KeyError:
        return True


def gizmo_shown(context):
    """The object transform gizmo is up: a transform tool, or the viewport's own
    object gizmos (Viewport Gizmos > Object Gizmos)."""
    tool = context.workspace.tools.from_space_view3d_mode('OBJECT', create=False)
    if tool is not None and tool.idname in TOOLS:
        return True
    v3d = context.space_data
    return bool(v3d and v3d.type == 'VIEW_3D' and v3d.show_gizmo and (
        v3d.show_gizmo_object_translate or v3d.show_gizmo_object_rotate
        or v3d.show_gizmo_object_scale))


def applies(context):
    return (context.mode == 'OBJECT' and bool(context.selected_objects)
            and _smart_duplicate(context) and gizmo_shown(context))


class MAYAKIT_OT_manip_duplicate(bpy.types.Operator):
    """Shift+drag a manipulator: duplicate the selection, then the drag moves, rotates
    or scales the copies (Maya Smart Duplicate)"""
    bl_idname = "maya_kit.manip_duplicate"
    bl_label = "Smart Duplicate"
    bl_options = {'INTERNAL'}

    def invoke(self, context, _event):
        return self.execute(context)

    def execute(self, context):
        if applies(context):
            duplicate.duplicate(context)
        # Always pass the event on: the gizmo's own tweak transforms the selection.
        return {'PASS_THROUGH'}


class MAYAKIT_OT_manip_option(bpy.types.Operator):
    """Toggle a manipulator option (W/E/R hold menu: Smart Duplicate)"""
    bl_idname = "maya_kit.manip_option"
    bl_label = "Manipulator Option"
    bl_options = {'INTERNAL'}

    option: bpy.props.EnumProperty(items=(('SMART_DUPLICATE', "Smart Duplicate", ""),))

    def execute(self, context):
        from .. import preferences
        prefs = preferences.get(context)
        prefs.smart_duplicate = not prefs.smart_duplicate
        self.report({'INFO'}, f"Smart Duplicate {'on' if prefs.smart_duplicate else 'off'}")
        return {'FINISHED'}


classes = (MAYAKIT_OT_manip_duplicate, MAYAKIT_OT_manip_option)
