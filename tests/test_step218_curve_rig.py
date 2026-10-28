"""Step 218 lane C: Spline IK on an existing curve (L6) and clusters on curve CVs (L7) against Maya 2026 Maya numbers
(, data maya2026_curve_rigs.json; scene script
C:/Repos/bmk-strategy/maya2026_re/scripts/py_curves.py). Maya (x, y, z) = Blender (x, -z, y), factory scene = 1 unit.

checked scene: joint1..joint5 at Maya (0, 2i, 0); spineCurve = degree 3, CVs (1,0,0) (2,2,0) (1,4,1) (0,6,0) (1,8,0).
"""

from importlib import import_module

import bpy
from mathutils import Vector

import kit

rig = import_module(kit.MODULE + ".operators.rig_maya")
ow = import_module(kit.MODULE + ".operators.option_windows")
parenting = import_module(kit.MODULE + ".operators.parenting")
cb = import_module(kit.MODULE + ".ui.channel_box")

MAYA = kit.MayaJson("maya", "re", "maya2026_curve_rigs.json")

CVS = [(1, 0, 0), (2, 2, 0), (1, 4, 1), (0, 6, 0), (1, 8, 0)]
# Blender's Spline IK walks the curve's polyline (kit resolution 128): checked 7e-5 against Maya's numbers, which are
# rounded to 4 decimals (±5e-5)
ROOT_ON_CURVE_TOL = 1e-4


def B(p):
    x, y, z = p
    return Vector((x, -z, y))


def _fresh():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for coll in (bpy.data.armatures, bpy.data.curves, bpy.data.meshes):
        for d in list(coll):
            coll.remove(d)


def _curve(name="spineCurve", cvs=CVS, resolution=12):
    cu = bpy.data.curves.new(name + "Shape", 'CURVE')
    cu.dimensions = '3D'
    cu.resolution_u = resolution
    sp = cu.splines.new('NURBS')
    sp.points.add(len(cvs) - 1)
    for p, c in zip(sp.points, cvs):
        p.co = (*B(c), 1.0)
    sp.order_u = 4
    sp.use_endpoint_u = True        # Maya clamped uniform knots (step 156)
    ob = bpy.data.objects.new(name, cu)
    bpy.context.collection.objects.link(ob)
    return ob


def _chain(parent_bone=False):
    """Kit skeleton: bones joint1..joint4 between the joints, joint5 = the end joint (short bone)."""
    data = bpy.data.armatures.new("skeleton")
    arm = bpy.data.objects.new("skeleton1", data)
    bpy.context.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    prev = None
    if parent_bone:
        prev = data.edit_bones.new("joint0")
        prev.head, prev.tail = (0, 0, -2), (0, 0, 0)
    for k in range(5):
        eb = data.edit_bones.new(f"joint{k + 1}")
        eb.head = (0, 0, 2 * k)
        eb.tail = (0, 0, 2 * k + (2 if k < 4 else 0.5))
        if prev is not None:
            eb.parent = prev
            eb.use_connect = True
        prev = eb
    bpy.ops.object.mode_set(mode='POSE')
    for pb in arm.pose.bones:
        cb.set_bone_selected(pb, pb.name in ("joint1", "joint5"))
    data.bones.active = data.bones["joint5"]
    return arm


def _joints(arm):
    bpy.context.view_layer.update()
    return [arm.matrix_world @ arm.pose.bones[f"joint{k}"].head for k in range(1, 6)]


def _err(got, maya):
    return max((g - B(m)).length for g, m in zip(got, maya))


def _spline(curve=None, **kw):
    return bpy.ops.allset.ik_spline_handle('EXEC_DEFAULT', True, curve=curve.name if curve else "", **kw)


# --- L6 Spline IK on an existing curve --------------------------------------------------------------------------

def test_root_on_curve_matches_maya():
    _fresh()
    curve = _curve()
    arm = _chain()
    assert _spline(curve, create_curve=False) == {'FINISHED'}
    con = arm.pose.bones["joint4"].constraints["ikHandle1"]
    assert con.type == 'SPLINE_IK' and con.target == curve and con.chain_count == 4
    assert con.y_scale_mode == 'NONE' and not con.use_chain_offset
    want = MAYA["L6_spline_existing_curve"]["roc1_snc0"]
    err = _err(_joints(arm), want["joints_after"])
    print(f"L6 roc1_snc0 max joint error {err:.6f}")
    assert err < ROOT_ON_CURVE_TOL, err
    cv0 = curve.matrix_world @ Vector(curve.data.splines[0].points[0].co[:3])
    assert (cv0 - B(want["curve_cv0_after"])).length < 1e-6
    assert curve.parent is None                      # root has no parent: the curve stays in the world (Maya)
    # Maya selects the new handle: the constraint's bone is the only selected joint
    assert [pb.name for pb in arm.pose.bones if cb.bone_selected(pb)] == ["joint4"]


def test_snap_curve_to_root_matches_maya():
    _fresh()
    curve = _curve()
    arm = _chain()
    curve.select_set(True)                           # the selected curve is used (no name given)
    assert _spline(None, create_curve=False, snap_curve=True) == {'FINISHED'}
    want = MAYA["L6_spline_existing_curve"]["roc1_snc1"]
    cv0 = curve.matrix_world @ Vector(curve.data.splines[0].points[0].co[:3])
    assert (cv0 - B(want["curve_cv0_after"])).length < 1e-6, cv0
    err = _err(_joints(arm), want["joints_after"])
    print(f"L6 roc1_snc1 max joint error {err:.6f}")
    assert err < ROOT_ON_CURVE_TOL, err


def test_root_on_curve_off_keeps_the_root():
    _fresh()
    curve = _curve()
    arm = _chain()
    assert _spline(curve, create_curve=False, root_on_curve=False) == {'FINISHED'}
    con = arm.pose.bones["joint4"].constraints["ikHandle1"]
    assert con.use_chain_offset
    got = _joints(arm)
    want = MAYA["L6_spline_existing_curve"]["roc0_snc0"]["joints_after"]
    assert (got[0] - B(want[0])).length < 1e-6                         # root stays (Maya)
    # Blender's Chain Offset = the root-on-curve chain shifted onto the root (the snap result); Maya instead puts
    # joint2.. on the curve itself (sphere from the root): checked gap 1.35, reported in the step doc
    snap = MAYA["L6_spline_existing_curve"]["roc1_snc1"]["joints_after"]
    assert _err(got, snap) < ROOT_ON_CURVE_TOL
    print(f"L6 roc0_snc0 max joint error vs Maya {_err(got, want):.6f} (Blender Chain Offset model)")
    for a, b in zip(got, got[1:]):
        assert abs((b - a).length - 2.0) < 1e-4                          # bone lengths kept


def test_auto_create_curve_is_maya():
    _fresh()
    arm = _chain()
    assert _spline() == {'FINISHED'}
    want = MAYA["L6_spline_auto_curve"]
    con = arm.pose.bones["joint4"].constraints["ikHandle1"]
    curve = con.target
    sp = curve.data.splines[0]
    assert sp.type == 'NURBS' and sp.order_u - 1 == want["curve_degree"] and len(sp.points) == want["cv_count"]
    assert curve.name == "curve1" and curve.parent is None
    assert [pb.name for pb in arm.pose.bones if cb.bone_selected(pb)] == ["joint4"]     # selection = handle
    err = max((a - b).length for a, b in zip(_joints(arm), [Vector((0, 0, 2 * k)) for k in range(5)]))
    assert err < 1e-3, err                                              # a curve through the chain moves nothing


def test_number_of_spans():
    _fresh()
    arm = _chain()
    assert _spline(spans=2) == {'FINISHED'}
    sp = arm.pose.bones["joint4"].constraints["ikHandle1"].target.data.splines[0]
    assert len(sp.points) == 5 and sp.use_endpoint_u
    assert Vector(sp.points[0].co[:3]).length < 1e-6
    assert (Vector(sp.points[-1].co[:3]) - Vector((0, 0, 8))).length < 1e-6


def test_auto_parent_curve():
    _fresh()
    curve = _curve()
    arm = _chain(parent_bone=True)
    before = curve.matrix_world.copy()
    assert _spline(curve, create_curve=False, root_on_curve=True) == {'FINISHED'}
    assert curve.parent == arm and curve.parent_type == 'BONE' and curve.parent_bone == "joint0"
    bpy.context.view_layer.update()
    assert max(abs(a - b) for ra, rb in zip(curve.matrix_world, before) for a, b in zip(ra, rb)) < 1e-5
    _fresh()
    curve = _curve()
    arm = _chain(parent_bone=True)
    assert _spline(curve, create_curve=False, parent_curve=False) == {'FINISHED'}
    assert curve.parent is None


def test_auto_create_off_needs_a_curve():
    _fresh()
    _chain()
    assert _spline(None, create_curve=False) == {'CANCELLED'}


def test_option_window_runs_the_tool_with_the_values():
    _fresh()
    curve = _curve()
    arm = _chain()
    curve.select_set(True)
    w = ow._BY_KEY["ik_spline_tool"]
    res = ow.run(w, bpy.context, {"create_curve": False, "snap_curve": True})
    assert not isinstance(res, str), res
    assert arm.pose.bones["joint4"].constraints["ikHandle1"].target == curve
    assert (curve.matrix_world @ Vector(curve.data.splines[0].points[0].co[:3])).length < 1e-6


def test_spline_ik_undo():
    _fresh()
    curve = _curve()
    arm = _chain()
    bpy.ops.ed.undo_push(message="test start")
    assert _spline(curve, create_curve=False, snap_curve=True) == {'FINISHED'}
    bpy.ops.ed.undo()
    arm = bpy.data.objects["skeleton1"]
    curve = bpy.data.objects["spineCurve"]
    assert not arm.pose.bones["joint4"].constraints
    assert curve.matrix_world.translation.length < 1e-9


# --- L7 Cluster on curve CVs ------------------------------------------------------------------------------------

def _curve_points(ob):
    """Evaluated curve polyline in world space (to_mesh)."""
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    try:
        return [ob.matrix_world @ v.co for v in me.vertices]
    finally:
        ev.to_mesh_clear()


def _cluster_on_cvs(cvs=(3, 4)):
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    curve = bpy.data.objects["spineCurve"]
    for o in bpy.context.selected_objects:
        o.select_set(False)
    curve.select_set(True)
    bpy.context.view_layer.objects.active = curve
    for i, p in enumerate(curve.data.splines[0].points):
        p.select = i in cvs
    bpy.ops.object.mode_set(mode='EDIT')
    assert bpy.ops.allset.cluster('EXEC_DEFAULT', True) == {'FINISHED'}
    return curve


def test_cluster_on_curve_cvs_matches_maya():
    _fresh()
    curve = _curve()
    arm = _chain()
    assert _spline(curve, create_curve=False) == {'FINISHED'}
    tip_before = _joints(arm)[-1]
    want = MAYA["L7_cluster_curve_cvs"]
    print(f"L7 tip before {_err([tip_before], [want['tip_joint_before_after'][0]]):.6f}")
    curve = _cluster_on_cvs()
    md = curve.modifiers["cluster1"]
    handle = bpy.data.objects[want["handle"]]
    assert md.type == 'HOOK' and md.object == handle and md.strength == 1.0
    assert (handle.matrix_world.translation - B(want["handle_rp_world"])).length < 1e-6       # pivot = CV centre
    assert bpy.context.mode == 'OBJECT' and bpy.context.active_object == handle and handle.select_get()
    before = _curve_points(curve)
    rest = _curve_points(_curve("ref", resolution=curve.data.resolution_u))
    assert max((a - b).length for a, b in zip(before, rest)) < 1e-6        # rest = no change
    handle.location.x += 2.0
    bpy.context.view_layer.update()
    # reference = the same curve with cv3 and cv4 moved +2 in x: identical polyline <=> exactly those CVs moved
    moved = [list(c) for c in CVS]
    moved[3][0] += 2.0
    moved[4][0] += 2.0
    ref = _curve("ref2", [tuple(c) for c in moved], curve.data.resolution_u)
    assert tuple(moved[3]) == tuple(want["cv3_after_move"]) and tuple(CVS[2]) == tuple(want["cv2_after_move"])
    got = _curve_points(curve)
    assert max((a - b).length for a, b in zip(got, _curve_points(ref))) < 1e-5
    bpy.data.objects.remove(ref)
    err = _err([_joints(arm)[-1]], [want["tip_joint_before_after"][1]])
    print(f"L7 tip after handle x+2 error {err:.6f}")
    assert err < ROOT_ON_CURVE_TOL, err
    # the handle under a control: moving the control drives the CVs and the chain (Maya ctrl z+3)
    ctrl = bpy.data.objects.new("ctrl", None)
    bpy.context.collection.objects.link(ctrl)
    bpy.context.view_layer.update()
    parenting.set_parent_maya(handle, ctrl)
    ctrl.location = B((0, 0, 3))
    err = _err([_joints(arm)[-1]], [want["tip_after_ctrl_z3"]])
    print(f"L7 tip after ctrl z+3 error {err:.6f}")
    assert err < ROOT_ON_CURVE_TOL, err


def test_cluster_object_mode_takes_every_cv():
    _fresh()
    curve = _curve()
    bpy.context.view_layer.objects.active = curve
    curve.select_set(True)
    assert bpy.ops.allset.cluster('EXEC_DEFAULT', True) == {'FINISHED'}
    handle = bpy.data.objects["cluster1Handle"]
    assert (handle.location - B((1, 4, 0.5))).length < 1e-6          # box centre of the CVs
    handle.location.z += 1.0
    bpy.context.view_layer.update()
    pts = _curve_points(curve)
    ref = _curve_points(_curve("ref"))
    assert all(abs((a - b).z - 1.0) < 1e-5 and abs((a - b).x) < 1e-5 for a, b in zip(pts, ref))


def test_cluster_bezier_point_indices():
    _fresh()
    cu = bpy.data.curves.new("bez", 'CURVE')
    sp = cu.splines.new('BEZIER')
    sp.bezier_points.add(2)
    for i, bp in enumerate(sp.bezier_points):
        bp.co = (2.0 * i, 0, 0)
        bp.handle_left_type = bp.handle_right_type = 'VECTOR'
        bp.select_control_point = bp.select_left_handle = bp.select_right_handle = (i == 1)
    ob = bpy.data.objects.new("bez", cu)
    bpy.context.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    centre, idx = rig._point_selection(ob, True)
    assert idx == [3, 4, 5] and (centre - Vector((2, 0, 0))).length < 1e-6


def test_cluster_undo():
    _fresh()
    _curve()
    bpy.ops.ed.undo_push(message="test start")
    _cluster_on_cvs()
    bpy.ops.ed.undo()
    curve = bpy.data.objects["spineCurve"]
    assert not curve.modifiers and "cluster1Handle" not in bpy.data.objects
