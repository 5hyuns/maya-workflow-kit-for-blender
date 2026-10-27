"""Step 246 (Issue #163): Skeleton menu commands with Maya's meaning.

Maya 2026 numbers: tests/maya2026_rig_data.py SKELETON_MENU["skeleton"] (insert_joint, remove_disconnect_connect_reroot,
mirror_joint; research/maya/re/joint_rig_2026_skeleton_menu.md §2-7) and the mayapy runs of docs/steps/step_246.md
「측정」 (skinned remove / insert / disconnect, root-only connect, connect under a turned parent) written here as literals.
Kit: operators/skeleton_menu.py, joints.mirror (factory XY, rotate values copied).
"""

import json
import math
from importlib import import_module

import bpy
from mathutils import Euler, Vector

import kit
import maya2026_rig as rig
import maya2026_rig_data as data

sm = import_module(kit.MODULE + ".operators.skeleton_menu")
joints = import_module(kit.MODULE + ".operators.joints")
joint_edit = import_module(kit.MODULE + ".operators.joint_edit")
menu_map = import_module(kit.MODULE + ".ui.menu_map")

SK = data.SKELETON_MENU["skeleton"]
RDC = SK["remove_disconnect_connect_reroot"]
TOL = 2e-4          # fixture values are rounded to 4 decimals
AX_TOL = 2e-4

# the oriented chain the remove / disconnect / reroot cases start from (jointOrient worked back from the "after"
# records: disconnect_j3 joint5 = joint3's old place under joint2, remove_j2 joint4 unchanged)
CHAIN4 = {
    "joint1": {"t": [0, 0, 0], "jo": [0, 0, 18.4349], "parent": None},
    "joint2": {"t": [3.1623, 0, 0], "jo": [0, 0, -36.8699], "parent": "joint1"},
    "joint3": {"t": [3.1623, 0, 0], "jo": [0, 0, 36.8699], "parent": "joint2"},
    "joint4": {"t": [3.1623, 0, 0], "jo": [0, 0, -18.4349], "parent": "joint3"},
}


def _reset():
    if bpy.context.object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for arm in list(bpy.data.armatures):
        bpy.data.armatures.remove(arm)
    bpy.context.scene.tool_settings.use_transform_skip_children = False
    joint_edit.rebase()


def _rec(r):
    return {k: v for k, v in r.items() if k in ("t", "jo", "r", "ra", "s", "parent")}


def _build(records, name="skeleton1", mode='POSE', reset=True, unit=1.0):
    if reset:
        _reset()
    elif bpy.context.object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    rest = {n: dict(_rec(r), r=[0, 0, 0]) for n, r in records.items()}
    ob = rig.build_skeleton(rest, unit=unit, name=name)
    for o in bpy.context.selected_objects:
        o.select_set(False)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode=mode)
    if mode == 'POSE':
        for pb in ob.pose.bones:
            pb.rotation_mode = 'XYZ'
    return ob


def _select(ob, names, active=None):
    cbm = joints._cb()
    if ob.mode == 'EDIT':
        from importlib import import_module as im
        js = im(kit.MODULE + ".operators.joint_selection")
        for eb in ob.data.edit_bones:
            js._set_edit(eb, False)
        for n in names:
            js._pick_shape(ob.data.edit_bones[n], True, False)
        ob.data.edit_bones.active = ob.data.edit_bones[active or names[-1]]
        return
    for pb in ob.pose.bones:
        cbm.set_bone_selected(pb, pb.name in names)
    ob.data.bones.active = ob.data.bones[active or names[-1]]


def _parent(ob, name):
    b = ob.data.edit_bones[name] if ob.mode == 'EDIT' else ob.data.bones[name]
    return b.parent.name if b.parent is not None else None


def _expect(records):
    worlds = rig.world_matrices({n: _rec(r) for n, r in records.items()})
    return {n: (m.to_translation(), m.to_3x3().normalized()) for n, m in worlds.items()}


def _check(ob, records, label, unit=1.0):
    want = _expect(records)
    for n, (p, ax) in want.items():
        got_p, got_ax = rig.joint_world(ob, n, unit)
        assert (got_p - p).length < TOL, f"{label}: {n} at {tuple(got_p)}, Maya {tuple(p)}"
        err = max((got_ax.col[i] - ax.col[i]).length for i in range(3))
        assert err < AX_TOL, f"{label}: {n} Maya axes off by {err:.2e}"
        assert _parent(ob, n) == records[n]["parent"], f"{label}: {n} parent {_parent(ob, n)}, Maya {records[n]['parent']}"


def _op(name, **kw):
    return getattr(bpy.ops.allset, name)('EXEC_DEFAULT', True, **kw)


# --- menu ---------------------------------------------------------------------------------------------

def test_menu_items_run_the_maya_commands():
    m = menu_map.MAP
    assert m["Skeleton/Insert Joints"] == "allset.insert_joint_tool"
    assert m["Skeleton/Remove Joints"] == "allset.remove_joint"
    assert m["Skeleton/Disconnect Joint"] == "allset.disconnect_joint"
    assert m["Skeleton/Connect Joint"] == "allset.connect_joint"
    for op in ("insert_joint_tool", "remove_joint", "disconnect_joint", "connect_joint"):
        assert hasattr(bpy.types, "ALLSET_OT_" + op), op


# --- Insert Joint ---------------------------------------------------------------------------------------

def _insert_before():
    after = SK["insert_joint"]["after"]
    recs = {n: dict(after[n]) for n in ("joint1", "joint2", "joint3")}
    recs["joint2"]["parent"] = "joint1"
    return recs


def test_insert_joint_matches_maya():
    for mode in ('POSE', 'EDIT'):
        ob = _build(_insert_before(), mode=mode)
        assert _op("insert_joint_tool", joint="joint1") == {'FINISHED'}
        case = SK["insert_joint"]
        bones = ob.data.edit_bones if ob.mode == 'EDIT' else ob.data.bones
        assert case["returned"] == "joint4" and "joint4" in bones
        want = dict(case["after"], joint4=case["new"])
        _check(ob, want, f"insert ({mode})")
        assert [c.name for c in bones["joint1"].children] == case["children_j1"]
        assert [c.name for c in bones["joint4"].children] == case["children_new"]
        # an end joint takes one too (on_end_joint: joint5 under joint3, at joint3)
        assert _op("insert_joint_tool", joint="joint3") == {'FINISHED'}
        end = case["on_end_joint"]
        assert end["returned"] == "joint5" and _parent(ob, "joint5") == "joint3"
        p, ax = rig.joint_world(ob, "joint5")
        assert (p - Vector(end["new"]["w"])).length < TOL
        p3, ax3 = rig.joint_world(ob, "joint3")
        assert max((ax.col[i] - ax3.col[i]).length for i in range(3)) < AX_TOL, "jointOrient 0 = joint3's frame"


def test_insert_joint_drag_moves_only_the_new_joint():
    ob = _build(_insert_before())
    before = {n: rig.joint_world(ob, n) for n in ("joint1", "joint2", "joint3")}
    target = rig.to_blender((2.0, 1.5, 0.0))
    assert _op("insert_joint_tool", joint="joint1", point=json.dumps(list(target))) == {'FINISHED'}
    p, ax = rig.joint_world(ob, "joint4")
    assert (p - Vector((2.0, 1.5, 0.0))).length < 1e-5, p
    for n, (bp, bax) in before.items():
        gp, gax = rig.joint_world(ob, n)
        assert (gp - bp).length < 1e-5, f"{n} moved"
        assert max((gax.col[i] - bax.col[i]).length for i in range(3)) < AX_TOL, f"{n} Maya frame changed"
    assert max((ax.col[i] - before["joint1"][1].col[i]).length for i in range(3)) < AX_TOL, "new joint = joint1 frame"
    b1 = ob.data.bones["joint1"]
    assert (b1.tail_local - ob.data.bones["joint4"].head_local).length < 1e-5, "joint1 now draws to the new joint"


# --- Remove Joint ---------------------------------------------------------------------------------------

def test_remove_joint_matches_maya():
    for mode in ('POSE', 'EDIT'):
        ob = _build(CHAIN4, mode=mode)
        _check(ob, CHAIN4, "chain before")
        case = RDC["remove_j2"]
        for n, w in case["world_before"].items():
            assert (rig.joint_world(ob, n)[0] - Vector(w)).length < TOL
        _select(ob, ["joint2"])
        assert _op("remove_joint") == {'FINISHED'}
        bones = ob.data.edit_bones if ob.mode == 'EDIT' else ob.data.bones
        assert "joint2" not in bones and not case["exists"]
        _check(ob, case["after"], f"remove ({mode})")


def _skin(ob):
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(4.5, 0.0, 0.5))
    cube = bpy.context.active_object
    cube.scale = (10.0, 1.0, 1.0)
    bpy.ops.object.transform_apply(scale=True)
    md = cube.modifiers.new("skinCluster1", 'ARMATURE')
    md.object = ob
    for i, n in enumerate(("joint1", "joint2", "joint3", "joint4")):
        vg = cube.vertex_groups.new(name=n)
        for v in cube.data.vertices:
            vg.add([v.index], 0.1 * (i + 1), 'REPLACE')
    for o in bpy.context.selected_objects:
        o.select_set(False)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode='POSE')
    return cube


def test_remove_skinned_joint_drops_only_its_influence():
    # mayapy 2026 (step_246.md 「측정」): joint2's influence leaves, the rest stay as they were (0.017 + 0.034 = 0.051
    # is left unnormalised), the mesh doesn't move
    ob = _build(CHAIN4)
    cube = _skin(ob)
    _select(ob, ["joint2"])
    assert _op("remove_joint") == {'FINISHED'}
    assert [g.name for g in cube.vertex_groups] == ["joint1", "joint3", "joint4"]
    v = cube.data.vertices[0]
    w = {cube.vertex_groups[g.group].name: round(g.weight, 6) for g in v.groups}
    assert w == {"joint1": 0.1, "joint3": 0.3, "joint4": 0.4}, w


def test_remove_undo():
    ob = _build(CHAIN4)
    bpy.ops.ed.undo_push(message="start")
    _select(ob, ["joint2"])
    assert _op("remove_joint") == {'FINISHED'}
    assert "joint2" not in ob.data.bones
    bpy.ops.ed.undo()
    ob = bpy.data.objects["skeleton1"]
    assert "joint2" in ob.data.bones and ob.data.bones["joint3"].parent.name == "joint2"


# --- Disconnect Joint -----------------------------------------------------------------------------------

def test_disconnect_joint_matches_maya():
    for mode in ('POSE', 'EDIT'):
        ob = _build(CHAIN4, mode=mode)
        _select(ob, ["joint3"])
        assert _op("disconnect_joint") == {'FINISHED'}
        case = RDC["disconnect_j3"]
        _check(ob, case["attrs"], f"disconnect ({mode})")
        assert sm.picked(ob) == case["selection"], sm.picked(ob)


def test_disconnect_root_is_refused():
    ob = _build(CHAIN4)
    _select(ob, ["joint1"])
    assert _op("disconnect_joint") == {'CANCELLED'}
    assert len(ob.data.bones) == 4


# --- Connect Joint --------------------------------------------------------------------------------------

def _connect_before():
    a = RDC["connect_cm"]["attrs"]
    return {"a1": _rec(a["a1"]), "a2": _rec(a["a2"]),
            "b1": {"t": RDC["connect_cm"]["world_before_b"]["b1"], "jo": [0, 0, 10], "parent": None},
            "b2": {"t": [3, 0, 0], "jo": [0, 0, 0], "parent": "b1"}}


def _connect_two_skeletons(mode):
    recs = _connect_before()
    a = _build({n: recs[n] for n in ("a1", "a2")}, name="skeletonA", mode='OBJECT')
    b = _build({n: recs[n] for n in ("b1", "b2")}, name="skeletonB", mode='OBJECT', reset=False)
    for o in (a, b):
        o.select_set(True)
    bpy.context.view_layer.objects.active = a
    bpy.ops.object.mode_set(mode=mode)
    cbm = joints._cb()
    if mode == 'POSE':
        for o in (a, b):
            for pb in o.pose.bones:
                cbm.set_bone_selected(pb, pb.name in ("b1", "a2"))
        a.data.bones.active = a.data.bones["a2"]
    else:
        js = import_module(kit.MODULE + ".operators.joint_selection")
        for o in (a, b):
            for eb in o.data.edit_bones:
                js._set_edit(eb, False)
        js._pick_shape(b.data.edit_bones["b1"], True, False)
        js._pick_shape(a.data.edit_bones["a2"], True, False)
        a.data.edit_bones.active = a.data.edit_bones["a2"]
    return a


def test_connect_joint_matches_maya_both_modes():
    for key, mode in (("connect_cm", "CONNECT"), ("connect_pm", "PARENT")):
        ob = _build(_connect_before())
        _check(ob, _connect_before(), "connect before")
        _select(ob, ["b1", "a2"], active="a2")
        assert _op("connect_joint", mode=mode) == {'FINISHED'}
        _check(ob, RDC[key]["attrs"], key)


def test_connect_joins_two_skeletons():
    for ob_mode in ('POSE', 'EDIT'):
        a = _connect_two_skeletons(ob_mode)
        assert _op("connect_joint", mode="CONNECT") == {'FINISHED'}
        assert "skeletonB" not in bpy.data.objects, "the second skeleton joined the first"
        _check(a, RDC["connect_cm"]["attrs"], f"connect across skeletons ({ob_mode})")


def test_connect_needs_a_root():
    ob = _build(_connect_before())
    _select(ob, ["b2", "a2"], active="a2")
    try:
        res = _op("connect_joint", mode="CONNECT")
    except RuntimeError as ex:
        assert sm.ROOT_ERROR in str(ex)
    else:
        assert res == {'CANCELLED'}
    assert _parent(ob, "b1") is None and _parent(ob, "b2") == "b1"


def test_connect_under_turned_parent_keeps_world_frames():
    # mayapy 2026 (step_246.md 「측정」 conn2 rot_parent): a1 at (1, 1, 0) jo z 30; b1 (5, 2, 0) -> a2's place
    # (3.598, 2.5, 0) with its world frame (identity, jo -30), b2 follows (6.598, 3.5, 0)
    recs = {"a1": {"t": [1, 1, 0], "jo": [0, 0, 30], "parent": None}, "a2": {"t": [3, 0, 0], "parent": "a1"},
            "b1": {"t": [5, 2, 0], "parent": None}, "b2": {"t": [3, 1, 0], "parent": "b1"}}
    ob = _build(recs)
    _select(ob, ["b1", "a2"], active="a2")
    assert _op("connect_joint", mode="CONNECT") == {'FINISHED'}
    p1, ax1 = rig.joint_world(ob, "b1")
    p2, _ = rig.joint_world(ob, "b2")
    assert (p1 - Vector((3.598076, 2.5, 0.0))).length < 1e-5 and (p2 - Vector((6.598076, 3.5, 0.0))).length < 1e-5
    assert max((ax1.col[i] - Vector([1.0 if i == j else 0.0 for j in range(3)])).length for i in range(3)) < 1e-5
    assert _parent(ob, "b1") == "a1"


# --- Mirror Joints --------------------------------------------------------------------------------------

def _set_maya_rotate(ob, name, deg):
    pb = ob.pose.bones[name]
    a = joints._maya_axes(pb.bone)
    r_m = Euler([math.radians(x) for x in deg], 'XYZ').to_matrix()
    pb.rotation_mode = 'XYZ'
    pb.rotation_euler = (a @ r_m @ a.transposed()).to_euler('XYZ')


def _maya_rotate(ob, name):
    """Maya rotate X / Y / Z (degrees) of a pose bone: its rotation in the joint's own Maya axes."""
    pb = ob.pose.bones[name]
    a = joints._maya_axes(pb.bone)
    return [math.degrees(x) for x in (a.transposed() @ pb.matrix_basis.to_3x3() @ a).to_euler('XYZ')]


def _posed(ob, name):
    pb = ob.pose.bones[name]
    m = ob.matrix_world @ pb.matrix
    ax = m.to_3x3().normalized() @ joints._maya_axes(pb.bone)
    return rig.to_maya(m.to_translation()), rig.frame_to_maya(ax)


def _mirror_case(key, plane, function, **names):
    case = SK["mirror_joint"][key]
    src = {n: _rec(v["att"]) for n, v in case["src"].items()}
    ob = _build(src)
    for n, v in case["src"].items():
        if any(abs(x) > 1e-9 for x in v["att"]["r"]):
            _set_maya_rotate(ob, n, v["att"]["r"])
    bpy.context.view_layer.update()
    for n, v in case["src"].items():
        p, _ = _posed(ob, n)
        assert (p - Vector(v["att"]["w"])).length < TOL, f"source {n} posed at {tuple(p)}"
    _select(ob, [next(iter(case["src"]))])
    args = dict(function=function, **names)
    if plane:
        args["plane"] = plane
    assert _op("mirror_joints", **args) == {'FINISHED'}
    bpy.context.view_layer.update()
    for n, v in case["dst"].items():
        assert n in ob.pose.bones, f"{n} not made ({[b.name for b in ob.pose.bones]})"
        p, ax = _posed(ob, n)
        assert (p - Vector(v["att"]["w"])).length < TOL, f"{key}: {n} at {tuple(p)}, Maya {v['att']['w']}"
        err = max((ax.col[i] - Vector(v["axes"][i])).length for i in range(3))
        assert err < 2e-4, f"{key}: {n} axes off by {err:.2e}"
        assert ob.data.bones[n].parent is None if v["att"]["parent"] is None \
            else ob.data.bones[n].parent.name == v["att"]["parent"]
    return ob


def test_mirror_factory_plane_is_xy_and_copies_rotate():
    assert bpy.ops.allset.mirror_joints.get_rna_type().properties["plane"].default == "XY"
    ob = _mirror_case("XY_behavior_factory", None, "BEHAVIOR")
    r = [_maya_rotate(ob, n) for n in ("L_b", "L_b1")]
    assert all(abs(a - b) < 1e-3 for a, b in zip(*r)) and abs(r[0][1] - 20.0) < 1e-3, r   # Channel Box values


def test_mirror_yz_behavior_and_orientation_copy_rotate():
    _mirror_case("YZ_behavior", "YZ", "BEHAVIOR", search="L_", replace="R_")
    _mirror_case("YZ_orientation", "YZ", "ORIENTATION", search="L_", replace="R_")
