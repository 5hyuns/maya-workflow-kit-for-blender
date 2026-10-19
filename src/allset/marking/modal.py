# SPDX-License-Identifier: GPL-3.0-or-later
"""Modal operators: the marking menu engine and the hotbox (docs/steps/step_9.md 「계획」 2-4).

``allset.mm_engine``: one marking menu (``marking/menus.py``) drawn with the
GPU, driven by ``engine.Session``. ``allset.hotbox``: Space hold (menu rows,
centre and N/S/E/W zones); a quick tap toggles the pane (HotboxMenus.mel:244).
Plus the small operators the hotbox zone menus run.
"""

import json
import time
import traceback

import bpy
from bpy.props import EnumProperty, StringProperty

from ..operators import keystate
from ..ui import menu_data, menu_map, menu_sets
from . import draw, engine
from . import menus as mm

BUTTONS = (("RIGHTMOUSE", "RMB", ""), ("LEFTMOUSE", "LMB", ""), ("MIDDLEMOUSE", "MMB", ""))
MOUSE_BUTTONS = {"LEFTMOUSE", "RIGHTMOUSE", "MIDDLEMOUSE"}
_TIMER = 0.05


def _prefs(context):
    from .. import preferences
    return preferences.get(context)


def _params():
    return engine.Params().scaled(draw.ui_scale())


# --- running a picked item ------------------------------------------------------------

def poll_action(action):
    """Greyed out? Checked once per (sub)menu when it opens, not per redraw."""
    if action is None:
        return False
    if isinstance(action, mm.Sub):
        return not mm.is_unavailable(action)
    kind, target, _props = menu_map.normalize(action)
    if kind not in ("op", "v3d"):
        return True
    mod, name = target.split(".")
    try:
        return bool(getattr(getattr(bpy.ops, mod), name).poll())
    except (AttributeError, RuntimeError, KeyError):
        return False


def run_action(context, action, option=False, path=None):
    """Run a menu action like Maya runs the item (or its option box). An action with an option window
    (``operators/option_windows``) opens it as the option box, and a plain run uses its saved values (Maya runs
    a menu item with its option values); ``path`` = the Maya menu path, for windows tied to a path."""
    from ..operators import option_windows
    window = option_windows.find_path(path) if path else option_windows.find(action)
    if window is not None:
        if option:
            mod, name = window.idname.split(".")
            return getattr(getattr(bpy.ops, mod), name)('INVOKE_DEFAULT')
        if option_windows.saved(window.key) is not None:
            res = option_windows.run_saved(window, context)
            if isinstance(res, str):
                raise RuntimeError(res)
            return res
    kind, target, props = menu_map.normalize(action)
    if kind == "prop":     # a Maya check / radio item (step 104)
        return menu_sets.set_prop(context, target, props)
    if kind == "menu":
        return bpy.ops.wm.call_menu(name=target)
    if kind == "pie":
        return bpy.ops.wm.call_menu_pie(name=target)
    if kind == "tool":
        res = bpy.ops.allset.menu_tool(tool=target, edit=props["edit"])
        if option:  # tool + its settings (toolPropertyWindow)
            bpy.ops.allset.editor_toggle(editor='TOOL_SETTINGS', show=True)
        return res
    if kind == "v3d" and (context.area is None or context.area.type != 'VIEW_3D'):
        return bpy.ops.allset.menu_run(op=target, props=json.dumps(props))
    mod, name = target.split(".")
    op = getattr(getattr(bpy.ops, mod), name)
    if option and "option_box" in op.get_rna_type().properties:
        # the operator has its own Maya options window (invoke_props_dialog, step 63)
        return op('INVOKE_DEFAULT', option_box=True, **props)
    res = op('INVOKE_DEFAULT', **props)
    if option and res == {'FINISHED'}:
        # Maya's option box opens the command's settings: Blender's Adjust Last Operation.
        try:
            bpy.ops.screen.redo_last('INVOKE_DEFAULT')
        except RuntimeError:
            pass
    return res


# --- marking menu engine --------------------------------------------------------------

class ALLSET_OT_mm_engine(bpy.types.Operator):
    """Maya marking menu: drag in a direction and release, flick, or click"""
    bl_idname = "allset.mm_engine"
    bl_label = "Marking Menu"
    bl_options = {'INTERNAL'}

    menu: StringProperty(options={'SKIP_SAVE'})
    button: EnumProperty(items=BUTTONS, options={'SKIP_SAVE'})
    # Where the button went down (region pixels). Callers pass the press position: the
    # event a nested invoke gets is the window's latest state, which may already have
    # moved on (measured with simulated events in the step-9 GUI test).
    origin: bpy.props.IntVectorProperty(size=2, default=(-1, -1), options={'SKIP_SAVE'})

    def invoke(self, context, event):
        region = context.region
        if self.menu not in mm.MENUS or region is None or region.type != 'WINDOW':
            return {'CANCELLED'}
        if draw.ACTIVE:  # another menu/hotbox is up: never stack two
            return {'CANCELLED'}
        origin = tuple(self.origin) if self.origin[0] >= 0 else (event.mouse_region_x, event.mouse_region_y)
        menu = mm.MENUS[self.menu]
        target = getattr(context.window_manager, "allset_mm_target", "") or             (context.active_object.name if context.active_object else "")
        menu = mm.with_object_name(menu, target)
        # Drawn over the whole window like Maya's menus (step 52): bounds = the window's editors.
        bounds = draw.window_bounds(context.window, region)
        self._session = engine.Session(menu, origin, time.monotonic(),
                                       draw.measure, _params(), poll_action, bounds)
        self._region = region
        self._shown = False
        self._pending = None   # (button, result): click-mode pick waiting for the release
        draw.activate(context.window, region, session=self._session)
        self._timer = context.window_manager.event_timer_add(_TIMER, window=context.window)
        context.window_manager.modal_handler_add(self)
        draw.redraw()
        return {'RUNNING_MODAL'}

    def _cleanup(self, context):
        if getattr(self, "_timer", None) is not None:
            context.window_manager.event_timer_remove(self._timer)
            self._timer = None
        draw.redraw()
        draw.ACTIVE.clear()

    def _finish(self, context, result):
        self._cleanup(context)
        verb, item, option = result
        if verb != "RUN":
            return {'CANCELLED'}
        try:
            run_action(context, item.action, option)
        except RuntimeError as ex:
            self.report({'WARNING'}, str(ex).strip())
        return {'FINISHED'}

    def modal(self, context, event):
        s = self._session
        try:
            x, y, now = event.mouse_region_x, event.mouse_region_y, time.monotonic()
            res = None
            pending = self._pending
            if pending is not None:
                # Click mode picked on a press: run on that button's release, so a popup the
                # item opens (Assign Existing Material) doesn't get the release and pick its
                # first row (GUI step 29). Maya menu items also run on release.
                button, picked = pending
                released = event.type == button and event.value == 'RELEASE'
                if released or (event.type == 'TIMER' and keystate.is_down(button) is False):
                    self._pending = None
                    return self._finish(context, picked)
                return {'RUNNING_MODAL'}
            if event.type in {'MOUSEMOVE', 'INBETWEEN_MOUSEMOVE'}:
                s.move(x, y, now)
                draw.redraw()
            elif event.type == self.button and event.value == 'RELEASE':
                res = s.release(x, y, now)
                draw.redraw()
            elif event.type in MOUSE_BUTTONS and event.value == 'PRESS' and s.mode == "CLICK":
                res = s.click(x, y, now)
                if res is not None and res[0] == "RUN":
                    self._pending, res = (event.type, res), None
                    draw.redraw()
                    draw.ACTIVE.clear()   # the menu goes away now; the item runs on release
                draw.redraw()
            elif event.type == 'ESC' and event.value == 'PRESS':
                res = s.cancel()
            elif event.type == 'WINDOW_DEACTIVATE':
                res = s.cancel()
            elif event.type == 'TIMER':
                if s.mode == "PRESS" and keystate.is_down(self.button) is False:
                    res = s.release(*s.pos, now)  # the release went to someone else
                elif not self._shown and s.visible(now):
                    self._shown = True
                    draw.redraw()  # show after the delay without a mouse move
            if res is not None:
                return self._finish(context, res)
            return {'RUNNING_MODAL'}
        except Exception:
            traceback.print_exc()
            self._cleanup(context)
            return {'CANCELLED'}


def open_menu(menu_name, button, origin=None):
    """Engine or pie, per the "Marking Menu Style" preference (step 8 pies as fallback)."""
    from . import idname
    if _prefs(bpy.context).marking_menu_style == 'PIE':
        return bpy.ops.wm.call_menu_pie(name=idname(menu_name))
    kw = {"origin": origin} if origin is not None else {}
    return bpy.ops.allset.mm_engine('INVOKE_DEFAULT', menu=menu_name, button=button, **kw)


# --- hotbox ---------------------------------------------------------------------------

def hotbox_rows(context, area_type=None):
    """(rows above, cursor row sides, rows below) like Maya's hotbox (13_hotbox.png; HotboxMenus.mel:187-237):
    common menus (+ Cache, Help), the 3D View's panel menus, then the menu set rows (every set when
    Hotbox Controls > Show All Menu Sets is on, Maya's default; else the current one)."""
    prefs = _prefs(context)

    def row(names):
        return [(menu_sets.menu_idname(n), menu_data.MENUS[n][0]) for n in names if n in menu_data.MENUS]
    above = [row(menu_sets._SET_MENUS[menu_sets.COMMON_SET] + menu_sets._ALWAYS_MENUS)]
    if (area_type or (context.area.type if context.area else None)) == 'VIEW_3D':
        from ..ui import panel_menus
        above.append([(idname, label) for label, idname in panel_menus.BAR])
    sides = (("RECENT", "Recent Commands"), ("CONTROLS", "Hotbox Controls"))
    sets = [sid for sid, _l, _d in menu_sets.SET_ITEMS] if prefs.hotbox_all_sets else [prefs.menu_set]
    below = [r for r in (row(menu_sets._SET_MENUS.get(sid, ())) for sid in sets) if r]
    return above, sides, below


def pane_tap(context):
    """Space tap: 3D View four views <-> single (step 4), other editors maximize the pane."""
    if context.area is not None and context.area.type == 'VIEW_3D':
        bpy.ops.allset.toggle_quad_view()
    else:
        bpy.ops.screen.screen_full_area()


class ALLSET_OT_hotbox(bpy.types.Operator):
    """Maya hotbox: hold Space; click a menu name, or click a zone for its marking menu.
    A quick tap toggles the pane"""
    bl_idname = "allset.hotbox"
    bl_label = "Hotbox"
    bl_options = {'INTERNAL'}

    def invoke(self, context, event):
        region = context.region
        if event.is_repeat or region is None or region.type != 'WINDOW' or draw.ACTIVE:
            return {'CANCELLED'}
        prefs = _prefs(context)
        self._key = event.type
        self._t0 = time.monotonic()
        self._clicked = False
        self._region = region
        center = (event.mouse_region_x, event.mouse_region_y)
        above, sides, below = hotbox_rows(context)
        self._layout = engine.HotboxLayout(above, center, draw.measure, style=prefs.hotbox_style,
                                           scale=draw.ui_scale(), bounds=draw.window_bounds(context.window, region),
                                           below=below, side=sides, title="Allset")
        draw.activate(context.window, region, hotbox=self._layout, hover=None)
        self._timer = context.window_manager.event_timer_add(_TIMER, window=context.window)
        context.window_manager.modal_handler_add(self)
        draw.redraw()
        return {'RUNNING_MODAL'}

    def _cleanup(self, context):
        if self._timer is not None:
            context.window_manager.event_timer_remove(self._timer)
            self._timer = None
        draw.redraw()
        draw.ACTIVE.clear()

    def _release(self, context):
        self._cleanup(context)
        if engine.is_tap(self._t0, time.monotonic(), self._clicked):
            pane_tap(context)
        return {'FINISHED'}

    def modal(self, context, event):
        try:
            x, y = event.mouse_region_x, event.mouse_region_y
            if event.type == self._key:
                if event.value == 'RELEASE':
                    return self._release(context)
                return {'RUNNING_MODAL'}  # key repeat
            if event.type in {'MOUSEMOVE', 'INBETWEEN_MOUSEMOVE'}:
                hover = self._layout.label_at(x, y)
                if hover != draw.ACTIVE.get("hover"):
                    draw.ACTIVE["hover"] = hover
                    draw.redraw()
                return {'RUNNING_MODAL'}
            if event.type in MOUSE_BUTTONS and event.value == 'PRESS':
                self._clicked = True
                key = self._layout.label_at(x, y)
                if key is not None:
                    self._cleanup(context)
                    self._open_label(key)
                    return {'FINISHED'}
                zone = self._layout.zone(x, y)
                if zone is not None:
                    self._cleanup(context)  # the zone's marking menu takes over (delegated)
                    open_menu(mm.HOTBOX_ZONES[zone].name, event.type, (x, y))
                    return {'FINISHED'}
                return {'RUNNING_MODAL'}
            if event.type == 'ESC' and event.value == 'PRESS' or event.type == 'WINDOW_DEACTIVATE':
                self._cleanup(context)
                return {'CANCELLED'}
            if event.type == 'TIMER' and keystate.is_down(self._key) is False:
                return self._release(context)  # the release was eaten elsewhere
            return {'RUNNING_MODAL'}
        except Exception:
            traceback.print_exc()
            self._cleanup(context)
            return {'CANCELLED'}

    @staticmethod
    def _open_label(key):
        if key == "RECENT":
            bpy.ops.screen.repeat_history('INVOKE_DEFAULT')
        elif key == "CONTROLS":
            bpy.ops.wm.call_menu(name=ALLSET_MT_hotbox_controls.bl_idname)
        else:
            bpy.ops.wm.call_menu(name=key)


class ALLSET_MT_hotbox_controls(bpy.types.Menu):
    """Hotbox Controls (HotboxControlsMenu.mel:158-207): menu sets, rows, style"""
    bl_idname = "ALLSET_MT_hotbox_controls"
    bl_label = "Hotbox Controls"

    def draw(self, context):
        prefs = _prefs(context)
        layout = self.layout
        layout.prop(prefs, "menu_set", expand=True)
        layout.separator()
        layout.prop(prefs, "hotbox_all_sets")
        layout.prop(prefs, "hotbox_style", expand=True)
        layout.separator()
        layout.prop(prefs, "marking_menu_style", expand=True)


# --- hotbox zone actions -------------------------------------------------------------------

def _view3d(context):
    area = context.area
    if area is None:
        return None, None
    if area.type != 'VIEW_3D':
        area.ui_type = 'VIEW_3D'  # Maya switchModelView turns the pane into a model panel
    region = next((r for r in area.regions if r.type == 'WINDOW'), None)
    return area, region


_persp_views = {}  # area pointer -> (rotation, location, distance) of the last perspective view


class ALLSET_OT_hb_view(bpy.types.Operator):
    """Switch the pane to a Maya camera view (HotboxCenterMenu.mel:143-163)"""
    bl_idname = "allset.hb_view"
    bl_label = "Switch View"
    bl_options = {'INTERNAL'}

    view: EnumProperty(items=[(v, v.title(), "") for v in
                              ("PERSP", "TOP", "FRONT", "RIGHT", "LEFT", "BACK", "BOTTOM")])

    def execute(self, context):
        area, region = _view3d(context)
        if area is None:
            return {'CANCELLED'}
        rv3d = area.spaces.active.region_3d
        key = area.as_pointer()
        if self.view == "PERSP":
            saved = _persp_views.get(key)
            if saved:
                rv3d.view_rotation, rv3d.view_location, rv3d.view_distance = saved
            rv3d.view_perspective = 'PERSP'
            return {'FINISHED'}
        if rv3d.view_perspective == 'PERSP':
            _persp_views[key] = (rv3d.view_rotation.copy(), rv3d.view_location.copy(), rv3d.view_distance)
        with context.temp_override(area=area, region=region):
            bpy.ops.view3d.view_axis(type=self.view)
        return {'FINISHED'}


class ALLSET_OT_hb_pane(bpy.types.Operator):
    """Turn the pane under the hotbox into another editor (HotboxSouthMenu.mel:28-119)"""
    bl_idname = "allset.hb_pane"
    bl_label = "Switch Panel Type"
    bl_options = {'INTERNAL'}

    ui_type: StringProperty()

    def execute(self, context):
        if context.area is None:
            return {'CANCELLED'}
        try:
            context.area.ui_type = self.ui_type
        except TypeError:
            return {'CANCELLED'}
        return {'FINISHED'}


class ALLSET_OT_hb_single(bpy.types.Operator):
    """Single Perspective layout: leave four views"""
    bl_idname = "allset.hb_single"
    bl_label = "Single Perspective"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        area, region = _view3d(context)
        if area is None:
            return {'CANCELLED'}
        if area.spaces.active.region_quadviews:
            with context.temp_override(area=area, region=region):
                bpy.ops.screen.region_quadview()
        return {'FINISHED'}


class ALLSET_OT_hb_workspace(bpy.types.Operator):
    """Switch to a workspace (Maya panel layouts with Hypershade or Graph Editor)"""
    bl_idname = "allset.hb_workspace"
    bl_label = "Switch Layout"
    bl_options = {'INTERNAL'}

    name: StringProperty()

    def execute(self, context):
        ws = bpy.data.workspaces.get(self.name)
        if ws is None:
            self.report({'WARNING'}, f"No '{self.name}' workspace in this file")
            return {'CANCELLED'}
        context.window.workspace = ws
        return {'FINISHED'}


UI_ELEMENTS = ("HELP_LINE", "STATUS_LINE", "COMMAND_LINE", "CHANNEL_BOX", "ATTRIBUTE",
               "TOOL_SETTINGS", "TOOLBOX")
_PREF_ELEMENTS = {"HELP_LINE": "show_help_line", "STATUS_LINE": "show_status_line",
                  "COMMAND_LINE": "show_command_line"}


class ALLSET_OT_hb_ui(bpy.types.Operator):
    """Show or hide a Maya UI element (HotboxEastMenu.mel:26-90)"""
    bl_idname = "allset.hb_ui"
    bl_label = "Toggle UI Element"
    bl_options = {'INTERNAL'}

    element: EnumProperty(items=[(e, e.replace("_", " ").title(), "") for e in UI_ELEMENTS])

    def execute(self, context):
        if self.element in _PREF_ELEMENTS:
            prefs = _prefs(context)
            attr = _PREF_ELEMENTS[self.element]
            setattr(prefs, attr, not getattr(prefs, attr))
            return {'FINISHED'}
        if self.element == "TOOLBOX":
            from ..ui.status_line import main_view3d
            area, _r = main_view3d(context.screen)
            if area is None:
                return {'CANCELLED'}
            # Set from inside an operator (or via screen.region_toggle / wm.context_toggle) the
            # toolbar stayed visible in the GUI test; set right after the operator it works.
            space = area.spaces.active

            def toggle():
                space.show_region_toolbar = not space.show_region_toolbar
            bpy.app.timers.register(toggle, first_interval=0.0)
            return {'FINISHED'}
        return bpy.ops.allset.editor_toggle(editor=self.element)


# Exclusive selection-mask presets (Maya setSelectMode, menu_ChangeSelectionMask.mel).
MASK_PRESETS = {
    "ALL": None,
    "POLYGONS": {"mesh"},
    "NURBS": {"curve", "surf", "font", "curves"},
    "RENDERING": {"camera", "light", "light_probe"},
    "DEFORMATIONS": {"lattice", "armature"},
    "ANIMATION": {"armature", "empty"},
}
_ALL_TYPES = ("mesh", "curve", "surf", "meta", "font", "curves", "pointcloud", "volume", "armature",
              "lattice", "empty", "grease_pencil", "camera", "light", "speaker", "light_probe")


class ALLSET_OT_hb_mask(bpy.types.Operator):
    """Only this kind of object can be selected (Maya selection mask preset)"""
    bl_idname = "allset.hb_mask"
    bl_label = "Selection Mask Preset"
    bl_options = {'INTERNAL'}

    preset: EnumProperty(items=[(k, k.title(), "") for k in MASK_PRESETS])

    def execute(self, context):
        from ..ui.status_line import all_view3d_spaces
        keep = MASK_PRESETS[self.preset]
        for space in all_view3d_spaces():
            for t in _ALL_TYPES:
                setattr(space, f"show_object_select_{t}", keep is None or t in keep)
        return {'FINISHED'}


class ALLSET_OT_hb_style(bpy.types.Operator):
    """Hotbox style: zones and menu rows, zones only, or centre only (HotboxCenterMenu.mel:168-176)"""
    bl_idname = "allset.hb_style"
    bl_label = "Hotbox Style"
    bl_options = {'INTERNAL'}

    style: EnumProperty(items=(("ALL", "Zones and Menu Rows", ""), ("ZONES", "Zones Only", ""),
                               ("CENTER", "Center Zone Only", "")))

    def execute(self, context):
        _prefs(context).hotbox_style = self.style
        return {'FINISHED'}


classes = (ALLSET_OT_mm_engine, ALLSET_OT_hotbox, ALLSET_MT_hotbox_controls, ALLSET_OT_hb_view,
           ALLSET_OT_hb_pane, ALLSET_OT_hb_single, ALLSET_OT_hb_workspace, ALLSET_OT_hb_ui,
           ALLSET_OT_hb_mask, ALLSET_OT_hb_style)

