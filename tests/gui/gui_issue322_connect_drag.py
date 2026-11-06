"""Connect Tool middle-drag in a real UI (issue #322): after two clicks join two edges of a face, a middle-drag to
the right re-does that connection with more Segments (the Tool Settings radio's value, like Maya), Ctrl+middle-drag
does the same, Esc during a drag puts the value back, Enter makes the connection final so a later drag only changes
the value, and the HUD line names the value."""

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


def settings():
    return import_module(MODULE + ".operators.edge_loops").settings(bpy.context)


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


def middle_drag(dx, ctrl=False, cancel=False):
    """Press the middle button in the view's middle, move ``dx`` pixels right, release (or Esc)."""
    area, region = view3d()
    x, y = region.x + region.width // 2, region.y + region.height // 2
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('MIDDLEMOUSE', 'PRESS', x=x, y=y, ctrl=ctrl)
    for k in range(1, 5):
        ev('MOUSEMOVE', 'NOTHING', x=x + dx * k // 4, y=y, ctrl=ctrl)
    if cancel:
        ev('ESC', 'PRESS', x=x + dx, y=y)
        ev('ESC', 'RELEASE', x=x + dx, y=y)
    ev('MIDDLEMOUSE', 'RELEASE', x=x + dx, y=y, ctrl=ctrl)


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
    s = settings()
    s.ct_mode, s.ct_segments, s.ct_slide, s.ct_pinch = 'SEGMENTS', 1, 0.5, 0.0
    menu("Mesh Tools/Connect")


@step
def s_entered():
    check(f"Mesh Tools > Connect = component mode + the kit Connect Tool ({bpy.context.mode}, {tool_id()})",
          bpy.context.mode == 'EDIT_MESH' and tool_id() == ct().TOOL)
    check(f"the HUD names the value the radio picks ({ct().hud_text(settings())})",
          ct().hud_text(settings()) == "Connect Segments: 1")
    with override():
        bpy.ops.mesh.select_all('EXEC_DEFAULT', True, action='DESELECT')
    C["n0"] = counts()
    click((-1.0, -1.0, 0.2))        # the front face's left edge
    click((1.0, -1.0, -0.2))        # the opposite edge of the front face


@step
def s_joined():
    v, e, f = counts()
    v0, e0, f0 = C["n0"]
    check(f"two clicks join the two edges across the face ({(v, e, f)} from {C['n0']})",
          (v, e, f) == (v0 + 2, e0 + 3, f0 + 1))
    middle_drag(60)                 # two segments more


@step
def s_dragged():
    v, e, f = counts()
    v0, e0, f0 = C["n0"]
    s = settings()
    check(f"a middle-drag right sets Segments 3 ({s.ct_segments}) and the HUD says so ({ct().hud_text(s)})",
          s.ct_segments == 3 and ct().hud_text(s) == "Connect Segments: 3")
    check(f"the connection is re-done with three segments ({(v, e, f)})", (v, e, f) == (v0 + 6, e0 + 9, f0 + 3))
    if SHOTS:
        screenshot(os.path.join(SHOTS, "gui_issue322_connect_drag.png"))
    middle_drag(-30, ctrl=True)     # one segment less with Ctrl held


@step
def s_ctrl_dragged():
    v, e, f = counts()
    v0, e0, f0 = C["n0"]
    s = settings()
    check(f"Ctrl+middle-drag left takes one segment away ({s.ct_segments}, {(v, e, f)})",
          s.ct_segments == 2 and (v, e, f) == (v0 + 4, e0 + 6, f0 + 2))
    middle_drag(90, cancel=True)    # Esc during the drag: the value comes back


@step
def s_cancelled():
    v, e, f = counts()
    v0, e0, f0 = C["n0"]
    s = settings()
    check(f"Esc during a middle-drag puts Segments back ({s.ct_segments}, {(v, e, f)})",
          s.ct_segments == 2 and (v, e, f) == (v0 + 4, e0 + 6, f0 + 2))
    ev('MOUSEMOVE', 'NOTHING', x=C["x"], y=C["y"])
    ev('Z', 'PRESS', ctrl=True)
    ev('Z', 'RELEASE', ctrl=True)


@step
def s_undo():
    v, e, f = counts()
    v0, e0, f0 = C["n0"]
    check(f"Ctrl+Z takes back the last drag only ({(v, e, f)})", (v, e, f) == (v0 + 6, e0 + 9, f0 + 3))
    check(f"Ctrl+Z keeps component mode and the tool ({bpy.context.mode}, {tool_id()})",
          bpy.context.mode == 'EDIT_MESH' and tool_id() == ct().TOOL)
    ev('RET', 'PRESS', x=C["x"], y=C["y"])
    ev('RET', 'RELEASE', x=C["x"], y=C["y"])


@step
def s_final():
    check("Enter ends the path and makes the connection final", not ct()._path and not ct()._last)
    C["n1"] = counts()
    settings().ct_mode = 'SLIDE'
    middle_drag(40)                 # Slide 0.5 -> 0.7, the final connection stays


@step
def s_slide_after_enter():
    s = settings()
    check(f"after Enter a middle-drag only changes the value ({s.ct_slide:.2f}, {counts()} = {C['n1']})",
          abs(s.ct_slide - 0.7) < 1e-6 and counts() == C["n1"])
    check(f"the HUD follows the radio ({ct().hud_text(s)})", ct().hud_text(s) == "Connect Slide: 0.7")


if __name__ == "__main__":
    run()
