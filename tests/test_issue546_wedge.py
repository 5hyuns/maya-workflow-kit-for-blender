"""Edit Mesh > Wedge (#546): the selected faces swing around the edge picked for the wedge, lifting toward their
normal, one ring of new vertices per division (90 degrees in 4 divisions ends with the face standing on that edge)."""

import math

import bmesh
import bpy
from mathutils import Vector

import kit


def _cube_top(edge_y=None, edge_x=None):
    """A 2 x 2 x 2 cube in Edit Mode with its top face selected and the top edge at y = ``edge_y`` (or x =
    ``edge_x``) as the active edge."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    kit.enable()
    bpy.ops.mesh.primitive_cube_add(size=2)
    ob = bpy.context.object
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(ob.data)
    for el in (*bm.verts, *bm.edges, *bm.faces):
        el.select = False
    top = next(f for f in bm.faces if f.normal.z > 0.9)
    top.select = True
    for e in top.edges:
        e.select = True
    for v in top.verts:
        v.select = True
    hinge = next(e for e in top.edges
                 if (edge_y is not None and all(abs(v.co.y - edge_y) < 1e-6 for v in e.verts))
                 or (edge_x is not None and all(abs(v.co.x - edge_x) < 1e-6 for v in e.verts)))
    bm.select_history.clear()
    bm.select_history.add(hinge)
    bmesh.update_edit_mesh(ob.data)
    return ob


def _coords(ob):
    bm = bmesh.from_edit_mesh(ob.data)
    return sorted(tuple(round(c, 4) for c in v.co) for v in bm.verts)


def _arc(hinge, start, axis_dir, n=4, angle=90.0):
    """Where ``start`` goes after each division turning around the hinge line (point, direction)."""
    out = []
    for k in range(1, n + 1):
        a = math.radians(angle * k / n)
        p = start - hinge
        d = axis_dir.normalized()
        r = p * math.cos(a) + d.cross(p) * math.sin(a) + d * d.dot(p) * (1 - math.cos(a))
        out.append(tuple(round(c, 4) for c in hinge + r))
    return out


def _expected_new(hinge_pts, far_pts):
    """New vertices: the far edge's two vertices turned upward around the hinge edge."""
    h0, h1 = hinge_pts
    axis = h1 - h0
    up = Vector((0, 0, 1))
    mid_far = (far_pts[0] + far_pts[1]) / 2
    if axis.cross(mid_far - h0).dot(up) < 0:
        axis = -axis
    pts = []
    for p in far_pts:
        pts += _arc(h0, p, axis)
    return sorted(pts)


def _check(ob, hinge, far):
    before = {(-1.0, -1.0, -1.0), (1.0, -1.0, -1.0), (-1.0, 1.0, -1.0), (1.0, 1.0, -1.0),
              (-1.0, -1.0, 1.0), (1.0, -1.0, 1.0), (-1.0, 1.0, 1.0), (1.0, 1.0, 1.0)}
    got = _coords(ob)
    new = sorted(c for c in got if c not in before)
    want = _expected_new([Vector(p) for p in hinge], [Vector(p) for p in far])
    assert len(got) == 16, (len(got), got)
    assert all((Vector(a) - Vector(b)).length < 1e-3 for a, b in zip(new, want)), (new, want)
    bm = bmesh.from_edit_mesh(ob.data)
    assert len(bm.faces) == 18, len(bm.faces)       # 5 cube sides, 4 strips, 4 + 4 side wedges, the moved face


def test_wedge_turns_around_the_picked_edge():
    for kw, hinge, far in (
            ({"edge_y": -1.0}, [(-1, -1, 1), (1, -1, 1)], [(-1, 1, 1), (1, 1, 1)]),
            ({"edge_y": 1.0}, [(-1, 1, 1), (1, 1, 1)], [(-1, -1, 1), (1, -1, 1)]),
            ({"edge_x": -1.0}, [(-1, -1, 1), (-1, 1, 1)], [(1, -1, 1), (1, 1, 1)]),
            ({"edge_x": 1.0}, [(1, -1, 1), (1, 1, 1)], [(-1, -1, 1), (-1, 1, 1)])):
        ob = _cube_top(**kw)
        assert bpy.ops.allset.wedge() == {'FINISHED'}
        _check(ob, hinge, far)


def _plane(cuts_x=0):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    kit.enable()
    bpy.ops.mesh.primitive_plane_add(size=2)
    ob = bpy.context.object
    bpy.ops.object.mode_set(mode='EDIT')
    if cuts_x:
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.subdivide(number_cuts=cuts_x)      # a 3 x 3 grid for 2 cuts
    return ob


def _select(ob, face, hinge):
    bm = bmesh.from_edit_mesh(ob.data)
    for el in (*bm.verts, *bm.edges, *bm.faces):
        el.select = False
    face.select = True
    bm.select_flush(True)
    bm.select_history.clear()
    bm.select_history.add(hinge)
    bmesh.update_edit_mesh(ob.data)


def test_wedge_closes_the_solid_with_outward_normals():
    ob = _cube_top(edge_y=-1.0)
    assert bpy.ops.allset.wedge() == {'FINISHED'}
    bm = bmesh.from_edit_mesh(ob.data)
    assert all(len(e.link_faces) == 2 for e in bm.edges)
    volume = sum(f.calc_area() * f.normal.dot(f.calc_center_median()) for f in bm.faces) / 3
    assert volume > 8.0, volume                       # the cube plus the quarter-round wedge, normals out
    assert [f for f in bm.faces if f.select] and all(f.normal.y < -0.99 for f in bm.faces if f.select)


def test_wedge_angle_and_divisions():
    ob = _cube_top(edge_y=-1.0)
    assert bpy.ops.allset.wedge(angle=45.0, divisions=2) == {'FINISHED'}
    bm = bmesh.from_edit_mesh(ob.data)
    assert (len(bm.verts), len(bm.faces)) == (12, 12), (len(bm.verts), len(bm.faces))
    top = max(v.co.z for v in bm.verts)
    assert abs(top - (1 + 2 * math.sin(math.radians(45)))) < 1e-4, top


def test_a_lone_face_keeps_its_place_as_the_bottom():
    ob = _plane()
    bm = bmesh.from_edit_mesh(ob.data)
    bm.faces.ensure_lookup_table()
    face = bm.faces[0]
    _select(ob, face, next(e for e in face.edges if all(abs(v.co.y + 1) < 1e-6 for v in e.verts)))
    assert bpy.ops.allset.wedge() == {'FINISHED'}
    bm = bmesh.from_edit_mesh(ob.data)
    assert (len(bm.verts), len(bm.faces)) == (12, 14), (len(bm.verts), len(bm.faces))
    flat = [f for f in bm.faces if all(abs(v.co.z) < 1e-6 for v in f.verts)]
    assert len(flat) == 1 and flat[0].normal.z < -0.99, [f.normal for f in flat]


def test_a_face_with_neighbours_opens_its_place():
    ob = _plane(cuts_x=2)
    bm = bmesh.from_edit_mesh(ob.data)
    mid = min(bm.faces, key=lambda f: f.calc_center_median().length)    # the middle of the 3 x 3 grid
    hinge = min(mid.edges, key=lambda e: ((e.verts[0].co + e.verts[1].co) / 2).y)
    n_faces = len(bm.faces)
    _select(ob, mid, hinge)
    assert bpy.ops.allset.wedge() == {'FINISHED'}
    bm = bmesh.from_edit_mesh(ob.data)
    assert len(bm.faces) == n_faces - 1 + 13, len(bm.faces)
    assert len(bm.verts) == 16 + 8, len(bm.verts)
