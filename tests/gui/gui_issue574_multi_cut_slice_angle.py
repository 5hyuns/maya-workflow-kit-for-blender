"""#574: Multi-Cut, a slice dragged with Shift held has its screen angle in 10 degree steps; without Shift
the line follows the mouse; the tool shows the knife pointer, like Maya."""

import math
import os
import sys
from importlib import import_module

import bmesh
import bpy
from mathutils import Quaternion

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, setup, step, view3d, win  # noqa: E402

C = {}


def override():
    a, r = view3d()
    return bpy.context.temp_override(window=win(), area=a, region=r)


def plane_verts():
    b = bmesh.from_edit_mesh(bpy.context.edit_object.data)
    return [v.co.copy() for v in b.verts]


def new_angle():
    """Screen angle (degrees, 0..180) of the line through the vertices the slice added."""
    new = [v for v in plane_verts() if all((v - o).length > 1e-4 for o in C["before"])]
    if len(new) < 2:
        return None
    a, b = new[0], new[-1]
    return math.degrees(math.atan2(b.y - a.y, b.x - a.x)) % 180.0


def prepare():
    with override():
        if bpy.context.object and bpy.context.object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)
        bpy.ops.mesh.primitive_plane_add(size=4)
        bpy.ops.object.mode_set(mode='EDIT')
        a, r = view3d()
        rv = a.spaces.active.region_3d
        rv.view_rotation = Quaternion((1, 0, 0, 0))     # top
        rv.view_perspective = 'ORTHO'
        rv.view_location = (0, 0, 0)
        rv.view_distance = 9
        bpy.ops.wm.tool_set_by_id(name=import_module(MODULE + ".operators.multi_cut").TOOL, space_type='VIEW_3D')
    C["before"] = plane_verts()


def start_drag(deg, shift):
    a, r = view3d()
    cx, cy = r.x + r.width // 2, r.y + r.height // 2
    length = r.height * 0.45
    t = math.radians(deg)
    C["p0"] = (round(cx - length * math.cos(t)), round(cy - length * math.sin(t)))
    C["p1"] = (round(cx + length * math.cos(t)), round(cy + length * math.sin(t)))
    C["shift"] = shift
    ev('MOUSEMOVE', 'NOTHING', x=C["p0"][0], y=C["p0"][1])
    ev('LEFTMOUSE', 'PRESS', x=C["p0"][0], y=C["p0"][1])


def mid_drag():
    x = (C["p0"][0] * 3 + C["p1"][0]) // 4
    y = (C["p0"][1] * 3 + C["p1"][1]) // 4
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    if C["shift"]:
        ev('LEFT_SHIFT', 'PRESS', shift=True)
    ev('MOUSEMOVE', 'NOTHING', x=C["p1"][0], y=C["p1"][1], shift=C["shift"])


def end_drag():
    ev('LEFTMOUSE', 'RELEASE', x=C["p1"][0], y=C["p1"][1], shift=C["shift"])
    if C["shift"]:
        ev('LEFT_SHIFT', 'RELEASE')


@step
def s_setup():
    setup()
    prepare()
    tool = import_module(MODULE + ".ui.mesh_tools").ALLSET_TL_multi_cut
    check(f"the Multi-Cut tool shows the knife pointer ({tool.bl_cursor})", tool.bl_cursor == 'KNIFE')


CASES = ((16, True, 20.0), (44, True, 40.0), (136, True, 140.0), (16, False, None))


def make_case(deg, shift, want):
    @step
    def s_press():
        prepare()
        start_drag(deg, shift)

    @step
    def s_move():
        mid_drag()

    @step
    def s_release():
        end_drag()

    @step
    def s_check():
        got = new_angle()
        label = "Shift" if shift else "no Shift"
        if want is None:
            check(f"{label}: a {deg} degree slice follows the mouse ({got})", got is not None and abs(got - deg) < 1.5)
        else:
            check(f"{label}: a {deg} degree slice is cut at {want} degrees ({got})",
                  got is not None and abs(got - want) < 0.05)


for _deg, _shift, _want in CASES:
    make_case(_deg, _shift, _want)

run()
