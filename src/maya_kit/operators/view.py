# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya camera/view feel: ortho tumble lock, framing in all views,
view-change undo (``[`` / ``]``), Space-tap four-view toggle.

Design: docs/steps/step_4.md 「계획」 2-5. Evidence:
research/maya/interaction.md §1 (:38-57), §8 (:189-196), §10 (:216-225),
§12 (:248-249).
"""

import bpy

# --- tumble -------------------------------------------------------------------


def tumble_locked(rv3d, lock):
    """Maya top/front/side views do not tumble (step_4.md 「계획」 2)."""
    return bool(lock) and rv3d.view_perspective == 'ORTHO' and rv3d.is_orthographic_side_view


class MAYAKIT_OT_tumble(bpy.types.Operator):
    """Tumble the view (Maya Alt+LMB); locked in axis-aligned ortho views"""
    bl_idname = "maya_kit.tumble"
    bl_label = "Tumble"

    @classmethod
    def poll(cls, context):
        return context.region_data is not None

    def invoke(self, context, event):
        from .. import preferences
        if tumble_locked(context.region_data, preferences.get(context).lock_ortho_tumble):
            return {'FINISHED'}
        bpy.ops.view3d.rotate('INVOKE_DEFAULT')
        return {'FINISHED'}


# --- framing ------------------------------------------------------------------


def view3d_window_regions(window):
    """(area, region) for every 3D view WINDOW region (quad views: all four)."""
    for area in window.screen.areas:
        if area.type != 'VIEW_3D':
            continue
        for region in area.regions:
            if region.type == 'WINDOW':
                yield area, region


class MAYAKIT_OT_frame_all_views(bpy.types.Operator):
    """Frame the selection (or everything) in every 3D view (Maya Shift+F / Shift+A)"""
    bl_idname = "maya_kit.frame_all_views"
    bl_label = "Frame in All Views"

    selected: bpy.props.BoolProperty(name="Selected", default=True)

    @classmethod
    def poll(cls, context):
        return context.window is not None

    def execute(self, context):
        count = 0
        for area, region in view3d_window_regions(context.window):
            with context.temp_override(area=area, region=region):
                if self.selected:
                    bpy.ops.view3d.view_selected()
                else:
                    bpy.ops.view3d.view_all(center=False)
            count += 1
        return {'FINISHED'} if count else {'CANCELLED'}


# --- view history ---------------------------------------------------------------

_DIGITS = 5


def capture(rv3d):
    """Comparable snapshot of a RegionView3D's view."""
    r = lambda v: round(v, _DIGITS)  # noqa: E731
    return (tuple(map(r, rv3d.view_location)), tuple(map(r, rv3d.view_rotation)),
            r(rv3d.view_distance), rv3d.view_perspective,
            r(rv3d.view_camera_zoom), tuple(map(r, rv3d.view_camera_offset)))


def restore(rv3d, state):
    loc, rot, dist, persp, cam_zoom, cam_offset = state
    rv3d.view_perspective = persp
    rv3d.view_location = loc
    rv3d.view_rotation = rot
    rv3d.view_distance = dist
    rv3d.view_camera_zoom = cam_zoom
    rv3d.view_camera_offset = cam_offset


class ViewHistory:
    """Undo/redo stack of settled view states for one RegionView3D.

    ``observe`` is called periodically with the current state. A change is
    recorded once the view has stayed the same for one more observation
    (navigation or smooth-view animation finished).
    """

    def __init__(self, limit=50):
        self.limit = limit
        self.undo = []
        self.redo = []
        self.stable = None
        self.pending = None

    def _push(self, state):
        self.undo.append(state)
        del self.undo[:-self.limit]
        self.redo.clear()

    def observe(self, state):
        if self.stable is None or state == self.stable:
            self.stable = state
            self.pending = None
            return
        if state != self.pending:
            self.pending = state  # still moving
            return
        self._push(self.stable)
        self.stable = state
        self.pending = None

    def step_back(self, current):
        """State to show for "undo view change", or None."""
        if self.stable is None:  # never observed: nothing to go back to
            self.stable = current
            return None
        if current != self.stable:  # a change not settled/observed yet
            self._push(self.stable)
            self.stable = current
        if not self.undo:
            return None
        self.redo.append(current)
        self.stable = self.undo.pop()
        self.pending = None
        return self.stable

    def step_forward(self, current):
        """State to show for "redo view change", or None."""
        if self.stable is None:
            self.stable = current
            return None
        if current != self.stable:
            self.redo.clear()  # the view moved since the undo: redo is void
            self.observe(current)
            return None
        if not self.redo:
            return None
        self.undo.append(current)
        self.stable = self.redo.pop()
        self.pending = None
        return self.stable


_histories = {}
POLL_INTERVAL = 0.25


def history_for(rv3d):
    key = rv3d.as_pointer()
    h = _histories.get(key)
    if h is None:
        h = _histories[key] = ViewHistory()
    return h


def _all_rv3d():
    wm = bpy.context.window_manager
    for window in wm.windows:
        for area in window.screen.areas:
            if area.type != 'VIEW_3D':
                continue
            space = area.spaces.active
            yield space.region_3d
            yield from space.region_quadviews


def poll_views():
    """Timer: observe every 3D view; forget views that no longer exist."""
    seen = set()
    for rv3d in _all_rv3d():
        if rv3d is None:
            continue
        seen.add(rv3d.as_pointer())
        history_for(rv3d).observe(capture(rv3d))
    for key in list(_histories):
        if key not in seen:
            del _histories[key]
    return POLL_INTERVAL


class MAYAKIT_OT_view_history(bpy.types.Operator):
    """Undo or redo a view change (Maya [ and ]); separate from scene undo"""
    bl_idname = "maya_kit.view_history"
    bl_label = "Undo/Redo View Change"

    direction: bpy.props.EnumProperty(items=(("UNDO", "Undo", ""), ("REDO", "Redo", "")))

    @classmethod
    def poll(cls, context):
        return context.region_data is not None

    def execute(self, context):
        rv3d = context.region_data
        h = history_for(rv3d)
        cur = capture(rv3d)
        state = h.step_back(cur) if self.direction == "UNDO" else h.step_forward(cur)
        if state is None:
            self.report({'INFO'}, "No more view changes")
            return {'CANCELLED'}
        restore(rv3d, state)
        if context.area:
            context.area.tag_redraw()
        return {'FINISHED'}


# --- Space tap: four views <-> single view -------------------------------------


class MAYAKIT_OT_toggle_quad_view(bpy.types.Operator):
    """Toggle four views; leaving it keeps the view under the cursor (Maya Space tap)"""
    bl_idname = "maya_kit.toggle_quad_view"
    bl_label = "Toggle Four Views"

    @classmethod
    def poll(cls, context):
        return context.space_data is not None and context.space_data.type == 'VIEW_3D'

    def execute(self, context):
        space = context.space_data
        area = context.area
        leaving = bool(space.region_quadviews)
        hovered = capture(context.region_data) if leaving and context.region_data else None
        region = context.region if context.region and context.region.type == 'WINDOW' else \
            next(r for r in area.regions if r.type == 'WINDOW')
        with context.temp_override(area=area, region=region):
            bpy.ops.screen.region_quadview()
        if hovered is not None:
            restore(space.region_3d, hovered)
        area.tag_redraw()
        return {'FINISHED'}


classes = (MAYAKIT_OT_tumble, MAYAKIT_OT_frame_all_views, MAYAKIT_OT_view_history,
           MAYAKIT_OT_toggle_quad_view)


def register_timer():
    if not bpy.app.timers.is_registered(poll_views):
        bpy.app.timers.register(poll_views, first_interval=POLL_INTERVAL, persistent=True)


def unregister_timer():
    if bpy.app.timers.is_registered(poll_views):
        bpy.app.timers.unregister(poll_views)
    _histories.clear()
