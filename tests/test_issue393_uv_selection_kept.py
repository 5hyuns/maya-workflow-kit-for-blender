"""#393 follow-up: the UV commands that run a Blender unwrap / pack on chosen shells (Straighten Shell, Unfold,
Layout) keep the user's selection like Maya, with UV Sync Selection on or off and with several meshes in edit mode,
and work on the right shells while Blender keeps a UV selection of its own (``uv_select_sync_valid``, as in a fresh
UI session). A Maya menu item that can't run in object mode is cancelled (no empty undo step)."""

import math
from importlib import import_module

import bmesh
import bpy

import kit

compat = import_module(kit.MODULE + ".compat")

N, H, RING = 20, 4, 2


def _clear():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)


def _cylinder(name, x):
    """A cylinder side cut along one edge line, laid out as a wavy upright ribbon (one shell, no caps)."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("map1")
    ring = [[bm.verts.new((x + math.cos(2 * math.pi * i / N), math.sin(2 * math.pi * i / N), 0.5 * j))
             for i in range(N)] for j in range(H + 1)]
    where = {}
    for j in range(H):
        for i in range(N):
            corners = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
            f = bm.faces.new([ring[jj][ii % N] for ii, jj in corners])
            where[f] = corners
            for lp, (ii, jj) in zip(f.loops, corners):
                lp[uv].uv = (0.3 + 0.1 * jj + 0.03 * math.sin(ii * 0.7), 0.05 + 0.045 * ii)
    bm.faces.index_update()
    where = {f.index: c for f, c in where.items()}
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    return ob, where


def _scene(count):
    _clear()
    obs = [_cylinder(f"ribbon{k}", 3.0 * k) for k in range(count)]
    for o in bpy.context.scene.objects:
        o.select_set(True)
    bpy.context.view_layer.objects.active = obs[0][0]
    bpy.ops.object.mode_set(mode='EDIT')
    return obs


def _ring_edges(bm, where):
    bm.faces.ensure_lookup_table()
    on = set()
    for fi, corners in where.items():
        for k, lp in enumerate(bm.faces[fi].loops):
            if corners[k][1] == RING and corners[(k + 1) % 4][1] == RING:
                on.add(lp.edge)
    return on


def _select(obs, sync, uv_sync_valid=False):
    """The ring edge loop of every ribbon selected: sync on = mesh edges; sync off = UV edges, all faces shown.
    ``uv_sync_valid``: Blender's own UV selection marked valid but empty (a fresh UI session)."""
    ts = bpy.context.scene.tool_settings
    ts.use_uv_select_sync = sync
    ts.mesh_select_mode = (False, True, False)
    for ob, where in obs:
        bm = bmesh.from_edit_mesh(ob.data)
        uv = bm.loops.layers.uv.active
        on = _ring_edges(bm, where)
        for el in (*bm.faces, *bm.edges, *bm.verts):
            el.select = False
        for f in bm.faces:
            f.uv_select = False
            for lp in f.loops:
                lp.uv_select_vert = lp.uv_select_edge = False
        if sync:
            for e in on:
                e.select = True
                for v in e.verts:
                    v.select = True
        else:
            verts = {v for e in on for v in e.verts}
            for f in bm.faces:
                f.select = True
                for lp in f.loops:
                    compat.set_uv_vert_selected(lp, uv, lp.vert in verts)
                    compat.set_uv_edge_selected(lp, uv, lp.edge in on)
        if hasattr(bm, "uv_select_sync_valid"):
            bm.uv_select_sync_valid = uv_sync_valid
        bmesh.update_edit_mesh(ob.data)


def _state(ob):
    bm = bmesh.from_edit_mesh(ob.data)
    loops = [lp for f in bm.faces for lp in f.loops]
    return {"edges": sum(e.select for e in bm.edges), "verts": sum(v.select for v in bm.verts),
            "faces": sum(f.select for f in bm.faces), "uv_edges": sum(lp.uv_select_edge for lp in loops),
            "uv_verts": sum(lp.uv_select_vert for lp in loops)}


def _uvs(ob):
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.active
    return [tuple(round(c, 5) for c in lp[uv].uv) for f in bm.faces for lp in f.loops]


def _straight_strip(ob, where):
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.active
    bm.faces.ensure_lookup_table()
    grid = {}
    for fi, corners in where.items():
        for lp, ij in zip(bm.faces[fi].loops, corners):
            grid[ij] = lp[uv].uv.copy()
    height = max(p.y for p in grid.values()) - min(p.y for p in grid.values())
    bend = max(max(grid[i, j].x for i in range(N + 1)) - min(grid[i, j].x for i in range(N + 1))
               for j in range(H + 1))
    return bend < 1e-4 * height, round(bend, 6)


def test_straighten_shell_with_blender_uv_selection_valid():
    """Fresh UI session: Blender's own UV selection is valid but empty; the whole shell is still unfolded."""
    obs = _scene(1)
    _select(obs, sync=False, uv_sync_valid=True)
    before = _state(obs[0][0])
    assert bpy.ops.allset.uv_straighten_shell() == {'FINISHED'}
    ok, bend = _straight_strip(*obs[0])
    assert ok, ("ring bend", bend)
    assert _state(obs[0][0]) == before, (_state(obs[0][0]), before)
    bpy.ops.object.mode_set(mode='OBJECT')


def test_straighten_shell_two_meshes_uv_sync():
    obs = _scene(2)
    _select(obs, sync=True)
    before = [_state(ob) for ob, _w in obs]
    assert bpy.ops.allset.uv_straighten_shell() == {'FINISHED'}
    for (ob, where), b in zip(obs, before):
        ok, bend = _straight_strip(ob, where)
        assert ok, (ob.name, "ring bend", bend)
        assert _state(ob) == b, (ob.name, _state(ob), b)
    bpy.ops.object.mode_set(mode='OBJECT')


def _keeps_selection(op, sync, count, uv_sync_valid=False):
    obs = _scene(count)
    _select(obs, sync=sync, uv_sync_valid=uv_sync_valid)
    before = [_state(ob) for ob, _w in obs]
    uvs = [_uvs(ob) for ob, _w in obs]
    assert op() == {'FINISHED'}
    wrong = []
    for (ob, _w), b, u in zip(obs, before, uvs):
        if _state(ob) != b:
            wrong.append((ob.name, "selection", b, _state(ob)))
        if _uvs(ob) == u:
            wrong.append((ob.name, "UVs did not change"))
    bpy.ops.object.mode_set(mode='OBJECT')
    return wrong


def test_unfold_keeps_the_selection():
    wrong = []
    for sync in (True, False):
        for count in (1, 2):
            wrong += [(sync, count, w) for w in _keeps_selection(bpy.ops.allset.uv_unfold, sync, count)]
    wrong += [("valid", w) for w in _keeps_selection(bpy.ops.allset.uv_unfold, False, 1, uv_sync_valid=True)]
    assert not wrong, wrong


def test_layout_keeps_the_selection():
    wrong = []
    for sync in (True, False):
        for count in (1, 2):
            wrong += [(sync, count, w) for w in _keeps_selection(bpy.ops.allset.uv_layout, sync, count)]
    assert not wrong, wrong


def test_object_mode_item_without_a_3d_view_is_cancelled():
    """No 3D View anywhere: an object-mode Camera-based can't run; it is cancelled, the object stays as it was."""
    obs = _scene(1)
    bpy.ops.object.mode_set(mode='OBJECT')
    ob = obs[0][0]
    before = [tuple(round(c, 5) for c in d.uv) for d in ob.data.uv_layers.active.data]
    changed = []
    for w in bpy.context.window_manager.windows:
        for a in w.screen.areas:
            if a.type == 'VIEW_3D':
                changed.append(a)
                a.type = 'IMAGE_EDITOR'
    try:
        with bpy.context.temp_override(window=bpy.context.window_manager.windows[0]):
            res = bpy.ops.allset.menu_whole_mesh(item="UV/Camera-based")
    finally:
        for a in changed:
            a.type = 'VIEW_3D'
    assert res == {'CANCELLED'}, res
    assert ob.mode == 'OBJECT'
    assert [tuple(round(c, 5) for c in d.uv) for d in ob.data.uv_layers.active.data] == before
