# SPDX-License-Identifier: GPL-3.0-or-later
"""Key batch 3: Maya keys that had no or a wrong binding.

Maya commands (, meanings from  annotations):
- Ctrl+M ToggleMainMenubar: the main menu bar folds into Blender's top-bar menu button (``area.show_menus`` of the
  top bar, which the kit menu bar already follows: ui/status_line.draw_left).
- Alt+B CycleBackgroundColor: Maya's whole cycle in every view, gradient included (step 120, see below).
- Alt+C ToggleColorFeedback (skin paint): the weight colours on / off (Weight Paint overlay opacity 1 <-> 0).
- u PaintOperationMarkingMenu: Maya's Artisan paint operations Replace / Add / Scale / Smooth (ui/paint_weights.py
  OPERATIONS) as a menu.
"""

import bpy
from bpy.props import EnumProperty

# Maya background (step 120, ). checked in a running Maya 2022 with factory prefs
# (, ): cycleBackgroundColor
# ($M/scripts/others/Maya) is one global state for every viewport -
#   gradient on        -> background 0 0 0, gradient off
#   background == 0    -> 0.36 (factory)
#   background <  0.5  -> 0.631
#   else               -> gradient on (backgroundTop #889db3 at the top, backgroundBottom #0d0d0d at the bottom)
# Values are display (sRGB) values: the factory viewport pixel is #5c5c5c = 0.36 ().
FLAT, LIGHT, BLACK = 0.36, 0.631, 0.0
GRADIENT_TOP = (0.535, 0.617, 0.702)
GRADIENT_BOTTOM = (0.052, 0.052, 0.052)
CYCLE = ("GREY", "LIGHT", "GRADIENT", "BLACK")


def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def linear_to_srgb(c):
    return c * 12.92 if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def theme_gradients():
    """The 3D View background gradient of the current theme (``THEME`` views draw it)."""
    return bpy.context.preferences.themes[0].view_3d.space.gradients


def gradient_allowed():
    """The gradient lives in the theme (Blender has no per-view gradient), so the kit only turns it on in its own
    Maya theme (switch / disable restore the user's theme); with the user's own theme the cycle skips it (delegated)."""
    from .. import theme
    return theme.is_applied()


def background_state(shading, gradients=None):
    """'GREY' / 'LIGHT' / 'GRADIENT' / 'BLACK' of a 3D View's shading, else the display value of its colour."""
    if shading.background_type == 'THEME':
        if gradients is not None and gradients.background_type != 'SINGLE_COLOR':
            return "GRADIENT"
        return "GREY"
    if shading.background_type != 'VIEWPORT':
        return FLAT                                  # world colour: read like Maya's flat background
    v = linear_to_srgb(shading.background_color[0])
    if abs(v - LIGHT) < 1e-3:
        return "LIGHT"
    if v < 1e-4:
        return "BLACK"
    return v


def next_state(state, gradient_ok=True):
    """Maya's rule (Maya) on a state or a display value."""
    if state == "GRADIENT":
        return "BLACK"
    value = {"GREY": FLAT, "LIGHT": LIGHT, "BLACK": BLACK}.get(state, state)
    if value == 0:
        return "GREY"
    if value < 0.5:
        return "LIGHT"
    return "GRADIENT" if gradient_ok else "BLACK"


def set_gradient(gradients, on, top=GRADIENT_TOP, bottom=GRADIENT_BOTTOM):
    """Theme gradient on (Maya's top / bottom colours) or off (the Maya theme's flat 0.36)."""
    if on:
        gradients.background_type = 'LINEAR'
        gradients.high_gradient = top              # Blender draws high_gradient at the top (checked, step 120)
        gradients.gradient = bottom
    else:
        gradients.background_type = 'SINGLE_COLOR'
        gradients.high_gradient = (FLAT, FLAT, FLAT)
        gradients.gradient = GRADIENT_BOTTOM


def set_shading(shading, state, color=None):
    if state in ("GREY", "GRADIENT"):
        shading.background_type = 'THEME'
    else:
        shading.background_type = 'VIEWPORT'
        rgb = color if color is not None else (LIGHT if state == "LIGHT" else BLACK,) * 3
        shading.background_color = tuple(srgb_to_linear(c) for c in rgb)


def view_spaces():
    """Every 3D View of the file (Maya's background is one global setting), the Tool Box column excepted."""
    from ..ui import toolbox
    for screen in bpy.data.screens:
        for area in screen.areas:
            for space in area.spaces:
                if space.type == 'VIEW_3D' and not toolbox.is_toolbox(space):
                    yield area, space


def apply_background(state, color=None, top=GRADIENT_TOP, bottom=GRADIENT_BOTTOM):
    """Put every 3D View in a Maya background state ('GREY' / 'LIGHT' / 'BLACK' / 'GRADIENT' / 'CUSTOM' + color)."""
    if gradient_allowed():
        set_gradient(theme_gradients(), state == "GRADIENT", top, bottom)
    for area, space in view_spaces():
        set_shading(space.shading, state, color)
        area.tag_redraw()


def cycle_background(shading):
    """Next Maya background (Alt+B) read from ``shading`` (the view under the mouse), applied to every view."""
    state = next_state(background_state(shading, theme_gradients()), gradient_allowed())
    apply_background(state)
    set_shading(shading, state)      # also when ``shading`` isn't a view (the scene's display shading in tests)
    return state


def reset_background():
    """Maya's factory background (flat 0.36) in every view: promotional / comparison shots use it (step 120)."""
    apply_background("GREY")


class ALLSET_OT_cycle_background(bpy.types.Operator):
    """Cycle the background color from dark to light (Maya Alt+B): grey, light grey, gradient, black"""
    bl_idname = "allset.cycle_background"
    bl_label = "Cycle Background Color"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space is not None and space.type == 'VIEW_3D'

    def execute(self, context):
        state = cycle_background(context.space_data.shading)
        self.report({'INFO'}, f"Background: {state.title()}")
        return {'FINISHED'}


def _dialog_values(op):
    shading = next((space.shading for _area, space in view_spaces()), None)
    gradients = theme_gradients()
    state = background_state(shading, gradients) if shading is not None else "GREY"
    op.gradient = state == "GRADIENT"
    if shading is not None and shading.background_type == 'VIEWPORT':
        op.background = tuple(linear_to_srgb(c) for c in shading.background_color)
    else:
        op.background = (FLAT,) * 3
    if op.gradient:
        op.gradient_top, op.gradient_bottom = tuple(gradients.high_gradient), tuple(gradients.gradient)


class ALLSET_OT_color_settings(bpy.types.Operator):
    """Viewport background colors (Maya Windows > Settings/Preferences > Color Settings: 3D Views Background,
    Gradient Top / Bottom, and Preferences > Display > Gradient background)"""
    bl_idname = "allset.color_settings"
    bl_label = "Color Settings"
    bl_options = {'REGISTER'}

    background: bpy.props.FloatVectorProperty(name="Background", subtype='COLOR_GAMMA', size=3, min=0.0, max=1.0,
                                              default=(FLAT,) * 3)
    gradient: bpy.props.BoolProperty(name="Gradient Background", default=False)
    gradient_top: bpy.props.FloatVectorProperty(name="Gradient Top", subtype='COLOR_GAMMA', size=3, min=0.0,
                                                max=1.0, default=GRADIENT_TOP)
    gradient_bottom: bpy.props.FloatVectorProperty(name="Gradient Bottom", subtype='COLOR_GAMMA', size=3,
                                                   min=0.0, max=1.0, default=GRADIENT_BOTTOM)

    def invoke(self, context, event):
        _dialog_values(self)
        return context.window_manager.invoke_props_dialog(self, title="Color Settings", confirm_text="Apply")

    def draw(self, context):
        col = self.layout.column()
        col.use_property_split = True
        col.label(text="3D Views")
        col.prop(self, "background")
        row = col.row()
        row.enabled = gradient_allowed()
        row.prop(self, "gradient")
        sub = col.column()
        sub.enabled = self.gradient and gradient_allowed()
        sub.prop(self, "gradient_top")
        sub.prop(self, "gradient_bottom")

    def execute(self, context):
        if self.gradient and gradient_allowed():
            apply_background("GRADIENT", top=tuple(self.gradient_top), bottom=tuple(self.gradient_bottom))
        elif all(abs(c - FLAT) < 1e-3 for c in self.background):
            apply_background("GREY")
        else:
            apply_background("CUSTOM", color=tuple(self.background))
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


classes = (ALLSET_OT_cycle_background, ALLSET_OT_color_settings, ALLSET_OT_main_menubar_toggle, ALLSET_OT_color_feedback,
           ALLSET_OT_paint_operation, ALLSET_MT_paint_operation)
