"""Shared attribute editing / modeling history / Bridge (#326): the default state keeps the kit's earlier behaviour.

Persistent Modeling History is a Preferences option, off by default: then a mesh keeps only its newest kit node, for
the session, and nothing extra is written into the mesh or the file. Option Boxes in Floating Windows is off by
default too (the dialog stays; tests/gui/gui_step103_option_windows.py and gui_step162_option_windows.py).
"""
from importlib import import_module

import bmesh
import bpy
import kit

ex = import_module(kit.MODULE + '.operators.extrude')
history = import_module(kit.MODULE + '.operators.model_history')
in_view = import_module(kit.MODULE + '.ui.in_view')
preferences = import_module(kit.MODULE + '.preferences')


def _cube_top_extruded_twice():
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.mesh.primitive_cube_add()
    ob = bpy.context.object
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.scene.tool_settings.mesh_select_mode = (False, False, True)
    bm = bmesh.from_edit_mesh(ob.data)
    ex.deselect_all(bm)
    max(bm.faces, key=lambda face: face.normal.z).select_set(True)
    bm.select_flush_mode()
    bmesh.update_edit_mesh(ob.data)
    assert bpy.ops.allset.extrude('EXEC_DEFAULT', True, thickness=.5) == {'FINISHED'}
    assert bpy.ops.allset.extrude('EXEC_DEFAULT', True, thickness=.25) == {'FINISHED'}
    return ob


def test_new_options_default_to_the_earlier_behaviour():
    prefs = preferences.get()
    assert prefs.model_history_files is False
    assert prefs.option_boxes_floating is False        # option boxes open the kit's dialog
    assert prefs.cb_manipulators == 'STANDARD'
    assert prefs.inview_editors is True


def test_without_persistent_history_only_the_newest_node_is_kept_and_nothing_is_written():
    assert not preferences.get().model_history_files
    meshes = set(bpy.data.meshes)
    ob = _cube_top_extruded_twice()
    rec = ex.current(ob)
    assert rec is not None and rec.history_id is None and rec.input_snapshot is None
    assert history.KEY not in ob.data and history.BASE not in ob.data
    assert not [me for me in set(bpy.data.meshes) - meshes if me is not ob.data], "no hidden input mesh"
    assert history.read(ob) is None and history.records(ob) == []
    assert in_view.cb_record(bpy.context, ob) is rec          # Channel Box INPUTS: the newest node only
    assert in_view.HISTORY_TIP.startswith("Blender keeps no edit-mode history")
    assert ex.set_params(bpy.context, thickness=.75) == {'FINISHED'} and rec.params['thickness'] == .75
    bpy.ops.object.mode_set(mode='OBJECT')


def test_persistent_history_option_keeps_the_chain():
    prefs = preferences.get()
    prefs.model_history_files = True
    try:
        ob = _cube_top_extruded_twice()
        data = history.read(ob)
        assert data is not None and len(data['nodes']) == 2
        assert isinstance(ob.data.get(history.BASE), bpy.types.Mesh)
        assert [r.name for r in history.records(ob)] == [n['name'] for n in data['nodes']]
        bpy.ops.object.mode_set(mode='OBJECT')
    finally:
        prefs.model_history_files = False
    assert history.read(ob) is None          # off again: a recipe in the mesh is left unused


def test_the_field_gesture_watch_does_not_hold_back_autosave():
    # it stays modal while the pointer rests on a kit number field: the timers that wait for no running tool skip it
    listeners = import_module(kit.MODULE + '.modal_listeners')
    assert 'ALLSET_OT_attribute_field_watch' in listeners.NAMES
    assert 'ALLSET_OT_attribute_field_drag' not in listeners.NAMES


def test_without_persistent_history_a_bridge_follows_its_path_curve():
    from test_bridge_paths import bridge_object
    curve = import_module(kit.MODULE + '.operators.bridge_curve')
    nodes = import_module(kit.MODULE + '.ui.node_attributes')
    assert not preferences.get().model_history_files
    ob, record = bridge_object()
    node = nodes.target(bpy.context)
    assert nodes.apply(bpy.context, node, dict(node.params, curve_type=2)) == {'FINISHED'}
    path = curve.curve_object(ob, record.params)
    bpy.ops.object.mode_set(mode='OBJECT')
    before = ex.mesh_coords_hash(ob.data)
    path.data.splines[0].points[2].co.x += 1
    curve._dirty.add(path.data.session_uid)
    curve.refresh()
    assert ex.mesh_coords_hash(ob.data) != before
    assert ex.object_record(ob) is record and not record.live
