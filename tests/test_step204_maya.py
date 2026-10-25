"""Step 204: the kit's animation layer commands against Maya 2022 mayapy (tests/maya204_layers_data.py, from
research/maya/re/anim_layers_201.json): SCENE rebuilt (Maya auto tangents of these curves are all flat = Bezier
handles a third of the way, flat), every CASE run through the kit command like a UI button (one undo step), then
layer order / created / deleted names, members, mode, weight, curves, weight keys and the evaluated result of every
frame 1..24 compared with 1e-5; one undo must restore the order and the result.

Cases the kit can't reproduce honestly are skipped with the reason in SKIP; PARTIAL lists the parts left out of a
compared case."""

import math
from importlib import import_module

import bpy

import kit
from maya204_layers_data import CASES, SCENE

al = import_module(kit.MODULE + ".operators.anim_layers")
a4 = import_module(kit.MODULE + ".operators.anim_layers_204")
TOL = 1e-5

SKIP = {
    "extract_none_selected_layer": "no layer selected: the kit always has a selected layer (Layer Editor index), "
                                   "Maya does nothing here (delegated)",
    "zero_weight_none": "no layer selected: the kit always has a selected layer, Maya does nothing (delegated)",
}
PARTIAL = {
    "delete_empty": "layer parenting (AnimLayer5/6, AnimLayer7/8) is not in the kit's flat layer list: only the flat "
                    "layers AnimLayer3 / 4 / 9 are built and compared",
    "delete_empty_selected_l1": "as delete_empty",
    "copy_noanim_l2": "the held value is a one-key CONSTANT curve in the kit where Maya has a static plug value "
                      "(NLA has no per-strip constant): curves compared without it, the result is exact",
    "copy_base": "members without a base curve hold their value as a one-key CONSTANT curve (as copy_noanim_l2)",
}
ATTR = {"tx": "translateX", "ty": "translateY", "tz": "translateZ", "rx": "rotateX", "ry": "rotateY",
        "rz": "rotateZ", "sx": "scaleX", "sy": "scaleY", "sz": "scaleZ", "v": "visibility"}
PATH = {"translateX": ("location", 0), "translateY": ("location", 1), "translateZ": ("location", 2),
        "rotateX": ("rotation_euler", 0), "rotateY": ("rotation_euler", 1), "rotateZ": ("rotation_euler", 2),
        "scaleX": ("scale", 0), "scaleY": ("scale", 1), "scaleZ": ("scale", 2)}
SHORT = {"tx": "translateX", "ty": "translateY", "ry": "rotateY"}
BY_PATH = {v: k for k, v in PATH.items()}
FRAMES = list(range(SCENE["frames"][0], SCENE["frames"][1] + 1))


def _k(attr):
    return math.pi / 180.0 if attr.startswith("rotate") else 1.0


def _flat(fc):
    """Maya auto tangents of these keys are flat (every key an end or an extreme): Hermite with zero slopes = Bezier
    with flat handles a third of the way to the neighbours."""
    pts = fc.keyframe_points
    for i, kp in enumerate(pts):
        kp.interpolation = 'BEZIER'
        kp.handle_left_type = kp.handle_right_type = 'FREE'
        x, y = kp.co
        left = (x - pts[i - 1].co.x) / 3.0 if i > 0 else 1.0
        right = (pts[i + 1].co.x - x) / 3.0 if i + 1 < len(pts) else 1.0
        kp.handle_left = (x - left, y)
        kp.handle_right = (x + right, y)
    fc.update()


def _write(ob, act, attr, keys):
    path, idx = PATH[attr]
    fc = al._fcurve(act, path, idx) or al._new_fcurve(ob, act, path, idx)
    for f, v in keys:
        fc.keyframe_points.insert(f, v * _k(attr), options={'FAST'})
    _flat(fc)


def _scene(case):
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for act in list(bpy.data.actions):
        bpy.data.actions.remove(act)
    sc = bpy.context.scene
    sc.allset_anim_layers.clear()
    sc.allset_anim_layer_index = 0
    sc.frame_set(1)
    obs = {}
    for name in ("pCube1", "pSphere1"):
        ob = bpy.data.objects.new(name, bpy.data.meshes.new(name + "Shape"))
        sc.collection.objects.link(ob)
        ob.rotation_mode = 'XYZ'
        obs[name] = ob
    if case == "extract_l1_nonmember":
        ob = bpy.data.objects.new("pCone1", bpy.data.meshes.new("pConeShape1"))
        sc.collection.objects.link(ob)
    for plug, keys in SCENE["base"].items():
        n, attr = plug.split(".")
        ob = obs[n]
        path, idx = PATH[attr]
        for f, v in keys:
            ob.path_resolve(path)[idx] = v * _k(attr)
            ob.keyframe_insert(path, index=idx, frame=f)
        _flat(next(fc for fc in kit.fcurves(ob) if fc.data_path == path and fc.array_index == idx))
    layers = [dict(x) for x in SCENE["layers"]]
    if case.startswith("delete_empty"):
        # the flat part of the mayapy setup: AnimLayer3 no attributes, AnimLayer4 pSphere1.rz without keys,
        # AnimLayer9 emptied by Layers > Empty
        layers += [{"name": "AnimLayer3", "override": False, "weight": 1.0, "attrs": [], "keys": {}},
                   {"name": "AnimLayer4", "override": False, "weight": 1.0, "attrs": ["pSphere1.rotateZ"],
                    "keys": {}},
                   {"name": "AnimLayer9", "override": False, "weight": 1.0, "attrs": ["pSphere1.scaleX"], "keys": {},
                    "empty": True}]
    for spec in layers:
        bpy.ops.allset.anim_layer_create(from_selected=False)
        e = sc.allset_anim_layers[sc.allset_anim_layer_index]
        e.name = spec["name"]            # AnimLayer9 after 3 / 4: the nested 5-8 are not built (PARTIAL)
        e.override = spec["override"]
        e.weight = spec["weight"]
        per = {}
        for plug in spec["attrs"]:
            n, attr = plug.split(".")
            per.setdefault(n, []).append(next(k for k, v in ATTR.items() if v == attr))
        for n, keys in per.items():
            al.add_attrs(sc, obs[n], e.name, keys)
        for plug, keys in spec["keys"].items():
            n, attr = plug.split(".")
            _write(obs[n], al._strip(al.tracks(obs[n])[e.name]).action, attr, keys)
        if spec.get("empty"):
            a4.empty(sc, e.name)
    al.sync(sc)
    sc.allset_anim_layer_index = 0
    for e in sc.allset_anim_layers:
        e.picked = False
    al.show(sc)
    return sc


def _pick(sc, names):
    idx = [i for i, e in enumerate(sc.allset_anim_layers) if e.name in names]
    if not idx:
        return
    a4.pick(sc, idx[0])
    for i in idx[1:]:
        a4.pick(sc, i, toggle=True)
    assert [e.name for e in al.selected_layers(sc)] == list(names), (al.selected_layers(sc), names)


def _results(sc):
    out = {}
    for f in FRAMES:
        sc.frame_set(f)
        for n in ("pCube1", "pSphere1"):
            ob = bpy.data.objects[n].evaluated_get(bpy.context.evaluated_depsgraph_get())
            for short, attr in SHORT.items():
                path, idx = PATH[attr]
                out.setdefault(f"{n}.{short}", []).append(getattr(ob, path)[idx] / _k(attr))
    return out


def _compare_results(case, got, want):
    """|kit - Maya| < 1e-5 in Blender's units: rotations in radians (Blender keeps them as float32 radians, ~1e-5 deg
    at 90 deg; mayapy values are rounded to 6 decimals)."""
    worst = 0.0
    for plug, vals in want.items():
        k = _k(SHORT[plug.split(".")[1]])
        for f, (g, w) in zip(FRAMES, zip(got[plug], vals)):
            worst = max(worst, abs(g - w) * k)
            assert abs(g - w) * k < TOL, (case, plug, f, g, w)
    return worst


def _order(sc):
    return [e.name for e in sc.allset_anim_layers if e.name != al.BASE]


def _layer_info(sc, name):
    e = sc.allset_anim_layers[name]
    attrs, curves, static, wkeys = set(), {}, {}, []
    for ob in sc.objects:
        if name not in al.tracks(ob):
            continue
        if name != al.BASE:
            attrs |= {f"{ob.name}.{ATTR[k]}" for k in al.member_keys(ob, name)}
        for fc in al.layer_curves(ob, name):
            attr = BY_PATH.get((fc.data_path, fc.array_index))
            if attr is None:
                continue
            keys = [[kp.co.x, kp.co.y / _k(attr)] for kp in fc.keyframe_points]
            if len(keys) == 1 and fc.keyframe_points[0].interpolation == 'CONSTANT':
                static[f"{ob.name}.{attr}"] = keys[0][1]
            else:
                curves[f"{ob.name}.{attr}"] = keys
        st = al._strip(al.tracks(ob)[name])
        fc = st.fcurves.find("influence") if st.use_animated_influence else None
        if fc is not None and len(fc.keyframe_points):
            wkeys.append([[kp.co.x, kp.co.y] for kp in fc.keyframe_points])
    return {"attrs": attrs, "override": e.override, "weight": e.weight, "curves": curves, "static": static,
            "weight_keys": wkeys}


def _keys_equal(a, b):
    return len(a) == len(b) and all(abs(x[0] - y[0]) < TOL and abs(x[1] - y[1]) < TOL for x, y in zip(a, b))


def _compare_layers(case, sc, want):
    for name, w in want.items():
        if name == al.BASE:
            got = _layer_info(sc, name)
            for wc in w["weight_keys"].values():
                assert got["weight_keys"] and all(_keys_equal(k, wc["keys"]) for k in got["weight_keys"]), \
                    (case, name, got["weight_keys"], wc)
            continue
        if name not in sc.allset_anim_layers:
            continue                       # nested layers of the delete_empty setup (PARTIAL)
        got = _layer_info(sc, name)
        assert got["attrs"] == set(w["attrs"]), (case, name, sorted(got["attrs"]), w["attrs"])
        assert got["override"] == w["override"], (case, name, got["override"])
        assert abs(got["weight"] - w["weight"]) < TOL, (case, name, got["weight"], w["weight"])
        assert set(got["curves"]) == set(w["curves"]), (case, name, sorted(got["curves"]), sorted(w["curves"]))
        for plug, keys in w["curves"].items():
            assert _keys_equal(got["curves"][plug], keys), (case, name, plug, got["curves"][plug], keys)
        if got["static"]:
            assert case in PARTIAL, (case, name, got["static"])
        wk = list(w["weight_keys"].values())
        if not wk:
            assert not got["weight_keys"], (case, name, got["weight_keys"])
        else:
            assert got["weight_keys"], (case, name)
            for k in got["weight_keys"]:
                assert _keys_equal(k, wk[0]["keys"]), (case, name, k, wk[0]["keys"])


def _run(case, c, sc):
    cmd = c["cmd"]
    op = bpy.ops.allset

    def run(name, **kw):
        assert getattr(op, name)('EXEC_DEFAULT', True, **kw) == {'FINISHED'}, (case, name)
    if "SingleAnimLayer" in cmd:
        run("anim_layer_extract", base=True)
    elif "ExtractObjects" in cmd:
        run("anim_layer_extract")
    elif "CopyAnimLayerNoAnim" in cmd:
        run("anim_layer_duplicate", no_animation=True)
    elif "CopyAnimLayer" in cmd:
        for _ in range(cmd.count("layerEditorCopyAnimLayer(")):
            run("anim_layer_duplicate")
    elif "deleteEmptyAnimLayers" in cmd:
        run("anim_layer_delete_empty")
    elif "ZeroWeightKey" in cmd and "FullWeightKey" in cmd:
        run("anim_layer_key_weight", weight=0.0)
        bpy.context.scene.frame_set(20)
        run("anim_layer_key_weight", weight=1.0)
    elif "ZeroWeightKey" in cmd:
        run("anim_layer_key_weight", weight=0.0)
    elif "FullWeightKey" in cmd:
        run("anim_layer_key_weight", weight=1.0)
    elif "KeyWeightAnimLayer" in cmd:
        run("anim_layer_key_weight", current=True)
    else:
        raise AssertionError((case, cmd))
    return 2 if "currentTime" in cmd or cmd.count("layerEditorCopyAnimLayer(") == 2 else 1


def test_cases_match_mayapy():
    done, worst = [], 0.0
    for case, c in CASES.items():
        if case in SKIP:
            print("skip", case, "-", SKIP[case])
            continue
        sc = _scene(case)
        layers_before = [e.name for e in sc.allset_anim_layers]
        if not case.startswith("delete_empty"):
            assert _order(sc) == c["order_before"], (case, _order(sc))
            worst = max(worst, _compare_results(case + " before", _results(sc), c["result_before"]))
        _pick(sc, c["layers_arg"])
        for ob in sc.objects:
            ob.select_set(ob.name in c["selection_arg"])
        bpy.context.view_layer.objects.active = bpy.data.objects[c["selection_arg"][0]] \
            if c["selection_arg"] else None
        sc.frame_set(c["time"])
        before = _results(sc)
        sc.frame_set(c["time"])
        bpy.ops.ed.undo_push(message="step 204 " + case)
        commands = _run(case, c, sc)
        sc = bpy.context.scene
        order = _order(sc)
        if case.startswith("delete_empty"):
            nested = ("AnimLayer5", "AnimLayer7")       # PARTIAL: not built
            assert order == [n for n in c["order_before"] if n not in nested and n not in c["deleted"]], (case, order)
        else:
            assert order == c["order_after"], (case, order, c["order_after"])
            assert [n for n in order if n not in layers_before] == \
                [n for n in c["order_after"] if n in c["created"]], (case, order)
        _compare_layers(case, sc, c["layers_after"])
        if not case.startswith("delete_empty"):
            worst = max(worst, _compare_results(case, _results(sc), c["result_after"]))
        # new layers are not selected: the selection stays (anim_layers_201.md §2)
        assert [e.name for e in al.selected_layers(sc)] == (c["layers_arg"] or [al.BASE]), \
            (case, al.selected_layers(sc))
        # undo: one step per command (zero_then_full_l1 / copy_l1_twice run two commands)
        for _ in range(commands):
            bpy.ops.ed.undo()
        sc = bpy.context.scene
        assert [e.name for e in sc.allset_anim_layers] == layers_before, (case, "undo", _order(sc))
        sc.frame_set(c["time"])
        got = _results(sc)
        for plug in before:
            assert max(abs(a - b) for a, b in zip(got[plug], before[plug])) < TOL, (case, "undo", plug)
        done.append(case)
    print(f"step 204 mayapy: {len(done)} cases match (max |d| {worst:.2e}), skipped {sorted(SKIP)}")
    assert len(done) == len(CASES) - len(SKIP)
