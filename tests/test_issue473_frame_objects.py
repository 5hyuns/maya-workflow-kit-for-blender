"""Frame Selected on several objects apart: each object keeps its own box, so the view comes as close as those boxes
allow (not as close as the one box around all of them), and still aims at the middle of everything (#473)."""

import math
from importlib import import_module

import bpy
from mathutils import Matrix, Quaternion, Vector

import kit

framing = import_module(kit.MODULE + ".operators.framing")
view_frame = import_module(kit.MODULE + ".operators.view_frame")

SIZE = (1100, 700)


def _persp_win(lens=35.0, size=SIZE, near=0.01, far=1000.0):
    w, h = size
    half_w = near * 18.0 / lens
    half_h = half_w * h / w
    return Matrix(((near / half_w, 0, 0, 0), (0, near / half_h, 0, 0),
                   (0, 0, -(far + near) / (far - near), -2 * far * near / (far - near)),
                   (0, 0, -1, 0)))


def _rot():
    return Quaternion((1, 0, 0), math.radians(62)) @ Quaternion((0, 0, 1), math.radians(45))


def _cube(half=0.5, at=(0, 0, 0)):
    return [Vector(at) + Vector((x, y, z)) for x in (-half, half) for y in (-half, half) for z in (-half, half)]


def _fit(points, per_box=True):
    return framing.fit(points, _rot(), _persp_win(), 10.0, False, SIZE, (0, 0) + SIZE, per_box=per_box)


def test_two_objects_closer_than_their_joint_box():
    two = _cube() + _cube(1.0, (5, 0, 0))
    loc_two, d_two = _fit(two)
    loc_box, d_box = _fit(two, per_box=False)
    assert d_two < d_box - 0.5, (d_two, d_box)
    # the view still aims at the middle of the box around both
    mid = (Vector((-0.5, -1, -1)) + Vector((6, 1, 1))) / 2
    assert (loc_two - mid).length < 1e-4 and (loc_box - mid).length < 1e-4, (loc_two, loc_box, mid)


def test_one_box_unchanged():
    box = _cube(1.0, (2, 1, 0))
    assert abs(_fit(box)[1] - _fit(framing.box_corners(box))[1]) < 1e-9


def test_one_point_padded():
    loc, d = _fit([Vector((1, 2, 3))])
    assert (loc - Vector((1, 2, 3))).length < 1e-6 and d > 0.5, (loc, d)


def test_frame_selected_objects_per_box():
    # F on two objects in Object Mode uses their own boxes
    assert view_frame._per_box(bpy.context, True) == (bpy.context.mode == 'OBJECT')
    assert view_frame._per_box(bpy.context, False)


def test_object_points_world_box():
    # a rotated object frames by its box along the world axes, a shape's points are the box corners
    bpy.ops.mesh.primitive_cube_add(size=2.0)
    ob = bpy.context.active_object
    ob.rotation_euler = (0.0, 0.0, math.radians(45))
    bpy.context.view_layer.update()
    pts = view_frame._object_points(ob, bpy.context.evaluated_depsgraph_get())
    assert len(pts) == 8
    r = math.sqrt(2.0)
    xs = sorted({round(p.x, 5) for p in pts})
    assert xs == [round(-r, 5), round(r, 5)], xs
