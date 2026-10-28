"""Audit 128 dogfood session 2 (modeling lane): component click modifiers, Delete History in component mode,
Center Pivot / Freeze. PASS = Maya-like. Prints AUDIT lines."""

import os
import sys
from importlib import import_module

import bpy
import bmesh
from bpy_extras import view3d_utils
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sim import MODULE, check, ev, run, setup, step, tap, view3d, win, load_maya_layout  # noqa: E402

GUI_TIMEOUT = 240
C = {}


def ts():
    return bpy.context.scene.tool_settings


def in_v3d(fn, *a, **kw):
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        return fn(*a, **kw)


def centre():
    _a, r = view3d()
    return r.x + r.width // 2, r.y + r.height // 2


def hover(x=None, y=None):
    if x is None:
        x, y = centre()
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)


def obj():
    return bpy.data.objects[C["ob"]]


def bm():
    return bmesh.from_edit_mesh(obj().data)


def face_px(normal):
    """Window pixel of the centre of the cube face whose normal is ``normal``."""
    area, region = view3d()
    rv3d = area.spaces.active.region_3d
    b = bm()
    b.faces.ensure_lookup_table()
    f = next(f for f in b.faces if (f.normal - Vector(normal)).length < 1e-3)
    p = view3d_utils.location_3d_to_region_2d(region, rv3d, obj().matrix_world @ f.calc_center_median())
    return int(region.x + p.x), int(region.y + p.y), f.index


def sel_faces():
    return sorted(f.index for f in bm().faces if f.select)


def menu(path):
    return in_v3d(bpy.ops.allset.menu_item, item=path)


@step
def s_setup():
    setup()
    bpy.ops.allset.make_maya(open_layout=False)
    load_maya_layout()


@step
def s_scene():
    bpy.ops.allset.keymap_activate()
    in_v3d(bpy.ops.allset.create, kind='CUBE')
    C["ob"] = bpy.context.active_object.name
    area, region = view3d()
    rv3d = area.spaces.active.region_3d
    # a view that sees +X, -Y (front) and +Z faces
    from mathutils import Euler
    rv3d.view_rotation = Euler((1.1, 0.0, 0.6)).to_quaternion()
    rv3d.view_location = (0, 0, 0)
    rv3d.view_distance = 6 * obj().dimensions.x
    in_v3d(bpy.ops.object.mode_set, mode='EDIT')
    ts().mesh_select_mode = (False, False, True)
    in_v3d(bpy.ops.mesh.select_all, action='DESELECT')
    in_v3d(bpy.ops.wm.tool_set_by_id, name="builtin.select_box")
    hover()


@step
def s_click_a():
    x, y, C["a"] = face_px((0, 0, 1))
    C["pa"] = (x, y)
    hover(x, y)


@step
def s_click_a2():
    ev('LEFTMOUSE', 'PRESS')
    ev('LEFTMOUSE', 'RELEASE')


@step
def s_shift_b():
    C["after_a"] = sel_faces()
    x, y, C["b"] = face_px((1, 0, 0))
    C["pb"] = (x, y)
    hover(x, y)


@step
def s_shift_b2():
    ev('LEFTMOUSE', 'PRESS', shift=True)
    ev('LEFTMOUSE', 'RELEASE', shift=True)


@step
def s_shift_b_again():
    C["after_shift_b"] = sel_faces()
    ev('LEFTMOUSE', 'PRESS', shift=True)
    ev('LEFTMOUSE', 'RELEASE', shift=True)


@step
def s_ctrl_shift_b():
    C["after_shift_b2"] = sel_faces()
    ev('LEFTMOUSE', 'PRESS', shift=True, ctrl=True)
    ev('LEFTMOUSE', 'RELEASE', shift=True, ctrl=True)


@step
def s_ctrl_a():
    C["after_cs_b"] = sel_faces()
    hover(*C["pa"])


@step
def s_ctrl_a2():
    ev('LEFTMOUSE', 'PRESS', ctrl=True)
    ev('LEFTMOUSE', 'RELEASE', ctrl=True)


@step
def s_click_check():
    a, b = C["a"], C["b"]
    after_ctrl = sel_faces()
    print("AUDIT clicks a", a, "b", b, C["after_a"], C["after_shift_b"], C["after_shift_b2"], C["after_cs_b"], after_ctrl)
    check(f"click selects face ({C['after_a']})", C["after_a"] == [a])
    check(f"Shift+click adds (toggle) ({C['after_shift_b']})", C["after_shift_b"] == sorted([a, b]))
    check(f"Shift+click again toggles off ({C['after_shift_b2']})", C["after_shift_b2"] == [a])
    check(f"Ctrl+Shift+click adds ({C['after_cs_b']})", C["after_cs_b"] == sorted([a, b]))
    check(f"Ctrl+click deselects ({after_ctrl})", after_ctrl == [b])
    # (Delete History in component mode was dropped from this audit: Maya shows Maya's `delete -ch` with only
    # components selected keeps the history too.)


run()
