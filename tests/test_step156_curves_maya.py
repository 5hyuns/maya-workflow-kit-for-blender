"""Step 156: Maya curve commands against mayapy ground truth (research/maya/re/curves_156.json, rules in
research/maya/re/curves_156.md). Coordinates stay Maya's (every rule is rotation-free; the two-point arc normal is
passed in Maya axes)."""

import json
import os
from importlib import import_module

import bpy

import kit

cm = import_module(kit.MODULE + ".operators.curves_math")
cmaya = import_module(kit.MODULE + ".operators.curves_maya")

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "research", "maya", "re", "curves_156.json")
_D = None


def data():
    global _D
    if _D is None:
        with open(DATA, encoding="utf-8") as fh:
            _D = json.load(fh)
    return _D


def case(k):
    return data()["cases"][k]


def crv(c):
    return [tuple(x) for x in c["cvs"]], list(c["knots"]), c["degree"]


def err(got, want):
    assert len(got) == len(want), (len(got), len(want))
    return max(max(abs(a - b) for a, b in zip(g, w)) for g, w in zip(got, want))


def test_ep_curve_tool_uniform_and_chord():
    tc = data()["gui_tools"]["tool_curves"]
    for key, uniform in (("ep_p4", True), ("ep_p7", True), ("ep_p7_chord", False)):
        c = tc[key]["curves"][0]
        cvs, knots, _d = cm.ep_curve(c["edit_points"], 3, uniform)
        assert err(cvs, c["cvs"]) < 1e-5, key
        assert max(abs(a - b) for a, b in zip(knots, c["knots"])) < 1e-5, key


def test_cv_curve_tool_knots():
    c = data()["gui_tools"]["tool_curves"]["cv_p7"]["curves"][0]
    cvs, knots, d = cm.cv_curve(c["cvs"], 3)
    assert knots == c["knots"] and d == 3


ARC3 = {"half": [(0, 0, 0), (2, 0, -2), (4, 0, 0)], "quarter_ish": [(0, 0, 0), (1, 0, -2), (3, 0, -3)],
        "big_sweep": [(0, 0, 0), (4, 0, 0), (1, 0, 1)], "tilted": [(0, 0, 0), (2, 2, -1), (5, 0, -3)]}
ARC2 = {"x4": [(0, 0, 0), (4, 0, 0)], "diag": [(0, 0, 0), (3, 0, -2)], "tilted": [(0, 0, 0), (2, 2, -1)]}


def test_three_point_arcs():
    for k, pts in ARC3.items():
        for d, s in ((3, 8), (1, 8), (3, 4), (3, 16)):
            a = case(f"arc3_{k}_d{d}_s{s}")["after"][0]
            cvs, knots, _ = cm.arc3(*pts, sections=s, degree=d)
            assert err(cvs, a["cvs"]) < 1e-5, (k, d, s)
            assert max(abs(x - y) for x, y in zip(knots, a["knots"])) < 1e-5, (k, d, s)


def test_two_point_arcs():
    for k, pts in ARC2.items():
        for r, t, dv in ((None, False, None), (3.0, False, None), (3.0, True, None), (3.0, False, (0, 0, 1)),
                         (1.0, False, None)):
            key = f"arc2_{k}_r{'def' if r is None else r}_t{int(t)}_{'dirdef' if dv is None else 'dirz'}"
            a = case(key)["after"][0]
            # the node defaults: radius 1, directionVector (0, 0, 1) (curves_156.md 4.2)
            cvs, _k, _d = cm.arc2(*pts, normal=(0, 0, 1), radius=1.0 if r is None else r, toggle=t)
            assert err(cvs, a["cvs"]) < 1e-5, key


def _result(c, marker):
    return next(a for a in c["after"] if marker in a["name"])


def test_attach():
    for k in ("attach_gap", "attach_gap_BA", "attach_gap_Brev", "attach_gap_bias0", "attach_gap_bias1",
              "attach_touch", "attach_long_B", "attach_d2_gap", "attach_d1_gap", "attach_gap_connect",
              "attach_touch_connect"):
        c = case(k)
        A, B = crv(c["before"][0]), crv(c["before"][1])
        if k.endswith("_BA"):
            A, B = B, A
        bias = 0.0 if "bias0" in k else 1.0 if "bias1" in k else 0.5
        cvs, knots = cm.attach((A[0], A[1]), (B[0], B[1]), A[2], "CONNECT" if "connect" in k else "BLEND", bias)
        out = _result(c, "attach")
        assert err(cvs, out["cvs"]) < 1e-6, k
        assert max(abs(x - y) for x, y in zip(knots, out["knots"])) < 1e-6, k


def test_detach_cut_straighten_seam():
    for k in ("detach_A_u1.5", "detach_A_u2", "detach_A_u0.7_u3.2", "detach_NU_u2"):
        c = case(k)
        A = crv(c["before"][0])
        cur, pieces = (A[0], A[1]), []
        for u in (float(x) for x in k.split("_u")[1:]):
            a, cur = cm.split(cur[0], cur[1], A[2], u)
            pieces.append(a)
        pieces.append(cur)
        assert len(pieces) == len(c["after"]), k
        for p, o in zip(pieces, c["after"]):
            assert err(p[0], o["cvs"]) < 1e-6 and max(abs(x - y) for x, y in zip(p[1], o["knots"])) < 1e-6, k
    for k in ("cut_AB", "cut_AB2", "cut_ABC", "cut_AB_lifted_3d"):
        c = case(k)
        res = cm.cut_all([(*crv(b), None) for b in c["before"]])
        flat = [p for ps in res for p in ps]
        assert len(flat) == len(c["after"]), k
        for p in flat:
            assert any(len(o["cvs"]) == len(p[0]) and err(p[0], o["cvs"]) < 1e-6 for o in c["after"]), k
    for k in ("straighten_A", "straighten_A3D"):
        c = case(k)
        assert err(cm.straighten(crv(c["before"][0])[0]), c["after"][-1]["cvs"]) < 1e-6, k
    for k in ("seam_loop_u3", "seam_loop_u2.4"):
        c = case(k)
        cvs, knots, d = crv(c["before"][0])
        assert err(cm.move_seam(cvs, knots, d, float(k.split("_u")[1])), c["after"][-1]["cvs"]) < 1e-6, k


def test_fillet():
    for k, r in (("fillet_corner", 1.0), ("fillet_corner_r2", 2.0), ("fillet_angle", 1.0), ("fillet_cross", 1.0)):
        c = case(k)
        A, B = crv(c["before"][0]), crv(c["before"][1])
        cvs, knots, w = cm.fillet_curves((*A, None), (*B, None), r)
        o = c["after"][-1]
        assert err(cvs, o["cvs"]) < 1e-6, k
        assert max(abs(x - y) for x, y in zip(w, o["cv_w"])) < 1e-6, k
        assert abs(knots[-1] - o["knots"][-1]) < 1e-6, k


def test_rebuild_shape():
    # the exact Maya Rebuild algorithm is unknown [U]: the kit fit keeps the ends, end tangents, knots and spans;
    # its shape stays within 0.6 % of the curve length of the Maya result (curves_156.md 4.3)
    for k in ("rebuild_A", "rebuild_A3D", "rebuild_EP7", "rebuild_NU", "rebuild_A_s2", "rebuild_A_s12",
              "rebuild_line3"):
        c = case(k)
        A = crv(c["before"][0])
        o = c["after"][-1]
        cvs, knots, d = cm.rebuild(A[0], A[1], A[2], spans=int(o["spans"]), new_degree=o["degree"])
        assert len(cvs) == len(o["cvs"]) and max(abs(x - y) for x, y in zip(knots, o["knots"])) < 1e-6, k
        assert err([cvs[0], cvs[-1]], [o["cvs"][0], o["cvs"][-1]]) < 1e-6, k
        sm = cm.samples(cvs, knots, d, 400)
        dev = max(min(cm.norm(cm.sub(p, q)) for q in sm) for p in o["samples_param"])
        assert dev < 0.006 * o["length"], (k, dev, o["length"])


def _blender_points(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    pts = [tuple(v.co) for v in me.vertices]
    ev.to_mesh_clear()
    return pts


def _shape_dev(ob, c, n=1500):
    if c.periodic:      # the domain of a periodic curve is knots[degree - 1] .. knots[-degree]
        a, b = c.knots[c.degree - 1], c.knots[-c.degree]
        ref = [cm.evaluate(c.cvs, c.knots, c.degree, a + (b - a) * i / (n - 1), c.weights) for i in range(n)]
    else:
        ref = cm.samples(c.cvs, c.knots, c.degree, n, c.weights)
    return max(min(cm.norm(cm.sub(p, q)) for q in ref) for p in _blender_points(ob))


def test_write_spline_draws_the_maya_curve():
    """What Blender draws = the Maya curve: NURBS endpoint (EP / arcs), rational (fillet), Bezier (a non-uniform
    detach piece), POLY (degree 1), cyclic NURBS (periodic)."""
    ctx = bpy.context
    tc = data()["gui_tools"]["tool_curves"]
    curves = []
    cvs, knots, d = cm.ep_curve(tc["ep_p7"]["curves"][0]["edit_points"])
    curves.append(cmaya.MCurve(cvs, knots, d))
    cvs, knots, d = cm.arc3(*ARC3["big_sweep"])
    curves.append(cmaya.MCurve(cvs, knots, d))
    A, B = crv(case("fillet_angle")["before"][0]), crv(case("fillet_angle")["before"][1])
    cvs, knots, w = cm.fillet_curves((*A, None), (*B, None), 1.0)
    curves.append(cmaya.MCurve(cvs, knots, 3, w))
    A = crv(case("detach_A_u1.5")["before"][0])
    (p0, k0), _rest = cm.split(A[0], A[1], 3, 1.5)
    curves.append(cmaya.MCurve(p0, k0, 3))
    curves.append(cmaya.MCurve([(0, 0, 0), (1, 2, 0), (3, 1, 1)], [0.0, 1.0, 2.0], 1))
    c = case("seam_loop_u3")["before"][0]
    curves.append(cmaya.MCurve([tuple(x) for x in c["cvs"]], c["knots"], c["degree"], periodic=True))
    for i, c in enumerate(curves):
        ob = cmaya._new_curve_object(ctx, "check", [c])
        ob.data.resolution_u = 32
        for sp in ob.data.splines:
            sp.resolution_u = 32
        dev = _shape_dev(ob, c)
        kind = ob.data.splines[0].type
        assert dev < 2e-3 * max(1.0, max(cm.norm(v) for v in c.cvs)), (i, kind, dev)
        back = cmaya.read_spline(ob.data.splines[0])
        if kind == 'NURBS' and not c.periodic:
            assert err(back.cvs, c.cvs) < 1e-6
        bpy.data.objects.remove(ob)


def _object(name, c):
    ob = cmaya._new_curve_object(bpy.context, name, [c])
    ob.name = name
    return ob


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


def test_operators_end_to_end():
    _clear()
    c = case("attach_gap")
    A = _object("curveA", cmaya.MCurve(*crv(c["before"][0])))
    B = _object("curveB", cmaya.MCurve(*crv(c["before"][1])))
    _sel(A, B)                               # A first, B last (= active): the Maya selection order
    assert bpy.ops.allset.curve_attach() == {'FINISHED'}
    new = bpy.context.view_layer.objects.active
    assert new.name.startswith("curveAattachedCurve"), new.name
    got = cmaya.read_spline(new.data.splines[0])
    assert err(got.cvs, _result(c, "attach")["cvs"]) < 1e-5
    assert "curveA" in bpy.data.objects and "curveB" in bpy.data.objects      # keep originals (factory)

    _clear()
    c = case("fillet_corner")
    A = _object("curveA", cmaya.MCurve(*crv(c["before"][0])))
    B = _object("curveB", cmaya.MCurve(*crv(c["before"][1])))
    _sel(A, B)
    bpy.ops.allset.curve_fillet(radius=1.0 / max(1e-9, cmaya.units.maya_unit(bpy.context.scene)))
    f = bpy.context.view_layer.objects.active
    assert f.name.startswith("filletedCurve"), f.name
    got = cmaya.read_spline(f.data.splines[0])
    assert err(got.cvs, c["after"][-1]["cvs"]) < 1e-5 and got.weights and abs(got.weights[1] - 0.8047379) < 1e-6

    _clear()
    c = case("cut_AB")
    A = _object("curveA", cmaya.MCurve(*crv(c["before"][0])))
    B = _object("curveB", cmaya.MCurve(*crv(c["before"][1])))
    _sel(A, B)
    assert bpy.ops.allset.curve_cut() == {'FINISHED'}
    names = sorted(o.name for o in bpy.data.objects)
    assert len(names) == 4 and any(n.startswith("curveAdetachedCurve") for n in names), names

    _clear()
    c = case("detach_A_u2")
    A = _object("curveA", cmaya.MCurve(*crv(c["before"][0])))
    _sel(A)
    bpy.ops.object.mode_set(mode='EDIT')
    for i, p in enumerate(A.data.splines[0].points):
        p.select = i == 3                    # CV 3: Greville parameter 2 = the edit point at u 2
    assert bpy.ops.allset.curve_detach() == {'FINISHED'}
    assert bpy.context.mode == 'OBJECT'
    pieces = [cmaya.read_spline(o.data.splines[0]) for o in sorted(bpy.data.objects, key=lambda o: o.name)]
    assert len(pieces) == 2
    for p, o in zip(pieces, c["after"]):
        assert err(p.cvs, o["cvs"]) < 1e-5

    _clear()
    c = case("straighten_A")
    A = _object("curveA", cmaya.MCurve(*crv(c["before"][0])))
    _sel(A)
    assert bpy.ops.allset.curve_straighten() == {'FINISHED'}
    assert err(cmaya.read_spline(A.data.splines[0]).cvs, c["after"][-1]["cvs"]) < 1e-5

    _clear()
    c = case("rebuild_A")
    A = _object("curveA", cmaya.MCurve(*crv(c["before"][0])))
    _sel(A)
    assert bpy.ops.allset.curve_rebuild() == {'FINISHED'}
    got = cmaya.read_spline(A.data.splines[0])
    assert len(got.cvs) == 7 and got.knots == [0.0, 0.0, 0.0, 1.0, 2.0, 3.0, 4.0, 4.0, 4.0]


def test_operators_undo_only():
    for cls in cmaya.classes:
        assert 'UNDO' in cls.bl_options
