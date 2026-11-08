"""#321 in a real UI: top face -> Edit Mesh > Transform (Transform Component) -> the manipulator in the face's local
frame and the In-View Editor show, the mesh unchanged; drag the blue Z arrow (Local Translate Z: the face moves up
along its normal, one Ctrl+Z step) and the red X scale cube (Local Scale X). Then the light-blue ring: a quarter-turn
drag turns the face about the view axis (Local Rotate, one Ctrl+Z step) and shows the rotate rings, a click hides
them; the world / local switch puts the manipulator on world axes, where the up arrow drives Translate Z.
Screenshots gui_issue321_transform.png, gui_issue321_ring.png, gui_issue321_world.png."""

import math
import os
import sys
from importlib import import_module

import bmesh
import bpy
from bpy_extras import view3d_utils
from mathutils import Euler, Matrix, Vector

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


# --- the light-blue ring and the world / local switch ---------------------------------------------------------

def top_normal():
    bm = bmesh.from_edit_mesh(cube().data)
    bm.faces.ensure_lookup_table()
    sel = [f for f in bm.faces if f.select]
    return sum((f.normal for f in sel), Vector()).normalized()


def ring_geometry():
    """(centre px (window), ring radius px, free angle on the ring away from every arrow, view axis toward the
    viewer)."""
    area, region = view3d()
    in_view = mod(".ui.in_view")
    with v3d_ctx():
        ob, r = in_view.record(bpy.context)
        c, axes, _k = in_view.manip_frame(ob, r)
        upx = in_view.unit_px(bpy.context)
    rv3d = area.spaces.active.region_3d
    p0 = view3d_utils.location_3d_to_region_2d(region, rv3d, c)
    dirs = []
    for i in range(3):
        p = view3d_utils.location_3d_to_region_2d(region, rv3d, c + axes.col[i] * 0.01)
        if (p - p0).length > 1e-6:
            dirs.append(math.atan2(p.y - p0.y, p.x - p0.x))

    def gap(a):
        return min(abs((a - d + math.pi) % (2 * math.pi) - math.pi) for d in dirs) if dirs else math.pi
    free = max((math.radians(k * 5) for k in range(72)), key=gap)
    view = (rv3d.view_rotation @ Vector((0, 0, 1))).normalized()
    return (region.x + p0.x, region.y + p0.y), in_view.VIEW_RING_R * upx, free, view


def ring_at(a, radius=None):
    (cx, cy), rr, _free, _view = C["ring"]
    rr = rr if radius is None else radius
    return round(cx + rr * math.cos(a)), round(cy + rr * math.sin(a))


@step
def s_ring_setup():
    ev('MOUSEMOVE', 'NOTHING', x=C["x"] - 300, y=C["y"] - 200)
    C["ring"] = ring_geometry()
    C["n0"] = top_normal()
    C["rot0"] = tuple(rec().params[f] for f in ("local_rotate_x", "local_rotate_y", "local_rotate_z"))
    redraw()


@step
def s_ring_hover():
    ev('MOUSEMOVE', 'NOTHING', x=ring_at(C["ring"][2])[0], y=ring_at(C["ring"][2])[1])


@step
def s_ring_press():
    x, y = ring_at(C["ring"][2])
    ev('LEFTMOUSE', 'PRESS', x=x, y=y)


@step
def s_ring_sweep():
    a0 = C["ring"][2]
    for i in range(1, 10):           # a quarter turn counter-clockwise round the centre
        x, y = ring_at(a0 + math.radians(90) * i / 9)
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y)


@step
def s_ring_release():
    x, y = ring_at(C["ring"][2] + math.radians(90))
    ev('LEFTMOUSE', 'RELEASE', x=x, y=y)


@step
def s_ring_done():
    r = rec()
    rot = tuple(r.params[f] for f in ("local_rotate_x", "local_rotate_y", "local_rotate_z")) if r else None
    view = C["ring"][3]
    want = Matrix.Rotation(math.radians(90), 3, view) @ C["n0"]
    got = top_normal()
    err = math.degrees(got.angle(want, 0.0))
    state = mod(".ui.in_view").flags(r)
    check(f"drag the light-blue ring a quarter turn -> Local Rotate changes, the top face turns 90 deg about the view "
          f"axis ({rot}, normal off by {err:.1f} deg), the press shows the rotate rings ({state})",
          r is not None and rot != C["rot0"] and err < 4.0 and state == (False, True))
    ev('MOUSEMOVE', 'NOTHING', x=C["x"] - 300, y=C["y"] - 200)
    redraw()


@step
def s_rings_shot():
    if SHOTS:
        screenshot(os.path.join(SHOTS, "gui_issue321_rings.png"))


@step
def s_ring_undo():
    ev('Z', 'PRESS', ctrl=True)
    ev('Z', 'RELEASE', ctrl=True)


@step
def s_ring_undone():
    r = rec()
    rot = tuple(r.params[f] for f in ("local_rotate_x", "local_rotate_y", "local_rotate_z")) if r else None
    err = math.degrees(top_normal().angle(C["n0"], 0.0))
    check(f"one Ctrl+Z takes the turn back ({rot}, normal {err:.2f} deg off)",
          rot == C["rot0"] and err < 0.5)
    redraw()


@step
def s_ring_click_hover():
    C["ring"] = ring_geometry()
    x, y = ring_at(C["ring"][2])
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)


@step
def s_ring_click():
    x, y = ring_at(C["ring"][2])
    ev('LEFTMOUSE', 'PRESS', x=x, y=y)
    ev('LEFTMOUSE', 'RELEASE', x=x, y=y)


@step
def s_ring_clicked():
    r = rec()
    rot = tuple(r.params[f] for f in ("local_rotate_x", "local_rotate_y", "local_rotate_z")) if r else None
    check(f"a click on the ring hides the rotate rings again, no value changes ({mod('.ui.in_view').flags(r)}, {rot})",
          r is not None and mod(".ui.in_view").flags(r) == (False, False) and rot == C["rot0"])
    ev('MOUSEMOVE', 'NOTHING', x=C["x"] - 300, y=C["y"] - 200)
    if SHOTS:
        screenshot(os.path.join(SHOTS, "gui_issue321_ring.png"))


@step
def s_space_hover():
    _area, region = view3d()
    with v3d_ctx():
        (x, y), rr = mod(".ui.in_view").space_button(bpy.context)
    C["space"] = (region.x + round(x), region.y + round(y))
    ev('MOUSEMOVE', 'NOTHING', x=C["space"][0], y=C["space"][1])


@step
def s_space_click():
    ev('LEFTMOUSE', 'PRESS', x=C["space"][0], y=C["space"][1])
    ev('LEFTMOUSE', 'RELEASE', x=C["space"][0], y=C["space"][1])


@step
def s_space_done():
    r = rec()
    check(f"a click on the switch puts the manipulator on world axes ({mod('.ui.in_view').flags(r)})",
          r is not None and mod(".ui.in_view").flags(r) == (True, False))
    C["z_before"], _xs = top()
    C["ltz_before"] = r.params["local_translate_z"]
    ev('MOUSEMOVE', 'NOTHING', x=C["x"] - 300, y=C["y"] - 200)
    redraw()
    if SHOTS:
        screenshot(os.path.join(SHOTS, "gui_issue321_world.png"))


@step
def s_world_point():
    area, region = view3d()
    in_view = mod(".ui.in_view")
    with v3d_ctx():
        ob, r = in_view.record(bpy.context)
        c, axes, _k = in_view.manip_frame(ob, r, True)
        upx = in_view.unit_px(bpy.context)
    rv3d = area.spaces.active.region_3d
    p0 = view3d_utils.location_3d_to_region_2d(region, rv3d, c)
    w = view3d_utils.region_2d_to_location_3d(region, rv3d, p0 + Vector((1, 0)), c) - c
    p = view3d_utils.location_3d_to_region_2d(region, rv3d, c + axes.col[2] * upx * w.length * 0.5)
    C["wz"] = (region.x + round(p.x), region.y + round(p.y), (p - p0).normalized())


_drag_steps("wz", 50)


@step
def s_world_done():
    r = rec()
    z, _xs = top()
    tz = r.params["translate_z"] if r else None
    check(f"on world axes the blue up arrow drives Translate Z, not Local Translate Z ({tz}, "
          f"{r and r.params['local_translate_z']}, z {C['z_before']} -> {z})",
          r is not None and tz > 0.05 and r.params["local_translate_z"] == C["ltz_before"] and z > C["z_before"] + 0.03)


run()
