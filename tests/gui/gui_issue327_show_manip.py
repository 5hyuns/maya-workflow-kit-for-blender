"""Issue #327: T = Show Manipulator Tool with real key events.

Edit mode: face -> Ctrl+E -> W (Move manipulator) -> T brings back the extrude manipulator and In-View Editor, with no
error report (T used to cycle Blender's tools and stop on an empty entry of the extrude tool group). Object mode: T
opens the last extrusion again (edit mode, the extruded faces selected). No history: T = the Transform tool.
"""

import os
import sys
from importlib import import_module

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, setup, step, tap, view3d, win  # noqa: E402

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
    redraw()


@step
def s_t_object():
    tap('T')


@step
def s_t_object_done():
    redraw()
    shot("327_t_object.png")
    check(f"#327 T in object mode: the last extrusion opens in edit mode ({bpy.context.mode}, {shown()})",
          bpy.context.mode == 'EDIT_MESH' and shown())
    with v3d_ctx():
        bpy.ops.object.mode_set(mode='OBJECT')
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
