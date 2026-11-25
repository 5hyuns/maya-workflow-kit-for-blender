"""In a real UI: F11 (faces) -> select all -> Delete removes every face, no menu;
F10 (edges) + Backspace dissolves an edge and keeps its vertices, like Maya (#565); Ctrl+Backspace (Edit Mesh >
Delete Edge/Vertex) on two parallel edges of one face keeps both side faces (#569); Delete in object mode still
deletes the object."""

import os
import sys

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, ev, run, step, setup, screenshot, tap, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def shot(name):
    if SHOTS:
        screenshot(os.path.join(SHOTS, name))


def counts(ob):
    if ob.mode == 'EDIT':
        bm = bmesh.from_edit_mesh(ob.data)
        return len(bm.verts), len(bm.edges), len(bm.faces)
    return len(ob.data.vertices), len(ob.data.edges), len(ob.data.polygons)


def centre():
    ev('MOUSEMOVE', 'NOTHING', x=C["x"], y=C["y"])


def v3d_override():
    area, region = view3d()
    return bpy.context.temp_override(window=win(), area=area, region=region)


@step
def s_setup():
    C["x"], C["y"] = setup()
    cube = bpy.data.objects["Cube"]
    for o in bpy.context.view_layer.objects:
        o.select_set(o is cube)
    bpy.context.view_layer.objects.active = cube
    centre()
    tap('F11')


@step
def s_faces():
    check(f"F11 -> face mode ({bpy.context.mode}, {tuple(bpy.context.tool_settings.mesh_select_mode)})",
          bpy.context.mode == 'EDIT_MESH' and tuple(bpy.context.tool_settings.mesh_select_mode) == (False, False, True))
    centre()
    ev('A', 'PRESS', ctrl=True, shift=True)
    ev('A', 'RELEASE', ctrl=True, shift=True)


@step
def s_selected():
    bm = bmesh.from_edit_mesh(bpy.data.objects["Cube"].data)
    check("Ctrl+Shift+A selects all faces", all(f.select for f in bm.faces))
    centre()
    tap('DEL')


@step
def s_deleted():
    ob = bpy.data.objects["Cube"]
    check(f"Delete removes every face right away, no menu (counts {counts(ob)})", counts(ob) == (0, 0, 0))
    shot("gui_step24_deleted.png")
    with v3d_override():
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.mesh.primitive_cube_add()
    C["ob"] = bpy.context.view_layer.objects.active.name
    centre()
    tap('F10')


@step
def s_edge_mode():
    ob = bpy.data.objects[C["ob"]]
    with v3d_override():
        bpy.ops.mesh.select_all(action='DESELECT')
    bm = bmesh.from_edit_mesh(ob.data)
    bm.edges.ensure_lookup_table()
    bm.edges[0].select = True
    bm.select_flush_mode()
    bmesh.update_edit_mesh(ob.data)
    check(f"F10 -> edge mode ({tuple(bpy.context.tool_settings.mesh_select_mode)})",
          tuple(bpy.context.tool_settings.mesh_select_mode) == (False, True, False))
    centre()
    tap('BACK_SPACE')


@step
def s_edge_deleted():
    ob = bpy.data.objects[C["ob"]]
    check(f"Backspace dissolves the edge, its vertices stay (counts {counts(ob)})",
          counts(ob) == (8, 11, 5))
    with v3d_override():
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.mesh.primitive_cube_add(location=(3, 0, 0))
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='EDGE')
        bpy.ops.mesh.select_all(action='DESELECT')
    ob = bpy.context.view_layer.objects.active
    C["ob"] = ob.name
    bm = bmesh.from_edit_mesh(ob.data)
    top = max(bm.faces, key=lambda f: f.calc_center_median().z)
    e0 = top.edges[0]
    e1 = next(e for e in top.edges if not set(e.verts) & set(e0.verts))
    e0.select = e1.select = True
    bm.select_flush_mode()
    bmesh.update_edit_mesh(ob.data)
    centre()
    ev('BACK_SPACE', 'PRESS', ctrl=True)
    ev('BACK_SPACE', 'RELEASE', ctrl=True)


@step
def s_delete_edge_vertex():
    ob = bpy.data.objects[C["ob"]]
    bm = bmesh.from_edit_mesh(ob.data)
    sizes = sorted(len(f.verts) for f in bm.faces)
    check(f"Ctrl+Backspace deletes both edges and keeps the side faces ({len(bm.verts)} points, faces {sizes})",
          len(bm.verts) == 6 and sizes == [3, 3, 4, 6])
    tap('F8')


@step
def s_object_mode():
    check(f"F8 -> object mode ({bpy.context.mode})", bpy.context.mode == 'OBJECT')
    C["n"] = len(bpy.data.objects)
    centre()
    tap('DEL')


@step
def s_object_deleted():
    check(f"Delete in object mode still deletes the object ({C['n']} -> {len(bpy.data.objects)})",
          len(bpy.data.objects) == C["n"] - 1 and C["ob"] not in bpy.data.objects)


run()
