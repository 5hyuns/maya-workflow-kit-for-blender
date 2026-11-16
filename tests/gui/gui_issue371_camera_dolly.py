"""#371 with simulated events: Alt+RMB dolly reacts to a left / right drag in a view that looks through a camera or a
spot light, like in the perspective view (Maya: the same dolly in both; it moves the camera). A drag right (or up)
moves the camera forward, a drag left moves it back, Ctrl+Z puts it back, and an orthographic camera changes its
width instead."""

import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, ev, run, setup, step, view3d, win  # noqa: E402

C = {}


def rv3d():
    return view3d()[0].spaces.active.region_3d


def drag(dx, dy=0):
    """Alt+RMB press, two moves, release (the dolly reads each move)."""
    x, y = C["x"], C["y"]
    ev('RIGHTMOUSE', 'PRESS', x=x, y=y, alt=True)
    ev('MOUSEMOVE', 'NOTHING', x=x + dx // 2, y=y + dy // 2, alt=True)
    ev('MOUSEMOVE', 'NOTHING', x=x + dx, y=y + dy, alt=True)
    ev('RIGHTMOUSE', 'RELEASE', x=x + dx, y=y + dy, alt=True)
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)


def look_through(ob):
    for o in bpy.context.scene.objects:
        o.select_set(o == ob)
    bpy.context.view_layer.objects.active = ob
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.allset.panel_look_through()


def forward(ob):
    return (ob.matrix_world.to_quaternion() @ Vector((0.0, 0.0, -1.0))).normalized()


def moved(ob, key):
    """(along the object's view axis, sideways) since ``C[key]``."""
    d = ob.matrix_world.translation - C[key]
    along = d.dot(forward(ob))
    return along, (d - forward(ob) * along).length


def note(ob, key):
    C[key] = ob.matrix_world.translation.copy()


@step
def s_setup():
    C["x"], C["y"] = setup()
    C["dist"] = rv3d().view_distance
    drag(120)                                   # horizontal only


@step
def s_persp():
    d = rv3d().view_distance
    check(f"perspective view: a drag right dollies in ({C['dist']:.2f} -> {d:.2f})", d < C["dist"])
    sc = bpy.context.scene
    cam = bpy.data.objects.new("cam371", bpy.data.cameras.new("cam371"))
    sc.collection.objects.link(cam)
    cam.location = (0.0, -12.0, 3.0)
    cam.rotation_euler = (1.35, 0.0, 0.0)
    C["cam"] = cam.name
    look_through(cam)


@step
def s_cam_wait():
    cam = bpy.data.objects[C["cam"]]
    check(f"the view looks through the camera ({rv3d().view_perspective})", rv3d().view_perspective == 'CAMERA')
    note(cam, "c0")
    drag(120)                                   # horizontal only


@step
def s_cam_in():
    cam = bpy.data.objects[C["cam"]]
    along, side = moved(cam, "c0")
    check(f"camera view: a drag right moves the camera forward ({along:.3f} along, {side:.4f} sideways)",
          along > 0.1 and side < 1e-3)
    check(f"the view still looks through the camera ({rv3d().view_perspective})",
          rv3d().view_perspective == 'CAMERA')
    note(cam, "c1")
    drag(-120)


@step
def s_cam_out():
    cam = bpy.data.objects[C["cam"]]
    along, side = moved(cam, "c1")
    check(f"camera view: a drag left moves the camera back ({along:.3f} along, {side:.4f} sideways)",
          along < -0.1 and side < 1e-3)
    note(cam, "c2")
    drag(0, 120)                                # vertical only


@step
def s_cam_up():
    cam = bpy.data.objects[C["cam"]]
    along, _side = moved(cam, "c2")
    check(f"camera view: a drag up still moves the camera forward ({along:.3f})", along > 0.1)
    note(cam, "c3")
    ev('Z', 'PRESS', ctrl=True)
    ev('Z', 'RELEASE', ctrl=True)


@step
def s_cam_undo():
    cam = bpy.data.objects[C["cam"]]
    back = (cam.matrix_world.translation - C["c2"]).length
    check(f"Ctrl+Z puts the camera back where it was before the last dolly ({back:.4f} off)", back < 1e-3)
    x, y = C["x"], C["y"]
    ev('RIGHTMOUSE', 'PRESS', x=x, y=y, alt=True)
    ev('MOUSEMOVE', 'NOTHING', x=x + 60, y=y, alt=True)
    ev('MOUSEMOVE', 'NOTHING', x=x + 120, y=y, alt=True)
    ev('ESC', 'PRESS', x=x + 120, y=y, alt=True)
    ev('ESC', 'RELEASE', x=x + 120, y=y, alt=True)
    ev('RIGHTMOUSE', 'RELEASE', x=x + 120, y=y, alt=True)
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)


@step
def s_cam_esc():
    cam = bpy.data.objects[C["cam"]]
    back = (cam.matrix_world.translation - C["c2"]).length
    check(f"Esc during the dolly puts the camera back ({back:.4f} off)", back < 1e-3)
    sc = bpy.context.scene
    light = bpy.data.objects.new("spot371", bpy.data.lights.new("spot371", 'SPOT'))
    sc.collection.objects.link(light)
    light.location = (4.0, -8.0, 5.0)
    light.rotation_euler = (1.0, 0.0, 0.5)
    C["spot"] = light.name
    look_through(light)


@step
def s_spot_wait():
    light = bpy.data.objects[C["spot"]]
    check(f"the view looks through the spot light ({rv3d().view_perspective})", rv3d().view_perspective == 'CAMERA')
    note(light, "s0")
    drag(120)


@step
def s_spot_in():
    light = bpy.data.objects[C["spot"]]
    along, side = moved(light, "s0")
    check(f"Look Through Selected on a spot light: a drag right moves the light forward ({along:.3f} along, "
          f"{side:.4f} sideways)", along > 0.1 and side < 1e-3)
    sc = bpy.context.scene
    data = bpy.data.cameras.new("ortho371")
    data.type = 'ORTHO'
    data.ortho_scale = 10.0
    ortho = bpy.data.objects.new("ortho371", data)
    sc.collection.objects.link(ortho)
    ortho.location = (0.0, -10.0, 0.0)
    ortho.rotation_euler = (1.5708, 0.0, 0.0)
    C["ortho"] = ortho.name
    look_through(ortho)


@step
def s_ortho_wait():
    ortho = bpy.data.objects[C["ortho"]]
    note(ortho, "o0")
    C["w0"] = ortho.data.ortho_scale
    drag(120)


@step
def s_ortho_in():
    ortho = bpy.data.objects[C["ortho"]]
    w = ortho.data.ortho_scale
    off = (ortho.matrix_world.translation - C["o0"]).length
    check(f"orthographic camera: a drag right narrows its width ({C['w0']:.3f} -> {w:.3f})", w < C["w0"] - 0.1)
    check(f"orthographic camera: the camera itself stays ({off:.4f} moved)", off < 1e-3)


run()
