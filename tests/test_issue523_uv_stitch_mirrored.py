"""#523: Stitch Together on a mirrored shell, and which shell Move and Sew moves when both have as many faces.

Like Maya: when the two shells have the same number of faces, Move and Sew moves the shell on the side of the edge
whose face runs along the edge's own direction (first vertex to second). Stitch Together sews with Move and Sew after
lining the shells up, so a mirrored shell (its edge copy runs the other way) ends up folded onto the other shell the
same way as in Maya."""

import math

import bmesh
import bpy

import kit  # noqa: F401


def _strip(layouts, edge_from_right=False):
    """Two unit quads side by side (vertices 0 1 2 / 3 4 5, the shared edge 1-4); face i gets the UV corners
    ``layouts[i]``. The shared edge runs 1 -> 4 (the left face's direction) or 4 -> 1 (``edge_from_right``)."""
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    me = bpy.data.meshes.new("strip")
    bm = bmesh.new()
    vs = [bm.verts.new((x, y, 0.0)) for y in (0, 1) for x in range(3)]
    bm.edges.new((vs[4], vs[1]) if edge_from_right else (vs[1], vs[4]))
    uv = bm.loops.layers.uv.new("UVMap")
    for i in range(2):
        f = bm.faces.new((vs[i], vs[i + 1], vs[4 + i], vs[3 + i]))
        for loop, p in zip(f.loops, layouts[i]):
            loop[uv].uv = p
    bm.to_mesh(me)
    ob = bpy.data.objects.new("strip", me)
    bpy.context.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.scene.tool_settings.use_uv_select_sync = True
    bpy.ops.mesh.select_mode(type='EDGE')
    bm = bmesh.from_edit_mesh(ob.data)
    for el in (*bm.verts, *bm.edges, *bm.faces):
        el.select = False
    e = next(e for e in bm.edges if {v.index for v in e.verts} == {1, 4})
    assert [v.index for v in e.verts] == ([4, 1] if edge_from_right else [1, 4])
    e.select = True
    for v in e.verts:
        v.select = True
    bmesh.update_edit_mesh(ob.data)
    return ob


def _face_uvs(ob, i):
    bm = bmesh.from_edit_mesh(ob.data)
    bm.faces.ensure_lookup_table()
    uv = bm.loops.layers.uv.active
    return [tuple(l[uv].uv) for l in bm.faces[i].loops]


def _close(got, want, tol=1e-5):
    assert all(abs(g[0] - w[0]) < tol and abs(g[1] - w[1]) < tol for g, w in zip(got, want)), (got, want)


def _moved(points, deg, k, t, centre=(0.5, 0.5)):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return [(centre[0] + k * (c * (u - centre[0]) - s * (v - centre[1])) + t[0],
             centre[1] + k * (s * (u - centre[0]) + c * (v - centre[1])) + t[1]) for u, v in points]


LEFT = [(0.0, 0.0), (0.5, 0.0), (0.5, 1.0), (0.0, 1.0)]
RIGHT = [(0.5, 0.0), (1.0, 0.0), (1.0, 1.0), (0.5, 1.0)]


def _mirrored_right():
    moved = _moved(RIGHT, 20, 0.7, (0.2, 0.3), centre=(0.75, 0.5))
    mid = 0.95
    return [(2 * mid - u, v) for u, v in moved]


def test_stitch_together_folds_a_mirrored_shell_like_maya():
    ob = _strip([LEFT, _mirrored_right()])
    assert bpy.ops.allset.uv_stitch_together() == {'FINISHED'}
    # the smaller (mirrored) shell lands beside the edge with its ends swapped; the sew then turns the left face,
    # which runs along the edge, half a turn about the edge middle onto it
    _close(_face_uvs(ob, 1), [(0.5, 1.0), (1.0, 1.0), (1.0, 0.0), (0.5, 0.0)])
    _close(_face_uvs(ob, 0), [(1.0, 1.0), (0.5, 1.0), (0.5, 0.0), (1.0, 0.0)])


def test_stitch_together_largest_to_smallest_on_a_mirrored_shell():
    ob = _strip([LEFT, _mirrored_right()])
    assert bpy.ops.allset.opt_uv_stitch_together('EXEC_DEFAULT', order="Largest to Smallest") == {'FINISHED'}
    right, left = _face_uvs(ob, 1), _face_uvs(ob, 0)
    _close(right, _mirrored_right())     # the smaller shell stays
    # both faces end on the same side of the shared edge, which the two copies now share
    _close([left[1], left[2]], [right[0], right[3]])
    side = [((p[0] - right[0][0]) * (right[3][1] - right[0][1]) - (p[1] - right[0][1]) * (right[3][0] - right[0][0]))
            for p in (left[0], right[1])]
    assert side[0] * side[1] > 0, (left, right)


def test_move_and_sew_with_equal_faces_moves_the_face_running_along_the_edge():
    right = _moved(RIGHT, 30, 1.0, (0.3, 0.2), centre=(0.75, 0.5))
    ob = _strip([LEFT, right])
    assert bpy.ops.allset.uv_move_sew() == {'FINISHED'}
    _close(_face_uvs(ob, 1), right)
    _close(_face_uvs(ob, 0), _moved(LEFT, 30, 1.0, (0.3, 0.2), centre=(0.75, 0.5)))
    # the same shells with the edge running the other way: the right face moves back onto the left one
    ob = _strip([LEFT, right], edge_from_right=True)
    assert bpy.ops.allset.uv_move_sew() == {'FINISHED'}
    _close(_face_uvs(ob, 0), LEFT)
    _close(_face_uvs(ob, 1), RIGHT)


def test_move_and_sew_still_moves_the_shell_with_fewer_faces():
    # three quads: faces 1 and 2 share UVs (one shell of two faces); face 0 alone moves even though the edge runs
    # along face 0's direction or not
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    me = bpy.data.meshes.new("strip3")
    bm = bmesh.new()
    vs = [bm.verts.new((x, y, 0.0)) for y in (0, 1) for x in range(4)]
    bm.edges.new((vs[5], vs[1]))
    uv = bm.loops.layers.uv.new("UVMap")
    t = (0.3, 0.2)
    layouts = [[(0.0, 0.0), (1 / 3, 0.0), (1 / 3, 1.0), (0.0, 1.0)],
               _moved([(1 / 3, 0.0), (2 / 3, 0.0), (2 / 3, 1.0), (1 / 3, 1.0)], 30, 1.0, t),
               _moved([(2 / 3, 0.0), (1.0, 0.0), (1.0, 1.0), (2 / 3, 1.0)], 30, 1.0, t)]
    for i in range(3):
        f = bm.faces.new((vs[i], vs[i + 1], vs[5 + i], vs[4 + i]))
        for loop, p in zip(f.loops, layouts[i]):
            loop[uv].uv = p
    bm.to_mesh(me)
    ob = bpy.data.objects.new("strip3", me)
    bpy.context.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.scene.tool_settings.use_uv_select_sync = True
    bpy.ops.mesh.select_mode(type='EDGE')
    bm = bmesh.from_edit_mesh(ob.data)
    for el in (*bm.verts, *bm.edges, *bm.faces):
        el.select = False
    e = next(e for e in bm.edges if {v.index for v in e.verts} == {1, 5})
    e.select = True
    for v in e.verts:
        v.select = True
    bmesh.update_edit_mesh(ob.data)
    assert bpy.ops.allset.uv_move_sew() == {'FINISHED'}
    _close(_face_uvs(ob, 1), layouts[1])
    _close(_face_uvs(ob, 0), _moved(layouts[0], 30, 1.0, t))
