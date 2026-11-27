"""#579: soft select colours in the UV Editor follow Blender's UV transform (what a UV move with soft select on
moves), and the UV manipulator reads the UV selection afresh (a UV pick with UV Sync off sends no depsgraph update).
GUI: tests/gui/gui_issue579_uv_soft.py."""

from importlib import import_module

import bmesh
import bpy
import numpy as np

import kit

overlay = import_module(kit.MODULE + ".ui.uv_soft_overlay")
manip = import_module(kit.MODULE + ".ui.uv_manipulator")
uv_arrays = import_module(kit.MODULE + ".operators.uv_arrays")
soft = import_module(kit.MODULE + ".operators.soft_select")

STEP = 0.1


def _clear():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for me in list(bpy.data.meshes):
        bpy.data.meshes.remove(me)


def _grid(n=13, gap=0.0):
    """An n x n vertex grid with UVs 0..1 in edit mode, UV Sync off, every face shown, one middle UV picked.
    ``gap``: the right half's UVs moved that far right (a second UV shell beside the first)."""
    _clear()
    me = bpy.data.meshes.new("grid")
    bm = bmesh.new()
    bm.loops.layers.uv.new("UVMap")
    bmesh.ops.create_grid(bm, x_segments=n - 1, y_segments=n - 1, size=1.0, calc_uvs=True)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("grid", me)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    ts = bpy.context.scene.tool_settings
    ts.use_uv_select_sync = False
    ts.uv_select_mode = 'VERTEX'
    bm = bmesh.from_edit_mesh(me)
    uv = bm.loops.layers.uv.active
    for f in bm.faces:
        f.select = True
        if gap and f.calc_center_median().x > 0:
            for l in f.loops:
                l[uv].uv.x += gap
    target = min(bm.verts, key=lambda v: (v.co.x + 0.08) ** 2 + v.co.y ** 2)     # left of the middle
    for f in bm.faces:
        for l in f.loops:
            l.uv_select_vert = l.vert is target
            l.uv_select_edge = False
    bmesh.update_edit_mesh(me)
    return ob


def _uv_area():
    w = bpy.context.window_manager.windows[0]
    area = max(w.screen.areas, key=lambda a: a.width * a.height)
    area.type = 'IMAGE_EDITOR'
    area.ui_type = 'UV'
    return w, area, next(r for r in area.regions if r.type == 'WINDOW')


def _corner_uvs(ob):
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.active
    return np.array([l[uv].uv[:] for f in bm.faces for l in f.loops])


def _check(falloff, connected, radius, gap=0.0, image=None):
    ob = _grid(gap=gap)
    ts = bpy.context.scene.tool_settings
    ts.proportional_edit_falloff = falloff
    ts.proportional_size = radius
    ts.use_proportional_connected = connected
    soft.set_on(True)
    w, area, region = _uv_area()
    area.spaces.active.image = image
    uv_arrays.invalidate()
    overlay._cache.clear()
    with bpy.context.temp_override(window=w, area=area, region=region):
        states = overlay._refresh(bpy.context, area.spaces.active)
        st = states[0]
        weights = np.zeros(len(_corner_uvs(ob)))
        weights[st.loops] = st.w
        before = _corner_uvs(ob)
        bpy.ops.transform.translate(value=(0, STEP, 0), use_proportional_edit=True, proportional_edit_falloff=falloff,
                                    proportional_size=radius, use_proportional_connected=connected)
    moved = (_corner_uvs(ob)[:, 1] - before[:, 1]) / STEP
    bad = np.flatnonzero(np.abs(moved - weights) > 1e-3)
    assert bad.size == 0, (falloff, connected, gap, [(int(i), float(moved[i]), float(weights[i])) for i in bad[:8]])
    assert (weights > 0).sum() > 8 and (weights == 0).sum() > 8, (weights > 0).sum()
    return weights


def test_weights_equal_blender_uv_move():
    for f in ('SMOOTH', 'LINEAR', 'SPHERE', 'SHARP', 'CONSTANT'):
        _check(f, False, 0.3)


def test_connected_weights_follow_the_shell():
    """With Connected the other shell, a small gap away, stays out; without it the gap is crossed."""
    on = _check('LINEAR', True, 0.35, gap=0.05)
    off = _check('LINEAR', False, 0.35, gap=0.05)
    assert (off > 0).sum() > (on > 0).sum(), ((off > 0).sum(), (on > 0).sum())


def test_image_aspect_stretches_the_distance():
    img = bpy.data.images.new("wide", 512, 256)
    try:
        _check('LINEAR', False, 0.3, image=img)
        _check('LINEAR', True, 0.3, image=img)
    finally:
        bpy.data.images.remove(img)


def test_uv_aspect():
    class _S:
        image = None
    assert overlay.uv_aspect(_S()) == (1.0, 1.0)
    img = bpy.data.images.new("tall", 128, 512)
    try:
        _S.image = img
        assert overlay.uv_aspect(_S()) == (1.0, 4.0), overlay.uv_aspect(_S())
    finally:
        bpy.data.images.remove(img)


def test_manipulator_reads_a_new_uv_pick_on_the_selection_signal():
    """The shared arrays live on after a UV pick (no depsgraph update): the UV Editor's selection signal (its gizmo
    refresh, ``uv_arrays.selection_changed``) makes the manipulator's box follow the pick; redraws without it don't
    read the UV selection again."""
    ob = _grid()
    w, area, region = _uv_area()
    with bpy.context.temp_override(window=w, area=area, region=region):
        b0 = manip.selected_uv_bounds(bpy.context)
        reads = uv_arrays.STATS["uv_sel_reads"]
        for _ in range(5):                              # redraws with no selection change (view moves, hovers)
            assert manip.selected_uv_bounds(bpy.context) == b0
        assert uv_arrays.STATS["uv_sel_reads"] == reads, "no re-read without the selection signal"
        bm = bmesh.from_edit_mesh(ob.data)
        uv = bm.loops.layers.uv.active
        far = max((l for f in bm.faces for l in f.loops), key=lambda l: l[uv].uv.x + l[uv].uv.y)
        for f in bm.faces:
            for l in f.loops:
                l.uv_select_vert = l.vert is far.vert
        uv_arrays.selection_changed()                   # what the UV Editor's gizmo refresh does
        b1 = manip.selected_uv_bounds(bpy.context)
        assert uv_arrays.STATS["uv_sel_reads"] == reads + 1
    assert b0 is not None and b1 is not None
    assert abs(b1[2] - far[uv].uv.x) < 1e-6 and abs(b1[3] - far[uv].uv.y) < 1e-6, (b0, b1)
    assert b0 != b1


def test_selection_watch_is_registered():
    assert "bl_rna" in manip.ALLSET_GGT_uv_select_watch.__dict__   # registered


def test_overlay_handler_registered():
    assert overlay._handle, "UV Editor POST_PIXEL draw handler"
