"""#491: Insert Edge Loop with edge flow on a curved surface puts the new loop on the same curve as Edit Edge Flow.

A 4 x 4 plane whose rows are bent onto an arc. A loop inserted with edge flow at weight w moves off the straight cut by
4 w (1 - w) times the offset of the Edit Edge Flow curve's middle: halfway it sits exactly where Edit Edge Flow puts
it. Several loops at once are cut straight. Where a ring neighbour has no edge beyond it (the vertex sits on a border
row), the curve leaves that neighbour along the ring edge itself.
"""
import math
from importlib import import_module

import bmesh
from mathutils import Vector

import kit

el = import_module(kit.MODULE + ".operators.edge_loops")
emi = import_module(kit.MODULE + ".operators.edit_mesh_items")

PHI = math.radians(30.0)


def _arc_plane():
    """5 x 5 vertices, x across, rows k = 0..4 on a circle of radius 1 (row 2 at the top)."""
    bm = bmesh.new()
    vs = []
    for k in range(5):
        a = PHI * (k - 2)
        for i in range(5):
            vs.append(bm.verts.new((i - 2.0, math.sin(a), math.cos(a) - 1.0)))
    for k in range(4):
        for i in range(4):
            bm.faces.new([vs[k * 5 + i], vs[k * 5 + i + 1], vs[(k + 1) * 5 + i + 1], vs[(k + 1) * 5 + i]])
    bm.edges.ensure_lookup_table()
    return bm, vs


def _edge(a, b):
    return next(e for e in a.link_edges if e.other_vert(a) is b)


def _inserted(w, flow, position='RELATIVE', count=2):
    """Positions of the new vertices of a loop through the ring of the edge between rows 2 and 1 at x = 0, cut at
    ``w`` from row 2, sorted by x."""
    bm, vs = _arc_plane()
    old = set(bm.verts)
    el.insert_loops(bm, _edge(vs[12], vs[7]), w, position, count, math.radians(30.0), flow)
    out = sorted((v.co.copy() for v in bm.verts if v not in old), key=lambda p: (p.x, p.y))
    bm.free()
    return out


def _flow_middle():
    """Edit Edge Flow on the straight loop cut halfway between rows 2 and 1: its positions sorted by x."""
    bm, vs = _arc_plane()
    old = set(bm.verts)
    new = el.insert_loops(bm, _edge(vs[12], vs[7]), 0.5, 'RELATIVE', 2, math.radians(30.0), None)
    emi.edit_edge_flow(bm, new, 1.0)
    out = sorted((v.co.copy() for v in bm.verts if v not in old), key=lambda p: (p.x, p.y))
    bm.free()
    return out


def test_halfway_loop_follows_edit_edge_flow():
    got, want = _inserted(0.5, 1.0), _flow_middle()
    assert len(got) == len(want) == 5
    for p, q in zip(got, want):
        assert (p - q).length < 1e-5, (p, q)
    straight = _inserted(0.5, None)
    assert all((p - q).length > 1e-3 for p, q in zip(got, straight)), "the curve lies off the straight cut"


def test_other_weights_scale_the_offset():
    mid = [p - q for p, q in zip(_inserted(0.5, 1.0), _inserted(0.5, None))]
    for w in (0.1, 0.25, 0.8):
        got = [p - q for p, q in zip(_inserted(w, 1.0), _inserted(w, None))]
        for d, m in zip(got, mid):
            assert (d - m * (4 * w * (1 - w))).length < 1e-5, (w, d, m)
    half = [p - q for p, q in zip(_inserted(0.25, 0.5), _inserted(0.25, None))]
    for d, m in zip(half, mid):
        assert (d - m * 0.375).length < 1e-5, "Adjust edge flow scales the offset"


def test_several_loops_are_cut_straight():
    for p, q in zip(_inserted(0.5, 1.0, 'MULTIPLE', 2), _inserted(0.5, None, 'MULTIPLE', 2)):
        assert (p - q).length < 1e-7, (p, q)


def test_edit_edge_flow_next_to_a_border_row():
    """The loop on row 1: one ring neighbour on the border row 0 has no edge beyond it."""
    bm, vs = _arc_plane()
    row = [vs[5 + i] for i in range(5)]
    loop = [_edge(row[i], row[i + 1]) for i in range(4)]
    a, b, b2 = vs[0].co.copy(), vs[10].co.copy(), vs[15].co.copy()      # x = -2: rows 0, 2, 3
    emi.edit_edge_flow(bm, loop, 1.0)
    got = row[0].co.copy()
    bm.free()
    u = (b - a).normalized()
    tb = (b2 - b).normalized()
    want = (a + b) / 2 + (u - tb) * (0.7 * (b - a).length / 8)
    assert (got - want).length < 1e-6, (got, want)
    mirrored = (a + b) / 2 + ((u * 2 * u.dot(tb) - tb) - tb) * (0.7 * (b - a).length / 8)
    assert (got - mirrored).length > 1e-3, "not the mirrored tangent"
    assert isinstance(got, Vector)
