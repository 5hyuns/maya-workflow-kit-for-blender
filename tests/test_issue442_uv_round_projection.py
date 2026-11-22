"""#442: UV > Cylindrical / Spherical sit on the selection's bounding box centre around the scene's up axis, need no
3D View (the view angle plays no part), and Cylindrical spans V 0-1 over the selection's height."""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector

# Box of 1 (X) x 0.5 (Y, depth) x 2 (Z, up), moved away from the origin
SIZE = Vector((1.0, 0.5, 2.0))
AT = Vector((5.0, 7.0, 11.0))


def _box(rot_z=0.0):
    bpy.ops.wm.read_homefile(use_empty=True)
    me = bpy.data.meshes.new("box")
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector(v.co[i] * SIZE[i] for i in range(3))
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("box", me)
    bpy.context.scene.collection.objects.link(ob)
    ob.matrix_world = Matrix.Translation(AT) @ Matrix.Rotation(rot_z, 4, 'Z')
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    return ob


def _faces(ob):
    """[(world normal, [(world corner, uv)])] per face."""
    me = ob.data
    uv = me.uv_layers.active.data
    mw = ob.matrix_world
    out = []
    for p in me.polygons:
        n = (mw.to_3x3() @ p.normal).normalized()
        out.append((n, [(mw @ me.vertices[me.loops[i].vertex_index].co, Vector(uv[i].uv)) for i in p.loop_indices]))
    return out


def _face(faces, d):
    return next(k for n, k in faces if n.dot(Vector(d)) > 0.99)


def _run(item):
    assert bpy.ops.allset.menu_item(item=item) == {'FINISHED'}, item
    assert bpy.context.mode == 'OBJECT'


def test_cylindrical_spans_height_and_sits_on_centre():
    ob = _box()
    _run("UV/Cylindrical")
    faces = _faces(ob)
    vs = [uv.y for _n, k in faces for _p, uv in k]
    assert abs(min(vs)) < 1e-5 and abs(max(vs) - 1.0) < 1e-5, (min(vs), max(vs))
    front = _face(faces, (0, -1, 0))
    us = sorted(uv.x for _p, uv in front)
    half = math.atan2(SIZE.x / 2, SIZE.y / 2) / math.pi      # half a turn = one tile
    assert abs(us[0] - (0.5 - half)) < 1e-5 and abs(us[-1] - (0.5 + half)) < 1e-5, us
    right = _face(faces, (1, 0, 0))
    assert min(uv.x for _p, uv in right) > 0.5 + half - 1e-5, [uv.x for _p, uv in right]
    for _p, uv in _face(faces, (0, 1, 0)):            # the back face stays whole across the seam
        assert uv.x > 0.5 + half - 1e-5, uv


def test_spherical_equator_at_middle():
    ob = _box()
    _run("UV/Spherical")
    front = _face(_faces(ob), (0, -1, 0))
    tilt = math.atan2(SIZE.z / 2, math.hypot(SIZE.x / 2, SIZE.y / 2)) / (math.pi / 2)
    vs = sorted(uv.y for _p, uv in front)
    assert abs(vs[0] - (0.5 - tilt)) < 1e-5 and abs(vs[-1] - (0.5 + tilt)) < 1e-5, vs


def test_axis_is_the_scene_up_axis():
    """Turning the object about the up axis only turns U: V stays the same per corner height."""
    for item in ("UV/Cylindrical", "UV/Spherical"):
        rows = []
        for rot in (0.0, math.radians(90)):
            ob = _box(rot)
            _run(item)
            rows.append(sorted((round(p.z, 4), round(uv.y, 4)) for _n, k in _faces(ob) for p, uv in k))
        assert rows[0] == rows[1], item


def test_edit_mode_selected_faces_only():
    ob = _box()
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.verify()
    for f in bm.faces:
        for lp in f.loops:
            lp[uv].uv = (9.0, 9.0)
        f.select_set(f.normal.z < 0.5)             # the four sides
    bmesh.update_edit_mesh(ob.data)
    assert bpy.ops.allset.uv_cylindrical() == {'FINISHED'}
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.active
    for f in bm.faces:
        for lp in f.loops:
            if f.select:
                assert -1e-5 < lp[uv].uv.y < 1 + 1e-5, lp[uv].uv
            else:
                assert tuple(lp[uv].uv) == (9.0, 9.0), lp[uv].uv
    bpy.ops.object.mode_set(mode='OBJECT')
