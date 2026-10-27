"""Step 252 (#168): Maya orient / parent constraint Interp Type and aim world up types against mayapy 2026
(tests/maya252_cons_data.py, research/maya/re/060_rig_lane.md "Step 252 measurements")."""

import math

import bpy
from mathutils import Matrix, Quaternion, Vector

import maya252_cons_data as M
from bl_ext.user_default.allset.operators import constrain_interp as ci
from bl_ext.user_default.allset.operators import constrain_multi as cm
from bl_ext.user_default.allset.operators.joints import MAYA_WORLD as K
from bl_ext.user_default.allset.ui import channel_box as cb

QK = K.to_quaternion()
TOL_DEG = 1e-3
TOL_KIT = 0.05      # end to end: Blender's float32 transforms (worst 0.04 deg measured)


def mq(rot, order='XYZ'):
    """Maya q_Euler of a rotate value in degrees (Maya axes)."""
    return ci.euler_quat([math.radians(a) for a in rot], order)


def ang(a, b):
    return math.degrees(2.0 * math.acos(min(1.0, abs(ci.qdot(ci.q_tuple(a), ci.q_tuple(b))))))


def maya_matrix(m16):
    """Maya xform -q -ws -m (row-major, row vectors) -> (rotation in Maya axes as a column matrix, translation)."""
    rows = [Vector(m16[i * 4:i * 4 + 3]) for i in range(3)]
    r = Matrix([rows[0].normalized(), rows[1].normalized(), rows[2].normalized()]).transposed()
    return r, Vector(m16[12:15])


def to_blender_rot(r_maya):
    return K @ r_maya @ K.inverted()


def _reset():
    if bpy.context.object is not None and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for arm in list(bpy.data.armatures):
        bpy.data.armatures.remove(arm)


def _node(name, rot=(0, 0, 0), loc=(0, 0, 0), parent=None):
    ob = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(ob)
    if parent is not None:
        ob.parent = parent
        ob.matrix_parent_inverse = Matrix.Identity(4)
    ob.rotation_mode = 'QUATERNION'
    ob.rotation_quaternion = _blender_q(mq(rot))                 # own_maya(ob) == Maya q_Euler(rot), sign kept
    ob.location = K @ Vector(loc)
    return ob


def _blender_q(q_maya):
    qk = ci.q_tuple(QK)
    return ci.qmul(ci.qmul(qk, q_maya), ci.qinv(qk))


def _constrain(owner, targets, ctype, mo=None):
    for ob in bpy.context.scene.objects:
        ob.select_set(False)
    for t in targets:
        t.select_set(True)
    owner.select_set(True)
    bpy.context.view_layer.objects.active = owner
    bpy.context.view_layer.update()
    kw = {} if mo is None else {"maintain_offset": 'ON' if mo else 'OFF'}
    assert bpy.ops.allset.constrain('EXEC_DEFAULT', type=ctype, **kw) == {'FINISHED'}
    groups = list(cm._groups(owner))
    assert len(groups) == 1, groups
    return groups[0]


def _set_weights(owner, group, ws):
    for (prop, _label), w in zip(cm.weights(owner, group), ws):
        owner[prop] = float(w)
    owner.id_data.update_tag()       # like a Channel Box edit (channel_box.set_value): drivers re-read the weights


def _settle(owner, group):
    for _ in range(3):
        bpy.context.view_layer.update()
        if ci.blend_constraint(owner, group) is not None:
            ci.update(owner, group)
    bpy.context.view_layer.update()


def _world_rot(ob):
    return ob.matrix_world.to_3x3().normalized()


# --- the maths against Maya ------------------------------------------------------------------------------------------

def test_blend_math_orient_rows():
    worst = {}
    for row in M.ROWS["rows"]:
        p = ci.canon(mq(row["target_parent"]))
        qs = [ci.qmul(p, mq(r)) for r in row["rots"]]
        last = ci.blend(qs, [1.0] * len(qs), ci.AVERAGE)          # the output when the constraint was made
        for it in range(4):
            q = ci.blend(qs, row["ws"], it, last)
            worst[it] = max(worst.get(it, 0.0), ang(q, mq(row["out"][str(it)]["rot"])))
    assert all(v < TOL_DEG for v in worst.values()), worst


def test_blend_math_parent_offsets_and_rotate_orders():
    worst = {}
    for data, key in ((M.PARENT_MO, "xyz"), (M.PARENT_RO, "ro")):
        for c in data:
            order = ['XYZ', 'YZX', 'ZXY', 'XZY', 'YXZ', 'ZYX'][c.get("ro", 0)]
            c0 = mq(c["c0"], order)
            for it in range(4):
                o = c["out"][str(it)]
                offs = []
                for t in c["t0"]:
                    m = ci.q_matrix(ci.qmul(ci.qinv(mq(t["r"])), c0))
                    offs.append(ci.euler_quat(ci.decompose(m, order), order))
                qs = [ci.qmul(mq(t["r"]), off) for t, off in zip(c["t1"], offs)]
                q = ci.blend(qs, c["ws"], it, c0)
                worst[(key, it)] = max(worst.get((key, it), 0.0), ang(q, mq(o["rot"], order)))
    # xyz owners: every type exact; other rotate orders: Shortest / Longest exact, Average / No Flip hit the stored
    # Euler branch of some offsets (060_questions.md C8)
    assert all(worst[("xyz", it)] < TOL_DEG for it in range(4)), worst
    assert worst[("ro", 2)] < TOL_DEG and worst[("ro", 3)] < TOL_DEG, worst


def test_blend_math_parent_sign_cases():
    # target parent turned -170 deg: Maya's parent part has w >= 0 (Average -85, not +95)
    s = M.SIGN
    assert abs(s["parent_m170_it1"]["rot"][2] + 85.0) < 1e-4
    qs = [ci.IDENTITY, ci.canon(mq((0, 0, -170)))]
    assert ang(ci.blend(qs, [1, 1], ci.AVERAGE), mq(s["parent_m170_it1"]["rot"])) < TOL_DEG
    qs = [ci.IDENTITY, ci.qmul(ci.canon(mq((0, 0, -170))), mq((0, 0, -20)))]       # own Euler sign kept: -95
    assert ang(ci.blend(qs, [1, 1], ci.AVERAGE), mq(s["parent_m170_own_m20_it1"]["rot"])) < TOL_DEG


def test_zero_weights_give_rest():
    rest = mq((0, 60, 0))
    assert ang(ci.blend([mq((0, 40, 0)), mq((0, 80, 0))], [0, 0], ci.AVERAGE, None, rest), rest) < 1e-9
    assert abs(M.ROWS["zero"]["1"]["rot"][1] - 60.0) < 1e-6


# --- the kit against Maya ---------------------------------------------------------------------------------------------

def test_orient_constraint_interp_types_end_to_end():
    worst = {}
    for row in M.ROWS["rows"]:
        for it in range(4):
            _reset()
            p = _node("P", row["target_parent"])
            ts = [_node(f"T{i}", r, parent=p) for i, r in enumerate(row["rots"])]
            c = _node("C")
            group = _constrain(c, ts, 'COPY_ROTATION')
            assert ci.mode_of(c, group) == ci.AVERAGE                       # Maya factory
            assert bpy.ops.allset.constraint_interp(object=c.name, group=group, mode=str(it)) == {'FINISHED'}
            _set_weights(c, group, row["ws"])
            _settle(c, group)
            want = to_blender_rot(maya_matrix(row["out"][str(it)]["wm"])[0])
            got = _world_rot(c)
            worst[it] = max(worst.get(it, 0.0), ang(got.to_quaternion(), want.to_quaternion()))
    assert all(v < TOL_KIT for v in worst.values()), worst


def test_parent_constraint_maintain_offset_end_to_end():
    worst_r, worst_t = {}, 0.0
    for case in M.PARENT_MO[:6]:
        for it in (1, 2, 3):
            _reset()
            ts = [_node(f"T{i}", t["r"], t["t"]) for i, t in enumerate(case["t0"])]
            c = _node("C", case["c0"], case["cpos"])
            group = _constrain(c, ts, 'CHILD_OF', mo=True)
            assert bpy.ops.allset.constraint_interp(object=c.name, group=group, mode=str(it)) == {'FINISHED'}
            _set_weights(c, group, case["ws"])
            for t, t1 in zip(ts, case["t1"]):
                t.rotation_quaternion = _blender_q(mq(t1["r"]))
            _settle(c, group)
            o = case["out"][str(it)]
            want = to_blender_rot(ci.q_matrix(mq(o["rot"])))
            worst_r[it] = max(worst_r.get(it, 0.0), ang(_world_rot(c).to_quaternion(), want.to_quaternion()))
            worst_t = max(worst_t, (c.matrix_world.translation - K @ Vector(o["pos"])).length)
    assert all(v < TOL_KIT for v in worst_r.values()), worst_r
    assert worst_t < 1e-3, worst_t


def test_shortest_uses_blender_influence_only():
    _reset()
    row = M.ROWS["rows"][7]                                              # three targets
    ts = [_node(f"T{i}", r) for i, r in enumerate(row["rots"])]
    c = _node("C")
    group = _constrain(c, ts, 'COPY_ROTATION')
    bpy.ops.allset.constraint_interp(object=c.name, group=group, mode=str(ci.SHORTEST))
    assert ci.blend_constraint(c, group) is None, "Shortest needs no kit blend"
    _set_weights(c, group, row["ws"])
    bpy.context.view_layer.update()
    want = to_blender_rot(ci.q_matrix(mq(row["out"]["2"]["rot"])))
    if any(abs(a) > 1e-9 for a in row["target_parent"]):
        return
    assert ang(_world_rot(c).to_quaternion(), want.to_quaternion()) < TOL_KIT


def test_zero_weights_keep_rest_end_to_end():
    _reset()
    a, b = _node("A", (0, 40, 0)), _node("B", (0, 80, 0))
    c = _node("C", (10, 20, 30))
    group = _constrain(c, [a, b], 'COPY_ROTATION')
    _set_weights(c, group, [0, 0])
    _settle(c, group)
    want = to_blender_rot(ci.q_matrix(mq(M.ROWS["zero"]["1"]["rot"])))
    assert ang(_world_rot(c).to_quaternion(), want.to_quaternion()) < TOL_KIT


def test_blend_is_part_of_the_node_and_goes_with_it():
    _reset()
    a, b = _node("A", (0, 0, 30)), _node("B", (0, 0, 90))
    c = _node("C")
    group = _constrain(c, [a, b], 'COPY_ROTATION')
    blend = ci.blend_constraint(c, group)
    assert blend is not None and blend not in cb.constraints(c), "the blend is hidden in the Channel Box"
    assert len(cb.constraints(c)) == 2
    cm.set_enabled(c, group, False)
    assert not blend.enabled
    cm.set_enabled(c, group, True)
    helper = blend.target.name
    cm.remove_group(c, group)
    assert ci.blend_constraint(c, group) is None and helper not in bpy.data.objects
    assert not any(k.startswith(ci.INTERP) for k in c.keys())


def test_bone_owner_runs():
    _reset()
    arm = bpy.data.armatures.new("A")
    ob = bpy.data.objects.new("skeleton1", arm)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT')
    eb = arm.edit_bones.new("joint1")
    eb.head, eb.tail = (0, 0, 0), (0, 1, 0)
    bpy.ops.object.mode_set(mode='OBJECT')
    t0, t1 = _node("T0", (0, 0, 20)), _node("T1", (0, 0, 120))
    pb = ob.pose.bones["joint1"]
    cm.build(bpy.context, pb, [(t0, ""), (t1, "")], 'COPY_ROTATION')
    group = next(iter(cm._groups(ob.pose.bones["joint1"])))
    pb = ob.pose.bones["joint1"]
    _settle(pb, group)
    # Average of two equal-weight targets 100 deg apart = the joint turned to their middle (Maya frames)
    cp_inv = ci.parent_frame(pb).inverted()
    want = ci.blend([ci.target_quat(cp_inv, t0), ci.target_quat(cp_inv, t1)], [1, 1], ci.AVERAGE)
    got = (cp_inv @ ci.frame(pb)).to_quaternion()
    assert ang(got, want) < TOL_KIT


# --- aim world up types ------------------------------------------------------------------------------------------------

def test_aim_world_up_types():
    from bl_ext.user_default.allset.operators import option_windows
    worst = {}
    for case in M.AIM:
        for wut, label in (("scene", "Scene up"), ("object", "Object up"), ("objectrotation", "Object rotation up"),
                           ("vector", "Vector"), ("none", "None")):
            _reset()
            a = _node("A", loc=case["a"])
            up = _node("UP", case["upr"], case["up"])
            c = _node("C", loc=case["c"])
            for ob in (a, up, c):
                ob.rotation_mode = 'XYZ' if ob is c else ob.rotation_mode
            for ob in bpy.context.scene.objects:
                ob.select_set(False)
            a.select_set(True)
            c.select_set(True)
            bpy.context.view_layer.objects.active = c
            bpy.context.view_layer.update()
            win = next(w for w in option_windows.WINDOWS if w.key == "aim_constraint")
            v = win.defaults()
            v.update(world_up_type=label, world_up_vector=tuple(case["wuv"]),
                     world_up_object="UP" if wut in ("object", "objectrotation") else "")
            assert win.run(bpy.context, v) == {'FINISHED'}, wut
            bpy.context.view_layer.update()
            bpy.context.view_layer.update()
            want_r, _t = maya_matrix(case["out"][wut])
            want = to_blender_rot(want_r)
            got = _world_rot(c)
            if wut == "none":
                # Maya: the shortest turn from the node's rest axes (Damped Track turns from the current ones: equal
                # here, the node starts unrotated)
                pass
            worst[wut] = max(worst.get(wut, 0.0), ang(got.to_quaternion(), want.to_quaternion()))
    assert all(v < TOL_KIT for v in worst.values()), worst


def test_aim_object_up_helper_goes_with_the_aim():
    from bl_ext.user_default.allset.operators import rig_tools
    _reset()
    a, up, c = _node("A", loc=(3, 1, 0)), _node("UP", loc=(0, 4, 0)), _node("C")
    con = c.constraints.new('TRACK_TO')
    con.target = a
    con = rig_tools.aim(c.constraints, con, world_up="Object up", up_object=up)
    companion = c.constraints.get(con.name + rig_tools.UP_SUFFIX)
    assert companion is not None and companion not in cb.constraints(c) and con in cb.constraints(c)
    helper, companion = companion.target.name, companion.name
    c.constraints.remove(con)
    cm.cleanup()
    assert helper not in bpy.data.objects and c.constraints.get(companion) is None
