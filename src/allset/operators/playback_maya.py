# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya Playback > Playback Looping (Continuous / Once / Oscillate) and Playback > Enable Stepped Preview.

Looping: Blender's playback always wraps around the range. While the animation plays, ``_on_frame`` watches the
frames: Once stops on the last frame of the range (the first frame when playing backward), Oscillate turns the
playback round at either end. The decision is bpy-free (``loop_step``); stopping / turning round runs from a timer,
outside the frame handler.

Stepped Preview: every time-keyed F-curve shows as if its keys were stepped, while playing and scrubbing; the keys,
their interpolation and the Graph Editor curves stay as they are (driver curves are left alone). Blender has no
stepped-evaluation switch, so after each frame change (and after keys change) the kit writes the value of the key
before the current frame into each animated channel (``apply_stepped``). Kit Auto Key compares channels with these
shown values (``curve_value``), so scrubbing keys nothing. Final renders (F12) show the curves' own values.
"""

import time

import bpy
from bpy.app.handlers import persistent

from .. import compat

LOOP_ITEMS = (
    ('CONTINUOUS', "Continuous", "Playback starts again at the other end of the range"),
    ('ONCE', "Once", "Playback stops at the end of the range"),
    ('OSCILLATE', "Oscillate", "Playback runs forward and backward between the ends of the range"),
)
LOOP_NEXT = {'CONTINUOUS': 'ONCE', 'ONCE': 'OSCILLATE', 'OSCILLATE': 'CONTINUOUS'}
STASH = "allset_stepped_keys"
INTERP = ('CONSTANT', 'LINEAR', 'BEZIER', 'SINE', 'QUAD', 'CUBIC', 'QUART', 'QUINT', 'EXPO', 'CIRC', 'BACK',
          'BOUNCE', 'ELASTIC')


# --- looping ------------------------------------------------------------------------------------------

def loop_step(mode, prev, cur, direction, start, end, first):
    """One playback frame step from ``prev`` to ``cur`` over the range start..end.

    ``direction`` is +1 / -1 (the known playback direction, 0 = not known yet), ``first`` = the first step after the
    playback started. Returns ``(direction, action, frame)``: action None (go on), 'STOP' (stop on ``frame``) or
    'TURN' (play the other way from ``frame``)."""
    d = cur - prev
    span = max(end - start, 1)
    wrapped = abs(d) > span / 2          # Blender jumped to the other end of the range
    if d:
        step = 1 if d > 0 else -1
        direction = -step if wrapped else step
    if mode == 'CONTINUOUS' or not direction or first:
        return direction, None, cur
    edge = end if direction > 0 else start
    if not wrapped and (cur - edge) * direction < 0:
        return direction, None, cur
    return direction, ('STOP' if mode == 'ONCE' else 'TURN'), edge


_play = {"prev": None, "t": 0.0, "dir": 0, "pending": False}


def _playing_window():
    wm = bpy.context.window_manager
    for w in (wm.windows if wm else ()):
        if w.screen is not None and w.screen.is_animation_playing:
            return w
    return None


def _range(scene):
    if scene.use_preview_range:
        return scene.frame_preview_start, scene.frame_preview_end
    return scene.frame_start, scene.frame_end


def _finish(action, frame, direction):
    _play["pending"] = False
    w = _playing_window()
    if w is None:
        return None
    scene = w.scene
    with bpy.context.temp_override(window=w, screen=w.screen):
        bpy.ops.screen.animation_cancel(restore_frame=False)
        _play["prev"] = None
        if scene.frame_current != frame:
            scene.frame_set(frame)
        if action == 'TURN':
            bpy.ops.screen.animation_play(reverse=direction > 0)
            _play.update(prev=frame, t=time.monotonic(), dir=-direction)
    return None


@persistent
def _on_frame(scene, *_args):
    mode = getattr(scene, "allset_playback_loop", 'CONTINUOUS')
    w = _playing_window() if mode != 'CONTINUOUS' else None
    if w is None or w.scene != scene:
        _play["prev"] = None
        return
    now, cur, prev = time.monotonic(), scene.frame_current, _play["prev"]
    fps = scene.render.fps / (scene.render.fps_base or 1.0)
    first = prev is None or now - _play["t"] > max(0.5, 3.0 / max(fps, 1.0))
    if first:
        _play["dir"] = 0
    start, end = _range(scene)
    direction, action, frame = loop_step(mode, cur if prev is None else prev, cur, _play["dir"], start, end, first)
    _play.update(prev=cur, t=now, dir=direction)
    if action and not _play["pending"]:
        _play["pending"] = True
        bpy.app.timers.register(lambda: _finish(action, frame, direction), first_interval=0.0)


class ALLSET_OT_playback_loop_cycle(bpy.types.Operator):
    """Playback looping: Continuous, Once, Oscillate (click for the next one)"""
    bl_idname = "allset.playback_loop_cycle"
    bl_label = "Playback Looping"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        sc = context.scene
        sc.allset_playback_loop = LOOP_NEXT[sc.allset_playback_loop]
        return {'FINISHED'}


LOOP_ICONS = {'CONTINUOUS': 'FILE_REFRESH', 'ONCE': 'FORWARD', 'OSCILLATE': 'ARROW_LEFTRIGHT'}


# --- stepped preview ----------------------------------------------------------------------------------

ANIMATED = ("objects", "shape_keys", "materials", "meshes", "armatures", "curves", "cameras", "lights", "worlds",
            "scenes", "node_groups", "textures", "lattices", "grease_pencils", "speakers", "particles")


def active(scene=None):
    scene = scene if scene is not None else bpy.context.scene
    return bool(getattr(scene, "allset_stepped_preview", False))


def _held_key(fc, t):
    """Time of the key a stepped curve holds at ``t``: the last key before ``t``, or None where the curve's own value
    is already that (on a key, before the first key, after the last one)."""
    pts = fc.keyframe_points
    lo, hi = 0, len(pts) - 1
    if hi < 1 or t <= pts[0].co.x + 1e-6 or t >= pts[hi].co.x - 1e-6:
        return None
    while lo < hi - 1:             # pts[lo].co.x < t < pts[hi].co.x
        mid = (lo + hi) // 2
        if pts[mid].co.x <= t + 1e-6:
            lo = mid
        else:
            hi = mid
    k = pts[lo].co.x
    return None if abs(k - t) < 1e-6 else k


def curve_value(fc, frame, scene=None):
    """What the curve shows at ``frame``: stepped while Enable Stepped Preview is on (Auto Key compares with this)."""
    if active(scene):
        k = _held_key(fc, frame)
        if k is not None:
            return fc.evaluate(k)
    return fc.evaluate(frame)


def _animated_ids():
    for name in ANIMATED:
        for idb in getattr(bpy.data, name, ()):
            ad = getattr(idb, "animation_data", None)
            if ad is not None and ad.action is not None:
                yield idb


def _owner(idb, path):
    """(owner, attribute or key, is a custom property) of an F-curve data path."""
    if path.endswith('"]'):
        i = path.rfind('["')
        return (idb.path_resolve(path[:i]) if i else idb), path[i + 2:-2], True
    if "." in path:
        head, attr = path.rsplit(".", 1)
        return idb.path_resolve(head), attr, False
    return idb, path, False


def _write(idb, fc, value):
    try:
        owner, attr, custom = _owner(idb, fc.data_path)
        cur = owner[attr] if custom else getattr(owner, attr)
        arr = not isinstance(cur, (int, float, bool))
        old = cur[fc.array_index] if arr else cur
        if isinstance(old, bool) or not isinstance(old, (int, float)):
            return
        new = int(round(value)) if isinstance(old, int) else value
        if abs(old - new) < 1e-7:
            return
        if arr:
            cur[fc.array_index] = new
        elif custom:
            owner[attr] = new
        else:
            setattr(owner, attr, new)
    except (ValueError, KeyError, IndexError, TypeError, AttributeError, RuntimeError):
        pass


def apply_stepped(scene):
    """Show every animation curve stepped at the current frame: the channels get the value of the key before it.
    The keys themselves are not changed (Blender has no stepped-evaluation switch: the shown values are written over
    the evaluated ones, until the next frame change)."""
    t = scene.frame_current + scene.frame_subframe
    for idb in _animated_ids():
        for fc in compat.id_fcurves(idb):
            if fc.mute or not fc.is_valid:
                continue
            k = _held_key(fc, t)
            if k is not None:
                _write(idb, fc, fc.evaluate(k))


# Files saved by an earlier build of this preview have their keys set to Constant, with each key's own interpolation
# kept on the action: they get it back.
def _bags(action):
    """(key, F-curves) for each channelbag of the action."""
    return [(f"{n}.{bag.slot_handle}", bag.fcurves) for n, bag in enumerate(compat.fcurve_owners(action))]


def _curve_key(bag_key, fc):
    return f"{bag_key}|{fc.data_path}|{fc.array_index}"


def read_stash(action):
    """{curve key: (frames, interpolation indices)} kept on the action (a list: ID property names are short)."""
    out = {}
    for ent in action.get(STASH, ()):
        out[ent["k"]] = (list(ent["f"]), list(ent["i"]))
    return out


def restore_pairs(key_frames, stash_frames):
    """For each key frame, the index of its stash entry (or None): same frame first, then the left-over keys and
    entries in frame order (keys moved while the preview was on)."""
    out = [None] * len(key_frames)
    by_frame = {}
    for j in sorted(range(len(stash_frames)), key=lambda j: stash_frames[j], reverse=True):
        by_frame.setdefault(round(stash_frames[j] * 1e3), []).append(j)
    for i, f in enumerate(key_frames):
        hits = by_frame.get(round(f * 1e3))
        if hits:
            out[i] = hits.pop()
    used = {j for j in out if j is not None}
    rest = sorted((j for j in range(len(stash_frames)) if j not in used), key=lambda j: stash_frames[j])
    for i, j in zip([i for i, v in enumerate(out) if v is None], rest):
        out[i] = j
    return out


def restore_action(action):
    """Give an action's keys back the interpolation an earlier build of the preview kept on it."""
    if STASH not in action:
        return
    stash = read_stash(action)
    for bag_key, fcurves in _bags(action):
        for fc in fcurves:
            ent = stash.get(_curve_key(bag_key, fc))
            if ent is None:
                continue
            frames, kinds = ent
            pts = fc.keyframe_points
            pairs = restore_pairs([k.co.x for k in pts], frames)
            for k, j in zip(pts, pairs):
                if j is not None:
                    k.interpolation = INTERP[kinds[j]]
            # keys added while the preview was on came in Constant from their stepped neighbour: like any new
            # Blender key they take the interpolation of the key before them (the first key: the one after it)
            for i, (k, j) in enumerate(zip(pts, pairs)):
                if j is None:
                    near = [pts[n] for n in (i - 1, i + 1) if 0 <= n < len(pts) and pairs[n] is not None]
                    if near:
                        k.interpolation = near[0].interpolation
            fc.update()
    del action[STASH]


def restore_all():
    for action in bpy.data.actions:
        if STASH in action:
            restore_action(action)


def _redraw(context):
    wm = context.window_manager
    for w in (wm.windows if wm else ()):
        for area in w.screen.areas:
            area.tag_redraw()


def _update_stepped(self, context):
    restore_all()
    if self.allset_stepped_preview:
        apply_stepped(self)
    else:                                    # the curves' own values again
        self.frame_set(self.frame_current, subframe=self.frame_subframe)
    _redraw(context)


_busy = []


def _guarded(fn, scene):
    if _busy:
        return
    _busy.append(1)
    try:
        fn(scene)
    finally:
        _busy.clear()


@persistent
def _on_frame_stepped(scene, depsgraph=None):
    if active(scene) and not (depsgraph is not None and depsgraph.mode == 'RENDER'):
        _guarded(apply_stepped, scene)


@persistent
def _on_depsgraph(scene, depsgraph):
    # keys set or edited: Blender shows the curves' own values again, step them
    if active(scene) and depsgraph.id_type_updated('ACTION'):
        _guarded(apply_stepped, scene)


@persistent
def _on_reload(*_args):
    try:
        restore_all()
        scene = bpy.context.scene
    except (AttributeError, RuntimeError):
        return
    if scene is not None and active(scene):
        _guarded(apply_stepped, scene)


classes = (ALLSET_OT_playback_loop_cycle,)

_HANDLERS = (("frame_change_post", _on_frame), ("frame_change_post", _on_frame_stepped),
             ("depsgraph_update_post", _on_depsgraph), ("load_post", _on_reload), ("undo_post", _on_reload),
             ("redo_post", _on_reload))


def register_props():
    bpy.types.Scene.allset_playback_loop = bpy.props.EnumProperty(
        name="Playback Looping", items=LOOP_ITEMS, default='CONTINUOUS',
        description="What playback does at the end of the range, like Maya's Playback Looping")
    bpy.types.Scene.allset_stepped_preview = bpy.props.BoolProperty(
        name="Enable Stepped Preview", default=False, update=_update_stepped,
        description="Play and scrub every animation curve as if its keys were stepped; the keys and their tangents "
                    "stay as they are")


def register_handlers():
    for name, fn in _HANDLERS:
        getattr(bpy.app.handlers, name).append(fn)
    if hasattr(bpy.data, "actions"):
        _on_reload()


def unregister():
    for name, fn in _HANDLERS:
        hs = getattr(bpy.app.handlers, name)
        if fn in hs:
            hs.remove(fn)
    try:
        for sc in bpy.data.scenes:
            if getattr(sc, "allset_stepped_preview", False):
                sc.frame_set(sc.frame_current, subframe=sc.frame_subframe)   # the curves' own values
    except (AttributeError, RuntimeError):
        pass
    for name in ("allset_stepped_preview", "allset_playback_loop"):
        if hasattr(bpy.types.Scene, name):
            delattr(bpy.types.Scene, name)
