"""Step 207: Curves 3 against Maya 2022 (, ground truth curves_201.json from
). Pure maths on Maya's numbers first (1e-6), then the kit operators on
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
TRUTH = os.path.join(ROOT, "research", "maya", "re", "curves_201.json")
TOL = 1e-6
_D = {}
WORST = {}


def data():
    if "d" not in _D:
        _D["d"] = None
        if os.path.exists(TRUTH):
            with open(TRUTH, encoding="utf-8") as fh:
                _D["d"] = json.load(fh)
        else:
            print(" missing: skipped")
    return _D["d"]


def case(k):
    return data()["cases"][k]


def named(c, name, when="after"):
    return [x for x in c[when] if x["name"] == name][0]


def err(a, b):
    assert len(a) == len(b), (len(a), len(b))
    return max(abs(p - q) for P, Q in zip(a, b) for p, q in zip(P, Q))


def _modify_args(key, c):
    cmd = c["cmds"][-1]
    if cmd.startswith("modifySelectedCurves"):
        _m, op, a1, a2 = cmd.split()
        return op, float(a1), float(a2)
    op = key.split("_")[0]
    return op, *{"bend": (0.2, 0.0), "curl": (0.3, 1.0), "curvature": (1.1, 0.8)}[op]


KIND = {"bend": 'BEND', "curl": 'CURL', "curvature": 'CURVATURE'}


# --- pure maths -----------------------------------------------------------------------------------------------

def test_bend_curl_scale_curvature_pure():
    if data() is None:
        return
    n = 0
    for key, c in data()["cases"].items():
        if not key.split("_")[0] in ("bend", "curl", "curvature", "smooth", "straighten") or "error" in c:
            continue
        op, a1, a2 = _modify_args(key, c)
        before = c["before"][0]["cvs_local"]
        want = named(c, "curveA")["cvs_local"]
        start, count = (2, 4) if "cv2_5" in key else (0, None)
        if op in KIND:
            got = c207.modify_points(KIND[op], before, a1, a2, start, count)
        elif op == "smooth":
            got = cm.smooth_cvs(before, a1)
        else:
            got = cm.straighten(before, a1, bool(a2))
        w = err(got, want)
        WORST[key] = w
        assert w <= TOL, (key, w)
        n += 1
    assert n >= 65, n


def test_cv_hardness_pure():
    if data() is None:
        return
    n = 0
    for key, c in data()["cases"].items():
        if not key.startswith("hard_") or key in ("hard_C9_cv4_m1",):
            continue
        b = c["before"][0]
        cvs = [int(x) for x in re.findall(r"cv(\d+)", key)] or [4]       # hard_factory picks cv[4]
        last = max(cvs)
        got = cm.harden(b["knots"], b["degree"], last)
        want = named(c, "curveA")["knots"]
        assert got == want, (key, got, want)
        assert err(b["cvs"], named(c, "curveA")["cvs"]) < 1e-9
        n += 1
    assert n >= 25, n


def test_fit_bspline_pure():
    if data() is None:
        return
    for key in [k for k in data()["cases"] if k.startswith("fit_")]:
        c = case(key)
        cvs, knots, deg = cm.fit_bspline(c["before"][0]["cvs"])
        out = named(c, "fitBsplineCurve1")
        assert deg == 3 and max(abs(a - b) for a, b in zip(knots, out["knots"])) < TOL, key
        w = err(cvs, out["cvs"])
        WORST[key] = w
        assert w < TOL, (key, w)


def test_align_pure():
    if data() is None:
        return
    for key in [k for k in data()["cases"] if k.startswith("align_")]:
        c = case(key)
        A0, B0 = named(c, "curveA", "before")["cvs"], named(c, "curveB", "before")["cvs"]
        if key == "align_B1_A":       # B selected first: B moves
            got = cm.align_ends(B0, A0)
            w = err(got, named(c, "curveB")["cvs"])
            assert err(A0, named(c, "curveA")["cvs"]) < 1e-9
        else:
            got = cm.align_ends(A0, B0)
            w = err(got, named(c, "curveA")["cvs"])
            assert err(B0, named(c, "curveB")["cvs"]) < 1e-9
        WORST[key] = w
        assert w < TOL, (key, w)


def _surf(c):
    S = c["surface"]
    nu, nv, d = S["nu"], S["nv"], S["degree"]
    cvs = [[tuple(S["cvs"][i * nv + j]) for j in range(nv)] for i in range(nu)]
    ku = [k / (nu - d) for k in cm.clamped_uniform(nu, d)]
    kv = [k / (nv - d) for k in cm.clamped_uniform(nv, d)]
    return sm.Surf(cvs, ku, kv, d, d)


LINES = {"dup_v0.5": [("V", 0.5)], "dup_u0.25": [("U", 0.25)], "dup_u0": [("U", 0.0)],
         "dup_two": [("U", 0.25), ("V", 0.75)], "dup_d1": [("V", 0.5)]}


def test_duplicate_surface_curves_pure():
    if data() is None:
        return
    for key in [k for k in data()["cases"] if k.startswith("dup_")]:
        c = case(key)
        s = _surf(c)
        lines = sm.visible_isoparms(s) if key == "dup_object" else LINES[key]
        assert len(lines) == len(c["after"]), key
        for (direction, t), out in zip(lines, c["after"]):
            cr = sm.isoparm(s, direction, t)
            assert cr.knots == out["knots"] and cr.degree == out["degree"], key
            w = err(cr.cvs, out["cvs"])
            WORST[key + direction + str(t)] = w
            assert w < TOL, (key, w)


def test_intersect_parameters_pure():
    if data() is None:
        return
    c = case("intersect_AB")
    A, B = named(c, "curveA", "before"), named(c, "curveB", "before")
    got = cm.intersections((A["cvs"], A["knots"], 3, None), (B["cvs"], B["knots"], 3, None), tol=0.01)
    want = c["curveIntersect"]["curveIntersect1"]
    ua = sorted(u for u, _ in got)
    ub = sorted(v for _, v in got)
    assert max(abs(a - b) for a, b in zip(ua, want["parameter1"][0])) < TOL
    assert max(abs(a - b) for a, b in zip(ub, want["parameter2"][0])) < TOL
    assert len(c["selection_after"]) == 2 * len(got)       # a locator per crossing on each curve


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


def test_modify_operator_matches_maya():
    if data() is None:
        return
    for key in ("bend_A3D_0.2_0", "curl_A3D_0.3_1", "curvature_A3D_1.1_0.8", "bend_VERT_0.5_0.5",
                "curl_LONG_1_2.5", "curvature_NEGZ_2_0.3", "bend_factory", "curl_factory", "curvature_factory"):
        _clear()
        c = case(key)
        op, a1, a2 = _modify_args(key, c)
        ob = _curve("curveA", c["before"][0]["cvs_local"])
        _sel(ob)
        res = bpy.ops.allset.curve_modify(kind=KIND[op], amount=a1, second=a2) if "factory" not in key else \
            bpy.ops.allset.curve_modify(kind=KIND[op])
        assert res == {'FINISHED'}, key
        w = err(_cvs(ob), _bl(named(c, "curveA")["cvs_local"]))
        WORST["op_" + key] = w
        assert w < TOL, (key, w)


def test_modify_cv_range_in_edit_mode():
    if data() is None:
        return
    _clear()
    c = case("bend_A3D_cv2_5")
    ob = _curve("curveA", c["before"][0]["cvs_local"])
    _sel(ob)
    bpy.ops.object.mode_set(mode='EDIT')
    for i, p in enumerate(ob.data.splines[0].points):
        p.select = 2 <= i <= 5
    assert bpy.ops.allset.curve_modify(kind='BEND') == {'FINISHED'}
    assert bpy.context.mode == 'EDIT_CURVE'
    bpy.ops.object.mode_set(mode='OBJECT')
    assert err(_cvs(ob), _bl(named(c, "curveA")["cvs_local"])) < TOL


def test_cv_hardness_operator():
    if data() is None:
        return
    _clear()
    c = case("hard_C9_cv4")
    ob = _curve("curveA", c["before"][0]["cvs"])
    _sel(ob)
    bpy.ops.object.mode_set(mode='EDIT')
    for i, p in enumerate(ob.data.splines[0].points):
        p.select = i == 4
    assert bpy.ops.allset.curve_cv_hardness() == {'FINISHED'}
    bpy.ops.object.mode_set(mode='OBJECT')
    out = named(c, "curveA")
    want = cm.to_bezier(_bl(out["cvs"]), out["knots"], 3)
    got = cmaya.read_spline(ob.data.splines[0])
    flat = [want[0][0]] + [p for seg in want for p in seg[1:]]
    assert err(got.cvs, flat) < TOL
    # an end CV: nothing to harden (Maya does nothing)
    bpy.ops.object.mode_set(mode='EDIT')
    for i, p in enumerate(ob.data.splines[0].bezier_points):
        p.select_control_point = i == 0
    assert bpy.ops.allset.curve_cv_hardness() == {'CANCELLED'}
    bpy.ops.object.mode_set(mode='OBJECT')


def test_fit_bspline_operator():
    if data() is None:
        return
    _clear()
    c = case("fit_p7")
    ob = _curve("curveA", c["before"][0]["cvs"], degree=1)
    _sel(ob)
    assert bpy.ops.allset.curve_fit_bspline() == {'FINISHED'}
    new = bpy.context.view_layer.objects.active
    assert new.name == "fitBsplineCurve1" and "curveA" in bpy.data.objects, new.name
    out = named(c, "fitBsplineCurve1")
    want = cm.to_bezier(_bl(out["cvs"]), out["knots"], 3)
    flat = [want[0][0]] + [p for seg in want for p in seg[1:]]
    assert err(cmaya.read_spline(new.data.splines[0]).cvs, flat) < TOL


def test_align_operator():
    if data() is None:
        return
    _clear()
    c = case("align_A3D_B2")
    a = _curve("curveA", named(c, "curveA", "before")["cvs"])
    b = _curve("curveB", named(c, "curveB", "before")["cvs"])
    _sel(a, b)                  # A first, B active (= Maya selection order)
    assert bpy.ops.allset.curve_align() == {'FINISHED'}
    assert err(_cvs(a), _bl(named(c, "curveA")["cvs"])) < TOL
    assert err(_cvs(b), _bl(named(c, "curveB")["cvs"])) < TOL


def test_duplicate_surface_curves_operator():
    if data() is None:
        return
    _clear()
    c = case("dup_object")
    s = _surf(c)
    s.cvs = [[c207.from_maya(p) for p in col] for col in s.cvs]
    surf = smaya.new_surface(bpy.context, "nurbsPlane", s)
    _sel(surf)
    assert bpy.ops.allset.duplicate_surface_curves() == {'FINISHED'}
    made = sorted((o for o in bpy.data.objects if o.name.startswith("duplicatedCurve")), key=lambda o: o.name)
    assert [o.name for o in made] == ["duplicatedCurve%d" % i for i in range(1, 7)], [o.name for o in made]
    for ob, out in zip(made, c["after"]):
        got = cmaya.read_spline(ob.data.splines[0], ob.matrix_world).cvs
        assert err(got, _bl(out["cvs"])) < TOL, ob.name


def test_intersect_operator():
    if data() is None:
        return
    _clear()
    c = case("intersect_AB")
    a = _curve("curveA", named(c, "curveA", "before")["cvs"])
    b = _curve("curveB", named(c, "curveB", "before")["cvs"])
    _sel(a, b)
    assert bpy.ops.allset.curve_intersect() == {'FINISHED'}
    locs = [o for o in bpy.data.objects if o.type == 'EMPTY']
    assert len(locs) == 4 and {o.parent.name for o in locs} == {"curveA", "curveB"}
    pa = [cm.evaluate(_cvs(a), cm.clamped_uniform(7, 3), 3, u) for u in
          c["curveIntersect"]["curveIntersect1"]["parameter1"][0]]
    for p in pa:
        assert min((o.matrix_world.translation - __import__("mathutils").Vector(p)).length for o in locs) < 1e-5


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


def test_undo_and_menu():
    if data() is None:
        return
    _clear()
    c = case("bend_A3D_0.2_0")
    ob = _curve("curveA", c["before"][0]["cvs_local"])
    _sel(ob)
    bpy.ops.ed.undo_push(message="before")
    first = _cvs(ob)
    assert bpy.ops.allset.curve_modify('EXEC_DEFAULT', True, kind='BEND') == {'FINISHED'}
    assert err(_cvs(bpy.data.objects["curveA"]), first) > 0.01
    bpy.ops.ed.undo()
    assert err(_cvs(bpy.data.objects["curveA"]), first) < 1e-9
    mm = import_module(kit.MODULE + ".ui.menu_map")
    for label in ("Lock Length", "Unlock Length", "Bend", "Curl", "Scale Curvature", "CV Hardness", "Fit B-spline",
                  "Align", "Duplicate Surface Curves", "Intersect"):
        assert "Curves/" + label in mm.MAP, label
    for key in ("bend_curves", "curl_curves", "scale_curvature"):
        assert hasattr(bpy.ops.allset, "opt_" + key), key


def test_report_worst():
    print("WORST", json.dumps({k: v for k, v in sorted(WORST.items())}, indent=0, default=str))


def test_modify_in_a_cm_scene_uses_maya_units():
    """Maya Bend / Curl amounts are lengths: in a cm scene (Maya Workflow Kit template) 1 Maya unit = 0.01 BU, so the
    same Maya curve scaled by 0.01 bends to the Maya result scaled by 0.01 ()."""
    if data() is None:
        return
    _clear()
    us = bpy.context.scene.unit_settings
    us.system, us.length_unit, us.scale_length = 'METRIC', 'CENTIMETERS', 1.0
    try:
        for key in ("bend_A3D_0.5_0.5", "curl_A3D_1_2.5"):
            c = case(key)
            op, a1, a2 = _modify_args(key, c)
            ob = _curve("curveA", [cm.mul(p, 0.01) for p in c["before"][0]["cvs_local"]])
            _sel(ob)
            assert bpy.ops.allset.curve_modify(kind=KIND[op], amount=a1, second=a2) == {'FINISHED'}
            want = _bl([cm.mul(p, 0.01) for p in named(c, "curveA")["cvs_local"]])
            assert err(_cvs(ob), want) < 1e-8, key
            _clear()
    finally:
        us.length_unit, us.system = 'METERS', 'METRIC'
