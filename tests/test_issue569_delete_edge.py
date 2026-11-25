"""#569 Edit Mesh > Delete Edge/Vertex (allset.delete_edge_vertex, Ctrl+Delete) on edges.

Edges go one at a time; each end vertex left with two edges, whose faces all keep four or more corners, is cleaned
up. Two parallel edges of one cube face leave both side faces (one corner cleaned on each) instead of removing them.
Border edges stay and stay selected; vertex mode deletes the vertices with their edges.
"""

import bmesh
import bpy

import kit


def _mesh(add, mode='EDGE', **kw):
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    add(**kw)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type=mode)
    bpy.ops.mesh.select_all(action='DESELECT')
    ob = bpy.context.active_object
    return ob, bmesh.from_edit_mesh(ob.data)


def _pick(ob, elems):
    for el in elems:
        el.select = True
    bmesh.update_edit_mesh(ob.data)


def _state(ob):
    bm = bmesh.from_edit_mesh(ob.data)
    return len(bm.verts), sorted(len(f.verts) for f in bm.faces)


def _top_face(bm):
    return max(bm.faces, key=lambda f: f.calc_center_median().z)


def test_menu_and_keys_use_the_kit_operator():
    from importlib import import_module
    menu_map = import_module(kit.MODULE + ".ui.menu_map")
    assert menu_map.MAP["Edit Mesh/Delete Edge/Vertex"] == "allset.delete_edge_vertex"
    km = kit.maya_kc().keymaps["Mesh"]
    for key in ('DEL', 'BACK_SPACE'):
        ctrl = [k.idname for k in km.keymap_items if k.active and k.type == key and k.ctrl]
        assert ctrl == ["allset.delete_edge_vertex"], (key, ctrl)


def test_one_edge_cleans_both_ends():
    ob, bm = _mesh(bpy.ops.mesh.primitive_cube_add)
    _pick(ob, [_top_face(bm).edges[0]])
    assert bpy.ops.allset.delete_edge_vertex() == {'FINISHED'}
    assert _state(ob) == (6, [3, 3, 4, 4, 4]), _state(ob)


def test_two_parallel_edges_keep_the_side_faces():
    ob, bm = _mesh(bpy.ops.mesh.primitive_cube_add)
    top = _top_face(bm)
    e0 = top.edges[0]
    e1 = next(e for e in top.edges if not set(e.verts) & set(e0.verts))
    _pick(ob, [e0, e1])
    assert bpy.ops.allset.delete_edge_vertex() == {'FINISHED'}
    assert _state(ob) == (6, [3, 3, 4, 6]), _state(ob)
    assert not any(e.select for e in bmesh.from_edit_mesh(ob.data).edges)


def test_two_edges_at_one_corner():
    ob, bm = _mesh(bpy.ops.mesh.primitive_cube_add)
    top = _top_face(bm)
    e0 = top.edges[0]
    e1 = next(e for e in top.edges if e is not e0 and set(e.verts) & set(e0.verts))
    _pick(ob, [e0, e1])
    assert bpy.ops.allset.delete_edge_vertex() == {'FINISHED'}
    # the result follows the edge numbers (which edge goes first, which joined edge carries on); with the cube
    # primitive's numbering the corner collapses to four triangles
    assert _state(ob) == (4, [3, 3, 3, 3]), _state(ob)


def test_border_edge_stays_selected():
    ob, bm = _mesh(bpy.ops.mesh.primitive_grid_add, x_subdivisions=4, y_subdivisions=4)
    border = next(e for e in bm.edges if e.is_boundary)
    inner = next(e for e in bm.edges if not e.is_boundary and not any(v.is_boundary for v in e.verts))
    ends = [tuple(v.co) for v in border.verts]
    nv = len(bm.verts)
    _pick(ob, [border, inner])
    assert bpy.ops.allset.delete_edge_vertex() == {'FINISHED'}
    bm = bmesh.from_edit_mesh(ob.data)
    sel = [e for e in bm.edges if e.select]
    assert len(sel) == 1 and sel[0].is_boundary, sel
    assert sorted(tuple(v.co) for v in sel[0].verts) == sorted(ends)
    assert len(bm.verts) == nv           # an inner edge between four-edge vertices leaves no two-edge vertex


def test_vertex_mode_deletes_vertices():
    ob, bm = _mesh(bpy.ops.mesh.primitive_grid_add, mode='VERT', x_subdivisions=4, y_subdivisions=4)
    nv = len(bm.verts)
    _pick(ob, [next(v for v in bm.verts if len(v.link_edges) == 4)])
    assert bpy.ops.allset.delete_edge_vertex() == {'FINISHED'}
    assert len(bmesh.from_edit_mesh(ob.data).verts) == nv - 1


def test_nothing_selected_cancels():
    ob, bm = _mesh(bpy.ops.mesh.primitive_cube_add)
    assert bpy.ops.allset.delete_edge_vertex() == {'CANCELLED'}
    assert _state(ob) == (8, [4] * 6)

