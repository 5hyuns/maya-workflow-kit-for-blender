"""#527: with UV Sync Selection on and the mesh selection shown (a face picked in the 3D View), face select mode
draws only the picked faces' border sides in the selection colour (``uv_display.selected_segments``), like Maya: a
side of another shell on the same mesh edge stays unselected. Vertex / edge mode keep both sides of a selected edge.
GUI: tests/gui/gui_issue527_uv_face_highlight.py."""

from importlib import import_module

import bmesh
import bpy

import kit

compat = import_module(kit.MODULE + ".compat")
uvd = import_module(kit.MODULE + ".ui.uv_display")


def _clear():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)


def _two_shells():
    """Two quads sharing the edge x = 1; the right quad's UVs moved off (two shells), nothing selected."""
    _clear()
    me = bpy.data.meshes.new("two")
    me.from_pydata([(0, 0, 0), (1, 0, 0), (2, 0, 0), (0, 1, 0), (1, 1, 0), (2, 1, 0)], [],
                   [(0, 1, 4, 3), (1, 2, 5, 4)])
    me.uv_layers.new(name="UVMap")
    ob = bpy.data.objects.new("two", me)
    bpy.context.collection.objects.link(ob)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(me)
    uv = bm.loops.layers.uv.active
    for f in bm.faces:
        right = f.calc_center_median().x > 1.0
        for loop in f.loops:
            loop[uv].uv = (loop.vert.co.x * 0.25 + (0.25 if right else 0.0), loop.vert.co.y * 0.25)
    for el in (*bm.verts, *bm.edges, *bm.faces):
        el.select = False
    bmesh.update_edit_mesh(me)
    uvd._invalidate()
    return ob


def _segs(points):
    return {tuple(sorted(((round(p[0], 4), round(p[1], 4)), (round(q[0], 4), round(q[1], 4)))))
            for p, q in zip(points[0::2].tolist(), points[1::2].tolist())}


LEFT = {((0.0, 0.0), (0.25, 0.0)), ((0.25, 0.0), (0.25, 0.25)), ((0.0, 0.25), (0.25, 0.25)),
        ((0.0, 0.0), (0.0, 0.25))}
RIGHT_SHARED = ((0.5, 0.0), (0.5, 0.25))        # the right shell's side on the shared mesh edge


def _pick_face(ob, left=True):
    bm = bmesh.from_edit_mesh(ob.data)
    for el in (*bm.verts, *bm.edges, *bm.faces):
        el.select = False
    face = min(bm.faces, key=lambda f: f.calc_center_median().x * (1 if left else -1))
    face.select_set(True)
    bm.select_flush_mode()
    bmesh.update_edit_mesh(ob.data)
    return bm


def test_face_mode_draws_only_the_picked_face_sides():
    ob = _two_shells()
    ts = bpy.context.scene.tool_settings
    ts.use_uv_select_sync = True
    ts.mesh_select_mode = (False, False, True)
    bm = _pick_face(ob)
    assert not getattr(bm, "uv_select_sync_valid", False), "a mesh pick: the UV Editor shows the mesh selection"
    got = _segs(uvd.selected_segments(ob, True))
    assert got == LEFT, got
    assert RIGHT_SHARED not in got, "the other shell's side on the shared edge is not drawn selected"
    _pick_face(ob, left=False)
    bpy.context.evaluated_depsgraph_get()
    got = _segs(uvd.selected_segments(ob, True))
    assert RIGHT_SHARED in got and not got & LEFT, got


def test_edge_and_vertex_mode_keep_both_sides_of_a_selected_edge():
    ob = _two_shells()
    ts = bpy.context.scene.tool_settings
    ts.use_uv_select_sync = True
    ts.mesh_select_mode = (False, False, True)
    _pick_face(ob)
    assert RIGHT_SHARED not in _segs(uvd.selected_segments(ob, True))
    for mode in ((False, True, False), (True, False, False)):
        ts.mesh_select_mode = mode          # the same selection counts: the mode change alone updates the lines
        bpy.context.evaluated_depsgraph_get()
        got = _segs(uvd.selected_segments(ob, True))
        assert RIGHT_SHARED in got and LEFT <= got, (mode, got)


def test_uv_sync_off_still_reads_the_uv_selection():
    ob = _two_shells()
    ts = bpy.context.scene.tool_settings
    ts.use_uv_select_sync = False
    ts.mesh_select_mode = (False, False, True)
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.active
    for f in bm.faces:
        f.select_set(True)
        compat.set_uv_face_selected(f, uv, False)
    left = min(bm.faces, key=lambda f: f.calc_center_median().x)
    compat.set_uv_face_selected(left, uv, True)
    bmesh.update_edit_mesh(ob.data)
    uvd._invalidate()
    assert _segs(uvd.selected_segments(ob, False)) == LEFT
