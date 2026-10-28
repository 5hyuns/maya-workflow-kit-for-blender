"""Step 181: the Surfaces menu operators (operators/surfaces_maya.py) on Blender objects against mayapy ground truth
(research/maya/re/surfaces_181.json). Inputs are built from the JSON in Maya coordinates turned into Blender's
(X, -Z, Y); results are checked twice: the Blender surface's CVs = Maya's CVs (uniform directions), and the vertices
Blender evaluates = Maya's surface at the same parameters (every direction, Bezier-decomposed ones included)."""

import json
from importlib import import_module

import bpy
from mathutils import Vector

import kit

sm = import_module(kit.MODULE + ".operators.surfaces_math")
smaya = import_module(kit.MODULE + ".operators.surfaces_maya")
cmaya = import_module(kit.MODULE + ".operators.curves_maya")

TOL = 1e-4          # task threshold (actual errors are float32 noise, ~1e-6)
_D = None


def data():
    global _D
    if _D is None:
        with open(kit.maya_data("maya", "re", "surfaces_181.json"), encoding="utf-8") as fh:
            _D = json.load(fh)
    return _D


def case(k):
    return data()["cases"][k]


def b(p):
    return (p[0], -p[2], p[1])


def _fresh():
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for d in list(bpy.data.curves):
        bpy.data.curves.remove(d)


def _curve_object(name, c):
    """A Blender curve object from a JSON Maya curve (world = object space, origin at 0)."""
    cvs = [b(p) for p in c["cvs"]]
    mc = cmaya.MCurve(cvs, c["knots"], c["degree"], None, c["form"] == "periodic")
    data_ = bpy.data.curves.new(name, 'CURVE')
    data_.dimensions = '3D'
    cmaya.write_spline(data_, mc)
    ob = bpy.data.objects.new(name, data_)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def _surface_object(name, s):
    return smaya.new_surface(bpy.context, name, _maya_surf(s), select=False)


def _maya_surf(s):
    return sm.Surf([[b(p) for p in col] for col in s["cvs"]], s["knots_u"], s["knots_v"], s["degree_uv"][0],
                   s["degree_uv"][1], s["form_uv"][0] == "periodic", s["form_uv"][1] == "periodic")


def _select(obs):
    for o in bpy.context.scene.objects:
        o.select_set(False)
    for o in obs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = obs[-1]


def _inputs(k):
    """Curve objects named so selection_order (others by name, active last) = Maya's selection order."""
    obs = [_curve_object(f"c{i}_{c['name']}", c) for i, c in enumerate(case(k)["before"])]
    _select(obs)
    return obs


def _out(k, name=None):
    surfs = [o for o in case(k)["after"] if o.get("kind") == "nurbsSurface"]
    return next(o for o in surfs if name is None or o["name"] == name)


def _new_object(base):
    obs = [o for o in bpy.data.objects if o.name.startswith(base)]
    assert obs, (base, [o.name for o in bpy.data.objects])
    return obs[-1]


def _check(ob, want):
    """CVs (uniform directions) and evaluated vertices vs Maya's surface ``want`` (JSON dict). Returns max errors."""
    ms = _maya_surf(want)
    grid = sm.blender_grid(ms)
    sp = ob.data.splines[0]
    nu, nv = sp.point_count_u, sp.point_count_v
    assert (nu, nv) == (len(grid["rows"][0]), len(grid["rows"])), ((nu, nv), len(grid["rows"][0]), len(grid["rows"]))
    for key in ("u", "v"):
        assert getattr(sp, "order_" + key) == grid["order_" + key], key
        assert getattr(sp, "use_cyclic_" + key) == grid["cyclic_" + key], key
        assert getattr(sp, "use_bezier_" + key) == grid["bezier_" + key], key
    mw = ob.matrix_world
    cv_err = max((mw @ Vector(sp.points[j * nu + i].co[:3]) - Vector(grid["rows"][j][i])).length
                 for j in range(nv) for i in range(nu))
    assert cv_err < TOL, cv_err
    # evaluated mesh: vertex i * totv + j at Blender parameters linspace over the domain (nurbs_surface_181.md)
    ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
    me = ev.to_mesh()
    try:
        cu, cv = ob.data.resolution_u * nu, ob.data.resolution_v * nv
        assert len(me.vertices) == cu * cv, (len(me.vertices), cu, cv)

        def params(brk, count, cyclic):
            lo, hi = brk[0][1], brk[-1][1]
            steps = count if cyclic else count - 1
            return [smaya._back(brk, lo + (hi - lo) * k / steps) for k in range(count)]
        us = params(grid["map_u"], cu, grid["cyclic_u"])
        vs = params(grid["map_v"], cv, grid["cyclic_v"])
        ev_err = 0.0
        for i in range(0, cu, max(1, cu // 9)):
            for j in range(0, cv, max(1, cv // 9)):
                got = mw @ me.vertices[i * cv + j].co
                ev_err = max(ev_err, (got - Vector(ms.point(us[i], vs[j]))).length)
    finally:
        ev.to_mesh_clear()
    assert ev_err < TOL, ev_err
    return cv_err, ev_err


def _run(k, op, base, **kw):
    _fresh()
    _inputs(k)
    assert op(**kw) == {'FINISHED'}, k
    return _check(_new_object(base), _out(k))


def test_loft_cases():
    # loft3_mixed_cvs is left to test_step181_surfaces_math: its chord-length EP curve has non-uniform knots, which a
    # Blender curve keeps only as a Bezier decomposition (step 156) -> other knots, other loft parameterisation
    errs = {}
    for k, kw in (("loft2", {}), ("loft3", {}), ("loft4", {}), ("loft5", {}), ("loft3_chord", {"uniform": False}),
                  ("loft3_close", {"close": True}), ("loft4_ss2", {"section_spans": 2}),
                  ("loft3_lin", {"degree": '1'}), ("loft3_mixed_deg", {}),
                  ("loft3_circles", {}), ("loft3_reversed", {}), ("loft2_arcs", {})):
        try:
            errs[k] = _run(k, bpy.ops.allset.loft, "loftedSurface", **kw)
        except AssertionError as ex:
            raise AssertionError(f"{k}: {ex}")
    print("loft", {k: "%.1e / %.1e" % v for k, v in errs.items()})
    ob = _new_object("loftedSurface")
    assert ob.type == 'SURFACE' and ob.name == "loftedSurface1" and ob.active_material is not None


def test_revolve_cases():
    errs = {}
    for k, kw in (("revolve", {}), ("revolve_ax_x", {"axis": 'X'}), ("revolve_ax_z", {"axis": 'Z'}),
                  ("revolve_180", {"end_sweep": 180.0}), ("revolve_30_200", {"start_sweep": 30.0, "end_sweep": 200.0}),
                  ("revolve_s4", {"segments": 4}), ("revolve_lin", {"degree": '1'}),
                  ("revolve_pivot", {"pivot": 'PRESET', "pivot_point": (1.0, 0.0, 0.5)}), ("revolve_arc", {})):
        errs[k] = _run(k, bpy.ops.allset.revolve, "revolvedSurface", **kw)
    print("revolve", {k: "%.1e / %.1e" % v for k, v in errs.items()})


def test_extrude_cases():
    errs = {}
    for k, kw in (("extrude_tube", {}), ("extrude_tube_open_profile", {}), ("extrude_tube_path7", {}),
                  ("extrude_flat", {"style": 'FLAT'}), ("extrude_dist", {"style": 'DISTANCE'}),
                  ("extrude_dist_dirY_len3", {"style": 'DISTANCE', "direction": 'Y', "length": 3.0}),
                  ("extrude_dist_dirX_dl1", {"style": 'DISTANCE', "direction": 'X', "length": 2.0})):
        errs[k] = _run(k, bpy.ops.allset.surface_extrude, "extrudedSurface", **kw)
    print("extrude", {k: "%.1e / %.1e" % v for k, v in errs.items()})


def test_birail_finds_profile_and_rails_by_shape():
    errs = {}
    for k, kw in (("birail1_straight", {}), ("birail1_straight_div", {}),
                  ("birail1_straight_div_tm0", {"proportional": False}), ("birail1_planar_curved", {})):
        _fresh()
        obs = _inputs(k)
        # shuffle the Blender selection order: the roles come from where the curves touch
        _select([obs[1], obs[2], obs[0]])
        assert bpy.ops.allset.birail1(**kw) == {'FINISHED'}, k
        errs[k] = _check(_new_object("singleProfileBirailSurface"), _out(k))
    print("birail", {k: "%.1e / %.1e" % v for k, v in errs.items()})


def test_boundary_and_square():
    errs = {}
    for k, kind, base in (("boundary3", 'BOUNDARY', "boundarySurface"), ("boundary4", 'BOUNDARY', "boundarySurface"),
                          ("square4", 'SQUARE', "squareSurface")):
        errs[k] = _run(k, bpy.ops.allset.surface_boundary, base, kind=kind)
    print("boundary", {k: "%.1e / %.1e" % v for k, v in errs.items()})


def test_attach_reverse_rebuild_on_surfaces():
    _fresh()
    c = case("attach_surfaces")
    a = _surface_object("surfA", c["before"][0])
    bb = _surface_object("surfB", c["before"][1])
    a.name, bb.name = "surfA", "surfB"
    _select([a, bb])
    assert bpy.ops.allset.surface_attach() == {'FINISHED'}
    ob = bpy.context.active_object
    assert ob.name == "surfAattachedSurface1", ob.name
    assert "surfA" in bpy.data.objects and "surfB" in bpy.data.objects       # Maya keeps both originals
    print("attach", _check(ob, _out("attach_surfaces", "surfAattachedSurface1")))
    for k, d in (("reverse_u", 'U'), ("reverse_v", 'V'), ("reverse_both", 'BOTH'), ("reverse_swap", 'SWAP')):
        _fresh()
        s = _surface_object("surfA", case(k)["before"][0])
        _select([s])
        assert bpy.ops.allset.surface_reverse(direction=d) == {'FINISHED'}, k
        print(k, _check(s, _out(k)))
    _fresh()
    s = _surface_object("surfA", case("rebuild_surface")["before"][0])
    _select([s])
    assert bpy.ops.allset.surface_rebuild() == {'FINISHED'}
    got = smaya.read_surface(s)
    want = _out("rebuild_surface")
    assert got.knots_u == want["knots_u"] and got.knots_v == want["knots_v"], (got.knots_u, want["knots_u"])


def _edit_select(ob, picks):
    """Edit mode on ``ob`` with exactly the Blender points (i, j) selected."""
    _select([ob])
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.curve.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    sp = ob.data.splines[0]
    nu = sp.point_count_u
    for i, j in picks:
        sp.points[j * nu + i].select = True
    bpy.ops.object.mode_set(mode='EDIT')


def test_detach_insert_patch_from_picked_cvs():
    # surfA: 4-curve factory loft, U 2 spans (5 CVs, knots 0 0 0 1 2 2 2), V 3 spans (6 CVs)
    src = case("detach_u")["before"][0]
    _fresh()
    s = _surface_object("surfA", src)
    s.name = "surfA"
    g = sm.greville(src["knots_u"], 3, len(src["cvs"]))
    i = min(range(len(g)), key=lambda k: abs(g[k] - 1.0))       # the CV column whose Greville u is the inner knot
    _edit_select(s, [(i, j) for j in range(len(src["cvs"][0]))])
    assert bpy.ops.allset.surface_detach() == {'FINISHED'}
    assert bpy.context.mode == 'OBJECT'
    t = g[i]
    want_a, want_b = sm.detach(_maya_surf(src), "U", t)
    pieces = [s, bpy.data.objects["surfAdetachedSurface1"]]
    for ob, want in zip(pieces, (want_a, want_b)):
        got = smaya.read_surface(ob)
        assert got.knots_u == want.knots_u, (got.knots_u, want.knots_u)
        err = max((Vector(p) - Vector(q)).length for cg, cw in zip(got.cvs, want.cvs) for p, q in zip(cg, cw))
        assert err < TOL, err
    # Insert Isoparms on a V row: one more CV row, same shape
    _fresh()
    s = _surface_object("surfA", src)
    before = smaya.read_surface(s)
    _edit_select(s, [(i, 2) for i in range(len(src["cvs"]))])
    assert bpy.ops.allset.surface_insert_isoparm() == {'FINISHED'}
    after = smaya.read_surface(s)
    assert after.num_cvs == (before.num_cvs[0], before.num_cvs[1] + 1), (after.num_cvs, before.num_cvs)
    for u in (0.0, 0.7, 1.3, 2.0):
        for v in (0.0, 0.9, 1.7, 2.4, 3.0):
            assert (Vector(after.point(u, v)) - Vector(before.point(u, v))).length < TOL
    # Duplicate NURBS Patch around one CV: a single patch
    _fresh()
    s = _surface_object("surfA", src)
    _edit_select(s, [(2, 2)])
    assert bpy.ops.allset.duplicate_nurbs_patch() == {'FINISHED'}
    p = smaya.read_surface(bpy.data.objects["duplicatedSurface1"])
    assert len(set(p.knots_u)) == 2 and len(set(p.knots_v)) == 2, (p.knots_u, p.knots_v)


def test_curves_from_step156_tools_loft():
    """EP / CV curve tool curves (step 156 builders) loft into a surface through them."""
    _fresh()
    a = cmaya.make_ep_curve(bpy.context, [(0, 0, 0), (2, 0, 1), (4, 0, 0), (6, 0, 1)])
    b2 = cmaya.make_cv_curve(bpy.context, [(0, 3, 0), (2, 3, 2), (4, 3, 2), (6, 3, 0)])
    a.name, b2.name = "a_ep", "b_cv"
    _select([a, b2])
    assert bpy.ops.allset.loft() == {'FINISHED'}
    s = smaya.read_surface(bpy.context.active_object)
    assert s.degree_v == 3 and len(set(s.knots_v)) == 2
    # the loft's v = 0 / v = 1 isoparms are the two curves
    from importlib import import_module as im
    cm = im(kit.MODULE + ".operators.curves_math")
    for ob, v in ((a, 0.0), (b2, 1.0)):
        c = cmaya.read_spline(ob.data.splines[0], ob.matrix_world)
        d0, d1 = s.domain_u()
        e0, e1 = c.knots[0], c.knots[-1]
        for k in range(7):
            f = k / 6
            p = cm.evaluate(c.cvs, c.knots, c.degree, e0 + (e1 - e0) * f)
            q = s.point(d0 + (d1 - d0) * f, v)
            assert (Vector(p) - Vector(q)).length < TOL, (ob.name, f, p, q)
