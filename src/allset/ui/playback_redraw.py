# SPDX-License-Identifier: GPL-3.0-or-later
"""What the Maya layout redraws on each frame of playback (#344): the viewports and the animation editors, like
Maya, not the kit's Tool Box column or shelf.

Blender redraws, on each played frame, the regions its playback settings name (Timeline > Playback: 3D Viewport,
Animation Editors, ...). Two kit parts were redrawn too although nothing in them changes while playing:

- the Tool Box column is a narrow 3D View (``toolbox_column``), so "3D Viewport" redrew it on every frame (about as
  long as a small viewport takes). While playing, that switch is off on the screens that have the column
  (``Screen.use_play_3d_editors``, read by Blender after ``animation_playback_pre``) and the kit redraws the main
  region of every other 3D View itself after each frame (``_on_frame``), so the viewports update as before. The
  switch is put back when playback stops, before a save, and on load (a screen marked ``MARK`` was saved while
  playing).
- playback started from the Time Slider / an animation editor makes Blender redraw every 3D View and every Image
  Editor on each frame; the kit's shelf and Status Line rows are Image Editors drawn by the kit, so the Time Slider's
  play buttons and Maya's Play key (``allset.play``) start playback from the main viewport instead.
"""

import bpy
from bpy.app.handlers import persistent
from bpy.props import BoolProperty

MARK = "allset_play_3d"      # Screen ID property: the kit turned "3D Viewport" playback redraws off for this playback
_state = {"on": False, "skip": set()}      # on = the kit redraws the viewports; skip = Tool Box area pointers


def _toolbox_areas(screen):
    from .toolbox_column import is_toolbox
    return [a for a in screen.areas if a.type == 'VIEW_3D' and is_toolbox(a.spaces.active)]


def views_to_redraw(windows, skip):
    """The main regions of the 3D Views in ``windows`` whose area pointer is not in ``skip`` (the Tool Box columns):
    what Blender's "3D Viewport" playback setting redraws, without the columns."""
    out = []
    for window in windows:
        screen = window.screen
        if screen is None:
            continue
        for area in screen.areas:
            if area.type != 'VIEW_3D' or area.as_pointer() in skip:
                continue
            out.extend(r for r in area.regions if r.type == 'WINDOW')
    return out


def restore(screens=None):
    """Put "3D Viewport" playback redraws back on every screen the kit turned it off on. Returns how many."""
    n = 0
    for screen in (bpy.data.screens if screens is None else screens):
        if screen.get(MARK):
            screen.use_play_3d_editors = True
            del screen[MARK]
            n += 1
    return n


def turn_off(windows, columns=None):
    """Turn "3D Viewport" playback redraws off on the screens of ``windows`` that have a Tool Box column (only where
    the user left both "3D Viewport" and "Animation Editors" on: the Time Slider's playhead needs one of them) and
    mark them. Returns the pointers of their Tool Box areas (empty: nothing turned off). ``columns(screen)``: the
    Tool Box areas of a screen (tests)."""
    columns = columns or _toolbox_areas
    skip = set()
    for window in windows:
        screen = window.screen
        if screen is None or not (screen.use_play_3d_editors and screen.use_play_animation_editors):
            continue
        found = columns(screen)
        if not found:
            continue
        screen.use_play_3d_editors = False
        screen[MARK] = 1
        skip.update(a.as_pointer() for a in found)
    return skip


@persistent
def _on_playback_pre(*_args):
    restore()
    wm = bpy.context.window_manager
    skip = turn_off(wm.windows if wm is not None else ())
    _state["skip"] = skip
    _state["on"] = bool(skip)


@persistent
def _on_playback_post(*_args):
    _state["on"] = False
    _state["skip"].clear()
    restore()


@persistent
def _on_frame(*_args):
    if not _state["on"]:
        return
    try:
        for region in views_to_redraw(bpy.context.window_manager.windows, _state["skip"]):
            region.tag_redraw()
    except (AttributeError, ReferenceError):
        pass


@persistent
def _on_save_pre(*_args):
    restore()           # a saved file never keeps the switch off


@persistent
def _on_save_post(*_args):
    if _state["on"]:            # still playing: marked again, so that stopping puts the switch back
        turn_off(bpy.context.window_manager.windows)


@persistent
def _on_load(*_args):
    _state["on"] = False
    _state["skip"].clear()
    restore()


def main_view(context):
    """(window, area, region) of the main viewport to start playback from: the largest 3D View of the context's
    window, else of the first window that has one."""
    from .status_line import main_view3d
    windows = [context.window] if context.window is not None else []
    windows += [w for w in context.window_manager.windows if w not in windows]
    for window in windows:
        area, region = main_view3d(window.screen)
        if area is not None and region is not None:
            return window, area, region
    return None, None, None


class ALLSET_OT_play(bpy.types.Operator):
    """Play the animation, or stop it when it plays (Maya Play / Stop)"""
    bl_idname = "allset.play"
    bl_label = "Play / Stop"

    reverse: BoolProperty(name="Reverse", description="Play backwards", options={'SKIP_SAVE'})

    def execute(self, context):
        if any(w.screen is not None and w.screen.is_animation_playing for w in context.window_manager.windows):
            return bpy.ops.screen.animation_play()        # stops the playback, wherever it was started
        window, area, region = main_view(context)
        if area is None:
            return bpy.ops.screen.animation_play(reverse=self.reverse)
        # from the viewport: Blender redraws the viewports and animation editors on each frame, not the shelf
        with context.temp_override(window=window, screen=window.screen, area=area, region=region):
            return bpy.ops.screen.animation_play(reverse=self.reverse)


_HANDLERS = (("animation_playback_pre", _on_playback_pre), ("animation_playback_post", _on_playback_post),
             ("frame_change_post", _on_frame), ("save_pre", _on_save_pre), ("save_post", _on_save_post),
             ("load_post", _on_load))
classes = (ALLSET_OT_play,)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    for name, fn in _HANDLERS:
        getattr(bpy.app.handlers, name).append(fn)


def unregister():
    for name, fn in _HANDLERS:
        handlers = getattr(bpy.app.handlers, name)
        if fn in handlers:
            handlers.remove(fn)
    _state["on"] = False
    _state["skip"].clear()
    try:
        restore()
    except AttributeError:              # restricted bpy.data (quit)
        pass
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
