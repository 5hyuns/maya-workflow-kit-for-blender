# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya Time Slider + Range Slider in the Timeline header, and a timeline view that
follows the playback range.

research/maya/ui_layout.md:106-108, §4.10 (:272-282: 8 transport buttons, current time
field, auto key), §4.11 (:284-286: animation start, playback start, [range], playback end,
animation end). Blender form (docs/steps/step_20.md 「계획」 2, 4):
- ``bl_ui.space_time.TIME_HT_editor_buttons.draw_header`` (a plain class, not in bpy.types)
  is swapped for ``draw_header`` below and restored on unregister.
- Maya's animation range = scene frame_start/end; its playback range = the preview range
  (``use_preview_range`` off: playback = animation range, inner fields greyed).
- Maya's time slider always shows the playback range: after a file load and whenever the
  range changes, every Timeline runs ``anim.scene_range_frame`` (a msgbus subscription and
  a load_post handler defer it to a timer).
- Step 56 (docs/steps/step_56.md 「계획」 1, 2, 5): LMB on the timeline = time (Shift = red range), RMB = Maya's
  Time Slider menu, MMB = time + a notice (no Maya MMB time drag in Blender).
- Step 50 (docs/steps/step_50.md 「계획」 4, screens/20_time_slider_crop.png, 21_range_slider_crop.png): the
  header is the Range Slider row in Maya's order; Blender's Playback / Keying / View / Marker menus move
  into the animation preferences menu at its right end (``TIME_MT_editor_menus.draw_collapsible`` is
  overridden on the class, deleted on unregister). A timeline with its sidebar shown (the Allset
  layout) draws the current frame field and the 8 transport buttons there, at the right end of the
  Time Slider row like Maya (``ALLSET_PT_time_slider``); other timelines keep them in the header.
"""

import bpy

from .. import compat
from bpy.app.handlers import persistent

# Blender 5.x (docs/steps/step_53.md): the Timeline is a Dope Sheet mode; compat picks the header classes.
LEGACY_TIMELINE = compat.LEGACY_TIMELINE
header_classes = compat.timeline_header_classes


def _is_timeline(context):
    space = getattr(context, "space_data", None)
    return space is not None and getattr(space, "mode", None) == 'TIMELINE'

_ORIGINAL = {}
_OWNER = object()
_RANGE_PROPS = ("frame_start", "frame_end", "frame_preview_start", "frame_preview_end",
                "use_preview_range")


def draw_transport(layout, context):
    """Current frame field + Maya's 8 transport buttons (ui_layout.md:272-276)."""
    scene, screen = context.scene, context.screen
    row = layout.row()
    row.ui_units_x = 4.5    # Maya timeField width 90 (timeSlider.mel:223-226)
    row.prop(scene, "frame_current", text="")
    row = layout.row(align=True)
    row.operator("screen.frame_jump", text="", icon='REW').end = False
    row.operator("screen.frame_offset", text="", icon='TRIA_LEFT_BAR').delta = -1
    row.operator("screen.keyframe_jump", text="", icon='PREV_KEYFRAME').next = False
    if screen.is_animation_playing:
        row.scale_x = 2
        row.operator("screen.animation_play", text="", icon='PAUSE')
        row.scale_x = 1
    else:
        row.operator("screen.animation_play", text="", icon='PLAY_REVERSE').reverse = True
        row.operator("screen.animation_play", text="", icon='PLAY')
    row.operator("screen.keyframe_jump", text="", icon='NEXT_KEYFRAME').next = True
    row.operator("screen.frame_offset", text="", icon='TRIA_RIGHT_BAR').delta = 1
    row.operator("screen.frame_jump", text="", icon='FF').end = True


def has_slider_panel(space, area=None):
    """The timeline shows the Time Slider buttons in its sidebar (the Allset layout). With ``area``, the
    sidebar must also have room: Blender 5.x loads the 4.5 template's timeline sidebar 1 px wide
    (docs/steps/step_53.md), and then the buttons stay in the header."""
    if space is None or space.type != 'DOPESHEET_EDITOR' or not space.show_region_ui:
        return False
    if area is None:
        return True
    ui = next((r for r in area.regions if r.type == 'UI'), None)
    return ui is not None and ui.width > 20


# Range Slider row, Maya order (playbackRange.mel:288-332, :366-596; ui_layout.md:284-288).
RANGE_ITEMS = ("start", "playback start", "range", "playback end", "end", "auto key", "No Character Set",
               "No Anim Layer", "fps", "loop", "sound", "animation preferences")


def draw_header(context, layout):
    space, area = context.space_data, context.area
    if has_slider_panel(space) and not has_slider_panel(space, area):
        # Allset layout whose sidebar can't open (Blender 5.x: the Timeline mode keeps its sidebar 1 px, even in a
        # factory file — measured, step 118): one row, Range Slider first, the Time Slider buttons at the right end
        draw_range_slider(layout, context)
        layout.separator_spacer()
        draw_transport(layout, context)
        return
    if not has_slider_panel(space, area):
        layout.separator_spacer()
        draw_transport(layout, context)
        layout.separator_spacer()
    draw_range_slider(layout, context)   # Maya: the range fields start at the left edge


def draw_range_slider(layout, context):
    scene, ts = context.scene, context.tool_settings
    # animation start | playback start [range bar] playback end | animation end
    row = layout.row(align=True)
    row.ui_units_x = 4.5
    row.prop(scene, "frame_start", text="")
    row = layout.row(align=True)
    row.ui_units_x = 4.5
    row.active = scene.use_preview_range
    row.prop(scene, "frame_preview_start", text="")
    # Maya's range bar (ui_layout.md:285). In the Allset layout an empty label holds its place and
    # ui/range_bar.py draws the draggable bar there (docs/steps/step_73.md). Elsewhere Blender has no such
    # widget: the toggle = use the playback range (off = the whole animation range), the button frames it.
    from . import range_bar
    bar = layout.row(align=True)
    bar.ui_units_x = range_bar.BAR_UNITS
    if range_bar.active(context):
        bar.label(text="")
    else:
        a, b = (scene.frame_preview_start, scene.frame_preview_end) if scene.use_preview_range else \
            (scene.frame_start, scene.frame_end)
        bar.prop(scene, "use_preview_range", text="", toggle=True, icon='PREVIEW_RANGE')
        bar.operator("anim.scene_range_frame", text=f"{a}" + " " * 40 + f"{b}")
    row = layout.row(align=True)
    row.ui_units_x = 4.5
    row.active = scene.use_preview_range
    row.prop(scene, "frame_preview_end", text="")
    row = layout.row(align=True)
    row.ui_units_x = 4.5
    row.prop(scene, "frame_end", text="")

    layout.separator_spacer()
    row = layout.row(align=True)
    row.prop(ts, "use_keyframe_insert_auto", text="", toggle=True)   # Maya auto key (:585)
    sub = row.row(align=True)
    sub.active = ts.use_keyframe_insert_auto
    sub.popover(panel="TIME_PT_auto_keyframing", text="")
    for text in ("No Character Set", "No Anim Layer"):   # Maya character sets / anim layers: none in Blender
        sub = layout.row()
        sub.enabled = False
        sub.ui_units_x = 6
        sub.label(text=text, icon='DOWNARROW_HLT')
    row = layout.row()
    row.ui_units_x = 5
    fps = scene.render.fps / scene.render.fps_base
    row.menu("RENDER_MT_framerate_presets", text=f"{fps:g} fps")
    row = layout.row(align=True)
    sub = row.row(align=True)
    sub.enabled = False   # Maya loop / once / oscillate: Blender always loops
    sub.label(text="", icon='FILE_REFRESH')
    row.prop(scene, "use_audio", text="", icon='SPEAKER', invert_checkbox=True)
    row.menu("ALLSET_MT_anim_preferences", text="", icon='PREFERENCES')


class ALLSET_MT_anim_preferences(bpy.types.Menu):
    """Animation preferences (Maya's button at the right end of the Range Slider): Blender's
    timeline Playback, Keying, View and Marker menus"""
    bl_label = "Animation Preferences"

    def draw(self, context):
        lay = self.layout
        lay.popover(panel="TIME_PT_playback", text="Playback")
        lay.popover(panel="TIME_PT_keyframing_settings", text="Keying")
        lay.separator()
        lay.menu("TIME_MT_view", text="View")
        lay.menu(compat.timeline_marker_menu(), text="Marker")


class ALLSET_PT_time_slider(bpy.types.Panel):
    """Current time field and transport buttons at the right of Maya's Time Slider (timeSlider.mel:217-281)."""
    bl_space_type = 'DOPESHEET_EDITOR'
    bl_region_type = 'UI'
    bl_label = "Time Slider"
    bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space is not None and space.mode == 'TIMELINE'

    def draw(self, context):
        draw_transport(self.layout.row(align=False), context)


def _no_editor_menus(cls, context, layout):
    """TIME_MT_editor_menus.draw_collapsible while the kit is on: the menus live in
    ALLSET_MT_anim_preferences (Maya has no menus in the Range Slider)."""


# --- Time Slider hand feel (docs/steps/step_56.md 「계획」 1, 2, 5) ---------------------------------
# Maya: LMB anywhere on the Time Slider moves the time, Shift+LMB drag highlights a range, RMB = the
# Time Slider menu (others/TimeSliderMenu.mel:858-1170, labels resources/MayaStrings m_TimeSliderMenu.*).
# Blender's timeline is a Dope Sheet mode, so these sit first in the "Dopesheet" keymap and pass
# through in the Dope Sheet itself (keys are clicked there in Maya too).

RANGE_COLOR = (0.78, 0.16, 0.16, 0.35)   # Maya's red range highlight [K]
RANGE_ARROW_COLOR = (1.0, 1.0, 1.0, 0.9)
MMB_NOTICE = ("Blender always updates the scene when the time changes (no Maya MMB time drag): "
              "copy keys instead (RMB > Copy, move, RMB > Paste).")
# Time Slider items with no Blender equivalent: (label, Help Line text)
TIME_NOTICES = {
    "Paste Connect": "Blender pastes keys as they were copied: no connect (offset) paste.",
    "Play Every Frame, Free": "Blender never plays faster than the scene frame rate.",
    "Once": "Blender playback always loops.",
    "Oscillate": "Blender playback always loops.",
    "Enabled Clips": "Blender has no Time Editor clips (NLA strips instead).",
    "Sound Length": "Use the sound strip's length in the Video Sequencer.",
}


def frame_at(region, x):
    """Whole frame under window x in a timeline WINDOW region."""
    return int(round(region.view2d.region_to_view(x - region.x, 0)[0]))


def set_range(wm, a, b, on=True):
    wm.allset_time_range = (int(a), int(b))
    wm.allset_time_range_on = on


class ALLSET_OT_time_scrub(bpy.types.Operator):
    """Maya Time Slider: click or drag to move the time (Shift: highlight a range)"""
    bl_idname = "allset.time_scrub"
    bl_label = "Time Slider Scrub"
    bl_options = {'INTERNAL'}

    range: bpy.props.BoolProperty(name="Range", description="Shift-drag: highlight a time range",
                                  options={'SKIP_SAVE'})
    notice: bpy.props.BoolProperty(name="Notice", description="Show the MMB time drag notice",
                                   options={'SKIP_SAVE'})

    def invoke(self, context, event):
        region = context.region
        if not _is_timeline(context) or region is None or region.type != 'WINDOW':
            return {'PASS_THROUGH'}
        self._region = region
        self._button = event.type
        wm, scene = context.window_manager, context.scene
        self._old = (scene.frame_current, tuple(wm.allset_time_range), wm.allset_time_range_on)
        f = frame_at(region, event.mouse_x)
        if self.range:
            self._anchor = f
            set_range(wm, f, f)
        else:
            wm.allset_time_range_on = False   # a plain click drops the highlighted range (Maya)
            scene.frame_current = f
        if self.notice:
            from . import notices
            notices.show(MMB_NOTICE)
        _tag(context)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        wm, scene = context.window_manager, context.scene
        if event.type == 'MOUSEMOVE':
            f = frame_at(self._region, event.mouse_x)
            if self.range:
                set_range(wm, self._anchor, f)
            elif f != scene.frame_current:
                scene.frame_current = f
            _tag(context)
            return {'RUNNING_MODAL'}
        if event.type == self._button and event.value == 'RELEASE':
            return {'FINISHED'}
        if event.type in {'ESC', 'RIGHTMOUSE'} and event.value == 'PRESS':
            scene.frame_current = self._old[0]
            set_range(wm, *self._old[1], on=self._old[2])
            _tag(context)
            return {'CANCELLED'}
        return {'RUNNING_MODAL'}


RANGE_EDGE_PX = 8          # end-arrow zone of a highlighted range (x UI scale), docs/steps/step_84.md 「계획」 1


def range_zone(context, region, x):
    """'LEFT' / 'RIGHT' / 'MOVE' when window x is on the highlighted range of this timeline, else None."""
    from ..operators import time_range
    wm = context.window_manager
    if not getattr(wm, "allset_time_range_on", False):
        return None
    x0, x1 = range_rect(region, *wm.allset_time_range)
    edge = RANGE_EDGE_PX * (context.preferences.system.ui_scale or 1.0)
    return time_range.zone(x - region.x, x0, x1, edge)


class ALLSET_OT_time_range_drag(bpy.types.Operator):
    """Maya Time Slider range: drag the middle to move its keys, an end arrow to scale them"""
    bl_idname = "allset.time_range_drag"
    bl_label = "Move / Scale Range Keys"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    def invoke(self, context, event):
        from ..operators import time_keys, time_range
        region = context.region
        if not _is_timeline(context) or region is None or region.type != 'WINDOW':
            return {'PASS_THROUGH'}
        mode = range_zone(context, region, event.mouse_x)
        if mode is None:
            return {'PASS_THROUGH'}
        wm = context.window_manager
        a, b = sorted(wm.allset_time_range)
        curves, seen = [], set()
        for node in time_keys.nodes(context):
            for fc in time_keys.node_fcurves(node):
                if fc.as_pointer() in seen:
                    continue
                seen.add(fc.as_pointer())
                idx = [i for i, kp in enumerate(fc.keyframe_points) if time_keys._in(kp, a, b)]
                if idx:
                    curves.append((fc, idx))
        self._drag = time_range.Drag(curves, a, b)
        self._region, self._mode, self._range = region, ('MOVE' if a == b else mode), (a, b)
        self._f0 = frame_at(region, event.mouse_x)
        self._f, self._moved = self._f0, False
        self._x0 = event.mouse_x
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def _update(self, context, f):
        from ..operators import time_range
        wm = context.window_manager
        self._f = f
        self._drag.apply(self._mode, self._f0, f)
        set_range(wm, *time_range.new_range(*self._range, self._mode, self._f0, f))
        _tag(context)
        for area in context.screen.areas:
            if area.type in {'GRAPH_EDITOR', 'VIEW_3D'}:
                area.tag_redraw()

    def modal(self, context, event):
        wm, scene = context.window_manager, context.scene
        if event.type == 'MOUSEMOVE':
            f = frame_at(self._region, event.mouse_x)
            if abs(event.mouse_x - self._x0) >= 3:
                self._moved = True
            if self._moved and f != self._f:
                self._update(context, f)
            return {'RUNNING_MODAL'}
        if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            if not self._moved:
                # a click on the range = a plain Time Slider click: drop the range, go to that frame (no undo step)
                wm.allset_time_range_on = False
                scene.frame_current = self._f0
                _tag(context)
                return {'CANCELLED'}
            n = self._drag.finish(self._mode, self._f0, self._f)
            scene.frame_set(scene.frame_current)          # re-evaluate at the current time
            self.report({'INFO'}, f"{'Moved' if self._mode == 'MOVE' else 'Scaled'} {n} key(s)")
            _tag(context)
            return {'FINISHED'}
        if event.type in {'ESC', 'RIGHTMOUSE'} and event.value == 'PRESS':
            self._drag.cancel()
            set_range(wm, *self._range)
            _tag(context)
            return {'CANCELLED'}
        return {'RUNNING_MODAL'}


def _tag(context):
    for area in context.screen.areas if context.screen else ():
        if area.type == 'DOPESHEET_EDITOR':
            area.tag_redraw()


class ALLSET_OT_time_slider_menu(bpy.types.Operator):
    """Maya Time Slider menu (RMB on the Time Slider)"""
    bl_idname = "allset.time_slider_menu"
    bl_label = "Time Slider Menu"
    bl_options = {'INTERNAL'}

    def invoke(self, context, event):
        if not _is_timeline(context):
            return {'PASS_THROUGH'}
        bpy.ops.wm.call_menu(name=ALLSET_MT_time_slider.__name__)
        return {'FINISHED'}


class ALLSET_OT_time_slider_unavailable(bpy.types.Operator):
    """Time Slider item with no Blender equivalent (greyed)"""
    bl_idname = "allset.time_slider_unavailable"
    bl_label = "Not Available"
    bl_options = {'INTERNAL'}

    item: bpy.props.StringProperty(options={'SKIP_SAVE'})

    @classmethod
    def poll(cls, context):
        return False

    @classmethod
    def description(cls, context, props):
        line = TIME_NOTICES.get(props.item, "")
        if line:
            from . import notices
            notices.show(f"{props.item}: {line}")
        return f"Maya: Time Slider > {props.item}\n{line}"

    def execute(self, context):
        return {'CANCELLED'}


def _keys(layout, action, text=None, **props):
    op = layout.operator("allset.time_keys", text=text)
    op.action = action
    for k, v in props.items():
        setattr(op, k, v)
    return op


def _grey(layout, label):
    layout.operator(ALLSET_OT_time_slider_unavailable.bl_idname, text=label).item = label


class ALLSET_MT_time_slider(bpy.types.Menu):
    """Maya Time Slider menu, in Maya's order (TimeSliderMenu.mel:873-1170)"""
    bl_label = "Time Slider"

    def draw(self, context):
        lay = self.layout
        _keys(lay, "CUT", "Cut")
        _keys(lay, "COPY", "Copy")
        lay.menu("ALLSET_MT_time_slider_paste", text="Paste")
        _keys(lay, "DELETE", "Delete")
        _keys(lay, "SNAP", "Snap")
        lay.menu("ALLSET_MT_time_slider_keys", text="Keys")
        lay.menu("ALLSET_MT_time_slider_tangents", text="Tangents")
        lay.separator()
        lay.menu("ALLSET_MT_time_slider_speed", text="Playback Speed")
        lay.menu("ALLSET_MT_time_slider_looping", text="Playback Looping")
        lay.menu("ALLSET_MT_time_slider_range", text="Set Range to")
        lay.separator()
        op = lay.operator("allset.menu_run", text="Playblast...")
        op.op, op.props = "render.opengl", '{"animation": true}'


class ALLSET_MT_time_slider_paste(bpy.types.Menu):
    bl_label = "Paste"

    def draw(self, context):
        _keys(self.layout, "PASTE", "Paste")
        _grey(self.layout, "Paste Connect")


class ALLSET_MT_time_slider_keys(bpy.types.Menu):
    bl_label = "Keys"

    def draw(self, context):
        for action, label in (("TO_KEY", "Convert to Key"), ("TO_BREAKDOWN", "Convert to Breakdown"),
                              ("ADD_INBETWEEN", "Add Inbetween"), ("REMOVE_INBETWEEN", "Remove Inbetween")):
            _keys(self.layout, action, label)


class ALLSET_MT_time_slider_tangents(bpy.types.Menu):
    bl_label = "Tangents"

    def draw(self, context):
        for kind in ("SPLINE", "LINEAR", "CLAMPED", "STEPPED", "FLAT", "PLATEAU", "AUTO"):
            _keys(self.layout, "TANGENT", kind.title(), tangent=kind)


class ALLSET_MT_time_slider_speed(bpy.types.Menu):
    bl_label = "Playback Speed"

    def draw(self, context):
        lay = self.layout
        lay.prop_enum(context.scene, "sync_mode", 'FRAME_DROP', text="Real-time")
        _grey(lay, "Play Every Frame, Free")
        lay.prop_enum(context.scene, "sync_mode", 'NONE', text="Play Every Frame, Max Real-time")


class ALLSET_MT_time_slider_looping(bpy.types.Menu):
    bl_label = "Playback Looping"

    def draw(self, context):
        lay = self.layout
        _grey(lay, "Once")
        _grey(lay, "Oscillate")
        lay.label(text="Continuous", icon='CHECKMARK')


class ALLSET_MT_time_slider_range(bpy.types.Menu):
    bl_label = "Set Range to"

    def draw(self, context):
        lay = self.layout
        for mode, label in (("START_END", "Start/End"), ("MIN_MAX", "Min/Max"), ("SELECTED", "Selected")):
            lay.operator("allset.time_set_range", text=label).mode = mode
        _grey(lay, "Enabled Clips")
        _grey(lay, "Sound Length")


TIME_SLIDER_MENUS = (ALLSET_MT_time_slider, ALLSET_MT_time_slider_paste, ALLSET_MT_time_slider_keys,
                     ALLSET_MT_time_slider_tangents, ALLSET_MT_time_slider_speed,
                     ALLSET_MT_time_slider_looping, ALLSET_MT_time_slider_range)


# --- the red range highlight -----------------------------------------------------------------------

_draw_handle = []


def range_rect(region, a, b):
    """Window-region x0, x1 of frames a..b (whole frames: half a frame either side)."""
    lo, hi = min(a, b) - 0.5, max(a, b) + 0.5
    x0 = region.view2d.view_to_region(lo, 0, clip=False)[0]
    x1 = region.view2d.view_to_region(hi, 0, clip=False)[0]
    return x0, x1


def _draw_range():
    context = bpy.context
    wm = context.window_manager
    if not _is_timeline(context):
        return
    region = context.region
    _draw_keys(context, region)
    if not getattr(wm, "allset_time_range_on", False):
        return
    import gpu
    from gpu_extras.batch import batch_for_shader
    x0, x1 = range_rect(region, *wm.allset_time_range)
    h = region.height
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'TRIS', {"pos": ((x0, 0), (x1, 0), (x1, h), (x0, 0), (x1, h), (x0, h))})
    gpu.state.blend_set('ALPHA')
    shader.uniform_float("color", RANGE_COLOR)
    batch.draw(shader)
    # Maya's arrows on a highlighted range [K] (step 84): ◀ / ▶ in the end zones (scale), ◀▶ in the middle (move)
    edge = RANGE_EDGE_PX * (context.preferences.system.ui_scale or 1.0)
    k = min(edge * 0.6, h * 0.25)
    y = h * 0.5
    tris = []

    def arrow(cx, d):
        tris.extend(((cx - d * k * 0.5, y), (cx + d * k * 0.5, y + k * 0.6), (cx + d * k * 0.5, y - k * 0.6)))
    cx = (x0 + x1) * 0.5
    if x1 - x0 >= 3 * edge:
        arrow(x0 + edge * 0.5, 1)       # tip left
        arrow(x1 - edge * 0.5, -1)      # tip right
    arrow(cx - k * 0.55, 1)
    arrow(cx + k * 0.55, -1)
    batch = batch_for_shader(shader, 'TRIS', {"pos": tris})
    shader.uniform_float("color", RANGE_ARROW_COLOR)
    batch.draw(shader)
    gpu.state.blend_set('NONE')


# --- key ticks (docs/steps/step_73.md 「계획」 1) -----------------------------------------------------
# Maya draws the keys of the selected nodes (timeSliderShowKeys "active", PREF:473) as 1 px lines over the
# whole Time Slider height: displayRGBColor timeSliderKey red, timeSliderBreakdown green
# (research/maya/screens/_maya_ui_dump.json; measured in research/maya/screens/ts/ts_01_window.png).
KEY_RGB = (1.0, 0.0, 0.0, 1.0)
BREAKDOWN_RGB = (0.0, 1.0, 0.0, 1.0)


def key_frames(nodes):
    """Sorted [(frame, is_breakdown)] of the nodes' keys; a frame with any regular key is a regular key."""
    from ..operators import time_keys
    frames = {}
    for node in nodes:
        for fc in time_keys.node_fcurves(node):
            for kp in fc.keyframe_points:
                f = round(kp.co.x, 3)
                frames[f] = frames.get(f, True) and kp.type == 'BREAKDOWN'
    return sorted(frames.items())


def _draw_keys(context, region):
    from . import channel_box
    keys = key_frames(channel_box.targets(context))
    if not keys:
        return
    import gpu
    from gpu_extras.batch import batch_for_shader
    w = max(1.0, round(context.preferences.system.ui_scale or 1.0))
    h = region.height
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    for colour, breakdown in ((KEY_RGB, False), (BREAKDOWN_RGB, True)):
        tris = []
        for f, bd in keys:
            if bd != breakdown:
                continue
            x = region.view2d.view_to_region(f, 0, clip=False)[0]
            if x < -w or x > region.width + w:
                continue
            x0 = int(x)
            tris += [(x0, 0), (x0 + w, 0), (x0 + w, h), (x0, 0), (x0 + w, h), (x0, h)]
        if tris:
            shader.uniform_float("color", colour)
            batch_for_shader(shader, 'TRIS', {"pos": tris}).draw(shader)


# --- timeline view = playback range -------------------------------------------------------

def timeline_areas(wm):
    for win in wm.windows:
        for area in win.screen.areas:
            if area.type == 'DOPESHEET_EDITOR' and area.spaces.active.mode == 'TIMELINE':
                region = next((r for r in area.regions if r.type == 'WINDOW'), None)
                if region is not None:
                    yield win, area, region


def fit_timelines():
    wm = bpy.context.window_manager
    n = 0
    for win, area, region in list(timeline_areas(wm)):
        with bpy.context.temp_override(window=win, screen=win.screen, area=area, region=region):
            if bpy.ops.anim.scene_range_frame.poll():
                bpy.ops.anim.scene_range_frame()
                n += 1
    return n


def _deferred_fit():
    try:
        fit_timelines()
    except Exception:   # never break file loading / editing over a view nicety
        import traceback
        traceback.print_exc()
    return None


def _schedule():
    if not bpy.app.timers.is_registered(_deferred_fit):
        bpy.app.timers.register(_deferred_fit, first_interval=0.0)


def _subscribe():
    bpy.msgbus.clear_by_owner(_OWNER)
    for prop in _RANGE_PROPS:
        bpy.msgbus.subscribe_rna(key=(bpy.types.Scene, prop), owner=_OWNER, args=(), notify=_schedule)


@persistent
def _on_load(_dummy=None):
    _subscribe()   # file loading clears msgbus subscriptions
    if not bpy.app.background:
        _schedule()


classes = (ALLSET_MT_anim_preferences, ALLSET_PT_time_slider, ALLSET_OT_time_scrub, ALLSET_OT_time_range_drag, ALLSET_OT_time_slider_menu,
           ALLSET_OT_time_slider_unavailable, *TIME_SLIDER_MENUS)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    wm = bpy.types.WindowManager
    wm.allset_time_range_on = bpy.props.BoolProperty(
        name="Time Range", description="A Shift-dragged Time Slider range is highlighted", options={'SKIP_SAVE'})
    wm.allset_time_range = bpy.props.IntVectorProperty(name="Time Range", size=2, options={'SKIP_SAVE'})
    _draw_handle.append(bpy.types.SpaceDopeSheetEditor.draw_handler_add(_draw_range, (), 'WINDOW', 'POST_PIXEL'))
    buttons, menus = header_classes()
    if LEGACY_TIMELINE:
        menus.draw_collapsible = classmethod(_no_editor_menus)
        _ORIGINAL["draw_header"] = buttons.draw_header
        buttons.draw_header = staticmethod(draw_header)
    else:
        orig_menus, orig_header = menus.draw_collapsible, buttons.draw_header   # bound class methods
        _ORIGINAL["draw_header"] = buttons.__dict__["draw_header"]

        def _menus_5(cls, context, layout):
            if not _is_timeline(context):
                return orig_menus(context, layout)

        def _header_5(cls, context, layout):
            if _is_timeline(context):
                return draw_header(context, layout)
            return orig_header(context, layout)
        menus.draw_collapsible = classmethod(_menus_5)
        buttons.draw_header = classmethod(_header_5)
    _subscribe()
    bpy.app.handlers.load_post.append(_on_load)


def unregister():
    if _on_load in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_on_load)
    bpy.msgbus.clear_by_owner(_OWNER)
    if bpy.app.timers.is_registered(_deferred_fit):
        bpy.app.timers.unregister(_deferred_fit)
    buttons, menus = header_classes()
    if "draw_header" in _ORIGINAL:
        orig = _ORIGINAL.pop("draw_header")
        buttons.draw_header = orig if not LEGACY_TIMELINE else staticmethod(orig)
    if "draw_collapsible" in menus.__dict__:
        del menus.draw_collapsible
    while _draw_handle:
        bpy.types.SpaceDopeSheetEditor.draw_handler_remove(_draw_handle.pop(), 'WINDOW')
    wm = bpy.types.WindowManager
    del wm.allset_time_range
    del wm.allset_time_range_on
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
