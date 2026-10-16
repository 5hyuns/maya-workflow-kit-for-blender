# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya "tap = action, hold + click = menu" keys.

research/maya/interaction.md §0: on press Maya builds a marking menu on
LMB; if no menu was posted before release, the release runs the default
action (``a`` tap = FrameAll, ``buildSelectAllMM.mel``). Design:
docs/steps/step_3.md 「계획」 5.

API (used by the marking-menu step): subclass ``TapHoldBinding``, then
``register_binding(MyBinding())``; bind ``maya_kit.tap_hold`` with
``binding=<name>`` on the key's PRESS.
"""

import bpy

from . import keystate

_BINDINGS = {}


class TapHoldBinding:
    name = ""
    label = ""

    def tap(self, context):
        """Key released without a click while held."""

    def click(self, context, event):
        """LMB pressed while the key is held.

        Return 'DRAG' to receive ``drag()`` for mouse moves and ``drag_end()``
        on LMB release (the LMB release is consumed, not passed on).
        """

    def drag(self, context, event, start):
        """Mouse moved during a drag. ``start`` = (mouse_x, mouse_y) at click."""

    def drag_end(self, context):
        """LMB released after a drag."""

    def drag_cancel(self, context):
        """ESC / RMB during a drag: undo what the drag changed."""


def register_binding(binding):
    _BINDINGS[binding.name] = binding
    return binding


def unregister_binding(name):
    _BINDINGS.pop(name, None)


def get_binding(name):
    return _BINDINGS[name]


def binding_names():
    return sorted(_BINDINGS)


class MAYAKIT_OT_tap_hold(bpy.types.Operator):
    """Tap for the default action; hold and click for the menu (Maya)"""
    bl_idname = "maya_kit.tap_hold"
    bl_label = "Maya Tap/Hold Key"
    bl_options = {'INTERNAL'}

    binding: bpy.props.StringProperty(name="Binding")

    _POLL_INTERVAL = 0.05

    def invoke(self, context, event):
        if self.binding not in _BINDINGS:
            return {'CANCELLED'}
        if event.value != 'PRESS':
            return {'PASS_THROUGH'}
        self._b = _BINDINGS[self.binding]
        self._key = event.type
        self._used = False
        self._key_released = False
        self._drag_start = None
        self._timer = context.window_manager.event_timer_add(self._POLL_INTERVAL, window=context.window)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def _finish(self, context, released_cleanly):
        context.window_manager.event_timer_remove(self._timer)
        if self._drag_start is not None:
            self._b.drag_end(context)
        elif released_cleanly and not self._used:
            self._b.tap(context)
        return {'FINISHED'}

    def modal(self, context, event):
        # Drag in progress (key may or may not still be held).
        if self._drag_start is not None:
            if event.type == 'MOUSEMOVE':
                self._b.drag(context, event, self._drag_start)
                return {'RUNNING_MODAL'}
            if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
                self._b.drag_end(context)
                self._drag_start = None
                return self._finish(context, False) if self._key_released else {'RUNNING_MODAL'}
            if event.type in {'ESC', 'RIGHTMOUSE'} and event.value == 'PRESS':
                self._b.drag_cancel(context)
                self._drag_start = None
                return self._finish(context, False) if self._key_released else {'RUNNING_MODAL'}

        if event.type == self._key:
            if event.value == 'RELEASE':
                if self._drag_start is None:
                    return self._finish(context, released_cleanly=True)
                self._key_released = True  # finish after the drag ends
                return {'RUNNING_MODAL'}
            return {'RUNNING_MODAL'}  # key repeat

        if event.type == 'LEFTMOUSE' and event.value == 'PRESS' and self._drag_start is None:
            self._used = True
            if self._b.click(context, event) == 'DRAG':
                self._drag_start = (event.mouse_x, event.mouse_y)
            return {'RUNNING_MODAL'}

        if event.type == 'TIMER' and keystate.is_down(self._key) is False:
            if self._drag_start is None:
                # RELEASE swallowed elsewhere (e.g. by the menu we opened): no tap.
                return self._finish(context, released_cleanly=False)
        return {'PASS_THROUGH'}


# --- bindings of this step ----------------------------------------------------

def proportional_prop(context):
    """Soft select toggle: per-mode proportional editing property."""
    return "use_proportional_edit_objects" if context.mode == 'OBJECT' else "use_proportional_edit"


def radius_from_drag(start_size, dx):
    """B + LMB drag: doubles the radius every 100 px to the right."""
    return max(1e-4, start_size * 2.0 ** (dx / 100.0))


class SoftSelectBinding(TapHoldBinding):
    """B: tap toggles soft select, hold + LMB drag sets the radius (interaction.md:155-156)."""
    name = "soft_select"
    label = "Soft Select"

    def tap(self, context):
        ts = context.scene.tool_settings
        prop = proportional_prop(context)
        setattr(ts, prop, not getattr(ts, prop))

    def click(self, context, event):
        ts = context.scene.tool_settings
        self._start_size = ts.proportional_size
        self._prop = proportional_prop(context)
        self._was_on = getattr(ts, self._prop)
        setattr(ts, self._prop, True)
        self._header(context, ts.proportional_size)
        return 'DRAG'

    def drag(self, context, event, start):
        ts = context.scene.tool_settings
        ts.proportional_size = radius_from_drag(self._start_size, event.mouse_x - start[0])
        self._header(context, ts.proportional_size)

    def drag_end(self, context):
        self._header(context, None)

    def drag_cancel(self, context):
        ts = context.scene.tool_settings
        ts.proportional_size = self._start_size
        setattr(ts, self._prop, self._was_on)
        self._header(context, None)

    @staticmethod
    def _header(context, size):
        area = context.area
        if area is not None:
            area.header_text_set(None if size is None else f"Soft Select radius: {size:.3f}")


class SelectAllBinding(TapHoldBinding):
    """A: tap = frame all; hold + LMB = the Maya marking menu buildSelectAllMM
    (delete history, freeze; research/maya/interaction.md:194, docs/steps/step_10.md)."""
    name = "select_all"
    label = "Frame All / History Menu"

    def tap(self, context):
        from . import view   # Maya fit (fit factor 0.95, sidebar excluded), step 17
        area, region = context.area, context.region
        if area is not None and area.type == 'VIEW_3D' and region is not None and region.type == 'WINDOW':
            view.frame_region(context, area, region, selected=False)
        else:
            bpy.ops.view3d.view_all(center=False)

    def click(self, context, event):
        # Opened on the LMB press like Q/W/E/R: dragging and releasing LMB picks.
        from ..marking import modal
        modal.open_menu("buildSelectAllMM", 'LEFTMOUSE', (event.mouse_region_x, event.mouse_region_y))


class SpaceBinding(TapHoldBinding):
    """Space: tap = four views <-> single view (Maya pane maximize, interaction.md:248).
    Hold = hotbox (step 10)."""
    name = "space"
    label = "Four Views / Hotbox"

    def tap(self, context):
        if context.space_data is not None and context.space_data.type == 'VIEW_3D':
            bpy.ops.maya_kit.toggle_quad_view()


classes = (MAYAKIT_OT_tap_hold,)
_STEP_BINDINGS = (SoftSelectBinding, SelectAllBinding, SpaceBinding)


def register_bindings():
    for cls in _STEP_BINDINGS:
        register_binding(cls())


def unregister_bindings():
    for cls in _STEP_BINDINGS:
        unregister_binding(cls.name)
