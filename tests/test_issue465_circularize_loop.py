"""Issue #465: Circularize on an edge loop or a vertex loop.

Like Maya: the circle's centre is the loop's mean point and its radius the mean distance in the circle's plane;
spread evenly, the loop's lowest-index vertex keeps its angle. On a vertex loop the plane's normal is the summed
area normal of every face touching the loop, so a ring on a flat plane stays flat even when one ring vertex was
lifted; on an edge loop it is the loop's own normal."""

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
    n = Vector()
    for i in range(8):
        a, b = before[i], before[(i + 1) % 8]
        n += Vector(((a.y - b.y) * (a.z + b.z), (a.z - b.z) * (a.x + b.x), (a.x - b.x) * (a.y + b.y)))
    _check(ring, before, n.normalized())
    bm.free()
