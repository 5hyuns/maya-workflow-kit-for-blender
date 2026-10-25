"""Step 181: Maya surface commands (operators/surfaces_math.py) against mayapy ground truth
(research/maya/re/surfaces_181.json, rules in research/maya/re/surfaces_181.md) and the Blender legacy NURBS
representation (research/blender/nurbs_surface_181.md). Coordinates stay Maya's: every rule is rotation-free and the
revolve axis / extrude direction are passed as Maya vectors (read from each case's history node)."""

import json
import math
import os
from importlib import import_module

import kit

sm = import_module(kit.MODULE + ".operators.surfaces_math")

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "research", "maya", "re", "surfaces_181.json")
TOL = 1e-6
_D = None


def data():
    global _D
    if _D is None:
        with open(DATA, encoding="utf-8") as fh:
            _D = json.load(fh)
    return _D


def case(k):
    c = data()["cases"][k]
    assert "error" not in c, k
    return c


def crv(c):
    return sm.Crv([tuple(p) for p in c["cvs"]], list(c["knots"]), c["degree"], c["form"] == "periodic")


def surf(o):
    return sm.Surf(o["cvs"], o["knots_u"], o["knots_v"], o["degree_uv"][0], o["degree_uv"][1],
                   o["form_uv"][0] == "periodic", o["form_uv"][1] == "periodic")


def out_surface(c, name=None):
    return next(o for o in c["after"] if o["kind"] == "nurbsSurface" and (name is None or o["name"] == name))


def history(o):
    return o["history"][0]["attrs"] if o.get("history") else {}


def compare(got, o, key):
    """knots + degrees + CVs of Surf ``got`` vs Maya surface dict ``o``; returns the max CV distance."""
    assert [got.degree_u, got.degree_v] == o["degree_uv"], (key, got.degree_u, got.degree_v, o["degree_uv"])
    for mine, theirs, label in ((got.knots_u, o["knots_u"], "u"), (got.knots_v, o["knots_v"], "v")):
        assert len(mine) == len(theirs), (key, label, mine, theirs)
        ek = max(abs(a - b) for a, b in zip(mine, theirs))
        assert ek < 1e-6, (key, label, ek, mine, theirs)
    assert [len(got.cvs), len(got.cvs[0])] == o["num_cvs_uv"], (key, len(got.cvs), len(got.cvs[0]), o["num_cvs_uv"])
    e = max(math.dist(got.cvs[i][j], o["cvs"][i][j]) for i in range(len(got.cvs)) for j in range(len(got.cvs[0])))
    assert e < TOL, (key, e)
    assert (got.periodic_u, got.periodic_v) == (o["form_uv"][0] == "periodic", o["form_uv"][1] == "periodic"), key
    return e


def report(name, errs):
    worst = max(errs.values()) if errs else 0.0
    print("%s: %d cases, max CV error %.2e" % (name, len(errs), worst))
    for k, v in sorted(errs.items()):
        print("    %-42s %.2e" % (k, v))


# --- Loft -----------------------------------------------------------------------------------------------

def test_loft():
    errs = {}
    for key, c in data()["cases"].items():
        if not key.startswith("loft") or "error" in c:
            continue
        o = out_surface(c)
        h = history(o)
        got = sm.loft([crv(b) for b in c["before"]], uniform=h["uniform"], close=h["close"], degree=h["degree"],
                      section_spans=h["sectionSpans"], auto_reverse=h["autoReverse"])
        errs[key] = compare(got, o, key)
    assert len(errs) >= 23, len(errs)
    report("loft", errs)


# --- Revolve --------------------------------------------------------------------------------------------

def test_revolve():
    errs = {}
    for key, c in data()["cases"].items():
        if not key.startswith("revolve") or "error" in c:
            continue
        o = out_surface(c)
        h = history(o)
        got = sm.revolve(crv(c["before"][0]), axis=(h["axisX"], h["axisY"], h["axisZ"]),
                         pivot=(h["pivotX"], h["pivotY"], h["pivotZ"]), start=h["startSweep"], end=h["endSweep"],
                         segments=h["sections"], degree=h["degree"])
        errs[key] = compare(got, o, key)
    assert len(errs) >= 14, len(errs)
    report("revolve", errs)


# --- Extrude --------------------------------------------------------------------------------------------

def test_extrude():
    errs, skipped, loose = {}, [], {}
    for key, c in data()["cases"].items():
        if not key.startswith("extrude") or "error" in c:
            continue
        o = out_surface(c)
        h = history(o)
        if abs(h["rotation"]) > 1e-9 or abs(h["scale"] - 1.0) > 1e-9:
            skipped.append(key)          # rotation / scale: Maya rule [U] (surfaces_181.md 4.4)
            continue
        prof = crv(next(b for b in c["before"] if b["name"] == "prof"))
        path = next((crv(b) for b in c["before"] if b["name"] == "path"), None)
        if h["extrudeType"] == 2:
            got = sm.extrude_tube(prof, path, (h["pivotX"], h["pivotY"], h["pivotZ"]), at_path=h["fixedPath"],
                                  component_pivot=bool(h["useComponentPivot"]))
        elif h["extrudeType"] == 1:
            got = sm.extrude_flat(prof, path)
        else:
            d = None if h["useProfileNormal"] else (h["directionX"], h["directionY"], h["directionZ"])
            got = sm.extrude_distance(prof, d, h["length"])
        if path is not None and path.degree == 1 and h["extrudeType"] == 2:
            # degree-1 path: knots exact, interior ring directions [U] (not the control-polygon bisector)
            assert got.knots_u == o["knots_u"] and got.knots_v == o["knots_v"], key
            loose[key] = max(math.dist(got.cvs[i][j], o["cvs"][i][j])
                             for i in range(len(got.cvs)) for j in range(len(got.cvs[0])))
            assert loose[key] < 0.1, loose
            continue
        errs[key] = compare(got, o, key)
    assert len(errs) >= 16, len(errs)
    report("extrude (skipped rotation / scale: %s)" % ", ".join(sorted(skipped)), errs)
    report("extrude tube along a degree-1 path ([U], loose bound 0.1)", loose)


# --- Birail 1 ---------------------------------------------------------------------------------------------

PLANAR_RAILS = ("birail1_straight", "birail1_straight_div", "birail1_straight_div_tm0", "birail1_planar_curved")


def test_birail1():
    errs, twisted = {}, {}
    for key, c in data()["cases"].items():
        if not key.startswith("birail1") or "error" in c:
            continue
        o = out_surface(c)
        prof, r1, r2 = (crv(b) for b in c["before"])
        got = sm.birail1(prof, r1, r2, proportional=bool(history(o)["transformMode"]))
        if key in PLANAR_RAILS:
            errs[key] = compare(got, o, key)
        else:   # twisted rails: knots exact, CVs [U] (surfaces_181.md 4.5)
            assert got.knots_u == o["knots_u"] and got.knots_v == o["knots_v"], key
            twisted[key] = max(math.dist(got.cvs[i][j], o["cvs"][i][j])
                               for i in range(len(got.cvs)) for j in range(len(got.cvs[0])))
    assert set(errs) == set(PLANAR_RAILS), errs
    report("birail 1 (planar rails)", errs)
    report("birail 1 (twisted rails, [U], not asserted)", twisted)


# --- Boundary / Square --------------------------------------------------------------------------------------

def test_boundary_square():
    errs = {}
    for key in ("boundary3", "boundary4", "square4"):
        c = case(key)
        curves = [crv(b) for b in c["before"]]
        errs[key] = compare(sm.boundary(curves), out_surface(c), key)
        # the automatic ordering keeps an already head-to-tail selection, and repairs a shuffled / reversed one
        ordered = sm.order_boundary(curves)
        assert all(a.cvs == b.cvs for a, b in zip(ordered, curves)), key
        shuffled = [curves[0]] + [sm._reverse_curve(x) for x in curves[1:][::-1]]
        errs[key + "_reordered"] = compare(sm.boundary(sm.order_boundary(shuffled)), out_surface(c), key)
    report("boundary / square", errs)


def test_boundary_multi_span_coons():
    """[I] multi-span sides: the Coons patch on CV nets reproduces its four boundary curves exactly."""
    c = case("loft4")
    s = surf(out_surface(c))                 # a 2 x 3-span surface: its four edges as boundary curves
    du, dv = s.degree_u, s.degree_v
    e_v0 = sm.Crv([s.cvs[i][0] for i in range(len(s.cvs))], s.knots_u, du)
    e_u1 = sm.Crv(list(s.cvs[-1]), s.knots_v, dv)
    e_v1 = sm.Crv([s.cvs[i][-1] for i in range(len(s.cvs))][::-1], [s.knots_u[0] + s.knots_u[-1] - k
                                                                    for k in s.knots_u[::-1]], du)
    e_u0 = sm.Crv(list(s.cvs[0])[::-1], [s.knots_v[0] + s.knots_v[-1] - k for k in s.knots_v[::-1]], dv)
    b = sm.boundary([e_v0, e_u1, e_v1, e_u0])
    worst = 0.0
    for a in range(9):
        for c_ in range(9):
            # same parameters after normalisation to 0..1
            u = s.knots_u[0] + (s.knots_u[-1] - s.knots_u[0]) * a / 8
            v = s.knots_v[0] + (s.knots_v[-1] - s.knots_v[0]) * c_ / 8
            if a in (0, 8) or c_ in (0, 8):
                worst = max(worst, math.dist(b.point(a / 8, c_ / 8), s.point(u, v)))
    assert worst < 1e-9, worst
    print("boundary multi-span: edges reproduced, max %.2e" % worst)


# --- Attach / Detach / Insert / Reverse / Duplicate patch ------------------------------------------------------

def test_attach():
    errs = {}
    for key in ("attach_surfaces", "attach_surfaces_gap"):
        c = case(key)
        A, B = surf(c["before"][0]), surf(c["before"][1])
        o = next(x for x in c["after"] if x["name"].endswith("attachedSurface1"))
        errs[key] = compare(sm.attach(A, B), o, key)
        # B turned around (reversed U, swapped) still finds the same edge pair and gives the same shape
        for mode in ("U", "SWAP", "BOTH"):
            g = sm.attach(A, sm.reverse(B, mode))
            pts = [g.point(*p) for p in ((0.3, 0.7), (1.0, 1.5), (1.7, 2.9))]
            ref = [surf(o).point(*p) for p in ((0.3, 0.7), (1.0, 1.5), (1.7, 2.9))]
            e = max(math.dist(p, q) for p, q in zip(pts, ref))
            assert e < 1e-9, (key, mode, e)
    c = case("attach_surfaces")
    con = sm.attach(surf(c["before"][0]), surf(c["before"][1]), "CONNECT")
    assert con.knots_u == [0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 2.0, 2.0, 2.0], con.knots_u
    report("attach", errs)


def test_detach_insert_patch_reverse():
    errs = {}
    for key, d, t in (("detach_u", "U", 0.5), ("detach_v", "V", 1.5)):
        c = case(key)
        a, b = sm.detach(surf(c["before"][0]), d, t)
        errs[key] = max(compare(a, out_surface(c, "surfA"), key),
                        compare(b, out_surface(c, "surfAdetachedSurface2"), key))
    for key, d, t in (("insert_isoparm_u", "U", 0.5), ("insert_isoparm_v", "V", 2.5)):
        c = case(key)
        errs[key] = compare(sm.insert_knot(surf(c["before"][0]), d, t), out_surface(c), key)
    for key, mode in (("reverse_u", "U"), ("reverse_v", "V"), ("reverse_both", "BOTH"), ("reverse_swap", "SWAP"),
                      ("reverse_factory", "U")):
        c = case(key)
        errs[key] = compare(sm.reverse(surf(c["before"][0]), mode), out_surface(c), key)
    c = case("duplicate_patch")
    h = out_surface(c, "duplicatedSurface1")["history"][0]["attrs"]
    u0, v0 = float(h["firstFaceU"]), float(h["firstFaceV"])     # patch [0][1]: U 0..1, V 1..2 (unit spans)
    got = sm.sub_patch(surf(c["before"][0]), u0, u0 + h["faceCountU"], v0, v0 + h["faceCountV"])
    errs["duplicate_patch"] = compare(got, out_surface(c, "duplicatedSurface1"), "duplicate_patch")
    report("detach / insert / reverse / patch", errs)


def test_periodic_open_and_detach():
    """Periodic directions opened (detach at an isoparm, insert) keep the shape exactly."""
    o = out_surface(case("revolve"))           # V periodic (8 spans)
    s = surf(o)
    opened, none = sm.detach(s, "V", 2.0)
    assert none is None and not opened.periodic_v and opened.domain_v() == (2.0, 10.0), opened
    ins = sm.insert_knot(s, "V", 3.5)
    worst = 0.0
    for a in range(7):
        for b in range(7):
            u = 2.0 * a / 6
            v = 8.0 * b / 6
            ref = o["samples"][a][b]
            worst = max(worst, math.dist(s.point(u, v), ref), math.dist(ins.point(u, v), ref),
                        math.dist(opened.point(u, v if v >= 2.0 else v + 8.0), ref))
    assert worst < 1e-6, worst
    print("periodic open / insert / detach: max %.2e vs Maya samples" % worst)


# --- Rebuild ------------------------------------------------------------------------------------------------------

def test_rebuild():
    c = case("rebuild_surface")
    o = out_surface(c)
    src = surf(c["before"][0])
    got = sm.rebuild(src, 4, 4, 3, 3)
    assert got.knots_u == o["knots_u"] and got.knots_v == o["knots_v"], (got.knots_u, got.knots_v)
    assert [len(got.cvs), len(got.cvs[0])] == o["num_cvs_uv"]
    cv_err = max(math.dist(got.cvs[i][j], o["cvs"][i][j]) for i in range(7) for j in range(7))
    same_param = max(math.dist(got.point(a / 6, b / 6), o["samples"][a][b]) for a in range(7) for b in range(7))
    # shape: distance of Maya's samples to the rebuilt surface (dense grid closest point)
    grid = [got.point(a / 60, b / 60) for a in range(61) for b in range(61)]
    shape = max(min(math.dist(p, q) for q in grid) for row in o["samples"] for p in row)
    print("rebuild [U]: knots exact; CV error %.4f, same-parameter error %.4f, shape error %.4f (60x60 grid)"
          % (cv_err, same_param, shape))
    assert cv_err < 0.1 and same_param < 0.05 and shape < 0.05, (cv_err, same_param, shape)
    # exact when the new knots contain the old ones: 2 U spans -> 4 keeps the shape at the same (scaled) parameters
    up = sm.rebuild(src, 4, 3, 3, 3)
    e = max(math.dist(up.point(a / 6, b / 6), src.point(2 * a / 6, 3 * b / 6)) for a in range(7) for b in range(7))
    assert e < 1e-9, e


# --- Blender representation -------------------------------------------------------------------------------------

def _blender_knots(n, order, cyclic, endpoint, bezier):
    """Blender's full knot vector + domain (research/blender/nurbs_surface_181.md facts 2-4)."""
    k = order
    if cyclic:
        m = n + k - 1                     # wrapped point count
        return [float(i) for i in range(m + k)], (k - 1.0, n + k - 1.0)
    if bezier and endpoint:
        mm = (n - 1) // (k - 1)
        kv = [0.0] * k
        for x in range(1, mm):
            kv += [float(x)] * (k - 1)
        kv += [float(mm)] * k
        return kv, (0.0, float(mm))
    assert endpoint
    kv = [0.0] * k + [float(i) for i in range(1, n - k + 1)] + [float(n - k + 1)] * k
    return kv, (0.0, float(n - k + 1))


def _cox(U, i, k, t, last):
    """Textbook Cox-de Boor N_{i,k} (order k); the domain end ``last`` is closed when it is the last knot."""
    if k == 1:
        if U[i] <= t < U[i + 1] or (t == last == U[-1] and U[i] < U[i + 1] == last):
            return 1.0
        return 0.0
    a = (t - U[i]) / (U[i + k - 1] - U[i]) * _cox(U, i, k - 1, t, last) if U[i + k - 1] != U[i] else 0.0
    b = ((U[i + k] - t) / (U[i + k] - U[i + 1]) * _cox(U, i + 1, k - 1, t, last)
         if U[i + k] != U[i + 1] else 0.0)
    return a + b


def blender_eval(g, s_u, s_v):
    """Independent evaluator of the Blender surface at Blender parameters."""
    rows = g["rows"]
    nv, nu = len(rows), len(rows[0])
    Uu, du_ = _blender_knots(nu, g["order_u"], g["cyclic_u"], g["endpoint_u"], g["bezier_u"])
    Uv, dv_ = _blender_knots(nv, g["order_v"], g["cyclic_v"], g["endpoint_v"], g["bezier_v"])
    pu = list(range(nu)) + (list(range(g["order_u"] - 1)) if g["cyclic_u"] else [])
    pv = list(range(nv)) + (list(range(g["order_v"] - 1)) if g["cyclic_v"] else [])
    bu = [_cox(Uu, i, g["order_u"], s_u, du_[1]) for i in range(len(pu))]
    bv = [_cox(Uv, j, g["order_v"], s_v, dv_[1]) for j in range(len(pv))]
    out = [0.0, 0.0, 0.0]
    for jj, wv in enumerate(bv):
        if not wv:
            continue
        for ii, wu in enumerate(bu):
            if wu:
                p = rows[pv[jj]][pu[ii]]
                for c in range(3):
                    out[c] += wu * wv * p[c]
    return out, du_, dv_


def test_blender_grid_round_trip():
    worst, modes, count = 0.0, {}, 0
    for key, c in data()["cases"].items():
        if "error" in c:
            continue
        for o in c["after"]:
            if o["kind"] != "nurbsSurface" or o.get("trimmed") or o.get("rational"):
                continue
            s = surf(o)
            g = sm.blender_grid(s)
            nv, nu = len(g["rows"]), len(g["rows"][0])
            assert g["order_u"] <= nu and g["order_v"] <= nv, key
            for d in ("u", "v"):
                if g["bezier_" + d]:
                    n = nu if d == "u" else nv
                    assert (n - 1) % (g["order_" + d] - 1) == 0, (key, d, n)
            mode = tuple("C" if g["cyclic_" + d] else "B" if g["bezier_" + d] else "E" for d in "uv")
            modes[mode] = modes.get(mode, 0) + 1
            u0, u1 = s.domain_u()
            v0, v1 = s.domain_v()
            for a in range(9):
                for b in range(9):
                    u, v = u0 + (u1 - u0) * a / 8, v0 + (v1 - v0) * b / 8
                    bp, _du, _dv = blender_eval(g, sm.map_param(g["map_u"], u), sm.map_param(g["map_v"], v))
                    worst = max(worst, math.dist(bp, s.point(u, v)))
            # back to Maya knots: same shape (endpoint / cyclic keep the CVs; bezier keeps the decomposed CVs)
            back = sm.from_blender_grid(g["rows"], g["order_u"], g["order_v"], g["cyclic_u"], g["cyclic_v"],
                                        g["endpoint_u"], g["endpoint_v"], g["bezier_u"], g["bezier_v"])
            g2 = sm.blender_grid(back)
            assert g2["rows"] == g["rows"], key
            if not g["bezier_u"] and not g["bezier_v"] and s.degree_u > 1 and s.degree_v > 1:
                assert len(back.cvs) == len(s.cvs) and len(back.cvs[0]) == len(s.cvs[0]), key
                e = max(math.dist(back.cvs[i][j], s.cvs[i][j])
                        for i in range(len(s.cvs)) for j in range(len(s.cvs[0])))
                assert e < 1e-12, (key, e)
            count += 1
            # Maya samples at the same parameters (independent of Surf.point)
            for a in range(7):
                for b in range(7):
                    u, v = u0 + (u1 - u0) * a / 6, v0 + (v1 - v0) * b / 6
                    bp, _du, _dv = blender_eval(g, sm.map_param(g["map_u"], u), sm.map_param(g["map_v"], v))
                    worst = max(worst, math.dist(bp, o["samples"][a][b]))
    assert worst < 1e-5, worst
    assert count >= 80, count
    print("blender_grid: %d surfaces, modes %s, max error %.2e (vs Surf.point and Maya samples)"
          % (count, dict(sorted(modes.items())), worst))


def test_blender_grid_layout():
    """Endpoint / cyclic keep Maya's CVs one to one; rows[j][i] = Maya cv[i][j]; cyclic drops the wrap CVs."""
    o = out_surface(case("revolve"))            # U open uniform 5 CVs, V periodic 8 + 3
    g = sm.blender_grid(surf(o))
    assert (g["endpoint_u"], g["cyclic_v"], g["order_u"], g["order_v"]) == (True, True, 4, 4), g
    assert len(g["rows"]) == 8 and len(g["rows"][0]) == 5
    assert all(g["rows"][j][i] == tuple(o["cvs"][i][j]) for j in range(8) for i in range(5))
    o = out_surface(case("loft3_chord"))        # V chord knots: Bezier decomposition
    g = sm.blender_grid(surf(o))
    assert g["bezier_v"] and g["endpoint_v"] and not g["bezier_u"] and len(g["rows"]) == 7, len(g["rows"])
    o = out_surface(case("loft3_lin"))          # degree 1 V: order 2, knots irrelevant
    g = sm.blender_grid(surf(o))
    assert g["order_v"] == 2 and not g["bezier_v"] and len(g["rows"]) == 3
