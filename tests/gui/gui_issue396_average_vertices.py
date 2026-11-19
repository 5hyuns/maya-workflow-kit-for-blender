"""#396 in a real UI: on a subdivided cube with every vertex selected, Shift+RMB > Average Vertices (the vertex marking
menu's NE item) rounds the cube at once: the vertices move, no operator is left waiting for a mouse drag, and the
In-View Editor shows polyAverageVertex1 with its Iterations. Screenshots with ALLSET_GUI_SHOTS (or --shots)."""

import math
import os
import sys
from importlib import import_module

import bmesh
import bpy
import numpy as np
from bpy_extras import view3d_utils

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, screenshot, setup, step, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}
SECTORS = {"N": (0, 1), "NE": (1, 1), "E": (1, 0), "SE": (1, -1), "S": (0, -1), "SW": (-1, -1), "W": (-1, 0),
           "NW": (-1, 1)}


def shot(name):
    if SHOTS:
        screenshot(os.path.join(SHOTS, name))


def mod(name):
    return import_module(MODULE + name)


def draw():
    return mod(".marking.draw")


def session():
    return draw().ACTIVE.get("session")


def co():
    ob = bpy.context.edit_object
    return np.array([v.co[:] for v in bmesh.from_edit_mesh(ob.data).verts])


def sector_point(s, key):
    """A window point past the ring in the direction of radial item ``key``, on no other item."""
    eng = mod(".marking.engine")
    lay, (cx, cy) = s.stack[-1]
    ox, oy = draw().ACTIVE["origin"]
    p = lay.params
    target = lay.radial[key]
    others = [it for it in lay.items if it is not target]

    def ok(dx, dy):
        return (math.hypot(dx, dy) >= p.radius + 2 and eng.direction(dx, dy, p.dead) == key
                and not any(eng._inside(it.rect, dx, dy) or (it.opt_rect and eng._inside(it.opt_rect, dx, dy))
                            for it in others))
    x0, y0, x1, y1 = target.rect
    cands = [(x, y) for x in range(int(x0) + 3, int(x1) - 2, 3) for y in range(int(y0) + 3, int(y1) - 2, 3)]
    sx, sy = SECTORS[key]
    n = math.hypot(sx, sy)
    cands += [(sx / n * d, sy / n * d) for d in range(int(p.radius) + 10, 300, 5)]
    for dx, dy in cands:
        if ok(dx, dy):
            return ox + round(cx + dx), oy + round(cy + dy)
    return None


@step
def s_setup():
    setup()
    for ob in list(bpy.data.objects):
        if ob.name != "Cube":
            bpy.data.objects.remove(ob)
    ob = bpy.data.objects["Cube"]
    ob.location = (0, 0, 0)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='VERT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.subdivide(number_cuts=7)
        bpy.ops.mesh.select_all(action='SELECT')
    p = view3d_utils.location_3d_to_region_2d(region, area.spaces.active.region_3d, ob.matrix_world.translation)
    C["pt"] = (region.x + round(p.x), region.y + round(p.y))


@step
def s_press():
    C["before"] = co()
    shot("gui_issue396_before.png")
    ev('MOUSEMOVE', 'NOTHING', x=C["pt"][0], y=C["pt"][1])
    ev('RIGHTMOUSE', 'PRESS', x=C["pt"][0], y=C["pt"][1], shift=True)


@step
def s_ne():
    s = session()
    ok = s is not None and s.layout.radial.get("NE") is not None
    check(f"Shift+RMB on vertices opens the vertex marking menu ({ok and s.layout.radial['NE'].label})",
          ok and s.layout.radial["NE"].label == "Average Vertices")
    at = sector_point(s, "NE") if ok else None
    C["at"] = at or C["pt"]
    ev('MOUSEMOVE', 'NOTHING', x=C["at"][0], y=C["at"][1], shift=True)


@step
def s_release():
    ev('RIGHTMOUSE', 'RELEASE', x=C["at"][0], y=C["at"][1], shift=True)


step(lambda: None)


@step
def s_result():
    after = co()
    moved = float(np.abs(after - C["before"]).max())
    check(f"Average Vertices moved the vertices at once (max {moved:.4f})", moved > 0.05)
    waiting = [op.bl_idname for op in win().modal_operators]
    check(f"no operator waits for a mouse drag ({waiting})", not any("vertices_smooth" in w.lower() for w in waiting))
    rec = mod(".operators.extrude").RECORDS.get(bpy.context.edit_object.name)
    check(f"the polyAverageVertex node is the last one ({rec and rec.name}, {rec and rec.params})",
          rec is not None and rec.name == "polyAverageVertex1" and rec.params.get("iterations") == 10)
    shot("gui_issue396_after.png")


run()
