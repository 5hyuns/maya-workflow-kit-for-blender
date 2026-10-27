"""Step 247 (Issue #164): skin basics with Maya's meaning.

Maya 2026 numbers: tests/maya2026_rig_data.py SKINNING["skin"] (prune_and_max, unbind_and_bind_pose, copy_mirror_weights)
and the mayapy runs of docs/steps/step_247.md / research/maya/re/skin_basics_247.md, written here as literals:
prune with a locked joint, Set Max Influences (recomputed by distance), Go to Bind Pose, Mirror Skin Weights barycentric,
Closest in hierarchy rows (mayapy bind_hier2: Maya's own weights of three vertices).
Kit: operators/skin_basics.py, skin.py (bind options, mirror, closest_distance_weights).
"""

from importlib import import_module

import bpy
import numpy as np
from mathutils import Vector

import kit
import maya2026_rig_data as data

skin = import_module(kit.MODULE + ".operators.skin")
sb = import_module(kit.MODULE + ".operators.skin_basics")
rig_maya = import_module(kit.MODULE + ".operators.rig_maya")
menu_map = import_module(kit.MODULE + ".ui.menu_map")

SK = data.SKINNING["skin"]


def _reset():
    if bpy.context.object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for coll in (bpy.data.meshes, bpy.data.armatures):
        for d in list(coll):
            coll.remove(d)


def _b(p):
    """Maya point -> Blender world (x, -z, y), unit 1."""
    return Vector((p[0], -p[2], p[1]))


def _skeleton(joints, name="skeleton1"):
    """joints = [(name, maya point, parent)]; bones head = the point, tail toward the first child."""
    arm = bpy.data.armatures.new(name)
    ob = bpy.data.objects.new(name, arm)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT')
    pos = {n: _b(p) for n, p, _ in joints}
    for n, p, parent in joints:
        eb = arm.edit_bones.new(n)
        eb.head = pos[n]
        kids = [c for c, _q, par in joints if par == n]
        eb.tail = pos[kids[0]] if kids else pos[n] + Vector((0.0, 0.0, 0.5))
        if parent:
            eb.parent = arm.edit_bones[parent]
    bpy.ops.object.mode_set(mode='OBJECT')
    return ob


def _mesh(points, faces, name="body"):
    me = bpy.data.meshes.new(name)
    me.from_pydata([_b(p) for p in points], [], faces)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def _skin(mesh, arm, names):
    md = mesh.modifiers.new("skinCluster1", 'ARMATURE')
    md.object = arm
    for n in names:
        mesh.vertex_groups.new(name=n)


def _set(mesh, i, ws):
    for name, w in ws.items():
        vg = mesh.vertex_groups[name]
        if w > 0:
            vg.add([i], w, 'REPLACE')
        else:
            vg.remove([i])


def _get(mesh, i, names):
    out = []
    for n in names:
        vg = mesh.vertex_groups[n]
        try:
            out.append(vg.weight(i))
        except RuntimeError:
            out.append(0.0)
    return out


def _close(a, b, tol=1e-5):
    return all(abs(x - y) < tol for x, y in zip(a, b))


def _select(*obs, active=None):
    for o in bpy.context.selected_objects:
        o.select_set(False)
    for o in obs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = active or obs[-1]


CHAIN = [("joint1", (0, 0, 0), None), ("joint2", (3, 0, 0), "joint1"), ("joint3", (6, 0, 0), "joint2"),
         ("joint4", (9, 0, 0), "joint3")]
J = [n for n, _p, _q in CHAIN]


def _chain_skin():
    """Joints at Maya x 0 / 3 / 6 / 9; vertex 0 = Maya (0, 0, 0.5) like the mayapy plane's vertex 0."""
    _reset()
    arm = _skeleton(CHAIN)
    mesh = _mesh([(0, 0, 0.5), (9, 0, 0.5), (9, 0, -0.5)], [(0, 1, 2)])
    _skin(mesh, arm, J)
    return arm, mesh


# --- menu ---------------------------------------------------------------------------------------------------

def test_menu_items():
    m = menu_map.MAP
    assert m["Skin/Prune Small Weights"] == "allset.prune_small_weights"
    assert m["Skin/Go to Bind Pose"] == "allset.go_to_bind_pose"
    assert m["Skin/Edit Influences/Set Max Influences..."] == "allset.set_max_influences"


# --- Prune Small Weights ----------------------------------------------------------------------------------------

def test_prune_matrix_maya_rows():
    ex = SK["prune_and_max"]
    out, ch = sb.prune_matrix([ex["example_before"]], [False] * 4)
    assert _close(out[0], ex["example_after"]) and ch[0]
    # mayapy 2026 (skin_basics_247.md): unlocked rescaled, a locked small weight stays (vertex unchanged)
    out, _ = sb.prune_matrix([[0.6, 0.005, 0.3, 0.095]], [False] * 4)
    assert _close(out[0], [0.603015, 0.0, 0.301508, 0.095477], 1e-6), out
    out, ch = sb.prune_matrix([[0.6, 0.005, 0.3, 0.095]], [False, True, False, False])
    assert _close(out[0], [0.6, 0.005, 0.3, 0.095]) and not ch[0]


def test_prune_operator_whole_mesh_and_selected_vertices():
    arm, mesh = _chain_skin()
    for i in range(3):
        _set(mesh, i, dict(zip(J, [0.6, 0.005, 0.3, 0.095])))
    _select(mesh)
    assert bpy.ops.allset.prune_small_weights('EXEC_DEFAULT') == {'FINISHED'}
    for i in range(3):
        assert _close(_get(mesh, i, J), [0.603015, 0.0, 0.301508, 0.095477], 1e-6)
        assert all(g.weight > 0 for g in mesh.data.vertices[i].groups), "pruned weights leave the group"
    # filterSelected: only the selected vertex in Edit mode
    for i in range(3):
        _set(mesh, i, dict(zip(J, [0.6, 0.005, 0.3, 0.095])))
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    mesh.data.vertices[0].select = True
    bpy.ops.object.mode_set(mode='EDIT')
    assert bpy.ops.allset.prune_small_weights('EXEC_DEFAULT') == {'FINISHED'}
    bpy.ops.object.mode_set(mode='OBJECT')
    assert _close(_get(mesh, 0, J), [0.603015, 0.0, 0.301508, 0.095477], 1e-6)
    assert _close(_get(mesh, 1, J), [0.6, 0.005, 0.3, 0.095])


def test_prune_threshold_option():
    arm, mesh = _chain_skin()
    _set(mesh, 0, dict(zip(J, [0.6, 0.05, 0.3, 0.05])))
    _select(mesh)
    assert bpy.ops.allset.prune_small_weights('EXEC_DEFAULT', below=0.1) == {'FINISHED'}
    assert _close(_get(mesh, 0, J), [2 / 3, 0.0, 1 / 3, 0.0])


# --- Set Max Influences / Maintain max influences -----------------------------------------------------------------

def test_set_max_influences_recomputes_like_maya():
    for lock, want in ((False, [0.99927, 0.00073, 0.0, 0.0]), (True, [0.9, 0.0, 0.1, 0.0])):
        arm, mesh = _chain_skin()
        _set(mesh, 0, dict(zip(J, [0.4, 0.3, 0.1, 0.2])))
        mesh.vertex_groups["joint3"].lock_weight = lock
        _select(mesh)
        assert bpy.ops.allset.set_max_influences('EXEC_DEFAULT', max_influences=2) == {'FINISHED'}
        got = _get(mesh, 0, J)
        assert _close(got, want, 1e-5), (lock, got)
        assert mesh[rig_maya.MAX_INFLUENCES_PROP] == 2


def test_enforce_max_rule():
    # Maya 2026, measured with mayapy: smallest first, locked last, rest renormalised
    out = sb.enforce_max_matrix([[0.4, 0.3, 0.1, 0.2]], [False] * 4, 2)
    assert _close(out[0], [0.4 / 0.7, 0.3 / 0.7, 0.0, 0.0])
    out = sb.enforce_max_matrix([[0.4, 0.3, 0.1, 0.2]], [False, False, True, False], 2)
    assert _close(out[0], [0.9, 0.0, 0.1, 0.0])


# --- Bind Skin options ---------------------------------------------------------------------------------------

def test_on_joint_distance_is_1e4():
    segs = {"a": [(Vector((0, 0, 0)), Vector((0, 0, 0)))], "b": [(Vector((1, 0, 0)), Vector((1, 0, 0)))]}
    names, w = skin.closest_distance_weights([(5e-5, 0, 0)], segs)
    assert _close(w[0], [1.0, 0.0])
    names, w = skin.closest_distance_weights([(2e-4, 0, 0)], segs)
    assert w[0][0] < 1.0


HIER = [("hips", (0, 0, 0), None), ("spine", (0, 3, 0), "hips"), ("chest", (0, 6, 0), "spine"),
        ("head", (0, 9, 0), "chest"), ("lArm", (3, 6, 0), "chest"), ("lHand", (6, 6.5, 0), "lArm"),
        ("rArm", (-3, 6, 0), "chest"), ("rHand", (-6, 5.5, 0), "rArm"), ("lLeg", (2, -4, 0), "hips"),
        ("lFoot", (2, -8, 1), "lLeg")]


def test_closest_in_hierarchy_matches_maya_rows():
    # mayapy bind_hier2 (private measurement): Maya's weights (4 decimals) of three
    # vertices of a 16 x 20 plane (vertex i at Maya (-8 + i % 17, -10 + i // 17, 0.5), mayapy)
    names = [n for n, _p, _q in HIER]
    pos = {n: np.array(p, dtype=float) for n, p, _q in HIER}
    kids = {n: [c for c, _p, par in HIER if par == n] for n in names}
    segs = {n: [(pos[n], pos[c]) for c in kids[n]] or [(pos[n], pos[n])] for n in names}
    hier = {n: (par, kids[n]) for n, _p, par in HIER}
    rows = {2: (44, [0, 0, 0, 0, 0, 0, 0, 0, 0.5303, 0.4697]),
            3: (122, [0.5655, 0.1748, 0, 0, 0, 0, 0, 0, 0.2597, 0]),
            5: (311, [0, 0.0438, 0.4255, 0.0732, 0, 0, 0.4255, 0.032, 0, 0])}
    for mi, (i, want) in rows.items():
        p = (-8 + i % 17, -10 + i // 17, 0.5)
        got_names, w = skin.closest_distance_weights([p], segs, 4.0, mi, hier)
        assert got_names == names
        assert _close(w[0], want, 6e-5), (mi, [round(x, 4) for x in w[0]])
    plane = [(-8 + i % 17, -10 + i // 17, 0.5) for i in range(357)]
    _n, wd = skin.closest_distance_weights(plane, segs, 4.0, 3)
    _n, wh = skin.closest_distance_weights(plane, segs, 4.0, 3, hier)
    assert np.abs(wd - wh).max() > 0.05, "Closest in hierarchy is a different rule from Closest distance"


def test_bind_options_dropoff_skinning_maintain():
    _reset()
    arm = _skeleton(CHAIN)
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(4.5, 0, 0.5))
    mesh = bpy.context.active_object
    mesh.scale = (9.0, 1.0, 1.0)
    bpy.ops.object.transform_apply(scale=True)
    _select(arm, mesh)
    assert bpy.ops.allset.bind_skin('EXEC_DEFAULT', dropoff=2.0, skinning='DUAL_QUATERNION') == {'FINISHED'}
    md = skin.armature_modifier(mesh)
    assert md.use_deform_preserve_volume, "Dual quaternion = Blender Preserve Volume"
    assert mesh[sb.MAINTAIN_MAX] is True and mesh[rig_maya.MAX_INFLUENCES_PROP] == 5
    assert set(mesh[rig_maya.DROPOFF_PROP].keys()) == set(J) and mesh[rig_maya.DROPOFF_PROP]["joint1"] == 2.0
    co = np.array([mesh.matrix_world @ v.co for v in mesh.data.vertices])
    segs = skin.joint_segments(arm)
    names, w2 = skin.closest_distance_weights(co, segs, 2.0, 5)
    for i in range(len(co)):
        assert _close(_get(mesh, i, names), w2[i], 1e-5)
    assert "allset_bind_pose" in arm


# --- Go to Bind Pose ---------------------------------------------------------------------------------------

def test_go_to_bind_pose_restores_every_joint():
    _reset()
    arm = _skeleton(CHAIN)
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(4.5, 0, 0.5))
    mesh = bpy.context.active_object
    mesh.scale = (9.0, 1.0, 1.0)
    bpy.ops.object.transform_apply(scale=True)
    _select(arm, mesh)
    assert bpy.ops.allset.bind_skin('EXEC_DEFAULT') == {'FINISHED'}
    dg = bpy.context.evaluated_depsgraph_get()
    base = [v.co.copy() for v in mesh.evaluated_get(dg).to_mesh().vertices]
    mesh.evaluated_get(dg).to_mesh_clear()
    pb = arm.pose.bones
    pb["joint2"].rotation_mode = 'XYZ'
    pb["joint2"].rotation_euler = (0.0, 0.7, 0.0)
    pb["joint1"].rotation_mode = 'XYZ'
    pb["joint1"].rotation_euler = (0.0, 0.0, 0.17)
    pb["joint3"].location = (0.0, 4.0, 0.0)
    _select(mesh)
    assert bpy.ops.allset.go_to_bind_pose('EXEC_DEFAULT') == {'FINISHED'}
    dg = bpy.context.evaluated_depsgraph_get()
    after = [v.co.copy() for v in mesh.evaluated_get(dg).to_mesh().vertices]
    mesh.evaluated_get(dg).to_mesh_clear()
    err = max((a - b).length for a, b in zip(base, after))
    assert err < 1e-6, err   # fixture after_goto_mesh_err 0.0
    assert all(p.matrix_basis == p.matrix_basis.Identity(4) for p in pb)


def test_bind_pose_is_the_pose_at_bind_and_follows_remove_and_unbind():
    # mayapy: a skeleton bound with joint2 rz 30 goes back to rz 30
    _reset()
    arm = _skeleton(CHAIN)
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(4.5, 0, 0.5))
    mesh = bpy.context.active_object
    pb = arm.pose.bones["joint2"]
    pb.rotation_mode = 'XYZ'
    pb.rotation_euler = (0.0, 0.5236, 0.0)
    _select(arm, mesh)
    assert bpy.ops.allset.bind_skin('EXEC_DEFAULT') == {'FINISHED'}
    pb.rotation_euler = (0.0, 0.0, 0.0)
    _select(arm)
    assert bpy.ops.allset.go_to_bind_pose('EXEC_DEFAULT') == {'FINISHED'}
    assert abs(pb.rotation_euler[1] - 0.5236) < 1e-5
    # Remove Joint drops the member (step 246 + 247)
    bpy.ops.object.mode_set(mode='POSE')
    cbm = import_module(kit.MODULE + ".ui.channel_box")
    for p in arm.pose.bones:
        cbm.set_bone_selected(p, p.name == "joint4")
    arm.data.bones.active = arm.data.bones["joint4"]
    assert bpy.ops.allset.remove_joint('EXEC_DEFAULT') == {'FINISHED'}
    assert "joint4" not in arm["allset_bind_pose"] and "joint4" not in mesh.vertex_groups
    bpy.ops.object.mode_set(mode='OBJECT')
    _select(mesh)
    assert bpy.ops.allset.unbind_skin('EXEC_DEFAULT') == {'FINISHED'}
    assert "allset_bind_pose" not in arm, "Unbind deletes the bind pose"


def test_go_to_bind_pose_undo():
    _reset()
    arm = _skeleton(CHAIN)
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(4.5, 0, 0.5))
    mesh = bpy.context.active_object
    _select(arm, mesh)
    bpy.ops.allset.bind_skin('EXEC_DEFAULT')
    arm.pose.bones["joint2"].location = (0.0, 1.0, 0.0)
    bpy.ops.ed.undo_push(message="posed")
    _select(arm)
    assert bpy.ops.allset.go_to_bind_pose('EXEC_DEFAULT', True) == {'FINISHED'}
    assert tuple(bpy.data.objects["skeleton1"].pose.bones["joint2"].location) == (0.0, 0.0, 0.0)
    bpy.ops.ed.undo()
    assert tuple(bpy.data.objects["skeleton1"].pose.bones["joint2"].location) == (0.0, 1.0, 0.0)


# --- Mirror / Copy Skin Weights ---------------------------------------------------------------------------

MIRROR_XS = [-4, -3, -2.5, -1.5, -0.5, 0, 1, 4]


def test_mirror_skin_weights_barycentric_like_maya():
    _reset()
    arm = _skeleton([("C", (0, 0, 0), None), ("L_a", (4, 0, 0), "C"), ("R_a", (-4, 0, 0), "C")])
    pts = [(x, 0, z) for x in MIRROR_XS for z in (0, 1)]
    faces = [(2 * i, 2 * (i + 1), 2 * (i + 1) + 1, 2 * i + 1) for i in range(len(MIRROR_XS) - 1)]
    mesh = _mesh(pts, faces)
    names = ["C", "L_a", "R_a"]
    _skin(mesh, arm, names)
    src = {0: [1.0, 0.0, 0.0], 1: [0.6, 0.4, 0.0], 4: [0.0, 1.0, 0.0]}
    for i, x in enumerate(MIRROR_XS):
        for k in (0, 1):
            _set(mesh, 2 * i + k, dict(zip(names, src.get(x, [0.2, 0.0, 0.8]))))
    _select(mesh)
    assert bpy.ops.allset.mirror_skin_weights('EXEC_DEFAULT') == {'FINISHED'}   # factory YZ, positive to negative
    # mayapy 2026 copySkinWeights -mirrorMode YZ -sa closestPoint (skin_basics_247.md)
    want = {-4: [0, 0, 1], -3: [0.2, 0, 0.8], -2.5: [0.3, 0, 0.7], -1.5: [0.5, 0, 0.5], -0.5: [0.8, 0, 0.2],
            0: [1, 0, 0], 1: [0.6, 0.4, 0], 4: [0, 1, 0]}
    for i, x in enumerate(MIRROR_XS):
        for k in (0, 1):
            got = _get(mesh, 2 * i + k, names)
            assert _close(got, want[x], 1e-5), (x, got)


def test_mirror_factory_plane_is_yz():
    assert bpy.ops.allset.mirror_skin_weights.get_rna_type().properties["plane"].default == "YZ"


def test_mirror_fixture_rows():
    rows = SK["copy_mirror_weights"]["mirror_YZ_pos_to_neg"]
    _reset()
    arm = _skeleton([("C", (0, 0, 0), None), ("L_a", (2, 0, 0), "C"), ("L_b", (4, 0, 0), "L_a"),
                     ("R_a", (-2, 0, 0), "C"), ("R_b", (-4, 0, 0), "R_a")])
    xs = [r["x"] for r in rows]
    pts = [(x, 0, z) for x in xs for z in (0, 1)]
    faces = [(2 * i, 2 * (i + 1), 2 * (i + 1) + 1, 2 * i + 1) for i in range(len(xs) - 1)]
    mesh = _mesh(pts, faces)
    names = ["C", "L_a", "L_b", "R_a", "R_b"]
    _skin(mesh, arm, names)
    for i, r in enumerate(rows):
        w = r["w"] if r["x"] >= 0 else {"C": 0.3, "L_a": 0, "L_b": 0, "R_a": 0.1, "R_b": 0.6}
        for k in (0, 1):
            _set(mesh, 2 * i + k, w)
    _select(mesh)
    assert bpy.ops.allset.mirror_skin_weights('EXEC_DEFAULT', plane="YZ") == {'FINISHED'}
    for i, r in enumerate(rows):
        got = _get(mesh, 2 * i, names)
        assert _close(got, [r["w"][n] for n in names], 1e-5), (r["x"], got)


def test_copy_skin_weights_closest_point_interpolates():
    # fixture copy_closestPoint: wA 1 / .75 / .5 / .25 / 0 at x -2 .. 2 from a source whose vertices sit at x -2 and 2
    _reset()
    arm = _skeleton([("A", (-2, 0, 0), None), ("B", (2, 0, 0), "A")])
    src = _mesh([(-2, 0, 0), (2, 0, 0), (2, 0, 1), (-2, 0, 1)], [(0, 1, 2, 3)], "src")
    _skin(src, arm, ["A", "B"])
    for i, x in enumerate((-2, 2, 2, -2)):
        _set(src, i, {"A": 1.0 if x < 0 else 0.0, "B": 0.0 if x < 0 else 1.0})
    xs = [r["x"] for r in SK["copy_mirror_weights"]["copy_closestPoint"]]
    pts = [(x, 0, z) for x in xs for z in (0, 1)]
    faces = [(2 * i, 2 * (i + 1), 2 * (i + 1) + 1, 2 * i + 1) for i in range(len(xs) - 1)]
    dst = _mesh(pts, faces, "dst")
    _select(src, dst, active=dst)
    assert bpy.ops.allset.copy_skin_weights('EXEC_DEFAULT') == {'FINISHED'}
    for i, r in enumerate(SK["copy_mirror_weights"]["copy_closestPoint"]):
        try:
            got = dst.vertex_groups["A"].weight(2 * i)
        except RuntimeError:
            got = 0.0
        assert abs(got - r["wA"]) < 1e-4, (r["x"], got)
