"""Edge bevels keep every new edge at any scene unit: the merge tolerance after a bevel is a Maya length (0.0001 in
the scene's unit), so a small bevel in a centimetre scene no longer welds its new vertices away (issue #321)."""

from importlib import import_module

import bmesh
import bpy
from mathutils import Matrix

import kit

bev = import_module(kit.MODULE + ".operators.bevel_maya")


def _cube(bm):
    bmesh.ops.create_cube(bm, size=1.0)


def _cylinder(bm):
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=20, radius1=0.5, radius2=0.5, depth=2.0)


def _sphere(bm):
    bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=10, radius=1.0)


def _grid(bm):
    bmesh.ops.create_grid(bm, x_segments=4, y_segments=4, size=1.0)


def _prism(bm):
    """An octagonal prism: two 8-sided n-gon caps."""
    bmesh.ops.create_circle(bm, cap_ends=True, segments=8, radius=1.0)
    ret = bmesh.ops.extrude_face_region(bm, geom=list(bm.faces))
    bmesh.ops.translate(bm, vec=(0, 0, 1.0), verts=[g for g in ret["geom"] if isinstance(g, bmesh.types.BMVert)])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)


def _inner(bm):
    return [e for e in bm.edges if len(e.link_faces) == 2]


def _flat(e):
    return abs(e.verts[0].co.z - e.verts[1].co.z) < 1e-9


SELECTIONS = {   # name: (shape, edges to bevel)
    "cube edge": (_cube, lambda bm: _inner(bm)[:1]),
    "cube corner": (_cube, lambda bm: list(bm.verts[0].link_edges)),
    "cube all": (_cube, _inner),
    "cylinder side": (_cylinder, lambda bm: [e for e in _inner(bm) if not _flat(e)][:1]),
    "cylinder cap": (_cylinder, lambda bm: [e for e in _inner(bm) if _flat(e) and e.verts[0].co.z > 0.0]),
    "cylinder cap + side": (_cylinder, lambda bm: [e for e in _inner(bm) if _flat(e) and e.verts[0].co.z > 0.0]
                            + [e for e in _inner(bm) if not _flat(e)][:1]),
    "sphere pole": (_sphere, lambda bm: list(max(bm.verts, key=lambda v: v.co.z).link_edges)),
    "grid chain ending inside": (_grid, lambda bm: _chain(bm)),
    "prism n-gon caps": (_prism, _inner),
}


def _chain(bm):
    """Two edges in a row from the grid's middle vertex: the chain ends inside the mesh."""
    c = min(bm.verts, key=lambda v: v.co.length)
    first = c.link_edges[0]
    o = first.other_vert(c)
    d = (o.co - c.co).normalized()
    nxt = next(e for e in o.link_edges if e is not first and (e.other_vert(o).co - o.co).normalized().dot(d) > 0.999)
    return [first, nxt]


def _bevel(name, unit, fraction, segments, scale=(1.0, 1.0, 1.0)):
    """Vertex / edge / face counts after bevelling ``name`` built at ``unit`` (Blender units per Maya unit)."""
    shape, pick = SELECTIONS[name]
    bm = bmesh.new()
    try:
        shape(bm)
        bmesh.ops.transform(bm, matrix=Matrix.Diagonal((*(unit * s for s in scale), 1.0)), verts=bm.verts)
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        edges = pick(bm)
        for e in bm.edges:
            e.select = e in edges
        assert bev.bevel_edges(bm, edges, fraction=fraction, segments=segments, unit=unit), name
        return len(bm.verts), len(bm.edges), len(bm.faces)
    finally:
        bm.free()


def test_same_result_in_metres_and_centimetres():
    """The same Maya mesh and bevel in a metre scene (1 Maya unit = 1) and a centimetre scene (0.01) gives the same
    topology; before, small bevels in the centimetre scene lost new edges to the merge."""
    bad = []
    for name in SELECTIONS:
        for fraction in (0.5, 0.1, 0.02):
            for segments in (1, 3):
                for scale in ((1.0, 1.0, 1.0), (1.0, 5.0, 0.2)):
                    m = _bevel(name, 1.0, fraction, segments, scale)
                    cm = _bevel(name, 0.01, fraction, segments, scale)
                    # the squashed sphere's pole: rounding at 1/100 the size can change one edge pair
                    if m != cm and not (name == "sphere pole" and m[0] == cm[0] and abs(m[1] - cm[1]) <= 2):
                        bad.append((name, fraction, segments, scale, m, cm))
    assert not bad, bad[:5]


def test_small_bevel_keeps_its_edges():
    """Fraction 0.02 on a 1 cm cube edge: one new face, two new edges at each end (it used to weld back into
    the plain cube)."""
    assert _bevel("cube edge", 0.01, 0.02, 1) == (10, 15, 7)
    assert _bevel("cube edge", 0.01, 0.02, 1, (1.0, 5.0, 0.2)) == (10, 15, 7)
    assert _bevel("cylinder side", 0.01, 0.1, 3) == _bevel("cylinder side", 1.0, 0.1, 3)


def test_operator_in_a_centimetre_scene():
    """Edit Mesh > Bevel (allset.bevel) in a centimetre scene keeps the new edges of a small bevel."""
    sc = bpy.context.scene
    us = sc.unit_settings
    us.system, us.length_unit, us.scale_length = 'METRIC', 'CENTIMETERS', 1.0
    try:
        for ob in list(bpy.data.objects):
            bpy.data.objects.remove(ob)
        bpy.ops.mesh.primitive_cube_add(size=0.01)
        ob = bpy.context.active_object
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='EDGE')
        bm = bmesh.from_edit_mesh(ob.data)
        for e in bm.edges:
            e.select = False
        bm.edges.ensure_lookup_table()
        bm.edges[0].select = True
        bm.select_flush_mode()
        bmesh.update_edit_mesh(ob.data)
        assert bpy.ops.allset.bevel(fraction=0.01) == {"FINISHED"}
        bm = bmesh.from_edit_mesh(ob.data)
        assert (len(bm.verts), len(bm.edges), len(bm.faces)) == (10, 15, 7), (len(bm.verts), len(bm.edges))
        bpy.ops.object.mode_set(mode='OBJECT')
    finally:
        us.length_unit, us.system = 'METERS', 'METRIC'
