"""#393: Straighten Shell (UV Toolkit > Unfold, UV Editor > Modify, the UV Shift+RMB menu) works like Maya's: the
selected UV edge loop becomes a straight line along U or V (its length kept) and the rest of its shell is unfolded
around it, so a ribbon shell such as a cylinder side becomes a straight strip. It runs at once (no dialog) and needs
no active face; fewer than two selected UVs is a warning. GUI: tests/gui/gui_issue392_393_uv.py."""

import math
from importlib import import_module

import bmesh
import bpy

import kit

compat = import_module(kit.MODULE + ".compat")
menu_map = import_module(kit.MODULE + ".ui.menu_map")
uvt = import_module(kit.MODULE + ".operators.uv_tools")

ITEM = "UV Editor/Modify/Straighten Shell"
N, H = 20, 4            # sides around, rows up: the side shell is 4 UVs wide and 20 long, like the issue's
RING = 2                # the selected edge loop: the ring of edges halfway up (a long line of the side shell)


def _clear():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)


def _side_uv(i, j):
    """A wavy, slanted side shell standing upright in the UV square (u across the rings, v around)."""
    return (0.3 + 0.1 * j + 0.03 * math.sin(i * 0.7) + 0.004 * i, 0.05 + 0.065 * i + 0.01 * math.sin(j * 1.3))


def _cylinder():
    """A capped cylinder: side quads (one shell cut along one seam), caps = triangle fans (two more shells).
    Returns the object and ``where``: face index -> [(i, j) of each corner] for the side faces."""
    _clear()
    me = bpy.data.meshes.new("pCylinder1")
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("map1")
    ring = [[bm.verts.new((math.cos(2 * math.pi * i / N), math.sin(2 * math.pi * i / N), 0.5 * j))
             for i in range(N)] for j in range(H + 1)]
    where = {}
    for j in range(H):
        for i in range(N):
            corners = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
            f = bm.faces.new([ring[jj][ii % N] for ii, jj in corners])
            where[f] = corners
            for lp, (ii, jj) in zip(f.loops, corners):
                lp[uv].uv = _side_uv(ii, jj)
    for j, cu in ((0, 1.25), (H, 1.6)):
        c = bm.verts.new((0.0, 0.0, 0.5 * j))
        for i in range(N):
            vs = [c, ring[j][(i + 1) % N], ring[j][i]] if j == 0 else [c, ring[j][i], ring[j][(i + 1) % N]]
            f = bm.faces.new(vs)
            for lp in f.loops:
                if lp.vert is c:
                    lp[uv].uv = (cu, 0.5)
                else:
                    a = math.atan2(lp.vert.co.y, lp.vert.co.x)
                    lp[uv].uv = (cu + 0.15 * math.cos(a), 0.5 + 0.15 * math.sin(a))
    bm.faces.index_update()
    where = {f.index: c for f, c in where.items()}
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("pCylinder1", me)
    bpy.context.collection.objects.link(ob)
    for o in bpy.context.scene.objects:
        o.select_set(o is ob)
    bpy.context.view_layer.objects.active = ob
    return ob, where


def _select_ring(ob, where, sync):
    """Edit mode with the UV edge loop of ring ``RING`` selected: sync off = the UV edge selection (all faces
    selected, so the UV Editor shows them), sync on = the mesh edges."""
    bpy.ops.object.mode_set(mode='EDIT')
    ts = bpy.context.scene.tool_settings
    if sync:
        bpy.ops.allset.uv_component(mode='EDGE')
        ts.use_uv_select_sync = True
    else:
        bpy.ops.allset.uv_component(mode='UV_EDGE')
        assert not ts.use_uv_select_sync
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.active
    bm.faces.ensure_lookup_table()
    on = set()
    for fi, corners in where.items():
        f = bm.faces[fi]
        for k, lp in enumerate(f.loops):
            if corners[k][1] == RING and corners[(k + 1) % 4][1] == RING:
                on.add(lp.edge)
    for el in (*bm.verts, *bm.edges, *bm.faces):
        el.select = False
    if sync:
        for e in on:
            e.select = True
            for v in e.verts:
                v.select = True
        compat.uv_sync_from_mesh(bm)
    else:
        for f in bm.faces:
            f.select = True
        ring_verts = {v for e in on for v in e.verts}
        for f in bm.faces:
            for lp in f.loops:
                compat.set_uv_vert_selected(lp, uv, lp.vert in ring_verts and len(f.verts) == 4)
                compat.set_uv_edge_selected(lp, uv, lp.edge in on and len(f.verts) == 4)
    bmesh.update_edit_mesh(ob.data)
    return len(on)


def _grid(ob, where):
    """(i, j) -> UV of the side shell, and every cap UV."""
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.active
    bm.faces.ensure_lookup_table()
    grid, caps = {}, []
    for f in bm.faces:
        if f.index in where:
            for lp, ij in zip(f.loops, where[f.index]):
                p = lp[uv].uv.copy()
                if ij in grid:
                    assert (grid[ij] - p).length < 1e-5, ("one UV per side corner", ij, grid[ij], p)
                grid[ij] = p
        else:
            caps += [tuple(round(c, 6) for c in lp[uv].uv) for lp in f.loops]
    return grid, caps


def _length(pts):
    return sum((pts[k + 1] - pts[k]).length for k in range(len(pts) - 1))


def test_menu_item_runs_the_kit_command():
    assert menu_map.spec(ITEM)[1] == "allset.uv_straighten_shell", menu_map.spec(ITEM)


def _straighten(sync):
    ob, where = _cylinder()
    assert _select_ring(ob, where, sync) == N
    grid0, caps0 = _grid(ob, where)
    line0 = [grid0[i, RING] for i in range(N + 1)]
    res = bpy.ops.allset.menu_item(item=ITEM)
    assert res == {'FINISHED'}, res
    assert bpy.context.mode == 'EDIT_MESH'
    grid, caps = _grid(ob, where)
    width = max(p.x for p in grid.values()) - min(p.x for p in grid.values())
    height = max(p.y for p in grid.values()) - min(p.y for p in grid.values())
    assert height > 2 * width, ("still standing upright", width, height)
    tol = 1e-4 * height
    line = [grid[i, RING] for i in range(N + 1)]
    # the loop: a straight line along V, its length kept, where it was
    assert max(p.x for p in line) - min(p.x for p in line) < tol, [round(p.x, 5) for p in line]
    assert abs(_length(line) - _length(line0)) < 1e-3 * _length(line0), (_length(line), _length(line0))
    mid0 = (line0[0] + line0[-1]) / 2
    mid = (line[0] + line[-1]) / 2
    assert (mid - mid0).length < 0.05 * height, (mid, mid0)
    # the whole shell: a straight strip (each ring a vertical line, each side edge across it level)
    for j in range(H + 1):
        us = [grid[i, j].x for i in range(N + 1)]
        assert max(us) - min(us) < tol, ("ring straight", j, max(us) - min(us))
    for i in range(N + 1):
        vs = [grid[i, j].y for j in range(H + 1)]
        assert max(vs) - min(vs) < tol, ("level across", i, max(vs) - min(vs))
    # the rings keep their order and spacing (the cylinder side is 2 units tall and 2 pi around)
    xs = [grid[0, j].x for j in range(H + 1)]
    xs0 = [grid0[0, j].x for j in range(H + 1)]
    # not mirrored: the rings run across the strip the way they ran before (no reversed UVs)
    assert all(b > a for a, b in zip(xs, xs[1:])) and all(b > a for a, b in zip(xs0, xs0[1:])), (xs0, xs)
    assert abs(abs(xs[-1] - xs[0]) / _length(line) - 2.0 / (2 * N * math.sin(math.pi / N))) < 1e-3
    assert caps == caps0, "the other shells stay"
    # the selection stays, nothing is left pinned
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.active
    assert not any(lp[uv].pin_uv for f in bm.faces for lp in f.loops)
    if not sync:
        picked = {lp.vert for f in bm.faces for lp in f.loops if compat.uv_vert_selected(lp, uv)}
        assert len(picked) == N, len(picked)
    else:
        assert sum(e.select for e in bm.edges) == N
    bpy.ops.object.mode_set(mode='OBJECT')


def test_straighten_shell_uv_edge_loop():
    _straighten(sync=False)


def test_straighten_shell_with_uv_sync():
    _straighten(sync=True)


def test_one_uv_is_a_warning():
    ob, where = _cylinder()
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.allset.uv_component(mode='UV')
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.active
    bm.faces.ensure_lookup_table()
    one = bm.faces[0].loops[0].vert
    for f in bm.faces:
        f.select = True
        for lp in f.loops:
            compat.set_uv_vert_selected(lp, uv, lp.vert is one and f.index == 0)
            compat.set_uv_edge_selected(lp, uv, False)
    bmesh.update_edit_mesh(ob.data)
    grid0, caps0 = _grid(ob, where)
    res = bpy.ops.allset.uv_straighten_shell()
    assert res == {'CANCELLED'}, res
    assert bpy.ops.allset.menu_item(item=ITEM) == {'FINISHED'}     # the menu item reports the warning
    grid, caps = _grid(ob, where)
    assert grid == grid0 and caps == caps0
    bpy.ops.object.mode_set(mode='OBJECT')
