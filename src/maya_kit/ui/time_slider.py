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
"""

import bpy
from bl_ui import space_time
from bpy.app.handlers import persistent

_ORIGINAL = {}
_OWNER = object()
_RANGE_PROPS = ("frame_start", "frame_end", "frame_preview_start", "frame_preview_end",
                "use_preview_range")


def draw_header(context, layout):
    scene, ts, screen = context.scene, context.tool_settings, context.screen
    layout.separator_spacer()

    # Time Slider buttons, Maya order (ui_layout.md:274-276).
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

    row = layout.row()
    row.scale_x = 0.95
    row.prop(scene, "frame_current", text="")

    layout.separator_spacer()

    # Range Slider (ui_layout.md:285): animation start | playback start [toggle] playback end | animation end.
    row = layout.row(align=True)
    row.scale_x = 0.8
    row.prop(scene, "frame_start", text="")
    inner = row.row(align=True)
    inner.active = scene.use_preview_range
    inner.prop(scene, "frame_preview_start", text="")
    row.prop(scene, "use_preview_range", text="", toggle=True, icon='PREVIEW_RANGE')
    inner = row.row(align=True)
    inner.active = scene.use_preview_range
    inner.prop(scene, "frame_preview_end", text="")
    row.prop(scene, "frame_end", text="")

    row = layout.row(align=True)
    row.prop(ts, "use_keyframe_insert_auto", text="", toggle=True)   # Maya auto key (:285)
    sub = row.row(align=True)
    sub.active = ts.use_keyframe_insert_auto
    sub.popover(panel="TIME_PT_auto_keyframing", text="")


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


def register():
    _ORIGINAL["draw_header"] = space_time.TIME_HT_editor_buttons.draw_header
    space_time.TIME_HT_editor_buttons.draw_header = staticmethod(draw_header)
    _subscribe()
    bpy.app.handlers.load_post.append(_on_load)


def unregister():
    if _on_load in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_on_load)
    bpy.msgbus.clear_by_owner(_OWNER)
    if bpy.app.timers.is_registered(_deferred_fit):
        bpy.app.timers.unregister(_deferred_fit)
    if "draw_header" in _ORIGINAL:
        space_time.TIME_HT_editor_buttons.draw_header = staticmethod(_ORIGINAL.pop("draw_header"))
