"""Issue #329 (follow-up): a keyed constraint target weight drives the constraint on every frame, like Maya. Type a
weight in the Channel Box and key it at one frame, type another at a later frame and key it, then scrub: the weight
follows its keys, and the constrained object's or joint's evaluated position follows Maya's rule. One target: any
weight above 0 keeps the node fully on its target, 0 leaves it on its own channels (a weight keyed 0 -> 1 jumps onto
the target on the frame after the 0 key). Several targets: the weighted average of the targets. Covers a one-target
constraint on an object, a two-target node on an object, a joint following a locator (one target) and a joint
following two locators, keyed with S (the constraint node open in the Channel Box) and with Channels > Key
Selected; older scenes; deleted and renamed constraints."""

import math
import os
from importlib import import_module

import bpy
from mathutils import Vector

import kit

cb = import_module(kit.MODULE + ".ui.channel_box")
compat = import_module(kit.MODULE + ".compat")
multi = import_module(kit.MODULE + ".operators.constrain_multi")
interp = import_module(kit.MODULE + ".operators.constrain_interp")

OUT = os.path.join(os.environ.get("ALLSET_TEST_OUT", bpy.app.tempdir), "issue329_weight_scrub")
FOLLOW = 5.0        # the (first) target moves 5 along Y after the constraint is made: on the target = 5, off = 0


def _fresh():
    if bpy.context.object is not None and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for arm in list(bpy.data.armatures):
        bpy.data.armatures.remove(arm)
    for act in list(bpy.data.actions):
        bpy.data.actions.remove(act)
    cb.reset_open()
    cb.set_selected_channels([])
    bpy.context.scene.frame_set(1)


def _cube(name, x=0.0):
    bpy.ops.mesh.primitive_cube_add(location=(x, 0.0, 0.0))
    ob = bpy.context.active_object
    ob.name = name
    return ob


def _locator(name):
    e = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(e)
    return e


def _move_targets(targets):
    for i, t in enumerate(targets):
        t.select_set(False)
        t.location = (0.0, FOLLOW * (i + 1), 0.0)
    bpy.context.view_layer.update()


def _object_pos(name):
    dg = bpy.context.evaluated_depsgraph_get()
    return bpy.data.objects[name].evaluated_get(dg).matrix_world.translation.copy()


def _object_scene(n_targets):
    """pCube1 (.. pCubeN) parent-constrain the last cube (3 along X), made with Constrain > Parent."""
    _fresh()
    targets = [_cube(f"pCube{i + 1}") for i in range(n_targets)]
    child = _cube(f"pCube{n_targets + 1}", 3.0)
    for ob in bpy.context.scene.objects:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = child
    assert bpy.ops.allset.constrain(type='CHILD_OF') == {'FINISHED'}
    _move_targets(targets)
    cb.set_open(child, cb.con_node(child, child.constraints[0]))      # the user opened the node to type in it
    cb.rebuild_rows()
    name = child.name
    return child, targets, lambda: _object_pos(name)


def _joint_scene(n_targets):
    """locator1 (.. locatorN) parent-constrain a joint (pose bone at 3 along X), made with Constrain > Parent."""
    _fresh()
    targets = [_locator(f"locator{i + 1}") for i in range(n_targets)]
    bpy.ops.object.armature_add(location=(3.0, 0.0, 0.0))
    arm = bpy.context.active_object
    arm.name = "skeleton"
    for ob in bpy.context.scene.objects:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='POSE')
    cb.set_bone_selected(arm.pose.bones[0], True)
    arm.data.bones.active = arm.data.bones[0]
    assert bpy.ops.allset.constrain(type='CHILD_OF') == {'FINISHED'}
    _move_targets(targets)
    pb = arm.pose.bones[0]
    cb.set_open(pb, cb.con_node(pb, pb.constraints[0]))
    cb.rebuild_rows()

    def pos():
        dg = bpy.context.evaluated_depsgraph_get()
        ae = arm.evaluated_get(dg)
        return (ae.matrix_world @ ae.pose.bones[0].matrix).translation.copy()

    return pb, targets, pos


def _bone_scene(_n_targets=1):
    """A joint with a one-target point constraint on locator1 made outside the kit's node builder (a Blender Copy
    Location on the pose bone)."""
    _fresh()
    loc = _locator("locator1")
    bpy.ops.object.armature_add(location=(3.0, 0.0, 0.0))
    arm = bpy.context.active_object
    arm.name = "skeleton"
    pb = arm.pose.bones[0]
    con = pb.constraints.new('COPY_LOCATION')
    con.target = loc
    con.use_offset = True
    loc.select_set(False)
    bpy.ops.object.mode_set(mode='POSE')
    cb.set_bone_selected(pb, True)
    arm.data.bones.active = arm.data.bones[0]
    _move_targets([loc])
    cb.set_open(pb, cb.con_node(pb, con))
    cb.rebuild_rows()

    def pos():
        dg = bpy.context.evaluated_depsgraph_get()
        ae = arm.evaluated_get(dg)
        return (ae.matrix_world @ ae.pose.bones[0].matrix).translation.copy()

    return pb, [loc], pos


ONE_TARGET = (("object", _object_scene), ("joint", _joint_scene), ("joint (plain constraint)", _bone_scene))


def _rows():
    """The Channel Box weight rows: a one-target constraint's (CONSTRAINT) or a node's W0, W1 ... (CUSTOM)."""
    return [r for r in bpy.context.scene.allset_cb.rows
            if r.kind == "CONSTRAINT" or (r.kind == "CUSTOM" and r.name.startswith(multi.WEIGHT))]


def _expected_y(w0, n_targets):
    """Y of the constrained node for first weight w0 (the others 1): one target = on the target for any weight above
    0, its own place at 0 (Maya); several = the weighted average of the targets (target i follows to FOLLOW * (i + 1))."""
    if n_targets == 1:
        return FOLLOW if w0 > 1e-9 else 0.0
    ws = [w0] + [1.0] * (n_targets - 1)
    return sum(w * FOLLOW * (i + 1) for i, w in enumerate(ws)) / sum(ws)


def _key_weight(how, frame, text):
    bpy.context.scene.frame_set(frame)
    row = _rows()[0]
    row.text = text
    if how == "S":
        cb.set_selected_channels([])       # nothing picked in the Channel Box: S keys every keyable channel
        assert bpy.ops.allset.set_key() == {'FINISHED'}
    else:
        cb.set_selected_channels([cb.row_key(row)])
        assert bpy.ops.allset.cb_key_selected() == {'FINISHED'}
        cb.set_selected_channels([])


def _keys(fc):
    return [(round(k.co.x), round(k.co.y, 6)) for k in fc.keyframe_points]


def _check_scrub(tag, node, key, pos, n_targets):
    fc = cb.fcurve(node, key)
    assert fc is not None, (tag, "the weight has no curve", [f.data_path for f in compat.id_fcurves(node.id_data)])
    assert _keys(fc) == [(1, 1.0), (10, 0.0)], (tag, _keys(fc))
    for frame in (10, 5, 1, 7, 10, 9):       # back and forth like a scrub
        bpy.context.scene.frame_set(frame)
        want = fc.evaluate(frame)
        got = cb.get_value(node, key)
        assert abs(got - want) < 1e-5, (tag, frame, "Channel Box value", got, want)
        assert abs(float(_rows()[0].text) - want) < 1e-3, (tag, frame, "row text", _rows()[0].text, want)
        y = pos().y
        assert abs(y - _expected_y(want, n_targets)) < 1e-4, (tag, frame, "position", y, _expected_y(want, n_targets))
    bpy.context.scene.frame_set(5)
    assert 0.05 < cb.get_value(node, key) < 0.95, (tag, "the weight itself is between the keys")


def _leave_pose():
    if bpy.context.object is not None and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')


def _case(tag, make, n_targets, how):
    node, _targets, pos = make(n_targets)
    rows = _rows()
    assert rows, (tag, "weight rows", [(r.kind, r.name) for r in bpy.context.scene.allset_cb.rows])
    key = cb.row_key(rows[0])
    _key_weight(how, 1, "1")
    _key_weight(how, 10, "0")
    _check_scrub(f"{tag}-{how}", node, key, pos, n_targets)
    _leave_pose()


def test_one_target_constraint_on_an_object_follows_its_keys():
    for how in ("S", "K"):
        _case("object 1 target", _object_scene, 1, how)


def test_two_target_node_on_an_object_follows_its_keys():
    for how in ("S", "K"):
        _case("object 2 targets", _object_scene, 2, how)


def test_joint_following_one_locator_follows_its_keys():
    for how in ("S", "K"):
        _case("joint 1 target", _joint_scene, 1, how)


def test_joint_following_two_locators_follows_its_keys():
    for how in ("S", "K"):
        _case("joint 2 targets", _joint_scene, 2, how)


def test_one_target_weight_above_zero_follows_fully():
    """Like Maya: with one target any weight above 0 (0.01, 0.5, 1, 2) puts the node fully on its target and 0 on its
    own channels; the Channel Box shows the typed weight. Objects, joints, and a joint's plain Blender constraint."""
    for tag, make in ONE_TARGET:
        node, _targets, pos = make(1)
        row = _rows()[0]
        key = cb.row_key(row)
        for text, y in (("1", FOLLOW), ("0.5", FOLLOW), ("0", 0.0), ("0.01", FOLLOW), ("2", FOLLOW), ("0", 0.0),
                        ("0.25", FOLLOW)):
            _rows()[0].text = text
            bpy.context.view_layer.update()
            got = cb.get_value(node, key)
            assert abs(got - float(text)) < 1e-6, (tag, text, "the Channel Box keeps the typed weight", got)
            assert abs(float(_rows()[0].text) - float(text)) < 1e-3, (tag, text, _rows()[0].text)
            assert abs(pos().y - y) < 1e-4, (tag, text, pos().y, y)
        if row.kind == "CONSTRAINT":
            # the constraint's own weight: an ID property of the node (min 0, like Maya); the influence follows it
            con = cb.input_owner(node, key)
            prop = cb.constraint_weight(node, key)
            assert prop is not None and prop in node.keys(), (tag, list(node.keys()))
            fc = node.id_data.animation_data.drivers.find(con.path_from_id("influence"))
            assert fc is not None and fc.driver.expression == multi.SINGLE and fc.driver.is_simple_expression
            assert abs(con.influence - 1.0) < 1e-6, (tag, "on the target", con.influence)
            _rows()[0].text = "-1"
            bpy.context.view_layer.update()
            assert cb.get_value(node, key) == 0.0 and abs(pos().y) < 1e-4, (tag, "no weight below 0")
            assert abs(cb.drag_limit(node, key, 2.5) - 2.5) < 1e-9 and cb.drag_limit(node, key, -0.3) == 0.0
        _leave_pose()


def test_weight_keyed_from_zero_to_one_jumps_onto_the_target():
    """Like Maya: W0 keyed 0 at frame 1 and 1 at frame 10 -> frame 1 = the node's own place, from frame 2 (a weight
    of about 0.03) on fully on the target, no blend; the weight itself follows its curve."""
    for tag, make in ONE_TARGET:
        for how in ("S", "K"):
            node, _targets, pos = make(1)
            key = cb.row_key(_rows()[0])
            _key_weight(how, 1, "0")
            _key_weight(how, 10, "1")
            fc = cb.fcurve(node, key)
            assert fc is not None and _keys(fc) == [(1, 0.0), (10, 1.0)], (tag, how, fc and _keys(fc))
            for frame, y in ((1, 0.0), (2, FOLLOW), (5, FOLLOW), (10, FOLLOW), (1, 0.0), (3, FOLLOW), (1, 0.0)):
                bpy.context.scene.frame_set(frame)
                want = fc.evaluate(frame)
                assert abs(cb.get_value(node, key) - want) < 1e-5, (tag, how, frame, cb.get_value(node, key), want)
                assert abs(float(_rows()[0].text) - want) < 1e-3, (tag, how, frame, _rows()[0].text, want)
                assert abs(pos().y - y) < 1e-4, (tag, how, frame, "position", pos().y, y)
            bpy.context.scene.frame_set(2)
            assert 0.0 < cb.get_value(node, key) < 0.2, (tag, how, "a small weight", cb.get_value(node, key))
            _leave_pose()


def test_s_leaves_closed_constraint_nodes_unkeyed():
    """Like Maya, S keys the node's own channels; a constraint's weights only while its node is open in the Channel
    Box (where the weights show) — and on every selected object with the same constraint."""
    _fresh()
    parent = _cube("pCube1")
    a, b = _cube("pCube2", 3.0), _cube("pCube3", 6.0)
    for ob in (a, b):
        ob.constraints.new('CHILD_OF').target = parent
    parent.select_set(False)
    for ob in (a, b):
        ob.select_set(True)
    bpy.context.view_layer.objects.active = a
    cb.rebuild_rows()
    assert bpy.ops.allset.set_key() == {'FINISHED'}
    key = cb.constraint_key('CHILD_OF', 0, "influence")
    for ob in (a, b):
        assert cb.fcurve(ob, "tx") is not None
        assert cb.fcurve(ob, key) is None, "a closed node's weight stays unkeyed"
        assert cb.constraint_weight(ob, key) is None, "and keeps its influence as the weight"
    cb.set_open(a, cb.con_node(a, a.constraints[0]))
    cb.rebuild_rows()
    bpy.context.scene.frame_set(4)
    b.constraints[0].influence = 0.25
    assert bpy.ops.allset.set_key() == {'FINISHED'}
    for ob, v in ((a, 1.0), (b, 0.25)):
        fc = cb.fcurve(ob, key)
        assert fc is not None and _keys(fc) == [(4, v)], ob.name
        prop = cb.constraint_weight(ob, key)
        assert prop is not None and fc.data_path == multi.weight_path(ob, prop), (ob.name, fc.data_path)
    # a weight a driver feeds (a user's driver on the influence) is the driver's: S leaves it alone
    c = _cube("pCube4", 9.0)
    con = c.constraints.new('CHILD_OF')
    con.target = parent
    d = con.driver_add("influence")
    d.driver.expression = "0.5"
    parent.select_set(False)
    for ob in (a, b, c):
        ob.select_set(True)
    bpy.context.view_layer.objects.active = a
    cb.set_open(a, cb.con_node(a, a.constraints[0]))      # the lead came back: its nodes start collapsed again
    cb.rebuild_rows()
    bpy.context.scene.frame_set(8)
    assert bpy.ops.allset.set_key() == {'FINISHED'}
    assert cb.fcurve(c, key) is None and cb.constraint_weight(c, key) is None, "no key on a driven weight"
    assert cb.driver(c, key) is not None and c.animation_data.drivers.find(con.path_from_id("influence")) == d
    assert len(cb.fcurve(a, key).keyframe_points) == 2


def test_other_constraints_keep_their_influence_as_the_weight():
    """A constraint the Channel Box does not show as a Maya constraint node with target weights (a Shrinkwrap)
    keeps Blender's influence as its weight."""
    _fresh()
    parent = _cube("pCube1")
    a = _cube("pCube2", 3.0)
    con = a.constraints.new('SHRINKWRAP')
    con.target = parent
    parent.select_set(False)
    bpy.context.view_layer.objects.active = a
    cb.set_open(a, cb.con_node(a, con))
    cb.rebuild_rows()
    row = _rows()[0]
    key = cb.row_key(row)
    row.text = "0.3"
    assert abs(con.influence - 0.3) < 1e-6 and cb.constraint_weight(a, key) is None
    assert not [k for k in a.keys() if k.startswith(multi.WEIGHT)]
    assert abs(cb.drag_limit(a, key, 1.7) - 1.0) < 1e-9


def test_deleted_and_renamed_constraints():
    """A renamed constraint keeps its weight and keys; a deleted one takes its weight and the weight's curve with it."""
    child, targets, pos = _object_scene(1)
    key = cb.row_key(_rows()[0])
    _key_weight("S", 1, "0.5")
    _key_weight("S", 10, "0")
    prop = cb.constraint_weight(child, key)
    assert prop in child.keys()
    con = child.constraints[0]
    con.name = "followParent"
    assert cb.constraint_weight(child, key) == prop and cb.fcurve(child, key) is not None
    bpy.context.scene.frame_set(1)
    assert abs(cb.get_value(child, key) - 0.5) < 1e-6 and abs(pos().y - FOLLOW) < 1e-4
    bpy.context.scene.frame_set(10)
    assert abs(pos().y) < 1e-4
    assert multi.cleanup() == 0, "a live weight stays"
    # a new constraint under the old name gets a weight of its own
    second = child.constraints.new('CHILD_OF')
    second.target = targets[0]
    key1 = cb.constraint_key('CHILD_OF', 1, "influence")
    cb.set_value(child, key1, 0.0)
    prop1 = cb.constraint_weight(child, key1)
    assert prop1 is not None and prop1 != prop, (prop, prop1)
    assert cb.constraint_weight(child, key) == prop and len(cb.fcurve(child, key).keyframe_points) == 2
    child.constraints.remove(second)
    assert multi.cleanup() == 1 and prop1 not in child.keys() and prop in child.keys()
    child.constraints.remove(con)
    assert multi.cleanup() == 1
    assert prop not in child.keys()
    assert not [f.data_path for f in compat.id_fcurves(child) if f.data_path == multi.weight_path(child, prop)]
    assert multi.cleanup() == 0


def _single_joint():
    pb, targets, pos = _joint_scene(1)
    mb = multi.member(pb.constraints[0], pb)
    return pb, targets[0], pos, mb.group


def _weight_prop(pb, group):
    return multi.weights(pb, group)[0][0]


def _set_weight(pb, prop, value):
    pb[prop] = value
    pb.id_data.update_tag()
    bpy.context.view_layer.update()


def test_one_target_weight_is_a_simple_driver_on_every_member():
    pb, _loc, pos, group = _single_joint()
    arm = pb.id_data
    prop = _weight_prop(pb, group)
    for c in multi.members(pb, group):
        fc = arm.animation_data.drivers.find(c.path_from_id("influence"))
        assert fc is not None and fc.driver.is_simple_expression, (c.name, fc and fc.driver.expression)
        assert fc.driver.expression == multi.SINGLE
    for w, y in ((1.0, FOLLOW), (0.0, 0.0), (0.4, FOLLOW), (3.0, FOLLOW), (-1.0, 0.0), (0.01, FOLLOW)):
        _set_weight(pb, prop, w)
        assert abs(pos().y - y) < 1e-4, (w, pos().y, y)
    bpy.ops.object.mode_set(mode='OBJECT')


def test_one_target_weight_turns_rotation_on_and_off_with_every_interp_type():
    pb, loc, pos, group = _single_joint()
    prop = _weight_prop(pb, group)
    loc.rotation_euler = (0.0, 0.0, math.radians(90.0))
    bpy.context.view_layer.update()
    arm = pb.id_data

    def angle():
        dg = bpy.context.evaluated_depsgraph_get()
        ae = arm.evaluated_get(dg)
        return math.degrees((ae.matrix_world @ ae.pose.bones[0].matrix).to_quaternion().rotation_difference(
            (arm.matrix_world @ arm.data.bones[0].matrix_local).to_quaternion()).angle)

    for mode in (None, interp.SHORTEST, interp.AVERAGE, interp.NO_FLIP):
        if mode is not None:
            interp.set_mode(bpy.context, pb, group, mode)
        _set_weight(pb, prop, 1.0)
        on, p_on = angle(), pos()
        _set_weight(pb, prop, 0.0)
        off, p_off = angle(), pos()
        _set_weight(pb, prop, 0.5)
        half, p_half = angle(), pos()
        assert abs(on - 90.0) < 0.01 and off < 0.01 and abs(half - on) < 0.01, (mode, on, off, half)
        assert (p_off - Vector((3.0, 0.0, 0.0))).length < 1e-4, (mode, "weight 0: the joint's own place", p_off)
        assert (p_half - p_on).length < 1e-4, (mode, "weight 0.5: fully on the target", p_on, p_half)
    bpy.ops.object.mode_set(mode='OBJECT')


def _save_and_open(name):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    bpy.ops.wm.save_as_mainfile(filepath=path, copy=True)
    bpy.ops.wm.open_mainfile(filepath=path)
    cb.reset_open()
    cb.set_selected_channels([])


def test_older_one_target_groups_get_the_driver_on_load():
    for old in (None, "min(max(w0, 0.0), 1.0)"):      # no driver at all / the earlier linear one
        pb, _loc, pos, group = _single_joint()
        arm = pb.id_data
        prop = _weight_prop(pb, group)
        for c in multi.members(pb, group):
            if old is None:
                c.driver_remove("influence")
                c.influence = 1.0
            else:
                arm.animation_data.drivers.find(c.path_from_id("influence")).driver.expression = old
        _set_weight(pb, prop, 0.0 if old is None else 0.5)
        y = pos().y
        assert abs(y - (FOLLOW if old is None else 0.5 * FOLLOW)) < 1e-4, (old, "the old group", y)
        bpy.ops.object.mode_set(mode='OBJECT')
        _save_and_open("old_single_target.blend")
        arm = bpy.data.objects["skeleton"]
        pb = arm.pose.bones[0]
        bpy.context.view_layer.update()
        for c in multi.members(pb, group):
            fc = arm.animation_data.drivers.find(c.path_from_id("influence"))
            assert fc is not None and fc.driver.expression == multi.SINGLE, (old, fc and fc.driver.expression)
        y = (arm.matrix_world @ pb.matrix).translation.y
        want = 0.0 if old is None else FOLLOW
        assert abs(y - want) < 1e-4, (old, "after the load", y, want)
        _set_weight(pb, prop, 0.0 if old else 1.0)
        assert abs((arm.matrix_world @ pb.matrix).translation.y - (0.0 if old else FOLLOW)) < 1e-4
        assert multi.upgrade() == 0, "a second pass writes nothing"


def test_older_scenes_keep_a_keyed_influence_until_the_weight_is_keyed_again():
    """An earlier version keyed a one-target constraint's weight as its influence (1 at frame 1, 0 at frame 10, a
    blend between). The scene opens unchanged; keying the weight in the Channel Box moves those keys onto the weight
    and the Maya rule applies from then on."""
    child, _targets, _pos = _object_scene(1)
    con = child.constraints[0]
    sc = bpy.context.scene
    for frame, v in ((1, 1.0), (10, 0.0)):
        sc.frame_set(frame)
        con.influence = v
        con.keyframe_insert("influence")
    _save_and_open("old_keyed_influence.blend")
    child = bpy.data.objects["pCube2"]
    con = child.constraints[0]
    path = con.path_from_id("influence")
    key = cb.constraint_key('CHILD_OF', 0, "influence")
    fcs = compat.id_fcurve_collection(child)
    assert fcs.find(path) is not None and cb.constraint_weight(child, key) is None
    sc = bpy.context.scene
    sc.frame_set(5)
    y = _object_pos("pCube2").y
    assert 0.05 * FOLLOW < y < 0.95 * FOLLOW, ("the scene opens as it was saved (a blend)", y)
    assert multi.upgrade() == 0 and multi.cleanup() == 0, "nothing rewritten on load"
    for ob in bpy.data.objects:
        ob.select_set(ob is child)
    bpy.context.view_layer.objects.active = child
    cb.set_open(child, cb.con_node(child, con))
    cb.rebuild_rows()
    _key_weight("S", 20, "1")
    fcs = compat.id_fcurve_collection(child)
    prop = cb.constraint_weight(child, key)
    assert prop is not None and fcs.find(path) is None, "the keys moved off the influence"
    fc = fcs.find(multi.weight_path(child, prop))
    assert fc is not None and _keys(fc) == [(1, 1.0), (10, 0.0), (20, 1.0)], fc and _keys(fc)
    for frame, y in ((1, FOLLOW), (5, FOLLOW), (10, 0.0), (15, FOLLOW), (20, FOLLOW)):
        sc.frame_set(frame)
        assert abs(cb.get_value(child, key) - fc.evaluate(frame)) < 1e-5
        assert abs(_object_pos("pCube2").y - y) < 1e-4, (frame, _object_pos("pCube2").y, y)


def test_two_target_nodes_keep_their_weighted_average():
    """Several targets blend by the normalised weights: W0 0.5 / W1 0 = the first target, W0 1 / W1 3 = the weighted
    average; every weight 0 = the node's own place (Maya's rest position with Maintain Offset)."""
    child, _targets, pos = _object_scene(2)
    group = multi.member(child.constraints[0], child).group
    (p0, _l0), (p1, _l1) = multi.weights(child, group)
    ad = child.animation_data
    fc = ad.drivers.find(child.constraints[0].path_from_id("influence"))
    assert fc is not None and fc.driver.expression == multi.any_weight(2), fc and fc.driver.expression
    for w0, w1, y in ((0.5, 0.0, FOLLOW), (0.0, 0.0, 0.0), (1.0, 3.0, (FOLLOW + 6 * FOLLOW) / 4)):
        child[p0], child[p1] = w0, w1
        child.update_tag()
        bpy.context.view_layer.update()
        assert abs(pos().y - y) < 1e-4, (w0, w1, pos().y, y)
    assert multi.upgrade() == 0
