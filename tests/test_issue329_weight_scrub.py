"""Issue #329 (follow-up): a keyed constraint target weight drives the constraint on every frame. Type 1 in the
Channel Box weight at frame 1 and key it, type 0 at frame 10 and key it, then scrub: the weight and the constrained
object's or joint's evaluated position follow the keys (1, a blend, 0). Covers a one-target constraint on an object,
a two-target node on an object, a joint following a locator (one target) and a joint following two locators, keyed
with S (the constraint node open in the Channel Box) and with Channels > Key Selected."""

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
FOLLOW = 5.0        # the (first) target moves 5 along Y after the constraint is made: weight 1 = 5, weight 0 = 0


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

    def pos():
        dg = bpy.context.evaluated_depsgraph_get()
        return child.evaluated_get(dg).matrix_world.translation.copy()

    return child, targets, pos


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


def _rows():
    """The Channel Box weight rows: a one-target constraint's (CONSTRAINT) or a node's W0, W1 ... (CUSTOM)."""
    return [r for r in bpy.context.scene.allset_cb.rows
            if r.kind == "CONSTRAINT" or (r.kind == "CUSTOM" and r.name.startswith(multi.WEIGHT))]


def _expected_y(w0, n_targets):
    """Y of the constrained node for first weight w0 (the others 1): one target = blend to its own place (0),
    several = the weighted average of the targets (target i follows to FOLLOW * (i + 1))."""
    if n_targets == 1:
        return FOLLOW * w0
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


def _check_scrub(tag, node, key, pos, n_targets):
    fc = cb.fcurve(node, key)
    assert fc is not None, (tag, "the weight has no curve", [f.data_path for f in compat.id_fcurves(node.id_data)])
    assert [(round(k.co.x), round(k.co.y, 6)) for k in fc.keyframe_points] == [(1, 1.0), (10, 0.0)], \
        (tag, [(k.co.x, k.co.y) for k in fc.keyframe_points])
    for frame in (10, 5, 1, 7, 10):       # back and forth like a scrub
        bpy.context.scene.frame_set(frame)
        want = fc.evaluate(frame)
        got = cb.get_value(node, key)
        assert abs(got - want) < 1e-5, (tag, frame, "Channel Box value", got, want)
        assert abs(float(_rows()[0].text) - want) < 1e-3, (tag, frame, "row text", _rows()[0].text, want)
        y = pos().y
        assert abs(y - _expected_y(want, n_targets)) < 1e-4, (tag, frame, "position", y, _expected_y(want, n_targets))
    bpy.context.scene.frame_set(5)
    assert 0.05 < cb.get_value(node, key) < 0.95, (tag, "a blend between the keys")


def _case(tag, make, n_targets, how):
    node, _targets, pos = make(n_targets)
    rows = _rows()
    assert rows, (tag, "weight rows", [(r.kind, r.name) for r in bpy.context.scene.allset_cb.rows])
    key = cb.row_key(rows[0])
    _key_weight(how, 1, "1")
    _key_weight(how, 10, "0")
    _check_scrub(f"{tag}-{how}", node, key, pos, n_targets)
    if bpy.context.object is not None and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')


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
    cb.set_open(a, cb.con_node(a, a.constraints[0]))
    cb.rebuild_rows()
    bpy.context.scene.frame_set(4)
    b.constraints[0].influence = 0.25
    assert bpy.ops.allset.set_key() == {'FINISHED'}
    for ob, v in ((a, 1.0), (b, 0.25)):
        fc = cb.fcurve(ob, key)
        assert fc is not None and [(round(k.co.x), round(k.co.y, 6)) for k in fc.keyframe_points] == [(4, v)], ob.name
    # a driven weight is the driver's: S leaves it alone
    d = b.constraints[0].driver_add("influence")
    d.driver.expression = "0.5"
    cb.fcurve(b, key).keyframe_points.clear()
    bpy.context.scene.frame_set(8)
    assert bpy.ops.allset.set_key() == {'FINISHED'}
    assert len(cb.fcurve(b, key).keyframe_points) == 0, "no key on a driven weight"
    assert len(cb.fcurve(a, key).keyframe_points) == 2


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
    for w, y in ((1.0, FOLLOW), (0.0, 0.0), (0.4, 0.4 * FOLLOW), (3.0, FOLLOW), (-1.0, 0.0)):
        _set_weight(pb, prop, w)
        assert abs(pos().y - y) < 1e-4, (w, pos().y, y)
    bpy.ops.object.mode_set(mode='OBJECT')


def test_one_target_weight_blends_rotation_with_every_interp_type():
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
        assert abs(on - 90.0) < 0.01 and off < 0.01 and 1.0 < half < 89.0, (mode, on, off, half)
        assert (p_off - Vector((3.0, 0.0, 0.0))).length < 1e-4, (mode, "weight 0: the joint's own place", p_off)
        assert (p_half - (p_on + p_off) / 2).length < 1e-4, (mode, p_on, p_off, p_half)
    bpy.ops.object.mode_set(mode='OBJECT')


def test_older_one_target_groups_get_the_driver_on_load():
    pb, _loc, pos, group = _single_joint()
    arm = pb.id_data
    prop = _weight_prop(pb, group)
    for c in multi.members(pb, group):         # a group made before the weight drove anything
        c.driver_remove("influence")
        c.influence = 1.0
    _set_weight(pb, prop, 0.0)
    assert abs(pos().y - FOLLOW) < 1e-4, "the old group ignores its weight"
    bpy.ops.object.mode_set(mode='OBJECT')
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "old_single_target.blend")
    bpy.ops.wm.save_as_mainfile(filepath=path, copy=True)
    bpy.ops.wm.open_mainfile(filepath=path)
    arm = bpy.data.objects["skeleton"]
    pb = arm.pose.bones[0]
    bpy.context.view_layer.update()
    y = (arm.matrix_world @ pb.matrix).translation.y
    assert abs(y) < 1e-4, ("weight 0 after the load: the joint's own place", y)
    pb[prop] = 1.0
    arm.update_tag()
    bpy.context.view_layer.update()
    assert abs((arm.matrix_world @ pb.matrix).translation.y - FOLLOW) < 1e-4
    assert multi.upgrade() == 0, "a second pass writes nothing"


def test_two_target_nodes_keep_their_weighted_average():
    """The first target's constraints stay undriven with several targets: W0 0.5 / W1 0 = the first target, every
    weight 0 = the equal average."""
    child, _targets, pos = _object_scene(2)
    group = multi.member(child.constraints[0], child).group
    (p0, _l0), (p1, _l1) = multi.weights(child, group)
    ad = child.animation_data
    assert ad.drivers.find(child.constraints[0].path_from_id("influence")) is None
    for w0, w1, y in ((0.5, 0.0, FOLLOW), (0.0, 0.0, 1.5 * FOLLOW), (1.0, 3.0, (FOLLOW + 6 * FOLLOW) / 4)):
        child[p0], child[p1] = w0, w1
        child.update_tag()
        bpy.context.view_layer.update()
        assert abs(pos().y - y) < 1e-4, (w0, w1, pos().y, y)
    assert multi.upgrade() == 0
