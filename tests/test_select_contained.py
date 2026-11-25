"""Select > Convert Selection > To Contained Edges / Faces select what the selection fully holds, like Maya: edges
from faces = only the edges inside the face selection (not its outline, not the open border of the mesh); from
vertices = both ends selected; faces = all vertices (from edges: all edges) selected. When nothing is contained the
selection stays as it was."""

import bmesh
import bpy


def _grid(mode):
    """A 3 x 3 quad grid (vertex i + 4 j at (i, j, 0), face i + 3 j) in edit mode, nothing selected."""
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    verts = [(float(i), float(j), 0.0) for j in range(4) for i in range(4)]
    faces = [(i + 4 * j, i + 1 + 4 * j, i + 5 + 4 * j, i + 4 + 4 * j) for j in range(3) for i in range(3)]
    me = bpy.data.meshes.new("grid")
    me.from_pydata(verts, [], faces)
    ob = bpy.data.objects.new("pPlane1", me)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.tool_settings.mesh_select_mode = (mode == 'VERT', mode == 'EDGE', mode == 'FACE')
    bpy.ops.mesh.select_all(action='DESELECT')
    return ob


def _select(ob, mode, items):
    bm = bmesh.from_edit_mesh(ob.data)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    for it in items:
        if mode == 'VERT':
            bm.verts[it].select = True
        elif mode == 'FACE':
            bm.faces[it].select = True
        else:
            a, b = bm.verts[it[0]], bm.verts[it[1]]
            next(e for e in a.link_edges if e.other_vert(a) is b).select = True
    bm.select_flush_mode()
    bmesh.update_edit_mesh(ob.data)


def _got(ob):
    """(select mode, selection of that mode)."""
    sv, se, sf = bpy.context.tool_settings.mesh_select_mode
    bm = bmesh.from_edit_mesh(ob.data)
    if sf:
        return 'FACE', sorted(f.index for f in bm.faces if f.select)
    if se:
        return 'EDGE', sorted(tuple(sorted(v.index for v in e.verts)) for e in bm.edges if e.select)
    return 'VERT', sorted(v.index for v in bm.verts if v.select)


def _run(mode, items, label, editor=""):
    ob = _grid(mode)
    _select(ob, mode, items)
    path = editor + "Select/Convert Selection/" + label
    assert bpy.ops.allset.menu_item(item=path) == {'FINISHED'}, path
    return _got(ob)


def test_faces_to_contained_edges_leave_out_the_outline():
    # two faces side by side: only the edge they share
    assert _run('FACE', [0, 1], "To Contained Edges") == ('EDGE', [(1, 5)])
    # a 2 x 2 block in the corner: the four edges round the middle vertex, not the mesh border
    assert _run('FACE', [0, 1, 3, 4], "To Contained Edges") == ('EDGE', [(1, 5), (4, 5), (5, 6), (5, 9)])


def test_vertices_and_edges():
    assert _run('VERT', [0, 1, 4, 5], "To Contained Edges") == ('EDGE', [(0, 1), (0, 4), (1, 5), (4, 5)])
    assert _run('VERT', [0, 1, 4, 5], "To Contained Faces") == ('FACE', [0])
    assert _run('EDGE', [(0, 1), (1, 5), (4, 5), (0, 4)], "To Contained Faces") == ('FACE', [0])
    assert _run('EDGE', [(0, 1)], "To Contained Edges") == ('EDGE', [(0, 1)])
    assert _run('FACE', [3, 4], "To Contained Faces") == ('FACE', [3, 4])


def test_nothing_contained_keeps_the_selection():
    assert _run('FACE', [4], "To Contained Edges") == ('FACE', [4])
    assert _run('VERT', [0, 1, 2], "To Contained Faces") == ('VERT', [0, 1, 2])
    assert _run('EDGE', [(0, 1)], "To Contained Faces") == ('EDGE', [(0, 1)])


def test_uv_editor_menu_does_the_same():
    assert _run('FACE', [0, 1], "To Contained Edges", "UV Editor/") == ('EDGE', [(1, 5)])
    assert _run('FACE', [4], "To Contained Edges", "UV Editor/") == ('FACE', [4])

