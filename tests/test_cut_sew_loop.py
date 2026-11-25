"""3D Cut and Sew UV Tool: double-clicking an edge cuts its whole edge loop, Ctrl+double-click sews it back
(the tool's keymap has both)."""

from importlib import import_module

import bmesh
import bpy

import kit

cs = import_module(kit.MODULE + ".operators.cut_sew")
uv_tools = import_module(kit.MODULE + ".operators.uv_tools")

KM = "3D View Tool: Edit Mesh, 3D Cut and Sew UV Tool"


def _cylinder():
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)
    # no caps: every side vertex has four edges, so the middle ring is one closed edge loop
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, end_fill_type='NOTHING')
    ob = bpy.context.active_object
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.subdivide(number_cuts=1)
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.uv.cylinder_project()
    bm = bmesh.from_edit_mesh(ob.data)
    return ob, bm


def _ring_edge(bm):
    """An edge of the middle ring (z = 0, horizontal)."""
    return next(e for e in bm.edges if abs(e.verts[0].co.z) < 1e-6 and abs(e.verts[1].co.z) < 1e-6)


def test_loop_edges_walks_the_ring():
    _ob, bm = _cylinder()
    loop = cs.loop_edges(_ring_edge(bm))
    ring = [e for e in bm.edges if all(abs(v.co.z) < 1e-6 for v in e.verts)]
    assert len(ring) == 16 and set(loop) == set(ring), (len(loop), len(ring))
    assert all(abs(v.co.z) < 1e-6 for e in loop for v in e.verts)


def test_double_click_cuts_and_ctrl_double_click_sews_the_loop():
    ob, bm = _cylinder()
    uv = bm.loops.layers.uv.verify()
    n0 = len(uv_tools.islands(bm, uv))
    idx = _ring_edge(bm).index
    assert bpy.ops.allset.cut_sew_loop('EXEC_DEFAULT', action='CUT', edge_index=idx) == {'FINISHED'}
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.verify()
    assert len(uv_tools.islands(bm, uv)) == n0 + 1, "the ring cut splits the side into two shells"
    assert bpy.ops.allset.cut_sew_loop('EXEC_DEFAULT', action='SEW', edge_index=idx) == {'FINISHED'}
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.verify()
    assert len(uv_tools.islands(bm, uv)) == n0, "sewn back"


def test_keys():
    km = bpy.context.window_manager.keyconfigs.addon.keymaps.get(KM)
    assert km is not None
    got = {(k.type, k.value, k.ctrl, k.idname, getattr(k.properties, "action", None)) for k in km.keymap_items}
    assert ('LEFTMOUSE', 'DOUBLE_CLICK', False, "allset.cut_sew_loop", 'CUT') in got, got
    assert ('LEFTMOUSE', 'DOUBLE_CLICK', True, "allset.cut_sew_loop", 'SEW') in got, got
