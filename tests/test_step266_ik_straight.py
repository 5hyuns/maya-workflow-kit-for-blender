"""Step 266 (research/maya/re/060_questions.md R4): Maya's default pole vector of a straight chain.

mayapy 2026 (step 266 lane A, 179 cases): an RP handle on exactly 3 joints whose middle joint has preferredAngle ~0,
jointOrient ~0 and rotate 0 on a straight chain gets preferredAngle (0, 90, 0) written on the middle joint by
``ikHandle``, so pv = 2·unit(L2·(d̂ − Y_S(d̂·Y_S)) + L1·(d̂ × Y_S)) in the start joint's frame S; 4+ joint straight
chains take the A2 fallback (smallest |component| axis ⊥ d): (0, −2, 0) along X, and stay straight."""

from importlib import import_module

import bpy
from mathutils import Vector

import kit
import maya2026_rig as rig

ik_rp = import_module(kit.MODULE + ".operators.ik_rp")
rig_maya = import_module(kit.MODULE + ".operators.rig_maya")
t245 = import_module("test_step245_ik_rp")

# (start, L1, L2, Maya pv): chains along +X, jointOrient 0 (= the kit's xyz / yup orient), random start and lengths
X_CASES = [((-0.645621, -2.53067, -2.923785), 4.552451, 5.533695, (1.544505, -0.0, 1.270631)),
           ((1.568214, -4.848649, -0.889677), 1.041542, 5.24414, (1.961684, 0.0, 0.389611)),
           ((-1.872115, 1.89098, 4.240975), 4.25924, 4.913521, (1.511248, 0.0, 1.310011)),
           ((3.823164, 3.8975, 1.341802), 5.839989, 1.640725, (0.54095, 0.0, 1.925454)),
           ((4.991753, -0.133585, 3.949907), 4.704691, 4.302323, (1.349691, -0.0, 1.475918)),
           ((-1.05846, -0.644852, 4.181835), 1.257852, 2.272879, (1.7499, -0.0, 0.968426)),
           ((3.747681, -4.642238, -0.321919), 4.951845, 4.054825, (1.267096, -0.0, 1.547407)),
           ((-3.947265, -3.269478, 2.224927), 1.080425, 3.22431, (1.896367, -0.0, 0.635448)),
           ((4.110543, 0.203244, -4.38662), 1.687455, 4.151218, (1.852774, -0.0, 0.753146)),
           ((2.464264, -0.630134, 2.623597), 5.434516, 5.808458, (1.460443, 0.0, 1.366421))]


def test_two_bone_straight_chain_takes_mayas_auto_preferred_angle():
    worst = 0.0
    for start, l1, l2, maya_pv in X_CASES:
        s = Vector(start)
        ob = t245._chain([s, s + Vector((l1, 0, 0)), s + Vector((l1 + l2, 0, 0))])
        h = t245._ik(ob, "j2")
        pv = Vector([h[n] for n in ik_rp.PV])
        worst = max(worst, (pv - Vector(maya_pv)).length)
        assert [round(a, 6) for a in ob.pose.bones["j1"][rig_maya.PREFERRED_PROP]] == [0.0, 0.0, 90.0]
    assert worst < 1e-4, worst
    print(f"  2-bone straight pv: {len(X_CASES)} Maya cases, worst {worst:.1e}")
    t245._reset()


def test_three_bone_straight_chain_falls_back_and_stays_straight():
    ob = t245._chain([(0, 0, 0), (4, 0, 0), (8, 0, 0), (12, 0, 0)])
    h = t245._ik(ob, "j3")
    pv = Vector([h[n] for n in ik_rp.PV])
    assert (pv - Vector((0.0, -2.0, 0.0))).length < 1e-6, tuple(pv)       # Maya axes_3bone along +X
    assert rig_maya.PREFERRED_PROP not in ob.pose.bones["j1"]
    t245._solve(h, (10, 0, 0))
    for name in ("j1", "j2"):
        p = t245._maya(ob, name)
        assert abs(p.y) < 1e-4 and abs(p.z) < 1e-4, (name, tuple(p))   # Maya: no bend without preferred angles
    t245._reset()


def test_a_bent_middle_joint_keeps_its_own_preferred_angle():
    ob = t245._chain([(0, 0, 0), (4, 0, 0), (8, 0, 0)], {1: (0, 30, 0)})
    t245._ik(ob, "j2")
    assert [round(a, 6) for a in ob.pose.bones["j1"][rig_maya.PREFERRED_PROP]] == [0.0, 0.0, 30.0]
    t245._reset()


def test_fallback_axis_rule():
    f = ik_rp.straight_fallback
    assert tuple(f(Vector((8, 0, 0)))) == (0.0, 0.0, 64.0)          # k = z
    assert tuple(f(Vector((0, 8, 0)))) == (0.0, 0.0, 64.0)          # k = z
    assert tuple(f(Vector((0, 0, 8)))) == (0.0, 64.0, 0.0)          # k = y


def test_c8_offset_branch_is_mayas_offset_euler():
    # research/maya/re/060_questions.md C8 (step 266): two xyz offsets mayapy stored on the alternate branch, and a
    # standard one; offset_euler of the rotation gives Maya's stored Euler back
    import math
    ci = import_module(kit.MODULE + ".operators.constrain_interp")
    # angles are per axis (x, y, z); for ZXY the first axis is z, the middle x, the last y
    for deg, order, want in (((68.1, 203.8, 5.4), 'XYZ', (68.1, 203.8, 5.4)),
                             ((4.1, 162.7, 97.3), 'XYZ', (4.1, 162.7, 97.3)),
                             ((20.0, 30.0, 40.0), 'XYZ', (20.0, 30.0, 40.0)),
                             ((30.0, -150.0, -150.0), 'ZXY', (150.0, 30.0, 30.0)),
                             ((30.0, -100.0, -120.0), 'ZXY', (30.0, -100.0, -120.0))):
        e = [math.radians(a) for a in deg]
        m = ci.q_matrix(ci.euler_quat(e, order))
        got = [math.degrees(a) for a in ci.offset_euler(m, order)]
        assert all(abs(g - w) < 1e-3 for g, w in zip(got, want)), (deg, got)
