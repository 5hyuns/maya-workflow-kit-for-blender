"""Edit Mesh > Bevel (operators/bevel_maya.py), Fraction mode: at an acute or right corner where two bevelled edges of a
face meet, the new corner never slides past the far end of either edge (its foot on the edge stays within the edge),
so Fraction 1 there is the width that brings that foot to the edge's end."""

import math
from importlib import import_module

import bmesh

import kit

bev = import_module(kit.MODULE + ".operators.bevel_maya")


def _prism(theta, height=2.0, side=2.0):
    """A parallelogram prism: top face with angle ``theta`` (degrees) at the origin, sides ``side`` long, walls
    straight down by ``height``. Returns (bm, the two top edges at the origin)."""
    t = math.radians(theta)
    top = [(0.0, 0.0, 0.0), (side, 0.0, 0.0), (side + side * math.cos(t), 0.0, side * math.sin(t)),
           (side * math.cos(t), 0.0, side * math.sin(t))]
    bm = bmesh.new()
    up = [bm.verts.new(p) for p in top]
    down = [bm.verts.new((x, y - height, z)) for x, y, z in top]
    bm.faces.new(up)
    bm.faces.new(list(reversed(down)))
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((up[j], up[i], down[i], down[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    rims = [e for e in bm.edges if up[0] in e.verts and all(v.co.y == 0.0 for v in e.verts)]
    assert len(rims) == 2
    return bm, rims


def test_acute_corner_limits_the_fraction():
    bm, rims = _prism(60.0)
    # the corner moves along the bisector, W / sin 30 from the corner: its foot on a 2 long rim is W / tan 30
    want = 2.0 * math.tan(math.radians(30.0)) * bev.FIT
    got = bev.width(rims, fraction=1.0)
    bm.free()
    assert abs(got - want) < 1e-6, (got, want)


def test_wide_corner_keeps_the_bisector_limit():
    bm, rims = _prism(120.0)
    got = bev.width(rims, fraction=1.0)
    bm.free()
    # a 120 degree corner: the foot limit (2 tan 60) is wider than the others, so the width stays below it
    assert got < 2.0 * math.tan(math.radians(60.0)) * bev.FIT - 1e-3, got


def test_fraction_scales_the_limit():
    bm, rims = _prism(60.0)
    full = bev.width(rims, fraction=1.0)
    half = bev.width(rims, fraction=0.5)
    bm.free()
    assert abs(half - full / 2.0) < 1e-9, (half, full)
