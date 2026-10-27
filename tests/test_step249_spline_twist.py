"""Step 249 (Issue #166): Spline IK Twist / Roll / Twist Type like Maya.

Maya 2026 numbers (mayapy, docs/steps/step_249.md 「측정」, tmp/m249/sp.py): six joints 2 apart up Maya Y, oriented
(xyz / yup), ikHandle -sol ikSplineSolver -ns 2, curve CVs 3 / 4 moved by (2, 0, 0) / (4, 0, 1) (a bend out of plane);
joint rotate X for Twist / Roll / Twist Type. The fixture's straight-curve lists (SKINNING-style IK["ik"]["spline_ik"]
twist100_rx / twistType*_rx) share the spread rule: 25 / 25 / 25 / 25, 1.5625 / 10.9 / 29.6 / 57.5 ...
Kit: operators/spline_twist.py (drivers on each chain bone's roll), rig_maya.create_spline_ik.
"""

import math
from importlib import import_module

import bpy
from mathutils import Matrix

import kit
import maya2026_rig as rig
import maya2026_rig_data as data

rig_maya = import_module(kit.MODULE + ".operators.rig_maya")
st = import_module(kit.MODULE + ".operators.spline_twist")

M = {'cvs': [[0.0, -0.0, 0.0], [0.0, 1.666667, 0.0], [0.0, 5.0, 0.0], [2.0, 8.333333, 0.0], [4.0, 10.0, 1.0]],
     'base': [0.0, 0.0, 0.0151, 0.4288, 0.7953, 0.0],
     'twist100': [0.0, 25.0, 25.357, 25.5298, 24.4206, 0.0],
     'roll30': [30.0, 0.1121, 0.4006, 0.7453, 0.6103, 0.0],
     'twist100_roll30': [30.0, 25.1121, 25.4241, 24.7987, 24.1928, 0.0],
     'tt1': [0.0, 1.5625, 10.9772, 30.3336, 58.1305, 0.0],
     'tt2': [0.0, 57.8125, 30.0931, 10.5546, 0.7297, 0.0],
     'tt3': [0.0, 15.625, 34.6227, 34.9048, 14.8829, 0.0],
     'twist_neg60_tt3': [0.0, -9.375, -20.756, -20.9325, -9.758, 0.0]}
W = [[0.0, -0.0, 0.0], [0.03199, 1.99974, 0.0], [0.25359, 3.98743, 0.0], [0.82341, 5.90453, 0.00592],
     [1.79037, 7.6494, 0.14878], [3.05513, 9.14092, 0.56804]]
SETTINGS = {'base': {}, 'twist100': {"twist": 100.0}, 'roll30': {"roll": 30.0},
            'twist100_roll30': {"twist": 100.0, "roll": 30.0}, 'tt1': {"twist": 100.0, "twistType": 1},
            'tt2': {"twist": 100.0, "twistType": 2}, 'tt3': {"twist": 100.0, "twistType": 3},
            'twist_neg60_tt3': {"twist": -60.0, "twistType": 3}}
NAMES = [f"joint{i}" for i in range(1, 7)]
CHAIN = {"joint1": {"t": [0, 0, 0], "jo": [0, 0, 90], "parent": None},
         **{f"joint{i}": {"t": [2, 0, 0], "parent": f"joint{i - 1}"} for i in range(2, 6)},
         "joint6": {"t": [2, 0, 0], "jo": [0, 0, -90], "parent": "joint5"}}
TOL = 0.7          # RIG_UPGRADE_PLAN step 8 acceptance (Euler mixing of the bend)


def _reset():
    if bpy.context.object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)


def _curve(cvs):
    cd = bpy.data.curves.new("curveShape1", 'CURVE')
    cd.dimensions = '3D'
    sp = cd.splines.new('NURBS')
    sp.points.add(len(cvs) - 1)
    for p, c in zip(sp.points, cvs):
        b = rig.to_blender(c)
        p.co = (b.x, b.y, b.z, 1.0)
    sp.order_u = 4
    sp.use_endpoint_u = True
    ob = bpy.data.objects.new("curve1", cd)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def _setup(cvs=None):
    _reset()
    arm = rig.build_skeleton(CHAIN, name="skeleton1")
    curve = _curve(cvs or M['cvs'])
    bpy.context.view_layer.objects.active = arm
    con, curve = rig_maya.create_spline_ik(bpy.context, arm, ("joint1", 'HEAD'), ("joint6", 'HEAD'), curve=curve,
                                           parent_curve=False)
    handle = bpy.data.objects[con.name]
    return arm, con, handle


def _maya_rx(arm):
    """Maya rotate X of each joint: rotation in its own Maya axes relative to its rest (jointOrient) frame."""
    bpy.context.view_layer.update()
    ja = rig.JOINT_AXES
    out = []
    for n in NAMES:
        pb = arm.pose.bones[n]
        w = pb.matrix.to_3x3().normalized() @ ja
        r0 = pb.bone.matrix_local.to_3x3().normalized() @ ja
        if pb.parent is not None:
            wp = pb.parent.matrix.to_3x3().normalized() @ ja
            rp = pb.parent.bone.matrix_local.to_3x3().normalized() @ ja
            local, rest = wp.inverted() @ w, rp.inverted() @ r0
        else:
            local, rest = w, r0
        r = rest.inverted() @ local
        out.append(math.degrees(r.to_euler('XYZ').x))
    return out


def _set(handle, values):
    handle["twist"] = values.get("twist", 0.0)
    handle["roll"] = values.get("roll", 0.0)
    handle["twistType"] = values.get("twistType", 0)
    handle.update_tag()            # a Python ID-property write tags nothing (the Channel Box does this itself)


def test_shares_are_maya_curves():
    # fixture straight chain (IK spline_ik): twist 100 Linear 25 each, Ease In 1.5625 / 10.9375 / 29.6875 / 57.8125
    ik = data.IK["ik"]["spline_ik"]
    # (that chain is bent by an unrecorded curve: its Euler mixing reaches 0.75 deg, so 1 deg here; the exact
    # 0.7 check is the recorded bent curve below)
    lin = [100 * s for s in st.shares(5, 0)][1:]
    assert all(abs(a - b) < 1.0 for a, b in zip(lin, ik["twist100_rx"][1:5]))
    for kind, key in ((1, "twistType1_rx"), (2, "twistType2_rx"), (3, "twistType3_rx")):
        got = [100 * s for s in st.shares(5, kind)][1:]
        assert all(abs(a - b) < 1.0 for a, b in zip(got, ik[key][1:5])), (kind, got, ik[key])
    assert abs(st.shares(5, 1)[1] * 100 - 1.5625) < 1e-9


def test_handle_and_drivers_made():
    arm, con, handle = _setup()
    assert handle.name == con.name == "ikHandle1"
    assert all(k in handle for k in ("twist", "roll", "twistType"))
    drivers = {d.data_path for d in arm.animation_data.drivers}
    for n in NAMES[:5]:
        assert f'pose.bones["{n}"].rotation_euler' in drivers, n
    assert all(d.driver.is_simple_expression for d in arm.animation_data.drivers), "no Python auto-run needed"


def test_positions_match_maya_bent_curve():
    arm, con, handle = _setup()
    bpy.context.view_layer.update()
    err = max((rig.to_maya(arm.matrix_world @ arm.pose.bones[n].head) - rig.to_maya(rig.to_blender(w))).length
              for n, w in zip(NAMES, W))
    assert err < 2e-3, err


def test_twist_roll_twist_type_match_maya():
    arm, con, handle = _setup()
    worst = {}
    for case, values in SETTINGS.items():
        _set(handle, values)
        got = _maya_rx(arm)
        diff = max(abs(a - b) for a, b in zip(got[:5], M[case][:5]))
        worst[case] = diff
        assert diff < TOL, (case, [round(x, 3) for x in got], M[case])
    print("worst rx difference per case", {k: round(v, 3) for k, v in worst.items()})


def test_delete_handle_removes_solver():
    arm, con, handle = _setup()
    dag = import_module(kit.MODULE + ".operators.dag")
    dag.delete_hierarchy(bpy.context, [handle])
    assert not arm.pose.bones["joint5"].constraints, "the Spline IK goes with its handle"
    assert not (arm.animation_data and arm.animation_data.drivers), "and its twist drivers"


def test_save_open_keeps_twist(tmp_path=None):
    import os
    import tempfile
    arm, con, handle = _setup()
    _set(handle, {"twist": 100.0, "twistType": 1})
    path = os.path.join(tempfile.mkdtemp(prefix="allset249_"), "spline.blend")
    bpy.ops.wm.save_as_mainfile(filepath=path)
    bpy.ops.wm.open_mainfile(filepath=path)
    arm = bpy.data.objects["skeleton1"]
    got = _maya_rx(arm)
    assert max(abs(a - b) for a, b in zip(got[:5], M['tt1'][:5])) < TOL
