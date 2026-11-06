"""Edit Mesh > Bevel with Segments 3 on a right-angle edge: the strip's faces meet at exactly the Smoothing angle
(30 degrees), which is not more than it, so every one of those edges is soft and the strips shade alike. Rounding
used to leave some of them hard, so one strip of a box looked faceted next to a smooth one (#331)."""

import math
from importlib import import_module

import bmesh
import bpy

import kit

bev = import_module(kit.MODULE + ".operators.bevel_maya")


def _box():
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=2.0)
    bmesh.ops.scale(bm, vec=(1.0, 1.0, 1.5), verts=bm.verts)
    bm.normal_update()
    return bm


def _body_edges(bm):
    """The four vertical edges and the four top rim edges of a box."""
    top = max(v.co.z for v in bm.verts)
    return [e for e in bm.edges if abs(e.verts[0].co.z - e.verts[1].co.z) > 1e-6
            or all(abs(v.co.z - top) < 1e-6 for v in e.verts)]


def _angle(e):
    f0, f1 = e.link_faces
    return math.degrees(f0.normal.angle(f1.normal, 0.0))


def _at_angle(bm, angle):
    bm.normal_update()
    return [e for e in bm.edges if len(e.link_faces) == 2 and abs(_angle(e) - angle) < 1e-3]


def test_strip_edges_at_the_smoothing_angle_are_all_soft():
    """Eight box edges, Segments 3: the 16 edges inside the strips meet at 30 degrees and are all soft; the strips'
    outer edges (15 degrees) are soft too, the corner polygons' edges (45) hard."""
    bm = _box()
    assert bev.bevel_edges(bm, _body_edges(bm), segments=3)
    inner = _at_angle(bm, 30.0)
    assert len(inner) == 16, len(inner)
    hard = [e for e in inner if bev.is_hard(e)]
    assert not hard, f"{len(hard)} of {len(inner)} strip edges hard"
    assert not any(bev.is_hard(e) for e in _at_angle(bm, 15.0))
    assert all(bev.is_hard(e) for e in _at_angle(bm, 45.0))
    bm.free()


def test_sixty_degree_edge_in_two_segments():
    """Two faces meeting at 60 degrees, Segments 2: the one edge between the strip's faces meets at 30, so it is
    soft like the strip's outer edges (15)."""
    bm = bmesh.new()
    a, b = bm.verts.new((0.0, 0.0, 0.0)), bm.verts.new((0.0, 2.0, 0.0))
    c, d = bm.verts.new((2.0, 0.0, 0.0)), bm.verts.new((2.0, 2.0, 0.0))
    x, z = 2.0 * math.cos(math.radians(120.0)), 2.0 * math.sin(math.radians(120.0))
    p, q = bm.verts.new((x, 0.0, z)), bm.verts.new((x, 2.0, z))
    bm.faces.new((a, c, d, b))
    bm.faces.new((a, b, q, p))
    bm.normal_update()
    e = bm.edges.get((a, b))
    assert abs(_angle(e) - 60.0) < 1e-3
    assert bev.bevel_edges(bm, [e], segments=2)
    middle = _at_angle(bm, 30.0)
    assert len(middle) == 1, len(middle)
    assert not bev.is_hard(middle[0])
    assert len(_at_angle(bm, 15.0)) == 2 and not any(bev.is_hard(e) for e in _at_angle(bm, 15.0))
    bm.free()


def test_bevel_operator_leaves_the_strips_smooth():
    """Ctrl+B on a cube's vertical and top edges with Segments 3: no strip edge is sharp on the mesh, and the
    object gets Maya's smooth normals."""
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    assert bpy.ops.allset.create(kind='CUBE') == {'FINISHED'}
    ob = bpy.context.view_layer.objects.active
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='EDGE')
    bm = bmesh.from_edit_mesh(ob.data)
    picked = set(_body_edges(bm))
    for e in bm.edges:
        e.select = e in picked
    bm.select_flush_mode()
    bmesh.update_edit_mesh(ob.data)
    assert bpy.ops.allset.bevel(segments=3) == {'FINISHED'}
    bpy.ops.object.mode_set(mode='OBJECT')
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    inner = _at_angle(bm, 30.0)
    assert len(inner) == 16, len(inner)
    assert all(e.smooth for e in inner), sum(not e.smooth for e in inner)
    assert all(f.smooth for f in bm.faces)
    bm.free()
    assert ob.modifiers.get("Maya Normals") is not None
