"""Hypergraph: Hierarchy shows joints as nodes (#566): joint1 > joint2 > joint3 under each other, a kit skeleton's
root joints in place of the skeleton object, a named skeleton as a node with its root joints under it, objects
parented to a joint under that joint. Clicking joint nodes picks the joints; joints picked with other nodes stand for
their skeleton; a middle-mouse drop onto a joint parents under that joint."""

from importlib import import_module

import bpy

import kit

hg = import_module(kit.MODULE + ".ui.hypergraph")
cmds = import_module(kit.MODULE + ".command_line.cmds_shim")
channel_box = import_module(kit.MODULE + ".ui.channel_box")


def _skeleton():
    """skeleton object with joint1 > joint2 > joint3 and joint1 > joint4, a cube parented to joint2, a free null."""
    bpy.ops.wm.read_homefile(use_empty=True)
    cmds.joint(p=(0, 0, 0))
    cmds.joint(p=(0, 2, 0))
    cmds.joint(p=(0, 4, 0))
    cmds.select("joint1")
    cmds.joint(p=(2, 0, 0))
    arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    sc = bpy.context.scene
    me = bpy.data.meshes.new("pCubeShape1")
    me.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [], [(0, 1, 2)])
    cube = bpy.data.objects.new("pCube1", me)
    sc.collection.objects.link(cube)
    cube.parent = arm
    cube.parent_type = 'BONE'
    cube.parent_bone = "joint2"
    null = bpy.data.objects.new("null1", None)
    sc.collection.objects.link(null)
    for o in sc.objects:
        o.select_set(False)
    bpy.context.view_layer.update()
    return arm, cube, null


def _j(arm, name):
    return ('B', arm.session_uid, name)


def test_joints_are_nodes_under_each_other():
    arm, cube, null = _skeleton()
    nodes, by = hg.graph(bpy.context.scene)
    parent = dict(nodes)
    assert arm.session_uid not in parent             # a kit skeleton: its root joint is the top node
    assert parent[_j(arm, "joint1")] is None
    assert parent[_j(arm, "joint2")] == _j(arm, "joint1")
    assert parent[_j(arm, "joint3")] == _j(arm, "joint2")
    assert parent[_j(arm, "joint4")] == _j(arm, "joint1")
    assert parent[cube.session_uid] == _j(arm, "joint2")       # parented to a joint: under that joint
    assert parent[null.session_uid] is None
    kids = [k for k, p in nodes if p == _j(arm, "joint1")]
    assert kids == [_j(arm, "joint2"), _j(arm, "joint4")]       # creation order
    assert by[_j(arm, "joint3")] is arm and hg.node_kind(arm, _j(arm, "joint3")) == 'JOINT'
    cents, _n, _b = hg.centres(bpy.context.scene)
    assert {_j(arm, n) for n in ("joint1", "joint2", "joint3", "joint4")} <= set(cents)
    # collapsing a joint hides what is under it
    hg.COLLAPSED.clear()
    hg.toggle_collapsed(_j(arm, "joint2"))
    cents, _n, _b = hg.centres(bpy.context.scene)
    assert _j(arm, "joint3") not in cents and cube.session_uid not in cents and _j(arm, "joint4") in cents
    hg.COLLAPSED.clear()


def test_named_skeleton_is_a_node_with_its_root_joints_under_it():
    arm, _cube, _null = _skeleton()
    arm.name = "rig"
    nodes, _by = hg.graph(bpy.context.scene)
    parent = dict(nodes)
    assert parent[arm.session_uid] is None
    assert parent[_j(arm, "joint1")] == arm.session_uid


def test_object_parented_to_a_kit_skeleton_hangs_from_its_root_joint():
    arm, _cube, null = _skeleton()
    null.parent = arm
    bpy.context.view_layer.update()
    nodes, _by = hg.graph(bpy.context.scene)
    assert dict(nodes)[null.session_uid] == _j(arm, "joint1")


def _picked(arm):
    return sorted(pb.name for pb in arm.pose.bones if channel_box.bone_selected(pb)) if arm.mode == 'POSE' else []


def test_clicking_joint_nodes_picks_joints():
    arm, cube, null = _skeleton()
    _nodes, by = hg.graph(bpy.context.scene)
    ctx = bpy.context
    hg.select(ctx, by, [_j(arm, "joint2")], 'REPLACE', lead=_j(arm, "joint2"))
    assert arm.mode == 'POSE' and _picked(arm) == ["joint2"]
    assert hg.node_state(ctx, _j(arm, "joint2"), arm)[:2] == (True, True)
    assert not hg.node_state(ctx, _j(arm, "joint1"), arm)[0]
    hg.select(ctx, by, [_j(arm, "joint3")], 'TOGGLE', lead=_j(arm, "joint3"))
    assert _picked(arm) == ["joint2", "joint3"]
    hg.select(ctx, by, [_j(arm, "joint2")], 'REMOVE')
    assert _picked(arm) == ["joint3"]
    hg.select(ctx, by, [_j(arm, "joint1"), _j(arm, "joint4")], 'REPLACE', lead=_j(arm, "joint4"))
    assert _picked(arm) == ["joint1", "joint4"] and arm.data.bones.active.name == "joint4"
    # an object node picked after joints: Object Mode, only that object
    hg.select(ctx, by, [null.session_uid], 'REPLACE', lead=null.session_uid)
    assert ctx.mode == 'OBJECT' and null.select_get() and not arm.select_get()
    assert not hg.node_state(ctx, _j(arm, "joint4"), arm)[0]


def test_joints_with_objects_stand_for_their_skeleton():
    arm, cube, null = _skeleton()
    _nodes, by = hg.graph(bpy.context.scene)
    ctx = bpy.context
    hg.select(ctx, by, [_j(arm, "joint3"), null.session_uid], 'REPLACE', lead=null.session_uid)
    assert ctx.mode == 'OBJECT'
    assert arm.select_get() and null.select_get() and not cube.select_get()
    assert ctx.view_layer.objects.active == null
    # a picked kit skeleton in Object Mode shows as its root joint
    assert hg.node_state(ctx, _j(arm, "joint1"), arm)[0] and not hg.node_state(ctx, _j(arm, "joint2"), arm)[0]


def test_mmb_drop_onto_a_joint_parents_there():
    arm, cube, null = _skeleton()
    null.location = (1.0, 2.0, 3.0)
    bpy.context.view_layer.update()
    world = null.matrix_world.translation.copy()
    _nodes, by = hg.graph(bpy.context.scene)
    n, _msg = hg.drop(bpy.context, by, null.session_uid, _j(arm, "joint3"))
    bpy.context.view_layer.update()
    assert n == 1 and null.parent == arm and null.parent_type == 'BONE' and null.parent_bone == "joint3"
    assert (null.matrix_world.translation - world).length < 1e-5
    nodes, by = hg.graph(bpy.context.scene)
    assert dict(nodes)[null.session_uid] == _j(arm, "joint3")
    # a joint dropped onto another joint of its skeleton goes under it
    n, _msg = hg.drop(bpy.context, by, _j(arm, "joint4"), _j(arm, "joint3"))
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    assert n >= 1 and arm.data.bones["joint4"].parent.name == "joint3"
    nodes, _by = hg.graph(bpy.context.scene)
    assert dict(nodes)[_j(arm, "joint4")] == _j(arm, "joint3")
