"""Edit Mesh > Bevel (operators/bevel_maya.py): where two bevelled edges in a row around a vertex have two or more
unbevelled edges between them, the faces of that gap meet at one new vertex. It lies on the bisector of the gap's
faces laid flat around the vertex, at the bevel width from both bevelled edges in that flat layout."""

import math
from importlib import import_module

import bmesh
from mathutils import Vector

import kit

bev = import_module(kit.MODULE + ".operators.bevel_maya")
TOL = 1e-5


def _fan(az_el):
    """A cone-like solid: apex at the origin, one ring vertex per (azimuth, elevation from the down axis) on the plane
    y = -1, side triangles and a base cap."""
    bm = bmesh.new()
    apex = bm.verts.new((0.0, 0.0, 0.0))
    ring = []
    for az, el in az_el:
        a, r = math.radians(az), math.tan(math.radians(el))
        ring.append(bm.verts.new((r * math.cos(a), -1.0, r * math.sin(a))))
    n = len(ring)
    for i in range(n):
        bm.faces.new((apex, ring[(i + 1) % n], ring[i]))
    bm.faces.new(ring)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return bm, apex.co.copy(), [v.co.copy() for v in ring]


def _bevel_first_two(az_el, offset=0.1):
    bm, apex, ring = _fan(az_el)
    picked = [e for e in bm.edges if any(v.co.length < TOL for v in e.verts)
              and any((v.co - ring[i]).length < TOL for v in e.verts for i in (0, 1))]
    assert len(picked) == 2
    bev.bevel_edges(bm, picked, offset_as_fraction=False, offset=offset)
    return bm, apex, ring


def _check_gap_vertex(az_el, offset=0.1):
    bm, apex, ring = _bevel_first_two(az_el, offset)
    w = offset * bev.FIT
    dirs = [(p - apex).normalized() for p in ring]
    # the gap runs from ring edge 1 over edges 2 .. n-1 to edge 0
    order = [1] + list(range(2, len(ring))) + [0]
    angles = [dirs[a].angle(dirs[b]) for a, b in zip(order, order[1:])]
    theta = sum(angles)
    near = [v.co.copy() for v in bm.verts if 1e-6 < v.co.length < 0.5]
    # off the face between the two bevelled edges: exactly one vertex left on the gap side
    shared = dirs[0].cross(dirs[1]).normalized()
    far = [p for p in near if abs(p.dot(shared)) > 1e-5]
    assert len(far) == 1, far
    p = far[0]
    assert abs(p.length - w / math.sin(theta / 2.0)) < TOL, (p.length, w / math.sin(theta / 2.0))
    # in the gap face that holds the bisector, at half the flat angle from the first bevelled edge
    rest = theta / 2.0
    for (a, b), ang in zip(zip(order, order[1:]), angles):
        if rest <= ang + 1e-9:
            normal = dirs[a].cross(dirs[b]).normalized()
            assert abs(p.normalized().dot(normal)) < 1e-6
            assert abs(dirs[a].angle(p) - rest) < 1e-6
            break
        rest -= ang
    bm.free()


def test_square_pyramid_gap_is_one_vertex():
    _check_gap_vertex([(-45, 45), (45, 45), (135, 45), (225, 45)])


def test_uneven_fans_gap_on_the_flat_bisector():
    _check_gap_vertex([(-30, 50), (40, 35), (120, 60), (200, 30), (280, 55)])
    _check_gap_vertex([(-45, 45), (45, 45), (135, 45), (180, 20), (225, 45)], offset=0.2)


def test_one_unbevelled_edge_keeps_its_slide_point():
    """With a single unbevelled edge between them the new vertex stays on that edge."""
    bm, apex, ring = _bevel_first_two([(-60, 45), (60, 45), (180, 45)])
    d = (ring[2] - apex).normalized()
    on_edge = [v for v in bm.verts if 1e-6 < v.co.length < 0.5 and v.co.cross(d).length < 1e-6]
    assert len(on_edge) == 1
    bm.free()
