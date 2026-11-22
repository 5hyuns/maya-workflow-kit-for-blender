"""#444: Edit Mesh > Extrude with edges and a curve selected (Curve: Selected) extrudes the edges along the curve in
Divisions steps, like faces: step k puts the edges' centre (the mean of their midpoints) on the curve point at
parameter k / N, turned with the path, tapered and twisted; the node is a polyExtrudeEdge that stays editable.
Faces and edges turn on from the previous step's direction at every step (the turns add up along the path)."""

from importlib import import_module

import bmesh
import bpy
from mathutils import Matrix, Vector

import kit

extrude = import_module(kit.MODULE + ".operators.extrude")
ec = import_module(kit.MODULE + ".operators.extrude_curve")
cmaya = import_module(kit.MODULE + ".operators.curves_maya")


def _reset():
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for cu in list(bpy.data.curves):
        bpy.data.curves.remove(cu)
    extrude.clear()
    for k in [k for k in bpy.context.scene.keys() if k.startswith("allset_poly")]:
        del bpy.context.scene[k]


def _scene(path, degree=1):
    """A 2 x 2 plane at z = 0 and a curve through ``path``; edit mode, edge mode, only the plane's -Y border edge
    selected, the curve still selected."""
    _reset()
    c = cmaya.make_cv_curve(bpy.context, list(path), degree)
    c.name = "crv"
    c.select_set(True)
    me = bpy.data.meshes.new("m")
    bm = bmesh.new()
    vs = [bm.verts.new(p) for p in ((-1, -1, 0), (1, -1, 0), (1, 1, 0), (-1, 1, 0))]
    bm.faces.new(vs)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("mesh", me)
    bpy.context.scene.collection.objects.link(ob)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.scene.tool_settings.mesh_select_mode = (False, True, False)
    bm = bmesh.from_edit_mesh(ob.data)
    for el in (*bm.verts, *bm.edges, *bm.faces):
        el.select = False
    for e in bm.edges:
        if all(abs(v.co.y + 1) < 1e-6 for v in e.verts):
            e.select_set(True)
    bmesh.update_edit_mesh(ob.data)
    return ob


def _new_verts(ob):
    bm = bmesh.from_edit_mesh(ob.data)
    return [v.co.copy() for v in bm.verts if v.index >= 4]


def _pairs(points):
    """The new vertices in pairs of the same step: [(midpoint, half-span vector)] sorted by distance from the
    start of the path."""
    pts = sorted(points, key=lambda p: (p.z, p.x))
    out = []
    used = set()
    for i, p in enumerate(pts):
        if i in used:
            continue
        j = min((j for j in range(len(pts)) if j != i and j not in used), key=lambda j: (pts[j] - p).length
                if abs((pts[j] - p).length - 2.0) < 1e-3 else 1e9)
        used |= {i, j}
        out.append(((p + pts[j]) / 2, (pts[j] - p) / 2))
    return out


def test_edges_follow_the_curve():
    # a straight path far from the plane, going up: 3 steps land on the curve points at 1/3, 2/3, 1
    path = [(5, 0, 0), (5, 0, 3)]
    ob = _scene(path)
    r = bpy.ops.allset.extrude(divisions=3, curve='SELECTED')
    assert r == {'FINISHED'}, r
    new = _new_verts(ob)
    assert len(new) == 6, new
    mids = sorted((m for m, _h in _pairs(new)), key=lambda m: m.z)
    for k, m in enumerate(mids, 1):
        want = Vector((5, 0, k))
        assert (m - want).length < 1e-4, (k, m, want)
    rec = extrude.RECORDS.get(ob.name)
    assert rec is not None and rec.spec is ec.EDGE_SPEC and rec.name.startswith("polyExtrudeEdge"), rec
    bm = bmesh.from_edit_mesh(ob.data)
    sel = [e for e in bm.edges if e.select]
    assert len(sel) == 1 and all(v.co.z > 2.9 for v in sel[0].verts), [tuple(v.co) for e in sel for v in e.verts]


def test_taper_and_twist_and_edit():
    ob = _scene([(0, -1, 0), (0, -1, 4)])
    assert bpy.ops.allset.extrude(divisions=2, curve='SELECTED', taper=0.5, twist=90.0) == {'FINISHED'}
    pairs = sorted(_pairs_any(_new_verts(ob)), key=lambda p: p[0].z)
    (m1, h1), (m2, h2) = pairs
    assert abs(h1.length - 0.75) < 1e-4 and abs(h2.length - 0.5) < 1e-4, (h1, h2)
    # Twist 90 at the end: the last pair's span has turned a quarter turn about the path (up)
    assert abs(h2.normalized().dot(Vector((1, 0, 0)))) < 1e-4, h2
    # the node changes afterwards
    assert bpy.ops.allset.extrude_curve_edit(divisions=4, taper=1.0, twist=0.0, curve="crv") == {'FINISHED'}
    new = _new_verts(ob)
    assert len(new) == 8, len(new)
    assert max(p.z for p in new) > 3.99


def _pairs_any(points):
    """Pairs of the same step for spans of any length: the two vertices at the same height."""
    by_z = {}
    for p in points:
        by_z.setdefault(round(p.z, 4), []).append(p)
    out = []
    for z, ps in by_z.items():
        assert len(ps) == 2, (z, ps)
        out.append(((ps[0] + ps[1]) / 2, (ps[1] - ps[0]) / 2))
    return out


def test_curve_none_extrudes_straight():
    ob = _scene([(5, 0, 0), (5, 0, 3)])
    assert bpy.ops.allset.extrude(divisions=2, curve='NONE') == {'FINISHED'}
    rec = extrude.RECORDS.get(ob.name)
    assert rec is not None and rec.spec is not ec.EDGE_SPEC, rec
    assert all(abs(p.x) <= 1 + 1e-6 for p in _new_verts(ob))


def test_turns_add_up_along_the_path():
    """Three straight chords (up, then +X, then +Y): each step turns on from the previous chord, so the third step's
    frame is the chain of the three smallest turns, not one turn from the normal."""
    normal = Vector((0, 0, 1))
    pts = [Vector((0, 0, 1)), Vector((1, 0, 1)), Vector((1, 1, 1))]
    centre = Vector((0, 0, 0))
    base = Vector((1, 0, 0))
    out = ec.place([(centre, normal, [(k, k, base) for k in (1, 2, 3)])], pts, 3)
    chords = [pts[0] - centre, pts[1] - pts[0], pts[2] - pts[1]]
    turn, heading = Matrix.Identity(3), normal
    for k, c in enumerate(chords, 1):
        turn = heading.rotation_difference(c.normalized()).to_matrix() @ turn
        heading = c.normalized()
        want = pts[k - 1] + turn @ (base - centre)
        assert (out[k] - want).length < 1e-6, (k, out[k], want)
    # one turn from the normal straight onto the last chord would leave the offset elsewhere
    direct = pts[2] + normal.rotation_difference(chords[2].normalized()).to_matrix() @ (base - centre)
    assert (out[3] - direct).length > 0.1, (out[3], direct)
