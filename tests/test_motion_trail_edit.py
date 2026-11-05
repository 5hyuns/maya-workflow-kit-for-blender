"""Moving keys on a motion trail (operators/motion_trail_edit.py): world move -> location keys at the key's frame,
parent space, inserted / created keys put back, locked and constrained owners, bones, picked-key modes, keymap."""

import math
from importlib import import_module

import bpy
from mathutils import Euler, Vector

import kit

mte = import_module(kit.MODULE + ".operators.motion_trail_edit")
patches = import_module(kit.MODULE + ".keymap.maya_patches")

TOL = 1e-4


def _clear():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for a in list(bpy.data.actions):
        bpy.data.actions.remove(a)
    for arm in list(bpy.data.armatures):
        bpy.data.armatures.remove(arm)
    mte.clear()


def _keyed(name="Ball", parent=None, keys=((1, (0, 0, 0)), (10, (5, 0, 0)), (20, (10, 5, 0)))):
    scene = bpy.context.scene
    ob = bpy.data.objects.new(name, None)
    scene.collection.objects.link(ob)
    if parent is not None:
        ob.parent = parent
    for f, p in keys:
        ob.location = p
        ob.keyframe_insert("location", frame=f)
    scene.frame_set(1)
    return ob


def _world_at(ob, f, pb=None):
    scene = bpy.context.scene
    cur = scene.frame_current
    scene.frame_set(f)
    if pb is not None:
        w = (ob.matrix_world @ pb.matrix).translation.copy()
    else:
        w = ob.matrix_world.translation.copy()
    scene.frame_set(cur)
    return w


def _loc_keys(ob, path="location"):
    from importlib import import_module as im
    compat = im(kit.MODULE + ".compat")
    out = {}
    for fc in compat.id_fcurves(ob):
        if fc.data_path == path:
            out[fc.array_index] = [(round(k.co.x, 4), round(k.co.y, 4)) for k in fc.keyframe_points]
    return out


def _move(keys, d):
    mv = mte.KeyMove(bpy.context, keys)
    mv.apply(Vector(d))
    return mv


def test_plain_object_moves_the_key_at_its_frame():
    _clear()
    ob = _keyed()
    before = _loc_keys(ob)
    mv = _move([(("Ball", ""), 10)], (0, 0, 3))
    after = _loc_keys(ob)
    assert after[2] == [(1, 0), (10, 3), (20, 0)], after
    assert after[0] == before[0] and after[1] == before[1], after
    assert (_world_at(ob, 10) - Vector((5, 0, 3))).length < TOL
    mv.restore()
    assert _loc_keys(ob) == before


def test_rotated_parent_space():
    _clear()
    scene = bpy.context.scene
    grp = bpy.data.objects.new("Grp", None)
    scene.collection.objects.link(grp)
    grp.location = (0, 0, 3)
    grp.rotation_euler = Euler((0, 0, math.radians(90)))
    grp.scale = (2, 2, 2)
    bpy.context.view_layer.update()
    ob = _keyed(parent=grp)
    ob.matrix_parent_inverse = grp.matrix_world.inverted()       # parent with "keep transform"
    bpy.context.view_layer.update()
    w0 = _world_at(ob, 10)
    _move([(("Ball", ""), 10)], (1, 0, 0))
    assert (_world_at(ob, 10) - (w0 + Vector((1, 0, 0)))).length < TOL
    # keys at the other frames are untouched
    assert (_world_at(ob, 20) - w0).length > 1.0
    ob.matrix_parent_inverse.identity()
    bpy.context.view_layer.update()
    w0 = _world_at(ob, 20)
    before = _loc_keys(ob)
    _move([(("Ball", ""), 20)], (2, 0, 0))
    assert (_world_at(ob, 20) - (w0 + Vector((2, 0, 0)))).length < TOL
    after = _loc_keys(ob)
    # world +X under a parent turned 90 degrees about Z (scale 2) is local -Y / 2
    assert after[1][2] == (20, round(before[1][2][1] - 1.0, 4)), after
    assert after[0] == before[0], after


def test_animated_parent_uses_the_key_frame():
    _clear()
    scene = bpy.context.scene
    grp = bpy.data.objects.new("Grp", None)
    scene.collection.objects.link(grp)
    for f, rz in ((1, 0.0), (20, 90.0)):
        grp.rotation_euler = Euler((0, 0, math.radians(rz)))
        grp.keyframe_insert("rotation_euler", frame=f)
    ob = _keyed(parent=grp)
    scene.frame_set(1)
    w0 = _world_at(ob, 20)
    _move([(("Ball", ""), 20)], (0, 1, 0))
    assert (_world_at(ob, 20) - (w0 + Vector((0, 1, 0)))).length < TOL
    assert scene.frame_current == 1


def test_channel_without_key_gets_one_and_restore_removes_it():
    _clear()
    ob = _keyed(keys=((1, (0, 0, 0)), (20, (10, 0, 0))))
    before = _loc_keys(ob)
    w0 = _world_at(ob, 10)
    mv = _move([(("Ball", ""), 10)], (0, 2, 0))
    after = _loc_keys(ob)
    assert len(after[1]) == 3 and after[1][1] == (10, 2.0), after
    assert len(after[0]) == 2 and len(after[2]) == 2, after     # unchanged channels get no key
    assert (_world_at(ob, 10) - (w0 + Vector((0, 2, 0)))).length < TOL
    mv.restore()
    assert _loc_keys(ob) == before


def test_channel_without_a_curve_stays():
    _clear()
    scene = bpy.context.scene
    ob = bpy.data.objects.new("Ball", None)
    scene.collection.objects.link(ob)
    ob.location = (0, 0, 4)
    for f, x in ((1, 0.0), (20, 10.0)):
        ob.location.x = x
        ob.keyframe_insert("location", index=0, frame=f)
    scene.frame_set(1)
    mv = _move([(("Ball", ""), 20)], (1, 0, 1))
    keys = _loc_keys(ob)
    assert set(keys) == {0} and keys[0][1] == (20, 11.0), keys      # like Maya: no new curve for Z
    mv.restore()
    assert _loc_keys(ob)[0][1] == (20, 10.0)
    assert abs(ob.location.z - 4.0) < TOL


def test_locked_channel_stays():
    _clear()
    ob = _keyed()
    ob.lock_location[2] = True
    before = _loc_keys(ob)
    _move([(("Ball", ""), 10)], (1, 0, 1))
    after = _loc_keys(ob)
    assert after[2] == before[2], after
    assert after[0][1] == (10, 6.0), after


def test_several_keys_take_the_same_world_move():
    _clear()
    ob = _keyed()
    w10, w20 = _world_at(ob, 10), _world_at(ob, 20)
    _move([(("Ball", ""), 10), (("Ball", ""), 20)], (0, -1, 0))
    assert (_world_at(ob, 10) - (w10 + Vector((0, -1, 0)))).length < TOL
    assert (_world_at(ob, 20) - (w20 + Vector((0, -1, 0)))).length < TOL


def test_constrained_and_driven_owners_are_refused():
    _clear()
    ob = _keyed()
    target = bpy.data.objects.new("T", None)
    bpy.context.scene.collection.objects.link(target)
    target.location = (3, 3, 3)
    con = ob.constraints.new('COPY_LOCATION')
    con.target = target
    bpy.context.view_layer.update()
    before = _loc_keys(ob)
    mv = mte.KeyMove(bpy.context, [(("Ball", ""), 10)])
    assert not mv and mv.errors and "constraint" in mv.errors[0], mv.errors
    ob.constraints.remove(con)
    fc = ob.driver_add("location", 1)
    fc.driver.expression = "0"
    mv = mte.KeyMove(bpy.context, [(("Ball", ""), 10)])
    assert not mv and "driver" in mv.errors[0], mv.errors
    assert _loc_keys(ob) == before


def _rig():
    scene = bpy.context.scene
    arm = bpy.data.armatures.new("Rig")
    ob = bpy.data.objects.new("Rig", arm)
    scene.collection.objects.link(ob)
    ob.location = (1, 2, 0)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT')
    root = arm.edit_bones.new("root")
    root.head, root.tail = (0, 0, 0), (0, 0, 1)
    child = arm.edit_bones.new("child")
    child.head, child.tail = (0, 0, 1.5), (0, 1, 2)       # not connected, rolled rest
    child.parent = root
    bpy.ops.object.mode_set(mode='POSE')
    pr = ob.pose.bones["root"]
    for f, rz in ((1, 0.0), (20, 45.0)):
        pr.rotation_mode = 'XYZ'
        pr.rotation_euler = Euler((0, 0, math.radians(rz)))
        pr.keyframe_insert("rotation_euler", frame=f)
    pc = ob.pose.bones["child"]
    for f, p in ((1, (0, 0, 0)), (10, (0.5, 0, 0)), (20, (0, 0, 0))):
        pc.location = p
        pc.keyframe_insert("location", frame=f)
    scene.frame_set(1)
    return ob, pc


def test_pose_bone_head_follows_the_world_move():
    _clear()
    ob, pc = _rig()
    w0 = _world_at(ob, 10, pc)
    mv = _move([(("Rig", "child"), 10)], (0, 0, 0.7))
    assert mv, mv.errors
    assert (_world_at(ob, 10, pc) - (w0 + Vector((0, 0, 0.7)))).length < TOL
    keys = _loc_keys(ob, 'pose.bones["child"].location')
    assert all(len(v) == 3 for v in keys.values()), keys
    mv.restore()
    assert (_world_at(ob, 10, pc) - w0).length < TOL
    bpy.ops.object.mode_set(mode='OBJECT')


def test_connected_bone_is_refused():
    _clear()
    ob, pc = _rig()
    bpy.ops.object.mode_set(mode='EDIT')
    ob.data.edit_bones["child"].head = (0, 0, 1)
    ob.data.edit_bones["child"].use_connect = True
    bpy.ops.object.mode_set(mode='POSE')
    mv = mte.KeyMove(bpy.context, [(("Rig", "child"), 10)])
    assert not mv and "connected" in mv.errors[0], mv.errors
    bpy.ops.object.mode_set(mode='OBJECT')


def test_markers_are_key_frames_on_the_path():
    _clear()
    ob = _keyed()
    ob.rotation_euler.z = 0.3
    ob.keyframe_insert("rotation_euler", index=2, frame=15)
    scene = bpy.context.scene
    viz = ob.animation_visualization.motion_path
    viz.type, viz.range, viz.frame_start, viz.frame_end = 'RANGE', 'MANUAL', 1, 30
    with bpy.context.temp_override(selected_objects=[ob], selected_editable_objects=[ob], active_object=ob,
                                   object=ob):
        bpy.ops.object.paths_calculate(display_type='RANGE', range='MANUAL')
    owner = mte.Owner(ob)
    got = {f: tuple(round(c, 4) for c in co) for f, co in mte.markers(owner, scene)}
    assert sorted(got) == [1, 10, 15, 20], got
    assert got[10] == (5.0, 0.0, 0.0), got
    viz.show_keyframe_highlight = False
    assert mte.markers(owner, scene) == []
    viz.show_keyframe_highlight = True
    viz.type, viz.frame_before, viz.frame_after = 'CURRENT_FRAME', 5, 5
    scene.frame_set(12)
    assert [f for f, _c in mte.markers(owner, scene)] == [10, 15]
    viz.type = 'RANGE'
    scene.frame_set(1)
    # a move then a path update: the marker follows
    mv = _move([(("Ball", ""), 10)], (0, 0, 2))
    mte.update_paths(bpy.context, mv.owners())
    got = {f: tuple(round(c, 4) for c in co) for f, co in mte.markers(owner, scene)}
    assert got[10] == (5.0, 0.0, 2.0), got


def test_pick_modes():
    mte.clear()
    a, b = (("A", ""), 10), (("A", ""), 20)
    mte.select(a, 'SET')
    assert mte.picked() == [("A", "", 10)]
    mte.select(b, 'TOGGLE')
    assert mte.picked() == [("A", "", 10), ("A", "", 20)]
    mte.select(a, 'SET')                        # pressing a picked key keeps the set (it may be dragged)
    assert len(mte.picked()) == 2
    mte.select(a, 'TOGGLE')
    assert mte.picked() == [("A", "", 20)]
    mte.select(a, 'ADD')
    mte.select(a, 'ADD')
    assert mte.picked() == [("A", "", 20), ("A", "", 10)]
    mte.select(b, 'SUB')
    assert mte.picked() == [("A", "", 10)]
    mte.select(None, 'TOGGLE')
    assert mte.picked() == [("A", "", 10)]
    mte.select(None, 'SET')
    assert mte.picked() == []


def test_keymap_items_pass_through_first():
    assert "allset.motion_trail_key" in patches.PASS_THROUGH_FIRST
    rows = [r for r in patches.ADDED if r[1] == "allset.motion_trail_key"]
    assert {r[0] for r in rows} == {"3D View", "3D View Tool: Tweak", "3D View Tool: Move"}, rows
    mmb = [r for r in rows if r[0] == "3D View Tool: Move"]
    assert len(mmb) == 1 and mmb[0][2]["type"] == "MIDDLEMOUSE" and mmb[0][3] == {"button": 'MIDDLE'}, mmb
    assert sorted(r[3]["mode"] for r in rows if r[0] == "3D View") == ['ADD', 'SET', 'SUB', 'TOGGLE'], rows


def test_constrained_delta_axis_and_plane():
    a = Vector((1, 2, 3))
    # two rays looking down -Z, 2 units apart in X and 1 in Y
    r0 = (Vector((1, 2, 10)), Vector((0, 0, -1)))
    r1 = (Vector((3, 3, 10)), Vector((0, 0, -1)))
    view = Vector((2, 1, 0))
    assert (mte.constrained_delta('VIEW', a, r0, r1, view) - view).length < TOL
    assert (mte.constrained_delta(('AXIS', 0), a, r0, r1, view) - Vector((2, 0, 0))).length < TOL
    assert (mte.constrained_delta(('AXIS', 1), a, r0, r1, view) - Vector((0, 1, 0))).length < TOL
    assert (mte.constrained_delta(('PLANE', 2), a, r0, r1, view) - Vector((2, 1, 0))).length < TOL
    # a slanted ray: the X axis takes only the X part of the closest point
    r2 = (Vector((4, 2, 10)), Vector((0, 0.3, -1)).normalized())
    d = mte.constrained_delta(('AXIS', 0), a, r0, r2, view)
    assert abs(d.y) < TOL and abs(d.z) < TOL and abs(d.x - 3.0) < TOL, d
    # the XZ plane (normal Y) seen edge-on gives no move instead of a jump
    assert mte.constrained_delta(('PLANE', 1), a, (Vector((0, 2, 10)), Vector((1, 0, 0))),
                                 (Vector((0, 2, 11)), Vector((1, 0, 0))), view).length < TOL


def test_plain_pick_drops_the_object_selection():
    _clear()
    ob = _keyed()
    other = _keyed("Other")
    for o in (ob, other):
        o.select_set(True)
    assert mte.drop_selection(bpy.context)
    assert not ob.select_get() and not other.select_get()
    assert not mte.drop_selection(bpy.context)      # nothing left to drop
