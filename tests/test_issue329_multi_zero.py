"""Issue #329 (follow-up): a constraint node with two or more targets whose weights are all 0 goes back to its rest
position, like Maya: with Maintain Offset (Constrain > Parent's default) the node's own place, without it the node's
pose when the constraint was made. Any weight above 0 keeps the normalised blend (W0 0 · W1 0.5 = fully on the second
target, equal weights = the average). Objects and joints, typed and keyed weights (keyed 1 -> 0 on both: the average
until the last frame, then the rest position), point / orient / scale without offset, every Interp Type, Set Rest
Position, and scenes saved before this rule."""

import math
import os
from importlib import import_module

import bpy
from mathutils import Euler, Vector

import kit

cb = import_module(kit.MODULE + ".ui.channel_box")
compat = import_module(kit.MODULE + ".compat")
multi = import_module(kit.MODULE + ".operators.constrain_multi")
interp = import_module(kit.MODULE + ".operators.constrain_interp")

OUT = os.path.join(os.environ.get("ALLSET_TEST_OUT", bpy.app.tempdir), "issue329_multi_zero")
FOLLOW = 5.0        # target i moves FOLLOW * (i + 1) along Y after the constraint is made
TOL = 1e-4
TOL_DEG = 0.05      # Blender's float32 transforms


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


def _empty(name, loc=(0.0, 0.0, 0.0), rot_z=0.0, scale=1.0):
    e = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(e)
    e.location = loc
    e.rotation_euler = (0.0, 0.0, math.radians(rot_z))
    e.scale = (scale, scale, scale)
    return e


def _cube(name, x=0.0):
    bpy.ops.mesh.primitive_cube_add(location=(x, 0.0, 0.0))
    ob = bpy.context.active_object
    ob.name = name
    return ob


def _settle():
    for _ in range(3):
        bpy.context.view_layer.update()
        for h in interp.blend_helpers():
            owner = interp.owner_of_helper(h)
            if owner is not None and interp.blend_constraint(owner, h[interp.H_GROUP]) is not None:
                interp.update(owner, h[interp.H_GROUP])
    bpy.context.view_layer.update()


def _object_world(name):
    dg = bpy.context.evaluated_depsgraph_get()
    return bpy.data.objects[name].evaluated_get(dg).matrix_world.copy()


def _constrain_object(owner, targets, ctype, mo=None):
    for ob in bpy.context.scene.objects:
        ob.select_set(ob is owner or ob in targets)
    bpy.context.view_layer.objects.active = owner
    bpy.context.view_layer.update()
    kw = {} if mo is None else {"maintain_offset": 'ON' if mo else 'OFF'}
    assert bpy.ops.allset.constrain(type=ctype, **kw) == {'FINISHED'}
    group = multi.member(owner.constraints[0], owner).group
    _settle()
    return group


def _object_parent_scene(n_targets=2):
    """pCube1 .. pCubeN parent-constrain pCube(N+1) at 3 along X (Constrain > Parent: Maintain Offset on), then the
    targets move along Y."""
    _fresh()
    targets = [_cube(f"pCube{i + 1}") for i in range(n_targets)]
    child = _cube(f"pCube{n_targets + 1}", 3.0)
    group = _constrain_object(child, targets, 'CHILD_OF')
    _move(targets)
    name = child.name
    return child, targets, group, lambda: _object_world(name)


def _joint_parent_scene(n_targets=2, ctype='CHILD_OF', locs=None):
    """locator1 .. locatorN constrain a joint (a pose bone at 3 along X), made with Constrain > Parent / Point."""
    _fresh()
    targets = [_empty(f"locator{i + 1}", locs[i] if locs else (0.0, 0.0, 0.0)) for i in range(n_targets)]
    bpy.ops.object.armature_add(location=(3.0, 0.0, 0.0))
    arm = bpy.context.active_object
    arm.name = "skeleton"
    for ob in bpy.context.scene.objects:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='POSE')
    cb.set_bone_selected(arm.pose.bones[0], True)
    arm.data.bones.active = arm.data.bones[0]
    assert bpy.ops.allset.constrain(type=ctype) == {'FINISHED'}
    pb = arm.pose.bones[0]
    group = multi.member(pb.constraints[0], pb).group
    _settle()

    def world():
        dg = bpy.context.evaluated_depsgraph_get()
        ae = arm.evaluated_get(dg)
        return ae.matrix_world @ ae.pose.bones[0].matrix

    return pb, targets, group, world


def _move(targets):
    for i, t in enumerate(targets):
        t.location = (t.location.x, FOLLOW * (i + 1), t.location.z)
    _settle()


def _set_weights(owner, group, ws):
    for (prop, _label), w in zip(multi.weights(owner, group), ws):
        owner[prop] = float(w)
    owner.id_data.update_tag()
    _settle()


def _angle(m1, m2):
    return math.degrees(m1.to_quaternion().rotation_difference(m2.to_quaternion()).angle)


def _rest_parent(world, own, tag):
    """The node's world matrix equals ``own`` (place and turn)."""
    m = world()
    assert (m.translation - own.translation).length < TOL, (tag, tuple(m.translation), tuple(own.translation))
    assert _angle(m.to_3x3(), own.to_3x3()) < TOL_DEG, (tag, _angle(m.to_3x3(), own.to_3x3()))


def _check_blend_cases(owner, group, world, own, tag):
    """[0, 0] = own place; partial zeros and equal weights blend as before (normalised)."""
    for ws, y in (([1, 1], 1.5 * FOLLOW), ([0, 0.5], 2 * FOLLOW), ([0.3, 0.3], 1.5 * FOLLOW), ([0.5, 0], FOLLOW),
                  ([0, 0], None), ([1, 3], (FOLLOW + 6 * FOLLOW) / 4), ([0, 0], None), ([2, 2], 1.5 * FOLLOW)):
        _set_weights(owner, group, ws)
        if y is None:
            _rest_parent(world, own, (tag, ws))
        else:
            assert abs(world().translation.y - y) < TOL, (tag, ws, world().translation.y, y)


# --- Maintain Offset (Constrain > Parent): every weight 0 = the node's own place --------------------------------------

def test_two_targets_on_an_object_all_zero_go_back_to_its_own_place():
    child, targets, group, world = _object_parent_scene()
    own = child.matrix_basis.copy()
    targets[1].rotation_euler = (0.0, math.radians(90.0), 0.0)    # the targets also turn (about Y: Y stays)
    _settle()
    _check_blend_cases(child, group, world, own, "object")


def test_two_targets_on_a_joint_all_zero_go_back_to_its_own_place():
    pb, targets, group, world = _joint_parent_scene()
    arm = pb.id_data
    own = arm.matrix_world @ arm.data.bones[0].matrix_local        # the joint's own channels are its rest pose
    _move(targets)
    targets[1].rotation_euler = (0.0, math.radians(90.0), 0.0)    # about Y: the node keeps its Y
    _settle()
    _check_blend_cases(pb, group, world, own, "joint")
    bpy.ops.object.mode_set(mode='OBJECT')


def test_three_targets_all_zero_and_one_left():
    child, targets, group, world = _object_parent_scene(3)
    own = child.matrix_basis.copy()
    for ws, y in (([0, 0, 0], None), ([0, 0, 1], 3 * FOLLOW), ([0, 1, 0], 2 * FOLLOW), ([1, 1, 1], 2 * FOLLOW),
                  ([0, 1, 1], 2.5 * FOLLOW), ([0, 0, 0], None)):
        _set_weights(child, group, ws)
        if y is None:
            _rest_parent(world, own, ws)
        else:
            assert abs(world().translation.y - y) < TOL, (ws, world().translation.y, y)


def test_every_weight_driver_is_a_simple_expression():
    child, _targets, group, _world = _object_parent_scene()
    ad = child.animation_data
    first = multi.members(child, group)[0]
    fc = ad.drivers.find(first.path_from_id("influence"))
    assert fc is not None and fc.driver.expression == multi.any_weight(2), fc and fc.driver.expression
    blend = interp.blend_constraint(child, group)
    assert blend is not None and ad.drivers.find(blend.path_from_id("influence")) is not None
    for fc in ad.drivers:
        assert fc.driver.is_simple_expression, (fc.data_path, fc.driver.expression)
    assert multi.upgrade() == 0, "a new node needs nothing rewritten"


# --- keyed weights -------------------------------------------------------------------------------------------------

def _rows():
    return [r for r in bpy.context.scene.allset_cb.rows if r.kind == "CUSTOM" and r.name.startswith(multi.WEIGHT)]


def _key_both(frame, text):
    bpy.context.scene.frame_set(frame)
    rows = _rows()
    assert len(rows) == 2, [(r.kind, r.name) for r in bpy.context.scene.allset_cb.rows]
    for r in rows:
        r.text = text
    cb.set_selected_channels([])            # nothing picked: S keys every keyable channel, the open node's weights too
    assert bpy.ops.allset.set_key() == {'FINISHED'}


def _keyed_scrub(tag, node, world, own):
    cb.set_open(node, cb.con_node(node, node.constraints[0]))
    cb.rebuild_rows()
    _key_both(1, "1")
    _key_both(10, "0")
    keys = [cb.row_key(r) for r in _rows()]
    for key in keys:
        fc = cb.fcurve(node, key)
        assert fc is not None and [(round(k.co.x), round(k.co.y, 6)) for k in fc.keyframe_points] == \
            [(1, 1.0), (10, 0.0)], (tag, key, fc and list(fc.keyframe_points))
    for frame in (1, 5, 10, 9, 1, 10, 7, 10):      # back and forth like a scrub
        bpy.context.scene.frame_set(frame)
        _settle()
        ws = [cb.get_value(node, key) for key in keys]
        if frame < 10:
            assert ws[0] > 0.0 and abs(ws[0] - ws[1]) < 1e-9, (tag, frame, ws)
            assert abs(world().translation.y - 1.5 * FOLLOW) < TOL, (tag, frame, "the average", world().translation.y)
        else:
            assert ws == [0.0, 0.0], (tag, frame, ws)
            _rest_parent(world, own, (tag, frame))


def test_keyed_weights_one_to_zero_scrub_on_an_object():
    child, _targets, _group, world = _object_parent_scene()
    own = child.matrix_basis.copy()
    for ob in bpy.context.scene.objects:
        ob.select_set(ob is child)
    bpy.context.view_layer.objects.active = child
    _keyed_scrub("object", child, world, own)


def test_keyed_weights_one_to_zero_scrub_on_a_joint():
    pb, targets, _group, world = _joint_parent_scene()
    arm = pb.id_data
    own = arm.matrix_world @ arm.data.bones[0].matrix_local
    _move(targets)
    cb.rebuild_rows()
    _keyed_scrub("joint", pb, world, own)
    bpy.ops.object.mode_set(mode='OBJECT')


# --- without Maintain Offset: the rest position is the pose when the constraint was made ------------------------------

def test_point_without_offset_rests_where_it_was_made():
    _fresh()
    a, b = _empty("A", (2.0, 0.0, 0.0)), _empty("B", (6.0, 0.0, 0.0))
    o = _empty("obj", (0.0, 4.0, 0.0))
    group = _constrain_object(o, [a, b], 'COPY_LOCATION')
    made = Vector((4.0, 0.0, 0.0))
    assert (o.matrix_world.translation - made).length < TOL
    assert (o.location - made).length < TOL, ("the own channels hold the pose at creation", tuple(o.location))
    a.location.y = 10.0
    _settle()
    for ws, want in (([1, 1], (4.0, 5.0, 0.0)), ([0, 0], made), ([0, 0.5], (6.0, 0.0, 0.0)),
                     ([0.3, 0.3], (4.0, 5.0, 0.0)), ([0, 0], made)):
        _set_weights(o, group, ws)
        got = _object_world("obj").translation
        assert (got - Vector(want)).length < TOL, (ws, tuple(got), want)
    # Set Rest Position: the current constrained place becomes the rest position
    _set_weights(o, group, [1, 1])
    for ob in bpy.context.scene.objects:
        ob.select_set(ob is o)
    bpy.context.view_layer.objects.active = o
    assert bpy.ops.allset.set_constraint_rest() == {'FINISHED'}
    _set_weights(o, group, [0, 0])
    got = _object_world("obj").translation
    assert (got - Vector((4.0, 5.0, 0.0))).length < TOL, ("after Set Rest Position", tuple(got))


def test_orient_without_offset_rests_where_it_was_made_with_every_interp_type():
    _fresh()
    a, b = _empty("A", rot_z=40.0), _empty("B", rot_z=80.0)
    o = _empty("obj", (0.0, 4.0, 0.0), rot_z=10.0)
    group = _constrain_object(o, [a, b], 'COPY_ROTATION')
    made = Euler((0.0, 0.0, math.radians(60.0))).to_matrix()
    assert _angle(o.matrix_world.to_3x3(), made) < TOL_DEG
    a.rotation_euler.z = 0.0
    _settle()
    for mode in (interp.AVERAGE, interp.SHORTEST, interp.NO_FLIP, interp.LONGEST, interp.AVERAGE):
        assert bpy.ops.allset.constraint_interp(object=o.name, group=group, mode=str(mode)) == {'FINISHED'}
        _set_weights(o, group, [1, 1])
        on = _object_world("obj").to_3x3()
        assert _angle(on, made) > 5.0, (mode, "the weights act")
        if mode in (interp.AVERAGE, interp.SHORTEST):
            assert _angle(on, Euler((0.0, 0.0, math.radians(40.0))).to_matrix()) < TOL_DEG, (mode, "the blend")
        _set_weights(o, group, [0, 0])
        assert _angle(_object_world("obj").to_3x3(), made) < TOL_DEG, (mode, "the rest position")
        _set_weights(o, group, [0, 0.5])
        assert _angle(_object_world("obj").to_3x3(), b.matrix_world.to_3x3()) < TOL_DEG, (mode, "the second target")
        assert (_object_world("obj").translation - Vector((0.0, 4.0, 0.0))).length < TOL


def test_scale_without_offset_rests_where_it_was_made():
    _fresh()
    a, b = _empty("A", scale=2.0), _empty("B", scale=8.0)
    o = _empty("obj", (0.0, 4.0, 0.0), scale=1.5)
    group = _constrain_object(o, [a, b], 'COPY_SCALE')
    assert (o.matrix_world.to_scale() - Vector((4.0, 4.0, 4.0))).length < TOL      # the geometric mean
    a.scale = (1.0, 1.0, 1.0)
    _settle()
    for ws, want in (([1, 1], math.sqrt(8.0)), ([0, 0], 4.0), ([0, 1], 8.0), ([1, 0], 1.0), ([0, 0], 4.0)):
        _set_weights(o, group, ws)
        got = _object_world("obj").to_scale()
        assert (got - Vector((want,) * 3)).length < TOL, (ws, tuple(got), want)


def test_joint_point_without_offset_rests_where_it_was_made():
    pb, targets, group, world = _joint_parent_scene(ctype='COPY_LOCATION', locs=[(1.0, 0.0, 0.0), (5.0, 0.0, 2.0)])
    made = Vector((3.0, 0.0, 1.0))
    assert (world().translation - made).length < TOL, tuple(world().translation)
    _move(targets)
    for ws, want in (([1, 1], (3.0, 7.5, 1.0)), ([0, 0], made), ([0, 0.5], (5.0, 10.0, 2.0)), ([0, 0], made)):
        _set_weights(pb, group, ws)
        assert (world().translation - Vector(want)).length < TOL, (ws, tuple(world().translation), want)
    bpy.ops.object.mode_set(mode='OBJECT')


def test_keyed_and_driven_channels_keep_their_curves():
    """The rest position goes only into channels no key or driver sets: a keyed or driven axis keeps its curve."""
    _fresh()
    a, b = _empty("A", (2.0, 0.0, 0.0)), _empty("B", (6.0, 2.0, 0.0))
    o = _empty("obj", (0.0, 4.0, 0.0))
    o.keyframe_insert("location", index=0, frame=1)                  # X keyed at 0
    fc = o.driver_add("location", 2)                                 # Z driven: 1.5
    fc.driver.type = 'SCRIPTED'
    fc.driver.expression = "1.5"
    for m in list(fc.modifiers):
        fc.modifiers.remove(m)
    group = _constrain_object(o, [a, b], 'COPY_LOCATION')
    assert abs(o.location.y - 1.0) < TOL, ("the free axis holds the pose at creation", tuple(o.location))
    assert abs(o.location.x) < TOL, ("the keyed axis keeps its value", tuple(o.location))
    keys = [tuple(k.co) for fc in compat.id_fcurves(o) for k in fc.keyframe_points]
    assert keys == [(1.0, 0.0)], keys
    _set_weights(o, group, [0, 0])
    got = _object_world("obj").translation
    assert (got - Vector((0.0, 1.0, 1.5))).length < TOL, ("keyed X, rest Y, driven Z", tuple(got))
    # Euler rotation: a keyed axis stays, the others take the pose at creation
    _fresh()
    a, b = _empty("A", rot_z=40.0), _empty("B", rot_z=80.0)
    o = _empty("obj", (0.0, 4.0, 0.0), rot_z=10.0)
    o.rotation_euler.x = math.radians(15.0)
    o.keyframe_insert("rotation_euler", index=2, frame=1)
    group = _constrain_object(o, [a, b], 'COPY_ROTATION')
    assert abs(o.rotation_euler.x) < 1e-5 and abs(math.degrees(o.rotation_euler.z) - 10.0) < 1e-4, \
        tuple(o.rotation_euler)
    _set_weights(o, group, [0, 0])
    assert _angle(_object_world("obj").to_3x3(), Euler((0.0, 0.0, math.radians(10.0))).to_matrix()) < TOL_DEG


def test_one_undo_takes_the_node_and_its_rest_position_back():
    _fresh()
    a, b = _empty("A", (2.0, 0.0, 0.0)), _empty("B", (6.0, 0.0, 0.0))
    o = _empty("obj", (0.0, 4.0, 0.0))
    for ob in bpy.context.scene.objects:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.ed.undo_push(message="start")
    assert bpy.ops.allset.constrain('EXEC_DEFAULT', True, type='COPY_LOCATION') == {'FINISHED'}
    o = bpy.data.objects["obj"]
    assert len(o.constraints) == 2 and (o.location - Vector((4.0, 0.0, 0.0))).length < TOL, tuple(o.location)
    bpy.ops.ed.undo()
    o = bpy.data.objects["obj"]
    assert not o.constraints and (o.location - Vector((0.0, 4.0, 0.0))).length < TOL, tuple(o.location)


# --- scenes saved before this rule -----------------------------------------------------------------------------------

def _old_drivers(owner, group):
    """Turn a node's drivers back into the earlier ones: first member undriven at 1, the others falling back to the
    equal average, the Interp Type blend undriven."""
    ad = owner.id_data.animation_data
    names = [p for p, _l in multi.weights(owner, group)]
    s = "+".join(f"w{j}" for j in range(len(names)))
    for c in multi.members(owner, group) + [interp.blend_constraint(owner, group)]:
        if c is None:
            continue
        fc = ad.drivers.find(c.path_from_id("influence"))
        if fc is None:
            continue
        k = int(multi._NAME.match(c.name)["index"]) if multi.member(c, owner) is not None else 0
        if k == 0:
            c.driver_remove("influence")
            c.influence = 1.0
        else:
            fc.driver.expression = f"w{k} / ({s}) if ({s}) > 0 else 0.5"


def _save_and_open(name):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    bpy.ops.wm.save_as_mainfile(filepath=path, copy=True)
    bpy.ops.wm.open_mainfile(filepath=path)
    cb.reset_open()
    cb.set_selected_channels([])


def test_older_scenes_get_the_rest_rule_on_load():
    for mode in (interp.AVERAGE, interp.SHORTEST):
        child, _targets, group, world = _object_parent_scene()
        own = child.matrix_basis.copy()
        if mode != interp.AVERAGE:
            assert bpy.ops.allset.constraint_interp(object=child.name, group=group, mode=str(mode)) == {'FINISHED'}
        _old_drivers(child, group)
        _set_weights(child, group, [0, 0])
        assert abs(world().translation.y - 1.5 * FOLLOW) < TOL, (mode, "the old scene: the equal average")
        _save_and_open(f"old_multi_zero_{mode}.blend")
        child = bpy.data.objects["pCube3"]
        _settle()
        assert (_object_world("pCube3").translation - own.translation).length < TOL, (mode, "after the load")
        assert _angle(_object_world("pCube3").to_3x3(), own.to_3x3()) < TOL_DEG
        _set_weights(child, group, [0, 0.5])
        assert abs(_object_world("pCube3").translation.y - 2 * FOLLOW) < TOL, mode
        _set_weights(child, group, [1, 1])
        assert abs(_object_world("pCube3").translation.y - 1.5 * FOLLOW) < TOL, mode
        assert multi.upgrade() == 0, (mode, "a second pass writes nothing")


def test_a_users_own_driver_on_a_member_stays():
    child, _targets, group, _world = _object_parent_scene()
    first = multi.members(child, group)[0]
    child["ctrl"] = 1.0
    first.driver_remove("influence")
    fc = first.driver_add("influence")
    fc.driver.type = 'SCRIPTED'
    v = fc.driver.variables.new()
    v.name = "ctrl"
    v.targets[0].id = child
    v.targets[0].data_path = '["ctrl"]'
    fc.driver.expression = "ctrl"
    multi.upgrade()
    fc = child.animation_data.drivers.find(first.path_from_id("influence"))
    assert fc is not None and fc.driver.expression == "ctrl", fc and fc.driver.expression
