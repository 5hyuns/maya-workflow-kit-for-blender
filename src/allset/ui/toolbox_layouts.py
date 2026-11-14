# SPDX-License-Identifier: GPL-3.0-or-later
"""The buttons under the Tool Box's tools (``ALLSET_PT_toolbox_layouts``): Maya's quick layouts (Single
Perspective, Four View; Front/Persp greyed), the Outliner toggle (docks an Outliner beside the column, or closes the
docked / floating one) and command Search in the main viewport. Registered by ``toolbox``."""

import bpy

from .. import i18n
from ..operators import view
from .toolbox_column import GAP_PX, OUTLINER_PX, _enabled, is_toolbox


# --- quick layouts (Maya 2022 Tool Box) ---------------------------------------------------

class ALLSET_OT_quick_layout(bpy.types.Operator):
    """Maya Tool Box quick layout button"""
    bl_idname = "allset.quick_layout"
    bl_label = "Quick Layout"
    bl_options = {'INTERNAL'}

    layout: bpy.props.EnumProperty(items=(
        ('SINGLE', "Single Perspective View", "One perspective view (Maya quick layout 1)"),
        ('FOUR', "Four View", "Top, perspective, front and side views (Maya quick layout 2)"),
        ('FRONT_PERSP', "Front/Persp", "Front and perspective views side by side (Maya quick layout 3): "
                                       "not available, a Blender 3D View splits only into four"),
    ))

    @classmethod
    @i18n.translated
    def description(cls, context, props):
        return {
            "SINGLE": "Single Perspective View", "FOUR": "Four View. " + view.FOUR_VIEW_NOTE,
            "FRONT_PERSP": "Front/Persp: not available (a Blender 3D View splits only into four)"}[props.layout]

    def execute(self, context):
        if self.layout == 'FRONT_PERSP':
            return {'CANCELLED'}
        from .panel_menus import main_region
        from .status_line import main_view3d
        area, _r = main_view3d(context.screen)
        if area is None:
            # no 3D View panel (the one panel left is a Graph Editor ...): the layout itself
            from . import four_view
            done = four_view.set_layout(context, context.window, self.layout == 'FOUR')
            return {'FINISHED'} if done else {'CANCELLED'}
        key = "LAYOUT_SINGLE" if self.layout == 'SINGLE' else "LAYOUT_FOUR"
        with context.temp_override(area=area, region=main_region(area)):
            return bpy.ops.allset.panel_set(key=key)


def outliner_areas(screen):
    return [a for a in (screen.areas if screen else ()) if a.type == 'OUTLINER']


def floating_outliners(context):
    """Other windows that hold only Outliners (Maya's floating Outliner)."""
    return [w for w in context.window_manager.windows
            if w != context.window and w.screen.areas and all(a.type == 'OUTLINER' for a in w.screen.areas)]


def outliner_shown(context):
    """True while the Tool Box Outliner button is on: an Outliner in this window or floating."""
    return bool(outliner_areas(context.screen)) or bool(floating_outliners(context))


def _beside_column(screen):
    """The largest area right of this screen's Tool Box column (where the layout's Outliner docks), or None."""
    column = next((a for a in screen.areas if a.type == 'VIEW_3D' and is_toolbox(a.spaces.active)), None)
    if column is None:
        return None
    edge = column.x + column.width
    near = [a for a in screen.areas if a != column and abs(a.x - edge) <= GAP_PX
            and a.y < column.y + column.height and column.y < a.y + a.height]
    return max(near, key=lambda a: a.width * a.height, default=None)


def dock_outliner(context, window):
    """Split the area right of the Tool Box column (without a column: the main 3D View, e.g. Blender's own layouts)
    and put a Maya Outliner on its left. The new area or None."""
    screen = window.screen
    area = _beside_column(screen)
    if area is None:
        from .status_line import main_view3d
        area = main_view3d(screen)[0]
    if area is None:
        return None
    region = next((r for r in area.regions if r.type == 'WINDOW'), None)
    scale = context.preferences.system.ui_scale or 1.0      # 0 in background
    factor = min(0.45, OUTLINER_PX * scale / max(area.width, 1))
    before = {a.as_pointer() for a in screen.areas}
    with context.temp_override(window=window, screen=screen, area=area, region=region):
        if bpy.ops.screen.area_split(direction='VERTICAL', factor=factor) != {'FINISHED'}:
            return None
    new = next((a for a in screen.areas if a.as_pointer() not in before), None)
    if new is None:
        return None
    new.ui_type = 'OUTLINER'
    from . import maya_outliner
    maya_outliner.setup(new.spaces.active)
    return new


def _close_windows_later(pointers):
    from .. import live_refs

    def tick():
        for ptr in pointers:
            win = live_refs.window(ptr)
            if win is not None:
                with bpy.context.temp_override(window=win):
                    bpy.ops.wm.window_close()
        return None
    bpy.app.timers.register(tick, first_interval=0.0)


class ALLSET_OT_toggle_outliner(bpy.types.Operator):
    """Show or hide the Outliner"""
    bl_idname = "allset.toggle_outliner"
    bl_label = "Outliner"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        window = context.window
        if window is None:
            return {'CANCELLED'}
        screen = window.screen
        docked = outliner_areas(screen)
        if docked:
            if bpy.app.background:      # screen.area_close hangs without a UI
                return {'CANCELLED'}
            area = docked[0]
            with context.temp_override(window=window, screen=screen, area=area):
                bpy.ops.screen.area_close()
            return {'FINISHED'}
        floating = floating_outliners(context)
        if floating:
            _close_windows_later([w.as_pointer() for w in floating])
            return {'FINISHED'}
        if dock_outliner(context, window) is not None:
            return {'FINISHED'}
        # no 3D View to dock beside (a maximized view ...): the Outliner opens in its own window
        return bpy.ops.allset.open_editor(ui_type='OUTLINER')


class ALLSET_OT_viewport_search(bpy.types.Operator):
    """Open Blender command search using the actual modeling viewport, not the tool strip."""
    bl_idname = "allset.viewport_search"
    bl_label = "Search Commands"
    bl_description = "Search Blender commands in the main modeling viewport (F3)"
    bl_options = {'INTERNAL'}

    def invoke(self, context, event):
        from .status_line import main_view3d
        area, region = main_view3d(context.screen)
        if area is None or region is None:
            self.report({'WARNING'}, "No modeling viewport found")
            return {'CANCELLED'}
        # Search uses its invocation context for poll and dispatch. The narrow
        # dedicated toolbox is itself a VIEW_3D but has no useful model region.
        with context.temp_override(window=context.window, area=area, region=region):
            return bpy.ops.wm.search_menu('INVOKE_DEFAULT')

    def execute(self, context):
        return self.invoke(context, None)


class ALLSET_PT_toolbox_layouts(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_label = "Quick Layouts"
    bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(cls, context):
        return _enabled(context)

    def draw(self, context):
        col = self.layout.column(align=True)
        col.scale_y = 1.75   # = the tool buttons (ToolSelectPanelHelper.draw_cls scale_y)
        # kit-drawn Maya layout icons (#23; Blender's icon until the glyph is made)
        from .kit_icons import button
        op = ALLSET_OT_quick_layout.bl_idname
        button(col, op, "layout:SINGLE", 'VIEW_PERSPECTIVE', text="").layout = 'SINGLE'
        button(col, op, "layout:FOUR", 'VIEW_ORTHO', text="").layout = 'FOUR'
        sub = col.row()
        sub.enabled = False   # Front/Persp needs a two-pane split: no Blender equivalent
        button(sub, op, "layout:FRONT_PERSP", 'SPLIT_VERTICAL', text="").layout = 'FRONT_PERSP'
        col.separator()
        # Maya's Outliner check box: shows / hides the Outliner (pressed while one is shown)
        button(col, ALLSET_OT_toggle_outliner.bl_idname, "layout:OUTLINER", 'OUTLINER', text="",
               depress=outliner_shown(context))
        # Maya 2022.1+: the Search icon under the layout / Outliner buttons, after a divider (Maya 2022.1 Tool Box);
        # it opens Blender's command search (Maya Ctrl+F = SearchEngine).
        col.separator()
        col.operator_context = 'INVOKE_DEFAULT'
        col.operator('allset.viewport_search', text='', icon='VIEWZOOM')
