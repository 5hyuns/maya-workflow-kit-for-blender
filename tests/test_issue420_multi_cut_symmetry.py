"""Multi-Cut with symmetry on (GitHub #420): cuts, Ctrl+click edge loops and slices are made on both sides.
GUI: tests/gui/gui_issue420_multi_cut_symmetry.py."""

import math
from importlib import import_module

import bmesh
import bpy
from mathutils import Vector

import kit

mc = import_module(kit.MODULE + ".operators.multi_cut")
mcm = import_module(kit.MODULE + ".operators.multi_cut_mirror")
qds = import_module(kit.MODULE + ".operators.quad_draw_symmetry")
symmetry = import_module(kit.MODULE + ".operators.symmetry")

XS = (-2.0, -1.0, 0.0, 1.0, 2.0)


def _strip(bm=None, ys=(0.0, 1.0)):
    """A strip of 4 quads along X, symmetric about x = 0 (z = 0)."""
    bm = bm or bmesh.new()
    rows = [[bm.verts.new((x, y, 0.0)) for x in XS] for y in ys]
    for j in range(len(ys) - 1):
        for i in range(len(XS) - 1):
            bm.faces.new((rows[j][i], rows[j][i + 1], rows[j + 1][i + 1], rows[j + 1][i]))
    for seq in (bm.verts, bm.edges, bm.faces):
        seq.index_update()
        seq.ensure_lookup_table()
    return bm


def _counts(bm):
    return len(bm.verts), len(bm.edges), len(bm.faces)


def _has(bm, co):
    return any((v.co - Vector(co)).length < 1e-5 for v in bm.verts)


def _vert(bm, co):
    return next(v for v in bm.verts if (v.co - Vector(co)).length < 1e-5)


def _edge_point(bm, a, b, t_from_a):
    va, vb = _vert(bm, a), _vert(bm, b)
    e = next(e for e in va.link_edges if vb in e.verts)
    return ('EDGE', e.index, t_from_a if e.verts[0] is va else 1.0 - t_from_a)


def _x_mirror(bm):
    return mcm.Mirror(bm, matrix=qds.reflection(None, 'OBJECT', 0))


def test_cut_is_mirrored_by_position():
    bm = _strip()
    pts = [_edge_point(bm, (1, 0, 0), (1, 1, 0), 0.25), _edge_point(bm, (2, 0, 0), (2, 1, 0), 0.5)]
    other = _x_mirror(bm).path(pts)
    assert other is not None
    mc.cut(bm, pts, mirrored=other)
    assert _counts(bm) == (14, 19, 6), _counts(bm)        # two cuts: 10/13/4 + 2 x (2 v, 3 e, 1 f)
    for co in ((1, .25, 0), (2, .5, 0), (-1, .25, 0), (-2, .5, 0)):
        assert _has(bm, co), co
    bm.free()


def test_face_points_are_mirrored():
    bm = _strip()
    f = next(f for f in bm.faces if abs(f.calc_center_median().x - 1.5) < 1e-6)
    pts = [_edge_point(bm, (1, 0, 0), (1, 1, 0), 0.5), ('FACE', f.index, (1.6, 0.3, 0.0)),
           _edge_point(bm, (2, 0, 0), (2, 1, 0), 0.5)]
    mc.cut(bm, pts, mirrored=_x_mirror(bm).path(pts))
    assert _has(bm, (1.6, .3, 0)) and _has(bm, (-1.6, .3, 0))
    assert _counts(bm) == (16, 21, 6), _counts(bm)
    bm.free()


def test_a_cut_that_is_its_own_mirror_is_made_once():
    bm = _strip()
    pts = [_edge_point(bm, (-1, 0, 0), (-1, 1, 0), 0.5), _edge_point(bm, (0, 0, 0), (0, 1, 0), 0.5),
           _edge_point(bm, (1, 0, 0), (1, 1, 0), 0.5)]
    assert _x_mirror(bm).path(pts) is None
    mc.cut(bm, pts, mirrored=_x_mirror(bm).path(pts))
    assert _counts(bm) == (13, 18, 6), _counts(bm)
    bm.free()


def test_a_cut_across_the_plane_gets_its_mirror_too():
    bm = _strip()
    pts = [_edge_point(bm, (-1, 0, 0), (-1, 1, 0), 0.25), _edge_point(bm, (0, 0, 0), (0, 1, 0), 0.5),
           _edge_point(bm, (1, 0, 0), (1, 1, 0), 0.5)]
    other = _x_mirror(bm).path(pts)
    assert other is not None
    mc.cut(bm, pts, mirrored=other)
    for co in ((-1, .25, 0), (1, .25, 0), (-1, .5, 0), (1, .5, 0), (0, .5, 0)):
        assert _has(bm, co), co
    bm.free()


def test_no_partner_means_no_mirrored_cut():
    bm = _strip()
    _vert(bm, (-2, 1, 0)).co.x = -2.5                # the left end is not symmetric any more
    bm.verts.ensure_lookup_table()
    pts = [_edge_point(bm, (1, 0, 0), (1, 1, 0), 0.5), _edge_point(bm, (2, 0, 0), (2, 1, 0), 0.5)]
    assert _x_mirror(bm).path(pts) is None
    bm.free()


def test_topology_symmetry_mirrors_by_the_mesh_pairs():
    bm = _strip()
    for v in bm.verts:                               # bend the right side: no longer mirrored by position
        if v.co.x > 0.5:
            v.co.z = 0.3 * v.co.x
    seam = bm.edges.get((_vert(bm, (0, 0, 0)), _vert(bm, (0, 1, 0))))
    pairs = qds.topology_pairs(bm, [seam])
    assert pairs
    mirror = mcm.Mirror(bm, pairs=pairs)
    pts = [_edge_point(bm, (-1, 0, 0), (-1, 1, 0), 0.25), _edge_point(bm, (-2, 0, 0), (-2, 1, 0), 0.5)]
    other = mirror.path(pts)
    assert other is not None
    mc.cut(bm, pts, mirrored=other)
    assert _counts(bm) == (14, 19, 6), _counts(bm)
    assert _has(bm, (1, .25, .3)) and _has(bm, (2, .5, .6))
    bm.free()


def test_loop_is_mirrored_and_a_symmetric_loop_is_made_once():
    bm = _strip(ys=(0.0, 1.0, 2.0))
    # a loop through the ring of the bottom edge of the right-hand quad column = a vertical loop at x = 1.25
    bottom = bm.edges.get((_vert(bm, (1, 0, 0)), _vert(bm, (2, 0, 0))))
    t = 0.25 if bottom.verts[0].co.x < 1.5 else 0.75
    mc.loop(bm, bottom.index, t, mirror=_x_mirror(bm))
    assert _has(bm, (1.25, 0, 0)) and _has(bm, (-1.25, 0, 0)) and _has(bm, (-1.25, 2, 0))
    assert _counts(bm) == (21, 32, 12), _counts(bm)
    bm.free()
    bm = _strip()
    # a loop through the vertical edges = one horizontal loop across the plane: its own mirror
    side = bm.edges.get((_vert(bm, (1, 0, 0)), _vert(bm, (1, 1, 0))))
    mc.loop(bm, side.index, 0.5, mirror=_x_mirror(bm))
    assert _counts(bm) == (15, 22, 8), _counts(bm)
    bm.free()


def test_slice_is_mirrored():
    bm = _strip()
    mc.slice_mirrored(bm, Vector((1.5, 0, 0)), Vector((1, 0, 0)), lambda b: list(b.faces), _x_mirror(bm))
    assert _has(bm, (1.5, 0, 0)) and _has(bm, (-1.5, 0, 0))
    assert _counts(bm) == (14, 19, 6), _counts(bm)
    bm.free()
    bm = _strip()                                    # the plane of symmetry itself: once
    mc.slice_mirrored(bm, Vector((0.5, 0.5, 0)), Vector((0, 1, 0)), lambda b: list(b.faces), _x_mirror(bm))
    assert _counts(bm) == (15, 22, 8), _counts(bm)
    bm.free()


def _edit_strip(location=(0, 0, 0)):
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    me = bpy.data.meshes.new("strip")
    bm = _strip()
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("strip", me)
    ob.location = location
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    return ob


def _set_symmetry(mode):
    symmetry.set_mode(bpy.context.scene.allset_symmetry, mode)


def test_tool_completion_follows_the_symmetry_state():
    try:
        for mode, location, mirrored in (("OFF", (0, 0, 0), False), ("OBJECT_X", (3, 0, 0), True),
                                         ("WORLD_X", (0, 0, 0), True), ("WORLD_X", (0.5, 0, 0), False),
                                         ("TOPOLOGY", (0, 0, 0), True), ("OBJECT_Y", (0, 0, 0), False)):
            _set_symmetry(mode)
            ob = _edit_strip(location)
            bm = bmesh.from_edit_mesh(ob.data)
            bm.edges.ensure_lookup_table()
            pts = [_edge_point(bm, (1, 0, 0), (1, 1, 0), 0.25), _edge_point(bm, (2, 0, 0), (2, 1, 0), 0.5)]
            assert mc.complete(bpy.context, ob, pts)
            bm = bmesh.from_edit_mesh(ob.data)
            want = (14, 19, 6) if mirrored else (12, 16, 5)
            assert _counts(bm) == want, (mode, location, _counts(bm))
            bpy.ops.object.mode_set(mode='OBJECT')
    finally:
        _set_symmetry("OFF")


def test_ctrl_click_loop_operator_is_mirrored():
    try:
        _set_symmetry("OBJECT_X")
        ob = _edit_strip()
        bm = bmesh.from_edit_mesh(ob.data)
        bottom = bm.edges.get((_vert(bm, (1, 0, 0)), _vert(bm, (2, 0, 0))))
        t = 0.25 if bottom.verts[0].co.x < 1.5 else 0.75
        assert bpy.ops.allset.multicut_loop(object=ob.name, edge=bottom.index, factor=t) == {'FINISHED'}
        bm = bmesh.from_edit_mesh(ob.data)
        assert _has(bm, (1.25, 0, 0)) and _has(bm, (-1.25, 0, 0)), "the mirrored loop"
        assert _counts(bm) == (14, 19, 6), _counts(bm)
        bpy.ops.object.mode_set(mode='OBJECT')
    finally:
        _set_symmetry("OFF")
