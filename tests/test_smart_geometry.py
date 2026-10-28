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
