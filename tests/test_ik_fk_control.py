"""Maya IK / FK switching, part 2: Skeleton > Enable IK/FK Control and Enable IK Handle Snap, the joints' solved
rotation (Ik Blend 1 -> 0 keeps the IK pose) and Key > IK/FK Keys > Connect to IK/FK (RP arm shoulder (0,0,0) ->
elbow (4,0,-1) -> wrist (8,0,0), handle moved to (6,0,2))."""

import math
from importlib import import_module

import bpy
from mathutils import Vector

import kit
import test_step223_ik_fk as IK

ik_fk = import_module(kit.MODULE + ".operators.ik_fk")
ctl = import_module(kit.MODULE + ".operators.ik_fk_control")
menu_map = import_module(kit.MODULE + ".ui.menu_map")
notices = import_module(kit.MODULE + ".ui.notices")
cb_keys = import_module(kit.MODULE + ".ui.cb_keys")

GOAL = IK.bl((6, 0, 2))


def _update(n=3):
    for _ in range(n):
        bpy.context.view_layer.update()


def _reset_state(control=False, snap=True):
    ctl._STATE["control"], ctl._STATE["snap"] = control, snap
    ctl.forget()


def _rig(control=False, snap=True):
    """The arm with its handle moved to the goal, the handlers having seen it (Ik Blend 1)."""
    _reset_state(control, snap)
    arm, handle, con = IK._arm()
    _update()
    handle.location = GOAL
    _update()
    return arm, handle, con


def _wrist(arm):
    return arm.matrix_world @ arm.pose.bones["wrist"].head


def _close(a, b, tol=1e-3):
    return (Vector(a) - Vector(b)).length < tol


def _turn_shoulder(arm, deg=20.0):
    pb = arm.pose.bones["shoulder"]
    e = pb.rotation_euler.copy()
    e.y += math.radians(deg)
    pb.rotation_euler = e
    _update()


def test_menu_items_mapped():
    assert menu_map.MAP["Skeleton/Enable IK/FK Control"] == ("prop", "window_manager.allset_ik_fk_control", {})
    assert menu_map.MAP["Skeleton/Enable IK Handle Snap"] == (
        "prop", "window_manager.allset_ik_handle_snap", {"off_while": "window_manager.allset_ik_fk_control"})
    assert menu_map.MAP["Key/IK/FK Keys/Connect to IK/FK"] == "allset.connect_ik_fk"
    for path in ("Skeleton/Enable IK/FK Control", "Key/IK/FK Keys/Connect to IK/FK"):
        assert notices.notice(path) is None, path          # working items carry no "not in Blender" notice
    assert notices.category("Key/IK/FK Keys/Connect to IK/FK") is None or         "Connect to IK/FK" not in notices.category("Key/IK/FK Keys/Connect to IK/FK")[1]
    wm = bpy.context.window_manager
    _reset_state()
    assert wm.allset_ik_fk_control is False and wm.allset_ik_handle_snap is True        # off / on, like Maya


def test_snap_greyed_while_control_on():
    wm = bpy.context.window_manager
    _reset_state()
    wm.allset_ik_fk_control = True
    wm.allset_ik_handle_snap = False            # greyed in Maya: no effect
    assert wm.allset_ik_handle_snap is True
    assert not ctl.snap_on()
    wm.allset_ik_fk_control = False
    assert ctl.snap_on()


def test_blend_one_to_zero_keeps_ik_pose():
    """Maya writes the IK solution into the joints' rotate values: Ik Blend 1 -> 0 leaves the arm where IK put it,
    and the joints' channels hold the solved rotation."""
    arm, handle, con = _rig()
    at_ik = _wrist(arm)
    assert _close(at_ik, GOAL, 1e-2), (at_ik, GOAL)
    ik_fk.set_blend(arm, arm.pose.bones["elbow"], con, 0.0)
    _update()
    assert _close(_wrist(arm), at_ik), (_wrist(arm), at_ik)
    for name in ("shoulder", "elbow"):
        pb = arm.pose.bones[name]
        assert pb.rotation_euler.to_quaternion().angle > 1e-3, name     # not the rest pose any more


def test_fk_rotation_replaced_after_ik():
    """Maya: an FK rotation set at Ik Blend 0 is replaced by the IK solution once Ik Blend went back to 1 (joints
    without keys)."""
    arm, handle, con = _rig(snap=False)
    elbow = arm.pose.bones["elbow"]
    ik_fk.set_blend(arm, elbow, con, 0.0)
    _update()
    _turn_shoulder(arm, 30.0)
    fk = _wrist(arm)
    ik_fk.set_blend(arm, elbow, con, 1.0)
    _update()
    ik_fk.set_blend(arm, elbow, con, 0.0)
    _update()
    assert _close(_wrist(arm), GOAL, 1e-2), (_wrist(arm), fk)


def test_turning_a_joint_moves_the_handle():
    """IK/FK control off, snap on, handle without keys: the turned joint stays turned and the handle follows the end
    joint."""
    arm, handle, con = _rig()
    _turn_shoulder(arm)
    end = ik_fk.fk_end(arm, arm.pose.bones["elbow"], con)
    assert _close(handle.matrix_world.translation, end), (handle.matrix_world.translation, end)
    _update()
    assert _close(_wrist(arm), end, 1e-2), (_wrist(arm), end)
    assert not _close(end, GOAL, 0.1)


def test_keyed_handle_refuses_the_turn():
    """IK/FK control off and the handle keyed: the joint doesn't turn."""
    arm, handle, con = _rig()
    handle.keyframe_insert("location", frame=1)
    _update()
    before = tuple(arm.pose.bones["shoulder"].rotation_euler)
    _turn_shoulder(arm)
    after = tuple(arm.pose.bones["shoulder"].rotation_euler)
    assert _close(after, before, 1e-4), (after, before)
    assert _close(handle.matrix_world.translation, GOAL)


def test_control_on_lets_the_joint_turn():
    """IK/FK control on: the joint turns even with a keyed handle; the handle stays."""
    arm, handle, con = _rig(control=True)
    handle.keyframe_insert("location", frame=1)
    _update()
    before = tuple(arm.pose.bones["shoulder"].rotation_euler)
    _turn_shoulder(arm)
    pb = arm.pose.bones["shoulder"]
    # the channel took the turn (Blender's IK keeps the chain on the handle at Ik Blend 1)
    assert not _close(tuple(pb.rotation_euler), before, 1e-3)
    assert _close(handle.matrix_world.translation, GOAL)


def test_snap_off_handle_stays():
    arm, handle, con = _rig(snap=False)
    _turn_shoulder(arm)
    assert _close(handle.matrix_world.translation, GOAL)


def test_blend_zero_snap_keeps_handle_on_end_joint():
    """Snap on at Ik Blend 0: the handle sits on the end joint (Maya)."""
    arm, handle, con = _rig()
    ik_fk.set_blend(arm, arm.pose.bones["elbow"], con, 0.0)
    _update()
    handle.location = GOAL + Vector((1.0, 1.0, 1.0))
    _update()
    end = ik_fk.fk_end(arm, arm.pose.bones["elbow"], con)
    assert _close(handle.matrix_world.translation, end), (handle.matrix_world.translation, end)


def test_keyed_joints_keep_their_curves():
    """Joints with rotation keys: their curves give the FK values, the solved pose is not written over them."""
    arm, handle, con = _rig()
    for name in ("shoulder", "elbow"):
        arm.pose.bones[name].rotation_euler = (0.0, 0.0, 0.0)
        arm.pose.bones[name].keyframe_insert("rotation_euler", frame=1)
    _update()
    handle.location = GOAL + Vector((0.0, 0.0, 0.5))
    _update()
    for name in ("shoulder", "elbow"):
        assert arm.pose.bones[name].rotation_euler.to_quaternion().angle < 1e-6, name


# --- Connect to IK/FK ---------------------------------------------------------------------------------------------

def _ctrl(name="ctrl"):
    ob = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def test_connect_errors():
    arm, handle, con = _rig()
    a, b = _ctrl("a"), _ctrl("b")
    IK._select(a)
    try:
        bpy.ops.allset.connect_ik_fk('EXEC_DEFAULT')
    except RuntimeError as ex:
        assert ik_fk.CONNECT_SELECT_TWO in str(ex), ex
    else:
        raise AssertionError("one item: Maya's error expected")
    IK._select(a, b)
    try:
        bpy.ops.allset.connect_ik_fk('EXEC_DEFAULT')
    except RuntimeError as ex:
        assert ik_fk.CONNECT_LAST_HANDLE in str(ex), ex
    else:
        raise AssertionError("no handle: Maya's error expected")


def test_connect_drives_ik_blend():
    arm, handle, con = _rig()
    ctrl = _ctrl()
    IK._select(ctrl, handle)                       # the handle last (active)
    assert bpy.ops.allset.connect_ik_fk('EXEC_DEFAULT') == {'FINISHED'}
    assert ik_fk.connected_handle(ctrl) is handle
    handle[ik_fk.IK_BLEND] = 0.25
    handle.update_tag()
    _update()
    assert abs(ctrl[ik_fk.IK_BLEND] - 0.25) < 1e-6
    # no keys made by connecting (Maya)
    assert not kit.fcurves(ctrl)
    # connecting again: Maya's warning, no new connection
    made, warnings = ik_fk.connect_to_ik_fk([ctrl, handle], handle)
    assert made == 0 and warnings == [f"ctrl.ikBlend is already connected to {handle.name}.ikBlend"], warnings
    # two items with the handle first (not active) count too
    other = _ctrl("other")
    IK._select(handle, other)
    assert bpy.ops.allset.connect_ik_fk('EXEC_DEFAULT') == {'FINISHED'}
    assert ik_fk.connected_handle(other) is handle


def test_connected_object_drives_the_ik_fk_commands():
    arm, handle, con = _rig()
    ctrl = _ctrl()
    IK._select(ctrl, handle)
    bpy.ops.allset.connect_ik_fk('EXEC_DEFAULT')
    IK._select(ctrl)
    assert [c for _a, _p, c in ik_fk.ik_constraints(bpy.context)] == [con]
    assert bpy.ops.allset.ik_fk_key('EXEC_DEFAULT') == {'FINISHED'}
    paths = {fc.data_path for fc in kit.fcurves(handle)}
    assert '["ikBlend"]' in paths and "location" in paths, paths
    assert {fc.data_path for fc in kit.fcurves(ctrl)} == {"location"}       # Maya keys the object's translate
    ik_fk._STATE["on"] = True
    IK._select(ctrl)
    assert bpy.ops.allset.ik_solver_toggle('EXEC_DEFAULT') == {'FINISHED'}
    assert handle[ik_fk.IK_BLEND] == 0.0
    IK._select(ctrl)
    assert bpy.ops.allset.move_ik_to_fk('EXEC_DEFAULT') == {'FINISHED'}
    _update()
    assert _close(handle.matrix_world.translation, ik_fk.fk_end(arm, arm.pose.bones["elbow"], con))


def test_connected_channel_shows_in_channel_box():
    arm, handle, con = _rig()
    ctrl = _ctrl()
    IK._select(ctrl, handle)
    bpy.ops.allset.connect_ik_fk('EXEC_DEFAULT')
    keys = cb_keys.custom_keys(ctrl)
    assert ik_fk.IK_BLEND in keys, keys


class _Layout:
    """Records what a menu draw does with the layout."""

    def __init__(self, log):
        self.log, self.enabled = log, True

    def row(self):
        r = _Layout(self.log)
        self.log.append(("row", r))
        return r

    def prop(self, owner, attr, **kw):
        self.log.append(("prop", attr, self.enabled))


def test_snap_item_greyed_in_menu_while_control_on():
    draw = import_module(kit.MODULE + ".ui.menu_item_draw")
    s = menu_map.normalize(menu_map.MAP["Skeleton/Enable IK Handle Snap"])
    wm = bpy.context.window_manager
    for control in (False, True):
        _reset_state(control=control)
        log = []
        draw.draw_prop(_Layout(log), "Enable IK Handle Snap", s[1], s[2], "Skeleton/Enable IK Handle Snap")
        props = [e for e in log if e[0] == "prop"]
        assert props == [("prop", "allset_ik_handle_snap", not control)], (control, log)
    _reset_state()
    assert wm.allset_ik_fk_control is False


def test_blend_drop_after_load_keeps_ik_pose():
    """A file whose joint channels don't hold the IK solution (loaded, nothing moved since): Ik Blend 1 -> 0 still
    leaves the arm in the IK pose."""
    arm, handle, con = _rig()
    for name in ("shoulder", "elbow"):
        arm.pose.bones[name].rotation_euler = (0.0, 0.0, 0.0)
    ctl.forget()                                    # what load / undo do
    _update()
    at_ik = _wrist(arm)
    assert _close(at_ik, GOAL, 1e-2), at_ik
    assert arm.pose.bones["shoulder"].rotation_euler.to_quaternion().angle < 1e-6   # nothing written at load
    handle[ik_fk.IK_BLEND] = 0.0                    # typed in the Channel Box
    handle.update_tag()
    _update()
    assert _close(_wrist(arm), at_ik), (_wrist(arm), at_ik)
