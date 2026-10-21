"""Audit 128 repro: Ctrl+Shift+click in component mode must ADD only the clicked component (Maya: Shift toggle /
Ctrl remove / Ctrl+Shift add, research/maya/interaction.md:71). In the Maya keyconfig the IC "Mesh" keymap's
Ctrl+Shift+LMB mesh.shortest_path_pick runs before the 3D View select item, so it selects the whole path.
PASSES when fixed."""

import os
import sys

import bpy
import bmesh
from bpy_extras import view3d_utils

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sim import check, ev, run, setup, step, view3d, win  # noqa: E402

C = {}


def in_v3d(fn, *a, **kw):
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        return fn(*a, **kw)


def bm():
    return bmesh.from_edit_mesh(bpy.context.active_object.data)


def face_px(index):
    area, region = view3d()
    rv3d = area.spaces.active.region_3d
    b = bm()
    b.faces.ensure_lookup_table()
    ob = bpy.context.active_object
    p = view3d_utils.location_3d_to_region_2d(region, rv3d, ob.matrix_world @ b.faces[index].calc_center_median())
    return int(region.x + p.x), int(region.y + p.y)


def sel():
    return sorted(f.index for f in bm().faces if f.select)


@step
def s_setup():
    setup()
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)
    in_v3d(bpy.ops.mesh.primitive_grid_add, x_subdivisions=5, y_subdivisions=5, size=4)
    area, region = view3d()
    rv3d = area.spaces.active.region_3d
    rv3d.view_perspective = 'ORTHO'
    rv3d.view_rotation = (1, 0, 0, 0)       # top view
    rv3d.view_location = (0, 0, 0)
    rv3d.view_distance = 6
    in_v3d(bpy.ops.object.mode_set, mode='EDIT')
    bpy.context.tool_settings.mesh_select_mode = (False, False, True)
    in_v3d(bpy.ops.mesh.select_all, action='DESELECT')
    in_v3d(bpy.ops.wm.tool_set_by_id, name="builtin.select_box")
    C["n"] = len(bm().faces)


@step
def s_hover_first():
    C["p0"] = face_px(0)
    ev('MOUSEMOVE', 'NOTHING', x=C["p0"][0], y=C["p0"][1])


@step
def s_click_first():
    ev('LEFTMOUSE', 'PRESS')
    ev('LEFTMOUSE', 'RELEASE')


@step
def s_hover_last():
    C["first"] = sel()
    C["p1"] = face_px(C["n"] - 1)
    ev('MOUSEMOVE', 'NOTHING', x=C["p1"][0], y=C["p1"][1])


@step
def s_ctrl_shift():
    ev('LEFTMOUSE', 'PRESS', shift=True, ctrl=True)
    ev('LEFTMOUSE', 'RELEASE', shift=True, ctrl=True)


@step
def s_check():
    got = sel()
    ops = [op.bl_idname for op in bpy.context.window_manager.operators[-2:]]
    print("AUDIT ctrl+shift", C["first"], got, ops)
    check(f"click selects the corner face ({C['first']})", C["first"] == [0])
    check(f"Ctrl+Shift+click adds only the clicked face: [0, {C['n'] - 1}] (got {len(got)} faces, ops {ops})",
          got == [0, C["n"] - 1])


run()
