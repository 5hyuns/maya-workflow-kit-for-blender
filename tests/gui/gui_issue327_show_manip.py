"""Issue #327: T = Show Manipulator Tool with real key events.

Edit mode: face -> Ctrl+E -> W (Move manipulator) -> T brings back the extrude manipulator and In-View Editor, with no
error report (T used to cycle Blender's tools and stop on an empty entry of the extrude tool group). Object mode: T
shows the last extrusion's manipulator and In-View Editor and stays in object mode; W ends it. A polyCube: T shows the
polyCube1 In-View Editor in object mode, dragging its Width row rebuilds the cube (one undo step). No history: T = the
Transform tool.
"""

import os
import sys
from importlib import import_module

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, px, run, setup, step, tap, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def mod(name):
    return import_module(MODULE + name)


def shot(name):
    if SHOTS:
        with bpy.context.temp_override(window=win()):
            bpy.ops.screen.screenshot(filepath=os.path.join(SHOTS, name))


def cube():
    return bpy.data.objects["Cube"]


def v3d_ctx():
    area, region = view3d()
    return bpy.context.temp_override(window=win(), area=area, region=region, space_data=area.spaces.active)


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


def shown():
    with v3d_ctx():
        return mod(".ui.in_view").manip_visible(bpy.context)


def tool():
    t = bpy.context.workspace.tools.from_space_view3d_mode(bpy.context.mode, create=False)
    return t.idname if t else None


def errors():
    return [r for r in getattr(bpy.context.window_manager, "reports", ()) if 'ERROR' in r.type]


@step
def s_setup():
    C["x"], C["y"] = setup()
    bpy.ops.allset.keymap_activate()
    bpy.context.preferences.view.show_tooltips = False


@step
def s_edit():
    ev('MOUSEMOVE', 'NOTHING', x=C["x"], y=C["y"])
    for o in bpy.context.view_layer.objects:
        o.select_set(o.name == "Cube")
    bpy.context.view_layer.objects.active = cube()
    with v3d_ctx():
        bpy.ops.object.mode_set('EXEC_DEFAULT', True, mode='EDIT')
    bpy.context.scene.tool_settings.mesh_select_mode = (False, False, True)
    bm = bmesh.from_edit_mesh(cube().data)
    for f in bm.faces:
        f.select_set(f.normal.z > 0.9)
    bm.select_flush_mode()
    bmesh.update_edit_mesh(cube().data)
    redraw()


@step
def s_ctrl_e():
    ev('E', 'PRESS', ctrl=True)
    ev('E', 'RELEASE', ctrl=True)


@step
def s_extruded():
    check(f"#327 Ctrl+E: extrude manipulator shown ({shown()})", shown())
    tap('W')


@step
def s_w():
    check(f"#327 W: extrude manipulator hidden ({shown()})", not shown())
    C["errors"] = len(errors())
    tap('T')


@step
def s_t_edit():
    redraw()
    shot("327_t_edit.png")
    check(f"#327 T in edit mode: extrude manipulator + In-View Editor back ({shown()})", shown())
    check(f"#327 T in edit mode: no error report ({len(errors())} vs {C['errors']})", len(errors()) == C["errors"])
    with v3d_ctx():
        bpy.ops.object.mode_set(mode='OBJECT')
    for p in cube().data.polygons:
        p.select = False
    with v3d_ctx():
        bpy.ops.ed.undo_push(message="Toggle Edit Mode")      # what Tab leaves on the undo stack
    redraw()


@step
def s_t_object():
    tap('T')


@step
def s_t_object_done():
    redraw()
    shot("327_t_object.png")
    with v3d_ctx():
        rec = mod(".ui.in_view").record(bpy.context)[1]
        arrow = mod(".ui.in_view").arrow_visible(bpy.context)
    check(f"#327 T in object mode: stays in object mode and shows the last extrusion ({bpy.context.mode}, "
          f"{rec and rec.name}, manipulator {arrow})",
          bpy.context.mode == 'OBJECT' and rec is not None and rec.name.startswith("polyExtrudeFace") and arrow)
    check(f"#327 T in object mode: no error report ({len(errors())} vs {C['errors']})", len(errors()) == C["errors"])
    x, y, d = arrow_point()
    C["arrow"] = (x, y, d)
    C["z0"] = top_z()
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    redraw()


def top_z():
    return max(v.co.z for v in cube().data.vertices)


def arrow_point():
    """A window point on the blue arrow's shaft (a bit out from the faces' centre along the normal)."""
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
def s_arrow_press():
    x, y, _d = C["arrow"]
    ev('LEFTMOUSE', 'PRESS', x=x, y=y)


@step
def s_arrow_drag():
    x, y, d = C["arrow"]
    for i in range(1, 9):
        ev('MOUSEMOVE', 'NOTHING', x=x + round(d.x * px(60) * i / 8), y=y + round(d.y * px(60) * i / 8))


@step
def s_arrow_release():
    x, y, d = C["arrow"]
    ev('LEFTMOUSE', 'RELEASE', x=x + round(d.x * px(60)), y=y + round(d.y * px(60)))


@step
def s_arrow_done():
    with v3d_ctx():
        rec = mod(".ui.in_view").record(bpy.context)[1]
    ltz = rec.params["local_translate_z"] if rec else None
    check(f"#327 object mode: drag the blue arrow out -> Local Translate Z > 0, faces up, still object mode "
          f"(ltz {ltz}, z {C['z0']:.3f} -> {top_z():.3f}, {bpy.context.mode})",
          rec is not None and ltz > 0.05 and top_z() > C["z0"] + 0.05 and bpy.context.mode == 'OBJECT')
    C["z1"] = top_z()
    ev('Z', 'PRESS', ctrl=True)
    ev('Z', 'RELEASE', ctrl=True)


@step
def s_arrow_undo():
    check(f"#327 Ctrl+Z after the object-mode arrow drag: faces back in one step (z {C['z1']:.3f} -> {top_z():.3f})",
          abs(top_z() - C["z0"]) < 1e-4 and bpy.context.mode == 'OBJECT')
    tap('W')


@step
def s_w_object():
    redraw()
    check(f"#327 W after T in object mode: In-View Editor gone ({shown()})", not shown())
    with v3d_ctx():
        for o in list(bpy.data.objects):
            o.select_set(False)
        C["pcube"] = mod(".operators.prim_history").create_object(bpy.context, 'CUBE').name
        bpy.ops.ed.undo_push(message="polyCube")
    redraw()


@step
def s_t_polycube():
    tap('T')


def in_view_rows():
    """Window positions of the In-View rows' centres (the box layout of this view)."""
    _area, region = view3d()
    with v3d_ctx():
        _r, lay = mod(".ui.in_view").current_layout(bpy.context)
    if lay is None:
        return None
    return {f: (region.x + round((x0 + x1) / 2), region.y + round((y0 + y1) / 2)) for f, x0, y0, x1, y1 in lay["rows"]}


def width():
    ob = bpy.data.objects.get(C["pcube"])      # by name: an undo reloads the data
    return mod(".operators.prim_history").attrs(ob.data).get("width") if ob is not None else None


@step
def s_t_polycube_done():
    redraw()
    shot("327_t_polycube.png")
    with v3d_ctx():
        node = mod(".ui.in_view").record(bpy.context)[1]
        arrow = mod(".ui.in_view").arrow_visible(bpy.context)
    rows = node.spec.view_fields if node is not None else ()
    check(f"#327 T on a polyCube: polyCube1 In-View Editor in object mode, no manipulator ({bpy.context.mode}, "
          f"{node and node.name}, {rows}, {arrow})",
          bpy.context.mode == 'OBJECT' and node is not None and node.name == "polyCube1"
          and rows[:3] == ("width", "height", "depth") and len(rows) == 6 and not arrow)
    C["rows"] = in_view_rows()
    check(f"#327 polyCube1 In-View rows on screen ({C['rows'] and list(C['rows'])})", C["rows"] is not None)
    if C["rows"]:
        x, y = C["rows"]["width"]
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y)


@step
def s_press_width():
    redraw()
    x, y = C["rows"]["width"]
    ev('LEFTMOUSE', 'PRESS', x=x, y=y)


@step
def s_drag_width():
    x, y = C["rows"]["width"]
    d = round(50 * bpy.context.preferences.system.ui_scale)     # 0.01 Maya unit per px at scale 1 -> +0.5
    C["d"] = d
    for i in range(1, 9):
        ev('MOUSEMOVE', 'NOTHING', x=x + d * i // 8, y=y)


@step
def s_release_width():
    x, y = C["rows"]["width"]
    ev('LEFTMOUSE', 'RELEASE', x=x + C["d"], y=y)


@step
def s_width_done():
    w = width()
    sel = [o.name for o in bpy.context.selected_objects]
    check(f"#327 polyCube1 Width drag in object mode -> 1.5 (got {w}, {bpy.context.mode}, selected {sel})",
          w is not None and abs(w - 1.5) < 0.02 and bpy.context.mode == 'OBJECT' and sel == [C["pcube"]])
    ev('Z', 'PRESS', ctrl=True)
    ev('Z', 'RELEASE', ctrl=True)


@step
def s_width_undo():
    w = width()
    check(f"#327 Ctrl+Z after the Width drag: back to 1 in one step (got {w})", w is not None and abs(w - 1.0) < 1e-6)
    with v3d_ctx():
        bpy.ops.mesh.primitive_plane_add()
    redraw()


@step
def s_t_plain():
    tap('T')


@step
def s_t_plain_done():
    check(f"#327 T without history: the Transform tool ({bpy.context.mode}, {tool()})",
          bpy.context.mode == 'OBJECT' and tool() == "builtin.transform")


run()
