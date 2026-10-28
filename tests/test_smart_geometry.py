"""Modern Smart Extrude: volumes and topology, not just extrusion face counts."""
from importlib import import_module

import bmesh
import bpy
from mathutils import Matrix, Vector
from kit import MODULE


def module():
    return import_module(MODULE + '.operators.smart_geometry')


def cube():
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=2)
    bm.normal_update()
    bm.faces.index_update()
    return bm


def run(pre, offset, volume, faces=None):
    pre.faces.index_update()
    ids = faces if faces is not None else [max(pre.faces, key=lambda f: f.calc_center_median().z).index]
    result = module().sweep(bpy.context, pre, ids, [Matrix.Translation(offset)])
    try:
        assert abs(result.calc_volume() - volume) < 1e-4, (result.calc_volume(), volume)
        assert all(e.is_manifold and e.is_contiguous for e in result.edges)
        return result.copy()
    finally:
        result.free()


def test_outward_and_inward():
    bm = cube()
    try:
        run(bm, (0, 0, 1), 12).free()
        run(bm, (0, 0, -.5), 6).free()
    finally:
        bm.free()


def test_complete_through_rejected_without_mutation():
    bm = cube()
    try:
        try:
            run(bm, (0, 0, -3), 0)
        except module().GeometryError:
            pass
        else:
            raise AssertionError('a transform removing the entire mesh must be rejected')
        assert len(bm.faces) == 6 and abs(bm.calc_volume() - 8) < 1e-6
    finally:
        bm.free()


def inset_patch(bm):
    top = max(bm.faces, key=lambda f: f.calc_center_median().z)
    bmesh.ops.inset_region(bm, faces=[top], thickness=.5, depth=0, use_even_offset=True)
    bm.faces.index_update()
    return min((f for f in bm.faces if f.calc_center_median().z > .99),
               key=lambda f: f.calc_center_median().xy.length).index


def test_pocket_and_through_hole():
    bm = cube()
    try:
        face = inset_patch(bm)
        # centre is a 1x1 patch: no hidden internal cap after passing through.
        run(bm, (0, 0, -.5), 7.5, [face]).free()
        result = run(bm, (0, 0, -3), 6, [face])
        assert not any(abs(f.calc_center_median().z+2) < 1e-6 for f in result.faces)
        result.free()
    finally:
        bm.free()


def test_disconnected_shell_union():
    bm = cube()
    try:
        face = max(bm.faces, key=lambda f: f.calc_center_median().z)
        other = bmesh.ops.create_cube(bm, size=2)['verts']
        bmesh.ops.translate(bm, verts=other, vec=Vector((0, 0, 3)))
        bm.normal_update()
        bm.faces.index_update()
        run(bm, (0, 0, 3), 20, [face.index]).free()
    finally:
        bm.free()


def test_inward_corner_region():
    bm = cube()
    try:
        faces = [f.index for f in bm.faces if f.normal.x > .99 or f.normal.z > .99]
        run(bm, (-.5, 0, -.5), 4.5, faces).free()
    finally:
        bm.free()


def test_concave_multiface_region():
    bm = cube()
    try:
        top = max(bm.faces, key=lambda f: f.calc_center_median().z)
        bmesh.ops.subdivide_edges(bm, edges=list(top.edges), cuts=1, use_grid_fill=True)
        bm.normal_update()
        bm.faces.index_update()
        faces = [f.index for f in bm.faces if f.calc_center_median().z > .99
                 and not (f.calc_center_median().x > 0 and f.calc_center_median().y > 0)]
        assert len(faces) == 3
        run(bm, (0, 0, .5), 9.5, faces).free()
        run(bm, (0, 0, -.5), 6.5, faces).free()
        run(bm, (0, 0, -3), 2, faces).free()
    finally:
        bm.free()


def test_partial_through_side_and_bottom():
    bm = cube()
    try:
        face = inset_patch(bm)
        run(bm, (1, 0, -3), 145/24, [face]).free()
    finally:
        bm.free()


def test_cut_through_disconnected_shells():
    bm = cube()
    try:
        face = inset_patch(bm)
        selected = next(f for f in bm.faces if f.index == face)
        other = bmesh.ops.create_cube(bm, size=2)['verts']
        bmesh.ops.translate(bm, verts=other, vec=Vector((0, 0, -3)))
        bm.normal_update()
        bm.faces.index_update()
        run(bm, (0, 0, -6), 12, [selected.index]).free()
    finally:
        bm.free()


def test_grid_cut_walls_are_clean_quads_at_and_past_exit():
    for textured in (False, True):
        bm = cube()
        try:
            bmesh.ops.subdivide_edges(bm, edges=list(bm.edges), cuts=2, use_grid_fill=True)
            bm.normal_update()
            bm.faces.index_update()
            if textured:
                uv = bm.loops.layers.uv.new('ArtistUV')
                for f in bm.faces:
                    axes = [i for i in range(3) if abs(f.normal[i]) < .9]
                    for lp in f.loops:
                        lp[uv].uv = tuple(lp.vert.co[i] for i in axes)
            face = min((f for f in bm.faces if f.normal.z > .9), key=lambda f: f.calc_center_median().xy.length)
            for depth in (1., 1.99999, 2., 2.00001, 3., 6.):
                result = run(bm, (0, 0, -depth), 8-(4/9)*min(depth, 2), [face.index])
                try:
                    assert not any(len(f.verts) == 3 for f in result.faces), (textured, depth)
                    assert len(result.faces) <= (58 if depth < 2 else 56), (textured, depth, len(result.faces))
                finally:
                    result.free()
        finally:
            bm.free()


def test_partial_through_rejoins_original_skin_as_concave_ngons():
    bm = cube()
    try:
        face = inset_patch(bm)
        result = run(bm, (1, 0, -3), 145/24, [face])
        try:
            skin = [f for f in result.faces if f.normal.x > .99 and abs(f.calc_center_median().x-1) < 1e-5]
            assert len(skin) == 1 and len(skin[0].verts) >= 6, [len(f.verts) for f in skin]
            assert not any(len(f.verts) == 3 for f in skin)
            assert result.faces.layers.int.get(module().SOURCE) is None
        finally:
            result.free()
    finally:
        bm.free()


def test_perpendicular_tunnels_join_planar_walls_into_ngons():
    for textured in (False, True, 'legacy'):
        bm = cube()
        first = second = None
        try:
            if textured:
                layer = bm.loops.layers.uv.new('ArtistUV')
                for f in bm.faces:
                    axes = [i for i in range(3) if abs(f.normal[i]) < .9]
                    for lp in f.loops:
                        lp[layer].uv = tuple(lp.vert.co[i] for i in axes)
            top = inset_patch(bm)
            first = run(bm, (0, 0, -3), 6, [top])
            if textured == 'legacy':
                first.faces.layers.int.remove(first.faces.layers.int.get(module().SURFACE))
            side = max(first.faces, key=lambda f: f.calc_center_median().x)
            bmesh.ops.inset_region(first, faces=[side], thickness=.5, depth=0, use_even_offset=True)
            first.faces.index_update()
            patch = min((f for f in first.faces if f.normal.x > .99 and f.calc_center_median().x > .99),
                        key=lambda f: f.calc_center_median().yz.length)
            second = run(first, (-3, 0, 0), 5, [patch.index])
            # The two intersecting tunnel walls are crosses with 12 corners,
            # each representable by one concave ngon instead of many strips.
            for y in (-.5, .5):
                walls = [f for f in second.faces if abs(abs(f.normal.y)-1) < 1e-5
                         and all(abs(v.co.y-y) < 1e-5 for v in f.verts)]
                assert len(walls) == 1 and len(walls[0].verts) >= 12, (textured, y, [len(f.verts) for f in walls])
            for axis in (0, 2):
                for sign in (-1, 1):
                    ring = [f for f in second.faces if all(abs(v.co[axis]-sign) < 1e-5 for v in f.verts)]
                    assert len(ring) <= 2, (textured, axis, sign, len(ring))
            assert not any(len(f.verts) == 3 for f in second.faces)
        finally:
            if second is not None:
                second.free()
            if first is not None:
                first.free()
            bm.free()


def test_cleanup_leaves_unaffected_shell_topology():
    bm = cube()
    try:
        top = inset_patch(bm)
        other = bmesh.ops.create_cube(bm, size=2)['verts']
        bmesh.ops.translate(bm, verts=other, vec=Vector((5, 0, 0)))
        bmesh.ops.subdivide_edges(bm, edges=[e for e in bm.edges if all(v.co.x > 3 for v in e.verts)],
                                  cuts=2, use_grid_fill=True)
        bm.normal_update()
        bm.faces.index_update()
        chosen = min((f for f in bm.faces if f.normal.z > .9 and f.calc_center_median().x < 2),
                     key=lambda f: f.calc_center_median().xy.length)
        expected = sorted(sorted(tuple(v.co) for v in f.verts) for f in bm.faces if f.calc_center_median().x > 3)
        result = run(bm, (0, 0, -3), 14, [chosen.index])
        try:
            actual = sorted(sorted(tuple(v.co) for v in f.verts) for f in result.faces if f.calc_center_median().x > 3)
            assert actual == expected
        finally:
            result.free()
    finally:
        bm.free()


def test_cleanup_preserves_explicit_seams_on_the_cut_rim():
    bm = cube()
    try:
        chosen = inset_patch(bm)
        marked = []
        for e in bm.edges:
            if len(e.link_faces) == 2 and all(f.normal.z > .9 for f in e.link_faces):
                if any(f.index == chosen for f in e.link_faces):
                    continue
                e.seam = True
                marked.append(frozenset(tuple(v.co) for v in e.verts))
        assert len(marked) == 4
        result = run(bm, (0, 0, -3), 6, [chosen])
        try:
            actual = {frozenset(tuple(v.co) for v in e.verts) for e in result.edges if e.seam}
            assert all(key in actual for key in marked)
        finally:
            result.free()
    finally:
        bm.free()
