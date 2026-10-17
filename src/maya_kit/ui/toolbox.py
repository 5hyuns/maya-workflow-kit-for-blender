# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya Tool Box: the 3D View toolbar shows Maya's tools in every mode (docs/steps/step_49.md).

Maya's Tool Box (research/maya/ui_layout.md:224-233, toolbox.mel:196-307) is a 40 px column left of the
Outliner: Select, Lasso, Paint Select, Move, Rotate, Scale, the last non-sacred tool, then quick layout
buttons and an Outliner toggle. Here:

- ``VIEW3D_PT_tools_active.draw`` is wrapped so that, while it draws, ``tools_from_context`` yields the
  Maya list (``maya_tools``). Only drawing is filtered: ``wm.tool_set_by_id`` looks tools up through
  ``tools_from_context`` too, so replacing ``_tools`` would stop the shelf / menus / keys from
  activating tools that are not in the Tool Box (Multi-Cut, Quad Draw, ...). Modes without the Maya
  tools (sculpt and paint modes) keep Blender's list.
- ``MAYAKIT_PT_toolbox_layouts`` adds the quick layout buttons under the tools.
- The MayaKit template has a Tool Box column: a narrow 3D View showing only its toolbar (``is_toolbox``),
  with every object type hidden in that view (nothing drawn behind the tools; box / lasso select there
  touch nothing). A click under the tools reaches that view's WINDOW region and ``view3d.select`` would
  still deselect everything (measured), so ``maya_kit.toolbox_guard`` sits in front of it in the
  "3D View" keymap. Its overlays are off, so the kit's own drawing (grid, view furniture, selection
  wire) skips it as well.
"""

import bpy
from bl_ui.space_toolsystem_toolbar import VIEW3D_PT_tools_active as TOOLBAR

from ..operators import tool_keys

# toolbox.mel:262-302 order: Select, Lasso, Paint Select, Move, Rotate, Scale.
MAYA_TOOLS = ("builtin.select_box", "builtin.select_lasso", "builtin.select_circle",
              "builtin.move", "builtin.rotate", "builtin.scale")

_saved = {}
_drawing = [False]


def _enabled(context):
    from .. import preferences
    try:
        return preferences.get(context).maya_toolbox
    except KeyError:
        return False


def is_toolbox(space):
    """True for the MayaKit template's Tool Box column (= tools/make_startup.py is_toolbox_space)."""
    return (space is not None and space.type == 'VIEW_3D' and space.show_region_toolbar
            and not space.show_region_header and not space.show_region_ui and not space.overlay.show_overlays)


def _flat(items):
    for item in items:
        if type(item) is tuple:
            yield from (i for i in item if i is not None)
        elif item is not None:
            yield item


def maya_tools(blender_items, mode):
    """The Tool Box for one mode from Blender's tool items (ToolDefs, groups, None), or None when the
    mode lacks the Maya tools. The last slot is the last non-sacred tool used in that mode (Maya
    $gNonSacredToolWidget; tool_keys.LAST, the Y key's memory)."""
    by_id = {t.idname: t for t in _flat(blender_items)}
    picked = [by_id[i] for i in MAYA_TOOLS if i in by_id]
    if not any(t.idname == "builtin.move" for t in picked):
        return None
    out = picked + [None]
    last = tool_keys.LAST.get(mode)
    if last in by_id and last not in MAYA_TOOLS:
        out.append(by_id[last])
    return out


def _tools_from_context(cls, context, mode=None):
    original = _saved["tools_from_context"].__func__
    if _drawing[0] and mode is None:
        maya = maya_tools(list(original(cls, context)), context.mode)
        if maya is not None:
            yield from maya
            return
    yield from original(cls, context, mode)


def _draw(self, context):
    _drawing[0] = _enabled(context)
    try:
        self.draw_cls(self.layout, context)
    finally:
        _drawing[0] = False


class MAYAKIT_OT_toolbox_guard(bpy.types.Operator):
    """Ignore clicks under the Tool Box column's tools (they would deselect everything)"""
    bl_idname = "maya_kit.toolbox_guard"
    bl_label = "Tool Box Click"
    bl_options = {'INTERNAL'}

    def invoke(self, context, event):
        return {'FINISHED'} if is_toolbox(context.space_data) else {'PASS_THROUGH'}


# --- column width -----------------------------------------------------------------------------

# Blender's toolbar is one 56 px column at scale 1 (UI_TOOLBAR_MARGIN + UI_TOOLBAR_COLUMN = 0.5 * 32 +
# 1.25 * 32, interface UI_interface.hh); Maya's Tool Box is 40 px (ui_layout.md:224). Area sizes don't
# follow the UI scale: the template's column fits the toolbar at the Maya density (effective scale 1.0,
# "Maya Density" preset). At a larger scale it is resized to one toolbar column when Blender lets
# screen.area_move run (its poll fails while the mouse is over a region, measured); until then the
# toolbar would be cut off, so the main view of that screen shows its own toolbar meanwhile.
TOOLBAR_PX = 56
_FIT_TICK = 0.5
_fallback = set()   # screens whose main view shows its toolbar because the column is too narrow


def column_width(context=None):
    return round(TOOLBAR_PX * (context or bpy.context).preferences.system.ui_scale)


def _move_edge(window, area, x, y, delta):
    with bpy.context.temp_override(window=window, screen=window.screen, area=area):
        if not bpy.ops.screen.area_move.poll():
            return False
        return bpy.ops.screen.area_move(x=x, y=y, delta=delta) == {'FINISHED'}


def fit_columns():
    """Tool Box column = one toolbar column at the current UI scale (or the main view's toolbar)."""
    from .status_line import main_view3d
    context = bpy.context
    want = column_width(context)
    for window in context.window_manager.windows:
        screen = window.screen
        column = next((a for a in screen.areas if a.type == 'VIEW_3D' and is_toolbox(a.spaces.active)), None)
        if column is None:
            continue
        if abs(column.width - want) > 1 and column.x + column.width < window.width - 2:
            _move_edge(window, column, column.x + column.width, column.y + column.height // 2,
                       want - column.width)
        narrow = column.width < want - 1
        main, _r = main_view3d(screen)
        if main is None or main == column:
            continue
        key = screen.name
        if narrow and key not in _fallback and not main.spaces.active.show_region_toolbar:
            main.spaces.active.show_region_toolbar = True
            _fallback.add(key)
        elif not narrow and key in _fallback:
            main.spaces.active.show_region_toolbar = False
            _fallback.discard(key)


def _fit_tick():
    try:
        fit_columns()
    except Exception:   # a timer that raises is dropped: keep it running
        pass
    return _FIT_TICK


@bpy.app.handlers.persistent
def _fit_after_load(*_args):
    if not bpy.app.background:
        bpy.app.timers.register(lambda: _fit_tick() and None, first_interval=0.0)


# --- quick layouts (toolbox.mel:209, :397-404) ---------------------------------------------

class MAYAKIT_OT_quick_layout(bpy.types.Operator):
    """Maya Tool Box quick layout button"""
    bl_idname = "maya_kit.quick_layout"
    bl_label = "Quick Layout"
    bl_options = {'INTERNAL'}

    layout: bpy.props.EnumProperty(items=(
        ('SINGLE', "Single Perspective View", "One perspective view (Maya quick layout 1)"),
        ('FOUR', "Four View", "Top, perspective, front and side views (Maya quick layout 2)"),
        ('FRONT_PERSP', "Front/Persp", "Front and perspective views side by side (Maya quick layout 3): "
                                       "not available, a Blender 3D View splits only into four"),
    ))

    @classmethod
    def description(cls, context, props):
        return {
            "SINGLE": "Single Perspective View", "FOUR": "Four View",
            "FRONT_PERSP": "Front/Persp: not available (a Blender 3D View splits only into four)"}[props.layout]

    def execute(self, context):
        if self.layout == 'FRONT_PERSP':
            return {'CANCELLED'}
        from .panel_menus import main_region
        from .status_line import main_view3d
        area, _r = main_view3d(context.screen)
        if area is None:
            return {'CANCELLED'}
        key = "LAYOUT_SINGLE" if self.layout == 'SINGLE' else "LAYOUT_FOUR"
        with context.temp_override(area=area, region=main_region(area)):
            return bpy.ops.maya_kit.panel_set(key=key)


class MAYAKIT_PT_toolbox_layouts(bpy.types.Panel):
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
        col.operator(MAYAKIT_OT_quick_layout.bl_idname, text="", icon='VIEW_PERSPECTIVE').layout = 'SINGLE'
        col.operator(MAYAKIT_OT_quick_layout.bl_idname, text="", icon='VIEW_ORTHO').layout = 'FOUR'
        sub = col.row()
        sub.enabled = False   # Front/Persp needs a two-pane split: no Blender equivalent
        sub.operator(MAYAKIT_OT_quick_layout.bl_idname, text="", icon='SPLIT_VERTICAL').layout = 'FRONT_PERSP'
        col.separator()
        col.operator("maya_kit.open_editor", text="", icon='OUTLINER').ui_type = 'OUTLINER'


classes = (MAYAKIT_OT_toolbox_guard, MAYAKIT_OT_quick_layout, MAYAKIT_PT_toolbox_layouts)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    _saved["tools_from_context"] = TOOLBAR.__dict__["tools_from_context"]
    _saved["draw"] = TOOLBAR.__dict__.get("draw")
    TOOLBAR.tools_from_context = classmethod(_tools_from_context)
    TOOLBAR.draw = _draw
    if not bpy.app.background and not bpy.app.timers.is_registered(_fit_tick):
        bpy.app.timers.register(_fit_tick, first_interval=_FIT_TICK, persistent=True)
    bpy.app.handlers.load_post.append(_fit_after_load)


def unregister():
    if _fit_after_load in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_fit_after_load)
    if bpy.app.timers.is_registered(_fit_tick):
        bpy.app.timers.unregister(_fit_tick)
    TOOLBAR.tools_from_context = _saved.pop("tools_from_context")
    draw = _saved.pop("draw")
    if draw is None:
        del TOOLBAR.draw
    else:
        TOOLBAR.draw = draw
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
