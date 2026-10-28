"""#180 in a real UI: Quad Draw, Tab held + drag from the inner corner vertex of an L of three quads = the corner quad
(the vertex, its two border neighbours and the point under the mouse on the live surface); the same drag from an
outer corner makes nothing (the quad would fold over the face there)."""

import os
import sys

import bmesh
import bpy
from bpy_extras import view3d_utils
from mathutils import Quaternion, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, ev, run, screenshot, setup, step, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def shot(name):
    if SHOTS:
        screenshot(os.path.join(SHOTS, name))


def override():
    area, region = view3d()
    return bpy.context.temp_override(window=win(), area=area, region=region)


def to_window(w):
    area, region = view3d()
    p = view3d_utils.location_3d_to_region_2d(region, area.spaces.active.region_3d, Vector(w))
    return region.x + round(p.x), region.y + round(p.y)


def counts():
    b = bmesh.from_edit_mesh(bpy.data.objects["L"].data)
    return len(b.verts), len(b.edges), len(b.faces)


def l_mesh():
    """Three quads of a 2 x 2 grid (size 2, at z = 0.001 over the ground) without the +x -y one."""
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=2, y_segments=2, size=1.0)
    gone = next(f for f in bm.faces if f.calc_center_median().x > 0 and f.calc_center_median().y < 0)
    bmesh.ops.delete(bm, geom=[gone], context='FACES')
    me = bpy.data.meshes.new("L")
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("L", me)
    ob.location.z = 0.001
    bpy.context.scene.collection.objects.link(ob)
    return ob


@step
def s_setup():
    C["x"], C["y"] = setup()
    with override():
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    with override():
        bpy.ops.mesh.primitive_plane_add(size=10)
        bpy.ops.allset.make_live()
    lob = l_mesh()
    for ob in bpy.context.scene.objects:
        ob.select_set(ob is lob)
    bpy.context.view_layer.objects.active = lob
    area, _r = view3d()
    rv3d = area.spaces.active.region_3d
    rv3d.view_rotation = Quaternion((1, 0, 0, 0))      # top
    rv3d.view_perspective = 'ORTHO'
    rv3d.view_location = (0.0, 0.0, 0.0)
    rv3d.view_distance = 5.0
    ev('MOUSEMOVE', 'NOTHING', x=C["x"], y=C["y"])
    ev('Q', 'PRESS', ctrl=True, shift=True)
    ev('Q', 'RELEASE', ctrl=True, shift=True)


@step
def s_tool():
    ob = bpy.context.edit_object
    check(f"Ctrl+Shift+Q edits the L in Quad Draw ({ob and ob.name})", ob is not None and ob.name == "L")
    C["n0"] = counts() if ob is not None else None
    x, y = to_window((0.0, 0.0, 0.001))
    ev('MOUSEMOVE', 'NOTHING', x=x + 1, y=y)
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)


def tab_drag(name, start, end):
    @step
    def s_tab():
        x, y = to_window(start)
        ev('TAB', 'PRESS', x=x, y=y)

    @step
    def s_press():
        x, y = to_window(start)
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
        ev('LEFTMOUSE', 'PRESS', x=x, y=y)

    @step
    def s_move():
        x, y = to_window(end)
        ev('MOUSEMOVE', 'NOTHING', x=x - 6, y=y + 6)
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y)

    @step
    def s_release():
        shot(f"180_{name}_drag.png")
        ev('LEFTMOUSE', 'RELEASE')

    @step
    def s_tab_up():
        ev('TAB', 'RELEASE')
        C[name] = counts()


tab_drag("inner", (0.0, 0.0, 0.001), (0.9, -0.9, 0.0))


@step
def s_inner():
    n0, n = C["n0"], C["inner"]
    check(f"Tab+drag the inner corner vertex = the corner quad ({n0} -> {n})", n == (9, 12, 4))
    b = bmesh.from_edit_mesh(bpy.data.objects["L"].data)
    new = [v.co for v in b.verts if v.co.x > 0.5 and v.co.y < -0.5]
    check(f"its fourth corner is the point under the mouse on the live surface ({[tuple(round(c, 2) for c in v) for v in new]})",
          len(new) == 1 and abs(new[0].x - 0.9) < 0.1 and abs(new[0].y + 0.9) < 0.1 and abs(new[0].z + 0.001) < 1e-3)
    shot("180_inner_done.png")


tab_drag("outer", (-1.0, 1.0, 0.001), (-1.5, 1.5, 0.0))


@step
def s_outer():
    check(f"Tab+drag an outer corner vertex makes nothing ({C['inner']} -> {C['outer']})", C["outer"] == C["inner"])


run()
