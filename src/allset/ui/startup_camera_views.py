# SPDX-License-Identifier: GPL-3.0-or-later
"""A Maya persp / top / front / side panel shows its startup camera (#564): a change to a startup camera's Near / Far
Clip Plane (any of the four) or Focal Length (persp) goes to the 3D Views of that camera, as a Maya panel follows
its camera's attributes.

The kit's persp / ortho views are Blender's own views (``ui/panel_cameras.py``: ``panel_camera``), so the camera
objects (``operators/startup_cameras.py``) and the views keep their own values. When a camera value changes (a
message-bus subscription: the startup cameras are hidden, so the depsgraph reports nothing for them) or an undo /
redo runs, each startup camera is compared with what was last seen and a changed value is set on every view of the
same scene whose panel camera that is and that isn't looking through a camera. The cameras are remembered when a file loads, when Maya
mode starts and when a scene gets them, so opening a file never changes the views.
"""

import bpy
from bpy.app.handlers import persistent

# (scene name, startup camera name) -> (clip_start, clip_end, lens, sensor_width) last seen
_seen = {}


def _values(data):
    return (data.clip_start, data.clip_end, data.lens, data.sensor_width)


def _views_of(scene, name):
    """(area, space) of every 3D View showing ``scene`` whose panel camera is the startup camera ``name``."""
    from .panel_cameras import startup_name_of
    for window in bpy.context.window_manager.windows:
        if window.scene != scene:
            continue
        for area in window.screen.areas:
            if area.type != 'VIEW_3D':
                continue
            space = area.spaces.active
            rv3d = getattr(space, "region_3d", None)
            if rv3d is None or rv3d.view_perspective == 'CAMERA':
                continue
            if startup_name_of(rv3d) == name:
                yield area, space


def push(scene, ob, before, now):
    """Set the values of the startup camera ``ob`` that changed from ``before`` to ``now`` on its views."""
    from ..operators import startup_cameras
    from ..operators.key_batch import VIEW_SENSOR
    name = ob.get(startup_cameras.MARK)
    clip = before is None or now[:2] != before[:2]
    lens = name == "persp" and (before is None or now[2:] != before[2:])
    for area, space in _views_of(scene, name):
        if clip:
            space.clip_start, space.clip_end = now[0], now[1]
        if lens and now[3] > 0.0:
            space.lens = now[2] * VIEW_SENSOR / now[3]
        area.tag_redraw()


def remember(scene):
    """Remember the scene's startup cameras as they are now (no push)."""
    from ..operators import startup_cameras
    key0 = scene.name_full
    for ob in startup_cameras.cameras(scene):
        if ob.data is not None:
            _seen[key0, ob.get(startup_cameras.MARK)] = _values(ob.data)


def _remember_all():
    _seen.clear()
    try:
        for scene in bpy.data.scenes:
            remember(scene)
    except (AttributeError, ReferenceError):     # restricted context
        pass
    return None


def check(scene):
    """Compare the scene's startup cameras with what was last seen; push the changes to their views."""
    from ..operators import startup_cameras
    key0 = scene.name_full
    for ob in startup_cameras.cameras(scene):
        if ob.data is None:
            continue
        key = (key0, ob.get(startup_cameras.MARK))
        now = _values(ob.data)
        before = _seen.get(key)
        _seen[key] = now
        if before is not None and before != now:
            push(scene, ob, before, now)


_OWNER = object()
PROPS = ("clip_start", "clip_end", "lens", "sensor_width")


@persistent       # undo / redo handler: kept when a file loads
def _check_all(*_args):
    try:
        for scene in bpy.data.scenes:
            check(scene)
    except (ReferenceError, RuntimeError, AttributeError):
        pass


def _subscribe():
    bpy.msgbus.clear_by_owner(_OWNER)
    for prop in PROPS:
        bpy.msgbus.subscribe_rna(key=(bpy.types.Camera, prop), owner=_OWNER, args=(), notify=_check_all)


def _start():
    _remember_all()
    _subscribe()
    return None


@persistent
def _on_load(*_args):
    _start()      # a loaded file drops the subscriptions


def register():
    bpy.app.handlers.load_post.append(_on_load)
    bpy.app.handlers.undo_post.append(_check_all)
    bpy.app.handlers.redo_post.append(_check_all)
    bpy.app.timers.register(_start, first_interval=0.0)


def unregister():
    for handlers, fn in ((bpy.app.handlers.load_post, _on_load), (bpy.app.handlers.undo_post, _check_all),
                         (bpy.app.handlers.redo_post, _check_all)):
        if fn in handlers:
            handlers.remove(fn)
    if bpy.app.timers.is_registered(_start):
        bpy.app.timers.unregister(_start)
    bpy.msgbus.clear_by_owner(_OWNER)
    _seen.clear()
