"""Edit Mesh > Bevel on part of an n-gon cap's rim and on a whole n-gon rim (operators/bevel_maya.py): chain ends whose
slide edge runs near the bevelled edge's line, and n-gon corners."""

import math
from importlib import import_module

import bmesh
from mathutils import Vector

import kit

bev = import_module(kit.MODULE + ".operators.bevel_maya")
SIDES = 20


def _cylinder_caps0():
    """Radius 1, height 2, one n-gon per cap; top rim vertex i at angle -(i + 1) x 18 degrees."""
    bm = bmesh.new()
    angle = lambda i: -(i + 1) * 2.0 * math.pi / SIDES
    bottom = [bm.verts.new((math.cos(angle(i)), math.sin(angle(i)), -1.0)) for i in range(SIDES)]
    top = [bm.verts.new((math.cos(angle(i)), math.sin(angle(i)), 1.0)) for i in range(SIDES)]
    for i in range(SIDES):
        j = (i + 1) % SIDES
        bm.faces.new((bottom[i], bottom[j], top[j], top[i]))
    bm.faces.new(list(reversed(bottom)))
    bm.faces.new(top)
    bm.normal_update()
    return bm, top


def _rim(bm, top, count):
    return [bm.edges.get((top[i], top[i + 1])) for i in range(count)]


def test_part_of_an_ngon_rim():
    """Three rim edges: at the chain ends the rim neighbour runs 162 degrees from the bevelled edge, so both new
    vertices there sit k x W along their edges, k = sqrt(2) / sqrt(1 + sin^2 18) (side and cap at right angles); the
    width W comes from the rim neighbour (its length / k) and the inner vertices drop W."""
    bm, top = _cylinder_caps0()
    edges = _rim(bm, top, 3)
    rim = 2.0 * math.sin(math.pi / SIDES)
    k = math.sqrt(2.0) / math.sqrt(1.0 + math.sin(math.radians(18.0)) ** 2)
    w = 0.5 * 0.9999 * rim / k
    assert abs(bev.width(edges) - w) < 1e-7, (bev.width(edges), w)
    ends = [top[0].co.copy(), top[3].co.copy()]
    inner = [top[1].co.copy(), top[2].co.copy()]
    neighbours = [top[SIDES - 1].co.copy(), top[4].co.copy()]
    n0 = len(bm.verts)
    bev.bevel_edges(bm, edges)
    assert len(bm.verts) == n0 + 4, len(bm.verts)

    def drop(p):
        return [p.z - v.co.z for v in bm.verts if (v.co.xy - p.xy).length < 1e-6 and v.co.z < p.z - 1e-6]
    for p in inner:
        assert any(abs(d - w) < 1e-6 for d in drop(p)), (p, drop(p))
    for p, q in zip(ends, neighbours):
        assert any(abs(d - k * w) < 1e-6 for d in drop(p)), (p, drop(p))
        along = (q - p).normalized()
        assert any(abs((v.co - p).length - k * w) < 1e-6 and ((v.co - p).normalized() - along).length < 1e-5
                   for v in bm.verts), p
    bm.free()


def test_whole_ngon_rim():
    """A whole rim: each corner moves along its bisector, which leaves the n-gon through the opposite corner
    (distance 2) moving the other way, so the width is 0.5 x 0.9999 x 2 x sin 81 / 2 and the corners end
    W / sin 81 = 0.49995 in from the rim, like a fan cap's."""
    bm, top = _cylinder_caps0()
    edges = _rim(bm, top, SIDES - 1) + [bm.edges.get((top[SIDES - 1], top[0]))]
    half = math.radians(81.0)
    w = 0.5 * 0.9999 * math.sin(half)
    assert abs(bev.width(edges) - w) < 1e-7, (bev.width(edges), w)
    bev.bevel_edges(bm, edges)
    ring = [v for v in bm.verts if abs(v.co.z - 1.0) < 1e-6]
    assert len(ring) == SIDES and all(abs(v.co.xy.length - (1.0 - 0.49995)) < 1e-6 for v in ring), \
        sorted(round(v.co.xy.length, 6) for v in ring)
    bm.free()


def test_plain_ends_keep_blenders_offsets():
    """A lone edge of a cube: both slide edges at right angles, nothing near the line — the end vertices sit W along
    them."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bm.edges.ensure_lookup_table()
    e = bm.edges[0]
    assert not bev.end_moves([e])[0]
    p = Vector(e.verts[0].co)
    bev.bevel_edges(bm, [e])
    assert sorted(round((v.co - p).length, 6) for v in bm.verts if 1e-6 < (v.co - p).length < 0.6) == [0.49995] * 2
    bm.free()
