# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya object visibility keys: h, Ctrl+H, Alt+H, Shift+H, Ctrl+Shift+H.

 (HK:271-277): h toggles the visibility of the
selection and keeps it selected; Ctrl+H hides the selection, Alt+H the rest;
Shift+H shows the selected hidden objects; Ctrl+Shift+H shows what was hidden last.

Maya's ``visibility`` attribute is ``Object.hide_viewport`` (per object, keyable; the Channel
Box Visibility row reads the same flag): h, Display > Hide / Show and the Channel Box write one
attribute. A display layer's V uses the view-layer flag
(``hide_set``) instead, so it never changes this attribute.

A hidden object can't stay selected in Blender, so Maya's "hidden but still selected" is kept
as an ID property on the object (``KEPT``). ``LAST`` marks what the latest hide of this
operator hid.  2.
"""

import bpy
from bpy.props import EnumProperty

from .. import undo_steps

KEPT = "allset_kept"              # hidden by h while selected: h / Shift+H bring it back
LAST = "allset_last_hidden"       # hidden by the latest hide: Ctrl+Shift+H brings it back

ACTIONS = (
    ('TOGGLE', "Toggle Visibility", "Maya h: hide the selection and keep it selected, or show it again"),
    ('HIDE', "Hide Selection", "Maya Ctrl+H"),
    ('HIDE_UNSELECTED', "Hide Unselected Objects", "Maya Alt+H"),
    ('SHOW_SELECTED', "Show Selected Objects", "Maya Shift+H"),
    ('SHOW_LAST', "Show Last Hidden", "Maya Ctrl+Shift+H"),
    ('SHOW_ALL', "Show All", "Maya Display > Show > All: every object whose visibility is off"),
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
        ob.hide_viewport = True
        try:
            ob.select_set(False)
        except RuntimeError:
            pass
        ob[LAST] = True
        if kept:
            ob[KEPT] = True
    return len(objects)


def _show(objects, view_layer, select=True):
    shown = 0
    for ob in objects:
        ob.hide_viewport = False
        for key in (KEPT, LAST):
            if key in ob:
                del ob[key]
        if not select:
            shown += 1
            continue
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
    hidden = [ob for ob in objs if ob.hide_viewport]
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
    if action == 'SHOW_ALL':
        return _show(hidden, vl, select=False)
    raise ValueError(action)


@undo_steps.no_redo_panel      # step 147: no Adjust Last Operation (Maya has none)
class ALLSET_OT_visibility(bpy.types.Operator):
    """Maya object visibility (h, Ctrl+H, Alt+H, Shift+H, Ctrl+Shift+H)"""
    bl_idname = "allset.visibility"
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
        vl = context.view_layer
        had_selection = any(ob.visible_get() and ob.select_get() for ob in vl.objects)
        changed = apply(context, self.action)
        text = message(self.action, had_selection, changed)
        if text:
            from ..ui import view_message
            view_message.show(context, text)
        return {'FINISHED'}


def message(action, had_selection, changed):
    """Maya's in-view message for a visibility action, or None (Maya-90,
    Maya-125)."""
    if action == 'HIDE':
        if had_selection:
            return ("Selection <hl>hidden</hl>.\n"
                    "To show it again, select it in the Outliner and press <hl>Shift+H</hl>.")
        return "Nothing is selected to hide."
    if action == 'HIDE_UNSELECTED':
        if changed:
            return ("Unselected objects <hl>hidden</hl>.\n"
                    "To show them, select them in the Outliner and press <hl>Shift+H</hl>.")
        return "No unselected objects to hide."
    if action == 'TOGGLE' and not changed:
        return "Nothing selected to toggle."
    return None


classes = (ALLSET_OT_visibility,)
