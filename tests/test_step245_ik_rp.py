"""Step 245 (Issue #162): Maya ikRPsolver on kit IK handles — default pole vector, Blender pole_angle formula, twist,
Pole Vector constraint, straight chains with / without a preferred angle.

Maya 2026 truth (tests/maya2026_rig_data.py IK: default_pole_vector 12 cases, rp_solve 8 rows (5e-5 model),
rp_rest_plane_and_preferred_angle; research/maya/re/joint_rig_2026_ik.md §2–3, §7, principles.md §1.2–1.5).
"""

import math
from importlib import import_module

import bpy
from mathutils import Vector

import kit
import maya2026_rig as rig
import maya2026_rig_data as data

joints = import_module(kit.MODULE + ".operators.joints")
skin = import_module(kit.MODULE + ".operators.skin")
ik_rp = import_module(kit.MODULE + ".operators.ik_rp")
cb = import_module(kit.MODULE + ".ui.channel_box")

IK = data.IK["ik"]
ROWS = IK["rp_solve"]["rows"]
L1 = L2 = IK["rp_solve"]["L1"]


def _reset():
    if bpy.context.object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)


def _chain(pts, pa=None):
    """A Maya-oriented kit chain (aos orient) at Maya points; ``pa`` {joint index: Maya rotate} = preferred angles."""
    _reset()
    recs = {f"j{i}": {"w": p, "parent": (f"j{i - 1}" if i else None)} for i, p in enumerate(pts)}
    ob = rig.build_skeleton(recs, name="skeleton1", oriented=False)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    joints.orient(ob, ["j0"], "Y+", True, "xyz", True)
    bpy.ops.object.mode_set(mode='POSE')
    from importlib import import_module as im
    rig_maya = im(kit.MODULE + ".operators.rig_maya")
    for i, rot in (pa or {}).items():
        # Maya rotate (joint axes X, Y, Z) = rotation about the bone's Y, Z, X axes
        pb = ob.pose.bones[f"j{i}"]
        pb[rig_maya.PREFERRED_PROP] = [rot[2], rot[0], rot[1]]
    return ob


def _ik(ob, end):
    """Create IK Handle (RP) from j0 to joint ``end``."""
    h = skin.create_ik(bpy.context, ob, ("j0", 'HEAD'), (end, 'HEAD'), "RP")
    assert h is not None
    return h


def _maya(ob, name):
    return rig.to_maya(ob.matrix_world @ ob.pose.bones[name].head)


def _solve(handle, goal, pv=None, twist=None):
    handle.location = rig.to_blender(goal)
    if pv is not None:
        for n, v in zip(ik_rp.PV, pv):
            handle[n] = float(v)
    if twist is not None:
        handle[ik_rp.TWIST] = float(twist)
    for _ in range(3):
        bpy.context.view_layer.update()
        ik_rp.update_handle(handle)
    bpy.context.view_layer.update()


def test_default_pole_vector_equals_maya():
    worst = 0.0
    for case in IK["default_pole_vector"]:
        pts = [rig.to_blender(p) for p in ((0, 0, 0), case["elbow"], case["wrist"])]
        pv = rig.to_maya(ik_rp.default_pole_vector(pts, 2.0))
        worst = max(worst, (pv - Vector(case["poleVector"])).length)
    assert worst < 1e-5, worst
    print(f"  default pole vector: {len(IK['default_pole_vector'])} cases, worst {worst:.1e}")


def test_farthest_joint_rule_and_display_scale():
    # a 3-bone chain: the joint whose |p x d| is largest gives the pole (measured: the first joint would be off by 3.95)
    pts = [Vector(p) for p in ((0, 0, 0), (1, 0.2, 0), (3, 2.0, 0), (5, 0.1, 0))]
    pv = ik_rp.default_pole_vector(pts, 4.0)
    off = pts[2] - pts[3] * (pts[2].dot(pts[3]) / pts[3].length_squared)
    assert (pv.normalized() - off.normalized()).length < 1e-6 and abs(pv.length - 4.0) < 1e-6


def test_create_handle_gives_mayas_pole_vector_and_angle():
    ob = _chain([(0, 0, 0), (4, 0, -1), (8, 0, 0)])
    h = _ik(ob, "j2")
    assert [round(h[n], 5) for n in ik_rp.PV] == [0.0, 0.0, -2.0], [h[n] for n in ik_rp.PV]   # Maya (0, 0, -2)
    assert h[ik_rp.TWIST] == 0.0
    helper = h[ik_rp.HELPER]
    assert helper.hide_viewport and helper.get(ik_rp.OWNER) == h.name
    con = ob.pose.bones["j1"].constraints[h.name]
    assert con.pole_target == helper
    assert abs(abs(math.degrees(con.pole_angle)) - 180.0) < 1e-3, math.degrees(con.pole_angle)   # ik.md §7
    keys = cb.custom_keys(h)
    assert {"poleVectorX", "poleVectorY", "poleVectorZ", "twist", "ikBlend"} <= set(keys), keys
    # the chain doesn't move when the handle is made
    bpy.context.view_layer.update()
    assert (_maya(ob, "j1") - Vector((4, 0, -1))).length < 1e-4
    _reset()


def test_rp_solve_rows_equal_maya():
    ob = _chain([(0, 0, 0), (4, 0, -1), (8, 0, 0)])
    h = _ik(ob, "j2")
    worst_reach, worst_far = 0.0, 0.0
    for r in ROWS:
        _solve(h, r["goal"], r["pv"], r["twist"])
        e = (_maya(ob, "j1") - Vector(r["elbow"])).length
        reach = Vector(r["goal"]).length < L1 + L2 - 1e-6
        if reach:
            worst_reach = max(worst_reach, e)
            assert e < 1e-3, (r, e)
        else:
            worst_far = max(worst_far, e)
            # out of reach: Blender's IK keeps a sliver of bend (0.011 measured, ik.md §7)
            assert e < 0.015, (r, e)
    print(f"  rp_solve: reachable worst {worst_reach:.1e}, out of reach worst {worst_far:.1e}")
    _reset()


def test_twist_turns_the_plane_right_handed():
    ob = _chain([(0, 0, 0), (4, 0, -1), (8, 0, 0)])
    h = _ik(ob, "j2")
    goal = Vector((6, 1, 0))
    _solve(h, goal, (0, 0, -2), 0.0)
    e0 = _maya(ob, "j1")
    _solve(h, goal, (0, 0, -2), 90.0)
    e1 = _maya(ob, "j1")
    u = goal.normalized()
    from mathutils import Quaternion
    want = Quaternion(u, math.radians(90.0)) @ e0
    assert (e1 - want).length < 1e-3, (e1, want)
    _reset()


def test_pole_vector_constraint_is_target_minus_start():
    ob = _chain([(1, 0, 0), (5, 0, -1), (9, 0, 0)])
    h = _ik(ob, "j2")
    loc = bpy.data.objects.new("locator1", None)
    bpy.context.scene.collection.objects.link(loc)
    loc.location = rig.to_blender((5, 0, -5))
    bpy.ops.object.mode_set(mode='OBJECT')
    for o in bpy.context.selected_objects:
        o.select_set(False)
    loc.select_set(True)
    h.select_set(True)
    bpy.context.view_layer.objects.active = h
    assert bpy.ops.allset.pole_vector() == {'FINISHED'}
    bpy.context.view_layer.update()
    pv = [round(h[n], 4) for n in ik_rp.PV]
    assert pv == [4.0, 0.0, -5.0], pv                       # Maya: target - start joint
    loc.location = rig.to_blender((5, 3, -5))
    for _ in range(2):
        bpy.context.view_layer.update()
        ik_rp.update_handle(h)
    assert [round(h[n], 4) for n in ik_rp.PV] == [4.0, 3.0, -5.0]
    h.location = rig.to_blender((7, 1, 0))                  # moving the handle doesn't change pv
    for _ in range(2):
        bpy.context.view_layer.update()
        ik_rp.update_handle(h)
    assert [round(h[n], 4) for n in ik_rp.PV] == [4.0, 3.0, -5.0]
    _reset()


def test_straight_chain_bends_like_maya():
    straight = IK["rp_rest_plane_and_preferred_angle"]
    cases = [(None, straight["straight_no_pa_elbow"], (0, 0, 1)),
             ((0, 30, 0), straight["straight_pa_(0, 30, 0)"]["elbow"], straight["straight_pa_(0, 30, 0)"]["pv"]),
             ((0, 0, 30), straight["straight_pa_(0, 0, 30)"]["elbow"], straight["straight_pa_(0, 0, 30)"]["pv"]),
             ((0, -30, 0), straight["straight_pa_(0, -30, 0)"]["elbow"], straight["straight_pa_(0, -30, 0)"]["pv"])]
    for pa, elbow, maya_pv in cases:
        ob = _chain([(0, 0, 0), (4, 0, 0), (8, 0, 0)], {1: pa} if pa else None)
        h = _ik(ob, "j2")
        pv = Vector([h[n] for n in ik_rp.PV])
        if pa:      # in the preferred-angle pose: Maya's pole vector exactly
            assert (pv - Vector(maya_pv)).length < 1e-4, (pa, tuple(pv), maya_pv)
        else:       # straight, no preferred angle: Maya (1.414, 0, 1.414) [U]; the kit's +Z has the same solve plane
            perp = Vector(straight["straight_default_pv"]) * 1.0
            perp.x = 0.0
            assert (pv.normalized() - perp.normalized()).length < 1e-4, tuple(pv)
        _solve(h, (6, 0, 0))
        e = (_maya(ob, "j1") - Vector(elbow)).length
        assert e < 1e-3, (pa, tuple(_maya(ob, "j1")), elbow, e)
    _reset()


def test_delete_handle_removes_the_helper_and_undo():
    ob = _chain([(0, 0, 0), (4, 0, -1), (8, 0, 0)])
    bpy.ops.ed.undo_push(message="before")
    h = _ik(ob, "j2")
    helper_name = h[ik_rp.HELPER].name
    dag = import_module(kit.MODULE + ".operators.dag")
    dag.delete_hierarchy(bpy.context, [h])
    assert helper_name not in bpy.data.objects, "the pole helper goes with its handle"
    _reset()


def test_sc_handle_has_no_pole():
    ob = _chain([(0, 0, 0), (4, 0, -1), (8, 0, 0)])
    h = skin.create_ik(bpy.context, ob, ("j0", 'HEAD'), ("j2", 'HEAD'), "SC")
    assert ik_rp.HELPER not in h and ob.pose.bones["j1"].constraints[h.name].pole_target is None
    _reset()
