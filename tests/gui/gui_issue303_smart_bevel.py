"""In a real UI (#303): an edge of the cube -> Edit Mesh > Smart Bevel (Width 0.2, Segments 2) -> polySmartBevel1
with the In-View Editor (Width / Segments / Depth rows) and the manipulator arrow -> drag the arrow -> Width grows,
the mesh is rebuilt with the same vertex count -> T after picking the Move tool brings the manipulator back."""

import os
import sys
from importlib import import_module

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, dock_area, ev, px, run, screenshot, setup, step, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def shot(name):
    if SHOTS:
        screenshot(os.path.join(SHOTS, name))


def mod(name):
    return import_module(sys.modules["sim"].MODULE + name)


def cube():
    return bpy.data.objects["Cube"]


def counts():
    bm = bmesh.from_edit_mesh(cube().data)
    return len(bm.verts), len(bm.faces)


def rec():
    return mod(".operators.extrude").active(bpy.context)[1]


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


def v3d_ctx():
    area, region = view3d()
    return bpy.context.temp_override(window=win(), area=area, region=region, space_data=area.spaces.active)


def in_view_rows():
    area, region = view3d()
    in_view = mod(".ui.in_view")
    with v3d_ctx():
        _r, lay = in_view.current_layout(bpy.context)
    if lay is None:
        return None
    return {f: (region.x + round((x0 + x1) / 2), region.y + round((y0 + y1) / 2)) for f, x0, y0, x1, y1 in lay["rows"]}


def arrow_point():
    from bpy_extras import view3d_utils
    area, region = view3d()
    in_view = mod(".ui.in_view")
    with v3d_ctx():
        ob, r = in_view.record(bpy.context)
        c, n, _k = in_view.cap_frame(ob, r)
    rv3d = area.spaces.active.region_3d
    p0 = view3d_utils.location_3d_to_region_2d(region, rv3d, c)
    p1 = view3d_utils.location_3d_to_region_2d(region, rv3d, c + n * 0.01)
    d = (p1 - p0).normalized()
    p = p0 + d * px(45)
    return region.x + round(p.x), region.y + round(p.y), d


@step
def s_setup():
    C["x"], C["y"] = setup()
    dock_area('CHANNEL_BOX')
    bpy.context.view_layer.objects.active = cube()
    cube().select_set(True)
    with v3d_ctx():
        bpy.ops.object.mode_set('EXEC_DEFAULT', True, mode='EDIT')
    bpy.context.scene.tool_settings.mesh_select_mode = (False, True, False)
    bm = bmesh.from_edit_mesh(cube().data)
    for el in (*bm.verts, *bm.edges, *bm.faces):
        el.select_set(False)
    top = max(v.co.z for v in bm.verts)
    e = next(e for e in bm.edges if all(abs(v.co.z - top) < 1e-6 for v in e.verts)
             and abs(e.verts[0].co.x - e.verts[1].co.x) > 1e-6 and e.verts[0].co.y < 0)
    e.select_set(True)
    bm.select_flush_mode()
    bmesh.update_edit_mesh(cube().data)
    C["n0"] = counts()
    ev('MOUSEMOVE', 'NOTHING', x=C["x"] - px(200), y=C["y"] - px(150))
    redraw()


@step
def s_smart_bevel():
    with v3d_ctx():
        C["res"] = bpy.ops.allset.menu_item('EXEC_DEFAULT', True, item="Edit Mesh/Smart Bevel")


@step
def s_node():
    r = rec()
    n = counts()
    check(f"Edit Mesh > Smart Bevel = polySmartBevel1 ({C['res']}, {r and r.name}, {n})",
          C["res"] == {'FINISHED'} and r is not None and r.name == "polySmartBevel1" and n[0] == C["n0"][0] + 2)
    check("the node's spec is Smart Bevel with the Width arrow", r is not None and r.spec.arrow == "width")
    with v3d_ctx():
        check("the manipulator / In-View Editor show", mod(".ui.in_view").manip_visible(bpy.context))
    redraw()


@step
def s_rows():
    shot("gui_issue303_smart_bevel.png")
    C["rows"] = in_view_rows()
    rows = list(C["rows"]) if C["rows"] else None
    check(f"In-View rows Width / Segments / Depth on screen ({rows})",
          rows is not None and rows[:3] == ["width", "segments", "depth"])
    C["arrow"] = arrow_point()
    x, y, _d = C["arrow"]
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)


@step
def s_press_arrow():
    redraw()
    x, y, _d = C["arrow"]
    ev('LEFTMOUSE', 'PRESS', x=x, y=y)


@step
def s_drag_arrow():
    x, y, d = C["arrow"]
    n = px(40)
    for i in range(1, 9):
        ev('MOUSEMOVE', 'NOTHING', x=x + round(d.x * n * i / 8), y=y + round(d.y * n * i / 8))
    C["end"] = (x + round(d.x * n), y + round(d.y * n))


@step
def s_release_arrow():
    ev('LEFTMOUSE', 'RELEASE', x=C["end"][0], y=C["end"][1])


@step
def s_dragged():
    r = rec()
    w = r.params["width"] if r else None
    check(f"dragging the arrow out grew the Width (0.2 -> {w}), same vertex count {counts()}",
          r is not None and w is not None and w > 0.2 + 1e-4 and counts()[0] == C["n0"][0] + 2)
    C["w"] = w
    shot("gui_issue303_smart_bevel_drag.png")
    ev('MOUSEMOVE', 'NOTHING', x=C["x"] - px(200), y=C["y"] - px(150))


@step
def s_move_tool():
    ev('W', 'PRESS')          # Maya Move tool: the manipulator of the node gives way
    ev('W', 'RELEASE')


@step
def s_t_back():
    with v3d_ctx():
        C["gone"] = not mod(".ui.in_view").manip_visible(bpy.context)
    ev('T', 'PRESS')
    ev('T', 'RELEASE')


@step
def s_t_shows():
    with v3d_ctx():
        back = mod(".ui.in_view").manip_visible(bpy.context)
    check(f"W hides the Smart Bevel manipulator ({C['gone']}), T brings it back ({back})", C["gone"] and back)
    r = rec()
    check("the node and its Width survive", r is not None and r.name == "polySmartBevel1"
          and abs(r.params["width"] - C["w"]) < 1e-6)


run()
