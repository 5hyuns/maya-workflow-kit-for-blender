"""#506: UV Editor > Modify > Flip uses its options Coordinate (Pivot / Selection Center / Global) and Cut UV
Perimeter, like Maya.

Flip works on faces (the selected faces, or the faces using a selected UV). Pivot = the UV pivot (the 2D cursor while
it is the pivot, else the selection's UV box centre); Selection Center = the flipped faces' UV box centre; Global =
the 0 line. Cut UV Perimeter (default on) cuts the flipped faces free so their neighbours stay; off, the shared UVs
move and pull the neighbours along."""

from importlib import import_module

import bmesh
import bpy

import kit

ow = import_module(kit.MODULE + ".operators.option_windows")
emap = import_module(kit.MODULE + ".ui.editor_menu_map")
box = import_module(kit.MODULE + ".ui.menu_option_box")

ITEM = "UV Editor/Modify/Flip"
N = 4


def _grid():
    """A 4 x 4 face grid; UV of vertex (i, j) = (0.3 + 0.125 i, 0.15 + 0.1 j)."""
    ow.store("uv_flip", None)
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    me = bpy.data.meshes.new("grid")
    bm = bmesh.new()
    vs = [bm.verts.new((i, j, 0.0)) for j in range(N + 1) for i in range(N + 1)]
    uv = bm.loops.layers.uv.new("UVMap")
    for j in range(N):
        for i in range(N):
            a = j * (N + 1) + i
            f = bm.faces.new((vs[a], vs[a + 1], vs[a + N + 2], vs[a + N + 1]))
            for loop in f.loops:
                x, y = loop.vert.co.x, loop.vert.co.y
                loop[uv].uv = (0.3 + 0.125 * x, 0.15 + 0.1 * y)
    bm.to_mesh(me)
    ob = bpy.data.objects.new("grid", me)
    bpy.context.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.scene.tool_settings.use_uv_select_sync = True
    return ob


def _bm(ob):
    bm = bmesh.from_edit_mesh(ob.data)
    bm.faces.ensure_lookup_table()
    return bm, bm.loops.layers.uv.active


def _select_faces(ob, test):
    bpy.ops.mesh.select_mode(type='FACE')
    bm, _uv = _bm(ob)
    for el in (*bm.verts, *bm.edges, *bm.faces):
        el.select = False
    for f in bm.faces:
        if test(f.calc_center_median()):
            f.select = True
    bm.select_flush_mode()
    bmesh.update_edit_mesh(ob.data)


def _select_verts(ob, test):
    bpy.ops.mesh.select_mode(type='VERT')
    bm, _uv = _bm(ob)
    for el in (*bm.verts, *bm.edges, *bm.faces):
        el.select = False
    for v in bm.verts:
        if test(v.co):
            v.select = True
    bm.select_flush_mode()
    bmesh.update_edit_mesh(ob.data)


def _corners(ob):
    """{(face index, vertex index): (u, v)}"""
    bm, uv = _bm(ob)
    return {(f.index, l.vert.index): tuple(l[uv].uv) for f in bm.faces for l in f.loops}


def _left(c):
    return c.x < 2.0


def _check(before, after, moved_faces, axis, line, ob, drag=()):
    bm, _uv = _bm(ob)
    for (fi, vi), p in before.items():
        q = after[(fi, vi)]
        if fi in moved_faces or (fi, vi) in drag:
            want = list(p)
            want[axis] = 2 * line - p[axis]
        else:
            want = p
        assert abs(q[0] - want[0]) < 1e-6 and abs(q[1] - want[1]) < 1e-6, ((fi, vi), p, q, want)


def _faces_where(ob, test):
    bm, _uv = _bm(ob)
    return {f.index for f in bm.faces if test(f.calc_center_median())}


def test_menu_item_and_window():
    assert emap.MAP[ITEM] == "allset.uv_flip"
    w = ow.find_path(ITEM)
    assert w is not None and w.key == "uv_flip" and box.option_kind(ITEM) == "window"
    assert w.defaults() == {"direction": "Horizontal", "coordinate": "Pivot", "cut": True}
    assert not w.missing


def test_default_flips_around_the_selection_centre_and_cuts_free():
    ob = _grid()
    _select_faces(ob, _left)
    before = _corners(ob)
    assert bpy.ops.allset.menu_item(item=ITEM) == {'FINISHED'}
    # the left half (U 0.3 - 0.55) mirrors around U 0.425; the right half stays (cut free)
    _check(before, _corners(ob), _faces_where(ob, _left), 0, 0.425, ob)
    assert any(e.seam for e in _bm(ob)[0].edges), "the cut border is a seam"


def test_without_cut_the_shared_uvs_pull_the_neighbours():
    ob = _grid()
    _select_faces(ob, _left)
    before = _corners(ob)
    assert bpy.ops.allset.opt_uv_flip('EXEC_DEFAULT', direction="Horizontal", coordinate="Pivot", cut=False) == \
        {'FINISHED'}
    bm, _uv = _bm(ob)
    left = _faces_where(ob, _left)
    # the right faces' corners on the middle column (U 0.55) move with the left faces (to U 0.3)
    drag = {(f.index, l.vert.index) for f in bm.faces if f.index not in left for l in f.loops
            if abs(l.vert.co.x - 2.0) < 1e-6}
    _check(before, _corners(ob), left, 0, 0.425, ob, drag)
    assert ow.saved("uv_flip") == {"direction": "Horizontal", "coordinate": "Pivot", "cut": False}


def test_global_flips_around_zero():
    ob = _grid()
    _select_faces(ob, _left)
    before = _corners(ob)
    assert bpy.ops.allset.uv_flip(direction='VERTICAL', coordinate='GLOBAL') == {'FINISHED'}
    _check(before, _corners(ob), _faces_where(ob, _left), 1, 0.0, ob)


def test_selected_uvs_flip_the_faces_using_them():
    ob = _grid()
    _select_verts(ob, lambda co: co.x < 2.5)     # the UV columns 0, 1, 2
    before = _corners(ob)
    using = _faces_where(ob, lambda c: c.x < 3.0)     # every face that uses one of them
    # Selection Center: the box of the faces using the UVs (U 0.3 - 0.675)
    assert bpy.ops.allset.uv_flip(coordinate='CENTER') == {'FINISHED'}
    _check(before, _corners(ob), using, 0, 0.4875, ob)
    ob = _grid()
    _select_verts(ob, lambda co: co.x < 2.5)
    before = _corners(ob)
    # Pivot: the box of the selected UVs themselves (U 0.3 - 0.55)
    assert bpy.ops.allset.uv_flip(coordinate='PIVOT') == {'FINISHED'}
    _check(before, _corners(ob), using, 0, 0.425, ob)


def test_nothing_selected():
    ob = _grid()
    _select_faces(ob, lambda c: False)
    assert bpy.ops.allset.uv_flip() == {'CANCELLED'}
