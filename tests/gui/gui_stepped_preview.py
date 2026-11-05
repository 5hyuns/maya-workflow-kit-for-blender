"""Enable Stepped Preview in a real UI: the shown (evaluated) object holds the value of the key before the frame while
scrubbing and while playing, the keys keep their interpolation, and turning it off shows the curves again."""

import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, run, setup, step, win  # noqa: E402

C = {}


def shown_x():
    ob = bpy.data.objects["StepCube"]
    dg = bpy.context.evaluated_depsgraph_get()
    return round(ob.evaluated_get(dg).matrix_world.translation.x, 4)


def fc():
    ob = bpy.data.objects["StepCube"]
    return ob.animation_data.action.layers[0].strips[0].channelbags[0].fcurves.find("location", index=0)


def held(f):
    """The value the stepped curve shows at frame f (keys 1: 0, 6: 5, 12: 12)."""
    return 0.0 if f < 6 else 5.0 if f < 12 else 12.0


@step
def s_setup():
    setup()
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end, sc.use_preview_range = 1, 12, False
    sc.render.fps, sc.sync_mode = 24, 'NONE'
    mesh = bpy.data.meshes.new("StepCube")
    ob = bpy.data.objects.new("StepCube", mesh)
    sc.collection.objects.link(ob)
    for f, v in ((1, 0.0), (6, 5.0), (12, 12.0)):
        ob.location.x = v
        ob.keyframe_insert("location", index=0, frame=f)
    C["interp"] = [k.interpolation for k in fc().keyframe_points]
    sc.frame_set(4)
    sc.allset_stepped_preview = True


@step
def s_on():
    check(f"turned on at frame 4: shown x = key 1's 0 ({shown_x()})", shown_x() == 0.0)
    bpy.context.scene.frame_set(9)


@step
def s_scrub():
    check(f"scrubbed to 9: shown x = key 6's 5 ({shown_x()})", shown_x() == 5.0)
    C["seen"] = []
    bpy.app.handlers.frame_change_post.append(_note)
    with bpy.context.temp_override(window=win(), screen=win().screen):
        bpy.ops.screen.animation_play()


@bpy.app.handlers.persistent
def _note(scene, *_args):
    C["seen"].append((scene.frame_current, round(bpy.data.objects["StepCube"].location.x, 4)))


@step
def s_playing():
    sc = bpy.context.scene
    bad = [(f, x) for f, x in C["seen"] if x != held(f)]
    check(f"while playing every frame holds the key before it ({C['seen'][:8]}, wrong {bad[:4]})", not bad)
    f = sc.frame_current
    check(f"while playing (frame {f}): shown x = {held(f)} ({shown_x()})", shown_x() == held(f))
    with bpy.context.temp_override(window=win(), screen=win().screen):
        bpy.ops.screen.animation_cancel(restore_frame=False)
    bpy.app.handlers.frame_change_post.remove(_note)
    check(f"played some frames ({C['seen'][:6]})", len(C["seen"]) > 3)
    sc.frame_set(9)


@step
def s_keys_kept():
    check(f"keys keep their interpolation ({[k.interpolation for k in fc().keyframe_points]})",
          [k.interpolation for k in fc().keyframe_points] == C["interp"])
    bpy.context.scene.allset_stepped_preview = False


@step
def s_off():
    want = round(fc().evaluate(9), 4)
    check(f"turned off: shown x = the curve's own {want} ({shown_x()})", abs(shown_x() - want) < 1e-3 and want != 5.0)


run()
