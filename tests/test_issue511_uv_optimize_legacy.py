"""#511: the Optimize UVs Options window has Method: Legacy (relax), like Maya: choosing it switches the window to the
relax settings (Pin UV border, Pin UVs selected / unselected, Edge weights Uniform / World space, Maximum iterations)
and Optimize relaxes the UVs with them.

Legacy relax: the shells of the selection relax as a whole; every free UV moves toward the weighted average of its
neighbours, Maximum iterations solver steps from where the UVs are (enough steps = fully relaxed)."""

import random
from importlib import import_module

import bmesh
import bpy

import kit

ow = import_module(kit.MODULE + ".operators.option_windows")

N = 6
LEGACY = "Legacy (relax)"


def _grid(bend=True, seed=1):
    """A 6 x 6 face grid (bent in 3D when ``bend``) with jittered UVs."""
    ow.store("uv_optimize", None)
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    rnd = random.Random(seed)
    me = bpy.data.meshes.new("grid")
    bm = bmesh.new()
    vs = [bm.verts.new((i / N, j / N, 0.5 * (j / N) ** 2 if bend else 0.0)) for j in range(N + 1)
          for i in range(N + 1)]
    uv = bm.loops.layers.uv.new("UVMap")
    jit = {v: (rnd.uniform(-0.03, 0.03), rnd.uniform(-0.03, 0.03)) for v in vs}
    for j in range(N):
        for i in range(N):
            a = j * (N + 1) + i
            f = bm.faces.new((vs[a], vs[a + 1], vs[a + N + 2], vs[a + N + 1]))
            for loop in f.loops:
                d = jit[loop.vert]
                loop[uv].uv = (loop.vert.co.x + d[0], loop.vert.co.y + d[1])
    bm.to_mesh(me)
    ob = bpy.data.objects.new("grid", me)
    bpy.context.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.scene.tool_settings.use_uv_select_sync = True
    bpy.ops.mesh.select_mode(type='VERT')
    bpy.ops.mesh.select_all(action='SELECT')
    return ob


def _uvs(ob):
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.active
    return {l.vert.index: l[uv].uv.copy() for f in bm.faces for l in f.loops}


def _border(i):
    x, y = i % (N + 1), i // (N + 1)
    return x in (0, N) or y in (0, N)


def _neighbours(i):
    x, y = i % (N + 1), i // (N + 1)
    return [(x + dx) + (y + dy) * (N + 1) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
            if 0 <= x + dx <= N and 0 <= y + dy <= N]


def _run(**values):
    v = {**ow.current("uv_optimize"), "method": LEGACY, **values}
    return bpy.ops.allset.opt_uv_optimize('EXEC_DEFAULT', **v)


def test_window_switches_to_the_relax_settings():
    w = ow.find_path("UV Editor/Modify/Optimize")
    d = w.defaults()
    assert d["method"] == "Unfold3D"
    assert {k: d[k] for k in ("pin_border", "pin_uvs", "pin_which", "edge_weights", "max_iterations")} == {
        "pin_border": True, "pin_uvs": False, "pin_which": "Pin selected UVs", "edge_weights": "Uniform",
        "max_iterations": 5}
    assert not any("Legacy" in m for m in w.missing)
    assert w.enabled(d, "iterations") and not w.enabled(d, "pin_border")
    legacy = {**d, "method": LEGACY}
    assert not w.enabled(legacy, "iterations") and w.enabled(legacy, "max_iterations")
    assert not w.enabled(legacy, "pin_which") and w.enabled({**legacy, "pin_uvs": True}, "pin_which")


def test_relax_keeps_the_border_and_converges_to_the_neighbour_average():
    ob = _grid()
    before = _uvs(ob)
    assert _run() == {'FINISHED'}
    after = _uvs(ob)
    assert all((after[i] - before[i]).length < 1e-7 for i in before if _border(i)), "Pin UV border"
    assert any((after[i] - before[i]).length > 1e-3 for i in before if not _border(i))
    assert _run(max_iterations=500) == {'FINISHED'}
    after = _uvs(ob)
    for i in after:
        if not _border(i):
            mean = sum((after[j] for j in _neighbours(i)), after[i] * 0) / len(_neighbours(i))
            assert (after[i] - mean).length < 1e-6, (i, after[i], mean)


def test_more_iterations_relax_further_and_world_space_differs():
    ob = _grid()
    assert _run(max_iterations=1) == {'FINISHED'}
    one = _uvs(ob)
    ob = _grid()
    assert _run(max_iterations=5) == {'FINISHED'}
    five = _uvs(ob)
    assert any((one[i] - five[i]).length > 1e-4 for i in one)
    ob = _grid()
    assert _run(edge_weights="World space", max_iterations=50) == {'FINISHED'}
    world = _uvs(ob)
    ob = _grid()
    assert _run(max_iterations=50) == {'FINISHED'}
    uniform = _uvs(ob)
    assert max((world[i] - uniform[i]).length for i in world) > 1e-3, "World space follows the bent 3D surface"


def test_pin_uvs_selected_or_unselected():
    ob = _grid()
    bm = bmesh.from_edit_mesh(ob.data)
    for v in bm.verts:
        v.select = v.co.x < 0.45
    bm.select_flush(False)
    bmesh.update_edit_mesh(ob.data)
    picked = {v.index for v in bm.verts if v.select}
    before = _uvs(ob)
    assert _run(pin_uvs=True) == {'FINISHED'}
    after = _uvs(ob)
    assert all((after[i] - before[i]).length < 1e-7 for i in picked), "selected UVs pinned"
    assert any((after[i] - before[i]).length > 1e-4 for i in after if i not in picked and not _border(i))
    ob = _grid()
    bm = bmesh.from_edit_mesh(ob.data)
    for v in bm.verts:
        v.select = v.co.x < 0.45
    bm.select_flush(False)
    bmesh.update_edit_mesh(ob.data)
    before = _uvs(ob)
    assert _run(pin_uvs=True, pin_which="Pin unselected UVs", pin_border=False) == {'FINISHED'}
    after = _uvs(ob)
    assert all((after[i] - before[i]).length < 1e-7 for i in after if i not in picked), "unselected UVs pinned"
    assert any((after[i] - before[i]).length > 1e-4 for i in picked if _border(i)), "the border is free"


def test_saved_legacy_drives_the_menu_item():
    ob = _grid()
    ow.store("uv_optimize", {**ow.current("uv_optimize"), "method": LEGACY, "max_iterations": 500})
    assert bpy.ops.allset.menu_item(item="UV Editor/Modify/Optimize") == {'FINISHED'}
    after = _uvs(ob)
    i = 3 + 3 * (N + 1)
    mean = sum((after[j] for j in _neighbours(i)), after[i] * 0) / 4
    assert (after[i] - mean).length < 1e-6
