"""Editable motion trail in the Maya layout: a left drag on a key marker of a motion path moves the object's location
key at that frame (the trail follows), the picked key is drawn yellow, one undo takes the drag back, Esc cancels a
drag, and a click off the trail still selects normally."""

import math
import os
import sys
from importlib import import_module

import bpy
import numpy as np
from mathutils import Euler, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, load_maya_layout, run, screenshot, setup, step, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def mod(name):
    return import_module(MODULE + name)


def to_window(world):
    from bpy_extras.view3d_utils import location_3d_to_region_2d
    area, region = view3d()
    p = location_3d_to_region_2d(region, area.spaces.active.region_3d, world)
    return None if p is None else (int(round(p.x + region.x)), int(round(p.y + region.y)))


def shot(name):
    path = os.path.join(SHOTS or bpy.app.tempdir, f"gui_motion_trail_keys_{name}.png")
    screenshot(path)
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    px = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(px)
    bpy.data.images.remove(img)
    return px.reshape(h, w, 4)[..., :3]


def key_value(index, frame):
    for fc in mod(".compat").id_fcurves(bpy.data.objects["Ball"]):
        if fc.data_path == "location" and fc.array_index == index:
            for kp in fc.keyframe_points:
                if abs(kp.co.x - frame) < 1e-4:
                    return kp.co.y
    return None


def path_point(frame):
    mp = bpy.data.objects["Ball"].motion_path
    return Vector(mp.points[frame - mp.frame_start].co)


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


def press_at(p, value):
    ev('LEFTMOUSE', value, x=p[0], y=p[1])


def move(p):
    ev('MOUSEMOVE', 'NOTHING', x=p[0], y=p[1])


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_scene():
    bpy.ops.allset.keymap_activate()
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    scene = bpy.context.scene
    k = mod(".operators.units").maya_unit()
    C["k"] = k
    scene.frame_start, scene.frame_end = 1, 20
    ball = bpy.data.objects.new("Ball", None)
    ball.empty_display_size = 0.3 * k
    scene.collection.objects.link(ball)
    for f, p in ((1, (0, 0, 0)), (10, (5, 0, 0)), (20, (10, 0, 5))):
        ball.location = Vector(p) * k
        ball.keyframe_insert("location", frame=f)
    box = bpy.data.objects.new("Box", None)
    box.empty_display_type = 'PLAIN_AXES'
    box.empty_display_size = 0.5 * k
    box.location = Vector((2, 0, 4)) * k
    scene.collection.objects.link(box)
    scene.frame_set(1)
    for ob in scene.objects:
        ob.select_set(ob == ball)
    bpy.context.view_layer.objects.active = ball
    with bpy.context.temp_override(window=win()):
        bpy.ops.allset.motion_trail(action='CREATE')
    ball.select_set(False)
    area, region = view3d()
    space = area.spaces.active
    space.overlay.show_motion_paths = True
    rv3d = space.region_3d
    rv3d.view_perspective = 'ORTHO'
    rv3d.view_rotation = Euler((math.radians(90), 0, 0)).to_quaternion()     # front: X right, Z up
    rv3d.view_location = Vector((5, 0, 2)) * k
    rv3d.view_distance = 18 * k
    redraw()


@step
def s_ready():
    check(f"Ball has a motion path ({bpy.data.objects['Ball'].motion_path is not None})",
          bpy.data.objects["Ball"].motion_path is not None)
    with bpy.context.temp_override(window=win()):
        bpy.ops.ed.undo_push(message="trail ready")
    C["p"] = to_window(path_point(10))
    C["x0"], C["z0"] = key_value(0, 10), key_value(2, 10)
    move(C["p"])


@step
def s_press():
    press_at(C["p"], 'PRESS')


for i in range(1, 5):
    step(lambda i=i: move((C["p"][0] + 15 * i, C["p"][1])))


@step
def s_release():
    press_at((C["p"][0] + 60, C["p"][1]), 'RELEASE')


@step
def s_dragged():
    x, z = key_value(0, 10), key_value(2, 10)
    C["x1"] = x
    check(f"the drag moved the key's X ({C['x0']:.3f} -> {x:.3f})", x is not None and x > C["x0"] + 0.5 * C["k"])
    check(f"Z stays ({C['z0']:.4f} -> {z:.4f})", z is not None and abs(z - C["z0"]) < 1e-4 * C["k"])
    check(f"the other keys stay ({key_value(0, 1)}, {key_value(0, 20)})",
          abs(key_value(0, 1)) < 1e-6 and abs(key_value(0, 20) - 10 * C["k"]) < 1e-5)
    pt = path_point(10)
    check(f"the trail follows the key ({pt.x:.3f} ~ {x:.3f})", abs(pt.x - x) < 1e-3 * C["k"])
    picked = mod(".operators.motion_trail_edit").picked()
    check(f"the key is picked ({picked})", picked == [("Ball", "", 10)])
    C["p2"] = to_window(pt)
    redraw()


@step
def s_yellow():
    px = shot("picked")
    x, y = C["p2"]
    patch = px[y - 2:y + 3, x - 2:x + 3]
    yellow = (patch[..., 0] > 0.8) & (patch[..., 1] > 0.8) & (patch[..., 2] < 0.3)
    check(f"the picked key is drawn yellow ({int(yellow.sum())}/25)", yellow.sum() >= 9)
    ev('LEFT_CTRL', 'PRESS', ctrl=True)
    ev('Z', 'PRESS', ctrl=True)
    ev('Z', 'RELEASE', ctrl=True)
    ev('LEFT_CTRL', 'RELEASE')


step(lambda: None)


@step
def s_undone():
    x = key_value(0, 10)
    check(f"one undo takes the drag back ({x:.4f} ~ {C['x0']:.4f})", abs(x - C["x0"]) < 1e-5 * C["k"])
    C["p"] = to_window(path_point(10))
    move(C["p"])


@step
def s_press2():
    press_at(C["p"], 'PRESS')


step(lambda: move((C["p"][0], C["p"][1] + 20)))
step(lambda: move((C["p"][0], C["p"][1] + 40)))


@step
def s_esc():
    z = key_value(2, 10)
    check(f"while dragging up the key's Z rises ({C['z0']:.4f} -> {z:.4f})", z > C["z0"] + 0.5 * C["k"])
    ev('ESC', 'PRESS')
    ev('ESC', 'RELEASE')


@step
def s_esc_release():
    press_at((C["p"][0], C["p"][1] + 40), 'RELEASE')


@step
def s_cancelled():
    z = key_value(2, 10)
    check(f"Esc puts the key back ({z:.4f} ~ {C['z0']:.4f})", abs(z - C["z0"]) < 1e-5 * C["k"])
    box = bpy.data.objects["Box"]
    C["pb"] = to_window(box.matrix_world.translation)
    move(C["pb"])


@step
def s_box_press():
    press_at(C["pb"], 'PRESS')


@step
def s_box_release():
    press_at(C["pb"], 'RELEASE')


@step
def s_box_selected():
    box = bpy.data.objects["Box"]
    check(f"a click off the trail selects normally ({box.select_get()})", box.select_get())
    picked = mod(".operators.motion_trail_edit").picked()
    check(f"and drops the picked trail keys ({picked})", picked == [])



# a mesh object's own surface in front of its key marker wins (like Maya): the click selects the mesh
@step
def s_mesh():
    scene = bpy.context.scene
    k = C["k"]
    me = bpy.data.meshes.new("CubeMesh")
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0 * k)
    bm.to_mesh(me)
    bm.free()
    cube = bpy.data.objects.new("Cube", me)
    scene.collection.objects.link(cube)
    for f, p in ((1, (0, 0, 6)), (10, (5, 0, 6)), (20, (10, 0, 6))):
        cube.location = Vector(p) * k
        cube.keyframe_insert("location", frame=f)
    for ob in scene.objects:
        ob.select_set(ob == cube)
    bpy.context.view_layer.objects.active = cube
    with bpy.context.temp_override(window=win()):
        bpy.ops.allset.motion_trail(action='CREATE')
    scene.frame_set(10)          # the cube sits on its key 10 marker
    cube.select_set(False)
    mod(".operators.motion_trail_edit").clear()
    C["pc"] = to_window(Vector(cube.motion_path.points[10 - cube.motion_path.frame_start].co))
    redraw()


step(lambda: move(C["pc"]))
step(lambda: press_at(C["pc"], 'PRESS'))
step(lambda: press_at(C["pc"], 'RELEASE'))


@step
def s_mesh_won():
    cube = bpy.data.objects["Cube"]
    picked = mod(".operators.motion_trail_edit").picked()
    check(f"the mesh in front of its key marker wins the click ({picked}, selected {cube.select_get()})",
          picked == [] and cube.select_get())
    bpy.context.scene.frame_set(1)
    cube.select_set(False)
    redraw()


step(lambda: move(C["pc"]))
step(lambda: press_at(C["pc"], 'PRESS'))
step(lambda: press_at(C["pc"], 'RELEASE'))


@step
def s_mesh_away():
    picked = mod(".operators.motion_trail_edit").picked()
    check(f"with the mesh elsewhere the same marker is picked ({picked})", picked == [("Cube", "", 10)])


run()
