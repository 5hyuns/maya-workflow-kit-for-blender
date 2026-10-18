# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya tangents and key edits for the Graph Editor toolbar and the Shift+S marking menu.

Maya's Graph Editor tangent buttons and ``buildKeyframeTangentMM`` act on the selected keys in the Graph Editor
and on the current-time keys of the selection anywhere else (``timeSliderSetTangent``,
 buildKeyframeTangentMM :284-571; ).
In Blender's Graph Editor the selected keys are the selected control points of the editable curves; elsewhere
``operators/time_keys`` acts on the Channel Box nodes (Time Slider range, else the current frame).

Shift+S = ``KeyTangentBinding``: hold + LMB opens the marking menu; a tap does nothing, like Maya.
"""

import bpy
from bpy.props import EnumProperty

from . import taphold, time_keys

KEY_ACTIONS = [(k, l, d) for k, l, d in time_keys.ACTIONS if k not in {"SNAP", "TANGENT"}]


def in_graph_editor(context):
    space = getattr(context, "space_data", None)
    return space is not None and space.type == 'GRAPH_EDITOR'


def selected_keys(context):
    """[(fcurve, [keyframe points])] selected in the Graph Editor (editable curves)."""
    out = []
    for fc in getattr(context, "editable_fcurves", None) or ():
        pts = [kp for kp in fc.keyframe_points if kp.select_control_point]
        if pts:
            out.append((fc, pts))
    return out


def tangent_selected(context, kind):
    n = 0
    for fc, pts in selected_keys(context):
        for kp in pts:
            time_keys.apply_tangent(kp, kind)
            n += 1
        fc.update()
    return n


def _redraw(context):
    for area in context.screen.areas if context.screen else ():
        if area.type in {'GRAPH_EDITOR', 'DOPESHEET_EDITOR', 'VIEW_3D'}:
            area.tag_redraw()


class MAYAKIT_OT_set_tangent(bpy.types.Operator):
    """Set the in and out tangents: the selected keys in the Graph Editor, else the selection's keys at the
    current time (Maya Graph Editor tangent buttons, Shift+S marking menu)"""
    bl_idname = "maya_kit.set_tangent"
    bl_label = "Set Tangent"
    bl_options = {'REGISTER', 'UNDO'}

    kind: EnumProperty(items=time_keys.TANGENT_ITEMS, name="Tangent")

    @classmethod
    def description(cls, context, props):
        interp, handle = time_keys.TANGENTS[props.kind]
        blender = " + ".join(x.replace("_", " ").title() for x in (interp, handle) if x)
        note = " (Blender has no Stepped Next)" if props.kind == "STEPPED_NEXT" else ""
        return f"{time_keys.TANGENT_LABELS[props.kind]} tangents = Blender {blender}{note}"

    def execute(self, context):
        if in_graph_editor(context):
            n = tangent_selected(context, self.kind)
        else:
            a, b = time_keys.time_range(context)
            n = time_keys.set_tangent(context, a, b, self.kind)
        if self.kind == "STEPPED_NEXT":
            self.report({'INFO'}, "Stepped Next isn't available in Blender: Stepped used")
        elif not n:
            self.report({'WARNING'}, "No keys selected" if in_graph_editor(context) else "No keys at this time")
        _redraw(context)
        return {'FINISHED'}


class MAYAKIT_OT_key_edit(bpy.types.Operator):
    """Edit keys: the selected keys in the Graph Editor, else the selection's keys at the current time
    (Maya Shift+S marking menu > Keys)"""
    bl_idname = "maya_kit.key_edit"
    bl_label = "Edit Keys"
    bl_options = {'REGISTER', 'UNDO'}

    action: EnumProperty(items=KEY_ACTIONS, name="Action")

    @classmethod
    def description(cls, context, props):
        return next(d for k, _l, d in KEY_ACTIONS if k == props.action)

    def execute(self, context):
        act = self.action
        if not in_graph_editor(context) or act in {"ADD_INBETWEEN", "REMOVE_INBETWEEN"}:
            try:
                return bpy.ops.maya_kit.time_keys(action=act)
            except RuntimeError:     # time_keys polls on a Channel Box node
                self.report({'WARNING'}, "Select an animated object")
                return {'CANCELLED'}
        if act in {"COPY", "CUT"}:
            bpy.ops.graph.copy()
        if act == "PASTE":
            bpy.ops.graph.paste()
        elif act in {"CUT", "DELETE"}:
            for fc, _pts in selected_keys(context):
                # one at a time: removing a point invalidates the references to the later ones
                while True:
                    kp = next((k for k in fc.keyframe_points if k.select_control_point), None)
                    if kp is None:
                        break
                    fc.keyframe_points.remove(kp)
                fc.update()
        elif act in {"TO_KEY", "TO_BREAKDOWN"}:
            for _fc, pts in selected_keys(context):
                for kp in pts:
                    kp.type = 'KEYFRAME' if act == "TO_KEY" else 'BREAKDOWN'
        _redraw(context)
        return {'FINISHED'}


# Graph Editor 1 / 2 / 3 = graphEditorSetViewMode 0 / 1 / 2 (Maya-150, Maya:
# 12992-13006). Blender has Normalize; a stacked view (each curve in its own band) isn't there: 2 = normalized + notice.
VIEW_MODES = (("ABSOLUTE", "Absolute", "Maya 1: curves at their values"),
              ("STACKED", "Stacked", "Maya 2: not in Blender, curves are normalized instead"),
              ("NORMALIZED", "Normalized", "Maya 3: curves scaled to -1..1"))
STACKED_NOTICE = "Stacked view isn't in Blender: curves are normalized (-1..1) instead"


class MAYAKIT_OT_graph_view_mode(bpy.types.Operator):
    """Absolute / Stacked / Normalized curve view (Maya Graph Editor 1 / 2 / 3)"""
    bl_idname = "maya_kit.graph_view_mode"
    bl_label = "Graph Editor View Mode"
    bl_options = {'REGISTER'}

    mode: EnumProperty(items=VIEW_MODES, name="Mode")

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space is not None and space.type == 'GRAPH_EDITOR'

    def execute(self, context):
        context.space_data.use_normalization = self.mode != "ABSOLUTE"
        if self.mode == "STACKED":
            self.report({'INFO'}, STACKED_NOTICE)
        if context.area is not None:
            context.area.tag_redraw()
        return {'FINISHED'}


class KeyTangentBinding(taphold.TapHoldBinding):
    """Shift+S: hold + LMB = the Keyframe / Tangent marking menu (buildKeyframeTangentMM); a tap does nothing."""
    name = "key_tangent"
    label = "Keyframe / Tangent Menu"

    def tap(self, context):
        pass

    def click(self, context, event):
        from ..marking import modal
        modal.open_menu("buildKeyframeTangentMM", 'LEFTMOUSE', (event.mouse_region_x, event.mouse_region_y))


classes = (MAYAKIT_OT_set_tangent, MAYAKIT_OT_key_edit, MAYAKIT_OT_graph_view_mode)


def register_bindings():
    taphold.register_binding(KeyTangentBinding())


def unregister_bindings():
    taphold.unregister_binding(KeyTangentBinding.name)
