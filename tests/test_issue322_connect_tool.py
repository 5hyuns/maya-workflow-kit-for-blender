"""Mesh Tools > Connect is a tool like Maya's Connect Tool: entering it connects the selection, then clicks on
vertices / edges join them one after another, Ctrl+click connects an edge ring (issue #322)."""

from importlib import import_module

import bmesh
import bpy

import kit

connect_tool = import_module(kit.MODULE + ".operators.connect_tool")
menu_map = import_module(kit.MODULE + ".ui.menu_map")


def _grid(cuts=2):
    """A plane of (cuts + 1)^2 quads in object mode, active and selected."""
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=cuts + 1, y_subdivisions=cuts + 1, size=2)
    return bpy.context.active_object


def _edge(bm, a, b):
    """The edge between the vertices nearest to points ``a`` and ``b`` (x, y)."""
    def near(p):
        return min(bm.verts, key=lambda v: (v.co.x - p[0]) ** 2 + (v.co.y - p[1]) ** 2)
    va, vb = near(a), near(b)
    return next(e for e in va.link_edges if e.other_vert(va) is vb)


def test_menu_entry_is_the_tool():
    assert menu_map.MAP["Mesh Tools/Connect"] == "allset.connect_tool_enter"
    assert menu_map.MAP["Edit Mesh/Connect"] == "allset.connect"


def test_enter_from_object_mode_and_click_path():
    ob = _grid(1)                       # 2 x 2 quads, vertices at -1, 0, 1
    assert bpy.ops.allset.connect_tool_enter() == {'FINISHED'}
    assert bpy.context.mode == 'EDIT_MESH', "the tool starts in component mode"
    bm = bmesh.from_edit_mesh(ob.data)
    faces = len(bm.faces)
    left = _edge(bm, (-1, -1), (-1, 0)).index        # the left border edge of the lower-left quad
    mid = _edge(bm, (0, -1), (0, 0)).index           # its right edge (shared with the lower-right quad)
    right = _edge(bm, (1, -1), (1, 0)).index
    # first click: starts the path, nothing changes yet
    assert bpy.ops.allset.connect_click(object=ob.name, kind='EDGE', index=left) == {'FINISHED'}
    bm = bmesh.from_edit_mesh(ob.data)
    assert len(bm.faces) == faces
    # second click on the same face: both edges are cut in the middle and joined
    assert bpy.ops.allset.connect_click(object=ob.name, kind='EDGE', index=mid) == {'FINISHED'}
    bm = bmesh.from_edit_mesh(ob.data)
    assert len(bm.faces) == faces + 1, len(bm.faces)
    new = [e for e in bm.edges if e.select]
    assert len(new) == 1 and all(abs(v.co.y + 0.5) < 1e-6 for v in new[0].verts), [tuple(v.co) for v in new[0].verts]
    # third click continues the path from the last point into the next quad
    bm.edges.ensure_lookup_table()
    right = _edge(bm, (1, -1), (1, 0)).index
    assert bpy.ops.allset.connect_click(object=ob.name, kind='EDGE', index=right) == {'FINISHED'}
    bm = bmesh.from_edit_mesh(ob.data)
    assert len(bm.faces) == faces + 2, len(bm.faces)
    ys = sorted(round(v.co.y, 4) for v in bm.verts if abs(v.co.y + 0.5) < 1e-6)
    assert len(ys) == 3, ys
    bpy.ops.object.mode_set(mode='OBJECT')


def test_vertex_to_vertex_and_new_path():
    ob = _grid(1)
    bpy.ops.object.mode_set(mode='EDIT')
    connect_tool.end_path()
    bm = bmesh.from_edit_mesh(ob.data)
    faces = len(bm.faces)
    corner = min(bm.verts, key=lambda v: (v.co.x + 1) ** 2 + (v.co.y + 1) ** 2).index    # (-1, -1)
    centre = min(bm.verts, key=lambda v: v.co.x ** 2 + v.co.y ** 2).index                 # (0, 0)
    far = min(bm.verts, key=lambda v: (v.co.x - 1) ** 2 + (v.co.y - 1) ** 2).index       # (1, 1)
    bpy.ops.allset.connect_click(object=ob.name, kind='VERT', index=corner)
    bpy.ops.allset.connect_click(object=ob.name, kind='VERT', index=centre)   # diagonal of the lower-left quad
    bm = bmesh.from_edit_mesh(ob.data)
    assert len(bm.faces) == faces + 1
    bpy.ops.allset.connect_click(object=ob.name, kind='VERT', index=far)      # diagonal of the upper-right quad
    bm = bmesh.from_edit_mesh(ob.data)
    assert len(bm.faces) == faces + 2
    # Enter ends the path: the next click starts a new one and changes nothing
    assert connect_tool.end_path()
    bpy.ops.allset.connect_click(object=ob.name, kind='VERT', index=corner)
    bm = bmesh.from_edit_mesh(ob.data)
    assert len(bm.faces) == faces + 2
    bpy.ops.object.mode_set(mode='OBJECT')


def test_ctrl_click_ring_and_selection_on_enter():
    ob = _grid(1)
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(ob.data)
    edges = len(bm.edges)
    e = _edge(bm, (-1, -1), (0, -1)).index      # a bottom edge: its ring runs up through two quads
    assert bpy.ops.allset.connect_click(object=ob.name, kind='EDGE', index=e, ring=True) == {'FINISHED'}
    bm = bmesh.from_edit_mesh(ob.data)
    assert len([x for x in bm.edges if x.select]) == 2, "a new loop of two edges"
    assert len(bm.edges) == edges + 2 + 3, len(bm.edges)
    bpy.ops.object.mode_set(mode='OBJECT')
    # components selected before the tool are connected when it starts (Slide / Segments of the option window)
    ob = _grid(0)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='EDGE')
    bm = bmesh.from_edit_mesh(ob.data)
    for x in bm.edges:
        x.select = abs(x.verts[0].co.x - x.verts[1].co.x) < 1e-6      # the two edges along Y
    bm.select_flush_mode()
    bmesh.update_edit_mesh(ob.data)
    assert bpy.ops.allset.connect_tool_enter(segments=2) == {'FINISHED'}
    bm = bmesh.from_edit_mesh(ob.data)
    assert sorted({round(v.co.y, 4) for v in bm.verts}) == [-1.0, -0.3333, 0.3333, 1.0]
    bpy.ops.object.mode_set(mode='OBJECT')
