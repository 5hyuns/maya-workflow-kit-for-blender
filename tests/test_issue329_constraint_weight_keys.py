"""Issue #329: a constraint's target weight (pCube1W0 under the constraint node in the Channel Box INPUTS) is a
channel like Translate X — it can be selected, keyed with Channels > Key Selected (and Breakdown / Delete Selected),
shows its keyed / animated state, takes typed values and a value drag from 0 up, on every selected node with the
same constraint, like Maya. The weight is a value of its own on the object (or the joint) whose curve sits on the
object (or the armature for a joint), where the Graph Editor shows it; the constraint's influence follows it (any
weight above 0 = on the target, like Maya)."""

from importlib import import_module

import bpy

import kit

cb = import_module(kit.MODULE + ".ui.channel_box")
compat = import_module(kit.MODULE + ".compat")
multi = import_module(kit.MODULE + ".operators.constrain_multi")


def _fresh():
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    cb.reset_open()
    cb.set_selected_channels([])
    bpy.context.scene.frame_set(1)


def _cube(name, x=0.0):
    bpy.ops.mesh.primitive_cube_add(location=(x, 0.0, 0.0))
    ob = bpy.context.active_object
    ob.name = name
    return ob


def _scene():
    """pCube1 parent-constrains pCube2 and pCube3 (both selected, pCube2 the lead), the node opened."""
    _fresh()
    parent = _cube("pCube1")
    a, b = _cube("pCube2", 3.0), _cube("pCube3", 6.0)
    for ob in (a, b):
        con = ob.constraints.new('CHILD_OF')
        con.target = parent
    parent.select_set(False)
    for ob in (a, b):
        ob.select_set(True)
    bpy.context.view_layer.objects.active = a
    cb.set_open(a, cb.con_node(a, a.constraints[0]))     # INPUTS nodes start collapsed
    cb.rebuild_rows()
    return a, b


def _row():
    return next(r for r in bpy.context.scene.allset_cb.rows if r.kind == "CONSTRAINT")


def test_weight_rows_are_channels():
    a, b = _scene()
    row = _row()
    assert row.name == "influence" and row.mod_type == 'CHILD_OF', (row.name, row.mod_type)
    key = cb.row_key(row)
    assert key is not None and cb.is_input_key(key) and cb.is_constraint_key(key), key
    assert cb.has_channel(a, key) and cb.has_channel(b, key)
    assert not cb.has_channel(bpy.data.objects["pCube1"], key)
    assert cb.channel_label(key) == "pCube1W0"
    assert abs(cb.get_value(a, key) - 1.0) < 1e-6
    assert key in cb.drawn_keys(a)
    assert cb.is_keyable(a, key)
    # selecting the row selects the channel; its cells are Channel Box cells (the RMB menu finds the channel)
    row.sel = True
    assert cb.selected_channels() == [key] and row.sel
    i = list(bpy.context.scene.allset_cb.rows).index(row)
    assert cb.cell_key(f"allset_cb.rows[{i}].sel", bpy.context.scene) == (key, "NAME")
    assert cb.cell_key(f"allset_cb.rows[{i}].text", bpy.context.scene) == (key, "VALUE")
    assert cb.field_owner(bpy.context, key) == (row, "text")
    cb.set_selected_channels([])


def test_key_selected_keys_the_weight_on_every_selected_object():
    a, b = _scene()
    key = cb.row_key(_row())
    cb.set_selected_channels([key])
    assert cb.channel_state(a, key) is None
    cb.set_value(a, key, 0.25)
    cb.set_value(b, key, 0.75)
    assert bpy.ops.allset.cb_key_selected() == {'FINISHED'}
    for ob, v in ((a, 0.25), (b, 0.75)):
        fc = cb.fcurve(ob, key)
        prop = cb.constraint_weight(ob, key)
        assert prop is not None and fc is not None and fc.data_path == multi.weight_path(ob, prop), fc
        assert fc in list(compat.id_fcurves(ob)), "on the constrained object"
        assert len(fc.keyframe_points) == 1 and abs(fc.keyframe_points[0].co.y - v) < 1e-6
        assert cb.channel_state(ob, key) == 'KEYED'
        assert cb.fcurve(ob, "tx") is None, "Translate stays unkeyed"
    bpy.context.scene.frame_set(10)
    assert cb.channel_state(a, key) == 'ANIMATED'
    cb.set_value(a, key, 1.0)
    assert bpy.ops.allset.cb_key_selected() == {'FINISHED'}
    assert len(cb.fcurve(a, key).keyframe_points) == 2 and cb.channel_state(a, key) == 'KEYED'
    bpy.context.scene.frame_set(20)
    assert bpy.ops.allset.cb_breakdown_selected() == {'FINISHED'}
    assert cb.fcurve(a, key).keyframe_points[-1].type == 'BREAKDOWN'
    # Channels > Delete Selected removes the weight's curve and nothing else
    a.keyframe_insert("location", index=0)
    assert bpy.ops.allset.cb_delete_keys() == {'FINISHED'}
    for ob in (a, b):
        assert cb.fcurve(ob, key) is None and cb.channel_state(ob, key) is None
    assert cb.fcurve(a, "tx") is not None
    cb.set_selected_channels([])


def test_joint_constraint_weight_keys_on_the_armature():
    _fresh()
    target = _cube("locator1")
    bpy.ops.object.armature_add(location=(3.0, 0.0, 0.0))
    arm = bpy.context.active_object
    arm.name = "joint1"
    pb = arm.pose.bones[0]
    con = pb.constraints.new('COPY_LOCATION')
    con.target = target
    con.influence = 0.5
    target.select_set(False)
    bpy.ops.object.mode_set(mode='POSE')
    cb.set_bone_selected(pb, True)
    arm.data.bones.active = arm.data.bones[0]
    cb.set_open(pb, cb.con_node(pb, con))
    cb.rebuild_rows()
    key = cb.row_key(_row())
    assert cb.channel_label(key) == "locator1W0"
    assert cb.has_channel(pb, key) and not cb.has_channel(arm, key)
    cb.set_selected_channels([key])
    assert bpy.ops.allset.cb_key_selected() == {'FINISHED'}
    fc = cb.fcurve(pb, key)
    prop = cb.constraint_weight(pb, key)
    assert prop is not None and prop in pb.keys(), "the joint's own weight"
    assert fc is not None and fc.data_path == pb.path_from_id(f'["{prop}"]'), fc
    assert fc in list(compat.id_fcurves(arm)), "the armature object's animation"
    assert abs(fc.keyframe_points[0].co.y - 0.5) < 1e-6 and cb.channel_state(pb, key) == 'KEYED'
    assert cb.driver(pb, key) is None
    assert bpy.ops.allset.cb_delete_keys() == {'FINISHED'}
    assert cb.fcurve(pb, key) is None
    cb.set_selected_channels([])
    bpy.ops.object.mode_set(mode='OBJECT')


def test_typed_and_dragged_weights_stay_in_range_on_every_selected_object():
    a, b = _scene()
    row = _row()
    key = cb.row_key(row)
    row.text = "0.3"
    assert abs(cb.get_value(a, key) - 0.3) < 1e-6 and abs(cb.get_value(b, key) - 0.3) < 1e-6
    bpy.context.view_layer.update()
    for ob in (a, b):       # one target: any weight above 0 keeps the object fully on it (Maya)
        assert abs(ob.constraints[0].influence - 1.0) < 1e-6, ob.constraints[0].influence
    # a Maya weight goes from 0 up (2 = still fully on the one target)
    assert abs(cb.drag_limit(a, key, 1.7) - 1.7) < 1e-6 and abs(cb.drag_limit(a, key, -0.2)) < 1e-6
    assert cb.entry_kind(a, key) in ("FLOAT", "NONE"), cb.entry_kind(a, key)
    cb.set_value(b, key, 0.9)
    assert abs(cb.get_value(b, key) - 0.9) < 1e-6 and abs(cb.get_value(a, key) - 0.3) < 1e-6
    row.text = "0"
    bpy.context.view_layer.update()
    for ob in (a, b):       # 0 = the object's own channels
        assert cb.get_value(ob, key) == 0.0 and ob.constraints[0].influence < 1e-6
