"""#321 in a real UI: top face -> Edit Mesh > Transform (Transform Component) -> the manipulator in the face's local
frame and the In-View Editor show, the mesh unchanged; drag the blue Z arrow (Local Translate Z: the face moves up
along its normal, one Ctrl+Z step) and the red X scale cube (Local Scale X). Screenshot gui_issue321_transform.png."""

import math
import os
import sys
from importlib import import_module

import bmesh
import bpy
from bpy_extras import view3d_utils
from mathutils import Euler, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, ev, run, screenshot, setup, step, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def mod(name):
    return import_module(sys.modules["sim"].MODULE + name)


def cube():
    return bpy.data.objects["Cube"]


def rec():
    return mod(".operators.extrude").active(bpy.context)[1]


def top():
    """(min z, x range) of the vertices that started on the top face."""
    bm = bmesh.from_edit_mesh(cube().data)
    bm.verts.ensure_lookup_table()
    vs = [bm.verts[i] for i in C["top"]]
    return min(v.co.z for v in vs), (min(v.co.x for v in vs), max(v.co.x for v in vs))


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


def v3d_ctx():
    area, region = view3d()
    return bpy.context.temp_override(window=win(), area=area, region=region, space_data=area.spaces.active)


def handle_point(axis, frac):
    area, region = view3d()
    in_view = mod(".ui.in_view")
    with v3d_ctx():
        ob, r = in_view.record(bpy.context)
        c, axes, _k = in_view.manip_frame(ob, r)
        upx = in_view.unit_px(bpy.context)
    rv3d = area.spaces.active.region_3d
    p0 = view3d_utils.location_3d_to_region_2d(region, rv3d, c)
    w = view3d_utils.region_2d_to_location_3d(region, rv3d, p0 + Vector((1, 0)), c) - c
    p = view3d_utils.location_3d_to_region_2d(region, rv3d, c + axes.col[axis] * upx * w.length * frac)
    return region.x + round(p.x), region.y + round(p.y), (p - p0).normalized()


@step
def s_setup():
    C["x"], C["y"] = setup()
    area, _region = view3d()
    rv3d = area.spaces.active.region_3d
    rv3d.view_perspective = 'PERSP'
    rv3d.view_rotation = Euler((math.radians(62), 0, math.radians(42))).to_quaternion()
    rv3d.view_location = (0, 0, 0.3)
    rv3d.view_distance = 5.0
    bpy.context.view_layer.objects.active = cube()
    cube().select_set(True)
    with v3d_ctx():
        bpy.ops.object.mode_set('EXEC_DEFAULT', True, mode='EDIT')
    bpy.context.scene.tool_settings.mesh_select_mode = (False, False, True)
    bm = bmesh.from_edit_mesh(cube().data)
    for f in bm.faces:
        f.select_set(False)
    for f in bm.faces:
        if f.normal.z > 0.9:
            f.select_set(True)
    bm.select_flush_mode()
    bm.verts.index_update()
    C["top"] = [v.index for v in bm.verts if v.select]
    bmesh.update_edit_mesh(cube().data)
    ev('MOUSEMOVE', 'NOTHING', x=C["x"] - 300, y=C["y"] - 200)
    redraw()


@step
def s_menu():
    C["z0"], C["x0"] = top()
    with v3d_ctx():
        res = bpy.ops.allset.transform_component('INVOKE_DEFAULT', True)
    check(f"Edit Mesh > Transform runs ({res})", res == {'FINISHED'})
    redraw()


@step
def s_shown():
    r = rec()
    with v3d_ctx():
        shown = mod(".ui.in_view").manip_visible(bpy.context)
    check(f"polyMoveFace1 recorded, manipulator + In-View Editor shown, mesh unchanged ({r and r.name}, {shown}, "
          f"{top()})", r is not None and r.name == "polyMoveFace1" and shown and abs(top()[0] - C["z0"]) < 1e-6)
    C["tz"] = handle_point(2, 0.5)
    C["sx"] = handle_point(0, 1.0)
    if SHOTS:
        screenshot(os.path.join(SHOTS, "gui_issue321_transform.png"))


def _drag_steps(key, dist_px):
    holder = {}

    @step
    def s_hover():
        x, y, d = C[key]
        holder["p"] = (x, y, d.x * dist_px, d.y * dist_px)
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y)

    @step
    def s_press():
        x, y, _dx, _dy = holder["p"]
        ev('LEFTMOUSE', 'PRESS', x=x, y=y)

    @step
    def s_moves():
        x, y, dx, dy = holder["p"]
        for i in range(1, 9):
            ev('MOUSEMOVE', 'NOTHING', x=x + round(dx * i / 8), y=y + round(dy * i / 8))

    @step
    def s_release():
        x, y, dx, dy = holder["p"]
        ev('LEFTMOUSE', 'RELEASE', x=x + round(dx), y=y + round(dy))


_drag_steps("tz", 60)


@step
def s_tz_done():
    r = rec()
    z, _xs = top()
    ltz = r.params["local_translate_z"] if r else None
    check(f"drag the blue Z arrow -> Local Translate Z > 0, the top face moves up ({ltz}, z {C['z0']} -> {z})",
          r is not None and ltz > 0.05 and z > C["z0"] + 0.03)
    ev('MOUSEMOVE', 'NOTHING', x=C["x"] - 300, y=C["y"] - 200)
    redraw()


@step
def s_undo():
    ev('Z', 'PRESS', ctrl=True)
    ev('Z', 'RELEASE', ctrl=True)


@step
def s_undone():
    r = rec()
    check(f"one Ctrl+Z takes the drag back ({r and r.params['local_translate_z']}, z {top()[0]})",
          r is not None and abs(r.params["local_translate_z"]) < 1e-6 and abs(top()[0] - C["z0"]) < 1e-5)
    redraw()


_drag_steps("sx", 50)


@step
def s_sx_done():
    r = rec()
    lsx = r.params["local_scale_x"] if r else None
    _z, (x0, x1) = top()
    check(f"drag the red X scale cube out -> Local Scale X > 1, the top face wider in X ({lsx}, {(x0, x1)})",
          r is not None and lsx > 1.1 and x1 - x0 > (C["x0"][1] - C["x0"][0]) * 1.1)


run()
