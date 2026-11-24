"""Issue #532 with real key events: Ctrl+B on a selected object (object mode) bevels every edge of it, stays in object
mode and shows the polyBevel1 In-View Editor; a cube scaled (1, 1, 4) gets the same width on every edge."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, setup, step, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def mod(name):
    return import_module(MODULE + name)


def cube():
    return bpy.data.objects["Cube"]


def v3d_ctx():
    area, region = view3d()
    return bpy.context.temp_override(window=win(), area=area, region=region, space_data=area.spaces.active)


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


@step
def s_setup():
    C["x"], C["y"] = setup()
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for o in bpy.context.view_layer.objects:
        o.select_set(o.name == "Cube")
    bpy.context.view_layer.objects.active = cube()
    cube().scale = (1.0, 1.0, 4.0)
    xs = [v.co.x for v in cube().data.vertices]
    C["side"] = max(xs) - min(xs)
    ev('MOUSEMOVE', 'NOTHING', x=C["x"], y=C["y"])
    ev('B', 'PRESS', ctrl=True)
    ev('B', 'RELEASE', ctrl=True)


@step
def s_bevelled():
    ob = cube()
    check(f"#532 Ctrl+B on the object: still object mode, every edge bevelled ({bpy.context.mode}, "
          f"{len(ob.data.vertices)} verts)", bpy.context.mode == 'OBJECT' and len(ob.data.vertices) == 24)
    half = C["side"] / 2.0
    widths = [max(abs(s) * (half - abs(v.co[a])) for v in ob.data.vertices) for a, s in enumerate(ob.scale)]
    check(f"#532 the same world width on every axis of the scaled cube ({[round(w, 5) for w in widths]})",
          max(widths) - min(widths) < 1e-4)
    redraw()


@step
def s_in_view():
    if SHOTS:
        with bpy.context.temp_override(window=win()):
            bpy.ops.screen.screenshot(filepath=os.path.join(SHOTS, "532_object_bevel.png"))
    with v3d_ctx():
        node = mod(".ui.in_view").record(bpy.context)[1]
        _r, lay = mod(".ui.in_view").current_layout(bpy.context)
    check(f"#532 polyBevel1 In-View Editor in object mode ({node and node.name}, rows {lay and len(lay['rows'])})",
          node is not None and node.name == "polyBevel1" and lay is not None and len(lay["rows"]) > 0)


run()
