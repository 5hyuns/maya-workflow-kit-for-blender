# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya object visibility keys: h, Ctrl+H, Alt+H, Shift+H, Ctrl+Shift+H.

research/maya/interaction.md:233-238 (HK:271-277): h toggles the visibility of the
selection and keeps it selected; Ctrl+H hides the selection, Alt+H the rest;
Shift+H shows the selected hidden objects; Ctrl+Shift+H shows what was hidden last.

Blender deselects an object when it is hidden (``hide_set``), so Maya's "hidden but
still selected" is kept as an ID property on the object (``KEPT``). ``LAST`` marks
what the latest hide of this operator hid. Plan: docs/steps/step_16.md 2.
"""

import bpy
from bpy.props import EnumProperty

KEPT = "maya_kit_kept"              # hidden by h while selected: h / Shift+H bring it back
LAST = "maya_kit_last_hidden"       # hidden by the latest hide: Ctrl+Shift+H brings it back

ACTIONS = (
    ('TOGGLE', "Toggle Visibility", "Maya h: hide the selection and keep it selected, or show it again"),
    ('HIDE', "Hide Selection", "Maya Ctrl+H"),
    ('HIDE_UNSELECTED', "Hide Unselected Objects", "Maya Alt+H"),
    ('SHOW_SELECTED', "Show Selected Objects", "Maya Shift+H"),
    ('SHOW_LAST', "Show Last Hidden", "Maya Ctrl+Shift+H"),
)


def _clear(objects, key):
    for ob in objects:
        if key in ob:
            del ob[key]


def _hide(objects, all_objects, kept=False):
    """Hide ``objects``; they become the "last hidden" set (and the kept selection)."""
    _clear(all_objects, LAST)
    if kept:
        _clear(all_objects, KEPT)
    for ob in objects:
        ob.hide_set(True)
        ob[LAST] = True
        if kept:
            ob[KEPT] = True
    return len(objects)


def _show(objects, view_layer):
    shown = 0
    for ob in objects:
        ob.hide_set(False)
        for key in (KEPT, LAST):
            if key in ob:
                del ob[key]
        try:
            ob.select_set(True)
        except RuntimeError:   # not selectable in this view layer
            continue
        view_layer.objects.active = view_layer.objects.active or ob
        shown += 1
    return shown


def apply(context, action):
    """Run ``action`` on the view layer; returns the number of objects changed."""
    vl = context.view_layer
    objs = list(vl.objects)
    selected = [ob for ob in objs if ob.visible_get() and ob.select_get()]
    hidden = [ob for ob in objs if ob.hide_get()]
    if action == 'TOGGLE':
        if selected:
            return _hide(selected, objs, kept=True)
        return _show([ob for ob in hidden if KEPT in ob], vl)
    if action == 'HIDE':
        return _hide(selected, objs)
    if action == 'HIDE_UNSELECTED':
        return _hide([ob for ob in objs if ob.visible_get() and not ob.select_get()], objs)
    if action == 'SHOW_SELECTED':
        act = vl.objects.active
        return _show([ob for ob in hidden if KEPT in ob or ob == act], vl)
    if action == 'SHOW_LAST':
        return _show([ob for ob in hidden if LAST in ob], vl)
    raise ValueError(action)


class MAYAKIT_OT_visibility(bpy.types.Operator):
    """Maya object visibility (h, Ctrl+H, Alt+H, Shift+H, Ctrl+Shift+H)"""
    bl_idname = "maya_kit.visibility"
    bl_label = "Maya Visibility"
    bl_options = {'REGISTER', 'UNDO'}

    action: EnumProperty(name="Action", items=ACTIONS, default='TOGGLE')

    @classmethod
    def description(cls, context, props):
        return dict((a[0], a[2]) for a in ACTIONS)[props.action]

    @classmethod
    def poll(cls, context):
        return context.view_layer is not None and context.mode == 'OBJECT'

    def execute(self, context):
        apply(context, self.action)
        return {'FINISHED'}


classes = (MAYAKIT_OT_visibility,)
