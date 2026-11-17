# SPDX-License-Identifier: GPL-3.0-or-later
"""Drag a Shelf Editor button to a new place in Shelf Contents.

Press and hold a row's grip, move the mouse up/down (the button follows one row at a time), release to drop.
Esc while holding puts it back.

Blender's UI buttons only run operators on release, and its drag-toggle blocks all events while held, so neither
can drive a hold-drag. Instead a pass-through watcher modal runs in the Shelf Editor's region (started from the
grip's first draw). Window modal handlers see events before the UI, so on LEFTMOUSE PRESS it asks which button
is hovered (see _hovered_grip) and, if that's a grip, takes over until release.
"""

import re

import bpy
from bpy.props import IntProperty

from .shelf_editor_draft import _draft_buttons, _redraw, _set_message, _wm

ROW_PX = 20  # UIList DEFAULT row height in pixels at UI scale 1 (UI_UNIT_Y)
_state = {"window": 0, "pending": False}  # window: as_pointer() of the window whose watcher runs


class ALLSET_OT_shelf_editor_grip(bpy.types.Operator):
    """Press and hold, move the mouse up/down, release to drop the button there"""
    bl_idname = "allset.shelf_editor_grip"
    bl_label = "Drag Button"
    bl_options = {'INTERNAL'}

    index: IntProperty(options={'SKIP_SAVE'})

    def execute(self, context):
        return {'CANCELLED'}  # the watcher handles the press; a plain click does nothing


class ALLSET_OT_shelf_editor_drag_watch(bpy.types.Operator):
    bl_idname = "allset.shelf_editor_drag_watch"
    bl_label = "Shelf Editor Drag"
    bl_options = {'INTERNAL'}

    def invoke(self, context, event):
        self.dragging = False
        _state["window"] = context.window.as_pointer()
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        _state["window"] = 0  # window closed: the next grip draw starts a new watcher

    def _select(self, index):
        bpy.ops.allset.shelf_editor_select_button(index=index)

    def _place(self, context, target):
        order = self.original[:self.start] + self.original[self.start + 1:]
        order.insert(target, self.original[self.start])
        self.buttons[:] = order  # in place: the draft holds this same list
        self.current = target
        self._select(target)

    def _begin(self, context, event):
        index = _hovered_grip(context)
        if index is None:
            return False
        self.buttons = _draft_buttons(_wm(context).allset_se_shelf)
        self.start = index
        if not self.buttons or not 0 <= self.start < len(self.buttons):
            return False
        self.original = list(self.buttons)
        self.start_y = event.mouse_y
        self.row_px = ROW_PX * context.preferences.system.ui_scale
        self.current = self.start
        self.dragging = True
        self._select(self.start)
        _set_message(context, "Release to drop the button here (Esc puts it back)")
        return True

    def _end(self, context):
        self.dragging = False
        _set_message(context, "")
        _redraw(context)

    def modal(self, context, event):
        try:
            return self._modal(context, event)
        except Exception as error:  # any error would drop the handler silently; free the slot and say why
            _state["window"] = 0
            print("Shelf Editor drag stopped:", repr(error))
            _set_message(context, "")
            return {'CANCELLED', 'PASS_THROUGH'}

    def _modal(self, context, event):
        if _state["window"] != context.window.as_pointer():
            return {'CANCELLED', 'PASS_THROUGH'}  # replaced by a newer watcher
        if not self.dragging:
            if event.type == 'LEFTMOUSE' and event.value == 'PRESS' and self._begin(context, event):
                return {'RUNNING_MODAL'}
            return {'PASS_THROUGH'}
        if event.type == 'MOUSEMOVE':
            steps = round((self.start_y - event.mouse_y) / self.row_px)  # mouse down = later row
            target = max(0, min(len(self.original) - 1, self.start + steps))
            if target != self.current:
                self._place(context, target)
        elif event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            self._end(context)
        elif event.type == 'ESC' and event.value == 'PRESS':
            self._place(context, self.start)
            self._end(context)
        return {'RUNNING_MODAL'}


_GRIP_CALL = re.compile(r"bpy\.ops\.allset\.shelf_editor_grip\(index=(-?\d+)\)")


def _hovered_grip(context):
    """Row index of the grip under the mouse, or None.

    Python can't read the hovered button (``context.button_operator`` exists only inside its right-click menu), but
    ``ui.copy_python_command_button`` (Ctrl+C over a button) writes the hovered operator call to the clipboard.
    The clipboard text is put back right away.
    shortcut: runs on every left press in the editor window; non-text clipboard content (an image) can't be read
    back, so an empty text clipboard is left as the copied command rather than restored. Upgrade if that bites.
    """
    wm = context.window_manager
    saved = wm.clipboard
    try:
        bpy.ops.ui.copy_python_command_button()
    except RuntimeError:
        return None             # not over an operator button
    copied = wm.clipboard
    if saved:
        wm.clipboard = saved
    match = _GRIP_CALL.search(copied)
    return int(match.group(1)) if match else None


def _start_watch(window, area, region):
    _state["pending"] = False
    if _state["window"] == window.as_pointer():
        return None
    try:
        with bpy.context.temp_override(window=window, area=area, region=region):
            bpy.ops.allset.shelf_editor_drag_watch('INVOKE_DEFAULT')
    except (ReferenceError, RuntimeError, TypeError) as error:
        print("Shelf Editor drag: watcher not started:", error)  # window closed meanwhile; the next draw retries
    return None


def draw_grip(layout, index):
    context = bpy.context
    # shortcut: keyed on the window pointer; a closed window's pointer reused by a new one would skip the watcher
    # until the next Blender session. Fine unless grips stop reacting after reopening the editor.
    if context.window is not None and not _state["pending"] and _state["window"] != context.window.as_pointer():
        _state["pending"] = True
        window, area, region = context.window, context.area, context.region
        bpy.app.timers.register(lambda: _start_watch(window, area, region), first_interval=0.0)
    op = layout.operator(ALLSET_OT_shelf_editor_grip.bl_idname, text="", icon='GRIP', emboss=False)
    op.index = index


classes = (ALLSET_OT_shelf_editor_grip, ALLSET_OT_shelf_editor_drag_watch)


def unregister():
    _state["window"], _state["pending"] = 0, False
