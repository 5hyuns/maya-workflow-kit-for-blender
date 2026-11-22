"""Mesh > Fill Hole with one border edge of a hole selected closes that whole hole, like Maya (GitHub #?)."""

import bmesh
import bpy

import kit  # noqa: F401


def _plane_with_hole():
    """A 4 x 4 quad grid with its middle 2 x 2 faces deleted (an inner hole of 8 edges), edit mode, edge select."""
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    verts = [(i - 2.0, j - 2.0, 0.0) for j in range(5) for i in range(5)]
    faces = [(i + 5 * j, i + 1 + 5 * j, i + 6 + 5 * j, i + 5 + 5 * j) for j in range(4) for i in range(4)]
    faces = [f for k, f in enumerate(faces) if k not in (5, 6, 9, 10)]
    me = bpy.data.meshes.new("holed")
    me.from_pydata(verts, [], faces)
    ob = bpy.data.objects.new("pPlane1", me)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.tool_settings.mesh_select_mode = (False, True, False)
    bpy.ops.mesh.select_all(action='DESELECT')
    return ob


def _pick(ob, a, b):
    bm = bmesh.from_edit_mesh(ob.data)
    bm.verts.ensure_lookup_table()
    va, vb = bm.verts[a], bm.verts[b]
    next(e for e in va.link_edges if e.other_vert(va) is vb).select = True
    bm.select_flush_mode()
    bmesh.update_edit_mesh(ob.data)


def _sizes(ob):
    return sorted(len(f.verts) for f in bmesh.from_edit_mesh(ob.data).faces)


def test_one_edge_of_the_inner_hole_fills_it():
    ob = _plane_with_hole()
    _pick(ob, 6, 7)                      # one edge of the inner hole
    assert bpy.ops.allset.fill_hole() == {'FINISHED'}
    assert _sizes(ob) == [4] * 12 + [8], _sizes(ob)


def test_one_edge_of_the_outer_border_fills_only_that_border():
    ob = _plane_with_hole()
    _pick(ob, 0, 1)                      # one edge of the outer border
    assert bpy.ops.allset.fill_hole() == {'FINISHED'}
    assert _sizes(ob) == [4] * 12 + [16], _sizes(ob)


def test_every_hole_without_a_selection_is_unchanged():
    ob = _plane_with_hole()
    assert bpy.ops.allset.fill_hole() == {'FINISHED'}
    assert _sizes(ob) == [4] * 12 + [8, 16], _sizes(ob)
