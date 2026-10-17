# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya Time Slider + Range Slider in the Timeline header, and a timeline view that
follows the playback range.

, (:272-282: 8 transport buttons, current time
field, auto key), (:284-286: animation start, playback start, [range], playback end,
animation end). Blender form:
- ``bl_ui.space_time.TIME_HT_editor_buttons.draw_header`` (a plain class, not in bpy.types)
  is swapped for ``draw_header`` below and restored on unregister.
- Maya's animation range = scene frame_start/end; its playback range = the preview range
  (``use_preview_range`` off: playback = animation range, inner fields greyed).
- Maya's time slider always shows the playback range: after a file load and whenever the
  range changes, every Timeline runs ``anim.scene_range_frame`` (a msgbus subscription and
  a load_post handler defer it to a timer).
- Step 50: the
  header is the Range Slider row in Maya's order; Blender's Playback / Keying / View / Marker menus move
  into the animation preferences menu at its right end (``TIME_MT_editor_menus.draw_collapsible`` is
  overridden on the class, deleted on unregister). A timeline with its sidebar shown (the MayaKit
  layout) draws the current frame field and the 8 transport buttons there, at the right end of the
  Time Slider row like Maya (``MAYAKIT_PT_time_slider``); other timelines keep them in the header.
"""

import bpy
from bl_ui import space_time
from bpy.app.handlers import persistent

# Blender 5.x: the Timeline is a Dope Sheet mode and bl_ui.space_time has no
# TIME_HT_editor_buttons / TIME_MT_editor_menus; the timeline header is DOPESHEET_HT_editor_buttons.draw_header
# and DOPESHEET_MT_editor_menus with ``mode == 'TIMELINE'`` ($S52\startupl_ui\space_dopesheet.py:198-230,
# :395-412). There the kit wraps the Dope Sheet ones and keeps other modes untouched.
LEGACY_TIMELINE = hasattr(space_time, "TIME_HT_editor_buttons")


def header_classes():
    """(class whose ``draw_header`` draws the timeline buttons, class whose ``draw_collapsible`` draws
    the timeline menus) of this Blender."""
    if LEGACY_TIMELINE:
        return space_time.TIME_HT_editor_buttons, space_time.TIME_MT_editor_menus
    from bl_ui import space_dopesheet
    return space_dopesheet.DOPESHEET_HT_editor_buttons, space_dopesheet.DOPESHEET_MT_editor_menus


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
    row.ui_units_x = 4.5    # Maya timeField width 90 (Maya-226)
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
    """The timeline shows the Time Slider buttons in its sidebar (the MayaKit layout). With ``area``, the
    sidebar must also have room: Blender 5.x loads the 4.5 template's timeline sidebar 1 px wide
, and then the buttons stay in the header."""
    if space is None or space.type != 'DOPESHEET_EDITOR' or not space.show_region_ui:
        return False
    if area is None:
        return True
    ui = next((r for r in area.regions if r.type == 'UI'), None)
    return ui is not None and ui.width > 20


# Range Slider row, Maya order (Maya-332, :366-596; ui_layout.md:284-288).
RANGE_ITEMS = ("start", "playback start", "range", "playback end", "end", "auto key", "No Character Set",
               "No Anim Layer", "fps", "loop", "sound", "animation preferences")


def draw_header(context, layout):
    if not has_slider_panel(context.space_data, context.area):
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
    # Maya's range bar (ui_layout.md:285): Blender has no such widget. The toggle = use the playback range
    # (off = play the whole animation range), the bar shows the range and frames the time slider on it.
    bar = layout.row(align=True)
    bar.ui_units_x = 18
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
    row.menu("MAYAKIT_MT_anim_preferences", text="", icon='PREFERENCES')


class MAYAKIT_MT_anim_preferences(bpy.types.Menu):
    """Animation preferences (Maya's button at the right end of the Range Slider): Blender's
    timeline Playback, Keying, View and Marker menus"""
    bl_label = "Animation Preferences"

    def draw(self, context):
        lay = self.layout
        lay.popover(panel="TIME_PT_playback", text="Playback")
        lay.popover(panel="TIME_PT_keyframing_settings", text="Keying")
        lay.separator()
        lay.menu("TIME_MT_view", text="View")
        lay.menu("TIME_MT_marker", text="Marker")


class MAYAKIT_PT_time_slider(bpy.types.Panel):
    """Current time field and transport buttons at the right of Maya's Time Slider (Maya-281)."""
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
    MAYAKIT_MT_anim_preferences (Maya has no menus in the Range Slider)."""


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


classes = (MAYAKIT_MT_anim_preferences, MAYAKIT_PT_time_slider)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
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
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
