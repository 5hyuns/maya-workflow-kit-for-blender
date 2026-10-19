# SPDX-License-Identifier: GPL-3.0-or-later
"""Key batch 3: Maya keys that had no or a wrong binding.

Maya commands (, meanings from  annotations):
- Ctrl+M ToggleMainMenubar: the main menu bar folds into Blender's top-bar menu button (``area.show_menus`` of the
  top bar, which the kit menu bar already follows: ui/status_line.draw_left).
- Alt+B CycleBackgroundColor: Maya's Maya goes default grey 0.36 -> 0.631 -> gradient -> black
  -> default. Blender's viewport gradient is a global theme setting, so the kit cycles per 3D View: theme
  (#5c5c5c = Maya's 0.36) -> 0.631 -> black -> theme (delegated: the gradient step is skipped).
- Alt+C ToggleColorFeedback (skin paint): the weight colours on / off (Weight Paint overlay opacity 1 <-> 0).
- u PaintOperationMarkingMenu: Maya's Artisan paint operations Replace / Add / Scale / Smooth (ui/paint_weights.py
  OPERATIONS) as a menu.
"""

import bpy
from bpy.props import EnumProperty

# Maya displayRGBColor background values (display / sRGB), Maya; the theme is Maya's 0.36.
LIGHT, BLACK = 0.631, 0.0
CYCLE = ("THEME", "LIGHT", "BLACK")


def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def background_state(shading):
    """'THEME' / 'LIGHT' / 'BLACK' / 'OTHER' of a 3D View's shading."""
    if shading.background_type == 'THEME':
        return "THEME"
    if shading.background_type != 'VIEWPORT':
        return "OTHER"
    v = shading.background_color[0]
    if abs(v - srgb_to_linear(LIGHT)) < 1e-3:
        return "LIGHT"
    if v < 1e-4:
        return "BLACK"
    return "OTHER"


def cycle_background(shading):
    """Next Maya background of a 3D View's shading (THEME -> LIGHT -> BLACK -> THEME). Returns the new state."""
    state = background_state(shading)
    nxt = CYCLE[(CYCLE.index(state) + 1) % len(CYCLE)] if state in CYCLE else "THEME"
    if nxt == "THEME":
        shading.background_type = 'THEME'
    else:
        shading.background_type = 'VIEWPORT'
        v = srgb_to_linear(LIGHT if nxt == "LIGHT" else BLACK)
        shading.background_color = (v, v, v)
    return nxt


class ALLSET_OT_cycle_background(bpy.types.Operator):
    """Cycle the viewport background from dark to light (Maya Alt+B)"""
    bl_idname = "allset.cycle_background"
    bl_label = "Cycle Background Color"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space is not None and space.type == 'VIEW_3D'

    def execute(self, context):
        state = cycle_background(context.space_data.shading)
        if context.area is not None:
            context.area.tag_redraw()
        self.report({'INFO'}, f"Background: {state.title()}")
        return {'FINISHED'}


def top_bar(context):
    """The window's top bar area (a global area, remembered while the kit menu bar draws: ui/status_line)."""
    from ..ui import status_line
    window = context.window
    return status_line._top_bars.get(window.as_pointer()) if window is not None else None


class ALLSET_OT_main_menubar_toggle(bpy.types.Operator):
    """Show or hide the main menu bar (Maya Ctrl+M): the menus fold into the top bar's menu button"""
    bl_idname = "allset.main_menubar_toggle"
    bl_label = "Toggle Main Menu Bar"
    bl_options = {'REGISTER'}

    def execute(self, context):
        area = top_bar(context)
        if area is None:
            return {'CANCELLED'}
        try:
            area.show_menus = not area.show_menus
            area.tag_redraw()
        except ReferenceError:
            return {'CANCELLED'}
        return {'FINISHED'}


class ALLSET_OT_color_feedback(bpy.types.Operator):
    """Show or hide the weight colours while painting skin weights (Maya Alt+C, Toggle Color Feedback)"""
    bl_idname = "allset.color_feedback"
    bl_label = "Toggle Color Feedback"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space is not None and space.type == 'VIEW_3D'

    def execute(self, context):
        overlay = context.space_data.overlay
        overlay.weight_paint_mode_opacity = 0.0 if overlay.weight_paint_mode_opacity > 0.0 else 1.0
        return {'FINISHED'}


PAINT_OPERATIONS = (("MIX", "Replace"), ("ADD", "Add"), ("MUL", "Scale"), ("SMOOTH", "Smooth"))


class ALLSET_OT_paint_operation(bpy.types.Operator):
    """Maya paint operation of the skin weight brush: Replace / Add / Scale (brush blend) or Smooth (Blur tool)"""
    bl_idname = "allset.paint_operation"
    bl_label = "Paint Operation"
    bl_options = {'REGISTER', 'UNDO'}

    operation: EnumProperty(items=[(k, label, "") for k, label in PAINT_OPERATIONS])

    @classmethod
    def poll(cls, context):
        return context.mode == 'PAINT_WEIGHT'

    def execute(self, context):
        if self.operation == "SMOOTH":
            return bpy.ops.wm.tool_set_by_id(name="builtin_brush.Blur")
        brush = context.tool_settings.weight_paint.brush
        if brush is None:
            return {'CANCELLED'}
        brush.blend = self.operation
        return {'FINISHED'}


class ALLSET_MT_paint_operation(bpy.types.Menu):
    """Maya Artisan paint operation marking menu (u)"""
    bl_idname = "ALLSET_MT_paint_operation"
    bl_label = "Paint Operation"

    def draw(self, context):
        brush = getattr(context.tool_settings.weight_paint, "brush", None)
        for key, label in PAINT_OPERATIONS:
            on = brush is not None and brush.blend == key
            self.layout.operator(ALLSET_OT_paint_operation.bl_idname, text=label,
                                 icon='RADIOBUT_ON' if on else 'RADIOBUT_OFF').operation = key


classes = (ALLSET_OT_cycle_background, ALLSET_OT_main_menubar_toggle, ALLSET_OT_color_feedback,
           ALLSET_OT_paint_operation, ALLSET_MT_paint_operation)
