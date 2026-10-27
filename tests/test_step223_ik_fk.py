"""Step 223 (Issue #133, ATTACH_PLAN L14): Maya IK / FK switching on kit IK handles — Ik Blend on the handle drives
the IK constraint's Influence (Channel Box "Ik Blend"), poses at Ik Blend 1 / 0 equal Maya's, Set IK/FK Key / Enable
IK Solver / Move IK to FK follow Maya 2026. Maya truth: tests/maya223_rig_data.py IK (mayapy, RP arm shoulder (0,0,0)
-> elbow (4,0,-1) -> wrist (8,0,0), handle moved to (6,0,2)); research/scripts/maya_rig223/make.py / solver.py."""

import math
from importlib import import_module

import bpy
from mathutils import Matrix, Vector

import kit
import maya223_rig_data as truth

compat = import_module(kit.MODULE + ".compat")
skin = import_module(kit.MODULE + ".operators.skin")
ik_fk = import_module(kit.MODULE + ".operators.ik_fk")
channel_box = import_module(kit.MODULE + ".ui.channel_box")
menu_map = import_module(kit.MODULE + ".ui.menu_map")

PTS = {"shoulder": (0, 0, 0), "elbow": (4, 0, -1), "wrist": (8, 0, 0)}
JO_Z = (math.sin(math.radians(14.036243467926484)), 0.0, math.cos(math.radians(14.036243467926484)))


def bl(p):
    return Vector((p[0], -p[2], p[1]))        # Maya (x, y, z) -> Blender (x, -z, y), 1 Maya unit = 1 m here


def _arm():
    if bpy.context.object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for a in list(bpy.data.actions):
        bpy.data.actions.remove(a)
    sc = bpy.context.scene
    sc.frame_set(1)
    arm = bpy.data.objects.new("skeleton1", bpy.data.armatures.new("skeleton1"))
    sc.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    prev = None
    for name, tail in (("shoulder", PTS["elbow"]), ("elbow", PTS["wrist"]), ("wrist", (9, 0, 0))):
        eb = arm.data.edit_bones.new(name)
        eb.head, eb.tail = bl(PTS[name]), bl(tail)
        if prev is not None:
            eb.parent, eb.use_connect = prev, True
        prev = eb
    bpy.ops.object.mode_set(mode='OBJECT')
    for pb in arm.pose.bones:
        pb.rotation_mode = 'XYZ'
    handle = skin.create_ik(bpy.context, arm, ("shoulder", 'HEAD'), ("wrist", 'HEAD'))
    con = arm.pose.bones["elbow"].constraints[0]
    return arm, handle, con


def _update():
    bpy.context.view_layer.update()


def _world(arm, name):
    return arm.matrix_world @ arm.pose.bones[name].head


def _check(arm, state, tol=2e-3):
    for name in ("elbow", "wrist"):
        got, want = _world(arm, name), bl(truth.IK[state][name]["world"])
        assert (got - want).length < tol, (state, name, got, want)


def _rotate_shoulder(arm, deg):
    """Maya shoulder.rotateZ += deg: about the shoulder's joint Z (jointOrient (0, 14.04, 0)) in world."""
    pb = arm.pose.bones["shoulder"]
    rot = Matrix.Rotation(math.radians(deg), 4, bl(JO_Z).normalized())
    pb.matrix = rot @ pb.matrix
    _update()


def _select(*obs):
    for ob in bpy.context.selected_objects:
        ob.select_set(False)
    for ob in obs:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = obs[-1] if obs else None


def test_ik_blend_on_the_handle_like_maya():
    arm, handle, con = _arm()
    assert handle["ikBlend"] == truth.IK["handle_default"]["ikBlend"] == 1.0
    assert "ikBlend" in channel_box.custom_keys(handle)
    assert channel_box.nice_name("ikBlend") == truth.IK["cb_labels"][-1] == "Ik Blend"
    handle["ikBlend"] = 0.0
    handle.update_tag()
    _update()
    assert con.influence == 0.0                       # Ik Blend drives the IK constraint
    # Maya adds ikBlend on the chain joints, connected from the handle (shoulder, elbow; not the end joint)
    for name, attrs in truth.IK["joint_attrs"].items():
        assert ("ikBlend" in arm.pose.bones[name].keys()) == ("ikBlend" in attrs), name
    assert arm.pose.bones["shoulder"]["ikBlend"] == 0.0


def test_pose_at_blend_1_and_0_equals_maya():
    arm, handle, con = _arm()
    handle.location = bl((6, 0, 2))
    _update()
    _check(arm, "blend1")
    _select(handle)
    assert bpy.ops.allset.ik_fk_key() == {'FINISHED'}      # FK channels = the solved pose (Maya rotate under IK)
    ik_fk.set_blend(arm, arm.pose.bones["elbow"], con, 0.0)
    _update()
    _check(arm, "blend1")                              # Ik Blend 0 keeps the pose (Maya move_ik_to_fk.joints)
    _rotate_shoulder(arm, 30.0)
    _check(arm, "blend0")                              # Maya: ikBlend 0 + shoulder.rz 30


def test_set_ik_fk_key_channels_and_tangents():
    arm, handle, con = _arm()
    handle.location = bl((6, 0, 2))
    _update()
    _select(handle)
    assert bpy.ops.allset.ik_fk_key() == {'FINISHED'}
    paths = {(fc.data_path, fc.array_index) for fc in compat.id_fcurves(handle)}
    want = {("location", i) for i in range(3)} | {("rotation_euler", i) for i in range(3)} \
        | {("scale", i) for i in range(3)} | {("hide_viewport", 0), ('["ikBlend"]', 0)}
    assert paths == want, paths
    bones = {(fc.data_path, fc.array_index) for fc in compat.id_fcurves(arm)}
    want_b = {(f'pose.bones["{b}"].rotation_euler', i) for b in ("shoulder", "elbow") for i in range(3)} \
        | {('pose.bones["shoulder"].location', i) for i in range(3)}
    assert want_b <= bones, bones
    # Maya keys every chain joint's rotate, the handle channels, ikBlend: 32 curves minus Pole Vector X / Y / Z,
    # Offset, Roll, Twist (no Blender channel) and preferredAngle (only kept when set) = 15 + 6
    maya = {c for c in truth.IK["set_key_f1"] if "poleVector" not in c and not c.endswith(("offset", "roll", "twist"))
            and "preferredAngle" not in c}
    assert len(maya) == len(paths) + len(want_b), (len(maya), len(paths), len(want_b))
    # frame 10: Ik Blend 0 + FK rotate, key again; frame 5 = Maya's in auto / out clamped curve
    sc = bpy.context.scene
    sc.frame_set(10)
    ik_fk.set_blend(arm, arm.pose.bones["elbow"], con, 0.0)
    _update()
    _rotate_shoulder(arm, 30.0)
    assert bpy.ops.allset.ik_fk_key() == {'FINISHED'}
    fc = next(c for c in compat.id_fcurves(handle) if c.data_path == '["ikBlend"]')
    assert [round(k.co.y, 6) for k in fc.keyframe_points] == [1.0, 0.0]
    assert abs(fc.evaluate(5) - truth.IK["frames_after_keys"]["5"]["ikBlend"]) < 1e-4, fc.evaluate(5)
    vis = next(c for c in compat.id_fcurves(handle) if c.data_path == "hide_viewport")
    assert all(k.interpolation == 'CONSTANT' for k in vis.keyframe_points)       # Maya visibility out step
    for f in (1, 10):
        sc.frame_set(f)
        _check(arm, "blend1" if f == 1 else "blend0")


def test_enable_ik_solver_like_maya():
    arm, handle, con = _arm()
    handle.location = bl((6, 0, 2))
    _update()
    ik_fk._STATE["on"] = False                     # Maya factory: ikFKSwitchState 0
    _select(handle)
    assert bpy.ops.allset.ik_solver_toggle() == {'FINISHED'}
    assert handle["ikBlend"] == 1.0                # first use: on
    assert bpy.ops.allset.ik_solver_toggle() == {'FINISHED'}
    _update()
    assert handle["ikBlend"] == 0.0 and con.influence == 0.0
    _check(arm, "blend1")                          # the IK pose stays (Maya solver.json second: wrist (6, 0, 2))
    # a selected joint finds its handle
    _select(arm)
    bpy.ops.object.mode_set(mode='POSE')
    for pb in arm.pose.bones:
        channel_box.set_bone_selected(pb, pb.name == "shoulder")
    assert bpy.ops.allset.ik_solver_toggle() == {'FINISHED'}
    assert handle["ikBlend"] == 1.0
    bpy.ops.object.mode_set(mode='OBJECT')
    _select()
    try:
        bpy.ops.allset.ik_solver_toggle()
        raise AssertionError("no error with nothing selected")
    except RuntimeError as ex:
        assert ik_fk.NO_HANDLE in str(ex)


def test_move_ik_to_fk_like_maya():
    # spec case: Ik Blend 0 from the rest pose, shoulder.rz 30 -> handle at the FK wrist (6.99, 3.88, 0.25)
    arm, handle, con = _arm()
    ik_fk.set_blend(arm, arm.pose.bones["elbow"], con, 0.0)
    _update()
    _rotate_shoulder(arm, 30.0)
    _select(handle)
    assert bpy.ops.allset.move_ik_to_fk() == {'FINISHED'}
    _update()
    got = handle.matrix_world.translation
    assert (got - _world(arm, "wrist")).length < 1e-5
    assert (got - bl((6.99, 3.88, 0.25))).length < 1e-2, got
    assert handle["ikBlend"] == 0.0
    # mayapy case: handle (6, 0, 2) solved, switched to FK keeping the pose, Move IK to FK -> handle (6, 0, 2)
    arm, handle, con = _arm()
    handle.location = bl((6, 0, 2))
    _update()
    ik_fk._STATE["on"] = True
    _select(handle)
    bpy.ops.allset.ik_solver_toggle()               # -> FK, pose kept
    handle.location = bl((7, 1, 1))                 # the handle drifts away while FK
    _update()
    assert bpy.ops.allset.move_ik_to_fk() == {'FINISHED'}
    _update()
    assert (handle.matrix_world.translation - bl(truth.IK["move_ik_to_fk"]["handle"])).length < 2e-3


def test_menu_items_mapped():
    for label, op in (("Set IK/FK Key", "allset.ik_fk_key"), ("Move IK to FK", "allset.move_ik_to_fk")):
        assert menu_map.MAP[f"Key/IK/FK Keys/{label}"] == op
    # step 238: a Maya check item drawn as the WindowManager property that runs allset.ik_solver_toggle
    assert menu_map.MAP["Key/IK/FK Keys/Enable IK Solver"] == ("prop", "window_manager.allset_ik_solver", {})


def test_undo_restores_blend():
    arm, handle, con = _arm()
    bpy.ops.ed.undo_push(message="before")
    _select(handle)
    ik_fk._STATE["on"] = True
    bpy.ops.allset.ik_solver_toggle('EXEC_DEFAULT', True)
    assert bpy.data.objects[handle.name]["ikBlend"] == 0.0
    bpy.ops.ed.undo()
    assert bpy.data.objects["ikHandle1"]["ikBlend"] == 1.0
