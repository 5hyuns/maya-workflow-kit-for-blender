"""Issue #374: F in a view that looks through a camera fills what the view shows, like Maya: with the Resolution Gate
shown (Overscan 1.3) the selection fills 0.95 of the view on its tighter axis and reaches into the room around the
gate; with the gate off it fills 0.95 of the view as well. The whole selection stays in the view and is centred."""

import os
import sys
from importlib import import_module

import bpy
from bpy_extras.object_utils import world_to_camera_view
from bpy_extras.view3d_utils import location_3d_to_region_2d
from mathutils import Euler, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, setup, step, tap, view3d, win, load_maya_layout  # noqa: E402

C = {}


def ov(fn, **kw):
    area, _region = view3d()
    region = import_module(MODULE + ".ui.panel_menus").main_region(area)
    with bpy.context.temp_override(window=win(), area=area, region=region):
        return fn(**kw)


def hover():
    _a, r = view3d()
    ev('MOUSEMOVE', 'NOTHING', x=r.x + r.width // 2, y=r.y + r.height // 2)


def view_cam():
    a, _r = view3d()
    sp = a.spaces.active
    return sp.camera if sp.use_local_camera and sp.camera is not None else bpy.context.scene.camera


def filled(label, gate):
    a, r = view3d()
    rv = r.data
    rect = import_module(MODULE + ".operators.view").visible_bounds(a, r)
    cube = bpy.data.objects[C["cube"]]
    pts = [cube.matrix_world @ Vector(c) for c in cube.bound_box]
    xy = [location_3d_to_region_2d(r, rv, p) for p in pts]
    check(f"{label}: the view still looks through the camera ({rv.view_perspective})", rv.view_perspective == 'CAMERA')
    if any(p is None for p in xy):
        check(f"{label}: the cube is in front of the camera", False)
        return
    x0, x1 = min(p.x for p in xy), max(p.x for p in xy)
    y0, y1 = min(p.y for p in xy), max(p.y for p in xy)
    w, h = rect[2] - rect[0], rect[3] - rect[1]
    fill = max((x1 - x0) / w, (y1 - y0) / h)
    check(f"{label}: the cube fills 0.95 of the view on its tighter axis ({fill:.3f})", abs(fill - 0.95) < 0.01)
    check(f"{label}: the whole cube is in the view ({x0:.0f} {y0:.0f} {x1:.0f} {y1:.0f} in {rect})",
          x0 >= rect[0] - 1 and y0 >= rect[1] - 1 and x1 <= rect[2] + 1 and y1 <= rect[3] + 1)
    cx, cy = (x0 + x1) / 2 - (rect[0] + rect[2]) / 2, (y0 + y1) / 2 - (rect[1] + rect[3]) / 2
    check(f"{label}: the cube is centred ({cx:.1f}, {cy:.1f} px off)", abs(cx) < 2 and abs(cy) < 2)
    cam = view_cam()
    if gate:
        uv = [world_to_camera_view(bpy.context.scene, cam, p) for p in pts]
        span = max(max(q.x for q in uv) - min(q.x for q in uv), max(q.y for q in uv) - min(q.y for q in uv))
        check(f"{label}: the cube reaches past the gate into the room around it ({span:.2f} of the gate)", span > 1.05)


@step
def prepare():
    setup()
    load_maya_layout()


@step
def scene():
    with bpy.context.temp_override(window=win()):
        for ob in list(bpy.context.scene.objects):
            if ob.type == 'MESH':
                bpy.data.objects.remove(ob)
    mesh = bpy.data.meshes.new("cube374")
    mesh.from_pydata([(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)], [],
                     [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)])
    cube = bpy.data.objects.new("cube374", mesh)
    bpy.context.scene.collection.objects.link(cube)
    C["cube"] = cube.name
    _a, r = view3d()
    r.data.view_perspective = 'PERSP'
    r.data.view_rotation = Euler((1.5708, 0.0, 0.0)).to_quaternion()     # front view, straight at a cube face
    r.data.view_location = (0.0, 0.0, 0.0)
    r.data.view_distance = 30.0
    ov(bpy.ops.allset.panel_set, key='RES_GATE')         # the panel toolbar's Resolution Gate button
    for ob in bpy.context.scene.objects:
        ob.select_set(ob == cube)
    bpy.context.view_layer.objects.active = cube
    hover()


@step
def settle():
    cam = view_cam()
    check("the Resolution Gate button looks through the panel's camera with Overscan 1.3",
          cam is not None and abs(getattr(cam.data, "allset_overscan", 0.0) - 1.3) < 1e-6)


@step
def settle2():
    hover()


@step
def gate_f():
    tap('F')


@step
def gate_check():
    filled("Resolution Gate shown", True)
    ov(bpy.ops.allset.panel_set, key='RES_GATE')         # gate off: Overscan 1.0
    hover()


@step
def nogate_settle():
    pass


@step
def nogate_f():
    hover()
    tap('F')


@step
def nogate_check():
    filled("no gate", False)


run()
