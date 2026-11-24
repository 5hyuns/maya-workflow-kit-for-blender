"""Issue #488: UV > Automatic with 3, 4, 5, 8 and 12 planes groups the faces like Maya.

3 planes project along the three axes and take faces on both sides of each, 4 planes are the faces of a
tetrahedron with one face to the front, and 5 planes face the front and the back plus three around the
front-back axis, 12 planes are the faces of a dodecahedron; each plane count has its own candidate angle
for Fewer pieces, and every projection frame is the X / Y axes turned onto the plane. The 8 planes keep
Maya's own frames, a little off the exact turn, which decide faces lying exactly between two planes."""

import math
from importlib import import_module

import bpy

import kit

al = import_module(kit.MODULE + ".operators.autoproj_layout")
create = import_module(kit.MODULE + ".operators.create")


def _close(a, b, tol=1e-9):
    return all(abs(x - y) < tol for x, y in zip(a, b))


def test_frames_are_the_axes_turned_onto_each_plane():
    for f in al.PLANES6:
        got = al.plane_frame(f[0])
        assert all(_close(g, w) for g, w in zip(got, f)), (f, got)
    for count, pset in al.PLANE_SETS.items():
        assert len(pset.frames) == count or (count == 3 and pset.both_sides), count
        tol = 1e-5 if count == 8 else 1e-9      # the 8 frames are Maya's float32 ones
        for n, u, v in pset.frames:
            cross = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
            assert _close(cross, n, tol), (count, n, u, v)
            assert abs(math.hypot(*u) - 1) < tol and abs(math.hypot(*v) - 1) < tol
            if count == 8:
                assert _close(al.plane_frame(n)[1], u, tol) and _close(al.plane_frame(n)[2], v, tol), (n, u, v)


def _cube_faces():
    """A unit cube in Maya face order: +Z, +Y, -Z, -Y, +X, -X (Maya axes)."""
    pts = [(-0.5, -0.5, 0.5), (0.5, -0.5, 0.5), (-0.5, 0.5, 0.5), (0.5, 0.5, 0.5),
           (-0.5, 0.5, -0.5), (0.5, 0.5, -0.5), (-0.5, -0.5, -0.5), (0.5, -0.5, -0.5)]
    faces = [[0, 1, 3, 2], [2, 3, 5, 4], [4, 5, 7, 6], [6, 7, 1, 0], [1, 7, 5, 3], [6, 0, 2, 4]]
    return pts, faces


def _groups(shells):
    return sorted(sorted(g) for _p, g in shells)


def test_cube_shells_per_plane_count():
    pts, faces = _cube_faces()
    # 3 planes: one shell per side, like 6
    assert _groups(al.assign_planes(pts, faces, planes=3)) == [[0], [1], [2], [3], [4], [5]]
    # 4 planes: front, top and +X alone; back, bottom and -X together
    assert _groups(al.assign_planes(pts, faces, planes=4)) == [[0], [1], [2, 3, 5], [4]]
    # 5 planes: front, top, back and +X alone; bottom and -X share the plane between them
    assert _groups(al.assign_planes(pts, faces, planes=5)) == [[0], [1], [2], [3, 5], [4]]


def test_cube_shells_with_8_planes():
    """Every cube side lies exactly between four planes of the 8: Maya's frames decide."""
    pts, faces = _cube_faces()
    # Fewer pieces: front, bottom, +X and -X on the (-1, -1, 1) plane; top and back on (1, 1, -1)
    assert al.assign_planes(pts, faces, planes=8) == [(0, [0, 3, 4, 5]), (1, [1, 2])]
    # Less distortion: each side on its own best plane, top and +X share (1, 1, 1)
    got = sorted(al.assign_planes(pts, faces, planes=8, optimize=False))
    assert got == [(0, [0]), (1, [2]), (3, [1, 4]), (6, [5]), (7, [3])], got


def _shell_count(ob):
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    uv = bm.loops.layers.uv.active
    parent = {f.index: f.index for f in bm.faces}

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for e in bm.edges:
        a, b = (list(e.link_faces) + [None, None])[:2]
        if a is None or b is None:
            continue
        ua = {lp.vert: lp[uv].uv.copy() for lp in a.loops}
        ub = {lp.vert: lp[uv].uv.copy() for lp in b.loops}
        if all((ua[v] - ub[v]).length < 1e-6 for v in e.verts):
            parent[find(a.index)] = find(b.index)
    n = len({find(f.index) for f in bm.faces})
    bm.free()
    return n


def test_menu_automatic_on_a_sphere():
    """A sphere gets one shell per plane with 4, 5 and 12 planes and one per side of each axis with 3."""
    for planes, shells in ((3, 6), (4, 4), (5, 5), (6, 6), (12, 12)):
        for ob in list(bpy.data.objects):
            bpy.data.objects.remove(ob)
        ob = create.create(bpy.context, 'SPHERE')
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        for o in bpy.context.view_layer.objects:
            o.select_set(o == ob)
        bpy.context.view_layer.objects.active = ob
        assert bpy.ops.allset.menu_item(item="UV/Automatic") == {'FINISHED'}
        bpy.context.window_manager.allset_history.planes_text = str(planes)
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        assert _shell_count(ob) == shells, (planes, _shell_count(ob))
