"""UV Toolkit Unfold Along U / V (#557): one run unfolds the shell all the way along the axis (a second run changes
nothing), the scale comes from the coordinate that stays, and with part of a shell selected only the selected UVs
move while the rest of the shell holds them, like Maya."""
import math

import bmesh
import bpy

import kit
from importlib import import_module

compat = import_module(kit.MODULE + ".compat")


def _clear():
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)


def _grid(name, w, h, sx, sy, uvf):
    """A flat w x h grid of sx x sy quads, one UV shell; ``uvf(x, y)`` gives each corner's UV."""
    _clear()
    verts = [(w * i / sx, h * j / sy, 0.0) for j in range(sy + 1) for i in range(sx + 1)]
    faces = [(j * (sx + 1) + i, j * (sx + 1) + i + 1, (j + 1) * (sx + 1) + i + 1, (j + 1) * (sx + 1) + i)
             for j in range(sy) for i in range(sx)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.uv_layers.new(name="map1")
    bm = bmesh.new()
    bm.from_mesh(me)
    uv = bm.loops.layers.uv.active
    for f in bm.faces:
        for lp in f.loops:
            lp[uv].uv = uvf(lp.vert.co.x, lp.vert.co.y)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT')
    return ob


def _select_faces(ob, faces=None):
    """UV Sync Selection on, face mode: ``faces`` selected (every face when None)."""
    ts = bpy.context.scene.tool_settings
    ts.use_uv_select_sync = True
    ts.mesh_select_mode = (False, False, True)
    bm = bmesh.from_edit_mesh(ob.data)
    bm.faces.ensure_lookup_table()
    for seq in (bm.verts, bm.edges, bm.faces):
        for el in seq:
            el.select = False
    for f in bm.faces:
        if faces is None or f.index in faces:
            f.select_set(True)
    bm.select_mode = {'FACE'}
    bm.select_flush_mode()
    compat.uv_sync_from_mesh(bm)
    bmesh.update_edit_mesh(ob.data)


def _uvs(ob):
    """vertex index -> UV (one shell: one UV per vertex)."""
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.active
    return {lp.vert.index: tuple(lp[uv].uv) for f in bm.faces for lp in f.loops}


def _extent(uvs, k):
    vals = [p[k] for p in uvs.values()]
    return max(vals) - min(vals)


def _close(a, b, tol=1e-4):
    return all(abs(a[i][0] - b[i][0]) < tol and abs(a[i][1] - b[i][1]) < tol for i in a)


def test_strip_unfolds_all_the_way_in_one_run():
    # a 3 x 1 strip of three faces whose UVs fill the unit square: U is squashed to a third
    ob = _grid("strip", 3.0, 1.0, 3, 1, lambda x, y: (x / 3.0, y))
    _select_faces(ob)
    before = _uvs(ob)
    assert bpy.ops.allset.uv_unfold_along(axis='U') == {'FINISHED'}
    once = _uvs(ob)
    assert abs(_extent(once, 0) - 3.0) < 1e-4, once          # the full 3D width at the scale V already has
    assert all(once[i][1] == before[i][1] for i in once)      # V stays
    mean = sum(p[0] for p in once.values()) / len(once)
    assert abs(mean - 0.5) < 1e-5, mean                       # whole shell selected: its U centre stays
    assert bpy.ops.allset.uv_unfold_along(axis='U') == {'FINISHED'}
    assert _close(_uvs(ob), once, 1e-6)                       # nothing left to unfold
    # Along V on the same strip: V shrinks to the scale U has (a third), around its centre
    ob = _grid("strip", 3.0, 1.0, 3, 1, lambda x, y: (x / 3.0, y))
    _select_faces(ob)
    assert bpy.ops.allset.uv_unfold_along(axis='V') == {'FINISHED'}
    after = _uvs(ob)
    assert abs(_extent(after, 1) - 1.0 / 3.0) < 1e-4, after
    assert abs(_extent(after, 0) - 1.0) < 1e-9
    assert abs(sum(p[1] for p in after.values()) / len(after) - 0.5) < 1e-5


def test_scale_comes_from_the_axis_that_stays():
    # a 1 x 3 strip with V squashed to 0.3: Unfold Along U makes U 0.1 (V's 0.3 over a 3D height of 3)
    ob = _grid("vstrip", 1.0, 3.0, 1, 3, lambda x, y: (x, 0.35 + 0.1 * y))
    _select_faces(ob)
    assert bpy.ops.allset.uv_unfold_along(axis='U') == {'FINISHED'}
    assert abs(_extent(_uvs(ob), 0) - 0.1) < 1e-4, _uvs(ob)


def test_turned_shell_becomes_an_undistorted_copy():
    # a 2 x 1 plane whose UVs are its shape turned 30 degrees and squashed along V: Unfold Along V gives every edge
    # the same UV-per-3D length (an undistorted copy)
    a = math.radians(30.0)

    def uvf(x, y):
        u, v = 0.5 * x, 0.5 * y
        return (u * math.cos(a) - v * math.sin(a), 0.6 * (u * math.sin(a) + v * math.cos(a)))
    ob = _grid("turned", 2.0, 1.0, 4, 2, uvf)
    _select_faces(ob)
    assert bpy.ops.allset.uv_unfold_along(axis='V') == {'FINISHED'}
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.active
    ratios = []
    for f in bm.faces:
        for lp in f.loops:
            nx = lp.link_loop_next
            ratios.append((lp[uv].uv - nx[uv].uv).length / (lp.vert.co - nx.vert.co).length)
    assert max(ratios) - min(ratios) < 1e-3, (min(ratios), max(ratios))


def test_part_of_a_shell_moves_only_its_uvs():
    # a 1 x 6 strip, U squashed to 0.3 wide; the bottom three faces selected: their UVs (the shared row too) take
    # the scale 0.3 per face height, held by the unselected top of the shell, which stays
    ob = _grid("s6", 1.0, 6.0, 1, 6, lambda x, y: (0.35 + 0.3 * x, y / 6.0))
    _select_faces(ob, {0, 1, 2})
    before = _uvs(ob)
    assert bpy.ops.allset.uv_unfold_along(axis='V') == {'FINISHED'}
    after = _uvs(ob)
    for i, (u, v) in after.items():
        assert u == before[i][0]                              # U stays everywhere
        row = round(before[i][1] * 6.0)
        if row >= 4:
            assert abs(v - before[i][1]) < 1e-9, (i, v)       # not selected: stays
        else:
            want = 4.0 / 6.0 - 0.3 * (4 - row)
            assert abs(v - want) < 1e-4, (i, row, v, want)
