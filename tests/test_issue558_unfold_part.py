"""UV Unfold on part of a shell (#558): only the selected UVs move, like Maya; the rest of the shell stays where it
is. Selected faces take their corner UVs (the row they share with unselected faces too), a selected edge the UVs
at its ends, a selected vertex its UV. A whole selected shell still unfolds as a whole, and pins set before stay."""
import bmesh
import bpy

import kit
from importlib import import_module

compat = import_module(kit.MODULE + ".compat")


def _strip():
    """A 1 x 6 strip of six faces, one UV shell squashed to 0.3 wide (so Unfold has work to do)."""
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    verts = [(float(i), float(j), 0.0) for j in range(7) for i in range(2)]
    faces = [(2 * j, 2 * j + 1, 2 * j + 3, 2 * j + 2) for j in range(6)]
    me = bpy.data.meshes.new("s6")
    me.from_pydata(verts, [], faces)
    me.uv_layers.new(name="map1")
    bm = bmesh.new()
    bm.from_mesh(me)
    uv = bm.loops.layers.uv.active
    for f in bm.faces:
        for lp in f.loops:
            lp[uv].uv = (0.35 + 0.3 * lp.vert.co.x, lp.vert.co.y / 6.0)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("s6", me)
    bpy.context.collection.objects.link(ob)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT')
    return ob


def _select(ob, mode, faces=(), edges=(), verts=()):
    ts = bpy.context.scene.tool_settings
    ts.use_uv_select_sync = True
    ts.mesh_select_mode = (mode == 'VERT', mode == 'EDGE', mode == 'FACE')
    bm = bmesh.from_edit_mesh(ob.data)
    for seq in (bm.verts, bm.edges, bm.faces):
        seq.ensure_lookup_table()
        for el in seq:
            el.select = False
    for i in faces:
        bm.faces[i].select_set(True)
    for a, b in edges:
        next(e for e in bm.edges if {v.index for v in e.verts} == {a, b}).select_set(True)
    for i in verts:
        bm.verts[i].select_set(True)
    bm.select_mode = {mode}
    bm.select_flush_mode()
    compat.uv_sync_from_mesh(bm)
    bmesh.update_edit_mesh(ob.data)


def _uvs(ob):
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.active
    return {lp.vert.index: tuple(lp[uv].uv) for f in bm.faces for lp in f.loops}


def _moved(a, b):
    return sorted(i for i in a if abs(a[i][0] - b[i][0]) > 1e-6 or abs(a[i][1] - b[i][1]) > 1e-6)


def _pins(ob):
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.active
    return [lp[uv].pin_uv for f in bm.faces for lp in f.loops]


def _unfold(ob, mode, **sel):
    _select(ob, mode, **sel)
    before = _uvs(ob)
    assert bpy.ops.allset.uv_unfold(options='{"iterations": 1, "prevent_flips": true, "layout_uvs": false}') \
        == {'FINISHED'}
    return _moved(before, _uvs(ob))


def test_selected_faces_move_only_their_uvs():
    ob = _strip()
    moved = _unfold(ob, 'FACE', faces=(0, 1, 2))
    assert moved == list(range(8)), moved          # the bottom three faces' UVs, nothing above
    assert not any(_pins(ob)), "pins are put back"


def test_selected_edge_moves_its_two_uvs():
    ob = _strip()
    moved = _unfold(ob, 'EDGE', edges=((6, 7),))
    assert moved == [6, 7], moved


def test_selected_vertex_moves_its_uv():
    ob = _strip()
    moved = _unfold(ob, 'VERT', verts=(6,))
    assert moved == [6], moved


def test_whole_shell_still_unfolds_and_user_pins_stay():
    ob = _strip()
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.active
    bm.faces.ensure_lookup_table()
    bm.faces[5].loops[2][uv].pin_uv = True
    bmesh.update_edit_mesh(ob.data)
    pins = _pins(ob)
    moved = _unfold(ob, 'FACE', faces=range(6))
    assert len(moved) > 8, moved                                 # the whole shell unfolded
    ob2 = _strip()
    bm = bmesh.from_edit_mesh(ob2.data)
    uv = bm.loops.layers.uv.active
    bm.faces.ensure_lookup_table()
    bm.faces[5].loops[2][uv].pin_uv = True
    bmesh.update_edit_mesh(ob2.data)
    _unfold(ob2, 'FACE', faces=(0, 1))
    assert _pins(ob2) == pins, "a pin set before stays, the kit's own pins go"
