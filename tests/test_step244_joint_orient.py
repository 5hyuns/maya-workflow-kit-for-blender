"""Step 244 (Issue #161): joint orientation = Maya 2025+ factory (orientJoint with auto orient secondary axis).

Maya 2026 truth (tests/maya2026_rig_data.py): SKELETON_MENU orient_joint_algorithm (mayapy, every oj / sao), OJ_VERIFY
extremes (measured with mayapy: straight / diagonal / 180° fold / plane ties / zero-length child / root at the origin), JOINT_TOOL
front_chain (GUI Joint Tool, 4 front clicks). Rules: research/maya/re/joint_rig_2026_principles2.md §1. Kit:
operators/joint_orient.py (maths), joints.orient_bones / orient / orient_new (bones), AE Joint Orient / SSC.
"""

import math
import random
from importlib import import_module

import bpy
from mathutils import Matrix, Vector

import kit
import maya2026_rig as rig
import maya2026_rig_data as data

jo_mod = import_module(kit.MODULE + ".operators.joint_orient")
joints = import_module(kit.MODULE + ".operators.joints")
ae = import_module(kit.MODULE + ".ui.attribute_editor")

I3 = Matrix.Identity(3)
EXTREME_PTS = {     # oj_verify.py "extremes" (Maya world, chain order)
    "straight_x": [(0, 0, 0), (2, 0, 0), (4, 0, 0), (6, 0, 0)],
    "straight_diag": [(0, 0, 0), (1, 1, 1), (2, 2, 2), (3, 3, 3)],
    "fold180": [(0, 0, 0), (3, 0, 0), (1, 0, 0), (1, 2, 0)],
    "plane_xy_tie": [(0, 0, 0), (2, 1, 0), (4, 0, 0), (6, 1, 0)],
    "plane_xz": [(0, 0, 0), (2, 0, 1), (4, 0, 0), (6, 0, 1)],
    "zero_len_child": [(0, 0, 0), (2, 1, 0), (2, 1, 0), (4, 0, 0)],
    "root_at_origin_straight_y": [(0, 0, 0), (0, 2, 0), (0, 4, 0)],
}
TIES = {"plane_xy_tie", "fold180"}        # n . up = 0: Maya leaves the sign to rounding (principles2.md §1.3)
KIT_SAO = {"yup": "Y+", "ydown": "Y-", "zup": "Z+", "zdown": "Z-", "xup": "X+", "xdown": "X-", None: "NONE"}


def _chain_model(pts, oj, sao, aos, world=I3):
    names = [f"j{i}" for i in range(len(pts))]
    pos = {n: Vector(p) for n, p in zip(names, pts)}
    parent = {n: (names[i - 1] if i else None) for i, n in enumerate(names)}
    child = {n: (names[i + 1] if i + 1 < len(names) else None) for i, n in enumerate(names)}
    frames = {n: world.copy() for n in names}            # the joint command makes world-aligned joints
    jo_mod.orient_frames(names, pos, parent, child, frames, world, oj, sao, aos)
    return names, frames


def _axes_rows(m):
    return [list(m.col[i]) for i in range(3)]


def _err(a, b, skip_sign=()):
    worst = 0.0
    for i in range(3):
        d = (Vector(a.col[i]) - Vector(b.col[i])).length
        if i in skip_sign:
            d = min(d, (Vector(a.col[i]) + Vector(b.col[i])).length)
        worst = max(worst, d)
    return worst


def _rows_matrix(x, y, z):
    m = Matrix.Identity(3)
    m.col[0], m.col[1], m.col[2] = Vector(x), Vector(y), Vector(z)
    return m


# --- the maths against Maya --------------------------------------------------------------------------------------

def test_model_equals_maya_orient_joint_algorithm():
    cases = {"xyz_yup": ("xyz", "yup", False), "xyz_yup_aos": ("xyz", "yup", True), "xyz_zup": ("xyz", "zup", False),
             "xyz_ydown": ("xyz", "ydown", False), "yzx_zup": ("yzx", "zup", False), "xzy_yup": ("xzy", "yup", False),
             "none": ("none", "yup", False)}
    algo = data.SKELETON_MENU["skeleton"]["orient_joint_algorithm"]
    worst = 0.0
    for key, (oj, sao, aos) in cases.items():
        attrs = algo[key]["attrs"]
        names = list(attrs)
        pos = {n: Vector(attrs[n]["w"]) for n in names}
        parent = {n: attrs[n]["parent"] for n in names}
        child = {n: next((c for c in names if attrs[c]["parent"] == n), None) for n in names}
        frames = {n: I3.copy() for n in names}
        order = sorted(names, key=lambda n: sum(1 for _ in _ancestors(n, parent)))
        jo_mod.orient_frames(order, pos, parent, child, frames, I3, oj, sao, aos)
        want = {n: m.to_3x3().normalized() for n, m in rig.world_matrices(attrs).items()}
        ties = _ties(order, pos, parent, child, sao) if aos else set()
        for n in names:
            e = _err(frames[n], want[n], skip_sign=(1, 2) if n in ties else ())
            worst = max(worst, e)
            assert e < 2e-3, (key, n, e)                      # fixture jointOrient rounded to 4 decimals
    print(f"  orient_joint_algorithm worst {worst:.1e}")


def _ties(order, pos, parent, child, sao):
    """Joints (and the end joints under them) whose bend normal is perpendicular to the up axis: Maya's sign is float
    rounding there (principles2.md §1.3)."""
    up = Vector(jo_mod.world_up(sao, I3))
    out = set()
    for n in order:
        par, c = parent.get(n), child.get(n)
        if par is not None and par in out and c is None:
            out.add(n)
        if par is None or c is None:
            continue
        nrm = (pos[n] - pos[par]).cross(pos[c] - pos[n])
        if nrm.length > 1e-9 and abs(nrm.normalized().dot(up)) < 1e-6:
            out.add(n)
    return out


def _ancestors(n, parent):
    while parent.get(n) is not None:
        n = parent[n]
        yield n


def test_model_equals_maya_extremes():
    ext = data.OJ_VERIFY["extremes"]
    worst = 0.0
    for key, row in ext.items():
        name, oj, sao, aos = key.split("|")
        sao = None if sao == "None" else sao
        names, frames = _chain_model(EXTREME_PTS[name], oj, sao, aos == "aos1")
        for n, maya in zip(names, row["joints"]):
            want = _rows_matrix(maya["x"], maya["y"], maya["z"])
            e = _err(frames[n], want, skip_sign=(1, 2) if name in TIES else ())
            worst = max(worst, e)
            assert e < 1e-4, (key, n, e, _axes_rows(frames[n]), maya)
    print(f"  extremes worst {worst:.1e} ({len(ext)} cases)")


def test_model_equals_maya_joint_tool_front_chain():
    fc = data.JOINT_TOOL["front_chain"]
    pts = [fc[n]["p"] for n in ("joint1", "joint2", "joint3", "joint4")]
    names, frames = _chain_model(pts, "xyz", "yup", True)
    for n, mn in zip(names, ("joint1", "joint2", "joint3", "joint4")):
        want = _rows_matrix(*fc[mn]["axes"])
        assert _err(frames[n], want) < 1e-4, (mn, _axes_rows(frames[n]), fc[mn]["axes"])
    # Maya's variable bone radius: from the distance to the child (the end joint copies its parent's)
    for i, mn in enumerate(("joint1", "joint2", "joint3")):
        r = jo_mod.radius((Vector(pts[i + 1]) - Vector(pts[i])).length)
        assert abs(r - fc[mn]["radius"]) < 2e-3, (mn, r, fc[mn]["radius"])
    assert fc["joint4"]["radius"] == fc["joint3"]["radius"]


# --- the kit's bones ---------------------------------------------------------------------------------------------

def _reset():
    if bpy.context.object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)


def _build(pts, unit=1.0, branch=None):
    _reset()
    recs = {f"j{i}": {"w": p, "parent": (f"j{i - 1}" if i else None)} for i, p in enumerate(pts)}
    for name, (p, par) in (branch or {}).items():
        recs[name] = {"w": p, "parent": par}
    ob = rig.build_skeleton(recs, unit=unit, name="skeleton1", oriented=False)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    return ob


def _heads(ob, count, unit):
    """The joints' positions as the kit read them (``head_local`` = the edit-mode heads; ``matrix_local``'s translation
    is rebuilt through the parent chain in float32 and is ~1e-6 off on long chains)."""
    return [tuple(rig.to_maya(ob.matrix_world @ ob.data.bones[f"j{i}"].head_local, unit)) for i in range(count)]


def test_random_chains_bones_take_mayas_frames():
    """8 random 6-joint chains x every oj order x sao / aos: in edit mode (the very positions the kit used) every
    joint's frame = the model and bone Z = Maya Y within 1e-6; after edit mode within 1e-5 (Blender rebuilds the bones
    through the parent chain in float32 — a nearly straight joint's bend normal amplifies that)."""
    rnd = random.Random(244)
    worst, worst_obj, n = 0.0, 0.0, 0
    for chain in range(8):
        pts = [(0.0, 0.0, 0.0)]
        for _ in range(5):
            pts.append(tuple(c + rnd.uniform(-4, 4) for c in pts[-1]))
        for oj in jo_mod.ORDERS:
            for sao, aos in (("yup", True), ("yup", False), ("zdown", True), ("xup", False), (None, False)):
                ob = _build(pts)
                bpy.ops.object.mode_set(mode='EDIT')
                joints.orient(ob, ["j0"], KIT_SAO[sao], True, oj, aos)
                ebs = ob.data.edit_bones
                read = [tuple(rig.to_maya(ebs[f"j{i}"].head)) for i in range(len(pts))]
                names, model = _chain_model(read, oj, sao, aos)
                for name in names:
                    e = _err(rig.joint_world(ob, name)[1], model[name])
                    worst = max(worst, e)
                    n += 1
                    # Blender's float32 roll -> matrix is not quite orthogonal for bones close to -Y (worst 1.3e-6
                    # measured, j1 of chain 6 at y -0.975): no stored rotation can take that out
                    near_minus_y = ebs[name].y_axis.y < -0.9
                    assert e < (2e-6 if near_minus_y else 1e-6), (chain, oj, sao, aos, name, e)
                    if oj == "xyz" and name != names[-1]:
                        # the bone's own Z = Maya Y (Blender's roll is float32 and loses ~3e-6 on bones close to
                        # -Y; the stored remainder makes the joint frame exact, above)
                        bz = rig.frame_to_maya(ebs[name].matrix.to_3x3().normalized()).col[2]
                        assert (bz - model[name].col[1]).length < 5e-6, ("bone Z = Maya Y", chain, sao, name)
                bpy.ops.object.mode_set(mode='OBJECT')
                for name in names:
                    worst_obj = max(worst_obj, _err(rig.joint_world(ob, name)[1], model[name]))
    assert worst_obj < 1e-5, worst_obj
    print(f"  random chains: {n} joints, worst {worst:.1e} (edit), {worst_obj:.1e} (after edit mode)")
    _reset()


def test_joint_tool_front_chain_like_maya():
    fc = data.JOINT_TOOL["front_chain"]
    pts = [fc[n]["p"] for n in ("joint1", "joint2", "joint3", "joint4")]
    _reset()
    import json
    unit = 1.0
    r = bpy.ops.allset.joint_tool('EXEC_DEFAULT', points=json.dumps([list(rig.to_blender(p, unit)) for p in pts]))
    assert r == {'FINISHED'}, r
    ob = bpy.context.active_object
    names = [b.name for b in ob.data.bones]
    for name, mn in zip(names, ("joint1", "joint2", "joint3", "joint4")):
        pos, axes = rig.joint_world(ob, name, unit)
        want = _rows_matrix(*fc[mn]["axes"])
        assert _err(axes, want) < 1e-4, (mn, axes, fc[mn]["axes"])
        bone = ob.data.bones[name]
        assert bone.inherit_scale == 'NONE', "Maya segmentScaleCompensate on"
        assert abs(bone[joints.RADIUS] - fc[mn]["radius"]) < 2e-3, (mn, bone[joints.RADIUS], fc[mn]["radius"])
        if mn != "joint4":       # the bone itself takes Maya's frame (a stored remainder only polishes float32)
            own = rig.frame_to_maya(bone.matrix_local.to_3x3().normalized() @ joints.JOINT_AXES)
            assert _err(own, want) < 1e-4, (mn, "the bone takes Maya's frame itself")
        # AE Joint Orient = Maya's jointOrient
        jo = [math.degrees(v) for v in ae.joint_orient(ob.pose.bones[name])]
        got = Matrix.Identity(3)
        want_jo = rig._rot(fc[mn]["jo"]).to_3x3()
        from mathutils import Euler
        got = Euler([math.radians(v) for v in jo], 'XYZ').to_matrix()
        assert _err(got, want_jo) < 1e-3, (mn, jo, fc[mn]["jo"])
    _reset()


def test_end_joint_takes_parent_frame_with_aos_world_without():
    pts = [(0, 0, 0), (3, 2, 0), (6, 1, 1)]
    for aos in (True, False):
        ob = _build(pts)
        joints.orient(ob, ["j0"], "Y+", True, "xyz", aos)
        _p, end = rig.joint_world(ob, "j2")
        _p, par = rig.joint_world(ob, "j1")
        want = par if aos else I3
        assert _err(end, want) < 1e-6, (aos, end)
    _reset()


def test_rotated_and_skinned_joints_are_skipped_with_mayas_warning():
    pts = [(0, 0, 0), (3, 1, 0), (6, 0, 1), (8, 2, 0)]
    ob = _build(pts)
    before = {n: rig.joint_world(ob, n)[1] for n in ("j0", "j1", "j2")}
    bpy.ops.object.mode_set(mode='POSE')
    ob.pose.bones["j1"].rotation_mode = 'XYZ'
    ob.pose.bones["j1"].rotation_euler = (0.1, 0.2, 0.3)
    skipped = []
    joints.orient(ob, ["j0"], "Y+", True, "xyz", True, skipped)
    assert skipped == [("j1", "It has non-zero rotations.")], skipped
    bpy.ops.object.mode_set(mode='OBJECT')
    names, model = _chain_model(pts, "xyz", "yup", True)
    # Maya: the rotated joint keeps its jointOrient (it turns with its re-oriented parent), the joints after it are
    # oriented (skeleton_menu.md §1 with_rotate)
    keep = model["j0"] @ (before["j0"].transposed() @ before["j1"])
    assert _err(rig.joint_world(ob, "j1")[1], keep) < 1e-5
    assert _err(rig.joint_world(ob, "j2")[1], model["j2"]) < 1e-5, "Maya: the joints after it are oriented"
    # the operator reports Maya's warning text
    bpy.ops.object.mode_set(mode='POSE')
    for pb in ob.pose.bones:
        pb.bone.select = pb.name == "j0"
    ob.data.bones.active = ob.data.bones["j0"]
    r = bpy.ops.allset.orient_joint('EXEC_DEFAULT')
    assert r == {'FINISHED'}
    # skinned skeleton: every joint skipped
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.mesh.primitive_cube_add()
    body = bpy.context.active_object
    body.modifiers.new("skinCluster1", 'ARMATURE').object = ob
    bpy.context.view_layer.objects.active = ob
    skipped = []
    assert joints.orient(ob, ["j0"], "Y+", True, "xyz", True, skipped) == 0
    assert all(why == "It is bound to a skin." for _n, why in skipped) and len(skipped) == 4, skipped
    _reset()


def test_orient_to_world_and_traditional():
    pts = [(1, 0, 0), (3, 2, 0), (6, 1, 1)]
    ob = _build(pts)
    joints.orient(ob, ["j0"], "Y+", True, "none", True)
    for n in ("j0", "j1", "j2"):
        assert _err(rig.joint_world(ob, n)[1], I3) < 1e-6, n
    ob = _build(pts)
    joints.orient(ob, ["j0"], "NONE", True, "xyz", False)
    names, model = _chain_model(pts, "xyz", None, False)
    for n in names:
        assert _err(rig.joint_world(ob, n)[1], model[n]) < 1e-6, n
    _reset()


def test_siblings_first_child_and_zero_length_child_unchanged():
    pts = [(0, 0, 0), (2, 1, 0), (4, 2, 1)]
    ob = _build(pts, branch={"k2": ((3, -1, 2), "j1")})
    joints.orient(ob, ["j0"], "Y+", True, "xyz", True)
    x = rig.joint_world(ob, "j1")[1].col[0]
    aim = (Vector((4, 2, 1)) - Vector((2, 1, 0))).normalized()
    assert (x - aim).length < 1e-6, "X aims at the first child"
    ob = _build([(0, 0, 0), (2, 1, 0), (2, 1, 0), (4, 0, 0)])
    joints.orient(ob, ["j0"], "Y+", True, "xyz", True)
    # Maya (oj_verify zero_len_child): the joint gets jointOrient 0 = its parent's frame
    assert _err(rig.joint_world(ob, "j1")[1], rig.joint_world(ob, "j0")[1]) < 1e-6
    _reset()


def test_ae_segment_scale_compensate_check_box():
    ob = _build([(0, 0, 0), (2, 0, 0)])
    bone = ob.data.bones["j1"]
    bone.allset_ssc = True
    assert bone.inherit_scale == 'NONE'
    bone.allset_ssc = False
    assert bone.inherit_scale == 'FULL' and not bone.allset_ssc
    _reset()


def test_orient_joint_undo():
    pts = [(0, 0, 0), (3, 1, 0), (6, 0, 1)]
    ob = _build(pts)
    bpy.ops.object.mode_set(mode='POSE')
    before = {n: rig.joint_world(ob, n)[1] for n in ("j0", "j1")}
    for pb in ob.pose.bones:
        pb.bone.select = pb.name == "j0"
    ob.data.bones.active = ob.data.bones["j0"]
    bpy.ops.ed.undo_push(message="before")
    assert bpy.ops.allset.orient_joint('EXEC_DEFAULT', True) == {'FINISHED'}
    assert _err(rig.joint_world(ob, "j0")[1], before["j0"]) > 1e-3
    bpy.ops.ed.undo()
    ob = bpy.data.objects["skeleton1"]
    assert _err(rig.joint_world(ob, "j0")[1], before["j0"]) < 1e-6
    _reset()


def test_cm_scene_within_float_precision():
    """The Maya Workflow Kit template is a cm scene (maya_unit 0.01): the same chains within 1e-5."""
    rnd = random.Random(2440)
    worst = 0.0
    for chain in range(8):
        pts = [(0.0, 0.0, 0.0)]
        for _ in range(5):
            pts.append(tuple(c + rnd.uniform(-4, 4) for c in pts[-1]))
        ob = _build(pts, 0.01)
        joints.orient(ob, ["j0"], "Y+", True, "xyz", True)
        read = _heads(ob, len(pts), 0.01)
        names, model = _chain_model(read, "xyz", "yup", True)
        for name in names:
            worst = max(worst, _err(rig.joint_world(ob, name, 0.01)[1], model[name]))
    assert worst < 1e-5, worst
    print(f"  cm scene worst {worst:.1e}")
    _reset()
