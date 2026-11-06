"""#321: Edit Mesh > Extrude on edges works like Maya: Keep Faces Together is on, so connected edges share their new
vertices; Offset moves a border edge out of its face (whatever its vertex order), mitred at a corner, and an edge
between two faces gets no Offset; Local Translate Z / Thickness go along the face normals."""

from importlib import import_module

import bmesh
import bpy
from mathutils import Vector

import kit

ex = import_module(kit.MODULE + ".operators.extrude")


def _grid():
    """A 2 x 2 grid of quads from -1 to 1 in the XY plane, normals +Z."""
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=2, y_segments=2, size=1.0)
    bm.normal_update()
    return bm


def _edges(bm, pred):
    return [e for e in bm.edges if all(pred(v.co) for v in e.verts)]


def _front(co):         # the border edge y = -1, x from -1 to 0
    return abs(co.y + 1) < 1e-6 and co.x < 0.5


def _left(co):          # the border edge x = -1, y from -1 to 0
    return abs(co.x + 1) < 1e-6 and co.y < 0.5


def _new_points(bm, n_before):
    return sorted(tuple(round(c, 5) for c in v.co) for v in bm.verts[n_before:])


def _run(bm, edges, **params):
    n = len(bm.verts)
    ex.extrude_edges(bm, edges, **params)
    bm.verts.ensure_lookup_table()
    return (len(bm.verts), len(bm.edges), len(bm.faces)), _new_points(bm, n)


def test_connected_edges_share_their_corner():
    bm = _grid()
    counts, pts = _run(bm, _edges(bm, _front) + _edges(bm, _left), local_translate_z=1.0)
    assert counts == (12, 17, 6), counts
    assert pts == [(-1.0, -1.0, 1.0), (-1.0, 0.0, 1.0), (0.0, -1.0, 1.0)], pts
    bm.free()
    bm = _grid()
    counts, _pts = _run(bm, _edges(bm, _front) + _edges(bm, _left), local_translate_z=1.0, keep_faces_together=False)
    assert counts == (13, 18, 6), counts
    bm.free()


def test_offset_goes_out_of_the_face():
    for pred, want in ((_front, [(-1.0, -1.5, 0.0), (0.0, -1.5, 0.0)]), (_left, [(-1.5, -1.0, 0.0), (-1.5, 0.0, 0.0)])):
        for flip in (False, True):
            bm = _grid()
            if flip:            # the vertex order of the edge must not matter
                bmesh.ops.reverse_faces(bm, faces=list(bm.faces))
                bm.normal_update()
            _counts, pts = _run(bm, _edges(bm, pred), offset=0.5)
            assert pts == want, (pred.__name__, flip, pts)
            bm.free()


def test_offset_mitres_a_corner():
    bm = _grid()
    _counts, pts = _run(bm, _edges(bm, _front) + _edges(bm, _left), offset=0.5)
    assert pts == [(-1.5, -1.5, 0.0), (-1.5, 0.0, 0.0), (0.0, -1.5, 0.0)], pts
    bm.free()
    # a sharper corner: each edge still moves out by the offset (mitre)
    bm = _grid()
    corner = next(v for v in bm.verts if (v.co - Vector((-1, -1, 0))).length < 1e-6)
    corner.co.x = -1.5
    bm.normal_update()
    left = [e for e in corner.link_edges if (e.other_vert(corner).co - Vector((-1, 0, 0))).length < 1e-6]
    _counts, pts = _run(bm, _edges(bm, _front) + left, offset=0.5)
    assert pts == [(-2.30902, -1.5, 0.0), (-1.44721, 0.22361, 0.0), (0.0, -1.5, 0.0)], pts
    bm.free()


def test_edge_between_two_faces_gets_no_offset():
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=2.0)
    bm.normal_update()
    top_front = _edges(bm, lambda co: abs(co.z - 1) < 1e-6 and abs(co.y + 1) < 1e-6)
    _counts, pts = _run(bm, top_front, offset=0.5)
    assert pts == [(-1.0, -1.0, 1.0), (1.0, -1.0, 1.0)], pts
    bm.free()
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=2.0)
    bm.normal_update()
    top_front = _edges(bm, lambda co: abs(co.z - 1) < 1e-6 and abs(co.y + 1) < 1e-6)
    _counts, pts = _run(bm, top_front, local_translate_z=1.0)
    h = round(1 + 0.5 ** 0.5, 5)
    assert pts == [(-1.0, -h, h), (1.0, -h, h)], pts      # along the mean of the two face normals
    bm.free()


def test_cube_top_loop_stays_connected():
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=2.0)
    bm.normal_update()
    counts, pts = _run(bm, _edges(bm, lambda co: abs(co.z - 1) < 1e-6), local_translate_z=0.5)
    assert counts == (12, 20, 10), counts
    # a corner takes the mean of its two edges' directions
    c = round(1 + 0.5 * 0.5 * 0.5 ** 0.5, 5)
    assert (c, c, round(1 + 0.5 * 0.5 ** 0.5, 5)) in pts, pts
    bm.free()


def test_operator_records_keep_faces_together():
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    ex.clear()
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=2, y_subdivisions=2, size=2.0)
    ob = bpy.context.active_object
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.tool_settings.mesh_select_mode = (False, True, False)
    bm = bmesh.from_edit_mesh(ob.data)
    ex.deselect_all(bm)
    for e in _edges(bm, _front) + _edges(bm, _left):
        e.select_set(True)
    bm.select_flush_mode()
    bmesh.update_edit_mesh(ob.data)
    assert bpy.ops.allset.extrude() == {'FINISHED'}
    _o, rec = ex.active(bpy.context)
    assert rec.spec is ex.EDGE and rec.params["keep_faces_together"] is True, rec.params
    assert len(bmesh.from_edit_mesh(ob.data).verts) == 12
    assert ex.set_params(bpy.context, keep_faces_together=False) == {'FINISHED'}
    assert len(bmesh.from_edit_mesh(ob.data).verts) == 13
    assert ex.set_params(bpy.context, keep_faces_together=True, offset=0.5) == {'FINISHED'}
    pts = sorted(tuple(round(c, 4) for c in v.co) for v in bmesh.from_edit_mesh(ob.data).verts if abs(v.co.x) > 1.2
                 or abs(v.co.y) > 1.2)
    assert pts == [(-1.5, -1.5, 0.0), (-1.5, 0.0, 0.0), (0.0, -1.5, 0.0)], pts
