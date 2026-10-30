"""Edit Mesh > Bevel (operators/bevel_maya.py): a lone rim edge of an n-gon cap with many sides, a non-planar face next
to a bevelled side edge, border edges in the selection, Merge Vertices numbering, and the face order around chain ends.
Meshes are built in the vertex / face / edge order of the kit's Maya-style primitives; expected values by index."""

import math
from importlib import import_module

import bmesh
from mathutils import Vector

import kit

bev = import_module(kit.MODULE + ".operators.bevel_maya")
TOL = 1e-5


def _mesh(V, F, E):
    bm = bmesh.new()
    vs = [bm.verts.new(p) for p in V]
    for f in F:
        bm.faces.new([vs[i] for i in f])
    bm.verts.index_update()
    pair = {frozenset(e): i for i, e in enumerate(E)}
    ids = {e: pair[frozenset((e.verts[0].index, e.verts[1].index))] for e in bm.edges}
    return bm, ids


def _bevel(V, F, E, sel, **kw):
    bm, ids = _mesh(V, F, E)
    made = bev.bevel_edges(bm, [e for e in bm.edges if ids[e] in set(sel)], edge_ids=ids, **kw)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    got = [v.co.copy() for v in bm.verts]
    faces = [{v.index for v in f.verts} for f in bm.faces]
    bm.free()
    return got, faces, made


def _ring(n, i, y, r=1.0):
    a = -(i + 1) * 2.0 * math.pi / n
    return [r * math.cos(a), y, r * math.sin(a)]


def _cylinder(n=20, fans=True):
    """Radius 1, height 2 (y up): bottom ring 0..n-1, top ring n..2n-1, then the cap centres (fan caps) or one n-gon
    per cap; edges: rings, sides, then the spokes."""
    V = [_ring(n, i, -1.0) for i in range(n)] + [_ring(n, i, 1.0) for i in range(n)]
    F = [[i, (i + 1) % n, n + (i + 1) % n, n + i] for i in range(n)]
    E = [[i, (i + 1) % n] for i in range(n)] + [[n + i, n + (i + 1) % n] for i in range(n)] + [[i, n + i] for i in range(n)]
    if fans:
        V += [[0.0, -1.0, 0.0], [0.0, 1.0, 0.0]]
        F += [[(i + 1) % n, i, 2 * n] for i in range(n)] + [[n + i, n + (i + 1) % n, 2 * n + 1] for i in range(n)]
        E += [[2 * n, i] for i in range(n)] + [[n + i, 2 * n + 1] for i in range(n)]
    else:
        F += [[0] + list(range(n - 1, 0, -1)), list(range(n, 2 * n))]
    return V, F, E


def _plane(n=4):
    """Size n x n, n x n faces, row-major vertices from (-n/2, 0, n/2)."""
    m = n + 1
    V = [[-n / 2 + c, 0.0, n / 2 - r] for r in range(m) for c in range(m)]
    F = [[r * m + c, r * m + c + 1, (r + 1) * m + c + 1, (r + 1) * m + c] for r in range(n) for c in range(n)]
    E = []
    for v in range(m * m):
        r, c = divmod(v, m)
        if c < n:
            E.append([v, v + 1])
        if r < n:
            E.append([v, v + m])
    return V, F, E


def _near(got, want, tol=TOL):
    bad = [(i, tuple(round(x, 6) for x in g), w) for i, (g, w) in enumerate(zip(got, want))
           if (g - Vector(w)).length > tol]
    assert not bad, bad[:4]


def test_ngon_lone_rim_edge_with_many_sides():
    """A lone rim edge of an n-gon cap: with 24 sides the width comes from the rim neighbour (length / k); with 40
    sides, where the two rim neighbours run outwards almost parallel, from half the edge's own length over k
    (k = sqrt 2 / sqrt(1 + sin^2(the turn at a rim vertex)), side and cap at right angles)."""
    for n, halved in ((24, False), (40, True)):
        V, F, E = _cylinder(n, fans=False)
        bm, ids = _mesh(V, F, E)
        edge = [e for e in bm.edges if ids[e] == n]
        rim = 2.0 * math.sin(math.pi / n)
        k = math.sqrt(2.0) / math.sqrt(1.0 + math.sin(2.0 * math.pi / n) ** 2)
        want = 0.5 * 0.9999 * (rim / (2.0 * k) if halved else rim / k)
        assert abs(bev.width(edge) - want) < 1e-7, (n, bev.width(edge), want)
        bm.free()
    got, _faces, _made = _bevel(*_cylinder(40, fans=False), [40])
    assert len(got) == 82, len(got)
    _near(got[78:], [[0.987689, 0.960774, -0.156434], [0.990766, 1.0, -0.11733], [0.951057, 0.960774, -0.309017],
                     [0.936046, 1.0, -0.345257]])


def test_non_planar_face_next_to_a_bevelled_side_edge():
    """Side edge 1-21 of a fan-capped cylinder whose bottom vertex 0 is moved to (0.7, -1, 0), so the side face 0-1-21-20
    is not planar: the bevel takes one angle for the whole edge (at its first vertex), so the top end's new vertices
    move in by the same factor."""
    V, F, E = _cylinder()
    V[0] = [0.7, -1.0, 0.0]
    got, _faces, _made = _bevel(V, F, E, [41])
    assert len(got) == 46, len(got)
    _near(got[40:], [[0.69703, -1.0, -0.506422], [0.698413, -1.0, -0.698391], [0.780493, -1.0, -0.43399],
                     [0.69703, 1.0, -0.506422], [0.872644, 1.0, -0.462911], [0.709917, 1.0, -0.686886]])


PLANE_AFTER = [[-2.0, 0.0, 2.0], [0.0, 0.0, 2.0], [2.0, 0.0, 2.0], [-2.0, 0.0, 1.0], [0.0, 0.0, 1.0], [2.0, 0.0, 1.0],
               [-2.0, 0.0, 0.0], [2.0, 0.0, 0.0], [-2.0, 0.0, -1.0], [-1.0, 0.0, -1.0], [0.0, 0.0, -1.0], [1.0, 0.0, -1.0],
               [2.0, 0.0, -1.0], [-2.0, 0.0, -2.0], [-1.0, 0.0, -2.0], [0.0, 0.0, -2.0], [1.0, 0.0, -2.0], [2.0, 0.0, -2.0],
               [-0.50005, 0.0, 2.0], [-1.49995, 0.0, 2.0], [-1.49995, 0.0, 1.0], [-0.50005, 0.0, 1.0], [1.49995, 0.0, 2.0],
               [0.50005, 0.0, 2.0], [0.50005, 0.0, 1.0], [1.49995, 0.0, 1.0], [-0.50005, 0.0, 0.49995],
               [-1.49995, 0.0, -0.49995], [0.50005, 0.0, 0.49995], [1.49995, 0.0, -0.49995], [0.0, 0.0, 0.49995],
               [0.0, 0.0, -0.49995]]
PLANE_AFTER_F = [[8, 9, 14, 13], [9, 10, 15, 14], [10, 11, 16, 15], [11, 12, 17, 16], [19, 18, 21, 20], [20, 21, 26, 27],
                 [23, 22, 25, 24], [24, 25, 29, 28], [27, 26, 30, 31], [28, 29, 31, 30], [0, 19, 20, 3], [21, 18, 1, 4],
                 [1, 23, 24, 4], [25, 22, 2, 5], [3, 20, 27, 6], [21, 4, 30, 26], [4, 24, 28, 30], [25, 5, 7, 29],
                 [6, 27, 9, 8], [27, 31, 10, 9], [31, 29, 11, 10], [29, 7, 12, 11]]


def test_closed_loop_along_a_border():
    """A closed loop on a 4 x 4 plane that runs two edges along the border: the border edges stay as they are (vertex
    1 keeps its place and number), the rest bevels; vertices and faces in the expected order."""
    got, faces, _made = _bevel(*_plane(), [2, 4, 7, 16, 22, 20, 12, 3])
    assert len(got) == 32, len(got)
    _near(got, PLANE_AFTER)
    assert faces == [set(f) for f in PLANE_AFTER_F], faces


def test_lone_border_edge_does_nothing():
    V, F, E = _plane()
    got, faces, made = _bevel(V, F, E, [0])
    assert not made and len(got) == 25 and len(faces) == 16


def test_merged_vertices_keep_the_old_number():
    """Fraction 1 on three rim edges of a 20-sided n-gon cap: the chain ends' new vertices on the rim neighbours land
    on the neighbours' vertices and merge into them; the old vertices keep their numbers and the other new vertices
    close up after them."""
    V, F, E = _cylinder(20, fans=False)
    got, faces, _made = _bevel(V, F, E, [20, 21, 22], fraction=1.0)
    assert len(got) == 42, len(got)
    kept = [i for i in range(40) if i not in (20, 21, 22, 23)]
    _near(got[:36], [V[i] for i in kept], 1e-4)      # 20 and 35 took in a new vertex: halfway, 0.00002 away
    _near(got[36:], [[0.951057, 0.687162, -0.309017], [0.61937, 1.0, -0.449999], [0.809017, 0.768469, -0.587786],
                     [0.449999, 1.0, -0.61937], [0.587786, 0.768469, -0.809017], [0.309017, 0.687162, -0.951057]])
    assert faces[0] == {3, 4, 20, 41} and faces[20] == {39, 40, 41, 20} and len(faces) == 25, (faces[0], faces[20])


CUBE_V = [[-0.5, -0.5, 0.5], [0.5, -0.5, 0.5], [-0.5, 0.5, 0.5], [0.5, 0.5, 0.5], [-0.5, 0.5, -0.5], [0.5, 0.5, -0.5],
          [-0.5, -0.5, -0.5], [0.5, -0.5, -0.5]]
CUBE_F = [[0, 1, 3, 2], [2, 3, 5, 4], [4, 5, 7, 6], [6, 7, 1, 0], [1, 7, 5, 3], [6, 0, 2, 4]]
CUBE_E = [[0, 1], [2, 3], [4, 5], [6, 7], [0, 2], [1, 3], [2, 4], [3, 5], [4, 6], [5, 7], [6, 0], [7, 1]]


def test_face_order_at_chain_ends():
    """A lone cube edge and a lone rim edge of a fan-capped cylinder: old faces keep their order, except a face whose
    vertex list starts at a chain end (without that end's bevelled edge), which goes after the others; then the bevel
    face and the end faces."""
    got, faces, _made = _bevel(CUBE_V, CUBE_F, CUBE_E, [0])
    _near(got, [[-0.5, 0.5, 0.5], [0.5, 0.5, 0.5], [-0.5, 0.5, -0.5], [0.5, 0.5, -0.5], [-0.5, -0.5, -0.5],
                [0.5, -0.5, -0.5], [-0.5, -0.5, 5e-05], [-0.5, -5e-05, 0.5], [0.5, -0.5, 5e-05], [0.5, -5e-05, 0.5]])
    assert faces == [{7, 9, 1, 0}, {0, 1, 3, 2}, {2, 3, 5, 4}, {4, 5, 8, 6}, {4, 6, 7, 0, 2}, {9, 8, 5, 3, 1},
                     {7, 6, 8, 9}], faces
    got, faces, _made = _bevel(*_cylinder(), [20])
    assert len(got) == 46 and len(faces) == 63, (len(got), len(faces))
    _near(got[40:], [[0.738052, 1.0, -0.239808], [0.975526, 1.0, -0.154524], [0.951057, 0.77879, -0.309017],
                     [0.627824, 1.0, -0.456141], [0.809017, 0.77879, -0.587786], [0.698413, 1.0, -0.69839]])
    want = ([{0, 1, 44, 42}, {1, 2, 20, 45, 44}] + [{i, i + 1, 19 + i, 18 + i} for i in range(2, 19)]
            + [{19, 0, 42, 41, 37}] + [{(i + 1) % 20, i, 38} for i in range(20)] + [{40, 43, 39}]
            + [{18 + i, 19 + i, 39} for i in range(2, 19)]
            + [{37, 41, 40, 39}, {43, 45, 20, 39}, {40, 42, 44, 43}, {40, 41, 42}, {43, 44, 45}])
    assert faces == want, [(i, f, w) for i, (f, w) in enumerate(zip(faces, want)) if f != w][:4]
