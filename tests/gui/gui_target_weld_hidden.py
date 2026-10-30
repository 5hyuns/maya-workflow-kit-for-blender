"""Target Weld in shaded mode skips hidden components (#233): drag the front corner of the cube onto the hidden back
corner (inside the cube's outline on screen) -> nothing welds; with X-ray on the same drag welds onto it."""

import os
import sys
from importlib import import_module

import bmesh
import bpy
from bpy_extras import view3d_utils

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, setup, step, view3d, win  # noqa: E402

C = {}


def cube():
    return bpy.data.objects["Cube"]


def bm():
    b = bmesh.from_edit_mesh(cube().data)
    b.verts.ensure_lookup_table()
    return b


def to_window(co):
    area, region = view3d()
    p = view3d_utils.location_3d_to_region_2d(region, area.spaces.active.region_3d, cube().matrix_world @ co)
    return region.x + round(p.x), region.y + round(p.y)


def depth(co):
    area, _region = view3d()
    return -(area.spaces.active.region_3d.view_matrix @ (cube().matrix_world @ co)).z


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


def drag_steps(tag):
    """press on the front corner, move to the back corner, release (separate ticks)."""
    def press():
        b = bm()
        for v in b.verts:
            v.select = False
        b.select_flush(False)
        bmesh.update_edit_mesh(cube().data)
        front = min(b.verts, key=lambda v: depth(v.co))
        back = max(b.verts, key=lambda v: depth(v.co))
        C["back"], C["n0"] = back.co.copy(), len(b.verts)
        C["p0"], C["p1"] = to_window(front.co), to_window(back.co)
        ev('MOUSEMOVE', 'NOTHING', x=C["p0"][0], y=C["p0"][1])
        redraw()

    def down():
        ev('LEFTMOUSE', 'PRESS', x=C["p0"][0], y=C["p0"][1])

    def move():
        (x0, y0), (x1, y1) = C["p0"], C["p1"]
        for i in range(1, 9):
            ev('MOUSEMOVE', 'NOTHING', x=x0 + (x1 - x0) * i // 8, y=y0 + (y1 - y0) * i // 8)

    def wait():
        redraw()

    def up():
        ev('LEFTMOUSE', 'RELEASE', x=C["p1"][0], y=C["p1"][1])

    for fn in (press, down, move, wait, up):
        fn.__name__ = f"s_{tag}_{fn.__name__}"
        step(fn)


@step
def s_setup():
    setup()
    ob = cube()
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.context.tool_settings.mesh_select_mode = (True, False, False)
        bpy.ops.wm.tool_set_by_id(name="allset.target_weld_tool")
    shading = area.spaces.active.shading
    shading.type = 'SOLID'
    shading.show_xray = False
    redraw()


drag_steps("hidden")


@step
def s_not_welded():
    n = len(bm().verts)
    check(f"shaded, no X-ray: a drag onto the hidden back corner welds nothing ({C['n0']} -> {n} vertices)",
          n == C["n0"])
    ev('MOUSEMOVE', 'NOTHING', x=C["p0"][0] + 300, y=C["p0"][1])
    area, _region = view3d()
    area.spaces.active.shading.show_xray = True
    redraw()


drag_steps("xray")


@step
def s_welded():
    b = bm()
    n = len(b.verts)
    at = any((v.co - C["back"]).length < 1e-5 for v in b.verts)
    check(f"with X-ray the same drag welds onto the back corner ({C['n0']} -> {n} vertices)",
          n == C["n0"] - 1 and at)
    view3d()[0].spaces.active.shading.show_xray = False


run()
