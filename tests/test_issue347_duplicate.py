"""#347: Edit > Duplicate (Ctrl+D) copies only the node itself, like Maya: the geometry as it shows now (shape-key mix,
skin pose and deformers baked in), materials, display and children kept, but no history, no deformers, no shape keys,
no animation, no drivers and no constraints, so changing the original's animation leaves the copy alone. Keyed
channels keep their current values. Shift+D, Smart Duplicate (Shift+drag) and ``cmds.duplicate`` make the same copy.
Duplicate Special's "Duplicate input graph" gives the copy its own copies of the inputs (modifiers, shape keys, its own
animation, its own creation node); "Duplicate input connections" lets it share the original's (the same animation
drives both). Instance stays an instance."""

import math
from importlib import import_module

import bpy
from mathutils import Vector

import kit

duplicate = import_module(kit.MODULE + ".operators.duplicate")
display = import_module(kit.MODULE + ".operators.display")
prim_history = import_module(kit.MODULE + ".operators.prim_history")
manip = import_module(kit.MODULE + ".operators.manip")
ow = import_module(kit.MODULE + ".operators.option_windows")
cmds = import_module(kit.MODULE + ".command_line.cmds_shim")

SMILE = 'key_blocks["smile"].value'


def _fresh():
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for coll in (bpy.data.objects, bpy.data.meshes, bpy.data.actions, bpy.data.armatures, bpy.data.materials,
                 bpy.data.curves):
        for idb in list(coll):
            coll.remove(idb)
    duplicate.PAIRS.clear()
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, 24
    sc.frame_set(1)
    ow.store("duplicate_special_maya", None)


def _only(*obs):
    for o in bpy.context.view_layer.objects:
        o.select_set(o in obs)
    bpy.context.view_layer.objects.active = obs[-1]


def _fc(idb, path, index=0):
    fcs = kit.fcurves(idb)
    return fcs.find(path, index=index) if fcs is not None else None


def _set_last_key(idb, path, value, index=0):
    fc = _fc(idb, path, index)
    fc.keyframe_points[-1].co.y = value
    fc.keyframe_points[-1].handle_left.y = value
    fc.keyframe_points[-1].handle_right.y = value
    fc.update()


def _points(ob):
    """World positions of what the object shows now (shape keys, modifiers, constraints)."""
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    return [ev.matrix_world @ v.co for v in ev.data.vertices]


def _same(a, b, eps=1e-4):
    return len(a) == len(b) and all((p - q).length < eps for p, q in zip(a, b))


def _actions(idb):
    ad = getattr(idb, "animation_data", None)
    if ad is None:
        return set()
    out = {ad.action} if ad.action is not None else set()
    for tr in ad.nla_tracks:
        out |= {s.action for s in tr.strips if s.action is not None}
    return out


def _has_animation(idb):
    ad = getattr(idb, "animation_data", None)
    return ad is not None and (ad.action is not None or len(ad.drivers) > 0 or len(ad.nla_tracks) > 0)


def _character():
    """A kit cube (polyCube1) with a red material, a keyed "smile" shape key (0 at frame 1, 1 at frame 11), keyed
    translate X (0 -> 10 cm) and a driver on its scale Z; the scene at frame 6."""
    _fresh()
    assert bpy.ops.allset.create(kind='CUBE') == {'FINISHED'}
    ob = bpy.context.active_object
    mat = bpy.data.materials.new("red")
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    ob.shape_key_add(name="Basis")
    sk = ob.shape_key_add(name="smile", from_mix=False)
    for v in sk.data:
        if v.co.z > 0:
            v.co.z += ob.dimensions.z
    keys = ob.data.shape_keys
    sk.value = 0.0
    keys.keyframe_insert(SMILE, frame=1)
    sk.value = 1.0
    keys.keyframe_insert(SMILE, frame=11)
    ob.location.x = 0.0
    ob.keyframe_insert("location", index=0, frame=1)
    ob.location.x = 0.1
    ob.keyframe_insert("location", index=0, frame=11)
    drv = ob.driver_add("scale", 2).driver
    drv.type = 'SCRIPTED'
    drv.expression = "1.5"
    bpy.context.scene.frame_set(6)
    _only(ob)
    return ob


# --- the report: Ctrl+D -------------------------------------------------------------------------------------

def test_ctrl_d_copy_has_no_animation_and_keeps_the_shape_it_shows():
    ob = _character()
    shown = _points(ob)
    assert abs(ob.data.shape_keys.key_blocks["smile"].value - 0.5) < 1e-4
    assert bpy.ops.allset.duplicate() == {'FINISHED'}
    copy = bpy.context.active_object
    assert (copy.name, copy.data.name) == ("pCube2", "pCubeShape2"), (copy.name, copy.data.name)
    assert copy.data is not ob.data
    assert not _has_animation(copy), "no keys and no drivers on the copy"
    assert copy.data.shape_keys is None, "no blend shape on the copy"
    assert not _has_animation(copy.data)
    assert abs(copy.location.x - 0.05) < 1e-6, f"keyed channels keep the current value ({copy.location.x})"
    assert abs(copy.scale.z - 1.5) < 1e-6, f"driven channels keep the current value ({copy.scale.z})"
    assert _same(_points(copy), shown), "the copy shows the shape the original shows now"
    assert copy.data.materials[0] is ob.data.materials[0], "materials stay"
    assert prim_history.owner_of(copy) is None, "no creation node (polyCube1) on the copy"
    assert prim_history.owner_of(ob) is not None, "the original keeps its creation node"
    # the original is untouched
    assert ob.data.shape_keys is not None and _actions(ob) and _actions(ob.data.shape_keys)


def test_changing_the_original_animation_leaves_the_copy_alone():
    ob = _character()
    assert bpy.ops.allset.duplicate() == {'FINISHED'}
    copy = bpy.context.active_object
    held = _points(copy)
    _set_last_key(ob, "location", 0.3)
    _set_last_key(ob.data.shape_keys, SMILE, 0.25)
    bpy.context.scene.frame_set(11)
    assert abs(ob.location.x - 0.3) < 1e-6, "the original follows its keys"
    assert abs(ob.data.shape_keys.key_blocks["smile"].value - 0.25) < 1e-6
    assert abs(copy.location.x - 0.05) < 1e-6, copy.location.x
    assert _same(_points(copy), held), "the copy holds still"


def test_ctrl_d_is_one_undo_step():
    ob = _character()
    bpy.ops.ed.undo_push(message="before")
    assert bpy.ops.allset.duplicate('EXEC_DEFAULT', True) == {'FINISHED'}
    assert "pCube2" in bpy.data.objects
    bpy.ops.ed.undo()
    assert "pCube2" not in bpy.data.objects, "one undo takes the copy back"
    ob = bpy.data.objects["pCube1"]
    assert ob.data.shape_keys is not None and _actions(ob) and _actions(ob.data.shape_keys)


def test_skinned_mesh_copy_is_the_pose_now():
    """A skinned mesh (Armature modifier, keyed bone): the copy is the deformed shape now, without the skin."""
    _fresh()
    arm_data = bpy.data.armatures.new("skeleton")
    arm = bpy.data.objects.new("joint1", arm_data)
    bpy.context.collection.objects.link(arm)
    _only(arm)
    bpy.ops.object.mode_set(mode='EDIT')
    b1 = arm_data.edit_bones.new("joint1")
    b1.head, b1.tail = (0, 0, 0), (0, 0, 1)
    b2 = arm_data.edit_bones.new("joint2")
    b2.head, b2.tail, b2.parent = (0, 0, 1), (0, 0, 2), b1
    bpy.ops.object.mode_set(mode='OBJECT')
    pb = arm.pose.bones["joint2"]
    pb.rotation_mode = 'XYZ'
    pb.rotation_euler.x = 0.0
    pb.keyframe_insert("rotation_euler", index=0, frame=1)
    pb.rotation_euler.x = math.radians(90)
    pb.keyframe_insert("rotation_euler", index=0, frame=11)
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.2, depth=2.0, location=(0, 0, 1))
    mesh = bpy.context.active_object
    mesh.name = "pCylinder1"
    bpy.context.view_layer.update()
    g1, g2 = mesh.vertex_groups.new(name="joint1"), mesh.vertex_groups.new(name="joint2")
    for v in mesh.data.vertices:
        (g2 if (mesh.matrix_world @ v.co).z > 1.0 else g1).add([v.index], 1.0, 'REPLACE')
    md = mesh.modifiers.new("skinCluster1", 'ARMATURE')
    md.object = arm
    bpy.context.scene.frame_set(6)
    shown = _points(mesh)
    _only(mesh)
    assert bpy.ops.allset.duplicate() == {'FINISHED'}
    copy = bpy.context.active_object
    assert not [m for m in copy.modifiers if not display.is_preview(m)], [m.name for m in copy.modifiers]
    assert _same(_points(copy), shown), "the copy is the pose at frame 6"
    bpy.context.scene.frame_set(11)
    assert not _same(_points(mesh), shown), "the original keeps following the skeleton"
    assert _same(_points(copy), shown), "the copy doesn't"
    # the skeleton itself: the copy holds the pose of the frame it was made at, without keys
    bpy.context.scene.frame_set(6)
    _only(arm)
    assert bpy.ops.allset.duplicate() == {'FINISHED'}
    arm2 = bpy.context.active_object
    assert arm2.type == 'ARMATURE' and arm2 is not arm and not _has_animation(arm2)
    assert abs(arm2.pose.bones["joint2"].rotation_euler.x - math.radians(45)) < 1e-4
    bpy.context.scene.frame_set(11)
    assert abs(arm2.pose.bones["joint2"].rotation_euler.x - math.radians(45)) < 1e-4


def _bone_world(arm, name):
    ev = arm.evaluated_get(bpy.context.evaluated_depsgraph_get())
    return ev.matrix_world @ ev.pose.bones[name].matrix


def _close_matrix(a, b, eps=1e-4):
    return all(abs(x - y) < eps for ra, rb in zip(a, b) for x, y in zip(ra, rb))


def test_kit_skin_and_ik_rig_copies_hold_still():
    """Bind Skin (the mesh follows its skeleton) on a chain bent by an IK constraint, the skeleton moved after the
    bind: the mesh copy is the shape shown now without skin or follow; the skeleton copy holds the IK pose in its own
    channels, without the constraint."""
    _fresh()
    skin = import_module(kit.MODULE + ".operators.skin")
    arm = bpy.data.objects.new("skeleton1", bpy.data.armatures.new("skeleton1"))
    bpy.context.collection.objects.link(arm)
    _only(arm)
    bpy.ops.object.mode_set(mode='EDIT')
    a = arm.data.edit_bones.new("joint1")
    a.head, a.tail = (0, 0, 0), (2, 0, 0)
    b = arm.data.edit_bones.new("joint2")
    b.head, b.tail, b.parent, b.use_connect = (2, 0, 0), (4, 0, 0), a, True
    bpy.ops.object.mode_set(mode='OBJECT')
    target = bpy.data.objects.new("ikHandle1", None)
    bpy.context.collection.objects.link(target)
    target.location = (3, 0, 1.5)
    con = arm.pose.bones["joint2"].constraints.new('IK')
    con.target, con.chain_count = target, 2
    bpy.ops.mesh.primitive_cube_add(size=1)
    mesh = bpy.context.active_object
    mesh.scale, mesh.location = (4, 0.5, 0.5), (2, 0, 0)
    bpy.ops.object.transform_apply(scale=True, location=False)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.subdivide(number_cuts=6)
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.update()
    skin.bind_skin(bpy.context, arm, [mesh])
    arm.location.y = 1.0                      # the skeleton moves after the bind: the mesh follows it
    target.location = (3, 1.0, 1.0)
    bpy.context.view_layer.update()
    shown = _points(mesh)
    _only(mesh)
    assert bpy.ops.allset.duplicate() == {'FINISHED'}
    copy = bpy.context.active_object
    assert not copy.modifiers and not copy.constraints, ([m.name for m in copy.modifiers], list(copy.constraints))
    assert _same(_points(copy), shown), "the copy is the skin's shape now"
    pose = _bone_world(arm, "joint2")
    _only(arm)
    assert bpy.ops.allset.duplicate() == {'FINISHED'}
    arm2 = bpy.context.active_object
    assert arm2.type == 'ARMATURE' and not any(pb.constraints for pb in arm2.pose.bones)
    assert _close_matrix(_bone_world(arm2, "joint2"), pose), "the copy holds the IK pose"
    arm.location.y = 2.0
    target.location = (2, 1.0, 2.0)
    bpy.context.view_layer.update()
    assert not _same(_points(mesh), shown), "the original skin follows its skeleton"
    assert _same(_points(copy), shown), "the mesh copy doesn't"
    assert _close_matrix(_bone_world(arm2, "joint2"), pose), "the skeleton copy doesn't follow the IK target"


def test_deformers_and_history_bake_display_stays():
    """A bend (Simple Deform) and the kit's smooth mesh preview: the copy has the bent shape, no bend, and keeps the
    preview (a display setting, not history)."""
    _fresh()
    assert bpy.ops.allset.create(kind='CUBE') == {'FINISHED'}
    ob = bpy.context.active_object
    bend = ob.modifiers.new("bend1", 'SIMPLE_DEFORM')
    bend.deform_method = 'BEND'
    bend.angle = math.radians(60)
    display.set_smooth_preview(ob, 3)
    bpy.context.view_layer.update()
    _only(ob)
    before = {m.name: m.show_viewport for m in ob.modifiers}
    for m in ob.modifiers:
        if display.is_preview(m):
            m.show_viewport = False
    flat = _points(ob)
    for m in ob.modifiers:
        m.show_viewport = before[m.name]
    assert bpy.ops.allset.duplicate() == {'FINISHED'}
    copy = bpy.context.active_object
    assert "bend1" not in copy.modifiers, [m.name for m in copy.modifiers]
    assert display.PREVIEW_MOD_NAME in copy.modifiers, "smooth preview stays on the copy"
    for m in copy.modifiers:
        m.show_viewport = False
    assert _same(_points(copy), flat), "the bend is in the copy's points"


def test_constrained_copy_stays_where_it_shows():
    _fresh()
    target = bpy.data.objects.new("locator1", None)
    bpy.context.collection.objects.link(target)
    target.location = (0.3, 0, 0)
    assert bpy.ops.allset.create(kind='CUBE') == {'FINISHED'}
    ob = bpy.context.active_object
    con = ob.constraints.new('COPY_LOCATION')
    con.target = target
    bpy.context.view_layer.update()
    _only(ob)
    assert bpy.ops.allset.duplicate() == {'FINISHED'}
    copy = bpy.context.active_object
    assert len(copy.constraints) == 0
    bpy.context.view_layer.update()
    assert (copy.matrix_world.translation - Vector((0.3, 0, 0))).length < 1e-6
    target.location.x = 0.7
    bpy.context.view_layer.update()
    assert abs(ob.matrix_world.translation.x - 0.7) < 1e-6
    assert abs(copy.matrix_world.translation.x - 0.3) < 1e-6, "the copy doesn't follow the constraint target"


def test_children_copied_plain_too():
    ob = _character()
    grp = bpy.data.objects.new("group1", None)
    bpy.context.collection.objects.link(grp)
    ob.parent = grp
    grp.location.z = 0.5
    grp.keyframe_insert("location", index=2, frame=1)
    bpy.context.scene.frame_set(6)
    shown = _points(ob)
    _only(grp)
    assert bpy.ops.allset.duplicate() == {'FINISHED'}
    g2 = bpy.context.active_object
    kids = list(g2.children)
    assert g2.name == "group2" and [k.name for k in kids] == ["pCube2"], (g2.name, [k.name for k in kids])
    assert not _has_animation(g2) and not _has_animation(kids[0]) and kids[0].data.shape_keys is None
    assert _same(_points(kids[0]), shown)


def test_curve_cluster_bakes_into_the_points():
    _fresh()
    cu = bpy.data.curves.new("curveShape1", 'CURVE')
    sp = cu.splines.new('POLY')
    sp.points.add(2)
    for i, p in enumerate(sp.points):
        p.co = (i * 0.1, 0, 0, 1)
    ob = bpy.data.objects.new("curve1", cu)
    bpy.context.collection.objects.link(ob)
    handle = bpy.data.objects.new("cluster1Handle", None)
    bpy.context.collection.objects.link(handle)
    hook = ob.modifiers.new("cluster1", 'HOOK')
    hook.object = handle
    hook.vertex_indices_set([2])
    handle.location.z = 0.2
    bpy.context.view_layer.update()
    _only(ob)
    assert bpy.ops.allset.duplicate() == {'FINISHED'}
    copy = bpy.context.active_object
    assert copy.type == 'CURVE' and len(copy.modifiers) == 0, [m.name for m in copy.modifiers]
    assert abs(copy.data.splines[0].points[2].co.z - 0.2) < 1e-6, tuple(copy.data.splines[0].points[2].co)
    handle.location.z = 0.5
    bpy.context.view_layer.update()
    assert abs(copy.data.splines[0].points[2].co.z - 0.2) < 1e-6


# --- the other plain paths -----------------------------------------------------------------------------------

def _plain_check(ob, copy):
    assert copy is not ob and copy.data is not ob.data
    assert not _has_animation(copy) and copy.data.shape_keys is None, copy.name
    assert abs(copy.location.x - 0.05) < 1e-6, (copy.name, copy.location.x)


def test_shift_d_smart_duplicate_and_cmds_make_plain_copies():
    ob = _character()
    assert bpy.ops.allset.duplicate_with_transform() == {'FINISHED'}
    _plain_check(ob, bpy.context.active_object)
    _only(ob)
    manip.start_duplicate(bpy.context)
    _plain_check(ob, bpy.context.active_object)
    names = cmds.duplicate(ob.name)
    copy = bpy.data.objects[names[0]]
    _plain_check(ob, copy)
    assert prim_history.owner_of(copy) is None


# --- Duplicate Special: input graph / input connections / instance ----------------------------------------------

def test_input_graph_copy_animates_on_its_own():
    ob = _character()
    assert bpy.ops.allset.duplicate_special(input_graph=True) == {'FINISHED'}
    copy = bpy.context.active_object
    assert copy.data.shape_keys is not None and copy.data.shape_keys is not ob.data.shape_keys
    assert _actions(copy) and not (_actions(copy) & _actions(ob)), "its own object animation"
    assert _actions(copy.data.shape_keys) and not (_actions(copy.data.shape_keys) & _actions(ob.data.shape_keys))
    assert _fc(copy, "scale", 2) is None and copy.animation_data.drivers.find("scale", index=2) is not None
    node = prim_history.node_dict(prim_history.owner_of(copy))
    assert node is not None and node["name"] == "polyCube2", node and node["name"]
    _set_last_key(ob, "location", 0.3)
    _set_last_key(ob.data.shape_keys, SMILE, 0.25)
    bpy.context.scene.frame_set(11)
    assert abs(copy.location.x - 0.1) < 1e-6, f"the copy keeps the old keys ({copy.location.x})"
    assert abs(copy.data.shape_keys.key_blocks["smile"].value - 1.0) < 1e-6
    assert abs(ob.location.x - 0.3) < 1e-6


def test_input_connections_copy_shares_the_animation():
    ob = _character()
    assert bpy.ops.allset.duplicate_special(input_connections=True) == {'FINISHED'}
    copy = bpy.context.active_object
    assert _actions(copy) == _actions(ob), "the same animation drives both"
    assert _actions(copy.data.shape_keys) == _actions(ob.data.shape_keys)
    _set_last_key(ob, "location", 0.3)
    bpy.context.scene.frame_set(11)
    assert abs(copy.location.x - 0.3) < 1e-6, copy.location.x


def test_instance_stays_an_instance():
    ob = _character()
    assert bpy.ops.allset.duplicate_special(geometry_type='INSTANCE') == {'FINISHED'}
    copy = bpy.context.active_object
    assert copy.data is ob.data


def test_option_window_fields_and_greying():
    w = ow._BY_KEY["duplicate_special_maya"]
    names = [f.name for f in w.fields]
    assert names[-2:] == ["input_graph", "input_connections"], names
    assert not any("input" in m for m in w.missing), w.missing
    vals = w.defaults()
    assert vals["input_graph"] is False and vals["input_connections"] is False
    assert w.enabled(vals, "translate") and w.enabled(vals, "input_graph") and w.enabled(vals, "input_connections")
    on = dict(vals, input_graph=True)
    assert not w.enabled(on, "translate") and not w.enabled(on, "smart") and not w.enabled(on, "input_connections")
    inst = dict(vals, geometry_type="Instance")
    assert not w.enabled(inst, "input_graph") and not w.enabled(inst, "input_connections")
    assert w.enabled(dict(inst, input_graph=True), "translate"), "an instance ignores the input options"


def test_option_window_runs_input_graph_without_offsets():
    ob = _character()
    res = ow.run(ow._BY_KEY["duplicate_special_maya"], bpy.context,
                 {"input_graph": True, "translate": (5.0, 0.0, 0.0), "copies": 2})
    assert not isinstance(res, str), res
    copies = [o for o in bpy.context.selected_objects if o is not ob]
    assert len(copies) == 2, [o.name for o in copies]
    for c in copies:
        assert _actions(c) and not (_actions(c) & _actions(ob))
        assert abs(c.location.x - ob.location.x) < 1e-6, "offsets apply to plain copies only, like Maya"
    # the next plain run is plain again (the operator's last input option doesn't carry over), with its offset
    _only(ob)
    res = ow.run(ow._BY_KEY["duplicate_special_maya"], bpy.context, {"translate": (5.0, 0.0, 0.0)})
    assert not isinstance(res, str), res
    plain = bpy.context.active_object
    assert plain is not ob and not _has_animation(plain) and plain.data.shape_keys is None
    assert plain.location.x > ob.location.x + 1e-4, (plain.location.x, ob.location.x)
    # an instance ignores the input options
    _only(ob)
    res = ow.run(ow._BY_KEY["duplicate_special_maya"], bpy.context,
                 {"geometry_type": "Instance", "input_graph": True})
    assert not isinstance(res, str), res
    assert bpy.context.active_object.data is ob.data


def test_cmds_duplicate_flags():
    ob = _character()
    graph = bpy.data.objects[cmds.duplicate(ob.name, upstreamNodes=True)[0]]
    assert _actions(graph) and not (_actions(graph) & _actions(ob)) and graph.data.shape_keys is not None
    conn = bpy.data.objects[cmds.duplicate(ob.name, ic=True)[0]]
    assert _actions(conn) == _actions(ob)
