# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya keys without a Blender operator of their own.

- ``maya_kit.box_zoom`` (Ctrl+Alt+LMB drag): draw a box; left→right zooms in on it,
  right→left zooms out ().
- ``maya_kit.last_tool`` (Y): back to the last tool that is not Q/W/E/R/T, Maya's
  "non-sacred" tool (interaction.md:96). A timer remembers it per mode.
- ``maya_kit.menu_set`` (F2–F6): switch the Maya menu set (Maya-327).
"""

import bpy
import gpu
from bpy.props import EnumProperty
from gpu_extras.batch import batch_for_shader

# --- box zoom ------------------------------------------------------------------------------------

MIN_DRAG = 6  # px: a smaller box is a click, not a zoom


def zoom_direction(start_x, end_x):
    """Maya box zoom: dragging right zooms in, dragging left zooms out."""
    return 'OUT' if end_x < start_x else 'IN'


class MAYAKIT_OT_box_zoom(bpy.types.Operator):
    """Drag a box to zoom: left to right zooms in on it, right to left zooms out (Maya Ctrl+Alt+LMB)"""
    bl_idname = "maya_kit.box_zoom"
    bl_label = "Box Zoom"

    @classmethod
    def poll(cls, context):
        return context.region_data is not None and context.region is not None \
            and context.region.type == 'WINDOW'

    def invoke(self, context, event):
        self._start = (event.mouse_region_x, event.mouse_region_y)
        self._end = self._start
        self._button = event.type
        self._region = context.region
        self._handle = context.space_data.draw_handler_add(self._draw, (), 'WINDOW', 'POST_PIXEL')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def _draw(self):
        if bpy.context.region != self._region:
            return
        (x0, y0), (x1, y1) = self._start, self._end
        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'LINE_LOOP', {"pos": [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]})
        gpu.state.blend_set('ALPHA')
        shader.uniform_float("color", (1.0, 1.0, 1.0, 0.8))
        batch.draw(shader)
        gpu.state.blend_set('NONE')

    def _finish(self, context):
        context.space_data.draw_handler_remove(self._handle, 'WINDOW')
        self._region.tag_redraw()

    def modal(self, context, event):
        if event.type in {'MOUSEMOVE', 'INBETWEEN_MOUSEMOVE'}:
            self._end = (event.mouse_region_x, event.mouse_region_y)
            self._region.tag_redraw()
            return {'RUNNING_MODAL'}
        if event.type in {'ESC', 'RIGHTMOUSE'} and event.value == 'PRESS':
            self._finish(context)
            return {'CANCELLED'}
        if event.type == self._button and event.value == 'RELEASE':
            self._end = (event.mouse_region_x, event.mouse_region_y)
            self._finish(context)
            (x0, y0), (x1, y1) = self._start, self._end
            if abs(x1 - x0) < MIN_DRAG or abs(y1 - y0) < MIN_DRAG:
                return {'CANCELLED'}
            with context.temp_override(region=self._region):
                bpy.ops.view3d.zoom_border(xmin=min(x0, x1), xmax=max(x0, x1), ymin=min(y0, y1),
                                           ymax=max(y0, y1), wait_for_input=False,
                                           zoom_out=zoom_direction(x0, x1) == 'OUT')
            return {'FINISHED'}
        return {'RUNNING_MODAL'}


# --- Y: last non-sacred tool ----------------------------------------------------------------------

# Maya's sacred tools: Q select, W move, E rotate, R scale, T show manipulator.
SACRED_PREFIXES = ("builtin.select", "builtin.move", "builtin.rotate", "builtin.scale",
                   "builtin.transform")
_TICK = 0.25
LAST = {}   # mode -> tool idname


def is_sacred(idname):
    return idname.startswith(SACRED_PREFIXES)


def remember(mode, idname):
    if idname and not is_sacred(idname):
        LAST[mode] = idname


def _watch():
    try:
        context = bpy.context
        workspace = context.workspace
        if workspace is not None:
            tool = workspace.tools.from_space_view3d_mode(context.mode, create=False)
            remember(context.mode, tool.idname if tool else None)
    except (AttributeError, RuntimeError, ReferenceError):
        pass
    return _TICK


class MAYAKIT_OT_last_tool(bpy.types.Operator):
    """Go back to the last tool other than Select/Move/Rotate/Scale (Maya Y)"""
    bl_idname = "maya_kit.last_tool"
    bl_label = "Last Tool"

    def execute(self, context):
        tool = LAST.get(context.mode)
        if tool is None:
            self.report({'INFO'}, "No previous tool in this mode")
            return {'CANCELLED'}
        try:
            bpy.ops.wm.tool_set_by_id(name=tool, space_type='VIEW_3D')
        except RuntimeError as ex:
            self.report({'WARNING'}, str(ex).strip())
            return {'CANCELLED'}
        return {'FINISHED'}


# --- F2–F6: menu sets ------------------------------------------------------------------------------

MENU_SET_KEYS = (('F2', 'modelingMenuSet'), ('F3', 'riggingMenuSet'), ('F4', 'animationMenuSet'),
                 ('F5', 'dynamicsMenuSet'), ('F6', 'renderingMenuSet'))


def _set_items(self, context):
    from ..ui import menu_sets
    return menu_sets.SET_ITEMS


class MAYAKIT_OT_menu_set(bpy.types.Operator):
    """Switch the Maya menu set (Maya F2 Modeling, F3 Rigging, F4 Animation, F5 FX, F6 Rendering)"""
    bl_idname = "maya_kit.menu_set"
    bl_label = "Menu Set"

    set: EnumProperty(items=_set_items, name="Menu Set")

    def execute(self, context):
        from .. import preferences
        preferences.get(context).menu_set = self.set
        for window in context.window_manager.windows:
            for area in window.screen.areas:
                area.tag_redraw()
        from ..ui import status_line
        status_line.redraw_top_bars()   # the Maya menu bar is in the top bar, a global area (step 72)
        return {'FINISHED'}


class MAYAKIT_OT_toggle_sel_mode(bpy.types.Operator):
    """Toggle object / component selection (Maya F8, SelectToggleMode) with Maya's in-view message"""
    bl_idname = "maya_kit.toggle_sel_mode"
    bl_label = "Object/Component"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return bpy.ops.object.editmode_toggle.poll()

    def execute(self, context):
        result = bpy.ops.object.editmode_toggle()
        if 'FINISHED' not in result:
            return {'CANCELLED'}
        from ..ui import view_message
        # Maya Maya-30: a topCenter message naming the new mode and the key back.
        if context.mode == 'OBJECT':
            text = "Object selection <hl>on</hl>.\nF8 goes back to components."
        else:
            text = "Component selection <hl>on</hl>.\nF8 goes back to objects."
        view_message.show(context, text, 'TOP_CENTER')
        return {'FINISHED'}


classes = (MAYAKIT_OT_box_zoom, MAYAKIT_OT_last_tool, MAYAKIT_OT_menu_set, MAYAKIT_OT_toggle_sel_mode)


def register_timer():
    if not bpy.app.timers.is_registered(_watch):
        bpy.app.timers.register(_watch, first_interval=_TICK, persistent=True)  # survives file loads


def unregister_timer():
    if bpy.app.timers.is_registered(_watch):
        bpy.app.timers.unregister(_watch)
    LAST.clear()
