"""Playback Looping like Maya during real playback: Once stops on the last frame, Oscillate turns round at both ends,
and play pressed again on the last frame in Once starts from the first frame."""

import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, run, setup, step, win  # noqa: E402

C = {"frames": []}


def playing():
    return any(w.screen.is_animation_playing for w in bpy.context.window_manager.windows)


def play(reverse=False):
    with bpy.context.temp_override(window=win(), screen=win().screen):
        bpy.ops.screen.animation_play(reverse=reverse)


def stop():
    with bpy.context.temp_override(window=win(), screen=win().screen):
        bpy.ops.screen.animation_cancel(restore_frame=False)


@bpy.app.handlers.persistent
def _record(scene, *_args):
    C["frames"].append(scene.frame_current)


@step
def s_setup():
    setup()
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end, sc.use_preview_range = 1, 12, False
    sc.render.fps, sc.sync_mode = 24, 'NONE'
    sc.allset_playback_loop = 'ONCE'
    sc.frame_set(1)
    bpy.app.handlers.frame_change_post.append(_record)
    play()


@step
def s_wait1():
    pass


@step
def s_wait2():
    pass


@step
def s_once_stopped():
    sc = bpy.context.scene
    check(f"Once: playback stopped ({playing()})", not playing())
    check(f"Once: on the last frame ({sc.frame_current})", sc.frame_current == 12)
    check("Once: never wrapped to the first frame", 1 not in C["frames"][1:])
    C["frames"].clear()
    play()                                   # again from the last frame: starts over


@step
def s_wait3():
    pass


@step
def s_wait4():
    pass


@step
def s_once_again():
    sc = bpy.context.scene
    f = C["frames"]
    check(f"Once again from the end: played from the start ({f[:4]})", f[:1] == [1] and 6 in f)
    check(f"Once again: stopped on the last frame ({sc.frame_current})", not playing() and sc.frame_current == 12)
    sc.allset_playback_loop = 'OSCILLATE'
    sc.frame_set(1)
    C["frames"].clear()
    play()


@step
def s_wait5():
    pass


@step
def s_wait6():
    pass


@step
def s_wait7():
    pass


@step
def s_oscillate():
    f = C["frames"]
    check(f"Oscillate: still playing ({playing()})", playing())
    top = f.index(12) if 12 in f else -1
    check(f"Oscillate: reached the end ({f})", top >= 0)
    after = f[top + 1:top + 4]
    check(f"Oscillate: turned round at the end ({after})", after[:2] == [11, 10] or after[:3] == [12, 11, 10])
    low = [i for i, v in enumerate(f) if v == 1 and i > top]
    check(f"Oscillate: turned round at the start too ({f[low[0]:low[0] + 3] if low else f})",
          bool(low) and f[low[0] + 1:low[0] + 2] in ([2], [1]))
    stop()
    bpy.context.scene.allset_playback_loop = 'CONTINUOUS'
    bpy.app.handlers.frame_change_post.remove(_record)


run()
