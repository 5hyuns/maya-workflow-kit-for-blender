# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya "only while held" keys: X/C/V/J snapping, D pivot editing.

research/maya/interaction.md §0 (press/release hotkeys), §4 (D hold /
Insert), §5 (X grid, C curve, V point); hotkeys_default.json j =
MoveRotateScaleToolToggleSnapMode press/release. Design and limits:
docs/steps/step_3.md 「계획」 1-4.

``begin``/``end`` are plain functions (headless-testable). The operator
``maya_kit.hold`` wraps them in a modal that waits for the key's RELEASE.
"""

import bpy

from . import keystate


class HoldGroup:
    """Tool settings that several holds share; saved once, restored once."""

    def capture(self, ts):
        raise NotImplementedError

    def apply(self, ts, names):
        raise NotImplementedError

    def restore(self, ts, state):
        raise NotImplementedError


class SnapGroup(HoldGroup):
    # Hold name -> Blender snap elements (step_3.md 「계획」 3).
    ELEMENTS = {"grid": {'GRID'}, "curve": {'EDGE'}, "point": {'VERTEX'}, "step": {'INCREMENT'}}

    def capture(self, ts):
        return (ts.use_snap, set(ts.snap_elements))

    def apply(self, ts, names):
        elements = set().union(*(self.ELEMENTS[n] for n in names))
        ts.snap_elements = elements
        ts.use_snap = True

    def restore(self, ts, state):
        use_snap, elements = state
        ts.snap_elements = elements
        ts.use_snap = use_snap


class PivotGroup(HoldGroup):
    """D hold: transform affects only object origins (research/blender/api_limits.md §7)."""

    def capture(self, ts):
        return ts.use_transform_data_origin

    def apply(self, ts, names):
        ts.use_transform_data_origin = True

    def restore(self, ts, state):
        ts.use_transform_data_origin = state


GROUPS = {"snap": SnapGroup(), "pivot": PivotGroup()}
HOLDS = {"grid": "snap", "curve": "snap", "point": "snap", "step": "snap", "pivot": "pivot"}

# group -> {"saved": state, "active": [hold names in press order]}
_state = {}


def active_holds():
    return {g: list(s["active"]) for g, s in _state.items()}


def begin(ts, name):
    """Start holding ``name``. Saves the group's state on its first hold."""
    group_name = HOLDS[name]
    group = GROUPS[group_name]
    st = _state.get(group_name)
    if st is None:
        st = _state[group_name] = {"saved": group.capture(ts), "active": []}
    if name not in st["active"]:
        st["active"].append(name)
    group.apply(ts, st["active"])


def end(ts, name):
    """Stop holding ``name``. Restores the saved state when the group empties."""
    group_name = HOLDS[name]
    st = _state.get(group_name)
    if st is None or name not in st["active"]:
        return
    st["active"].remove(name)
    group = GROUPS[group_name]
    if st["active"]:
        group.apply(ts, st["active"])
    else:
        group.restore(ts, st["saved"])
        del _state[group_name]


def end_all(ts):
    """Restore everything (used on unregister)."""
    for group_name, st in list(_state.items()):
        GROUPS[group_name].restore(ts, st["saved"])
    _state.clear()


_HOLD_ITEMS = (
    ("grid", "Grid Snap", "Maya X: snap to grid while held"),
    ("curve", "Curve Snap", "Maya C: snap to curves/edges while held"),
    ("point", "Point Snap", "Maya V: snap to vertices while held"),
    ("step", "Step Snap", "Maya J: incremental snap while held"),
    ("pivot", "Pivot Edit", "Maya D: affect only origins while held"),
)


class MAYAKIT_OT_hold(bpy.types.Operator):
    """Enable a Maya hold mode while the key is held, restore on release"""
    bl_idname = "maya_kit.hold"
    bl_label = "Maya Hold Key"
    bl_options = {'INTERNAL'}

    name: bpy.props.EnumProperty(items=_HOLD_ITEMS, name="Hold")

    _POLL_INTERVAL = 0.05

    def invoke(self, context, event):
        if event.value != 'PRESS':
            return {'CANCELLED'}
        self._key = event.type
        self._ts = context.scene.tool_settings
        begin(self._ts, self.name)
        self._timer = context.window_manager.event_timer_add(self._POLL_INTERVAL, window=context.window)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def _finish(self, context):
        end(self._ts, self.name)
        context.window_manager.event_timer_remove(self._timer)
        return {'FINISHED'}

    def modal(self, context, event):
        if event.type == self._key:
            if event.value == 'RELEASE':
                return self._finish(context)
            return {'RUNNING_MODAL'}  # key repeat
        if event.type == 'TIMER' and keystate.is_down(self._key) is False:
            # RELEASE was consumed by another modal (e.g. a transform drag).
            return self._finish(context)
        return {'PASS_THROUGH'}


class MAYAKIT_OT_pivot_toggle(bpy.types.Operator):
    """Toggle pivot edit mode: transform affects only origins (Maya Insert)"""
    bl_idname = "maya_kit.pivot_toggle"
    bl_label = "Toggle Pivot Edit"
    bl_options = {'REGISTER'}

    def execute(self, context):
        ts = context.scene.tool_settings
        ts.use_transform_data_origin = not ts.use_transform_data_origin
        self.report({'INFO'}, "Pivot edit " + ("on" if ts.use_transform_data_origin else "off"))
        return {'FINISHED'}


classes = (MAYAKIT_OT_hold, MAYAKIT_OT_pivot_toggle)


def unregister_cleanup():
    """Restore held states if the add-on is disabled mid-hold."""
    scene = getattr(bpy.context, "scene", None)
    if scene is not None and _state:
        end_all(scene.tool_settings)
    _state.clear()
