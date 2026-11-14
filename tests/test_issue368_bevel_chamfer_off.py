"""#368: Chamfer off inserts support edges without cutting away the original surface."""

from importlib import import_module

import bmesh
import bpy
from mathutils import Matrix

import kit

bev = import_module(kit.MODULE + ".operators.bevel_maya")


def test_support_edges_preserve_the_surface_and_corners():
    for shear in (0.0, 0.35):
        transform = Matrix(((1.0, shear, 0.0), (0.0, 1.5, shear), (0.0, 0.0, 2.0)))
        inverse = transform.inverted()
        for count in (1, 2, 3, 12):
            for segments in (1, 2, 3, 4):
                for fraction in (False, True):
                    bm = bmesh.new()
                    try:
                        bmesh.ops.create_cube(bm, size=2.0)
                        bmesh.ops.transform(bm, matrix=transform.to_4x4(), verts=bm.verts)
                        bm.normal_update()
                        corners = [v.co.copy() for v in bm.verts]
                        volume = bm.calc_volume()
                        tip = max(bm.verts, key=lambda v: sum(v.co))
                        edges = list(bm.edges) if count == 12 else list(tip.link_edges)[:count]
                        label = (shear, count, segments, fraction)
                        assert bev.bevel_edges(bm, edges, offset_as_fraction=fraction, fraction=0.2,
                                               offset=0.2, segments=segments, chamfer=False), label
                        assert all(e.is_manifold for e in bm.edges), label
                        assert all(f.calc_area() > 1e-8 for f in bm.faces), label
                        assert abs(bm.calc_volume() - volume) < 1e-4, (label, bm.calc_volume(), volume)
                        for corner in corners:
                            assert min((v.co - corner).length for v in bm.verts) < 1e-5, (label, tuple(corner))
                        # Every new face remains on one of the six original face planes.
                        for face in bm.faces:
                            points = [inverse @ v.co for v in face.verts]
                            assert any(all(abs(p[axis] - sign) < 1e-5 for p in points)
                                       for axis in range(3) for sign in (-1, 1)), label
                    finally:
                        bm.free()


def test_history_chamfer_toggle_rebuilds_support_edges():
    extrude = import_module(kit.MODULE + ".operators.extrude")
    bpy.ops.wm.read_homefile(use_empty=True)
    extrude.clear()
    bpy.ops.allset.create(kind='CUBE')
    ob = bpy.context.active_object
    corners = [v.co.copy() for v in ob.data.vertices]
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='EDGE')
    bpy.ops.mesh.select_all(action='SELECT')
    assert bpy.ops.allset.bevel(fraction=0.2) == {'FINISHED'}
    node_name = extrude.RECORDS[ob.name].name
    bm = bmesh.from_edit_mesh(ob.data)
    assert bm.calc_volume() < 0.99
    for depth, segments in ((1.0, 1), (0.0, 2), (-1.0, 3)):
        assert bpy.ops.allset.bevel_edit(chamfer=False, depth=depth, segments=segments) == {'FINISHED'}
        bm = bmesh.from_edit_mesh(ob.data)
        assert abs(bm.calc_volume() - 1.0) < 1e-5
        assert all(min((v.co - c).length for v in bm.verts) < 1e-5 for c in corners)
        assert extrude.RECORDS[ob.name].name == node_name
    assert bpy.ops.allset.bevel_edit(chamfer=True, depth=1.0) == {'FINISHED'}
    assert bmesh.from_edit_mesh(ob.data).calc_volume() < 0.99
