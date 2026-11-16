"""Issue #369: Delete History on a mesh with a keyed nonlinear deformer works like Maya: the mesh keeps the shape it has
at the current frame, the deformer goes with its handle, its weights and its animation curves (no keys left on the
mesh for a deformer that is gone, no empty channel group or action); the mesh's own keys stay; a handle still used
by another mesh stays. Delete History with the handle selected changes nothing (the handle has no history). The Time
Slider shows the deformer's keys neither with the mesh nor with the handle selected (Maya shows them while the
deformer node itself is selected)."""

from importlib import import_module

import bpy
import numpy as np

import kit

deformers = import_module(kit.MODULE + ".operators.deformers")
history = import_module(kit.MODULE + ".operators.history")
time_slider = import_module(kit.MODULE + ".ui.time_slider")
compat = import_module(kit.MODULE + ".compat")


def _fresh():
    if bpy.context.object is not None and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for coll in (bpy.data.meshes, bpy.data.actions, bpy.data.lattices):
        for d in list(coll):
            coll.remove(d)
    bpy.context.scene.frame_set(1)


def _select(*obs):
    for o in bpy.context.scene.objects:
        o.select_set(False)
    for o in obs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = obs[-1]


def _cube(name, x=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, 0.0, 0.0))
    ob = bpy.context.active_object
    ob.name, ob.data.name = name, name + "Shape"
    return ob


def _points(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    ev.to_mesh_clear()
    return co.reshape(-1, 3)


def _squash(*meshes, own_key=True):
    """Deform > Nonlinear > Squash on ``meshes``; factor keyed 0 at frame 5 and 1 at frame 20 (channel group
    "squash1"), and with ``own_key`` the first mesh's Translate X keyed at frame 12. Returns the handle."""
    _select(*meshes)
    assert bpy.ops.allset.deformer(kind='SQUASH') == {'FINISHED'}
    handle = bpy.context.view_layer.objects.active
    assert handle.name == "squash1Handle", handle.name
    for ob in meshes:
        md = ob.modifiers["squash1"]
        for frame, value in ((5, 0.0), (20, 1.0)):
            md.factor = value
            md.keyframe_insert("factor", frame=frame, group="squash1")
    if own_key:
        meshes[0].keyframe_insert("location", index=0, frame=12)
    bpy.context.scene.frame_set(1)
    return handle


def _paths(ob):
    return sorted({fc.data_path for fc in compat.id_fcurves(ob)})


def _ticks(*nodes):
    return [f for f, _bd in time_slider.key_frames(list(nodes))]


def test_delete_history_bakes_and_removes_the_deformer_with_its_keys():
    _fresh()
    cube = _cube("pCube1")
    _squash(cube)
    plain = _points(cube)
    bpy.context.scene.frame_set(20)
    bpy.context.view_layer.update()
    squashed = _points(cube)
    assert np.abs(squashed - plain).max() > 0.1, "factor 1 deforms the cube"
    _select(cube)
    assert bpy.ops.allset.delete_history() == {'FINISHED'}
    assert "squash1" not in cube.modifiers
    assert "squash1Handle" not in bpy.data.objects, "the handle goes with the deformer"
    assert _paths(cube) == ["location"], ("only the cube's own keys stay", _paths(cube))
    bag = compat.channelbag(cube.animation_data.action, cube.animation_data.action_slot)
    assert "squash1" not in [g.name for g in bag.groups], "no empty channel group"
    assert "squash1" not in cube.vertex_groups, "the deformer's weights go too"
    # the shape of the current frame is baked into the mesh and no longer changes with time
    for frame in (20, 5, 1):
        bpy.context.scene.frame_set(frame)
        assert np.abs(_points(cube) - squashed).max() < 1e-5, frame


def test_delete_history_leaves_no_empty_action():
    _fresh()
    cube = _cube("pCube1")
    _squash(cube, own_key=False)
    _select(cube)
    bpy.ops.allset.delete_history()
    assert cube.animation_data is None or cube.animation_data.action is None, "the factor curve was all there was"
    assert not compat.id_fcurves(cube)
    assert not [a for a in bpy.data.actions if a.users == 0 and not a.use_fake_user], "no orphan action left"


def test_delete_history_with_the_handle_selected_changes_nothing():
    _fresh()
    cube = _cube("pCube1")
    handle = _squash(cube)
    bpy.context.scene.frame_set(20)
    before = _points(cube)
    _select(handle)
    bpy.ops.allset.delete_history()
    assert "squash1" in cube.modifiers and "squash1Handle" in bpy.data.objects
    assert 'modifiers["squash1"].factor' in _paths(cube)
    bpy.context.scene.frame_set(5)
    assert np.abs(_points(cube) - before).max() > 0.1, "still animated"


def test_handle_used_by_another_mesh_stays():
    _fresh()
    a = _cube("pCube1")
    b = _cube("pCube2", 3.0)
    _squash(a, b, own_key=False)
    _select(a)
    bpy.ops.allset.delete_history()
    assert "squash1" not in a.modifiers and not compat.id_fcurves(a)
    assert "squash1Handle" in bpy.data.objects, "pCube2 still uses the handle"
    assert 'modifiers["squash1"].factor' in _paths(b), "pCube2 keeps its keys"
    _select(b)
    bpy.ops.allset.delete_history()
    assert "squash1Handle" not in bpy.data.objects


def test_non_deformer_history_keeps_the_keyed_deformer():
    _fresh()
    cube = _cube("pCube1")
    _squash(cube)
    _select(cube)
    bpy.ops.allset.delete_history(non_deformer=True)
    assert "squash1" in cube.modifiers and "squash1Handle" in bpy.data.objects
    assert 'modifiers["squash1"].factor' in _paths(cube)


def test_time_slider_does_not_show_the_deformer_keys_with_mesh_or_handle():
    _fresh()
    cube = _cube("pCube1")
    handle = _squash(cube)
    assert _ticks(cube) == [12], ("the cube's own key only", _ticks(cube))
    assert _ticks(handle) == [], _ticks(handle)
    assert _ticks(cube, handle) == [12]
    # the deformer's curves are still there for the Graph Editor / Dope Sheet
    assert 'modifiers["squash1"].factor' in _paths(cube)
