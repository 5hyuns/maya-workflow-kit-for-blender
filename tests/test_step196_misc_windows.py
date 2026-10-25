"""Step 196 lane B (issue #103): Maya option windows for Create Character Set / Subcharacter Set, Curves Cut / Detach /
Reverse Direction / Smooth (both) / Straighten, the circular arc tools, Merge UVs, Contour Stretch, Set / Assume
Preferred Angle and Add Influence (operators/option_windows_misc196.py).

Ground truth:  (window titles / buttons / factory values read from Maya 2022's
option-window MEL, Maya option effects) and  (curve cases)."""

import json
import math
import os
from importlib import import_module

import bmesh
import bpy

import kit

ow = import_module(kit.MODULE + ".operators.option_windows")
menu_sets = import_module(kit.MODULE + ".ui.menu_sets")
cmaya = import_module(kit.MODULE + ".operators.curves_maya")
cm = import_module(kit.MODULE + ".operators.curves_math")
rig = import_module(kit.MODULE + ".operators.rig_maya")

RE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "maya", "re")
_D = {}


def data(name):
    if name not in _D:
        with open(os.path.join(RE, name), encoding="utf-8") as fh:
            _D[name] = json.load(fh)
    return _D[name]


def maya():
    return data("options_196_misc.json")


def curve_case(k):
    return data("curves_156.json")["cases"][k]


PATHS = {
    "character_set": ("Control/Create Character Set", "Key/Create Character Set"),
    "subcharacter_set": ("Control/Create Subcharacter Set", "Key/Create Subcharacter Set"),
    "cut_curve": ("Curves/Cut",), "detach_curves": ("Curves/Detach",), "reverse_curve": ("Curves/Reverse Direction",),
    "smooth_curves": ("Curves/Smooth", "nHair/Modify Curves/Smooth"), "smooth_curve": ("Curves/Smooth#2",),
    "straighten_curves": ("Curves/Straighten", "nHair/Modify Curves/Straighten"),
    "arc3_tool": ("Create/Curve Tools/Three Point Circular Arc",),
    "arc2_tool": ("Create/Curve Tools/Two Point Circular Arc",),
    "merge_uvs": ("UV/Merge UVs",), "contour_stretch": ("UV/Contour Stretch",),
    "set_preferred_angle": ("Skeleton/Set Preferred Angle",),
    "assume_preferred_angle": ("Skeleton/Assume Preferred Angle",),
    "add_influence": ("Skin/Edit Influences/Add Influence",),
}


def err(got, want):
    assert len(got) == len(want), (len(got), len(want))
    return max(max(abs(a - b) for a, b in zip(g, w)) for g, w in zip(got, want))


def _clear():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)


def _sel(*obs):
    for o in bpy.context.scene.objects:
        o.select_set(o in obs)
    bpy.context.view_layer.objects.active = obs[-1] if obs else None


def run(key, **values):
    res = ow.run(ow._BY_KEY[key], bpy.context, values)
    assert not isinstance(res, str), (key, res)
    return res


# --- the windows ---------------------------------------------------------------------------------------

def test_every_box_is_a_maya_window_with_maya_defaults():
    spec = maya()["windows"]
    assert set(spec) == set(PATHS)
    for key, paths in PATHS.items():
        w = ow._BY_KEY[key]
        s = spec[key]
        for p in paths:
            assert menu_sets.option_kind(p) == "window", (p, menu_sets.option_kind(p))
            assert ow.find_path(p) is w, (p, ow.find_path(p) and ow.find_path(p).key)
        assert w.title == s["title"], (key, w.title)
        if not s["button"].startswith("("):          # tool settings have no command button
            assert w.action == s["button"], (key, w.action)
        assert len(w.fields) == len(s["fields"]), key
        for f, (label, kind, default, _note) in zip(w.fields, s["fields"]):
            assert f.default == default, (key, f.name, f.default, default)
            assert (f.label or f.text).rstrip(":") in (label.rstrip(":"), label.replace("No ", "").capitalize()), \
                (key, f.label, f.text, label)
        assert bool(w.missing) == bool(s["unsupported"]) or key == "cut_curve", key
        mod, name = w.idname.split(".")
        assert getattr(getattr(bpy.ops, mod), name).get_rna_type() is not None


def test_factory_values_agree_with_Maya_option_vars():
    v = maya()["Maya"]["setting"]
    d = {k: ow._BY_KEY[k].defaults() for k in PATHS}
    assert d["character_set"]["name"] == v["createCharacterName"] and v["characterKeysToUse"] == 2
    assert [d["character_set"][k] for k in ("no_translate", "no_rotate", "no_scale", "no_visibility", "no_dynamic",
                                            "hierarchy")] == \
        [bool(v[k]) for k in ("characterExcTranslate", "characterExcRotate", "characterExcScale", "characterExcVis",
                              "characterExcDyn", "characterHierarchy")]
    assert d["subcharacter_set"]["name"] == v["createSubCharacterName"]
    assert [d["subcharacter_set"][k] for k in ("no_translate", "no_rotate", "no_scale", "no_visibility",
                                               "no_dynamic")] == \
        [bool(v[k]) for k in ("subCharacterExcTranslate", "subCharacterExcRotate", "subCharacterExcScale",
                              "subCharacterExcVis", "subCharacterExcDyn")]
    assert v["cutCurveWithAllCurvesOrLastCurve"] == 1 and d["cut_curve"]["cut"] == "At all intersections"
    assert v["cutCurveSegmentOrKeepLongest"] == 2 and d["cut_curve"]["keep"] == "All curve segments"
    assert d["reverse_curve"]["keep_original"] == bool(v["reverseKeepOriginal"])
    assert d["smooth_curve"]["keep_original"] == bool(v["smoothCurveKeepOrig"])
    assert d["smooth_curves"]["factor"] == v["smoothHairCurvesSmoothFactor"]
    assert d["straighten_curves"]["straightness"] == v["straightenStraightness"]
    assert d["straighten_curves"]["preserve_length"] == bool(v["straightenPreserveLength"])
    assert v["recursive"] == 1 and d["set_preferred_angle"]["options"] == d["assume_preferred_angle"]["options"] \
        == "Hierarchy"
    assert d["add_influence"]["lock_weights"] == bool(v["lockWeights"])
    assert d["add_influence"]["default_weight"] == v["defaultWeight"]
    drag = maya()["Maya"]["drag"]
    assert drag["performSetPrefAngle 2"] == "joint -e -spa -ch"
    assert drag["performStraighten 2"] == "modifySelectedCurves straighten 1 1"
    assert drag["performSmoothHairCurves 2"] == "modifySelectedCurves smooth 4 0"


# --- character sets ------------------------------------------------------------------------------------

def cs():
    return import_module(kit.MODULE + ".operators.character_sets")


def _char_scene():
    sc = bpy.context.scene
    _clear()
    while sc.keying_sets:
        cs().remove_character(sc, sc.keying_sets[0])
    if cs().PARENT in sc:
        del sc[cs().PARENT]
    bpy.context.window_manager.allset_character_nodes = ""
    obs = []
    for name in ("pCube1", "pCube2"):
        ob = bpy.data.objects.new(name, bpy.data.meshes.new(name + "Shape"))
        sc.collection.objects.link(ob)
        obs.append(ob)
    obs[1].parent = obs[0]
    obs[0]["custom"] = 0.0
    _sel(obs[0])
    return obs


def _chars():
    sc = bpy.context.scene
    return {ks.bl_label: sorted(cs().member_names(sc, ks)) for ks in sc.keying_sets}


def test_character_set_window_follows_Maya():
    cases = maya()["Maya"]["cases"]
    for case, values in (("char_factory", {}), ("char_name_hero", {"name": "hero"}),
                         ("char_all_keyable", {"attributes": "All keyable"}),
                         ("char_except_rotate", {"no_rotate": True}),
                         ("char_except_translate_dyn", {"no_translate": True, "no_dynamic": True}),
                         ("char_hierarchy", {"hierarchy": True})):
        _char_scene()
        assert run("character_set", **values) == {'FINISHED'}, case
        assert _chars() == cases[case]["members"], (case, _chars(), cases[case]["members"])
    # the name counts up Maya's way (hero -> hero1, character1 -> character2)
    for case, values in (("char_name_hero_twice", {"name": "hero"}), ("char_factory_twice", {})):
        _char_scene()
        run("character_set", **values)
        run("character_set", **values)
        assert sorted(_chars()) == cases[case]["chars"], (case, sorted(_chars()))


def test_character_window_defaults_equal_the_plain_item():
    _char_scene()
    assert bpy.ops.allset.character_create('EXEC_DEFAULT') == {'FINISHED'}
    plain = _chars()
    _char_scene()
    run("character_set")
    assert _chars() == plain


def test_subcharacter_window():
    obs = _char_scene()
    run("character_set")
    _sel(obs[1])
    assert run("subcharacter_set", name="arms", no_rotate=True) == {'FINISHED'}
    got = _chars()
    assert got["arms"] == sorted(f"pCube2.translate{a}" for a in "XYZ"), got
    assert cs().current(bpy.context.scene).bl_label == "character1"        # Maya keeps the current character
    _sel(obs[1])
    run("subcharacter_set")
    assert "subCharacter1" in _chars()


def test_character_from_channel_box():
    obs = _char_scene()
    cb = import_module(kit.MODULE + ".ui.channel_box")
    cb.set_selected_channels(["tx", "rz"], bpy.context)
    try:
        run("character_set", attributes="From Channel Box")
    finally:
        cb.set_selected_channels([], bpy.context)
    assert _chars() == {"character1": ["pCube1.rotateZ", "pCube1.translateX"]}, _chars()


# --- curves ----------------------------------------------------------------------------------------------

def _crv(c):
    return cmaya.MCurve([tuple(x) for x in c["cvs"]], list(c["knots"]), c["degree"])


def _object(name, c):
    ob = cmaya._new_curve_object(bpy.context, name, [c])
    ob.name = name
    return ob


def _cvs(ob):
    return cmaya.read_spline(ob.data.splines[0]).cvs


def test_cut_window():
    for key, values in (("cut_AB", {}), ("cut_AB_lastonly", {"cut": "Using last curve"}),
                        ("cut_AB_longest", {"keep": "Longest segments"})):
        c = curve_case(key)
        _clear()
        obs = [_object(b["name"], _crv(b)) for b in c["before"]]
        _sel(*obs)
        assert run("cut_curve", **values) == {'FINISHED'}, key
        want = [a for a in c["after"] if "cvs" in a]
        got = [ob for ob in bpy.data.objects]
        assert len(got) == len(want), (key, [o.name for o in got])
        for ob in got:
            assert any(len(w["cvs"]) == len(_cvs(ob)) and err(_cvs(ob), w["cvs"]) < 1e-5 for w in want), (key, ob.name)


def test_detach_window_is_the_plain_detach():
    c = curve_case("detach_A_u2")
    _clear()
    A = _object("curveA", _crv(c["before"][0]))
    _sel(A)
    bpy.ops.object.mode_set(mode='EDIT')
    for i, p in enumerate(A.data.splines[0].points):
        p.select = i == 3
    assert run("detach_curves") == {'FINISHED'}
    pieces = sorted(bpy.data.objects, key=lambda o: o.name)
    assert len(pieces) == 2 and all(err(_cvs(o), w["cvs"]) < 1e-5 for o, w in zip(pieces, c["after"]))


def test_reverse_window_and_keep_original():
    c = curve_case("reverse_A")
    _clear()
    A = _object("curveA", _crv(c["before"][0]))
    _sel(A)
    assert run("reverse_curve") == {'FINISHED'}
    assert err(_cvs(A), c["after"][0]["cvs"]) < 1e-6
    _clear()
    A = _object("curveA", _crv(c["before"][0]))
    _sel(A)
    run("reverse_curve", keep_original=True)
    assert sorted(o.name for o in bpy.data.objects) == maya()["Maya"]["cases"]["reverse_keep_original"]["curves"]
    assert err(_cvs(A), c["before"][0]["cvs"]) < 1e-6
    assert err(_cvs(bpy.data.objects["curveAreversedCurve1"]), c["after"][0]["cvs"]) < 1e-6


def test_smooth_curves_window():
    c = curve_case("smooth_hair_A3D")
    for values, want in (({}, c["after"][0]["cvs"]),
                         ({"factor": 1}, maya()["Maya"]["cases"]["smooth_hair_1"]["cvs"]),
                         ({"factor": 10}, maya()["Maya"]["cases"]["smooth_hair_10"]["cvs"])):
        _clear()
        A = _object("curveA", _crv(c["before"][0]))
        _sel(A)
        assert run("smooth_curves", **values) == {'FINISHED'}
        assert err(_cvs(A), want) < 1e-5, values


def test_smooth_curve_keep_original():
    c = curve_case("smooth_A3D")
    _clear()
    A = _object("curveA", _crv(c["before"][0]))
    _sel(A)
    assert run("smooth_curve", keep_original=True) == {'FINISHED'}
    assert sorted(o.name for o in bpy.data.objects) == maya()["Maya"]["cases"]["smooth_keep_original"]["curves"]
    assert err(_cvs(A), c["before"][0]["cvs"]) < 1e-9                       # the original stays
    assert err(_cvs(bpy.data.objects["curveAsmoothCurve1"]), c["before"][0]["cvs"]) > 1e-3   # the copy moved


def test_straighten_window():
    c = curve_case("straighten_A3D")
    cases = maya()["Maya"]["cases"]
    for values, want in (({}, c["after"][-1]["cvs"]),
                         ({"straightness": 0.5}, cases["straighten_0.5_keep"]["cvs"]),
                         ({"preserve_length": False}, cases["straighten_1_nokeep"]["cvs"]),
                         ({"straightness": 0.5, "preserve_length": False}, cases["straighten_0.5_nokeep"]["cvs"])):
        _clear()
        A = _object("curveA", _crv(c["before"][0]))
        _sel(A)
        assert run("straighten_curves", **values) == {'FINISHED'}
        assert err(_cvs(A), want) < 1e-5, values


def test_arc_tool_settings():
    pts = json.dumps([(0, 0, 0), (2, 2, 0), (4, 0, 0)])
    for degree, sections in ((3, 8), (1, 12), (3, 16)):
        _clear()
        assert bpy.ops.allset.arc3_tool('EXEC_DEFAULT', points=pts, degree=degree, sections=sections) == {'FINISHED'}
        ob = bpy.context.view_layer.objects.active
        want, _knots, deg = cm.arc3((0, 0, 0), (2, 2, 0), (4, 0, 0), sections, degree)
        got = cmaya.read_spline(ob.data.splines[0])
        assert got.degree == deg == degree and err(got.cvs, want) < 1e-5, (degree, sections)
    _clear()
    bpy.ops.allset.arc2_tool('EXEC_DEFAULT', points=json.dumps([(0, 0, 0), (4, 0, 0)]), degree=1, sections=4)
    assert len(cmaya.read_spline(bpy.context.view_layer.objects.active.data.splines[0]).cvs) == 5
    for key in ("arc3_tool", "arc2_tool"):
        assert ow._BY_KEY[key].defaults() == {"degree": "3", "sections": 8}


# --- UVs ------------------------------------------------------------------------------------------------

def _uv_plane(shift):
    """Maya's case: a 2-face plane cut along the middle edge, the right face's UVs shifted by ``shift`` in U."""
    _clear()
    me = bpy.data.meshes.new("pPlaneShape1")
    me.from_pydata([(0, 0, 0), (1, 0, 0), (2, 0, 0), (0, 1, 0), (1, 1, 0), (2, 1, 0)], [], [(0, 1, 4, 3), (1, 2, 5, 4)])
    ob = bpy.data.objects.new("pPlane1", me)
    bpy.context.scene.collection.objects.link(ob)
    _sel(ob)
    bm = bmesh.new()
    bm.from_mesh(me)
    uv = bm.loops.layers.uv.verify()
    for f in bm.faces:
        for lp in f.loops:
            x, y = lp.vert.co.x / 2.0, lp.vert.co.y
            lp[uv].uv = (x + (shift if f.index == 1 else 0.0), y)
    bm.to_mesh(me)
    bm.free()
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.scene.tool_settings.use_uv_select_sync = True
    bpy.ops.mesh.select_all(action='SELECT')
    return ob


def _uv_count(ob):
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.verify()
    seen = set()
    for f in bm.faces:
        for lp in f.loops:
            seen.add((lp.vert.index, round(lp[uv].uv.x, 6), round(lp[uv].uv.y, 6)))
    return len(seen), sorted({round(lp[uv].uv.x, 6) for f in bm.faces for lp in f.loops})


def test_merge_uvs_window_follows_Maya():
    cases = maya()["Maya"]["cases"]
    for shift, values, case in ((0.005, {}, "merge_factory_seam_0.005"), (0.02, {}, "merge_factory_seam_0.02"),
                                (0.02, {"threshold": 0.05}, "merge_d0.05_seam_0.02"),
                                (-0.497, {}, "merge_factory_other_vertex")):
        ob = _uv_plane(shift)
        assert run("merge_uvs", **values) == {'FINISHED'}, case
        n, us = _uv_count(ob)
        want = cases[case]["after"]
        assert n == want["count"], (case, n, want["count"])
        assert us == sorted({round(u, 6) for u, _v in want["uvs"]}), (case, us)
        bpy.ops.object.mode_set(mode='OBJECT')


def test_contour_window_is_the_plain_contour():
    ob = _uv_plane(0.0)
    bpy.ops.object.mode_set(mode='OBJECT')
    _sel(ob)
    assert run("contour_stretch") == {'FINISHED'}
    after_window = [tuple(d.uv) for d in ob.data.uv_layers.active.data]
    assert bpy.ops.allset.uv_contour('EXEC_DEFAULT') == {'FINISHED'}
    assert err(after_window, [tuple(d.uv) for d in ob.data.uv_layers.active.data]) < 1e-6


# --- skeleton / skin ------------------------------------------------------------------------------------

def _chain():
    _clear()
    data = bpy.data.armatures.new("skeleton")
    arm = bpy.data.objects.new("skeleton1", data)
    bpy.context.scene.collection.objects.link(arm)
    _sel(arm)
    bpy.ops.object.mode_set(mode='EDIT')
    prev = None
    for k, (h, t) in enumerate((((0, 0, 0), (2, 0, 0)), ((2, 0, 0), (4, 0, 0)), ((4, 0, 0), (6, 0, 0)))):
        eb = data.edit_bones.new(f"joint{k + 1}")
        eb.head, eb.tail = h, t
        if prev is not None:
            eb.parent, eb.use_connect = prev, True
        prev = eb
    bpy.ops.object.mode_set(mode='POSE')
    cb = import_module(kit.MODULE + ".ui.channel_box")
    for i, pb in enumerate(arm.pose.bones):
        pb.rotation_mode = 'XYZ'
        pb.rotation_euler = (0.0, 0.0, math.radians(10 * (i + 1)))
        cb.set_bone_selected(pb, pb.name == "joint2")
    return arm


def _pref(arm):
    return {pb.name: round(pb[rig.PREFERRED_PROP][2], 4) if rig.PREFERRED_PROP in pb else 0.0
            for pb in arm.pose.bones}


def test_preferred_angle_windows_follow_Maya():
    cases = maya()["Maya"]["cases"]
    for options, case in (("Hierarchy", "pref_set_hierarchy"), ("Selected joint", "pref_set_selected")):
        arm = _chain()
        assert run("set_preferred_angle", options=options) == {'FINISHED'}
        assert _pref(arm) == {k: round(v, 4) for k, v in cases[case].items()}, (case, _pref(arm))
    for options, case in (("Hierarchy", "pref_assume_hierarchy"), ("Selected joint", "pref_assume_selected")):
        arm = _chain()
        for pb in arm.pose.bones:
            pb[rig.PREFERRED_PROP] = [0.0, 0.0, 45.0]
        assert run("assume_preferred_angle", options=options) == {'FINISHED'}
        got = {pb.name: round(math.degrees(pb.rotation_euler.z), 4) for pb in arm.pose.bones}
        assert got == {k: round(v, 4) for k, v in cases[case].items()}, (case, got)
    bpy.ops.object.mode_set(mode='OBJECT')


def _skinned():
    _clear()
    me = bpy.data.meshes.new("pPlaneShape1")
    me.from_pydata([(x, y, 0) for y in range(3) for x in range(3)], [], [])
    ob = bpy.data.objects.new("pPlane1", me)
    bpy.context.scene.collection.objects.link(ob)
    data = bpy.data.armatures.new("skeleton")
    arm = bpy.data.objects.new("skeleton1", data)
    bpy.context.scene.collection.objects.link(arm)
    _sel(arm)
    bpy.ops.object.mode_set(mode='EDIT')
    for name, h, t in (("joint1", (0, 0, 0), (1, 0, 0)), ("joint2", (1, 0, 0), (2, 0, 0)),
                       ("joint3", (0, 2, 0), (0, 3, 0))):
        eb = data.edit_bones.new(name)
        eb.head, eb.tail = h, t
    bpy.ops.object.mode_set(mode='OBJECT')
    md = ob.modifiers.new("skinCluster1", 'ARMATURE')
    md.object = arm
    ob.vertex_groups.new(name="joint1").add(list(range(9)), 1.0, 'REPLACE')
    ob.vertex_groups.new(name="joint2").add(list(range(9)), 0.0, 'REPLACE')
    cbm = import_module(kit.MODULE + ".ui.channel_box")       # Bone.select is gone in 5.x (step 200)
    for b in data.bones:
        cbm.set_bone_selected(arm.pose.bones[b.name], b.name == "joint3")
    _sel(ob, arm)
    return ob


def test_add_influence_window_follows_Maya():
    for values, case in (({}, None), ({"lock_weights": True}, "infl_lock_0"),
                         ({"lock_weights": True, "default_weight": 0.3}, "infl_lock_0.3")):
        ob = _skinned()
        assert run("add_influence", **values) == {'FINISHED'}
        g1, g3 = ob.vertex_groups["joint1"], ob.vertex_groups["joint3"]
        if case is None:                     # the plain item: weight 0, unlocked (kit; Maya's dropoff not modelled)
            assert all(g3.weight(i) == 0.0 for i in range(9)) and not g3.lock_weight
            continue
        w = maya()["Maya"]["cases"][case]
        assert g3.lock_weight == w["lock_j3"]
        assert all(abs(g3.weight(i) - w["weights"]["joint3"][0]) < 1e-6 for i in range(9)), case
        assert all(abs(g1.weight(i) - w["weights"]["joint1"][0]) < 1e-6 for i in range(9)), case
