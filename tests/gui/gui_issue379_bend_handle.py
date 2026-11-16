"""Issue #379 in a real UI: Deform > Nonlinear > Bend on a flat plane in the Maya layout. The plane stays flat (the
handle stands upright, no spin); with the handle turned to lie along the plane and Curvature 90, the view (front,
orthographic) shows the handle's straight line from Low Bound to High Bound, the bent line beside it and the short line
towards the bend, in the lead green while the handle is selected and dark blue once nothing is; the plane bends into a
half circle. Screenshots ``gui_issue379_<name>.png`` with ``--shots``."""

import math
import os
import sys
from importlib import import_module

import bpy
import numpy as np
from mathutils import Euler, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, load_maya_layout, run, screenshot, setup, step, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
# the lines are 1 px wide and smoothed, so a line between two pixel rows draws both half-mixed with the background:
# a pixel counts by its hue (lead green: green well over red and blue; dark blue: blue over red and green)
LEAD, DORMANT = "green", "blue"
C = {}
GUI_TIMEOUT = 240


def mod(name):
    return import_module(MODULE + name)


def shot(name):
    path = os.path.join(SHOTS or bpy.app.tempdir, f"gui_issue379_{name}.png")
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
    return None if p is None else (int(round(p.x + region.x)), int(round(p.y + region.y)))


def near(px, world, colour, half=4):
    """Pixels of ``colour`` within ``half`` px of where ``world`` is drawn."""
    p = to_window(world)
    if p is None:
        return 0
    x, y = p
    patch = px[y - half:y + half + 1, x - half:x + half + 1]
    r, g, b = patch[..., 0], patch[..., 1], patch[..., 2]
    if colour == LEAD:
        hit = (g - r > 0.25) & (g - b > 0.1)
    else:
        hit = (b - r > 0.05) & (b - g > 0.05) & (r < 0.35)
    return int(hit.sum())


def plane():
    return bpy.data.objects[C["plane"]]


def handle():
    return bpy.data.objects[C["handle"]]


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_scene():
    k = mod(".operators.units").maya_unit()
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=32, y_subdivisions=2, size=8.0 * k)
    ob = bpy.context.active_object
    C["plane"], C["k"] = ob.name, k
    C["rest"] = [tuple(ob.matrix_world @ v.co) for v in ob.data.vertices]
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        assert bpy.ops.allset.deformer(kind='BEND') == {'FINISHED'}
    C["handle"] = bpy.context.view_layer.objects.active.name
    rv3d = area.spaces.active.region_3d
    rv3d.view_perspective = 'ORTHO'
    rv3d.view_rotation = (0.7071068, 0.7071068, 0.0, 0.0)      # front: X right, Z up
    rv3d.view_location = (0.0, 0.0, -1.0 * k)
    rv3d.view_distance = 14.0 * k
    for ar in win().screen.areas:
        ar.tag_redraw()


@step
def s_flat_stays_flat():
    h = handle()
    check(f"the handle is selected and stands upright, scale half the plane's 8 ({tuple(h.scale)})",
          bpy.context.active_object == h and all(abs(s - 4.0 * C["k"]) < 1e-6 for s in h.scale))
    bend = mod(".operators.bend_deformer")
    bend.set_(plane().modifiers["bend1"], "Curvature", math.radians(90.0))
    bpy.context.view_layer.update()


@step
def s_flat_check():
    dg = bpy.context.evaluated_depsgraph_get()
    me = plane().evaluated_get(dg).to_mesh()
    moved = max((plane().matrix_world @ v.co - Vector(r)).length for v, r in zip(me.vertices, C["rest"]))
    plane().evaluated_get(dg).to_mesh_clear()
    check(f"Curvature 90 with the handle upright leaves the flat plane as it is ({moved:.2e})", moved < 1e-6)
    handle().rotation_euler = Euler((0.0, math.radians(90.0), 0.0))     # the handle's length along the plane's X
    for ar in win().screen.areas:
        ar.tag_redraw()


@step
def s_wait():
    pass


@step
def s_bent_selected():
    px = shot("bent_selected")
    m = handle().matrix_world
    c = math.pi / 2
    bend = mod(".operators.bend_deformer")
    ends = [m @ Vector((0, 0, -1)), m @ Vector((0, 0, 1))]
    arc_mid = [m @ bend.to_kit(*bend.bent(0.0, y, c, -1.0, 1.0)) for y in (-0.7, 0.7)]
    tick = m @ Vector((0.2 * c * 0.6, 0, 0))
    n_line = [near(px, p.lerp(m.translation, 0.15), LEAD) for p in ends]
    n_arc = [near(px, p, LEAD) for p in arc_mid]
    n_tick = near(px, tick, LEAD)
    check(f"the straight line draws green near both ends ({n_line})", min(n_line) > 0)
    check(f"the bent line draws green ({n_arc})", min(n_arc) > 0)
    check(f"the line towards the bend draws green ({n_tick})", n_tick > 0)
    dg = bpy.context.evaluated_depsgraph_get()
    me = plane().evaluated_get(dg).to_mesh()
    zs = [(plane().matrix_world @ v.co).z for v in me.vertices]
    xs = [(plane().matrix_world @ v.co).x for v in me.vertices]
    plane().evaluated_get(dg).to_mesh_clear()
    k = C["k"]
    r = 8.0 * k / math.pi
    check(f"the plane bends into a half circle (depth {-min(zs) / k:.3f}, width {(max(xs) - min(xs)) / k:.3f})",
          abs(-min(zs) - r) < 1e-3 * k + 1e-6 and abs(max(xs) - min(xs) - 2 * r) < 1e-3 * k + 1e-6)
    for ob in bpy.context.scene.objects:            # nothing selected (no selection wire over the bent line)
        ob.select_set(False)
    bpy.context.view_layer.objects.active = None
    for ar in win().screen.areas:
        ar.tag_redraw()


@step
def s_wait2():
    pass


@step
def s_dormant():
    px = shot("bent_not_selected")
    m = handle().matrix_world
    c = math.pi / 2
    bend = mod(".operators.bend_deformer")
    n = [near(px, m @ bend.to_kit(*bend.bent(0.0, y, c, -1.0, 1.0)), DORMANT) for y in (-0.7, 0.7)]
    g = [near(px, m @ bend.to_kit(*bend.bent(0.0, y, c, -1.0, 1.0)), LEAD) for y in (-0.7, 0.7)]
    check(f"not selected: dark blue ({n}), no green ({g})", min(n) > 0 and max(g) == 0)


run()
