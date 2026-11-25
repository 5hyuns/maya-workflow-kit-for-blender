"""#564 in a real UI: the perspective view of a new Maya scene follows the persp camera's Near / Far Clip Plane and
Focal Length when they change; a change to top's clip planes or to another camera leaves the perspective view
alone."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, load_maya_layout, run, setup, step, view3d  # noqa: E402

C = {}


def mod(name):
    return import_module(f"{MODULE}.{name}")


def space():
    area, _r = view3d()
    return area.spaces.active


def cam(name):
    sc = mod("operators.startup_cameras")
    return next(ob for ob in sc.cameras(bpy.context.scene) if ob.get(sc.MARK) == name)


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_scene():
    sc = mod("operators.startup_cameras")
    names = sorted(sc.names(bpy.context.scene))
    check(f"a new Maya scene has the startup cameras ({names})", names == sorted(sc.NAMES))
    s = space()
    s.region_3d.view_perspective = 'PERSP'
    C["before"] = (s.clip_start, s.clip_end, s.lens)
    persp = cam("persp").data
    check(f"persp and the view start with the same clip planes ({persp.clip_start}, {persp.clip_end} / "
          f"{s.clip_start}, {s.clip_end})",
          abs(persp.clip_start - s.clip_start) < 1e-6 and abs(persp.clip_end - s.clip_end) < 1e-6)
    top = cam("top").data
    top.clip_start, top.clip_end = top.clip_start * 3.0, top.clip_end * 3.0


@step
def s_top_changed():
    s = space()
    check(f"top's clip planes leave the perspective view alone ({(s.clip_start, s.clip_end)})",
          (s.clip_start, s.clip_end, s.lens) == C["before"])
    bpy.ops.object.camera_add()
    other = bpy.context.active_object
    other.data.clip_start = 7.0


@step
def s_other_changed():
    s = space()
    check(f"another camera's Near Clip Plane leaves the view alone ({s.clip_start})",
          (s.clip_start, s.clip_end, s.lens) == C["before"])
    persp = cam("persp").data
    C["near"], C["far"] = persp.clip_start * 5.0, persp.clip_end * 0.5
    persp.clip_start, persp.clip_end = C["near"], C["far"]


@step
def s_clip_changed():
    s = space()
    check(f"persp's Near / Far Clip Plane show in the perspective view ({s.clip_start}, {s.clip_end})",
          abs(s.clip_start - C["near"]) < 1e-6 and abs(s.clip_end - C["far"]) < 1e-6)
    check(f"the view's focal length is unchanged ({s.lens})", abs(s.lens - C["before"][2]) < 1e-6)
    cam("persp").data.lens = 50.0


@step
def s_lens_changed():
    s = space()
    persp = cam("persp").data
    want = 50.0 * 72.0 / persp.sensor_width        # the view's lens is on a 72 mm sensor
    check(f"persp's Focal Length 50 shows in the perspective view (lens {s.lens:.3f}, want {want:.3f})",
          abs(s.lens - want) < 1e-4)
    check(f"the clip planes stay ({s.clip_start}, {s.clip_end})",
          abs(s.clip_start - C["near"]) < 1e-6 and abs(s.clip_end - C["far"]) < 1e-6)
    C["want"] = want
    bpy.ops.ed.undo_push(message="Focal Length 50")
    cam("persp").data.lens = 80.0
    bpy.ops.ed.undo_push(message="Focal Length 80")


@step
def s_lens_80():
    s = space()
    check(f"Focal Length 80 in the view (lens {s.lens:.3f})", abs(s.lens - C["want"] * 80.0 / 50.0) < 1e-4)
    area, region = view3d()
    with bpy.context.temp_override(area=area, region=region):
        bpy.ops.ed.undo()


@step
def s_undone():
    s = space()
    check(f"Undo takes persp back to 50 and the view with it (camera {cam('persp').data.lens}, lens {s.lens:.3f})",
          abs(cam("persp").data.lens - 50.0) < 1e-6 and abs(s.lens - C["want"]) < 1e-4)


run()
