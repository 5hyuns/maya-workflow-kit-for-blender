"""Issue #355: a display layer made from a picked joint holds that joint, not its whole skeleton (like Maya).

The layer's state reaches the member joint, the joints below it and the objects under them; the joint above it stays
shown and pickable, the skeleton object is not hidden and no joint's own Visibility changes. Template / Reference
joints can't be picked; a parent's layer wins over a child's. Add moves a joint between layers, Remove / Empty / Delete
give it back, Select Objects picks the member joints. A kit skeleton picked as a whole stands for its root joints;
older files whose layer holds a skeleton object keep working. Membership survives renames, save / reload, a
duplicated skeleton and undo."""

import os
from importlib import import_module
from types import SimpleNamespace

import bpy
from mathutils import Matrix, Vector

import kit

le = import_module(kit.MODULE + ".ui.layer_editor")
lj = import_module(kit.MODULE + ".ui.layer_joints")
ot = import_module(kit.MODULE + ".ui.outliner_tree")
cb = import_module(kit.MODULE + ".ui.channel_box")
joints = import_module(kit.MODULE + ".operators.joints")
js = import_module(kit.MODULE + ".operators.joint_selection")
sp = import_module(kit.MODULE + ".operators.select_priority")
dag = import_module(kit.MODULE + ".operators.dag")

HIDDEN, TEMPLATE, REFERENCE = lj.HIDDEN, lj.TEMPLATE, lj.REFERENCE
IO = os.path.join(os.environ.get("ALLSET_TEST_TMP", bpy.app.tempdir), "issue355")


def _object_mode():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')


def _clear():
    _object_mode()
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for data in (bpy.data.armatures, bpy.data.meshes):
        for d in list(data):
            data.remove(d)
    scene = bpy.context.scene
    for coll in list(le.layers(scene)):
        bpy.data.collections.remove(coll)
    scene.allset_layer_index = 0


def _chain(name=None):
    """joint1 (0, 0, 0) > joint2 (0, 0, 1) > joint3 (0, 0, 2) of a new kit skeleton, Object Mode, nothing selected."""
    arm = joints.new_skeleton(bpy.context)
    made, parent = [], None
    for z in range(3):
        parent = joints.add_joint(arm, Vector((0.0, 0.0, float(z))), parent, length=0.5)
        made.append(parent)
    joints.finish(bpy.context, arm, made)
    _object_mode()
    if name:
        arm.name = name
    _deselect()
    return arm, made


def _deselect():
    _object_mode()
    js.clear(bpy.context)
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    bpy.context.view_layer.objects.active = None


def _pose_pick(arm, *names):
    """The joints picked in a view in Pose Mode (what a click does with a tool other than Move)."""
    _deselect()
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='POSE')
    for pb in arm.pose.bones:
        cb.set_bone_selected(pb, pb.name in names)
    arm.data.bones.active = arm.data.bones[names[-1]]


def _new_layer_from_selected():
    assert bpy.ops.allset.layer_new(selected=True) == {'FINISHED'}
    return le.active_layer(bpy.context)


def _empty(name, parent, bone=None):
    e = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(e)
    e.parent = parent
    if bone:
        e.parent_type = 'BONE'
        e.parent_bone = bone
    return e


def _upd():
    bpy.context.view_layer.update()
    dag.sync()


def _front_view():
    """Front orthographic region 200 x 100: world (x, z) -> (100 + 20 x, 50 + 20 z) px."""
    view = Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, -1, 0, -10), (0, 0, 0, 1)))
    proj = Matrix(((0.2, 0, 0, 0), (0, 0.4, 0, 0), (0, 0, -0.01, 0), (0, 0, 0, 1)))
    return SimpleNamespace(region_data=SimpleNamespace(perspective_matrix=proj @ view),
                           region=SimpleNamespace(width=200, height=100), space_data=None, window=None,
                           scene=bpy.context.scene, evaluated_depsgraph_get=bpy.context.evaluated_depsgraph_get)


def _row_hidden(arm, name):
    row = ot.Row('JOINT', arm.name, name, 0, False, False, name, 'JOINT', None, False)
    return ot.row_state(bpy.context, row, set())[2]


def test_a_layer_from_a_picked_joint_holds_that_joint():
    _clear()
    arm, (j1, j2, j3) = _chain()
    _pose_pick(arm, j2)
    coll = _new_layer_from_selected()
    assert lj.members(coll, bpy.context.scene) == {arm: [j2]}, lj.members(coll, bpy.context.scene)
    assert arm.name not in coll.objects, "the skeleton object is no member"
    coll.allset_layer.visible = False
    _upd()
    assert dict(lj.state(arm)) == {j2: HIDDEN, j3: HIDDEN}, dict(lj.state(arm))
    assert arm.visible_get() and not arm.hide_get(), "the skeleton object stays shown"
    assert not any(pb.hide for pb in arm.pose.bones), "no joint's own Visibility changes"
    assert [pb.name for pb in js.root_joints(arm)] == [j1]
    assert not _row_hidden(arm, j1) and _row_hidden(arm, j2) and _row_hidden(arm, j3)
    coll.allset_layer.visible = True
    _upd()
    assert not lj.state(arm) and not _row_hidden(arm, j3)


def test_b_edit_mode_pick_holds_the_picked_joint_only():
    """With the Move tool an unskinned skeleton's joint is picked in Edit Mode with its subtree selected: the layer
    still holds the picked joint only."""
    _clear()
    arm, (j1, j2, j3) = _chain()
    _deselect()
    js.select_edit(bpy.context, arm, j2)
    assert arm.mode == 'EDIT' and arm.data.edit_bones[j3].select, "the subtree is selected for the move"
    coll = _new_layer_from_selected()
    assert lj.members(coll, bpy.context.scene) == {arm: [j2]}
    coll.allset_layer.visible = False
    assert dict(lj.state(arm)) == {j2: HIDDEN, j3: HIDDEN}, "Edit Mode reads the edit bones' hierarchy"
    bpy.ops.object.mode_set(mode='POSE')
    assert lj.members(coll, bpy.context.scene) == {arm: [j2]}, "leaving Edit Mode keeps the membership"
    assert dict(lj.state(arm)) == {j2: HIDDEN, j3: HIDDEN}


def test_c_objects_under_hidden_joints_follow_and_skin_keeps_deforming():
    _clear()
    arm, (j1, j2, j3) = _chain()
    on3 = _empty("loc3", arm, j3)
    on1 = _empty("loc1", arm, j1)
    on_skel = _empty("locS", arm)                    # parented to the skeleton itself: under its first root joint
    me = bpy.data.meshes.new("skinShape")
    me.from_pydata([(0.5, 0.0, 2.0), (0.6, 0.0, 2.0), (0.5, 0.1, 2.0)], [], [(0, 1, 2)])
    skin = bpy.data.objects.new("skin", me)
    bpy.context.scene.collection.objects.link(skin)
    vg = skin.vertex_groups.new(name=j3)
    vg.add([0, 1, 2], 1.0, 'REPLACE')
    mod = skin.modifiers.new("Armature", 'ARMATURE')
    mod.object = arm
    _pose_pick(arm, j2)
    coll = _new_layer_from_selected()
    coll.allset_layer.visible = False
    _upd()
    assert not on3.visible_get() and dag.MARK in on3, "an object under a hidden joint is hidden"
    assert on1.visible_get() and on_skel.visible_get(), "objects above the member stay shown"
    assert not on3.hide_viewport, "its own Visibility stays on"
    assert skin.visible_get(), "the skinned surface is no member"
    dg = bpy.context.evaluated_depsgraph_get()
    before = skin.evaluated_get(dg).data.vertices[0].co.copy()
    pb = arm.pose.bones[j2]
    pb.rotation_mode = 'XYZ'
    pb.rotation_euler = (0.0, 0.7, 0.0)
    bpy.context.view_layer.update()
    after = skin.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.vertices[0].co
    assert (after - before).length > 0.1, "the hidden joints still deform the skin"
    # the root joint in a hidden layer: the whole skeleton and the object parented to the skeleton
    _pose_pick(arm, j1)
    root_layer = _new_layer_from_selected()
    root_layer.allset_layer.visible = False
    _upd()
    assert dict(lj.state(arm)) == {j1: HIDDEN, j2: HIDDEN, j3: HIDDEN}
    assert not on_skel.visible_get() and not on1.visible_get()
    root_layer.allset_layer.visible = True
    coll.allset_layer.visible = True
    _upd()
    assert on3.visible_get() and on1.visible_get() and on_skel.visible_get() and dag.MARK not in on3


def test_d_template_and_reference_joints_are_not_picked():
    _clear()
    arm, (j1, j2, j3) = _chain()
    _pose_pick(arm, j2)
    coll = _new_layer_from_selected()
    _deselect()
    ctx = _front_view()
    assert js.pick(ctx, arm, (100, 90), 6) == j3, "Normal: joint3 is picked"
    n_normal = len(sp._segments(arm, 'ARMATURE', bpy.context.evaluated_depsgraph_get())[0])
    for kind in (TEMPLATE, REFERENCE):
        coll.allset_layer.display_type = kind
        assert dict(lj.state(arm)) == {j2: kind, j3: kind}, (kind, dict(lj.state(arm)))
        assert js.pick(ctx, arm, (100, 90), 6) is None, kind
        assert js.pick(ctx, arm, (100, 70), 6) == j1, "joint2's place: the bone of joint1 (a bone is its parent's)"
        assert sp.pick_joint(ctx, arm, (100, 90), 6) is None, kind
        assert js.pick(ctx, arm, (100, 50), 6) == j1, "the joint above the member is picked"
        n = len(sp._segments(arm, 'ARMATURE', bpy.context.evaluated_depsgraph_get())[0])
        assert n == n_normal - 2, (kind, n, n_normal)
        assert arm.visible_get() and not arm.hide_select and arm.display_type != 'WIRE', "the object is untouched"
    coll.allset_layer.display_type = 'NORMAL'
    assert not lj.state(arm) and js.pick(ctx, arm, (100, 90), 6) == j3


def test_e_a_parent_layer_wins_over_a_child_layer():
    _clear()
    arm, (j1, j2, j3) = _chain()
    _pose_pick(arm, j3)
    child = _new_layer_from_selected()
    _pose_pick(arm, j1)
    parent = _new_layer_from_selected()
    parent.allset_layer.display_type = TEMPLATE
    assert dict(lj.state(arm)) == {j1: TEMPLATE, j2: TEMPLATE, j3: TEMPLATE}, "Template over the child's Normal"
    child.allset_layer.display_type = REFERENCE
    assert lj.state(arm)[j3] == TEMPLATE, "the parent's type wins"
    parent.allset_layer.display_type = 'NORMAL'
    assert dict(lj.state(arm)) == {j3: REFERENCE}
    parent.allset_layer.visible = False
    assert lj.state(arm)[j3] == HIDDEN, "a hidden parent hides a child in a visible layer"
    parent.allset_layer.visible = True
    child.allset_layer.visible = False
    assert dict(lj.state(arm)) == {j3: HIDDEN}


def test_f_add_moves_remove_empty_delete_give_back():
    _clear()
    arm, (j1, j2, j3) = _chain()
    on3 = _empty("loc3", arm, j3)
    scene = bpy.context.scene
    _pose_pick(arm, j2)
    first = _new_layer_from_selected()
    second = le.new_layer(scene)
    scene.allset_layer_index = le.layers(scene).index(second)
    assert bpy.ops.allset.layer_assign(remove=False) == {'FINISHED'}
    assert lj.members(first, scene) == {} and lj.members(second, scene) == {arm: [j2]}, "Add moves the joint"
    second.allset_layer.visible = False
    _upd()
    assert lj.hidden(arm, j3) and not on3.visible_get()
    assert bpy.ops.allset.layer_assign(remove=True) == {'FINISHED'}
    _upd()
    assert lj.members(second, scene) == {} and not lj.state(arm) and on3.visible_get(), "Remove gives it back"
    assert bpy.ops.allset.layer_assign(remove=False) == {'FINISHED'}
    assert bpy.ops.allset.layer_empty() == {'FINISHED'}
    _upd()
    assert lj.members(second, scene) == {} and not lj.state(arm) and on3.visible_get(), "Empty gives it back"
    assert bpy.ops.allset.layer_assign(remove=False) == {'FINISHED'}
    second.allset_layer.display_type = TEMPLATE
    assert lj.state(arm)
    assert bpy.ops.allset.layer_delete() == {'FINISHED'}
    _upd()
    assert lj.layer_of(arm.pose.bones[j2]) is None and not lj.state(arm) and on3.visible_get()
    assert le.layers(scene) == [first]


def test_g_select_objects_picks_the_member_joints():
    _clear()
    arm, (j1, j2, j3) = _chain()
    _pose_pick(arm, j2)
    coll = _new_layer_from_selected()
    coll.allset_layer.display_type = REFERENCE
    _deselect()
    assert bpy.ops.allset.layer_select() == {'FINISHED'}
    assert arm.mode == 'POSE' and bpy.context.active_object == arm
    assert [pb.name for pb in arm.pose.bones if cb.bone_selected(pb)] == [j2], "only the member, also in Reference"
    assert arm.data.bones.active.name == j2


def test_h_a_kit_skeleton_picked_as_a_whole_stands_for_its_root_joints():
    _clear()
    arm, (j1, j2, j3) = _chain()
    other, _ = _chain()
    other.name = "rig"                                 # not a kit-named skeleton: an object node
    scene = bpy.context.scene
    _deselect()
    arm.select_set(True)
    other.select_set(True)
    bpy.context.view_layer.objects.active = arm
    coll = _new_layer_from_selected()
    assert lj.members(coll, scene) == {arm: [j1]}, lj.members(coll, scene)
    assert arm.name not in coll.objects and other.name in coll.objects


def test_i_a_mesh_and_a_joint_in_one_layer():
    _clear()
    arm, (j1, j2, j3) = _chain()
    me = bpy.data.objects.new("pCube1", bpy.data.meshes.new("pCubeShape1"))
    bpy.context.scene.collection.objects.link(me)
    _pose_pick(arm, j2)
    bpy.ops.object.mode_set(mode='OBJECT')             # another object picked after the joint keeps it picked
    me.select_set(True)
    coll = _new_layer_from_selected()
    assert me.name in coll.objects and lj.members(coll, bpy.context.scene) == {arm: [j2]}
    assert arm.name not in coll.objects
    coll.allset_layer.visible = False
    _upd()
    assert not me.visible_get() and arm.visible_get() and lj.hidden(arm, j3)


def test_j_an_older_layer_holding_the_skeleton_object_keeps_working():
    _clear()
    arm, (j1, j2, j3) = _chain()
    scene = bpy.context.scene
    old = le.new_layer(scene, [arm])                   # what older files hold: the skeleton object
    old.allset_layer.visible = False
    _upd()
    assert not arm.visible_get() and not lj.state(arm), "the object path hides the whole skeleton"
    old.allset_layer.visible = True
    _upd()
    assert arm.visible_get()
    old.allset_layer.display_type = TEMPLATE
    assert arm.hide_select and arm.display_type == 'WIRE'
    old.allset_layer.display_type = 'NORMAL'
    assert not arm.hide_select and arm.display_type != 'WIRE'
    # the whole kit skeleton picked again: its root joint replaces the object in the layer it is added to
    _deselect()
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    scene.allset_layer_index = le.layers(scene).index(old)
    assert bpy.ops.allset.layer_assign(remove=True) == {'FINISHED'}
    assert arm.name not in old.objects and lj.members(old, scene) == {}, "Remove takes the old object member out"


def test_k_membership_survives_renames_save_reload_duplicate_and_undo():
    _clear()
    arm, (j1, j2, j3) = _chain()
    scene = bpy.context.scene
    _pose_pick(arm, j2)
    coll = _new_layer_from_selected()
    arm.data.bones[j2].name = "elbow"
    coll.name = "armLayer"
    assert lj.members(coll, scene) == {arm: ["elbow"]}
    bpy.ops.object.mode_set(mode='EDIT')
    arm.data.edit_bones["elbow"].name = "elbow2"
    bpy.ops.object.mode_set(mode='POSE')
    assert lj.members(coll, scene) == {arm: ["elbow2"]}, "an Edit Mode rename keeps it"
    os.makedirs(IO, exist_ok=True)
    path = os.path.join(IO, "layers.blend")
    _object_mode()
    name = arm.name
    bpy.ops.wm.save_as_mainfile(filepath=path, copy=True)
    bpy.ops.wm.open_mainfile(filepath=path)
    scene = bpy.context.scene
    arm = bpy.data.objects[name]
    coll = bpy.data.collections["armLayer"]
    assert lj.members(coll, scene) == {arm: ["elbow2"]}, "saved and loaded"
    coll.allset_layer.visible = False
    assert lj.hidden(arm, "elbow2") and lj.hidden(arm, j3)
    coll.allset_layer.visible = True
    _deselect()
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.duplicate()
    dup = bpy.context.active_object
    assert dup != arm and lj.members(coll, scene) == {arm: ["elbow2"], dup: ["elbow2"]}, "a duplicate keeps it"
    # undo takes a new membership back, redo puts it again
    bpy.ops.object.delete()
    _pose_pick(arm, j1)
    bpy.ops.ed.undo_push(message="pick")
    coll2 = _new_layer_from_selected()
    bpy.ops.ed.undo_push(message="New Layer")
    assert lj.members(coll2, bpy.context.scene) == {arm: [j1]}
    bpy.ops.ed.undo()
    arm = bpy.data.objects[name]
    assert lj.layer_of(arm.pose.bones[j1]) is None and len(le.layers(bpy.context.scene)) == 1
    bpy.ops.ed.redo()
    arm = bpy.data.objects[name]
    assert lj.layer_of(arm.pose.bones[j1]) is not None and len(le.layers(bpy.context.scene)) == 2


def test_l_playback_off_hides_only_while_playing():
    _clear()
    arm, (j1, j2, j3) = _chain()
    on3 = _empty("loc3", arm, j3)
    scene = bpy.context.scene
    _pose_pick(arm, j2)
    coll = _new_layer_from_selected()
    coll.allset_layer.playback = False
    _upd()
    assert not lj.state(arm) and on3.visible_get()
    le.on_playback_pre(scene)
    try:
        assert dict(lj.state(arm)) == {j2: HIDDEN, j3: HIDDEN} and not on3.visible_get()
    finally:
        le.on_playback_post(scene)
    assert not lj.state(arm) and on3.visible_get()


def test_m_the_state_is_kept_until_something_changes():
    """A big skeleton: the state is read once and kept while only the pose changes."""
    _clear()
    data = bpy.data.armatures.new("big")
    arm = bpy.data.objects.new("big", data)
    bpy.context.scene.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    prev = None
    for i in range(1000):
        eb = data.edit_bones.new(f"b{i}")
        eb.head, eb.tail = (0.0, 0.0, i * 0.1), (0.0, 0.0, i * 0.1 + 0.1)
        if prev is not None and i % 50:
            eb.parent = prev
        prev = eb
    bpy.ops.object.mode_set(mode='POSE')
    coll = le.new_layer(bpy.context.scene)
    lj.set_layer(arm.pose.bones["b120"], coll)
    coll.allset_layer.visible = False
    bpy.context.view_layer.update()
    st = lj.state(arm)
    assert len(st) == 30 and lj.state(arm) is st, "b120 .. b149 (the chain breaks every 50 bones)"
    rev = lj._REV[0]
    pb = arm.pose.bones["b3"]
    pb.rotation_mode = 'XYZ'
    for k in range(3):
        pb.rotation_euler = (0.1 * k, 0.0, 0.0)
        bpy.context.view_layer.update()
    assert lj._REV[0] == rev and lj.state(arm) is st, "a pose change keeps the state"
    import time
    t = time.perf_counter()
    for _ in range(1000):
        lj.state(arm)
    per = (time.perf_counter() - t) / 1000
    assert per < 2e-4, f"a kept state costs {per * 1e3:.3f} ms"
