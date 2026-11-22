"""Issue #369 with the reporter's steps: a cube, Deform > Nonlinear > Squash, the Factor keyed in the Channel Box
(the squash1 node open in the handle's INPUTS, Key Selected at two frames), then Delete History on the cube: the
squash node goes with its handle and its keys (none left on the cube), the cube keeps the shape it has at the current
frame and no longer changes with time (Maya bakes the deformation into the mesh), and the Time Slider shows no
deformer key on the cube or the handle."""

from importlib import import_module

import bpy
import numpy as np

import kit

cb = import_module(kit.MODULE + ".ui.channel_box")
deformers = import_module(kit.MODULE + ".operators.deformers")
time_slider = import_module(kit.MODULE + ".ui.time_slider")
compat = import_module(kit.MODULE + ".compat")


def _select(*obs):
    for o in bpy.context.scene.objects:
        o.select_set(False)
    for o in obs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = obs[-1]


def _points(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    ev.to_mesh_clear()
    return co.reshape(-1, 3)


def _row(attr):
    rows = [r for r in bpy.context.scene.allset_cb.rows if r.kind == "INPUT" and r.name == deformers.PREFIX + attr]
    assert rows, [(r.kind, r.name) for r in bpy.context.scene.allset_cb.rows]
    return rows[0]


def test_squash_keyed_in_the_channel_box_then_delete_history():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    cube = bpy.context.active_object
    cube.name = "pCube1"
    plain = _points(cube)
    assert bpy.ops.allset.deformer(kind='SQUASH') == {'FINISHED'}
    handle = bpy.context.view_layer.objects.active
    assert handle.name == "squash1Handle"
    md = cube.modifiers["squash1"]
    _select(handle)
    cb.set_open(handle, cb.mod_node(md))
    cb.rebuild_rows()
    for frame, text in ((1, "0"), (10, "1")):
        bpy.context.scene.frame_set(frame)
        _row("factor").text = text
        cb.set_selected_channels([cb.row_key(_row("factor"))])
        assert bpy.ops.allset.cb_key_selected() == {'FINISHED'}
    cb.set_selected_channels([])
    assert any(f.data_path.startswith('modifiers["squash1"]') for f in compat.id_fcurves(cube)), "keyed on the cube"
    assert [f for f, _b in time_slider.key_frames([handle])] == [], "Time Slider: no key with the handle selected"
    assert [f for f, _b in time_slider.key_frames([cube])] == [], "nor with the cube (Maya: with the node selected)"
    bpy.context.scene.frame_set(10)
    squashed = _points(cube)
    assert np.abs(squashed - plain).max() > 0.1
    _select(cube)
    assert bpy.ops.allset.delete_history() == {'FINISHED'}
    assert "squash1" not in cube.modifiers and "squash1Handle" not in bpy.data.objects
    assert not compat.id_fcurves(cube), "no keys of the gone squash left on the cube"
    for frame in (10, 1, 5):
        bpy.context.scene.frame_set(frame)
        assert np.abs(_points(cube) - squashed).max() < 1e-5, ("the shape of frame 10 stays", frame)
