"""Mesh Tools > Connect in a real UI (issue #322): from object mode the menu item enters component mode with the
kit Connect Tool; a click on one edge and then on the opposite edge of the same face joins them, a third click
continues the path, Enter ends it, Ctrl+click an edge connects its ring, Ctrl+Z takes back one connection."""

import os
import sys
from importlib import import_module

import bmesh
import bpy
from bpy_extras import view3d_utils
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, screenshot, setup, step, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def ct():
    return import_module(MODULE + ".operators.connect_tool")


def override():
    area, region = view3d()
    return bpy.context.temp_override(window=win(), area=area, region=region)


def menu(path):
    with override():
        return bpy.ops.allset.menu_item('EXEC_DEFAULT', True, item=path)


def tool_id():
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        t = bpy.context.workspace.tools.from_space_view3d_mode(bpy.context.mode, create=False)
    return t.idname if t else None


def to_window(w):
    area, region = view3d()
    p = view3d_utils.location_3d_to_region_2d(region, area.spaces.active.region_3d, Vector(w))
    return region.x + round(p.x), region.y + round(p.y)


def cube():
    return bpy.data.objects["Cube"]


def counts():
    b = bmesh.from_edit_mesh(cube().data)
    return len(b.verts), len(b.edges), len(b.faces)


def click(w, ctrl=False):
    x, y = to_window(w)
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('LEFTMOUSE', 'PRESS', x=x, y=y, ctrl=ctrl)
    ev('LEFTMOUSE', 'RELEASE', x=x, y=y, ctrl=ctrl)


@step
def s_setup():
    C["x"], C["y"] = setup()
    area, _r = view3d()
    rv3d = area.spaces.active.region_3d
    rv3d.view_location = (0.0, 0.0, 0.0)
    rv3d.view_distance = 7.0
    with override():
        bpy.ops.object.select_all(action='DESELECT')
    cube().select_set(True)
    bpy.context.view_layer.objects.active = cube()
    menu("Mesh Tools/Connect")


@step
def s_entered():
    check(f"Mesh Tools > Connect = component mode + the kit Connect Tool ({bpy.context.mode}, {tool_id()})",
          bpy.context.mode == 'EDIT_MESH' and tool_id() == ct().TOOL)
    with override():
        bpy.ops.mesh.select_all('EXEC_DEFAULT', True, action='DESELECT')
    C["n0"] = counts()
    click((-1.0, -1.0, 0.2))        # the front face's left edge (seen in the factory view)


@step
def s_first():
    check(f"the first click only starts the path ({counts()})", counts() == C["n0"])
    click((1.0, -1.0, -0.2))        # the opposite edge of the front face


@step
def s_second():
    v, e, f = counts()
    v0, e0, f0 = C["n0"]
    check(f"the second click joins the two edges across the face ({(v, e, f)} from {C['n0']})",
          (v, e, f) == (v0 + 2, e0 + 3, f0 + 1))
    click((1.0, 0.2, 1.0))          # the right face top edge: continue the path


@step
def s_third():
    v, e, f = counts()
    v0, e0, f0 = C["n0"]
    check(f"a third click continues the path across the right face ({(v, e, f)})",
          (v, e, f) == (v0 + 3, e0 + 5, f0 + 2))
    if SHOTS:
        screenshot(os.path.join(SHOTS, "gui_issue322_connect_path.png"))
    ev('RET', 'PRESS', x=C["x"], y=C["y"])
    ev('RET', 'RELEASE', x=C["x"], y=C["y"])


@step
def s_ended():
    check("Enter ends the path", not ct()._path)
    C["n1"] = counts()
    ev('MOUSEMOVE', 'NOTHING', x=C["x"], y=C["y"])
    ev('Z', 'PRESS', ctrl=True)
    ev('Z', 'RELEASE', ctrl=True)


@step
def s_undo():
    v, e, f = counts()
    v0, e0, f0 = C["n0"]
    check(f"Ctrl+Z takes back the last connection only ({(v, e, f)})", (v, e, f) == (v0 + 2, e0 + 3, f0 + 1))
    check(f"Ctrl+Z keeps component mode and the tool ({bpy.context.mode}, {tool_id()})",
          bpy.context.mode == 'EDIT_MESH' and tool_id() == ct().TOOL)
    C["n2"] = counts()
    click((-0.2, -1.0, -1.0), ctrl=True)     # the front face's bottom edge: its ring


@step
def s_ring():
    v, e, f = counts()
    v2, e2, f2 = C["n2"]
    check(f"Ctrl+click an edge connects its ring ({(v, e, f)} from {C['n2']})", v > v2 and f > f2)
    if SHOTS:
        screenshot(os.path.join(SHOTS, "gui_issue322_connect_ring.png"))


if __name__ == "__main__":
    run()
