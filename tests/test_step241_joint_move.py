"""Step 241 (Issue #156, report @cnzim): joints move after placement.

Maya 2026 (research/maya/re/joint_move_241.md, mayapy C:/Repos/bmk-strategy/maya2026_re/scripts/joint_move_241.py):
chain (0,0,0) (0,10,0) (0,20,0); W on joint2 by +3 X -> joint2 (3,10,0), joint3 follows to (3,20,0), joint1 stays;
undo restores. After Bind Skin a joint move poses (the mesh moves 3); Skin > Move Skinned Joints moves the joint with
the mesh unchanged (0.0) and the weights the same, and posing afterwards bends about the new place.
Kit: unskinned skeleton = Edit mode (picked joint + subtree), skinned = Pose, Move Skinned Joints = Edit and back.
"""

import math
from importlib import import_module

import bpy
from mathutils import Vector

import kit

joints = import_module(kit.MODULE + ".operators.joints")
js = import_module(kit.MODULE + ".operators.joint_selection")
skin = import_module(kit.MODULE + ".operators.skin")
units = import_module(kit.MODULE + ".operators.units")
cb = import_module(kit.MODULE + ".ui.channel_box")
pivot_mod = import_module(kit.MODULE + ".operators.pivot")

MAYA = {"before": {"joint1": (0, 0, 0), "joint2": (0, 10, 0), "joint3": (0, 20, 0)},
        "after": {"joint1": (0, 0, 0), "joint2": (3, 10, 0), "joint3": (3, 20, 0)}}


def _bl(p, k):
    return Vector((p[0], -p[2], p[1])) * k


def _maya(v, k):
    v = v / k
    return Vector((v.x, v.z, -v.y))


def _scene(skinned=False):
    if bpy.context.object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for a in list(bpy.data.armatures):
        bpy.data.armatures.remove(a)
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)
    sc = bpy.context.scene
    sc.unit_settings.system, sc.unit_settings.length_unit = 'METRIC', 'CENTIMETERS'
    k = units.maya_unit(sc)
    ob = joints.new_skeleton(bpy.context)
    parent = None
    for p in MAYA["before"].values():
        parent = joints.add_joint(ob, _bl(p, k), parent, up=Vector((0, 0, 1)), length=2 * k)
    joints.orient_new(ob, ["joint1", "joint2", "joint3"])
    joints.finish(bpy.context, ob, ["joint1", "joint2", "joint3"])
    bpy.ops.object.mode_set(mode='OBJECT')
    mesh = None
    if skinned:
        bpy.ops.mesh.primitive_cylinder_add(radius=1 * k, depth=20 * k, location=_bl((0, 10, 0), k), vertices=12)
        mesh = bpy.context.active_object
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.subdivide(number_cuts=9)
        bpy.ops.object.mode_set(mode='OBJECT')
        skin.bind_skin(bpy.context, ob, [mesh])
    for o in bpy.context.selected_objects:
        o.select_set(False)
    bpy.context.view_layer.update()
    return ob, mesh, k


class _MoveTool:
    """The Move tool on (background Blender has no tool keymaps: js.move_tool_active is replaced while inside)."""
    def __enter__(self):
        self._orig = js.move_tool_active
        js.move_tool_active = lambda context: True

    def __exit__(self, *a):
        js.move_tool_active = self._orig


def _heads(ob, k):
    if ob.mode == 'EDIT':
        return {eb.name: _maya(ob.matrix_world @ eb.head, k) for eb in ob.data.edit_bones}
    return {b.name: _maya(ob.matrix_world @ b.head_local, k) for b in ob.data.bones}


def _close(got, want, tol=1e-4):
    for name, p in want.items():
        assert (got[name] - Vector(p)).length < tol, (name, tuple(got[name]), p)


def _verts(mesh):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = mesh.evaluated_get(dg)
    return [ev.matrix_world @ v.co for v in ev.data.vertices]


def test_unskinned_pick_is_pose_without_the_move_tool():
    """Decision 16 stays for every other tool: Channel Box channels, S keys and pick walk are Pose-mode features."""
    ob, _m, k = _scene()
    assert js.select(bpy.context, ob, "joint2")
    assert ob.mode == 'POSE' and cb.bone_selected(ob.pose.bones["joint2"])


def test_move_tool_switches_picked_joints_to_edit_and_back():
    ob, _m, k = _scene()
    js.select(bpy.context, ob, "joint2")
    with _MoveTool():
        assert js.sync_tool_mode(bpy.context) == 'EDIT'
    assert ob.mode == 'EDIT' and ob.get(js.AUTO_EDIT)
    sel = {eb.name for eb in ob.data.edit_bones if eb.select and eb.select_head and eb.select_tail}
    assert sel == {"joint2", "joint3"}, sel
    assert js.sync_tool_mode(bpy.context) == 'POSE'          # E / R / Q: back to Pose, the same joint picked
    assert ob.mode == 'POSE' and not ob.get(js.AUTO_EDIT)
    assert [pb.name for pb in ob.pose.bones if cb.bone_selected(pb)] == ["joint2"]
    assert ob.data.bones.active.name == "joint2"


def test_f8_keeps_pose_while_the_move_tool_stays():
    ob, _m, k = _scene()
    with _MoveTool():
        js.select(bpy.context, ob, "joint2")
        assert ob.mode == 'EDIT'
        bpy.ops.allset.toggle_sel_mode()
        assert ob.mode == 'POSE'
        assert js.sync_tool_mode(bpy.context) is None and ob.mode == 'POSE'
    js.sync_tool_mode(bpy.context)
    assert not ob.get(js.POSE_PIN)


def test_unskinned_pick_with_the_move_tool_enters_edit_with_the_subtree():
    ob, _m, k = _scene()
    assert js.joint_mode(ob) == 'EDIT'
    with _MoveTool():
        assert js.select(bpy.context, ob, "joint2")
    assert ob.mode == 'EDIT'
    sel = {eb.name for eb in ob.data.edit_bones if eb.select and eb.select_head and eb.select_tail}
    assert sel == {"joint2", "joint3"}, sel
    assert ob.data.edit_bones.active.name == "joint2"


def test_w_moves_the_joint_and_children_like_maya_then_undo():
    ob, _m, k = _scene()
    with _MoveTool():
        js.select(bpy.context, ob, "joint2")
    bpy.ops.ed.undo_push(message="picked")
    assert bpy.ops.transform.translate('EXEC_DEFAULT', True, value=(3 * k, 0, 0)) == {'FINISHED'}
    _close(_heads(ob, k), MAYA["after"])
    # joint1 stays where it was; its bone now reaches the moved joint (Blender bones point at their child)
    assert (_maya(ob.matrix_world @ ob.data.edit_bones["joint1"].tail, k) - Vector(MAYA["after"]["joint2"])).length < 1e-4
    bpy.ops.object.mode_set(mode='OBJECT')
    _close(_heads(ob, k), MAYA["after"])                    # the move is the rest = Maya's translate
    bpy.ops.ed.undo()
    bpy.ops.ed.undo()
    ob = bpy.data.objects[ob.name]
    if ob.mode == 'EDIT':
        bpy.ops.object.mode_set(mode='OBJECT')
    _close(_heads(ob, k), MAYA["before"])


def test_e_turns_the_subtree_about_the_joint():
    """E / R pivot = the lead joint: Edit Armature pivot = cursor, kept on the picked joint (a background transform
    ignores the pivot setting, so the turn itself uses that point as its centre; GUI: gui_step241_joint_move)."""
    ob, _m, k = _scene()
    with _MoveTool():
        js.select(bpy.context, ob, "joint2")
    assert bpy.context.scene.tool_settings.transform_pivot_point == 'CURSOR'
    cursor = bpy.context.scene.cursor.location.copy()
    assert (_maya(cursor, k) - Vector((0, 10, 0))).length < 1e-4, tuple(cursor)
    bpy.ops.transform.rotate(value=math.radians(30), orient_axis='Y', orient_type='GLOBAL', center_override=cursor)
    h = _heads(ob, k)
    assert (h["joint2"] - Vector((0, 10, 0))).length < 1e-4, tuple(h["joint2"])
    assert abs((h["joint3"] - h["joint2"]).length - 10) < 1e-4
    assert abs(abs(h["joint3"].x) - 5) < 1e-3 and abs(h["joint3"].y - 18.6603) < 1e-3, tuple(h["joint3"])
    # the cursor follows the lead joint after a move (tool_keys watch)
    bpy.ops.transform.translate(value=(3 * k, 0, 0))
    js.sync_joint_pivot(bpy.context)
    assert (_maya(bpy.context.scene.cursor.location, k) - h["joint2"] - Vector((3, 0, 0))).length < 1e-4


def test_skinned_pick_poses():
    ob, mesh, k = _scene(skinned=True)
    assert js.is_skinned(ob) and js.joint_mode(ob) == 'POSE'
    js.select(bpy.context, ob, "joint2")
    assert ob.mode == 'POSE' and cb.bone_selected(ob.pose.bones["joint2"])


def test_move_skinned_joints_keeps_the_mesh_and_rebinds():
    ob, mesh, k = _scene(skinned=True)
    js.select(bpy.context, ob, "joint2")
    v0 = _verts(mesh)
    w0 = [[(g.group, round(g.weight, 6)) for g in v.groups] for v in mesh.data.vertices]
    assert bpy.ops.allset.move_skinned_joints() == {'FINISHED'}
    assert ob.mode == 'EDIT' and ob.get(js.MOVE_SKINNED)
    assert js.joint_mode(ob) == 'EDIT'
    sel = {eb.name for eb in ob.data.edit_bones if eb.select}
    assert sel == {"joint2", "joint3"}, sel
    bpy.ops.transform.translate(value=(3 * k, 0, 0))
    assert max((a - b).length for a, b in zip(v0, _verts(mesh))) < 1e-5 * k      # Maya: mesh move during 0.0
    assert bpy.ops.allset.move_skinned_joints() == {'FINISHED'}
    assert ob.mode == 'POSE' and not ob.get(js.MOVE_SKINNED)
    _close(_heads(ob, k), MAYA["after"])
    assert max((a - b).length for a, b in zip(v0, _verts(mesh))) < 1e-5 * k      # Maya: mesh move after 0.0
    w1 = [[(g.group, round(g.weight, 6)) for g in v.groups] for v in mesh.data.vertices]
    assert w0 == w1                                                                  # Maya: weights the same
    # posing bends about the new place (the new rest is the bind)
    pb = ob.pose.bones["joint1"]
    pb.rotation_mode = 'XYZ'
    pb.rotation_euler = (0, 0, math.radians(30))
    bpy.context.view_layer.update()
    assert max((a - b).length for a, b in zip(v0, _verts(mesh))) > 1 * k


def test_f8_ends_move_skinned_joints():
    ob, mesh, k = _scene(skinned=True)
    js.select(bpy.context, ob, "joint2")
    bpy.ops.allset.move_skinned_joints()
    assert ob.mode == 'EDIT'
    bpy.ops.allset.toggle_sel_mode()
    assert ob.mode == 'POSE' and not ob.get(js.MOVE_SKINNED) and js.joint_mode(ob) == 'POSE'


def test_menu_item_is_mapped():
    menu_map = import_module(kit.MODULE + ".ui.menu_map")
    assert menu_map.MAP["Skin/Move Skinned Joints"] == "allset.move_skinned_joints"


def test_joint_pivot_is_given_back_after_edit_mode():
    """The cursor pivot is only for joints in Edit mode: Object mode gets its Maya pivot back, a user's own cursor
    pivot is left alone."""
    ob, _m, k = _scene()
    ts = bpy.context.scene.tool_settings
    ts.transform_pivot_point = 'ACTIVE_ELEMENT'
    with _MoveTool():
        js.select(bpy.context, ob, "joint2")
    assert ts.transform_pivot_point == 'CURSOR'
    bpy.ops.object.mode_set(mode='OBJECT')
    assert js.restore_joint_pivot(bpy.context) and ts.transform_pivot_point == 'ACTIVE_ELEMENT'
    ts.transform_pivot_point = 'CURSOR'                     # the user's own choice
    assert not js.restore_joint_pivot(bpy.context) and ts.transform_pivot_point == 'CURSOR'
    ts.transform_pivot_point = 'ACTIVE_ELEMENT'
