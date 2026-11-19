"""#383 in a real UI: on the extrude manipulator (top face -> Ctrl+E) Ctrl+drag on the Local Scale Z cube scales
Local Scale X and Y together and keeps Z, Ctrl+drag on the Local Translate Z arrow moves in Local Translate X / Y
and keeps Z, like Maya; a plain drag on the cube still scales its own axis."""

import math
import os
import sys
from importlib import import_module

import bmesh
import bpy
from bpy_extras import view3d_utils
from mathutils import Euler, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, ev, run, setup, step, view3d, win  # noqa: E402

C = {}


def mod(name):
    return import_module(sys.modules["sim"].MODULE + name)


def cube():
    return bpy.data.objects["Cube"]


def rec():
    return mod(".operators.extrude").active(bpy.context)[1]


def params():
    return dict(mod(".operators.extrude").DEFAULTS, **rec().params)


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


def v3d_ctx():
    area, region = view3d()
    return bpy.context.temp_override(window=win(), area=area, region=region, space_data=area.spaces.active)


def handle_point(axis, frac):
    """Window point at ``frac`` arrow units along the manipulator's ``axis`` from its centre, and the screen
    direction of that axis."""
    area, region = view3d()
    in_view = mod(".ui.in_view")
    with v3d_ctx():
        ob, r = in_view.record(bpy.context)
        c, axes, _k = in_view.manip_frame(ob, r)
        upx = in_view.unit_px(bpy.context)
    rv3d = area.spaces.active.region_3d
    p0 = view3d_utils.location_3d_to_region_2d(region, rv3d, c)
    w = view3d_utils.region_2d_to_location_3d(region, rv3d, p0 + Vector((1, 0)), c) - c
    unit = upx * w.length
    p = view3d_utils.location_3d_to_region_2d(region, rv3d, c + axes.col[axis] * unit * frac)
    d = (p - p0).normalized()
    return region.x + round(p.x), region.y + round(p.y), d


def drag_steps(name, frac, dist, ctrl, side=False):
    """Steps: hover the Z handle at ``frac``, (Ctrl key +) press, moves along its screen direction (or sideways),
    release (+ Ctrl up)."""
    def s_hover():
        x, y, d = handle_point(2, frac)
        C[name] = (x, y, d)
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
        ev('MOUSEMOVE', 'NOTHING', x=x + 1, y=y)

    def s_press():
        x, y, _d = C[name]
        if ctrl:
            ev('LEFT_CTRL', 'PRESS', ctrl=True)
        ev('LEFTMOUSE', 'PRESS', x=x, y=y, ctrl=ctrl)

    def s_moves():
        x, y, d = C[name]
        v = Vector((dist, 0)) if side else d * dist
        for i in range(1, 9):
            ev('MOUSEMOVE', 'NOTHING', x=x + round(v.x * i / 8), y=y + round(v.y * i / 8), ctrl=ctrl)

    def s_release():
        x, y, d = C[name]
        v = Vector((dist, 0)) if side else d * dist
        ev('LEFTMOUSE', 'RELEASE', x=x + round(v.x), y=y + round(v.y), ctrl=ctrl)
        if ctrl:
            ev('LEFT_CTRL', 'RELEASE')
    for s in (s_hover, s_press, s_moves, s_release):
        s.__name__ = f"s_{name}_{s.__name__}"
        step(s)


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
        f.select_set(f.normal.z > 0.9)
    bm.select_flush_mode()
    bmesh.update_edit_mesh(cube().data)
    ev('MOUSEMOVE', 'NOTHING', x=C["x"] - 300, y=C["y"] - 200)
    redraw()


@step
def s_ctrl_e():
    ev('E', 'PRESS', ctrl=True)
    ev('E', 'RELEASE', ctrl=True)


@step
def s_extruded():
    check(f"Ctrl+E made an extrusion ({rec() and rec().name})", rec() is not None)
    C["p0"] = params()
    redraw()


drag_steps("sz", 1.0, 60, ctrl=True)


@step
def s_sz_check():
    p, p0 = params(), C["p0"]
    sx, sy, sz = p["local_scale_x"], p["local_scale_y"], p["local_scale_z"]
    check(f"Ctrl+drag on the Z scale cube scales X and Y, keeps Z ({sx:.3f}, {sy:.3f}, {sz:.3f})",
          abs(sz - p0["local_scale_z"]) < 1e-6 and abs(sx - p0["local_scale_x"]) > 1e-3 and abs(sx - sy) < 1e-6)
    C["p1"] = p


drag_steps("tz", 0.35, 70, ctrl=True, side=True)


@step
def s_tz_check():
    p, p0 = params(), C["p1"]
    tx, ty, tz = p["local_translate_x"], p["local_translate_y"], p["local_translate_z"]
    check(f"Ctrl+drag on the Z arrow moves in X / Y, keeps Z ({tx:.3f}, {ty:.3f}, {tz:.3f})",
          abs(tz - p0["local_translate_z"]) < 1e-6
          and (abs(tx - p0["local_translate_x"]) > 1e-3 or abs(ty - p0["local_translate_y"]) > 1e-3))
    C["p2"] = p


drag_steps("plain", 1.0, 60, ctrl=False)


@step
def s_plain_check():
    p, p0 = params(), C["p2"]
    check(f"a plain drag on the Z scale cube scales Z only ({p['local_scale_x']:.3f}, {p['local_scale_y']:.3f}, "
          f"{p['local_scale_z']:.3f})",
          abs(p["local_scale_z"] - p0["local_scale_z"]) > 1e-3 and abs(p["local_scale_x"] - p0["local_scale_x"]) < 1e-6)


run()
