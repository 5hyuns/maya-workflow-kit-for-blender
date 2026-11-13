"""#361: a selected edge on a UV shell border is drawn again in the selection colour over the thick texture / shell
border line (``uv_display.selected_segments``), with UV Sync Selection on (mesh edge selection) and off (UV edge
selection), and the selection is read on every redraw. GUI: tests/gui/gui_issue361_uv_border_selection.py."""

import time
from importlib import import_module

import bmesh
import bpy

import kit

compat = import_module(kit.MODULE + ".compat")
uvd = import_module(kit.MODULE + ".ui.uv_display")
uvt = import_module(kit.MODULE + ".operators.uv_tools")


def _clear():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)


def _grid():
    """A 4 x 4 quad grid in edit mode, one UV shell (UVs = x, y / 4), nothing selected."""
    _clear()
    n = 4
    verts = [(x, y, 0.0) for y in range(n + 1) for x in range(n + 1)]
    faces = [(y * (n + 1) + x, y * (n + 1) + x + 1, (y + 1) * (n + 1) + x + 1, (y + 1) * (n + 1) + x)
             for y in range(n) for x in range(n)]
    me = bpy.data.meshes.new("grid")
    me.from_pydata(verts, [], faces)
    me.uv_layers.new(name="UVMap")
    ob = bpy.data.objects.new("grid", me)
    bpy.context.collection.objects.link(ob)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(me)
    uv = bm.loops.layers.uv.active
    for f in bm.faces:
        for loop in f.loops:
            loop[uv].uv = (loop.vert.co.x / n, loop.vert.co.y / n)
    for el in (*bm.verts, *bm.edges, *bm.faces):
        el.select = False
    bmesh.update_edit_mesh(me)
    uvd._invalidate()
    return ob


def _edge(bm, a, b):
    for e in bm.edges:
        if sorted((round(v.co.x), round(v.co.y)) for v in e.verts) == sorted((a, b)):
            return e
    raise AssertionError(f"no edge {a} {b}")


def _segs(points):
    return {tuple(sorted(((round(p[0], 4), round(p[1], 4)), (round(q[0], 4), round(q[1], 4)))))
            for p, q in zip(points[0::2].tolist(), points[1::2].tolist())}


def _sync(edge_mode=True):
    ts = bpy.context.scene.tool_settings
    ts.use_uv_select_sync = True
    ts.mesh_select_mode = (False, True, False) if edge_mode else (True, False, False)


def _pick(ob, bm, *edges):
    for el in (*bm.verts, *bm.edges, *bm.faces):
        el.select = False
    for e in edges:
        e.select_set(True)
    bm.select_flush_mode()
    compat.uv_sync_from_mesh(bm)
    bmesh.update_edit_mesh(ob.data)


def test_selected_outline_edge_is_drawn_selected():
    ob = _grid()
    _sync()
    bm = bmesh.from_edit_mesh(ob.data)
    assert len(uvd.segments_of(ob, True)) == 2 * 16, "the grid's outline"
    assert not len(uvd.selected_segments(ob, True)), "nothing selected"
    _pick(ob, bm, _edge(bm, (0, 0), (1, 0)))
    assert _segs(uvd.selected_segments(ob, True)) == {((0.0, 0.0), (0.25, 0.0))}


def test_inner_edge_is_not_a_border_side():
    ob = _grid()
    _sync()
    bm = bmesh.from_edit_mesh(ob.data)
    _pick(ob, bm, _edge(bm, (2, 1), (2, 2)))
    assert not len(uvd.selected_segments(ob, True)), "an edge inside the shell: Blender's own line shows it"


def test_cut_edge_shows_both_sides_selected():
    ob = _grid()
    _sync()
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.active
    edge = _edge(bm, (2, 1), (2, 2))
    uvt.cut(bm, uv, [edge])
    bmesh.update_edit_mesh(ob.data)
    uvd._invalidate()
    _pick(ob, bm, edge)
    pts = uvd.selected_segments(ob, True)
    assert len(pts) == 4 and _segs(pts) == {((0.5, 0.25), (0.5, 0.5))}, "both sides of the cut edge"


def test_uv_sync_on_follows_each_selection_update():
    """UV Sync on: a selection change sends a depsgraph update, which drops the cached selected lines."""
    ob = _grid()
    _sync()
    bm = bmesh.from_edit_mesh(ob.data)
    _pick(ob, bm, _edge(bm, (0, 0), (1, 0)))
    bpy.context.evaluated_depsgraph_get()
    assert _segs(uvd.selected_segments(ob, True)) == {((0.0, 0.0), (0.25, 0.0))}
    _pick(ob, bm, _edge(bm, (4, 3), (4, 4)))       # the same counts of selected elements
    bpy.context.evaluated_depsgraph_get()
    assert _segs(uvd.selected_segments(ob, True)) == {((1.0, 0.75), (1.0, 1.0))}
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.context.evaluated_depsgraph_get()
    assert not len(uvd.selected_segments(ob, True))


def test_uv_sync_off_uses_the_uv_edge_selection():
    ob = _grid()
    ts = bpy.context.scene.tool_settings
    ts.use_uv_select_sync = False
    ts.uv_select_mode = 'EDGE'
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.active
    for f in bm.faces:          # every face shown in the UV Editor, no UV selected
        f.select = True
        for loop in f.loops:
            compat.set_uv_vert_selected(loop, uv, False)
            compat.set_uv_edge_selected(loop, uv, False)
    bmesh.update_edit_mesh(ob.data)
    uvd._invalidate()
    assert len(uvd.segments_of(ob, False)) == 2 * 16
    assert not len(uvd.selected_segments(ob, False)), "faces selected, no UV edge selected"
    edge = _edge(bm, (0, 4), (0, 3))
    loop = edge.link_loops[0]
    compat.set_uv_edge_selected(loop, uv, True)
    compat.set_uv_vert_selected(loop, uv, True)
    compat.set_uv_vert_selected(loop.link_loop_next, uv, True)
    assert _segs(uvd.selected_segments(ob, False)) == {((0.0, 0.75), (0.0, 1.0))}
    # UV Sync off: a UV selection change sends no depsgraph update, the next redraw still shows it
    compat.set_uv_edge_selected(loop, uv, False)
    assert not len(uvd.selected_segments(ob, False))


def _timed(fn, n=5):
    fn()                            # the first call builds the cached lines and loops
    t = time.perf_counter()
    for _ in range(n):
        out = fn()
    return (time.perf_counter() - t) / n, out


def test_dense_mesh_redraw_stays_light():
    """Every edge of a 48 400-face sphere cut (194 k border sides), everything selected: the selected lines of one
    redraw (UV Sync on: cached until the next selection update; off: read every time), and of the first redraw after a
    selection change."""
    _clear()
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16)
    ob = bpy.context.object
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.subdivide(number_cuts=10)
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.active
    for e in bm.edges:
        e.seam = True
    for f in bm.faces:
        for loop in f.loops:
            compat.set_uv_vert_selected(loop, uv, True)
            compat.set_uv_edge_selected(loop, uv, True)
    bmesh.update_edit_mesh(ob.data)
    uvd._invalidate()
    ts = bpy.context.scene.tool_settings
    ts.use_uv_select_sync = True
    ts.mesh_select_mode = (False, True, False)
    t_sync, pts = _timed(lambda: uvd.selected_segments(ob, True))
    n = len(uvd.segments_of(ob, True)) // 2
    assert len(pts) // 2 == n and n >= 190000, (len(pts), n)
    key = ("selected", (ob.as_pointer(), True))

    def fresh():
        uvd._cache.pop(key, None)
        return uvd.selected_segments(ob, True)
    t_change, pts = _timed(fresh)
    assert len(pts) // 2 == n, len(pts)
    ts.use_uv_select_sync = False
    t_uv, pts = _timed(lambda: uvd.selected_segments(ob, False))
    assert len(pts) // 2 == n, len(pts)
    print(f"{n} border sides, selected lines: UV Sync on {t_sync * 1000:.2f} ms per redraw, "
          f"{t_change * 1000:.1f} ms after a selection change; UV Sync off {t_uv * 1000:.1f} ms per redraw")
    assert t_sync < 0.002, t_sync
    assert t_change < 0.05 and t_uv < 0.05, (t_change, t_uv)
