"""Step 207: Curves 3 against Maya 2022.
Pure maths on Maya's numbers first (1e-6), then the kit operators on
Blender objects built from the same CVs (Maya Y-up -> Blender (X, -Z, Y))."""

import json
import math
import re
import os
from importlib import import_module

import bpy

import kit

cm = import_module(kit.MODULE + ".operators.curves_math")
sm = import_module(kit.MODULE + ".operators.surfaces_math")
cmaya = import_module(kit.MODULE + ".operators.curves_maya")
smaya = import_module(kit.MODULE + ".operators.surfaces_maya")
c207 = import_module(kit.MODULE + ".operators.curves_207")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOL = 1e-6
_D = {}
WORST = {}


def named(c, name, when="after"):
    return [x for x in c[when] if x["name"] == name][0]


def err(a, b):
    assert len(a) == len(b), (len(a), len(b))
    return max(abs(p - q) for P, Q in zip(a, b) for p, q in zip(P, Q))


def _modify_args(key, c):
    words = c["cmds"][-1].split()     # the recorded command: <command> <operation> <amount> <amount>
    if len(words) == 4 and words[1] in ("bend", "curl", "curvature", "smooth", "straighten"):
        return words[1], float(words[2]), float(words[3])
    op = key.split("_")[0]
    return op, *{"bend": (0.2, 0.0), "curl": (0.3, 1.0), "curvature": (1.1, 0.8)}[op]


KIND = {"bend": 'BEND', "curl": 'CURL', "curvature": 'CURVATURE'}


# --- pure maths -----------------------------------------------------------------------------------------------


def _surf(c):
    S = c["surface"]
    nu, nv, d = S["nu"], S["nv"], S["degree"]
    cvs = [[tuple(S["cvs"][i * nv + j]) for j in range(nv)] for i in range(nu)]
    ku = [k / (nu - d) for k in cm.clamped_uniform(nu, d)]
    kv = [k / (nv - d) for k in cm.clamped_uniform(nv, d)]
    return sm.Surf(cvs, ku, kv, d, d)


LINES = {"dup_v0.5": [("V", 0.5)], "dup_u0.25": [("U", 0.25)], "dup_u0": [("U", 0.0)],
         "dup_two": [("U", 0.25), ("V", 0.75)], "dup_d1": [("V", 0.5)]}


def test_keep_leg_lengths():
    old = [(0, 0, 0), (1, 0, 0), (2, 0.5, 0), (3, 0, 0), (4, 0, 0)]
    new = list(old)
    new[2] = (2, 2.0, 0.5)
    out = cm.keep_leg_lengths(old, new)
    assert out[2] == new[2]
    legs = lambda P: [cm.norm(cm.sub(P[i + 1], P[i])) for i in range(len(P) - 1)]
    assert max(abs(a - b) for a, b in zip(legs(out), legs(old))) < 1e-9
    assert cm.keep_leg_lengths(old, old) == old


# --- kit operators --------------------------------------------------------------------------------------------

def _clear():
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)


def _sel(*obs):
    for o in bpy.context.selected_objects:
        o.select_set(False)
    for o in obs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = obs[-1]


def _bl(pts):
    return [c207.from_maya(p) for p in pts]


def _curve(name, maya_cvs, degree=3):
    c = cmaya.MCurve(_bl(maya_cvs), cm.clamped_uniform(len(maya_cvs), degree), degree)
    ob = cmaya._new_curve_object(bpy.context, name, [c])
    ob.name = name
    return ob


def _cvs(ob):
    return cmaya.read_spline(ob.data.splines[0]).cvs


def test_lock_length():
    _clear()
    ob = _curve("curveA", [(0, 0, 0), (1, 0, -3), (4, 0, -4), (6, 0, -1), (8, 0, 2)])
    _sel(ob)
    assert bpy.ops.allset.curve_lock_length(lock=True) == {'FINISHED'}
    assert ob.data[c207.LOCK]
    legs = lambda P: [cm.norm(cm.sub(P[i + 1], P[i])) for i in range(len(P) - 1)]
    before = legs(_cvs(ob))
    sp = ob.data.splines[0]
    sp.points[2].co = (5.0, 2.0, 1.0, 1.0)
    assert c207.apply_lock(ob.data)
    after = _cvs(ob)
    assert tuple(after[2]) == (5.0, 2.0, 1.0)
    assert max(abs(x - y) for x, y in zip(legs(after), before)) < 1e-6
    assert bpy.ops.allset.curve_lock_length(lock=False) == {'FINISHED'}
    sp.points[0].co = (9.0, 9.0, 9.0, 1.0)
    bpy.context.view_layer.update()
    assert tuple(_cvs(ob)[0]) == (9.0, 9.0, 9.0)        # unlocked: nothing follows


def test_report_worst():
    print("WORST", json.dumps({k: v for k, v in sorted(WORST.items())}, indent=0, default=str))


