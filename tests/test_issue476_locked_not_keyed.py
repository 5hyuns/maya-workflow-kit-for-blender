"""#476: a locked channel is never keyed, like Maya: Key Selected, Key All Keyable, Breakdown Selected, S and
setKeyframe skip it and still key the other channels."""

from importlib import import_module

import bpy

import kit

cb = import_module(kit.MODULE + ".ui.channel_box")
cmds = import_module(kit.MODULE + ".command_line.cmds_shim")


def _cube():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for a in list(bpy.data.actions):
        bpy.data.actions.remove(a)
    bpy.ops.mesh.primitive_cube_add()
    ob = bpy.context.active_object
    cb.set_selected_channels([])
    bpy.context.scene.frame_set(1)
    return ob


def _curves(ob):
    return sorted((f.data_path, f.array_index) for f in kit.fcurves(ob))


def test_key_selected_skips_locked():
    ob = _cube()
    ob.lock_location[0] = True
    cb.set_selected_channels(["tx", "ty"])
    assert bpy.ops.allset.cb_key_selected() == {'FINISHED'}
    assert _curves(ob) == [("location", 1)], _curves(ob)


def test_breakdown_selected_skips_locked():
    ob = _cube()
    ob.lock_location[0] = True
    cb.set_selected_channels(["tx", "ty"])
    assert bpy.ops.allset.cb_breakdown_selected() == {'FINISHED'}
    assert _curves(ob) == [("location", 1)], _curves(ob)


def test_key_all_keyable_skips_locked():
    ob = _cube()
    ob.lock_location[1] = True
    assert bpy.ops.allset.cb_key_all() == {'FINISHED'}
    curves = _curves(ob)
    assert ("location", 1) not in curves and ("location", 0) in curves and ("scale", 2) in curves, curves


def test_set_key_skips_locked():
    ob = _cube()
    ob.lock_location[1] = True
    ob.lock_rotation[2] = True
    assert bpy.ops.allset.set_key() == {'FINISHED'}
    curves = _curves(ob)
    assert ("location", 1) not in curves and ("rotation_euler", 2) not in curves, curves
    assert ("location", 0) in curves and ("rotation_euler", 0) in curves and ("scale", 0) in curves, curves


def test_set_key_translate_skips_locked():
    ob = _cube()
    ob.lock_location[2] = True
    assert bpy.ops.allset.set_key(channels="TRANSLATE") == {'FINISHED'}
    assert _curves(ob) == [("location", 0), ("location", 1)], _curves(ob)


def test_set_keyframe_command_skips_locked():
    ob = _cube()
    ob.lock_location[0] = True
    cmds.setKeyframe(ob.name, attribute="translateX")
    cmds.setKeyframe(ob.name, attribute="translateY")
    assert _curves(ob) == [("location", 1)], _curves(ob)


def test_unlocked_again_is_keyed():
    ob = _cube()
    ob.lock_location[0] = True
    ob.lock_location[0] = False
    cb.set_selected_channels(["tx"])
    assert bpy.ops.allset.cb_key_selected() == {'FINISHED'}
    assert _curves(ob) == [("location", 0)], _curves(ob)
