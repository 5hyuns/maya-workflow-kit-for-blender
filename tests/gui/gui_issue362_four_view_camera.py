"""Issue #362: a panel that looks through a camera keeps that camera across the Space tap, like a Maya panel.

Single perspective view -> look through camera1 (Panels > Perspective > camera1) -> Space over it: the four view
comes back with camera1 in the persp panel; Space over that panel keeps it alone with camera1, Space again brings
the four back with camera1. In the four view the front panel looks through the scene camera (View > Cameras >
Active Camera, Numpad 0): Space over it keeps it alone with the camera, Space again keeps it in the four view. The
single top view looking through the scene camera comes back in the top place of the four view. The orthographic
panels and per-panel shading stay as they were. Real Space key events (the hotbox tap). Shots with ``--shots``."""

import math
import os
import sys
from importlib import import_module

import bpy
from mathutils import Euler

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sim  # noqa: E402
from sim import MODULE, check, load_maya_layout, run, screenshot, setup, step, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}
ZOOM = 12.0                   # a camera zoom the persp panel keeps


def fv():
    return import_module(f"{MODULE}.ui.four_view")


def ortho_key(area):
    return import_module(f"{MODULE}.operators.view").ortho_key(area.spaces.active.region_3d)


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


def shot(name):
    screenshot(os.path.join(SHOTS or bpy.app.tempdir, f"gui_issue362_{name}.png"))


def count():
    return len(win().screen.areas)


def camera_of(area):
    """Name of the camera ``area`` looks through, None when it shows no camera view."""
    space = area.spaces.active
    rv3d = getattr(space, "region_3d", None)
    if area.type != 'VIEW_3D' or rv3d is None or rv3d.view_perspective != 'CAMERA':
        return None
    ob = space.camera if space.use_local_camera else bpy.context.scene.camera
    return ob.name if ob is not None else None


def views():
    """{role: camera name / ortho key / 'PERSP'} of the four view."""
    out = {}
    for role, a in fv().roles(win().screen).items():
        out[role] = camera_of(a) or ortho_key(a) or a.spaces.active.region_3d.view_perspective
    return out


def override(area):
    region = next(r for r in area.regions if r.type == 'WINDOW')
    return bpy.context.temp_override(window=win(), screen=win().screen, area=area, region=region,
                                     space_data=area.spaces.active, region_data=region.data)


def space_over(get):
    """Space tap with the mouse over the area ``get()`` returns: the move in one tick, the key in the next (event
    simulation loses a key sent in the tick of a layout change), then two redraw ticks (the top row splits one tick
    later)."""
    def move():
        area = get()
        reg = next(r for r in area.regions if r.type == 'WINDOW')
        C["xy"] = (reg.x + reg.width // 2, reg.y + reg.height // 2)
        sim.ev('MOUSEMOVE', 'NOTHING', x=C["xy"][0], y=C["xy"][1])

    def key():
        x, y = C["xy"]
        sim.ev('MOUSEMOVE', 'NOTHING', x=x + 1, y=y)
        sim.ev('SPACE', 'PRESS', x=x, y=y)
        sim.ev('SPACE', 'RELEASE', x=x, y=y)
    step(move)
    step(key)
    step(redraw)
    step(redraw)


def role(name):
    return lambda: fv().roles(win().screen)[name]


def only():
    """The one panel left (by the recorded rect)."""
    return fv().single(win().screen)


def camera(name, location, rotation):
    ob = bpy.data.objects.new(name, bpy.data.cameras.new(name))
    bpy.context.scene.collection.objects.link(ob)
    ob.location = location
    ob.rotation_euler = Euler([math.radians(v) for v in rotation])
    return ob


@step
def s_setup():
    setup()
    load_maya_layout()


for _i in range(5):
    step(redraw)


@step
def s_start():
    C["n0"] = count()
    C["main"] = view3d()[0]
    check("Maya layout: one viewport panel", len(fv().panes(win().screen)) == 1)
    camera("camera1", (14.0, -14.0, 10.0), (63.0, 0.0, 45.0))
    scene_cam = camera("camera2", (-14.0, -14.0, 6.0), (78.0, 0.0, -45.0))
    bpy.context.scene.camera = scene_cam
    with override(C["main"]):
        got = bpy.ops.allset.panel_look_through(camera="camera1")      # Panels > Perspective > camera1
    check(f"Panels > Perspective > camera1 -> {got}", got == {'FINISHED'})
    redraw()


step(redraw)


@step
def s_looking():
    check(f"the single view looks through camera1 ({camera_of(C['main'])})", camera_of(C["main"]) == "camera1")


space_over(lambda: C["main"])


@step
def s_four_with_camera():
    screen = win().screen
    got = views()
    check(f"Space over the camera view -> four view ({count()} areas)", fv().is_four(screen)
          and count() == C["n0"] + 3)
    check(f"the persp panel still looks through camera1, the others are top / front / side {got}",
          got.get("persp") == "camera1" and str(got.get("top")).startswith("TOP")
          and str(got.get("front")).startswith("FRONT") and str(got.get("side")).startswith("SIDE"))
    shot("01_four_camera1")
    persp = fv().roles(screen).get("persp")
    if persp is not None and persp.spaces.active.region_3d is not None:
        persp.spaces.active.region_3d.view_camera_zoom = ZOOM
    top = fv().roles(screen).get("top")
    if top is not None:
        top.spaces.active.shading.type = 'WIREFRAME'
    redraw()


space_over(role("persp"))


@step
def s_single_camera():
    one = only()
    check(f"Space over the camera panel: it stays alone with camera1 ({count()} areas, "
          f"{one and camera_of(one)})", count() == C["n0"] and one is not None and camera_of(one) == "camera1")
    shot("02_single_camera1")


space_over(only)


@step
def s_four_again():
    screen = win().screen
    got = views()
    check(f"Space again: the four view keeps camera1 in the persp panel {got}",
          fv().is_four(screen) and got.get("persp") == "camera1")
    persp = fv().roles(screen).get("persp")
    zoom = persp.spaces.active.region_3d.view_camera_zoom if persp is not None else None
    check(f"the camera panel keeps its camera zoom ({zoom})", zoom is not None and abs(zoom - ZOOM) < 1e-3)
    front = fv().roles(screen).get("front")
    space = front.spaces.active
    check(f"the front panel has no camera of its own ({space.use_local_camera}, {space.lock_camera})",
          not space.use_local_camera and not space.lock_camera)
    with override(front):
        bpy.ops.view3d.view_camera()                       # View > Cameras > Active Camera (Numpad 0)
    redraw()


step(redraw)
step(redraw)


@step
def s_front_camera():
    front = fv().roles(win().screen).get("front")
    check(f"the front panel looks through the scene camera ({front and camera_of(front)})",
          front is not None and camera_of(front) == "camera2")


space_over(role("front"))


@step
def s_front_alone():
    one = only()
    check(f"Space over the front camera panel: it stays alone with the scene camera ({count()} areas, "
          f"{one and camera_of(one)})", count() == C["n0"] and one is not None and camera_of(one) == "camera2")


space_over(only)


@step
def s_four_two_cameras():
    screen = win().screen
    got = views()
    check(f"Space again: front keeps the scene camera, persp keeps camera1 {got}", fv().is_four(screen)
          and got.get("front") == "camera2" and got.get("persp") == "camera1"
          and str(got.get("top")).startswith("TOP") and str(got.get("side")).startswith("SIDE"))
    top = fv().roles(screen).get("top")
    check(f"the top panel keeps its own shading ({top and top.spaces.active.shading.type})",
          top is not None and top.spaces.active.shading.type == 'WIREFRAME')
    shot("03_four_two_cameras")


space_over(role("top"))


@step
def s_top_alone():
    one = only()
    check(f"Space over top: the top view alone, still orthographic ({one and ortho_key(one)})",
          one is not None and str(ortho_key(one)).startswith("TOP"))
    with override(one):
        bpy.ops.view3d.view_camera()                       # the single top view looks through the scene camera
    redraw()


step(redraw)
step(redraw)


@step
def s_top_camera():
    one = only()
    check(f"the single top view looks through the scene camera ({one and camera_of(one)})",
          one is not None and camera_of(one) == "camera2")


space_over(only)


@step
def s_four_top_camera():
    screen = win().screen
    got = views()
    check(f"Space over it: the four view with the scene camera in the top place, the others kept {got}",
          fv().is_four(screen) and got.get("top") == "camera2" and got.get("front") == "camera2"
          and got.get("persp") == "camera1" and str(got.get("side")).startswith("SIDE"))
    # the persp panel is now split off the top view: its camera zoom comes from its own record
    persp = fv().roles(screen).get("persp")
    zoom = persp.spaces.active.region_3d.view_camera_zoom if persp is not None else None
    check(f"the camera1 panel keeps its camera zoom ({zoom})", zoom is not None and abs(zoom - ZOOM) < 1e-3)
    shot("04_four_top_camera")


run()
