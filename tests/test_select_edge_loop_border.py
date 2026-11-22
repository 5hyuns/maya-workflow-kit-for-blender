"""Convert Selection > To Edge Loop on an open-border edge takes in the whole border, round the corners, like Maya
(GitHub #?); an inner edge's loop and Contiguous Edges on the border still stop where they did."""

import bmesh
import bpy

import kit


def _grid(mode):
    """A 4 x 4 quad grid (vertex i + 5 j at (i - 2, j - 2, 0), face i + 4 j) in edit mode, nothing selected."""
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    verts = [(i - 2.0, j - 2.0, 0.0) for j in range(5) for i in range(5)]
    faces = [(i + 5 * j, i + 1 + 5 * j, i + 6 + 5 * j, i + 5 + 5 * j) for j in range(4) for i in range(4)]
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


def _got(ob, mode):
    bm = bmesh.from_edit_mesh(ob.data)
    if mode == 'VERT':
        return sorted(v.index for v in bm.verts if v.select)
    if mode == 'FACE':
        return sorted(f.index for f in bm.faces if f.select)
    return sorted(tuple(sorted(v.index for v in e.verts)) for e in bm.edges if e.select)


def _run(mode, items, path):
    ob = _grid(mode)
    _select(ob, mode, items)
    assert bpy.ops.allset.menu_item(item=path) == {'FINISHED'}, path
    return _got(ob, mode)


def test_edge_loop_of_a_border_edge_is_the_whole_border():
    border = sorted({tuple(sorted(p)) for j in (0, 4) for p in ((5 * j + i, 5 * j + i + 1) for i in range(4))}
                    | {tuple(sorted(p)) for i in (0, 4) for p in ((5 * j + i, 5 * j + i + 5) for j in range(4))})
    for start in ((0, 1), (5, 10)):
        got = _run('EDGE', [start], "Select/Convert Selection/To Edge Loop")
        assert got == border, (start, got)


def test_inner_loop_and_contiguous_border_edges_are_unchanged():
    assert _run('EDGE', [(12, 13)], "Select/Convert Selection/To Edge Loop") == [(10, 11), (11, 12), (12, 13),
                                                                                  (13, 14)]
    assert _run('EDGE', [(0, 1)], "Select/Contiguous Edges") == [(0, 1), (1, 2), (2, 3), (3, 4)]
