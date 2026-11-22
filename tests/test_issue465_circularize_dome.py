"""#465: Edit Mesh > Circularize on a block of faces of a domed plane: the circle lies in the plane through the mean of
all the selected faces' vertices, and the vertices inside the block move onto that plane (they no longer stick out
of the circle). The border vertices end up evenly spread on the circle; faces outside the block stay."""
import math

import bmesh
import bpy


def _dome(x, y):
    return 0.6 - 0.1 * (x * x + y * y) + 0.03 * x


def _plane(n=4, size=4.0, block=1.01):
    """An n x n plane of ``size`` lifted onto a dome, in edit mode with the faces whose centre is within ``block``
    of the middle selected. Returns (object, {index: co before})."""
    bpy.ops.wm.read_homefile(use_empty=True)
    me = bpy.data.meshes.new("dome")
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=n, y_segments=n, size=size / 2)
    for v in bm.verts:
        v.co.z = _dome(v.co.x, v.co.y)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("dome", me)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    for p in me.polygons:
        p.select = abs(p.center.x) < block and abs(p.center.y) < block
    picked = {i for p in me.polygons if p.select for i in p.vertices}
    for v in me.vertices:
        v.select = v.index in picked
    for e in me.edges:
        e.select = all(i in picked for i in e.vertices)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='FACE')
    bpy.ops.object.mode_set(mode='OBJECT')
    return ob, {v.index: v.co.copy() for v in me.vertices}


def _run(ob):
    bpy.ops.object.mode_set(mode='EDIT')
    r = bpy.ops.allset.circularize()
    bpy.ops.object.mode_set(mode='OBJECT')
    assert r == {'FINISHED'}, r


def _block(ob):
    me = ob.data
    sel = [p for p in me.polygons if p.select]
    verts = {i for p in sel for i in p.vertices}
    count = {}
    for p in sel:
        for k in p.edge_keys:
            count[k] = count.get(k, 0) + 1
    border = {i for k, c in count.items() if c == 1 for i in k}
    return verts, border


def _check(ob, before):
    me = ob.data
    verts, border = _block(ob)
    inner = verts - border
    assert inner, "the block has inner vertices"
    centre = sum((before[i] for i in verts), before[0] * 0) / len(verts)
    pts = [me.vertices[i].co for i in border]
    # the circle's centre is the mean of all the block's vertices (before)
    mid = sum(pts, pts[0] * 0) / len(pts)
    assert (mid - centre).length < 1e-5, (mid, centre)
    # every vertex of the block (border and inner) lies in one plane
    a, b = pts[0] - mid, pts[len(pts) // 4] - mid
    normal = a.cross(b).normalized()
    for i in verts:
        d = (me.vertices[i].co - mid).dot(normal)
        assert abs(d) < 1e-5, ("off the circle's plane", i, d)
    # evenly spread on one circle
    radii = [(p - mid).length for p in pts]
    assert max(radii) - min(radii) < 1e-5, radii
    u = a.normalized()
    w = normal.cross(u)
    angs = sorted(math.atan2((p - mid).dot(w), (p - mid).dot(u)) % math.tau for p in pts)
    steps = [(angs[(k + 1) % len(angs)] - angs[k]) % math.tau for k in range(len(angs))]
    assert max(steps) - min(steps) < 1e-4, steps
    # outside the block nothing moves
    for v in me.vertices:
        if v.index not in verts:
            assert (v.co - before[v.index]).length < 1e-9, v.index


def test_four_faces():
    ob, before = _plane()
    _run(ob)
    _check(ob, before)


def test_three_by_three_block():
    ob, before = _plane(n=6, size=6.0, block=1.51)
    _run(ob)
    _check(ob, before)
