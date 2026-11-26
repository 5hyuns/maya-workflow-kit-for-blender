"""Duplicate Face with Keep Faces Together (on by default, like Maya): copied faces that share a vertex stay joined at
one copied vertex, which takes the mean of where each of its faces puts it (Offset insets only the outer border of
two side-by-side faces; where two faces meet only at a corner the corner stays). Off: one piece per face. Local
Scale applies before Offset, so Offset stays the same distance in from the scaled edges."""

from importlib import import_module

import bmesh
from mathutils import Vector

import kit

dup = import_module(kit.MODULE + ".operators.duplicate_face")


def _plane(centres):
    """A 4 x 4 plane of unit faces on XZ (normal +Y); the faces with these centres selected."""
    bm = bmesh.new()
    vs = {(i, j): bm.verts.new((i - 2.0, 0.0, j - 2.0)) for i in range(5) for j in range(5)}
    for i in range(4):
        for j in range(4):
            f = bm.faces.new((vs[i, j], vs[i, j + 1], vs[i + 1, j + 1], vs[i + 1, j]))
            f.select = any((f.calc_center_median() - Vector(c)).length < 1e-6 for c in centres)
    bm.normal_update()
    return bm


def _copies(bm):
    return [f for f in bm.faces if f.select]


def _has(points, p):
    return any((q - Vector(p)).length < 1e-6 for q in points)


def test_side_by_side_faces_stay_joined():
    bm = _plane([(-0.5, 0, 0.5), (0.5, 0, 0.5)])
    n = len(bm.verts)
    dup.duplicate(bm, {"offset": 0.1})
    assert len(bm.verts) - n == 6, "two joined quads = 6 new vertices"
    pts = [v.co for f in _copies(bm) for v in f.verts]
    assert _has(pts, (0, 0, 0.9)) and _has(pts, (0, 0, 0.1)), "the shared edge is not inset, only moved with the border"
    assert _has(pts, (-0.9, 0, 0.9)) and _has(pts, (0.9, 0, 0.1))
    bm.free()


def test_corner_shared_faces_keep_the_corner():
    bm = _plane([(-0.5, 0, 0.5), (0.5, 0, -0.5)])
    dup.duplicate(bm, {"offset": 0.1})
    pts = [v.co for f in _copies(bm) for v in f.verts]
    assert _has(pts, (0, 0, 0)), "the corner both faces share stays"
    bm.free()


def test_keep_faces_together_off_one_piece_per_face():
    bm = _plane([(-0.5, 0, 0.5), (0.5, 0, 0.5)])
    n = len(bm.verts)
    dup.duplicate(bm, {"offset": 0.1}, keep_faces_together=False)
    assert len(bm.verts) - n == 8
    pts = [v.co for f in _copies(bm) for v in f.verts]
    assert _has(pts, (-0.1, 0, 0.9)) and _has(pts, (0.1, 0, 0.9)), "each face inset on its own"
    bm.free()


def test_local_scale_before_offset():
    bm = _plane([(-0.5, 0, 0.5)])
    dup.duplicate(bm, {"offset": 0.1, "local_scale_x": 0.5}, keep_faces_together=False)
    xs = sorted({round(v.co.x, 6) for f in _copies(bm) for v in f.verts})
    assert xs == [-0.65, -0.35], f"half width, then 0.1 in from each scaled edge {xs}"
    bm.free()


def test_cube_edge_shared_vertex_is_the_mean():
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=2.0)
    for f in bm.faces:
        f.select = f.normal.z > 0.5 or f.normal.y > 0.5
    n = len(bm.verts)
    dup.duplicate(bm, {"local_translate_z": 0.5})
    assert len(bm.verts) - n == 6
    pts = [v.co for f in _copies(bm) for v in f.verts]
    assert _has(pts, (1, 1.25, 1.25)) and _has(pts, (-1, 1.25, 1.25)), \
        "the shared edge sits halfway between the two faces' moves"
    bm.free()
