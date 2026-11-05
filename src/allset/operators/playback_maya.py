# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya Playback > Playback Looping (Continuous / Once / Oscillate) and Playback > Enable Stepped Preview.

Looping: Blender's playback always wraps around the range. While the animation plays, ``_on_frame`` watches the
frames: Once stops on the last frame of the range (the first frame when playing backward), Oscillate turns the
playback round at either end. The decision is bpy-free (``loop_step``); stopping / turning round runs from a timer,
outside the frame handler.

Stepped Preview: every time-keyed F-curve plays as if its keys were stepped, also while scrubbing, and the curves get
their own interpolation back when it is turned off (driver curves are left alone). Blender has no evaluation-only
switch for this, so the kit sets the keys to Constant and keeps each key's own interpolation on the action
(``STASH``): keys added or re-set while the preview is on are stepped too and keep the interpolation they came with.
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


def _write_stash(action, stash):
    action[STASH] = [{"k": k, "f": f, "i": i} for k, (f, i) in stash.items()]


def step_action(action):
    """Step every key of the action that is not Constant yet, keeping its interpolation in the stash. True if a key
    changed."""
    stash = None
    for bag_key, fcurves in _bags(action):
        for fc in fcurves:
            pts = fc.keyframe_points
            moving = [k for k in pts if k.interpolation != 'CONSTANT']
            if not moving:
                continue
            if stash is None:
                stash = read_stash(action)
            ck = _curve_key(bag_key, fc)
            if ck not in stash:  # first time: every key of the curve, the Constant ones too
                stash[ck] = ([k.co.x for k in pts], [INTERP.index(k.interpolation) for k in pts])
            else:                # keys added or re-set while the preview is on
                frames, kinds = stash[ck]
                for k in moving:
                    _drop(frames, kinds, k.co.x)
                    frames.append(k.co.x)
                    kinds.append(INTERP.index(k.interpolation))
            for k in moving:
                k.interpolation = 'CONSTANT'
            fc.update()
    if stash is None:
        return False
    _write_stash(action, stash)
    return True


def _drop(frames, kinds, frame):
    for j in range(len(frames) - 1, -1, -1):
        if abs(frames[j] - frame) < 1e-4:
            del frames[j], kinds[j]


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


def _scenes_on():
    return any(getattr(s, "allset_stepped_preview", False) for s in bpy.data.scenes)


def step_all():
    changed = False
    for action in bpy.data.actions:
        changed = step_action(action) or changed
    return changed


def restore_all():
    for action in bpy.data.actions:
        restore_action(action)


def _update_stepped(self, context):
    if self.allset_stepped_preview:
        step_all()
    elif not _scenes_on():
        restore_all()
    for w in context.window_manager.windows:
        for area in w.screen.areas:
            area.tag_redraw()


_busy = []


@persistent
def _on_depsgraph(scene, depsgraph):
    if _busy or not getattr(scene, "allset_stepped_preview", False) or not depsgraph.id_type_updated('ACTION'):
        return
    _busy.append(1)
    try:
        step_all()
    finally:
        _busy.clear()


classes = (ALLSET_OT_playback_loop_cycle,)


def register_props():
    bpy.types.Scene.allset_playback_loop = bpy.props.EnumProperty(
        name="Playback Looping", items=LOOP_ITEMS, default='CONTINUOUS',
        description="What playback does at the end of the range, like Maya's Playback Looping")
    bpy.types.Scene.allset_stepped_preview = bpy.props.BoolProperty(
        name="Enable Stepped Preview", default=False, update=_update_stepped,
        description="Play and scrub every animation curve as if its keys were stepped; the curves keep their own "
                    "tangents for when this is off")


def register_handlers():
    bpy.app.handlers.frame_change_post.append(_on_frame)
    bpy.app.handlers.depsgraph_update_post.append(_on_depsgraph)


def unregister():
    for hs, fn in ((bpy.app.handlers.frame_change_post, _on_frame),
                   (bpy.app.handlers.depsgraph_update_post, _on_depsgraph)):
        if fn in hs:
            hs.remove(fn)
    try:
        if hasattr(bpy.data, "scenes") and _scenes_on():
            restore_all()
            for s in bpy.data.scenes:
                s.allset_stepped_preview = False
    except (AttributeError, RuntimeError):
        pass
    for name in ("allset_stepped_preview", "allset_playback_loop"):
        if hasattr(bpy.types.Scene, name):
            delattr(bpy.types.Scene, name)
