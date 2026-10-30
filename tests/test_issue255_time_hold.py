"""Issue #255: Time Slider middle mouse moves the time without updating the scene (Maya), so the pose can be
keyed at another frame with S. GUI: tests/gui/gui_step56_time_slider.py (MMB steps)."""

from importlib import import_module

import bpy

import kit

th = import_module(kit.MODULE + ".operators.time_hold")
tk = import_module(kit.MODULE + ".operators.time_keys")
cb = import_module(kit.MODULE + ".ui.channel_box")


def _key(owner, path, values, index=-1):
    for frame, value in values:
        if index >= 0:
            getattr(owner, path)[index] = value
        else:
            setattr(owner, path, value)
        owner.keyframe_insert(path, index=index, frame=frame)


def test_split_path():
    assert th.split_path("location") == ("", "attr", "location")
    assert th.split_path('pose.bones["a.b"].location') == ('pose.bones["a.b"]', "attr", "location")
    assert th.split_path('["my.prop"]') == ("", "key", "my.prop")
    assert th.split_path('pose.bones["x"]["c"]') == ('pose.bones["x"]', "key", "c")
    assert th.split_path('key_blocks["Key 1"].value') == ('key_blocks["Key 1"]', "attr", "value")
    assert th.split_path('nodes["Mix"].inputs[0].default_value') == ('nodes["Mix"].inputs[0]', "attr",
                                                                     "default_value")
    assert th.split_path("data.vertices[3]") == ("data.vertices", "index", 3)
    assert th.split_path('["q\\"uote"]') == ("", "key", 'q"uote')


def _scene():
    scene = bpy.context.scene
    ob = bpy.data.objects["Cube"]
    _key(ob, "location", [(1, (0, 0, 0)), (11, (10, 0, 0))])
    ob["c"] = 0.0
    ob.keyframe_insert('["c"]', frame=1)
    ob["c"] = 10.0
    ob.keyframe_insert('["c"]', frame=11)
    ob.shape_key_add(name="Basis")
    sk = ob.shape_key_add(name="Wide")
    sk.value = 0.0
    sk.keyframe_insert("value", frame=1)
    sk.value = 1.0
    sk.keyframe_insert("value", frame=11)
    bpy.ops.object.armature_add()
    arm = bpy.context.object
    pb = arm.pose.bones[0]
    pb.rotation_mode = 'XYZ'
    _key(pb, "rotation_euler", [(1, (0, 0, 0)), (11, (1.0, 0, 0))])
    scene.frame_set(1)
    return scene, ob, sk, pb


def test_move_time_keeps_every_channel():
    scene, ob, sk, pb = _scene()
    snap = th.snapshot()
    paths = {(i.name, p, n) for i, p, n, _v in snap}
    assert ("Cube", "location", 0) in paths and ("Cube", '["c"]', 0) in paths, paths
    th.move_time(scene, 6, snap)
    assert scene.frame_current == 6
    assert tuple(ob.location) == (0, 0, 0), tuple(ob.location)
    assert ob["c"] == 0.0 and sk.value == 0.0 and pb.rotation_euler.x == 0.0
    # nothing re-evaluates the animation until the time changes the ordinary way
    bpy.context.view_layer.update()
    ob.update_tag()
    bpy.context.view_layer.update()
    assert tuple(ob.location) == (0, 0, 0) and pb.rotation_euler.x == 0.0
    scene.frame_set(6)
    assert abs(ob.location.x - 5.0) < 1e-4 and abs(sk.value - 0.5) < 1e-4, (ob.location.x, sk.value)


def test_s_keys_the_held_pose():
    scene, ob, _sk, _pb = _scene()
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    th.move_time(scene, 6, th.snapshot())
    assert tk.set_key(bpy.context) > 0
    fc = cb._fcurves(ob).find("location", index=0)
    assert [round(k.co.x) for k in fc.keyframe_points] == [1, 6, 11]
    assert abs(fc.evaluate(6)) < 1e-6, fc.evaluate(6)


def test_restore_writes_only_changed_values():
    scene, _ob, _sk, _pb = _scene()
    snap = th.snapshot()
    assert th.restore(snap) == 0
    scene.frame_set(6)
    assert th.restore(snap) > 0


def test_mmb_keymap_item_holds():
    maya_patches = import_module(kit.MODULE + ".keymap.maya_patches")
    ic_data = import_module(kit.MODULE + ".keymap.ic_data")
    patch = import_module(kit.MODULE + ".keymap.patch")
    kd = patch.KeyconfigData(maya_patches.apply(ic_data.generate()))
    items = kd.find("Dopesheet", "allset.time_scrub", type="MIDDLEMOUSE")
    assert items and ('hold', True) in items[0][2]["properties"], items
