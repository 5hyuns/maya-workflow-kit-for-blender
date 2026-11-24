"""Issue #465: Circularize on an edge loop or a vertex loop.

Like Maya: the circle's centre is the loop's mean point and its radius the mean distance in the circle's plane;
spread evenly, the loop's lowest-index vertex keeps its angle. On a vertex loop the plane's normal is the summed
area normal of every face touching the loop, so a ring on a flat plane stays flat even when one ring vertex was
lifted. On an edge loop the vertices are taken in index order (not loop order): each neighbouring pair adds the
cross product of their offsets from the centre, skipping a term that points 90 degrees or more away from the sum
so far. On a block of faces the inner vertices relax against the border before it is spread evenly."""

import math
from importlib import import_module

import bmesh
from mathutils import Vector

import kit

poly = import_module(kit.MODULE + ".operators.poly_maya")


def _plane():
    """A 6 x 6 grid (vertex r * 7 + c at (c - 3, r - 3, 0)); returns bm and the ring around the middle 2 x 2 block
    in loop order."""
    bm = bmesh.new()
    vs = [bm.verts.new((c - 3.0, r - 3.0, 0.0)) for r in range(7) for c in range(7)]
    for r in range(6):
        for c in range(6):
            a = r * 7 + c
            bm.faces.new((vs[a], vs[a + 1], vs[a + 8], vs[a + 7]))
    bm.verts.index_update()
    ring = [vs[r * 7 + c] for r, c in ((2, 2), (2, 3), (2, 4), (3, 4), (4, 4), (4, 3), (4, 2), (3, 2))]
    return bm, ring


def _bump(ring):
    ring[1].co.z += 0.3          # a lifted vertex
    ring[3].co.x += 0.25         # and two pushed sideways, so the loop is not symmetric
    ring[6].co.y -= 0.2


def _select(bm, ring):
    for a, b in zip(ring, ring[1:] + ring[:1]):
        bm.edges.get((a, b)).select = True
        a.select = True


def _angle(p, c, n, u):
    d = p - c
    d -= n * d.dot(n)
    return math.atan2(n.cross(u).dot(d), u.dot(d))


def _check(ring, before, n):
    c = sum(before, Vector()) / len(before)
    u = Vector((1.0, 0.0, 0.0))
    u = (u - n * u.dot(n)).normalized()
    lowest = min(range(len(ring)), key=lambda i: ring[i].index)
    a0 = _angle(before[lowest], c, n, u)
    a1 = _angle(ring[lowest].co, c, n, u)
    assert abs(math.remainder(a1 - a0, math.tau)) < 1e-6, (a0, a1)      # the lowest index keeps its angle
    after = sum((v.co for v in ring), Vector()) / len(ring)
    assert (after - c).length < 1e-6                                     # centre = the loop's mean point
    steps = [math.remainder(_angle(ring[(i + 1) % 8].co, c, n, u) - _angle(ring[i].co, c, n, u), math.tau)
             for i in range(8)]
    assert all(abs(abs(s) - math.tau / 8) < 1e-6 for s in steps), steps   # evenly spread
    assert all(abs((v.co - c).dot(n)) < 1e-6 for v in ring)             # on the plane


def test_vertex_loop_keeps_the_faces_plane():
    bm, ring = _plane()
    _bump(ring)
    before = [v.co.copy() for v in ring]
    _select(bm, ring)
    assert poly.circularize_loops(bm, 'VERT') == 1
    # the faces touching the ring make a 4 x 4 block whose border is flat: the circle lies flat
    _check(ring, before, Vector((0.0, 0.0, 1.0)))
    bm.free()


def test_edge_loop_starts_at_the_lowest_index():
    bm, ring = _plane()
    _bump(ring)
    before = [v.co.copy() for v in ring]
    _select(bm, ring)
    assert poly.circularize_loops(bm, 'EDGE') == 1
    order = sorted(range(8), key=lambda i: ring[i].index)
    c = sum(before, Vector()) / 8
    n = Vector()
    for i, j in zip(order, order[1:]):
        t = (before[i] - c).cross(before[j] - c)
        if n.length == 0 or n.dot(t) > 0:
            n += t
    _check(ring, before, n.normalized())
    bm.free()


def test_edge_loop_plane_with_one_vertex_lifted():
    """A flat ring with only its second-lowest vertex lifted tilts the circle towards it, not symmetrically."""
    bm, ring = _plane()
    ring[1].co.z += 0.3
    _select(bm, ring)
    assert poly.circularize_loops(bm, 'EDGE') == 1
    pts = [v.co for v in ring]
    c = sum(pts, Vector()) / 8
    n = (pts[0] - c).cross(pts[2] - c).normalized()
    if n.z < 0:
        n.negate()
    # pairs in index order 16, 17, 18, 23, 25, 30, 31, 32, no wrap-around: the tilt is not symmetric
    want = Vector((0.0122563, 0.1961014, 0.980507))
    assert (n - want).length < 1e-6, n
    bm.free()


def test_face_block_inner_vertices_relax_twice():
    """The middle 4 x 4 faces of a flat 6 x 6 grid: the border goes onto a circle of radius 2.3251408 and the
    nine inner vertices end up 1.1333497 (edge middles) and 1.5280969 (corners) from the centre."""
    bm, _ring = _plane()
    for f in bm.faces:
        m = f.calc_center_median()
        f.select = abs(m.x) < 2 and abs(m.y) < 2
    assert poly.circularize_loops(bm, 'FACE') == 1
    bm.verts.ensure_lookup_table()
    vs = bm.verts
    for i in (16, 18, 30, 32):
        assert abs(vs[i].co.length - 1.5280969) < 1e-6, (i, vs[i].co.length)
    for i in (17, 23, 25, 31):
        assert abs(vs[i].co.length - 1.1333497) < 1e-6, (i, vs[i].co.length)
    assert vs[24].co.length < 1e-9
    for i in (8, 9, 10, 11, 12, 15, 19, 22, 26, 29, 33, 36, 37, 38, 39, 40):
        assert abs(vs[i].co.length - 2.3251408) < 1e-6, (i, vs[i].co.length)
    bm.free()
