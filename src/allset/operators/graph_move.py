# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya key moves in the Graph Editor: Shift axis lock and time snap to whole frames (step 281, #192).

Maya moves the selected keys linearly with the drag (time = dx / pixels per frame, value = -dy / pixels per value).
With Shift held the axis is decided by the first mouse move whose offset from the press reaches 3 px in x or y:
``|dx| >= |dy|`` = time only (a tie goes to time), else value only. The motion up to and including that move is
dropped; the move counts from that point, so a single long move followed by the release moves nothing.

With Maya's time snap on (the Graph Editor toolbar button, ``tool_settings.use_snap_anim``) the time delta is rounded
to whole frames and the moved key lands on a whole frame: a key at 10.3 moved by 0.38 frames lands on 10, by 0.59 on
11. Blender's frame snap rounds only the delta (10.3 keeps its fraction), so ``ALLSET_OT_graph_move_snap`` watches
Blender's own key moves (MMB / LMB drags) and drops the fraction afterwards.

``ALLSET_OT_graph_axis_drag`` = Shift+MMB anywhere in the canvas and Shift+LMB drag on a selected key: the kit applies
the move itself (Blender's transform would read the held Shift as precision mode). Pure rules: ``decide``,
``snapped_time``, ``whole_frame``, ``normalization``.
"""

import math

import bpy
from bpy.props import EnumProperty

DECIDE_PX = 3          # Maya: the first move reaching 3 px from the press decides the axis
WHOLE_EPS = 1e-4       # a time this close to a whole frame counts as that frame


# --- pure rules -------------------------------------------------------------------------------------------------

def decide(dx, dy, threshold=DECIDE_PX):
    """'TIME' / 'VALUE' for a move (dx, dy) px from the press, None while it hasn't reached the threshold."""
    if abs(dx) < threshold and abs(dy) < threshold:
        return None
    return 'TIME' if abs(dx) >= abs(dy) else 'VALUE'


def whole_frame(x):
    """Maya drops the fraction of a moved key's time (a time within WHOLE_EPS of a frame is that frame)."""
    r = round(x)
    if abs(x - r) < WHOLE_EPS:
        return float(r)
    return float(math.floor(x))


def snapped_time(x0, dt, snap):
    """New time of a key at ``x0`` moved by ``dt`` frames: Maya time snap rounds the delta (half up) and lands the
    key on a whole frame; without snap the delta is free."""
    if not snap:
        return x0 + dt
    return whole_frame(x0 + math.floor(dt + 0.5))


def normalization(points):
    """(factor, offset) of Blender's normalized Graph Editor view for one curve: display = (value + offset) x factor.
    ``points`` = [(co_y, left handle y, right handle y, interpolation)] in key order; Bezier segments count their
    handles, the curve's ends only their control points."""
    lo, hi = math.inf, -math.inf
    prev = None
    for co, left, right, interp in points:
        vals = [co]
        if prev is not None and prev[3] == 'BEZIER':
            vals += [prev[2], left]
        lo, hi = min(lo, *vals), max(hi, *vals)
        prev = (co, left, right, interp)
    if not points:
        return 1.0, 0.0
    rng = hi - lo
    if rng > 1.2e-7:
        return 2.0 / rng, -lo - rng / 2.0
    return 1.0, -lo


def time_snap_on(scene):
    ts = scene.tool_settings
    return bool(getattr(ts, "use_snap_anim", False)) and getattr(ts, "snap_anim_element", 'FRAME') == 'FRAME'


# --- curves -----------------------------------------------------------------------------------------------------

def _value_scales(context, fcurves):
    """Per curve: stored value per display value of the Graph Editor's value axis (rotation in degrees, normalized
    view)."""
    from ..ui import graph_units
    units = graph_units.curve_units(fcurves)
    degrees = getattr(context.scene.unit_settings, "system_rotation", 'DEGREES') == 'DEGREES'
    normalized = bool(getattr(context.space_data, "use_normalization", False))
    out = []
    for fc, unit in zip(fcurves, units):
        k = 1.0
        if unit == 'ROTATION' and degrees:
            k *= math.pi / 180.0
        if normalized:
            pts = [(kp.co.y, kp.handle_left.y, kp.handle_right.y, kp.interpolation) for kp in fc.keyframe_points]
            f, _off = normalization(pts)
            k /= f
        out.append(k)
    return out


def _recalc(fc):
    pts = fc.keyframe_points
    if hasattr(pts, "handles_recalc"):
        pts.handles_recalc()


class KeySet:
    """The selected keys of the editable curves with their positions at the press."""

    def __init__(self, context):
        fcs = [fc for fc in (getattr(context, "editable_fcurves", None) or ())
               if any(kp.select_control_point for kp in fc.keyframe_points)]
        self.curves = []
        for fc, scale in zip(fcs, _value_scales(context, fcs) if fcs else ()):
            keys = [(i, tuple(kp.co), tuple(kp.handle_left), tuple(kp.handle_right))
                    for i, kp in enumerate(fc.keyframe_points) if kp.select_control_point]
            self.curves.append((fc, scale, keys))

    def __bool__(self):
        return bool(self.curves)

    def apply(self, dt, dv, snap, time_axis=True):
        """Every key = its press position moved by ``dt`` frames and ``dv`` display units; handles move along."""
        for fc, scale, keys in self.curves:
            for i, co, left, right in keys:
                nx = snapped_time(co[0], dt, snap) if time_axis else co[0]
                ox, oy = nx - co[0], dv * scale
                kp = fc.keyframe_points[i]
                kp.co = (nx, co[1] + oy)
                kp.handle_left = (left[0] + ox, left[1] + oy)
                kp.handle_right = (right[0] + ox, right[1] + oy)
            _recalc(fc)

    def restore(self):
        self.apply(0.0, 0.0, False)

    def finish(self):
        for fc, _scale, _keys in self.curves:
            fc.update()
            fc.id_data.update_tag()


def _redraw(context):
    for area in context.screen.areas if context.screen else ():
        if area.type in {'GRAPH_EDITOR', 'DOPESHEET_EDITOR', 'VIEW_3D'}:
            area.tag_redraw()


def _graph_window(context):
    space, region = getattr(context, "space_data", None), getattr(context, "region", None)
    return (space is not None and space.type == 'GRAPH_EDITOR' and getattr(space, "mode", 'FCURVES') == 'FCURVES'
            and region is not None and region.type == 'WINDOW')


def near_selected_key(context, x, y):
    """True when region pixel (x, y) is within Blender's key pick distance of a selected key's control point."""
    region = context.region
    tol = 10.0 * getattr(context.preferences.system, "pixel_size", 1.0)
    fcs = [fc for fc in (getattr(context, "editable_fcurves", None) or ())
           if any(kp.select_control_point for kp in fc.keyframe_points)]
    if not fcs:
        return False
    for fc, scale in zip(fcs, _value_scales(context, fcs)):
        off = 0.0
        if getattr(context.space_data, "use_normalization", False):
            pts = [(kp.co.y, kp.handle_left.y, kp.handle_right.y, kp.interpolation) for kp in fc.keyframe_points]
            _f, off = normalization(pts)
        for kp in fc.keyframe_points:
            if not kp.select_control_point:
                continue
            vy = (kp.co.y + off) / scale
            px, py = region.view2d.view_to_region(kp.co.x, vy, clip=False)
            if abs(px - x) <= tol and abs(py - y) <= tol:
                return True
    return False


class ALLSET_OT_graph_axis_drag(bpy.types.Operator):
    """Maya Shift+drag in the Graph Editor: move the selected keys along time or value only (the first 3 px of the
    drag pick the axis)"""
    bl_idname = "allset.graph_axis_drag"
    bl_label = "Move Keys (Axis Lock)"
    bl_options = {'UNDO', 'INTERNAL'}

    button: EnumProperty(items=[('MIDDLE', "Middle", ""), ('LEFT', "Left", "")], default='MIDDLE',
                         options={'SKIP_SAVE'})

    def invoke(self, context, event):
        if not _graph_window(context):
            return {'PASS_THROUGH'}
        region = context.region
        if self.button == 'LEFT':
            px = getattr(event, "mouse_prev_press_x", event.mouse_x) - region.x
            py = getattr(event, "mouse_prev_press_y", event.mouse_y) - region.y
            if not near_selected_key(context, px, py):
                return {'PASS_THROUGH'}             # Blender's Shift marquee
        else:
            px, py = event.mouse_x - region.x, event.mouse_y - region.y
        self._keys = KeySet(context)
        if not self._keys:
            return {'PASS_THROUGH'} if self.button == 'LEFT' else {'CANCELLED'}
        self._region = region
        self._press = (px, py)
        self._axis = None
        self._origin = None
        if self.button == 'LEFT':
            # Blender sends the drag on the move that crossed its drag threshold: that move decides when it is 3 px
            x, y = event.mouse_x - region.x, event.mouse_y - region.y
            self._axis = decide(x - px, y - py)
            if self._axis is not None:
                self._origin = (x, y)
        self._moved = False
        self._snap = time_snap_on(context.scene)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def _view(self, x, y):
        return self._region.view2d.region_to_view(x, y)

    def modal(self, context, event):
        release = 'MIDDLEMOUSE' if self.button == 'MIDDLE' else 'LEFTMOUSE'
        if event.type in {'ESC', 'RIGHTMOUSE'} and event.value == 'PRESS':
            self._keys.restore()
            self._keys.finish()
            _redraw(context)
            return {'CANCELLED'}
        if event.type in {'MOUSEMOVE', 'INBETWEEN_MOUSEMOVE'}:
            x, y = event.mouse_x - self._region.x, event.mouse_y - self._region.y
            if self._axis is None:
                self._axis = decide(x - self._press[0], y - self._press[1])
                if self._axis is not None:
                    self._origin = (x, y)               # the deciding move itself is dropped
                return {'RUNNING_MODAL'}
            t0, v0 = self._view(*self._origin)
            t1, v1 = self._view(x, y)
            if self._axis == 'TIME':
                self._keys.apply(t1 - t0, 0.0, self._snap, time_axis=True)
            else:
                self._keys.apply(0.0, v1 - v0, self._snap, time_axis=False)
            self._moved = True
            _redraw(context)
            return {'RUNNING_MODAL'}
        if event.type == release and event.value == 'RELEASE':
            if not self._moved:
                return {'CANCELLED'}
            self._keys.finish()
            _redraw(context)
            return {'FINISHED'}
        return {'RUNNING_MODAL'}


# --- Blender's own key moves: drop the fraction when time snap is on ------------------------------------------

_PENDING = {}


def drop_fractions(fcurves):
    """Selected keys of these curves onto whole frames (handles move along); returns how many keys moved."""
    n = 0
    for fc in fcurves:
        hit = 0
        for kp in fc.keyframe_points:
            if not kp.select_control_point:
                continue
            x = whole_frame(kp.co.x)
            d = x - kp.co.x
            if abs(d) > 1e-9:
                kp.co.x = x
                kp.handle_left.x += d
                kp.handle_right.x += d
                hit += 1
        if hit:
            fc.update()
            fc.id_data.update_tag()
        n += hit
    return n


def _transform_running(wm):
    return any(op.bl_idname.startswith("TRANSFORM_OT") for w in wm.windows for op in w.modal_operators)


def _finish_move():
    p = _PENDING.get("move")
    if p is None:
        return None
    wm = bpy.context.window_manager
    if not p["started"]:
        last = wm.operators[-1].as_pointer() if len(wm.operators) else 0
        p["started"] = _transform_running(wm) or last != p["last"]
        p["ticks"] += 1
        if not p["started"] and p["ticks"] < 40:
            return 0.02
    if _transform_running(wm):
        return 0.02
    _PENDING.pop("move", None)
    last = wm.operators[-1] if len(wm.operators) else None
    if last is None or last.as_pointer() == p["last"] or not last.bl_idname.startswith("TRANSFORM_OT"):
        return None                                     # cancelled, or a marquee ran instead
    # a confirmed move: Maya drops the fraction even when the time delta rounds to 0 (nothing moved in Blender)
    moved = []
    for fc in p["curves"]:
        try:
            fc.keyframe_points
        except ReferenceError:
            continue
        moved.append(fc)
    if moved and drop_fractions(moved):
        win = p.get("window")
        windows = [w for w in wm.windows if w.as_pointer() == win] or list(wm.windows)
        if windows:
            with bpy.context.temp_override(window=windows[0]):
                bpy.ops.ed.undo_push(message="Snap Keys To Frames")
                _redraw(bpy.context)
    return None


class ALLSET_OT_graph_move_snap(bpy.types.Operator):
    """Maya time snap for Blender's key moves: after the move, the moved keys land on whole frames"""
    bl_idname = "allset.graph_move_snap"
    bl_label = "Maya Time Snap"
    bl_options = {'INTERNAL'}

    def invoke(self, context, event):
        if not _graph_window(context) or not time_snap_on(context.scene):
            return {'PASS_THROUGH'}
        curves = [fc for fc in (getattr(context, "editable_fcurves", None) or ())
                  if any(kp.select_control_point for kp in fc.keyframe_points)]
        if curves:
            wm = context.window_manager
            _PENDING["move"] = {"curves": curves, "last": wm.operators[-1].as_pointer() if len(wm.operators) else 0,
                                "started": False, "ticks": 0, "window": context.window.as_pointer()}
            if not bpy.app.timers.is_registered(_finish_move):
                bpy.app.timers.register(_finish_move, first_interval=0.02)
        return {'PASS_THROUGH'}


classes = (ALLSET_OT_graph_axis_drag, ALLSET_OT_graph_move_snap)


def unregister_timers():
    _PENDING.clear()
    if bpy.app.timers.is_registered(_finish_move):
        bpy.app.timers.unregister(_finish_move)
