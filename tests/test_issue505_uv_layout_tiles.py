"""#505: UV Editor > Modify > Layout spreads the shells over several UDIM tiles with the Layout UVs Options
Shell Distribution (Distribute / Shell Centers) and Tiles U / V, like Maya.

Distribute shares the shells out over the tiles by area in shell order (tiles along U first, then up V); Shell
Centers keeps each shell in the tile its centre is in (shells outside the tiles go together into the tile below the
first one). Each tile is packed and filled on its own. One tile = the layout as before."""

import math
from importlib import import_module

import bmesh
import bpy

import kit

ow = import_module(kit.MODULE + ".operators.option_windows")
uvl = import_module(kit.MODULE + ".operators.uv_layout")
uvt = import_module(kit.MODULE + ".operators.uv_tools")


def _quads(specs):
    """One mesh of separate quads; spec = (3D width, UV centre) per quad (UV size 0.3)."""
    ow.store("uv_layout", None)
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    me = bpy.data.meshes.new("quads")
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    for i, (w, (cu, cv)) in enumerate(specs):
        x = i * 3.0
        vs = [bm.verts.new(p) for p in ((x, 0, 0), (x + w, 0, 0), (x + w, 1, 0), (x, 1, 0))]
        f = bm.faces.new(vs)
        for loop, (du, dv) in zip(f.loops, ((-1, -1), (1, -1), (1, 1), (-1, 1))):
            loop[uv].uv = (cu + 0.15 * du, cv + 0.15 * dv)
    bm.to_mesh(me)
    ob = bpy.data.objects.new("quads", me)
    bpy.context.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.scene.tool_settings.use_uv_select_sync = True
    bpy.ops.mesh.select_mode(type='FACE')
    bpy.ops.mesh.select_all(action='SELECT')
    return ob


def _boxes(ob):
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.active
    out = []
    for f in sorted(bm.faces, key=lambda f: f.index):
        us = [l[uv].uv.x for l in f.loops]
        vs = [l[uv].uv.y for l in f.loops]
        out.append((min(us), max(us), min(vs), max(vs)))
    return out


def _tile(box):
    t = (math.floor(box[0] + 1e-6), math.floor(box[2] + 1e-6))
    assert box[1] <= t[0] + 1 + 1e-6 and box[3] <= t[1] + 1 + 1e-6, ("a shell crosses a tile border", box)
    return t


def _layout(**values):
    v = {**ow.current("uv_layout"), **values}
    return bpy.ops.allset.opt_uv_layout('EXEC_DEFAULT', **v)


SPECS = [(1.0, (0.5, 0.5)), (1.3, (0.5, 0.5)), (1.6, (0.5, 0.5)), (1.9, (0.5, 0.5)), (2.2, (0.5, 0.5))]


def test_window_fields():
    w = ow.find_path("UV Editor/Modify/Layout")
    d = w.defaults()
    assert (d["distribution"], d["tiles_u"], d["tiles_v"]) == ("Distribute", 1, 1)
    assert not any("Tiles" in m for m in w.missing)


def test_distribute_over_two_tiles_along_u():
    ob = _quads(SPECS)
    assert _layout(tiles_u=2) == {'FINISHED'}
    tiles = [_tile(b) for b in _boxes(ob)]
    # areas 1, 1.3, 1.6, 1.9, 2.2: the first three shells' share falls in the first tile, the rest in the second
    assert tiles == [(0, 0), (0, 0), (0, 0), (1, 0), (1, 0)], tiles
    boxes = _boxes(ob)
    for t in ((0, 0), (1, 0)):       # each tile is filled on its own
        inside = [b for b, tt in zip(boxes, tiles) if tt == t]
        assert max(max(b[1] for b in inside) - t[0], max(b[3] for b in inside) - t[1]) > 0.99


def test_distribute_over_tiles_up_v_and_three_tiles():
    ob = _quads(SPECS)
    assert _layout(tiles_v=2) == {'FINISHED'}
    assert [_tile(b) for b in _boxes(ob)] == [(0, 0), (0, 0), (0, 0), (0, 1), (0, 1)]
    ob = _quads(SPECS)
    assert _layout(tiles_u=3) == {'FINISHED'}
    assert [_tile(b) for b in _boxes(ob)] == [(0, 0), (0, 0), (1, 0), (1, 0), (2, 0)]


def test_shell_centers_keep_their_tiles():
    ob = _quads([(1.0, (0.4, 0.3)), (1.0, (1.5, 0.4)), (1.0, (2.6, 0.5)), (1.0, (0.3, 1.4)), (1.0, (1.7, 1.7)),
                 (1.0, (-0.4, 0.6))])
    assert _layout(distribution="Shell Centers", tiles_u=2, tiles_v=2) == {'FINISHED'}
    tiles = [_tile(b) for b in _boxes(ob)]
    assert tiles == [(0, 0), (1, 0), (0, -1), (0, 1), (1, 1), (0, -1)], tiles
    assert ow.saved("uv_layout")["distribution"] == "Shell Centers"


def test_one_tile_is_the_plain_layout():
    ob = _quads(SPECS)
    assert _layout() == {'FINISHED'}
    plain = _boxes(ob)
    ob = _quads(SPECS)
    assert _layout(distribution="Shell Centers") == {'FINISHED'}
    assert all(abs(a - b) < 1e-6 for p, q in zip(plain, _boxes(ob)) for a, b in zip(p, q))
    assert all(_tile(b) == (0, 0) for b in plain)
