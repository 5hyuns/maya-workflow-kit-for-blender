"""#427 Isolate Select with components (src/allset/operators/isolate_parts.py): which faces a selection isolates,
hiding only what the kit may hide and giving back exactly that (Edit Mode and Object Mode), leftovers from undo /
a saved file, and switching the kit off while isolating. The view itself (Ctrl+1, four view, undo in the UI):
tests/gui/gui_issue427_isolate_faces.py."""

from importlib import import_module

import bmesh
import bpy

import kit

iso = import_module(kit.MODULE + ".operators.isolate_parts")


def _grid():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    iso._on.clear()
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    me = bpy.data.meshes.new("pA")
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=4, y_segments=4, size=2.0)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("pA", me)
    bpy.context.collection.objects.link(ob)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT')
    return ob


def _bm(ob):
    bm = bmesh.from_edit_mesh(ob.data)
    for seq in (bm.verts, bm.edges, bm.faces):
        seq.index_update()
        seq.ensure_lookup_table()
    return bm


def _face_at(bm, x, y):
    return min(bm.faces, key=lambda f: (f.calc_center_median().x - x) ** 2 + (f.calc_center_median().y - y) ** 2)


def _vert_at(bm, x, y):
    return min(bm.verts, key=lambda v: (v.co.x - x) ** 2 + (v.co.y - y) ** 2)


def _hidden(ob):
    if ob.mode == 'EDIT':
        return sorted(f.index for f in _bm(ob).faces if f.hide)
    return sorted(p.index for p in ob.data.polygons if p.hide)


def _isolate(ob, keep):
    bm = _bm(ob)
    iso._apply(ob, bm, set(keep))
    iso._on[ob.name] = {"count": len(bm.faces), "keep": set(keep), "gone": 0}


def test_face_mode_takes_the_selected_faces():
    ob = _grid()
    bm = _bm(ob)
    a, b = _face_at(bm, -0.5, 0.5), _face_at(bm, 0.5, 0.5)
    a.select_set(True)
    b.select_set(True)
    assert iso.picked_faces(bm, (False, False, True)) == {a.index, b.index}


def test_vertices_and_edges_take_the_faces_using_their_vertices():
    ob = _grid()
    bm = _bm(ob)
    v = _vert_at(bm, 0, 0)
    v.select_set(True)
    assert iso.picked_faces(bm, (True, False, False)) == {f.index for f in v.link_faces}
    assert len(v.link_faces) == 4
    v.select_set(False)
    bm.select_flush(False)
    corner = _vert_at(bm, -2, -2)
    corner.select_set(True)
    assert len(iso.picked_faces(bm, (True, False, False))) == 1        # a corner: its one face
    corner.select_set(False)
    bm.select_flush(False)
    f1, f2 = _face_at(bm, -0.5, 0.5), _face_at(bm, 0.5, 0.5)
    e = next(e for e in f1.edges if e in f2.edges)
    e.select_set(True)
    got = iso.picked_faces(bm, (False, True, False))
    assert got == {f.index for v in e.verts for f in v.link_faces} and len(got) == 6, got


def test_isolate_hides_only_shown_faces_and_gives_back_exactly_those():
    ob = _grid()
    bm = _bm(ob)
    user = _face_at(bm, -1.5, -1.5)
    user.hide_set(True)
    user_i = user.index
    keep = {_face_at(bm, -0.5, 0.5).index, _face_at(bm, 0.5, 0.5).index}
    bmesh.update_edit_mesh(ob.data)
    _isolate(ob, keep)
    assert _hidden(ob) == sorted(set(range(16)) - keep)
    bm = _bm(ob)
    layer = bm.faces.layers.int.get(iso.ATTR)
    assert sorted(f.index for f in bm.faces if f[layer]) == sorted(set(range(16)) - keep - {user_i})
    shown_verts = {v.index for f in bm.faces if not f.hide for v in f.verts}
    assert all(not bm.verts[i].hide for i in shown_verts)        # the shown faces keep their corners
    iso.stop()
    assert _hidden(ob) == [user_i]
    assert _bm(ob).faces.layers.int.get(iso.ATTR) is None


def test_set_changes_show_and_hide_faces():
    ob = _grid()
    _isolate(ob, {0, 1})
    bm = _bm(ob)
    iso._apply(ob, bm, {0, 1, 2})
    assert _hidden(ob) == sorted(set(range(16)) - {0, 1, 2})
    iso._apply(ob, _bm(ob), {1, 2})
    assert _hidden(ob) == sorted(set(range(16)) - {1, 2})
    iso.stop()
    assert _hidden(ob) == []


def test_object_mode_gives_the_faces_back():
    ob = _grid()
    bm = _bm(ob)
    user = _face_at(bm, 1.5, 1.5)
    user.hide_set(True)
    user_i = user.index
    bmesh.update_edit_mesh(ob.data)
    _isolate(ob, {_face_at(_bm(ob), 0.5, -0.5).index})
    bpy.ops.object.mode_set(mode='OBJECT')
    assert ob.data.attributes.get(iso.ATTR) is not None and len(_hidden(ob)) == 15
    iso.stop()
    assert _hidden(ob) == [user_i] and ob.data.attributes.get(iso.ATTR) is None
    assert not any(v.hide for p in ob.data.polygons if not p.hide for v in (ob.data.vertices[i] for i in p.vertices))


def test_leftover_marks_are_cleared_when_nothing_isolates():
    """A mesh that carries the mark without an isolation (redo after it ended, a file saved while isolating) gets
    its faces back; the user's hidden faces stay."""
    ob = _grid()
    bm = _bm(ob)
    user = _face_at(bm, -1.5, 1.5)
    user.hide_set(True)
    user_i = user.index
    bmesh.update_edit_mesh(ob.data)
    _isolate(ob, {5})
    iso._on.clear()                       # isolation over, the mesh still marked
    iso._on_undo()
    assert _hidden(ob) == [user_i] and _bm(ob).faces.layers.int.get(iso.ATTR) is None
    _isolate(ob, {5})
    iso._on.clear()
    bpy.ops.object.mode_set(mode='OBJECT')
    iso._on_load()
    assert _hidden(ob) == [user_i] and ob.data.attributes.get(iso.ATTR) is None


def test_no_view_isolating_gives_the_faces_back():
    ob = _grid()
    _isolate(ob, {3})
    for _ in range(iso._GRACE):
        iso._check()                      # headless: no 3D View isolates anything
    assert iso.active() == [] and _hidden(ob) == []


def test_switching_the_kit_off_gives_the_faces_back():
    ob = _grid()
    _isolate(ob, {3, 4})
    kit.disable()
    try:
        assert _hidden(ob) == []
        assert _bm(ob).faces.layers.int.get(iso.ATTR) is None
    finally:
        kit.enable()
