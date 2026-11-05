"""#299: Camera and Aim in the Maya layout: Blender's relationship lines stay off, the kit draws a dark blue line from
the camera to its aim; it follows the aim when the aim moves, turns the lead green with the rig's group selected and
goes away with the group's Display Connector off."""

import os
import sys
from importlib import import_module

import bpy
import numpy as np
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, load_maya_layout, run, screenshot, setup, step, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def mod(name):
    return import_module(MODULE + name)


def shot(name):
    path = os.path.join(SHOTS or bpy.app.tempdir, f"gui_issue299_aim_line_{name}.png")
    screenshot(path)
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    px = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(px)
    bpy.data.images.remove(img)
    return px.reshape(h, w, 4)[..., :3]


def to_window(world):
    from bpy_extras.view3d_utils import location_3d_to_region_2d
    area, region = view3d()
    p = location_3d_to_region_2d(region, area.spaces.active.region_3d, world)
    return None if p is None else Vector((p.x + region.x, p.y + region.y))


def bluish(patch):
    # a 1 px dark blue line blends with the grey background: blue clearly above red and green
    return (patch[..., 2] > patch[..., 0] + 0.05) & (patch[..., 2] > patch[..., 1] + 0.05)


def on_line(px, a, b, colour, half=3):
    """How many of 9 points between 20 % and 80 % along a-b have ``colour`` (or ``bluish``) within ``half`` px."""
    pa, pb = to_window(a), to_window(b)
    hits = 0
    for i in range(9):
        p = pa.lerp(pb, 0.2 + 0.6 * i / 8)
        x, y = int(round(p.x)), int(round(p.y))
        patch = px[y - half:y + half + 1, x - half:x + half + 1]
        hit = bluish(patch) if colour is bluish else np.abs(patch - colour).max(axis=-1) < 0.06
        hits += bool(hit.any())
    return hits


def ends():
    cam, aim = bpy.data.objects["camera1"], bpy.data.objects["camera1_aim"]
    return cam.matrix_world.translation.copy(), aim.matrix_world.translation.copy()


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_scene():
    bpy.ops.allset.keymap_activate()
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    assert bpy.ops.allset.create(kind='CAMERA_AIM') == {'FINISHED'}
    k = mod(".operators.units").maya_unit()
    cam, aim = bpy.data.objects["camera1"], bpy.data.objects["camera1_aim"]
    cam.location = Vector((-6.0, 0.0, 2.0)) * k
    aim.location = Vector((6.0, 4.0, 0.0)) * k
    for ob in bpy.context.scene.objects:
        ob.select_set(False)
    area, region = view3d()
    rv3d = area.spaces.active.region_3d
    rv3d.view_perspective = 'PERSP'
    rv3d.view_location = (0.0, 2.0 * k, 1.0 * k)
    rv3d.view_distance = 30.0 * k
    C["k"] = k
    redraw()


@step
def s_dormant():
    space = view3d()[0].spaces.active
    check(f"Blender's relationship lines are off in the Maya layout view ({space.overlay.show_relationship_lines})",
          not space.overlay.show_relationship_lines)
    px = shot("dormant")
    n = on_line(px, *ends(), bluish)
    check(f"a dark blue line runs from the camera to the aim ({n}/9)", n >= 7)
    bpy.data.objects["camera1_aim"].location = Vector((4.0, -6.0, 0.0)) * C["k"]
    redraw()


@step
def s_moved():
    px = shot("moved")
    n = on_line(px, *ends(), bluish)
    check(f"the line follows the moved aim ({n}/9)", n >= 7)
    group = bpy.data.objects["camera1_group"]
    group.select_set(True)
    bpy.context.view_layer.objects.active = group
    redraw()


@step
def s_group_selected():
    px = shot("group")
    n = on_line(px, *ends(), np.array(mod(".ui.camera_aim_lines").LEAD))
    check(f"the group selected turns the line green ({n}/9)", n >= 7)
    group = bpy.data.objects["camera1_group"]
    group.select_set(False)
    group[mod(".ui.camera_aim_lines").CONNECTOR] = False
    redraw()


@step
def s_connector_off():
    px = shot("off")
    n = on_line(px, *ends(), bluish)
    check(f"Display Connector off: no line ({n}/9)", n == 0)


run()
