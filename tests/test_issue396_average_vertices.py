"""#396: Edit Mesh > Average Vertices and the vertex marking menu's Average Vertices round the selected vertices at
once, like Maya: no wait for a mouse drag, the mesh changes, and the polyAverageVertex node keeps its Iterations
(10 by default) editable afterwards."""

from importlib import import_module

import bmesh
import bpy
import numpy as np

import kit

ITEM = "Edit Mesh/Average Vertices"


def _mod(name):
    return import_module(kit.MODULE + name)


def _cube(cuts=7):
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    bpy.ops.mesh.primitive_cube_add(size=2.0)
    ob = bpy.context.active_object
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='VERT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.subdivide(number_cuts=cuts)
    bpy.ops.mesh.select_all(action='SELECT')
    return ob


def _co(ob):
    if ob.mode == 'EDIT':
        bm = bmesh.from_edit_mesh(ob.data)
        return np.array([v.co[:] for v in bm.verts])
    co = np.empty(len(ob.data.vertices) * 3)
    ob.data.vertices.foreach_get("co", co)
    return co.reshape(-1, 3)


def _corner(co):
    return int(np.argmax(np.linalg.norm(co, axis=1)))


def test_menu_item_rounds_the_selected_vertices():
    ob = _cube()
    before = _co(ob)
    assert bpy.ops.allset.menu_item(item=ITEM) == {'FINISHED'}
    after = _co(ob)
    assert np.abs(after - before).max() > 0.05, "nothing moved"
    c = _corner(before)
    assert np.linalg.norm(after[c]) < np.linalg.norm(before[c]) - 0.05, "the corners are not rounded"
    assert np.abs(after.mean(axis=0)).max() < 1e-5            # a symmetric shape stays centred
    assert bpy.context.mode == 'EDIT_MESH'


def test_marking_menu_item_is_the_menu_command():
    menus = _mod(".marking.menus")
    label, action = menus.SHIFT_VERTEX.radial["NE"]
    assert label == "Average Vertices" and action == ("item", ITEM), action
    ob = _cube()
    before = _co(ob)
    _mod(".marking.modal").run_action(bpy.context, action)
    assert np.abs(_co(ob) - before).max() > 0.05, "the marking menu item moved nothing"


def test_only_the_selection_moves_and_iterations_count():
    ob = _cube(3)
    bm = bmesh.from_edit_mesh(ob.data)
    for v in bm.verts:
        v.select_set(False)
    bm.select_flush(False)
    corner = max(bm.verts, key=lambda v: v.co.length)
    corner.select_set(True)
    ci = corner.index
    bmesh.update_edit_mesh(ob.data)
    before = _co(ob)
    bpy.ops.allset.average_vertices(iterations=0)
    assert np.abs(_co(ob) - before).max() == 0.0               # 0 iterations: nothing moves
    bpy.ops.allset.average_vertices(iterations=1)
    one = _co(ob)
    moved = np.flatnonzero(np.abs(one - before).max(axis=1) > 0)
    assert moved.tolist() == [ci], moved
    bpy.ops.allset.average_vertices(iterations=10)
    ten = _co(ob)
    assert np.linalg.norm(ten[ci]) < np.linalg.norm(one[ci])   # more iterations: rounder


def test_iterations_stay_editable():
    ob = _cube(3)
    assert bpy.ops.allset.menu_item(item=ITEM) == {'FINISHED'}
    rec = _mod(".operators.extrude").RECORDS.get(ob.name)
    assert rec is not None and rec.name.startswith("polyAverageVertex"), rec and rec.name   # numbered per scene
    assert rec.params["iterations"] == 10
    ten = _co(ob)
    assert bpy.ops.allset.average_vertices_edit(iterations=2) == {'FINISHED'}
    two = _co(ob)
    assert np.abs(two - ten).max() > 1e-4
    ob2 = _cube(3)
    bpy.ops.allset.average_vertices(iterations=2)
    assert np.abs(_co(ob2) - two).max() < 1e-6                 # the edit = a fresh run with that value


def test_option_box_runs_then_shows_iterations():
    # the menu's option box runs the command, then Adjust Last Operation shows its settings: Iterations
    assert _mod(".ui.menu_option_box").option_kind(ITEM) == "redo"
    rna = bpy.ops.allset.average_vertices.get_rna_type()
    shown = [p.identifier for p in rna.properties if p.identifier != "rna_type" and not p.is_hidden]
    assert shown == ["iterations"] and rna.properties["iterations"].default == 10, shown
    assert {'REGISTER', 'UNDO'} <= set(bpy.types.ALLSET_OT_average_vertices.bl_options)


def test_object_mode_averages_the_whole_mesh():
    ob = _cube(3)
    bpy.ops.object.mode_set(mode='OBJECT')
    before = _co(ob)
    assert bpy.ops.allset.menu_item(item=ITEM) == {'FINISHED'}
    assert bpy.context.mode == 'OBJECT'
    assert np.abs(_co(ob) - before).max() > 0.05
