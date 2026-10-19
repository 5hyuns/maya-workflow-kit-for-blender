# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya Tool Box: the 3D View toolbar shows Maya's tools in every mode.

Maya's Tool Box (, Maya-307) is a 40 px column left of the
Outliner: Select, Lasso, Paint Select, Move, Rotate, Scale, the last non-sacred tool, then quick layout
buttons and an Outliner toggle. Here:

- ``VIEW3D_PT_tools_active.draw`` is wrapped so that, while it draws, ``tools_from_context`` yields the
  Maya list (``maya_tools``). Only drawing is filtered: ``wm.tool_set_by_id`` looks tools up through
  ``tools_from_context`` too, so replacing ``_tools`` would stop the shelf / menus / keys from
  activating tools that are not in the Tool Box (Multi-Cut, Quad Draw, ...). Modes without the Maya
  tools (sculpt and paint modes) keep Blender's list.
- ``ALLSET_PT_toolbox_layouts`` adds the quick layout buttons under the tools.
- The Allset template has a Tool Box column: a narrow 3D View showing only its toolbar (``is_toolbox``),
  with every object type hidden in that view (nothing drawn behind the tools; box / lasso select there
  touch nothing). A click under the tools reaches that view's WINDOW region and ``view3d.select`` would
  still deselect everything (checked), so ``allset.toolbox_guard`` sits in front of it in the
  "3D View" keymap. Its overlays are off, so the kit's own drawing (grid, view furniture, selection
  wire) skips it as well.
"""

import bpy
from bl_ui.space_toolsystem_toolbar import VIEW3D_PT_tools_active as TOOLBAR

from ..operators import tool_keys

# Maya-302 order: Select, Lasso, Paint Select, Move, Rotate, Scale.
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
    """True for the Allset template's Tool Box column (= tools/make_startup.py is_toolbox_space). Not keyed on
    its overlays: a column whose overlays got turned on is still the column (``settle`` turns them off again;
    user report 2026-10-19, )."""
    return (space is not None and space.type == 'VIEW_3D' and space.show_region_toolbar
            and not space.show_region_header and not space.show_region_ui and not space.show_object_viewport_mesh)


def settle(space, prefs=None):
    """Keep the column a solid tool strip: overlays off (else the grid axis lines show through it) and a flat
    background in the toolbar's theme colour, so any width left beside the tools (the column is wider than one
    toolbar column until ALLSET_OT_fit_columns has fitted it) reads as part of the Tool Box, not as a viewport.
    Returns True when something changed."""
    prefs = prefs or bpy.context.preferences
    # the viewport background colour is scene linear, theme colours are display (sRGB) values (checked: an sRGB
    # 0.188 written as is showed as 119/255)
    rgb = tuple(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
                for c in tuple(prefs.themes[0].view_3d.space.button)[:3])
    shading = space.shading
    changed = False
    if space.overlay.show_overlays:
        space.overlay.show_overlays = False
        changed = True
    if shading.background_type != 'VIEWPORT':
        shading.background_type = 'VIEWPORT'
        changed = True
    if any(abs(a - b) > 1e-4 for a, b in zip(shading.background_color, rgb)):
        shading.background_color = rgb
        changed = True
    return changed


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


class ALLSET_OT_toolbox_guard(bpy.types.Operator):
    """Ignore clicks under the Tool Box column's tools (they would deselect everything)"""
    bl_idname = "allset.toolbox_guard"
    bl_label = "Tool Box Click"
    bl_options = {'INTERNAL'}

    def invoke(self, context, event):
        return {'FINISHED'} if is_toolbox(context.space_data) else {'PASS_THROUGH'}


# --- column width -----------------------------------------------------------------------------

# Blender's toolbar is one 56 px column at scale 1 (UI_TOOLBAR_MARGIN + UI_TOOLBAR_COLUMN = 0.5 * 32 +
# 1.25 * 32, interface UI_interface.hh); Maya's Tool Box is 40 px (ui_layout.md:224). Area sizes don't
# follow the UI scale: the template's column fits the toolbar at the Maya density (effective scale 1.0,
# "Maya Density" preset). At a larger scale it is resized to one toolbar column with screen.area_move,
# whose poll fails while the mouse is over any region (screen.active_region, checked): the column stayed
# empty at Windows 125 % without the density preset. So ALLSET_OT_fit_columns
# puts the cursor on the area edge for a moment (step 99, checked: the poll passes there), moves the edge and
# puts the cursor back; until then the main view of that screen shows its own toolbar.
TOOLBAR_PX = 56
SHELF_PX = 64        # = tools/make_startup.py SHELF_PX
OUTLINER_PX = 260    # Maya's narrow panel width () = the template Outliner at scale 1
_FIT_TICK = 0.5
_fallback = set()   # screens whose main view shows its toolbar because the column is too narrow


def column_width(context=None):
    return round(TOOLBAR_PX * (context or bpy.context).preferences.system.ui_scale)


MAX_WARPS = 3        # cursor-warp fits per screen and file load
_warps = {}          # screen name -> fits started since the last load
_running = [False]


def _move_edge(window, area, x, y, delta, edge, pending):
    """Move the edge through (x, y) by ``delta``; when the poll fails, remember ``edge`` (a window point in the
    gap between the areas) for ALLSET_OT_fit_columns."""
    with bpy.context.temp_override(window=window, screen=window.screen, area=area):
        if not bpy.ops.screen.area_move.poll():
            pending.setdefault(window.as_pointer(), (window, edge))
            return False
        return bpy.ops.screen.area_move(x=x, y=y, delta=delta) == {'FINISHED'}


def fit_columns(start_fit=True):
    """Tool Box column = one toolbar column at the current UI scale (or the main view's toolbar); the
    shelf row = 64 px times the UI scale. Returns {window pointer: (window, edge point)} of the moves whose
    poll failed; with ``start_fit`` a ALLSET_OT_fit_columns is started for the first of them."""
    from .status_line import main_view3d
    context = bpy.context
    want = column_width(context)
    pending = {}
    from .shelf import shelf_row_area
    for window in context.window_manager.windows:
        screen = window.screen
        # the Maya shelf row (tab row + icon row, 64 px at scale 1, step 51): grow it downwards
        row = shelf_row_area(screen)
        if row is not None and row.spaces.active.show_region_header:
            # step 113: the shelf row draws its tab strip in the WINDOW region (layouts saved before carry a header)
            with context.temp_override(window=window, screen=screen, area=row):
                row.spaces.active.show_region_header = False
        if row is not None:
            d = round(SHELF_PX * context.preferences.system.ui_scale) - row.height
            if abs(d) > 2:
                _move_edge(window, row, row.x + row.width // 2, row.y, -d,
                           (row.x + row.width // 2, row.y - 1), pending)
        column = next((a for a in screen.areas if a.type == 'VIEW_3D' and is_toolbox(a.spaces.active)), None)
        if column is None:
            continue
        if settle(column.spaces.active, context.preferences):
            column.tag_redraw()
        if abs(column.width - want) > 1 and column.x + column.width < window.width - 2:
            _move_edge(window, column, column.x + column.width, column.y + column.height // 2,
                       want - column.width, (column.x + column.width + 1, column.y + column.height // 2), pending)
        elif abs(column.width - want) <= 1:
            # the layout Outliner right of the column keeps Maya's panel width at this scale (widening the column
            # took its pixels; step 99)
            outl = next((a for a in screen.areas if a.type == 'OUTLINER' and abs(a.x - (column.x + column.width)) <= 4
                         and a.height >= column.height - 4), None)
            wo = round(OUTLINER_PX * context.preferences.system.ui_scale)
            if outl is not None and abs(outl.width - wo) > 2 and outl.x + outl.width < window.width - 2:
                _move_edge(window, outl, outl.x + outl.width, outl.y + outl.height // 2, wo - outl.width,
                           (outl.x + outl.width + 1, outl.y + outl.height // 2), pending)
        narrow = column.width < want - 1
        main, _r = main_view3d(screen)
        if main is None or main == column:
            continue
        key = screen.name
        # The property update re-inits the area through the context window: a timer runs with the last active
        # window, which may just have been closed (crash in WM_window_get_active_workspace, step 99) — so set it
        # with this window in the context.
        if narrow and key not in _fallback and not main.spaces.active.show_region_toolbar:
            with context.temp_override(window=window, screen=screen, area=main):
                main.spaces.active.show_region_toolbar = True
            _fallback.add(key)
        elif not narrow and key in _fallback:
            with context.temp_override(window=window, screen=screen, area=main):
                main.spaces.active.show_region_toolbar = False
            _fallback.discard(key)
    if start_fit and pending and not _running[0] and auto_warp():
        window, edge = next(iter(pending.values()))
        key = window.screen.name
        if _warps.get(key, 0) < MAX_WARPS:
            _warps[key] = _warps.get(key, 0) + 1
            with context.temp_override(window=window, screen=window.screen):
                bpy.ops.allset.fit_columns('INVOKE_DEFAULT', x=edge[0], y=edge[1])
    return pending


def auto_warp():
    """The cursor fit runs by itself except in event-simulated sessions (GUI tests, dogfood): they own the mouse,
    and a warp in the middle of a scripted step closes its menus. ALLSET_FIT_WARP=1 turns it on there."""
    import os
    return not bpy.app.use_event_simulate or os.environ.get("ALLSET_FIT_WARP") == "1"


def _warp(window, x, y):
    window.cursor_warp(x, y)
    if bpy.app.use_event_simulate:   # event simulation drops the OS mouse move a warp makes
        window.event_simulate(type='MOUSEMOVE', value='NOTHING', x=x, y=y)


class ALLSET_OT_fit_columns(bpy.types.Operator):
    """Resize the Tool Box column / shelf row: the cursor sits on the area edge (where screen.area_move polls)
    for a few timer ticks, then goes back"""
    bl_idname = "allset.fit_columns"
    bl_label = "Fit Maya Layout Columns"
    bl_options = {'INTERNAL'}

    x: bpy.props.IntProperty(options={'SKIP_SAVE'})
    y: bpy.props.IntProperty(options={'SKIP_SAVE'})

    def invoke(self, context, event):
        self._back = (event.mouse_x, event.mouse_y)
        self._n = 0
        self._window = context.window
        self._at = (self.x, self.y)
        _warp(context.window, self.x, self.y)
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.05, window=context.window)
        wm.modal_handler_add(self)
        _running[0] = True
        return {'RUNNING_MODAL'}

    def _finish(self, context, event):
        context.window_manager.event_timer_remove(self._timer)
        _running[0] = False
        if (event.mouse_x, event.mouse_y) == self._at:   # the user didn't move the mouse meanwhile
            _warp(self._window, *self._back)
        return {'FINISHED'}

    def modal(self, context, event):
        if event.type != 'TIMER':
            return {'PASS_THROUGH'}
        self._n += 1
        try:
            left = fit_columns(start_fit=False)
        except Exception:
            left = {}
        item = left.get(self._window.as_pointer())
        if item is None or self._n > 24:
            return self._finish(context, event)
        if item[1] != self._at:   # the next edge (column, then Outliner, then shelf row)
            if (event.mouse_x, event.mouse_y) != self._at:   # the user moved the mouse: stop here
                return self._finish(context, event)
            self._at = item[1]
            _warp(self._window, *item[1])
        return {'PASS_THROUGH'}


def _fit_tick():
    try:
        fit_columns()
    except Exception:   # a timer that raises is dropped: keep it running
        pass
    return _FIT_TICK


@bpy.app.handlers.persistent
def _fit_after_load(*_args):
    _warps.clear()
    if not bpy.app.background:
        bpy.app.timers.register(lambda: _fit_tick() and None, first_interval=0.0)


# --- quick layouts (Maya, :397-404) ---------------------------------------------

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
            return bpy.ops.allset.panel_set(key=key)


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
        col.operator(ALLSET_OT_quick_layout.bl_idname, text="", icon='VIEW_PERSPECTIVE').layout = 'SINGLE'
        col.operator(ALLSET_OT_quick_layout.bl_idname, text="", icon='VIEW_ORTHO').layout = 'FOUR'
        sub = col.row()
        sub.enabled = False   # Front/Persp needs a two-pane split: no Blender equivalent
        sub.operator(ALLSET_OT_quick_layout.bl_idname, text="", icon='SPLIT_VERTICAL').layout = 'FRONT_PERSP'
        col.separator()
        col.operator("allset.open_editor", text="", icon='OUTLINER').ui_type = 'OUTLINER'


classes = (ALLSET_OT_toolbox_guard, ALLSET_OT_fit_columns, ALLSET_OT_quick_layout, ALLSET_PT_toolbox_layouts)


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
    _running[0] = False
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
