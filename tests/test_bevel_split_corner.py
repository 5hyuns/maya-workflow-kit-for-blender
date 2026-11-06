"""Edit Mesh > Bevel (operators/bevel_maya.py), Fraction mode: a corner where three bevelled edges meet and their
sin(dihedral / 2) values differ a lot (a "split" corner). The kit places each face's new corner like this: the face
whose two edges have equal angles gets its corner on its bisector, every other face on the line through the old corner
and the point where the two edges' offset lines meet."""

import math
from importlib import import_module

import bmesh
from mathutils import Vector

import kit

bev = import_module(kit.MODULE + ".operators.bevel_maya")


def _corner(ab, bc, ca, length=2.0):
    """Parallelepiped whose corner at the origin has face angles ab (between edges A and B), bc and ca (degrees).
    Returns (bm, the three edges at the origin, {edge: unit direction}, edge ids)."""
    g, al, be = [math.radians(x) for x in (ab, bc, ca)]
    a = Vector((1.0, 0.0, 0.0))
    b = Vector((math.cos(g), math.sin(g), 0.0))
    cx = math.cos(be)
    cy = (math.cos(al) - math.cos(be) * math.cos(g)) / math.sin(g)
    c = Vector((cx, cy, -math.sqrt(max(0.0, 1.0 - cx * cx - cy * cy))))
    a, b, c = a * length, b * length, c * length
    o = Vector()
    pts = [o, a, b, c, a + b, b + c, a + c, a + b + c]
    bm = bmesh.new()
    vs = [bm.verts.new(p) for p in pts]
    for f in ((0, 1, 4, 2), (0, 2, 5, 3), (0, 3, 6, 1), (7, 4, 1, 6), (7, 5, 2, 4), (7, 6, 3, 5)):
        bm.faces.new([vs[i] for i in f])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.edges.index_update()
    ids = {e: e.index for e in bm.edges}
    mine = [e for e in bm.edges if vs[0] in e.verts]
    units = {e: (e.other_vert(vs[0]).co - o).normalized() for e in mine}
    return bm, mine, units, ids


def _line_dist(p, u):
    return (p - u * p.dot(u)).length


def test_split_corner_is_found_and_box_is_not():
    bm, mine, _u, ids = _corner(90, 90, 90)
    assert bev.corner_splits(mine, ids) == {}
    bm.free()
    bm, mine, _u, ids = _corner(60, 90, 90)
    got = bev.corner_splits(mine, ids)
    bm.free()
    assert len(got) == 1 and len(next(iter(got.values()))["faces"]) == 3, got


def test_faces_follow_their_rays():
    bm, mine, units, ids = _corner(60, 90, 90)
    h = {e: bev._half_sin(e, e.verts[0] if e.verts[0].co.length < 1e-9 else e.verts[1]) for e in mine}
    w = bev.width(mine, fraction=0.2)
    pairs = [(a, b) for i, a in enumerate(mine) for b in mine[i + 1:]]
    made = bev.bevel_edges(bm, mine, fraction=0.2, edge_ids=ids)
    assert made
    near = [v.co.copy() for v in made if 1e-6 < v.co.length < 0.6]
    assert len(near) == 3, len(near)
    for a, b in pairs:
        ua, ub = units[a], units[b]
        normal = ua.cross(ub).normalized()
        p = [q for q in near if abs(q.dot(normal)) < 1e-5][0]
        da, db = _line_dist(p, ua), _line_dist(p, ub)
        if abs(h[a] - h[b]) < 1e-9:
            assert abs(da - db) < 1e-5, (da, db)                  # on the bisector
        else:
            assert abs(da * h[a] - db * h[b]) < 1e-5, (da, db)    # on the line through the offset lines' meet
        assert da > 0.2 * w and db > 0.2 * w
    bm.free()


def test_full_fraction_stays_inside_the_edges():
    bm, mine, units, ids = _corner(60, 90, 90)
    made = bev.bevel_edges(bm, mine, fraction=1.0, edge_ids=ids)
    corner = sorted((v.co.copy() for v in made), key=lambda p: p.length)[:3]
    for p in corner:
        for u in units.values():
            if _line_dist(p, u) > 1e-6:
                assert p.dot(u) <= 2.0 + 1e-5, (tuple(p), tuple(u))
    bm.free()
