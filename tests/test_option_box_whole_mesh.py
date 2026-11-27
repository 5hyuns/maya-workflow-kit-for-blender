"""The option box (Shift+click / the box) of a component command picked in object mode runs it on the whole mesh,
like a plain click, and Adjust Last Operation holds the command's own settings (Average Vertices: Iterations)."""

from importlib import import_module

import bmesh
import bpy
import numpy as np

import kit


def _mod(name):
    return import_module(kit.MODULE + name)


def _cube(cuts=0, triangulate=False):
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    bpy.ops.mesh.primitive_cube_add(size=2.0)
    ob = bpy.context.active_object
    if cuts or triangulate:
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        if cuts:
            bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=cuts, use_grid_fill=True)
        if triangulate:
            bmesh.ops.triangulate(bm, faces=bm.faces[:])
        bm.to_mesh(ob.data)
        bm.free()
    return ob


def _co(ob):
    co = np.empty(len(ob.data.vertices) * 3)
    ob.data.vertices.foreach_get("co", co)
    return co.reshape(-1, 3)


def _box(item):
    return bpy.ops.allset.menu_option_box(item=item)


def test_every_whole_mesh_command_with_settings_has_an_option_operator():
    menu_map, ops = _mod(".ui.menu_map"), _mod(".ui.menu_item_ops")
    box = _mod(".ui.menu_option_box")
    redo = [p for p, r in menu_map.OBJECT_MODE.items() if isinstance(r, tuple) and box.option_kind(p) == "redo"]
    assert redo and all(p in ops.WHOLE_MESH_OPTIONS for p in redo), (redo, ops.WHOLE_MESH_OPTIONS)


def test_average_vertices_option_box_in_object_mode():
    ob = _cube(cuts=3)
    before = _co(ob)
    assert _box("Edit Mesh/Average Vertices") == {'FINISHED'}
    assert bpy.context.mode == 'OBJECT'
    assert np.abs(_co(ob) - before).max() > 0.05
    # its Adjust Last Operation: the command's name and its Iterations (default 10)
    idname = _mod(".ui.menu_item_ops").WHOLE_MESH_OPTIONS["Edit Mesh/Average Vertices"]
    mod, name = idname.split(".")
    rna = getattr(getattr(bpy.ops, mod), name).get_rna_type()
    assert rna.name == "Average Vertices", rna.name
    shown = [p.identifier for p in rna.properties if p.identifier != "rna_type" and not p.is_hidden]
    assert shown == ["iterations"] and rna.properties["iterations"].default == 10, shown


def test_the_settings_change_the_result():
    # what Adjust Last Operation does: the same operator again with another value
    idname = _mod(".ui.menu_item_ops").WHOLE_MESH_OPTIONS["Edit Mesh/Average Vertices"]
    mod, name = idname.split(".")
    op = getattr(getattr(bpy.ops, mod), name)
    ob = _cube(cuts=3)
    before = _co(ob)
    assert op(iterations=1) == {'FINISHED'}
    one = _co(ob)
    ob = _cube(cuts=3)
    assert op(iterations=10) == {'FINISHED'}
    ten = _co(ob)
    assert bpy.context.mode == 'OBJECT'
    assert np.abs(one - before).max() > 1e-3 and np.abs(ten - one).max() > 1e-3


def test_other_commands_run_on_the_whole_mesh():
    ob = _cube()
    assert _box("Edit Mesh/Add Divisions") == {'FINISHED'}
    assert len(ob.data.polygons) > 6
    ob = _cube()
    assert _box("Edit Mesh/Poke") == {'FINISHED'}
    assert len(ob.data.polygons) == 24
    ob = _cube()
    n0 = np.array([p.normal[:] for p in ob.data.polygons])
    assert _box("Toon/Reverse Surfaces") == {'FINISHED'}
    n1 = np.array([p.normal[:] for p in ob.data.polygons])
    assert np.allclose(n0, -n1)
    ob = _cube(triangulate=True)
    assert _box("Mesh/Quadrangulate") == {'FINISHED'}
    assert len(ob.data.polygons) == 6
    ob = _cube(cuts=2)
    assert _box("Edit Mesh/Edit Edge Flow") == {'FINISHED'}
    assert bpy.context.mode == 'OBJECT'


def test_component_mode_option_box_is_unchanged():
    ob = _cube(cuts=3)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    before = _co(ob)
    bpy.ops.object.mode_set(mode='EDIT')
    assert _box("Edit Mesh/Average Vertices") == {'FINISHED'}
    assert bpy.context.mode == 'EDIT_MESH'
    bpy.ops.object.mode_set(mode='OBJECT')
    assert np.abs(_co(ob) - before).max() > 0.05


def test_nothing_selected_warns():
    ob = _cube(cuts=3)
    before = _co(ob)
    bpy.ops.object.select_all(action='DESELECT')
    _box("Edit Mesh/Average Vertices")
    assert bpy.context.mode == 'OBJECT'
    assert np.abs(_co(ob) - before).max() < 1e-9
