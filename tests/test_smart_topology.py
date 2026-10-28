"""Source-feature preservation, deterministic hole bands and clipped edge lineage."""
from importlib import import_module

import bmesh
import bpy
from mathutils import Matrix, Vector
from kit import MODULE
import smart_reference as reference


def geometry():
    return import_module(MODULE+'.operators.smart_geometry')


def cut(bm, axis, sign, delta):
    return geometry().sweep(bpy.context, bm, [reference.patch(bm, axis, sign)], [Matrix.Translation(delta)])


def test_reference_keeps_all_input_features_and_rebuilds_four_floor_bands():
    pre = reference.mesh()
    first = result = None
    try:
        original = [(tuple(e.verts[0].co), tuple(e.verts[1].co)) for e in pre.edges]
        top = [frozenset(tuple(v.co) for v in f.verts) for f in pre.faces if f.normal.z > .99]
        first = cut(pre, 2, 1, (0, 0, -3))
        assert abs(first.calc_volume()-6) < 1e-5
        after_top = {frozenset(tuple(v.co) for v in f.verts) for f in first.faces if f.normal.z > .99}
        # The selected centre disappears, but every surrounding inset panel stays.
        assert all(face in after_top for face in top if not all(abs(v[0]) <= .50001 and abs(v[1]) <= .50001 for v in face))
        result = cut(first, 1, -1, (0, 3, 0))
        assert abs(result.calc_volume()-2.48) < 1e-4, result.calc_volume()
        assert all(e.is_manifold and e.is_contiguous for e in result.edges)
        for p, q in original:
            assert reference.covered(result, p, q), (p, q)
        for z in (-.8, .8):
            floor = [f for f in result.faces if all(abs(v.co.z-z) < 1e-5 for v in f.verts)]
            assert len(floor) == 4, (z, [len(f.verts) for f in floor])
            for x in (-1, 1):
                for y in (-1, 1):
                    assert reference.covered(result, (.8*x, y, z), (.5*x, .5*y, z)), (x, y, z)
        assert not any(len(f.verts) == 3 for f in result.faces)
    finally:
        if result is not None:
            result.free()
        if first is not None:
            first.free()
        pre.free()


def test_new_inset_edges_are_not_inherited_temporary_connectors():
    pre = reference.mesh()
    first = result = None
    try:
        first = cut(pre, 2, 1, (0, 0, -3))
        old_edges = set(first.edges)
        bottom = min(first.faces, key=lambda f: f.calc_center_median().z)
        bmesh.ops.inset_region(first, faces=[bottom], thickness=.05, depth=0, use_even_offset=True)
        first.normal_update()
        features = [(tuple(e.verts[0].co), tuple(e.verts[1].co)) for e in first.edges if e not in old_edges]
        assert len(features) >= 8  # boundary may also contain collinear stitch vertices
        result = cut(first, 1, -1, (0, 3, 0))
        for p, q in features:
            assert reference.covered(result, p, q), (p, q)
    finally:
        if result is not None:
            result.free()
        if first is not None:
            first.free()
        pre.free()


def test_partial_exit_splits_original_edge_and_keeps_only_surviving_segments():
    pre = reference.mesh()
    result = None
    try:
        result = cut(pre, 2, 1, (1, 0, -3))
        assert reference.covered(result, (1, -1, -1), (1, -.5, -1))
        assert reference.covered(result, (1, .5, -1), (1, 1, -1))
        assert not reference.covered(result, (1, -.4, -1), (1, .4, -1))
        for y in (-.5, .5):
            assert min((v.co-Vector((1, y, -1))).length for v in result.verts) < 1e-5
        assert all(e.is_manifold for e in result.edges)
    finally:
        if result is not None:
            result.free()
        pre.free()


def test_connector_proof_survives_mesh_roundtrip_but_not_edited_endpoints():
    topology = import_module(MODULE+'.operators.smart_topology')
    pre = reference.mesh()
    result = None
    mesh = None
    copy = None
    try:
        result = cut(pre, 2, 1, (0, 0, -3))
        groups = topology.input_panels(result)
        assert len(set(groups.values())) < len(result.faces)
        mesh = bpy.data.meshes.new('.smart_support_roundtrip')
        result.to_mesh(mesh)
        copy = bmesh.new()
        copy.from_mesh(mesh)
        assert len(set(topology.input_panels(copy).values())) == len(set(groups.values()))
        bmesh.ops.translate(copy, verts=list(copy.verts), vec=Vector((.2, 0, 0)))
        assert len(set(topology.input_panels(copy).values())) == len(copy.faces)
    finally:
        if copy is not None:
            copy.free()
        if mesh is not None:
            bpy.data.meshes.remove(mesh)
        if result is not None:
            result.free()
        pre.free()


def test_rebuilt_cap_keeps_source_corner_uvs():
    pre = reference.mesh()
    result = None
    try:
        layer = pre.loops.layers.uv.new('CapUV')
        pre.faces.ensure_lookup_table()
        face = pre.faces[reference.patch(pre, 2, 1)]
        expected = {}
        for i, lp in enumerate(face.loops):
            lp[layer].uv = (.13+i*.17, .29+i*.11)
            expected[tuple(lp.vert.co+Vector((0, 0, .5)))] = tuple(lp[layer].uv)
        result = cut(pre, 2, 1, (0, 0, .5))
        cap = [f for f in result.faces if all(abs(v.co.z-1.5) < 1e-5 for v in f.verts)]
        assert len(cap) == 1 and len(cap[0].verts) == 4
        uv = result.loops.layers.uv.get('CapUV')
        for lp in cap[0].loops:
            coord = min(expected, key=lambda p: (lp.vert.co-Vector(p)).length)
            assert (lp[uv].uv-Vector(expected[coord])).length < 1e-6
    finally:
        if result is not None:
            result.free()
        pre.free()
