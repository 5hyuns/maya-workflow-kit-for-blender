"""Multi-Cut between points that share no face (GitHub #545): the cut runs across the faces in between, in the
plane through both points that holds the sum of their normals; face points still need a shared face."""

from importlib import import_module

import bmesh
from mathutils import Vector

import kit

mc = import_module(kit.MODULE + ".operators.multi_cut")


def _mesh(verts, faces):
    bm = bmesh.new()
    vs = [bm.verts.new(co) for co in verts]
    for f in faces:
        bm.faces.new([vs[i] for i in f])
    bm.normal_update()
    for seq in (bm.verts, bm.edges, bm.faces):
        seq.index_update()
        seq.ensure_lookup_table()
    return bm


def _strip(heights=None):
    """A 4 x 1 strip along x (y up): bottom row 0..4 at z = 0.5, top row 5..9 at z = -0.5; ``heights``: column ->
    y of both its vertices."""
    heights = heights or {}
    verts = [(-2.0 + c, heights.get(c, 0.0), 0.5 - r) for r in range(2) for c in range(5)]
    faces = [(c, c + 5, c + 6, c + 1) for c in range(4)]
    return _mesh(verts, faces)


def _cube():
    """A 2 x 2 x 2 cube around the origin."""
    verts = [(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
    idx = {v: i for i, v in enumerate(verts)}

    def q(*cs):
        return tuple(idx[c] for c in cs)
    faces = [q((-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)), q((-1, -1, -1), (-1, 1, -1), (1, 1, -1), (1, -1, -1)),
             q((-1, -1, -1), (-1, -1, 1), (-1, 1, 1), (-1, 1, -1)), q((1, -1, -1), (1, 1, -1), (1, 1, 1), (1, -1, 1)),
             q((-1, -1, -1), (1, -1, -1), (1, -1, 1), (-1, -1, 1)), q((-1, 1, -1), (-1, 1, 1), (1, 1, 1), (1, 1, -1))]
    return _mesh(verts, faces)


def _vert(bm, co):
    return next(v for v in bm.verts if (v.co - Vector(co)).length < 1e-6)


def _ep(bm, a, b, t_from_a):
    va, vb = _vert(bm, a), _vert(bm, b)
    e = next(e for e in va.link_edges if vb in e.verts)
    return ('EDGE', e.index, t_from_a if e.verts[0] is va else 1.0 - t_from_a)


def _vp(bm, co):
    return ('VERT', _vert(bm, co).index)


def _counts(bm):
    return len(bm.verts), len(bm.edges), len(bm.faces)


def _has(bm, co, tol=1e-5):
    return any((v.co - Vector(co)).length < tol for v in bm.verts)


def test_edge_points_across_a_flat_strip():
    bm = _strip()
    a, b = _ep(bm, (-2, 0, .5), (-2, 0, -.5), 0.5), _ep(bm, (2, 0, .5), (2, 0, -.5), 0.9)
    assert mc.accepts(bm, [a], b), "the cut can run across the three faces in between"
    crossings = mc.across(bm, a, b)
    assert [p[0] for p in crossings] == ['EDGE'] * 3, crossings
    edges = mc.cut(bm, [a, b])
    assert _counts(bm) == (15, 22, 8), _counts(bm)
    assert len(edges) == 4
    for x, z in ((-1, -0.1), (0, -0.2), (1, -0.3)):          # the straight line from z 0 to z -0.4
        assert _has(bm, (x, 0, z)), (x, z)
    bm.free()


def test_vertex_to_vertex_across_and_along_a_border():
    bm = _strip()
    mc.cut(bm, [_vp(bm, (-2, 0, .5)), _vp(bm, (2, 0, -.5))])
    assert _counts(bm) == (13, 20, 8), _counts(bm)
    for x, z in ((-1, .25), (0, 0), (1, -.25)):
        assert _has(bm, (x, 0, z)), (x, z)
    bm.free()
    bm = _strip()                                       # along the border edges: nothing to cut
    a, b = _vp(bm, (-2, 0, .5)), _vp(bm, (2, 0, .5))
    assert mc.accepts(bm, [a], b)
    mc.cut(bm, [a, b])
    assert _counts(bm) == (10, 13, 4), _counts(bm)
    bm.free()


def test_cut_through_an_existing_vertex():
    verts = [(-2.0 + c, 0.0, 2.0 - r) for r in range(5) for c in range(5)]
    faces = [(r * 5 + c, (r + 1) * 5 + c, (r + 1) * 5 + c + 1, r * 5 + c + 1) for r in range(4) for c in range(4)]
    bm = _mesh(verts, faces)
    mc.cut(bm, [_vp(bm, (-1, 0, 1)), _vp(bm, (1, 0, -1))])  # the diagonal passes the vertex at the origin
    assert _counts(bm) == (25, 42, 18), _counts(bm)
    bm.free()


def test_cut_stays_in_one_plane_on_a_bent_strip():
    bm = _strip({1: 0.6, 2: 1.5})
    a, b = _ep(bm, (-1, .6, .5), (-1, .6, -.5), 0.3), _ep(bm, (2, 0, .5), (2, 0, -.5), 0.9)
    S, E = mc._point_co(bm, a), mc._point_co(bm, b)
    n = mc._point_normal(bm, a) + mc._point_normal(bm, b)
    m = (E - S).cross(n).normalized()
    pts = [mc._point_co(bm, p) for p in mc.across(bm, a, b)]
    assert len(pts) == 2, pts
    assert all(abs(m.dot(p - S)) < 1e-6 for p in pts), "every crossing lies in the cut plane"
    mc.cut(bm, [a, b])
    assert _counts(bm) == (14, 20, 7), _counts(bm)
    bm.free()


def test_cube_takes_the_shorter_way():
    bm = _cube()
    a, b = _ep(bm, (-1, 1, 1), (1, 1, 1), 0.5), _ep(bm, (1, 1, -1), (1, -1, -1), 0.5)
    crossings = mc.across(bm, a, b)
    assert len(crossings) == 1 and (mc._point_co(bm, crossings[0]) - Vector((1, 1, 0))).length < 1e-6, crossings
    mc.cut(bm, [a, b])
    assert _counts(bm) == (11, 17, 8), _counts(bm)
    bm.free()


def test_opposite_normals_still_cut():
    bm = _cube()                                        # the two edge normals cancel: a start face sets the plane
    a, b = _ep(bm, (-1, -1, 1), (-1, 1, 1), 0.5), _ep(bm, (1, 1, -1), (1, -1, -1), 0.5)
    assert mc.accepts(bm, [a], b)
    mc.cut(bm, [a, b])
    assert _counts(bm) == (11, 17, 8), _counts(bm)
    bm.free()


def test_face_points_still_need_a_shared_face():
    bm = _strip()
    a = _ep(bm, (-2, 0, .5), (-2, 0, -.5), 0.5)
    f0 = next(f for f in bm.faces if _vert(bm, (-2, 0, .5)) in f.verts)
    fp = ('FACE', f0.index, (-1.5, 0.0, 0.2))
    far = _ep(bm, (2, 0, .5), (2, 0, -.5), 0.5)
    assert mc.accepts(bm, [a], fp)
    assert not mc.accepts(bm, [a, fp], far), "a face point and a point on a face it doesn't touch"
    assert mc.with_crossings(bm, [a, far])[1:-1], "edge points get the crossings in between"
    bm.free()
