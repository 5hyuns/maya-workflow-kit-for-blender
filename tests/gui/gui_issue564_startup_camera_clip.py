"""#564 in a real UI: the perspective view of a new Maya scene follows the persp camera's Near / Far Clip Plane and
Focal Length when they change; a change to top's clip planes or to another camera leaves the perspective view
alone."""

import os
import sys
from importlib import import_module

import bpy
from mathutils import Quaternion, Vector

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
    # an edit of persp's translate (Channel Box / Attribute Editor), as its own undo step
    persp = cam("persp")
    C["eye0"] = persp.location.copy()
    persp.location = (persp.location.x + 3.0, persp.location.y, persp.location.z)
    bpy.ops.ed.undo_push(message="persp translate")


def eye(rv3d):
    return rv3d.view_location + rv3d.view_rotation @ Vector((0.0, 0.0, rv3d.view_distance))


@step
def s_translated():
    rv3d = space().region_3d
    persp = cam("persp")
    check(f"persp's translate moves the perspective view (eye {tuple(round(v, 3) for v in eye(rv3d))}, camera "
          f"{tuple(round(v, 3) for v in persp.location)})", (eye(rv3d) - persp.location).length < 1e-4)
    area, region = view3d()
    with bpy.context.temp_override(area=area, region=region):
        bpy.ops.ed.undo()


@step
def s_translate_undone():
    rv3d = space().region_3d
    persp = cam("persp")
    check(f"Undo of the translate edit takes persp and the view back ({tuple(round(v, 3) for v in persp.location)})",
          (persp.location - C["eye0"]).length < 1e-4 and (eye(rv3d) - C["eye0"]).length < 1e-4)
    # the view tumbles (what a view tool does to the view)
    rv3d.view_rotation = Quaternion((0.0, 0.0, 1.0), 0.6) @ rv3d.view_rotation


@step
def s_tumbled():
    rv3d = space().region_3d
    persp = cam("persp")
    rot = persp.matrix_basis.to_quaternion()
    check(f"tumbling the view moves persp with it (eye gap {(eye(rv3d) - persp.location).length:.5f})",
          (eye(rv3d) - persp.location).length < 1e-4 and rot.rotation_difference(rv3d.view_rotation).angle < 1e-4)
    C["eye1"], C["rot1"] = eye(rv3d).copy(), rv3d.view_rotation.copy()
    area, region = view3d()
    with bpy.context.temp_override(window=bpy.context.window_manager.windows[0], area=area, region=region):
        bpy.ops.mesh.primitive_cube_add('EXEC_DEFAULT', True)      # an undo step after the tumble


@step
def s_cube():
    area, region = view3d()
    with bpy.context.temp_override(area=area, region=region):
        bpy.ops.ed.undo()


@step
def s_undo_after_tumble():
    rv3d = space().region_3d
    persp = cam("persp")
    check(f"Undo doesn't move the view: camera moves aren't undoable (eye moved {(eye(rv3d) - C['eye1']).length:.5f})",
          (eye(rv3d) - C["eye1"]).length < 1e-4 and C["rot1"].rotation_difference(rv3d.view_rotation).angle < 1e-4)
    check(f"persp stays where the view is (gap {(persp.location - C['eye1']).length:.5f})",
          (persp.location - C["eye1"]).length < 1e-4)
    # the view turns to top (orthographic, looking down)
    rv3d.view_perspective = 'ORTHO'
    rv3d.view_rotation = Quaternion()
    C["dist0"] = rv3d.view_distance


@step
def s_top_view():
    top = cam("top")
    C["top_loc"] = top.location.copy()
    check(f"turning the view to top leaves top's place alone ({tuple(round(v, 2) for v in top.location)})",
          abs(space().region_3d.view_distance - C["dist0"]) < 1e-6)
    top.data.ortho_scale = 50.0 * mod("operators.units").maya_unit(bpy.context.scene)


@step
def s_top_width():
    s = space()
    want = cam("top").data.ortho_scale * s.lens / 72.0
    check(f"top's Orthographic Width zooms the top view (distance {s.region_3d.view_distance:.4f}, want {want:.4f})",
          abs(s.region_3d.view_distance - want) < 1e-5)
    C["w"] = cam("top").data.ortho_scale
    s.region_3d.view_distance *= 2.0            # the view zooms out


@step
def s_top_zoomed():
    top = cam("top")
    check(f"zooming the top view out doubles top's Orthographic Width ({top.data.ortho_scale:.4f}, was {C['w']:.4f})",
          abs(top.data.ortho_scale - 2.0 * C["w"]) < 1e-4)
    rv3d = space().region_3d
    rv3d.view_location = rv3d.view_location + Vector((2.0, 0.0, 0.0))     # the view tracks


@step
def s_top_tracked():
    top = cam("top")
    rv3d = space().region_3d
    check(f"tracking the top view moves top over it (top x {top.location.x:.4f}, view x {rv3d.view_location.x:.4f})",
          abs(top.location.x - rv3d.view_location.x) < 1e-4 and abs(top.location.z - C["top_loc"].z) < 1e-4)


run()
