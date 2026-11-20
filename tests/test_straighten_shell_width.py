"""Straighten Shell gives the shell Maya's width. Like Maya, the shell is unfolded around the straightened line starting
from its own UV layout with a limited effort: a line that runs the long way of a ribbon, or crosses a ribbon one face
tall, lets the shell reach its 3D proportions; a line that crosses a ribbon two or more faces tall changes the shell's
width across the line only part of the way from what it was. The shell stays a straight strip."""

import math
from importlib import import_module

import bmesh
import bpy

import kit

compat = import_module(kit.MODULE + ".compat")


def _clear():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)


def _ribbon(sx=20, sh=10, r=1.0, h=2.0, su=1.0):
    """A cylinder side (no caps), cut along one edge line, laid out like a cylinder side in UV space: u = around
    (0..1, times ``su``), v = up (0.25..0.75). Returns the object and face index -> [(i, j) of each corner]."""
    _clear()
    me = bpy.data.meshes.new("ribbon")
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("map1")
    ring = [[bm.verts.new((r * math.cos(2 * math.pi * i / sx), r * math.sin(2 * math.pi * i / sx), h * j / sh))
             for i in range(sx)] for j in range(sh + 1)]
    where = {}
    for j in range(sh):
        for i in range(sx):
            corners = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
            f = bm.faces.new([ring[jj][ii % sx] for ii, jj in corners])
            for lp, (ii, jj) in zip(f.loops, corners):
                lp[uv].uv = (0.5 + (ii / sx - 0.5) * su, 0.25 + 0.5 * jj / sh)
            where[f] = corners
    bm.faces.index_update()
    where = {f.index: c for f, c in where.items()}
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("ribbon", me)
    bpy.context.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    return ob, where


def _straighten(ob, where, on_edge):
    """Select the UV edges for which ``on_edge(corner_a, corner_b)`` holds (UV edge mode, sync off) and run the
    command. Returns the side UVs (i, j) -> (u, v)."""
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.allset.uv_component(mode='UV_EDGE')
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.active
    bm.faces.ensure_lookup_table()
    on = set()
    for fi, c in where.items():
        for k, lp in enumerate(bm.faces[fi].loops):
            if on_edge(c[k], c[(k + 1) % 4]):
                on.add(lp.edge)
    verts = {v for e in on for v in e.verts}
    for f in bm.faces:
        f.select = True
        for lp in f.loops:
            compat.set_uv_vert_selected(lp, uv, lp.vert in verts)
            compat.set_uv_edge_selected(lp, uv, lp.edge in on)
    bmesh.update_edit_mesh(ob.data)
    assert bpy.ops.allset.uv_straighten_shell() == {'FINISHED'}
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.active
    bm.faces.ensure_lookup_table()
    grid = {}
    for fi, c in where.items():
        for lp, ij in zip(bm.faces[fi].loops, c):
            grid[ij] = lp[uv].uv.copy()
    bpy.ops.object.mode_set(mode='OBJECT')
    return grid


def _box(grid):
    us = [p.x for p in grid.values()]
    vs = [p.y for p in grid.values()]
    return max(us) - min(us), max(vs) - min(vs)


def _column(sx=20, sh=10, **kw):
    ob, where = _ribbon(sx=sx, sh=sh, **kw)
    col = sx // 2
    grid = _straighten(ob, where, lambda a, b: a[0] == b[0] == col)
    w, h = _box(grid)
    line = [grid[col, j].x for j in range(sh + 1)]
    assert max(line) - min(line) < 1e-5, "the line is straight along V"
    assert abs(h - 0.5) < 1e-3, ("the line keeps its length and the strip its height", h)
    for j in range(sh + 1):         # still a straight strip: every row of UVs level
        vs = [grid[i, j].y for i in range(sx + 1)]
        assert max(vs) - min(vs) < 1e-3 * h, ("row level", j, max(vs) - min(vs))
    return w, h


def test_line_across_a_tall_ribbon_keeps_about_its_width():
    # 3D proportions would make it about 3.1 times as wide as tall; it was 2 times
    w, h = _column(sh=10)
    assert 2.1 < w / h < 2.35, w / h
    w, h = _column(sh=4)
    assert 2.1 < w / h < 2.35, w / h
    w, h = _column(sh=10, h=4.0)            # here the 3D proportions are narrower than the layout
    assert 1.75 < w / h < 2.0, w / h


def test_line_across_a_short_ribbon_reaches_the_3d_proportions():
    full = 2 * 20 * math.sin(math.pi / 20) / 2.0        # around / up
    w, h = _column(sh=1)
    assert abs(w / h - full) < 0.01 * full, (w / h, full)
    w, h = _column(sh=2)
    assert 2.6 < w / h < 2.85, w / h


def test_line_along_a_ribbon_reaches_the_3d_proportions():
    ob, where = _ribbon(sh=4)
    grid = _straighten(ob, where, lambda a, b: a[1] == b[1] == 2)
    w, h = _box(grid)
    full = 2 * 20 * math.sin(math.pi / 20) / 2.0
    assert abs(w / h - full) < 0.01 * full, (w / h, full)
