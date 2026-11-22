"""#439 / #440: Planar projection X / Y / Z follow the scene's axes, and the shorter side of the projection is
centred in 0-1 (the longer side spans 0-1)."""
import bmesh
import bpy
from mathutils import Vector

from bl_ext.user_default.allset.operators import menu_extras


def _box():
    """A 3 x 2 x 1 box (X x Y x Z) away from the origin, in object mode."""
    bpy.ops.wm.read_homefile(use_empty=True)
    me = bpy.data.meshes.new("box")
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * 3 + 5, v.co.y * 2 + 7, v.co.z * 1 + 11))
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("box", me)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    return ob


def _uv_of(ob):
    """{rounded vertex position: uv} over every loop (a box's loops of one vertex share no face here per axis)."""
    me = ob.data
    layer = me.uv_layers.active.data
    out = {}
    for lp in me.loops:
        co = tuple(round(c, 3) for c in me.vertices[lp.vertex_index].co)
        out.setdefault(co, set()).add(tuple(round(c, 3) for c in layer[lp.index].uv))
    return out


def _check(axis, u_of, v_of, u_span, v_span):
    ob = _box()
    assert bpy.ops.allset.uv_planar(axis=axis) == {'FINISHED'}
    for co, uvs in _uv_of(ob).items():
        assert len(uvs) == 1, (axis, co, uvs)          # a planar projection gives one UV per vertex
        u, v = next(iter(uvs))
        assert abs(u - u_of(co)) < 1e-3 and abs(v - v_of(co)) < 1e-3, (axis, co, (u, v))
    us = [next(iter(s))[0] for s in _uv_of(ob).values()]
    vs = [next(iter(s))[1] for s in _uv_of(ob).values()]
    assert (round(min(us), 3), round(max(us), 3)) == u_span, (axis, min(us), max(us))
    assert (round(min(vs), 3), round(max(vs), 3)) == v_span, (axis, min(vs), max(vs))


def test_x_projects_along_x():
    # sees Y (2) x Z (1): U along +Y spans 0-1, V along +Z centred
    _check('X', lambda c: (c[1] - 6) / 2, lambda c: (c[2] - 10.5) / 2 + 0.25, (0.0, 1.0), (0.25, 0.75))


def test_y_projects_along_y():
    # sees X (3) x Z (1): U along +X spans 0-1, V along +Z centred
    _check('Y', lambda c: (c[0] - 3.5) / 3, lambda c: (c[2] - 10.5) / 3 + 1 / 3, (0.0, 1.0), (0.333, 0.667))


def test_z_projects_along_z():
    # sees X (3) x Y (2): U along +X spans 0-1, V along +Y centred
    _check('Z', lambda c: (c[0] - 3.5) / 3, lambda c: (c[1] - 6) / 3 + 1 / 6, (0.0, 1.0), (0.167, 0.833))


def test_option_window_axes_match():
    for label, key in (("X axis", 'X'), ("Y axis", 'Y'), ("Z axis", 'Z')):
        ob = _box()
        from bl_ext.user_default.allset.operators import option_windows_basic as owb
        owb._run_uv_planar(bpy.context, {"fit": "Bounding box", "project_from": label})
        by_window = _uv_of(ob)
        ob = _box()
        bpy.ops.allset.uv_planar(axis=key)
        assert _uv_of(ob) == by_window, label


def test_square_fits_whole_tile():
    pts = [Vector(p) for p in ((0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0))]
    out = menu_extras.planar_uvs(pts, (0, 0, 1))
    assert sorted((round(u, 4), round(v, 4)) for u, v in out) == [(0, 0), (0, 1), (1, 0), (1, 1)], out
