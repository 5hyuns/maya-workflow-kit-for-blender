"""In a real UI (GitHub #421): two opposite edges of a face selected -> the Modeling Toolkit's Connect button = the
Connect Tool (one new edge) and its Connect Options in the Modeling Toolkit -> typing 5 into Segments makes five
edges instead of one, like Maya."""

import os
import sys
from importlib import import_module
from pathlib import Path

import bmesh
import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sim import MODULE, check, dock_area, dock_region, ev, find_button, run, screenshot, setup, step, tap, view3d, win  # noqa: E402

C = {}


def dock():
    return dock_area(), dock_region()


def cube():
    return bpy.data.objects["Cube"]


def counts():
    b = bmesh.from_edit_mesh(cube().data)
    return len(b.verts), len(b.edges), len(b.faces)


def tool_id():
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        t = bpy.context.workspace.tools.from_space_view3d_mode(bpy.context.mode, create=False)
    return t.idname if t else None


def redraw():
    for area in win().screen.areas:
        area.tag_redraw()


@step
def s_setup():
    setup()
    area, region = view3d()
    bpy.context.view_layer.objects.active = cube()
    cube().select_set(True)
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.context.tool_settings.mesh_select_mode = (False, True, False)
        bpy.ops.mesh.select_all(action='DESELECT')
    b = bmesh.from_edit_mesh(cube().data)
    b.faces.ensure_lookup_table()
    loops = b.faces[0].loops
    for lo in (loops[0], loops[2]):                   # two opposite edges of one face
        lo.edge.select = True
    b.select_flush_mode()
    bmesh.update_edit_mesh(cube().data)
    C["n0"] = counts()
    edge_loops = import_module(MODULE + ".operators.edge_loops")
    edge_loops.reset_settings(edge_loops.settings(bpy.context), 'CONNECT')
    dock_area('MODELING_TOOLKIT')


@step
def s_redraw():
    redraw()


step(find_button(dock, lambda path, cmd: "Mesh Tools/Connect" in cmd, C, "connect", x_frac=.25, step_px=6))


@step
def s_hover_button():
    check(f"Modeling Toolkit Connect button found ({C.get('connect')})", C.get("connect") is not None)
    if C.get("connect"):
        ev('MOUSEMOVE', 'NOTHING', x=C["connect"][0], y=C["connect"][1])


@step
def s_click_button():
    if C.get("connect"):
        x, y = C["connect"]
        ev('LEFTMOUSE', 'PRESS', x=x, y=y)
        ev('LEFTMOUSE', 'RELEASE', x=x, y=y)


@step
def s_entered():
    n0, n = C["n0"], counts()
    check(f"Connect button enters the Connect Tool ({tool_id()})", tool_id() == "allset.connect_tool")
    check(f"... and connects the two edges with one edge ({n0} -> {n})", n == (n0[0] + 2, n0[1] + 3, n0[2] + 1))
    redraw()


@step
def s_scroll():
    r = dock_region()                                 # the Connect Options sit below the Tools section
    for _ in range(10):
        ev('WHEELDOWNMOUSE', 'PRESS', x=r.x + r.width // 2, y=r.y + r.height // 2)
    redraw()


@step
def s_redraw2():
    redraw()
    if os.environ.get("ALLSET_GUI_SHOTS"):
        screenshot(os.path.join(os.environ["ALLSET_GUI_SHOTS"], "gui_issue421_options.png"))


step(find_button(dock, lambda path, cmd: path.endswith("allset_loop_tools.ct_segments"), C, "segments",
                 x_frac=.7, step_px=4))


@step
def s_hover_field():
    check(f"Connect Options in the Modeling Toolkit: Segments field found ({C.get('segments')})",
          C.get("segments") is not None)
    if C.get("segments"):
        ev('MOUSEMOVE', 'NOTHING', x=C["segments"][0], y=C["segments"][1])


@step
def s_click_field():
    if C.get("segments"):
        x, y = C["segments"]
        ev('LEFTMOUSE', 'PRESS', x=x, y=y)
        ev('LEFTMOUSE', 'RELEASE', x=x, y=y)


@step
def s_type():
    ev('A', 'PRESS', ctrl=True)
    ev('A', 'RELEASE', ctrl=True)
    ev('TEXTINPUT', 'PRESS', unicode="5")
    tap('RET')


@step
def s_five():
    n0, n = C["n0"], counts()
    s = import_module(MODULE + ".operators.edge_loops").settings(bpy.context)
    check(f"Segments 5 typed in (got {s.ct_segments}) re-does the connection with five edges ({n0} -> {n})",
          s.ct_segments == 5 and n == (n0[0] + 10, n0[1] + 15, n0[2] + 5))
    ev('MOUSEMOVE', 'NOTHING', x=view3d()[1].x + 50, y=view3d()[1].y + 50)
    ev('Z', 'PRESS', ctrl=True)
    ev('Z', 'RELEASE', ctrl=True)


@step
def s_undo():
    n0 = C["n0"]
    ok = bpy.context.mode == 'EDIT_MESH'
    n = counts() if ok else None
    check(f"Ctrl+Z goes back to the one-edge connection ({bpy.context.mode}, {n})",
          ok and n == (n0[0] + 2, n0[1] + 3, n0[2] + 1))
    import_module(MODULE + ".operators.edge_loops").reset_settings(
        import_module(MODULE + ".operators.edge_loops").settings(bpy.context), 'CONNECT')


run()
