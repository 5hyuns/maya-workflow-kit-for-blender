# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya tangents and key edits for the Graph Editor toolbar and the Shift+S marking menu (docs/steps/step_70.md).

Maya's Graph Editor tangent buttons and ``buildKeyframeTangentMM`` act on the selected keys in the Graph Editor
and on the current-time keys of the selection anywhere else (``timeSliderSetTangent``,
research/maya/marking_menus.json buildKeyframeTangentMM :284-571; research/maya/workflows/animation.md §2.14).
In Blender's Graph Editor the selected keys are the selected control points of the editable curves; elsewhere
``operators/time_keys`` acts on the Channel Box nodes (Time Slider range, else the current frame).

Shift+S = ``KeyTangentBinding``: hold + LMB opens the marking menu; a tap does nothing, like Maya.
"""

import bpy
from bpy.props import EnumProperty

from . import keystate, taphold, time_keys

KEY_ACTIONS = [(k, l, d) for k, l, d in time_keys.ACTIONS if k not in {"SNAP", "TANGENT"}]


def in_graph_editor(context):
    space = getattr(context, "space_data", None)
    return space is not None and space.type == 'GRAPH_EDITOR'


def selected_keys(context):
    """[(fcurve, [keyframe points])] selected in the Graph Editor (editable curves)."""
    out = []
    for fc in getattr(context, "editable_fcurves", None) or ():
        pts = [kp for kp in fc.keyframe_points if kp.select_control_point]
        if pts:
            out.append((fc, pts))
    return out


def tangent_selected(context, kind):
    n = 0
    for fc, pts in selected_keys(context):
        for kp in pts:
            time_keys.apply_tangent(kp, kind)
            n += 1
        fc.update()
    return n


def _redraw(context):
    for area in context.screen.areas if context.screen else ():
        if area.type in {'GRAPH_EDITOR', 'DOPESHEET_EDITOR', 'VIEW_3D'}:
            area.tag_redraw()


class MAYAKIT_OT_set_tangent(bpy.types.Operator):
    """Set the in and out tangents: the selected keys in the Graph Editor, else the selection's keys at the
    current time (Maya Graph Editor tangent buttons, Shift+S marking menu)"""
    bl_idname = "maya_kit.set_tangent"
    bl_label = "Set Tangent"
    bl_options = {'REGISTER', 'UNDO'}

    kind: EnumProperty(items=time_keys.TANGENT_ITEMS, name="Tangent")

    @classmethod
    def description(cls, context, props):
        interp, handle = time_keys.TANGENTS[props.kind]
        blender = " + ".join(x.replace("_", " ").title() for x in (interp, handle) if x)
        note = " (Blender has no Stepped Next)" if props.kind == "STEPPED_NEXT" else ""
        return f"{time_keys.TANGENT_LABELS[props.kind]} tangents = Blender {blender}{note}"

    def execute(self, context):
        if in_graph_editor(context):
            n = tangent_selected(context, self.kind)
        else:
            a, b = time_keys.time_range(context)
            n = time_keys.set_tangent(context, a, b, self.kind)
        if self.kind == "STEPPED_NEXT":
            self.report({'INFO'}, "Stepped Next isn't available in Blender: Stepped used")
        elif not n:
            self.report({'WARNING'}, "No keys selected" if in_graph_editor(context) else "No keys at this time")
        _redraw(context)
        return {'FINISHED'}


class MAYAKIT_OT_key_edit(bpy.types.Operator):
    """Edit keys: the selected keys in the Graph Editor, else the selection's keys at the current time
    (Maya Shift+S marking menu > Keys)"""
    bl_idname = "maya_kit.key_edit"
    bl_label = "Edit Keys"
    bl_options = {'REGISTER', 'UNDO'}

    action: EnumProperty(items=KEY_ACTIONS, name="Action")

    @classmethod
    def description(cls, context, props):
        return next(d for k, _l, d in KEY_ACTIONS if k == props.action)

    def execute(self, context):
        act = self.action
        if not in_graph_editor(context) or act in {"ADD_INBETWEEN", "REMOVE_INBETWEEN"}:
            try:
                return bpy.ops.maya_kit.time_keys(action=act)
            except RuntimeError:     # time_keys polls on a Channel Box node
                self.report({'WARNING'}, "Select an animated object")
                return {'CANCELLED'}
        if act in {"COPY", "CUT"}:
            bpy.ops.graph.copy()
        if act == "PASTE":
            bpy.ops.graph.paste()
        elif act in {"CUT", "DELETE"}:
            for fc, _pts in selected_keys(context):
                # one at a time: removing a point invalidates the references to the later ones
                while True:
                    kp = next((k for k in fc.keyframe_points if k.select_control_point), None)
                    if kp is None:
                        break
                    fc.keyframe_points.remove(kp)
                fc.update()
        elif act in {"TO_KEY", "TO_BREAKDOWN"}:
            for _fc, pts in selected_keys(context):
                for kp in pts:
                    kp.type = 'KEYFRAME' if act == "TO_KEY" else 'BREAKDOWN'
        _redraw(context)
        return {'FINISHED'}


# Graph Editor 1 / 2 / 3 = graphEditorSetViewMode 0 / 1 / 2 (hotkeySetup.mel:148-150, defaultRunTimeCommands.mel:
# 12992-13006). Blender has Normalize; a stacked view (each curve in its own band) isn't there: 2 = normalized + notice.
VIEW_MODES = (("ABSOLUTE", "Absolute", "Maya 1: curves at their values"),
              ("STACKED", "Stacked", "Maya 2: not in Blender, curves are normalized instead"),
              ("NORMALIZED", "Normalized", "Maya 3: curves scaled to -1..1"))
STACKED_NOTICE = "Stacked view isn't in Blender: curves are normalized (-1..1) instead"


class MAYAKIT_OT_graph_view_mode(bpy.types.Operator):
    """Absolute / Stacked / Normalized curve view (Maya Graph Editor 1 / 2 / 3)"""
    bl_idname = "maya_kit.graph_view_mode"
    bl_label = "Graph Editor View Mode"
    bl_options = {'REGISTER'}

    mode: EnumProperty(items=VIEW_MODES, name="Mode")

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space is not None and space.type == 'GRAPH_EDITOR'

    def execute(self, context):
        context.space_data.use_normalization = self.mode != "ABSOLUTE"
        if self.mode == "STACKED":
            self.report({'INFO'}, STACKED_NOTICE)
        if context.area is not None:
            context.area.tag_redraw()
        return {'FINISHED'}


# --- t / Alt+/ / i (docs/steps/step_92.md; behaviour spec research/maya/re/graph_editor_keys.md) ----------------

def center_delta(frame_x, region_width):
    """Pixels to pan so the current frame (at region x ``frame_x``) sits in the middle (Maya t = lookAt currentTime:
    horizontal only, zoom and value range kept)."""
    return int(round(frame_x - region_width / 2.0))


class MAYAKIT_OT_graph_center_time(bpy.types.Operator):
    """Center the Graph Editor on the current time, keeping the zoom (Maya t)"""
    bl_idname = "maya_kit.graph_center_time"
    bl_label = "Center Current Time"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return in_graph_editor(context) and context.region is not None and context.region.type == 'WINDOW'

    def execute(self, context):
        region = context.region
        x, _y = region.view2d.view_to_region(context.scene.frame_current, 0.0, clip=False)
        dx = center_delta(x, region.width)
        if dx:
            bpy.ops.view2d.pan(deltax=dx, deltay=0)
        return {'FINISHED'}


def snap_target(times):
    """Maya Snap Time To Selection: the earliest selected key (None when nothing is selected)."""
    return min(times) if times else None


def selected_key_times(objects):
    """{(object name, data path, index): (selected key times,)} over the objects' actions (numpy, cheap)."""
    import numpy as np
    out = {}
    for ob in objects:
        ad = ob.animation_data
        action = ad.action if ad else None
        if action is None:
            continue
        for fc in action.fcurves:
            n = len(fc.keyframe_points)
            if not n:
                continue
            sel = np.empty(n, dtype=bool)
            fc.keyframe_points.foreach_get("select_control_point", sel)
            if sel.any():
                co = np.empty(n * 2, dtype=np.float32)
                fc.keyframe_points.foreach_get("co", co)
                out[(ob.name, fc.data_path, fc.array_index)] = tuple(float(t) for t in co[0::2][sel])
    return out


_snap = {"last": None}
SNAP_POLL = 0.15


def remember_selection(scene=None):
    """Take the current key selection as the baseline (a kit edit that selects keys must not move the time)."""
    scene = scene or bpy.context.scene
    _snap["last"] = selected_key_times(scene.objects) if scene else None


def snap_step(scene, enabled):
    """One poll: the frame to go to, or None. Keeps the baseline in ``_snap``."""
    if not enabled:
        _snap["last"] = None
        return None
    now = selected_key_times(scene.objects)
    last, _snap["last"] = _snap["last"], now
    if last is None or now == last:
        return None
    return snap_target([t for ts in now.values() for t in ts])


def _graph_open():
    wm = bpy.context.window_manager
    return any(a.type == 'GRAPH_EDITOR' for w in wm.windows for a in w.screen.areas)


def _snap_tick():
    try:
        from .. import preferences
        enabled = preferences.get().snap_time_to_selection and _graph_open()
        scene = bpy.context.scene
        frame = snap_step(scene, enabled) if scene else None
        if frame is not None:
            whole = int(frame // 1)
            scene.frame_set(whole, subframe=frame - whole)
    except (KeyError, AttributeError, ReferenceError):
        pass
    return SNAP_POLL


@bpy.app.handlers.persistent
def _snap_reset(*_args):
    _snap["last"] = None


class MAYAKIT_OT_snap_time_toggle(bpy.types.Operator):
    """Turn Snap Time To Selection on or off: selecting keys moves the current time to them (Maya Alt+/)"""
    bl_idname = "maya_kit.snap_time_toggle"
    bl_label = "Snap Time To Selection"
    bl_options = {'REGISTER'}

    def execute(self, context):
        from .. import preferences
        prefs = preferences.get(context)
        prefs.snap_time_to_selection = not prefs.snap_time_to_selection
        remember_selection(context.scene)
        self.report({'INFO'}, "Snap Time To Selection: " + ("on" if prefs.snap_time_to_selection else "off"))
        return {'FINISHED'}


def draw_view_menu(self, context):
    """Graph Editor View > Snap Time To Selection (the Maya View menu check item, graphEditorPanel.mel:942-945)."""
    from .. import preferences
    try:
        prefs = preferences.get(context)
    except KeyError:
        return
    self.layout.separator()
    self.layout.prop(prefs, "snap_time_to_selection")


def insert_frame(view_x):
    """Maya's Insert Key tool keys on the whole frame under the mouse."""
    return int(round(view_x))


def insert_curves(curves):
    """Curves the Insert Key tool keys: the selected ones (a selected key or the channel selected), unlocked."""
    return [fc for fc in curves
            if not fc.lock and (fc.select or any(kp.select_control_point for kp in fc.keyframe_points))]


def insert_on(curves, frame):
    """Insert a shape-keeping key at ``frame`` on each curve; afterwards only the new keys are selected (Maya).
    Returns the curves that got a key."""
    from .key_insert import _at, insert_keep_shape
    done = [fc for fc in curves if insert_keep_shape(fc, frame)]
    for fc in curves:
        for kp in fc.keyframe_points:
            kp.select_control_point = kp.select_left_handle = kp.select_right_handle = False
        kp = _at(fc, frame)
        if kp is not None:
            kp.select_control_point = True
    return done


_LINE = {"x": None, "handle": None, "region": None}


def _draw_line():
    x = _LINE["x"]
    region = bpy.context.region
    if x is None or region is None or region.as_pointer() != _LINE["region"]:
        return
    import gpu
    from gpu_extras.batch import batch_for_shader
    coords, y = [], 0
    while y < region.height:                      # dashed, like Maya's insert line
        coords += [(x, y), (x, min(y + 6, region.height))]
        y += 10
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    shader.uniform_float("color", (1.0, 1.0, 1.0, 0.9))
    batch_for_shader(shader, 'LINES', {"pos": coords}).draw(shader)


class MAYAKIT_OT_insert_key_tool(bpy.types.Operator):
    """Insert Key tool while held: MMB click / drag in the Graph Editor inserts a key on the selected curves at that
    frame, keeping the curve shape (Maya i)"""
    bl_idname = "maya_kit.insert_key_tool"
    bl_label = "Insert Key Tool (hold)"
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return in_graph_editor(context) and context.region is not None and context.region.type == 'WINDOW'

    def invoke(self, context, event):
        if event.value != 'PRESS':
            return {'CANCELLED'}
        self._key, self._region, self._area, self._drag = event.type, context.region, context.area, False
        self._timer = context.window_manager.event_timer_add(0.05, window=context.window)
        _LINE.update(x=None, region=context.region.as_pointer())
        _LINE["handle"] = bpy.types.SpaceGraphEditor.draw_handler_add(_draw_line, (), 'WINDOW', 'POST_PIXEL')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def _finish(self, context):
        context.window_manager.event_timer_remove(self._timer)
        if _LINE["handle"] is not None:
            bpy.types.SpaceGraphEditor.draw_handler_remove(_LINE["handle"], 'WINDOW')
        _LINE.update(x=None, handle=None, region=None)
        self._area.tag_redraw()
        return {'FINISHED'}

    def _local_x(self, event):
        return event.mouse_x - self._region.x

    def _insert(self, context, event):
        view_x, _v = self._region.view2d.region_to_view(self._local_x(event), event.mouse_y - self._region.y)
        curves = insert_curves(list(getattr(context, "visible_fcurves", None) or ()))
        if insert_on(curves, insert_frame(view_x)):
            remember_selection(context.scene)        # Maya: inserting doesn't move the time
            bpy.ops.ed.undo_push(message="Insert Key")

    def modal(self, context, event):
        if event.type == self._key:
            if event.value == 'RELEASE' and not self._drag:
                return self._finish(context)
            return {'RUNNING_MODAL'}
        if event.type == 'MIDDLEMOUSE':
            if event.value == 'PRESS':
                self._drag = True
                _LINE["x"] = self._local_x(event)
                self._area.tag_redraw()
                return {'RUNNING_MODAL'}
            if event.value == 'RELEASE' and self._drag:
                self._drag = False
                self._insert(context, event)
                _LINE["x"] = None
                self._area.tag_redraw()
                if keystate.is_down(self._key) is False:
                    return self._finish(context)
                return {'RUNNING_MODAL'}
        if event.type == 'MOUSEMOVE' and self._drag:
            _LINE["x"] = self._local_x(event)
            self._area.tag_redraw()
            return {'RUNNING_MODAL'}
        if event.type == 'TIMER' and not self._drag and keystate.is_down(self._key) is False:
            return self._finish(context)
        return {'RUNNING_MODAL'} if self._drag else {'PASS_THROUGH'}


class KeyTangentBinding(taphold.TapHoldBinding):
    """Shift+S: hold + LMB = the Keyframe / Tangent marking menu (buildKeyframeTangentMM); a tap does nothing."""
    name = "key_tangent"
    label = "Keyframe / Tangent Menu"

    def tap(self, context):
        pass

    def click(self, context, event):
        from ..marking import modal
        modal.open_menu("buildKeyframeTangentMM", 'LEFTMOUSE', (event.mouse_region_x, event.mouse_region_y))


classes = (MAYAKIT_OT_set_tangent, MAYAKIT_OT_key_edit, MAYAKIT_OT_graph_view_mode, MAYAKIT_OT_graph_center_time,
           MAYAKIT_OT_snap_time_toggle, MAYAKIT_OT_insert_key_tool)


def register_bindings():
    taphold.register_binding(KeyTangentBinding())
    bpy.types.GRAPH_MT_view.append(draw_view_menu)
    bpy.app.handlers.load_post.append(_snap_reset)
    if not bpy.app.timers.is_registered(_snap_tick):
        bpy.app.timers.register(_snap_tick, first_interval=SNAP_POLL, persistent=True)


def unregister_bindings():
    if bpy.app.timers.is_registered(_snap_tick):
        bpy.app.timers.unregister(_snap_tick)
    if _snap_reset in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_snap_reset)
    bpy.types.GRAPH_MT_view.remove(draw_view_menu)
    _snap["last"] = None
    taphold.unregister_binding(KeyTangentBinding.name)
