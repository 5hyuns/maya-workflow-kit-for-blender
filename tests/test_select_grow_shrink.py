"""Select > Grow / Shrink follow Maya's rules (GitHub #?): an edge selection grows by the edges that share a vertex
with it (vertices and faces grow across faces), and Shrink also lets go of vertices and faces on the open border of the
mesh."""

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


def test_grow_edges_by_shared_vertex():
    got = _run('EDGE', [(12, 13)], "Select/Grow")
    assert got == [(7, 12), (8, 13), (11, 12), (12, 13), (12, 17), (13, 14), (13, 18)], got


def test_grow_vertices_and_faces_across_faces():
    assert _run('VERT', [12], "Select/Grow") == [6, 7, 8, 11, 12, 13, 16, 17, 18]
    assert _run('FACE', [5], "Select/Grow") == [0, 1, 2, 4, 5, 6, 8, 9, 10]


def test_shrink_lets_go_of_the_mesh_border():
    assert _run('VERT', [0, 1, 2, 5, 6, 7, 10, 11, 12], "Select/Shrink") == [6]
    assert _run('VERT', list(range(25)), "Select/Shrink") == [6, 7, 8, 11, 12, 13, 16, 17, 18]
    assert _run('FACE', [0, 1, 2, 4, 5, 6, 8, 9, 10], "Select/Shrink") == [5]
    assert _run('FACE', list(range(16)), "Select/Shrink") == [5, 6, 9, 10]


def test_shrink_inside_the_mesh_is_unchanged():
    assert _run('VERT', [6, 7, 8, 11, 12, 13, 16, 17, 18], "Select/Shrink") == [12]


def test_keys_and_menu_use_the_maya_rules():
    from importlib import import_module
    menu_map = import_module(kit.MODULE + ".ui.menu_map")
    assert menu_map.MAP["Select/Grow"] == "allset.grow_selection"
    assert menu_map.MAP["Select/Shrink"] == "allset.shrink_selection"
