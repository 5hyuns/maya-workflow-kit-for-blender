"""Step 206: UV Editor depth 2 against Maya 2022 (research/maya/re/uv_201.md, ground truth uv_201.json; HUD shots
research/maya/screens/uv_201/run2/_gui201.json). Each case rebuilds Maya's mesh (corner k of face f = loop k, vertex ids
kept), applies Maya's selection with UV sync off (the kit's UV mode), runs the kit operator and compares every
face-corner UV with Maya's result."""

import json
import os
from importlib import import_module

import bmesh
import bpy

import kit

compat = import_module(kit.MODULE + ".compat")
mod = import_module(kit.MODULE + ".operators.uv_206")
shells_mod = import_module(kit.MODULE + ".operators.uv_shells")
uv_tools = import_module(kit.MODULE + ".operators.uv_tools")
hud = import_module(kit.MODULE + ".ui.uv_hud")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRUTH = os.path.join(ROOT, "research", "maya", "re", "uv_201.json")
GUI = os.path.join(ROOT, "research", "maya", "screens", "uv_201", "run2", "_gui201.json")
TOL = 2e-7
_D = {}
WORST = {}


def data():
    if "d" not in _D:
        if not os.path.exists(TRUTH):
            print("research/ missing: skipped")
            _D["d"] = None
        else:
            with open(TRUTH, encoding="utf-8") as fh:
                _D["d"] = json.load(fh)
    return _D["d"]


def _clear():
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)


def build(verts, faces, face_uvs, name="m"):
    _clear()
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    uvl = me.uv_layers.new(name="map1")
    for f, poly in enumerate(me.polygons):
        for k in range(poly.loop_total):
            uvl.data[poly.loop_start + k].uv = face_uvs[f][k]
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    return ob


def build_case(case):
    name = case["meshes"][0]
    before = case["before"][name]
    m = data()["meshes"].get(name)
    verts = m["verts"] if m else before["verts"]
    return build(verts, before["face_verts"], before["face_uvs"], name), before


def select(ob, before, selection):
    ts = bpy.context.scene.tool_settings
    ts.use_uv_select_sync = False
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.verify()
    bm.faces.ensure_lookup_table()
    comps = [n.split(".", 1)[1] for n in selection if "." in n]
    kinds = {c.split("[")[0] for c in comps}
    whole = not comps and selection
    ts.uv_select_mode = 'FACE' if (kinds == {"f"} or whole) else 'EDGE' if kinds == {"e"} else 'VERTEX'
    for f in bm.faces:
        f.select = True
        for l in f.loops:
            compat.set_uv_vert_selected(l, uv, False)
            compat.set_uv_edge_selected(l, uv, False)
        if whole:
            compat.set_uv_face_selected(f, uv, True)
    edges = {}
    for f in before["face_verts"]:
        for k in range(len(f)):
            key = frozenset((f[k], f[(k + 1) % len(f)]))
            edges.setdefault(key, len(edges))
    by_id = {i: tuple(k) for k, i in edges.items()}
    for c in comps:
        kind, idx = c.split("[")[0], int(c.split("[")[1].rstrip("]"))
        if kind == "map":
            for f, ids in enumerate(before["face_uv_ids"]):
                for k, i in enumerate(ids or ()):
                    if i == idx:
                        compat.set_uv_vert_selected(bm.faces[f].loops[k], uv, True)
        elif kind == "vtx":
            for l in bm.verts[idx].link_loops if hasattr(bm.verts, "ensure_lookup_table") and not \
                    bm.verts.ensure_lookup_table() else ():
                compat.set_uv_vert_selected(l, uv, True)
        elif kind == "f":
            compat.set_uv_face_selected(bm.faces[idx], uv, True)
        elif kind == "e":
            a, b = by_id[idx]
            for f in bm.faces:
                for l in f.loops:
                    if {l.vert.index, l.link_loop_next.vert.index} == {a, b}:
                        compat.set_uv_edge_selected(l, uv, True)
                        compat.set_uv_vert_selected(l, uv, True)
                        compat.set_uv_vert_selected(l.link_loop_next, uv, True)
    bmesh.update_edit_mesh(ob.data)


def uvs(ob):
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.verify()
    return [[tuple(l[uv].uv) for l in f.loops] for f in bm.faces]


def kit_uv_count(ob):
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.verify()
    shells_mod._index_loops(bm)
    return len(shells_mod.uv_points(bm, uv, [l for f in bm.faces for l in f.loops]))


def kit_shells(ob):
    """Shells counted Maya's way (polyEvaluate -uvShell): faces sharing any UV (point) are one shell."""
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.verify()
    shells_mod._index_loops(bm)
    faces = list(bm.faces)
    parent = {f: f for f in faces}

    def find(x):
        while parent[x] is not x:
            x = parent[x]
        return x
    for p in shells_mod.uv_points(bm, uv, [l for f in faces for l in f.loops]):
        for l in p[1:]:
            a, b = find(p[0].face), find(l.face)
            if a is not b:
                parent[b] = a
    return len({find(f) for f in faces})


def worst(got, want):
    w = 0.0
    for gf, wf in zip(got, want):
        for g, x in zip(gf, wf):
            w = max(w, abs(g[0] - x[0]), abs(g[1] - x[1]))
    return w


def run_case(key, op, tol=TOL, repeat=None):
    case = data()["cases"][key]
    assert "ERROR" not in case, (key, case.get("ERROR"))
    name = case["meshes"][0]
    ob, before = build_case(case)
    select(ob, before, case["selection"])
    want = case["after"][name]["face_uvs"]
    unchanged = want == before["face_uvs"]
    for _ in range(repeat or len(case.get("mel_result") or [None])):
        res = getattr(bpy.ops.allset, op)()
        assert res == {'FINISHED'} or (unchanged and res == {'CANCELLED'}), (key, res)
    got = uvs(ob)
    w = worst(got, want)
    WORST[key] = w
    assert w <= tol, f"{key}: worst UV difference {w:.3g} > {tol} (got {got}, want {want})"
    return ob, case


def _keys(prefix):
    return sorted(k for k in data()["cases"] if k.startswith(prefix))


# --- Cycle --------------------------------------------------------------------------------------------------------

def test_maya_edge_ids_match_creation_order():
    if data() is None:
        return
    seen = 0
    for key, case in data()["cases"].items():
        name = case["meshes"][0]
        b = case.get("before", {}).get(name, {})
        if "edge_verts" not in b or name not in data()["meshes"]:
            continue
        ids = mod.maya_edge_ids(b["face_verts"])
        want = {frozenset(e): i for i, e in enumerate(b["edge_verts"])}
        assert ids == want, key
        seen += 1
    assert seen > 20, seen


def test_cycle():
    if data() is None:
        return
    keys = [k for k in _keys("cycle_") if k != "cycle_object"]
    assert len(keys) >= 10
    for key in keys:
        ob, case = run_case(key, "uv_cycle")
        if key == "cycle_grid3_four":
            continue        # four cycles put the UVs back: Blender can't keep a cut at unchanged coordinates
        # the face is cut out: Maya's shell count afterwards
        assert kit_shells(ob) == case["after"][case["meshes"][0]]["polyEvaluate_uvShell"], key


def test_cycle_nothing_selected_warns():
    if data() is None:
        return
    case = data()["cases"]["cycle_grid3_f4"]
    ob, before = build_case(case)
    select(ob, before, [])
    assert bpy.ops.allset.uv_cycle() == {'CANCELLED'}
    assert worst(uvs(ob), before["face_uvs"]) < 1e-6


def test_cycle_undo():
    if data() is None:
        return
    case = data()["cases"]["cycle_grid3_f4"]
    ob, before = build_case(case)
    select(ob, before, case["selection"])
    bpy.ops.ed.undo_push(message="before")
    assert bpy.ops.allset.uv_cycle('EXEC_DEFAULT', True) == {'FINISHED'}
    assert worst(uvs(ob), before["face_uvs"]) > 0.01
    bpy.ops.ed.undo()
    assert worst(uvs(bpy.context.object), before["face_uvs"]) < 1e-6


# --- Split --------------------------------------------------------------------------------------------------------

def test_split():
    if data() is None:
        return
    for key in _keys("split_"):
        ob, case = run_case(key, "uv_split", tol=uv_tools.NUDGE * 1.0001)
        after = case["after"][case["meshes"][0]]
        assert kit_uv_count(ob) == after["uv_count"], (key, kit_uv_count(ob), after["uv_count"])
        assert kit_shells(ob) == after["polyEvaluate_uvShell"], key


# --- Create Shell (Grid) ------------------------------------------------------------------------------------------

def test_grid_rule_pure():
    """rect_coords on the raw Maya meshes (no Blender): every changed face gets Maya's grid coordinates."""
    if data() is None:
        return
    n = 0
    for key in _keys("grid_"):
        case = data()["cases"][key]
        name = case["meshes"][0]
        b, a = case["before"][name], case["after"][name]
        picks = sorted(int(s.split("[")[1][:-1]) for s in case["selection"] if ".vtx[" in s)
        if len(picks) < 2:
            continue
        got = mod.rect_coords(b["face_verts"], picks[0], picks[1])
        changed = [f for f in range(len(b["face_uvs"])) if b["face_uvs"][f] != a["face_uvs"][f]]
        if got is None:
            assert not changed, key
            continue
        region, (I, J) = got
        for f, c in region.items():
            for v, want in zip(b["face_verts"][f], a["face_uvs"][f]):
                i, j = c[v]
                assert abs(i / I - want[0]) <= TOL and abs(j / J - want[1]) <= TOL, (key, f, v)
        n += 1
    assert n >= 30, n


def test_grid_shell():
    if data() is None:
        return
    keys = [k for k in _keys("grid_") if data()["cases"][k]["selection"]]
    assert len(keys) >= 45, len(keys)
    for key in keys:
        # where the new grid lands on a neighbour's UV, Blender needs the cut split NUDGE apart (outside faces move)
        ob, case = run_case(key, "uv_grid_shell", tol=uv_tools.NUDGE * 1.0001)
        after = case["after"][case["meshes"][0]]
        assert kit_shells(ob) == after["polyEvaluate_uvShell"], (key, kit_shells(ob), after["polyEvaluate_uvShell"])


# --- Auto Seams ---------------------------------------------------------------------------------------------------

def _cut_edges(ob):
    bm = bmesh.from_edit_mesh(ob.data)
    return [(e.verts[0].index, e.verts[1].index) for e in bm.edges if e.seam]


def _path_ends(pairs):
    deg = {}
    for a, b in pairs:
        deg[a] = deg.get(a, 0) + 1
        deg[b] = deg.get(b, 0) + 1
    return sorted(v for v, d in deg.items() if d == 1), max(deg.values()) if deg else 0


def _diameter(verts):
    import math
    return max(math.dist(p, q) for p in verts for q in verts)


def test_auto_seams_closed_genus0_is_one_path_like_maya():
    """Maya cuts a closed genus-0 shell along one path between two far-apart vertices (cube corner to corner, sphere
    over a pole, capped cylinder); the kit cuts one shortest path between its two farthest vertices."""
    if data() is None:
        return
    import math
    for k in ("cube", "cube2", "cylinder", "cylinder20", "sphere8", "sphere", "prism"):
        key = "autoseam_proj_" + k
        case = data()["cases"][key]
        name = case["meshes"][0]
        b, a = case["before"][name], case["after"][name]
        verts = b["verts"]
        diam = _diameter(verts)
        maya_ends, maya_deg = _path_ends(a["seam_edges"])
        assert len(maya_ends) == 2 and maya_deg <= 2, (key, maya_ends)
        maya_span = math.dist(verts[maya_ends[0]], verts[maya_ends[1]])
        ob, before = build_case(case)
        select(ob, before, [])
        assert bpy.ops.allset.uv_auto_seams() == {'FINISHED'}, key
        cut = _cut_edges(ob)
        ends, deg = _path_ends(cut)
        assert len(ends) == 2 and deg <= 2, (key, cut)
        span = math.dist(verts[ends[0]], verts[ends[1]])
        assert span >= 0.95 * diam and maya_span >= 0.8 * diam, (key, span, maya_span, diam)
        assert kit_shells(ob) == a["polyEvaluate_uvShell"], key
        WORST[key] = "kit %d edges, Maya %d" % (len(cut), len(a["seam_edges"]))


def test_auto_seams_disc_untouched():
    if data() is None:
        return
    for key in ("autoseam_proj_plane4", "autoseam_grid3", "autoseam_plane4"):
        case = data()["cases"][key]
        assert case["after"][case["meshes"][0]]["seam_edges"] == case["before"][case["meshes"][0]]["seam_edges"]
        ob, before = build_case(case)
        select(ob, before, [])
        assert bpy.ops.allset.uv_auto_seams() == {'CANCELLED'}, key
        assert not _cut_edges(ob), key


def _is_disc(ob):
    """Every UV shell is a topological disc: V - E + F = 1 counted on Maya UVs / UV edges."""
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.verify()
    shells_mod._index_loops(bm)
    for shell in uv_tools.islands(bm, uv):
        pts = shells_mod.uv_points(bm, uv, [l for f in shell for l in f.loops])
        owner = {l: i for i, p in enumerate(pts) for l in p}
        es = {frozenset((owner[l], owner[l.link_loop_next])) for f in shell for l in f.loops}
        if len(pts) - len(es) + len(shell) != 1:
            return False
    return True


def test_auto_seams_torus_and_pipe_become_discs():
    if data() is None:
        return
    for key in ("autoseam_proj_torus8", "autoseam_proj_pipe", "autoseam_proj_cylinder_nocap"):
        case = data()["cases"][key]
        ob, before = build_case(case)
        select(ob, before, [])
        assert bpy.ops.allset.uv_auto_seams() == {'FINISHED'}, key
        assert _is_disc(ob), key
        WORST[key] = "kit %d edges, Maya %d" % (len(_cut_edges(ob)),
                                                len(case["after"][case["meshes"][0]]["seam_edges"]))


def test_auto_seams_keeps_existing_cuts():
    """Maya keeps the default cube UVs' cuts (autoseam_cube: no change): an unfoldable shell gets nothing."""
    if data() is None:
        return
    case = data()["cases"]["autoseam_cube"]
    ob, before = build_case(case)
    select(ob, before, [])
    res = bpy.ops.allset.uv_auto_seams()
    assert worst(uvs(ob), before["face_uvs"]) < 1e-6
    assert res == {'CANCELLED'} and not _cut_edges(ob), (res, _cut_edges(ob))


# --- HUD ----------------------------------------------------------------------------------------------------------

def _gui():
    if not os.path.exists(GUI):
        return None
    with open(GUI, encoding="utf-8") as fh:
        return json.load(fh)


def _hud_mesh(spec, name):
    faces = spec["faces"]
    ids = spec.get("face_uv_ids") or [list(f) for f in faces]
    return build(spec["verts"], faces, [[spec["uvs"][i] for i in fid] for fid in ids], name)


def _stats(ob):
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.verify()
    return hud.mesh_statistics(bm, uv, False)


def _select_uvs(ob, spec, ids=(), faces=()):
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.verify()
    fid = spec.get("face_uv_ids") or [list(f) for f in spec["faces"]]
    for f, face in enumerate(bm.faces):
        face.select = True
        compat.set_uv_face_selected(face, uv, f in faces)
        for k, l in enumerate(face.loops):
            if fid[f][k] in ids:
                compat.set_uv_vert_selected(l, uv, True)
    bmesh.update_edit_mesh(ob.data)


def test_hud_statistics_like_maya():
    g = _gui()
    if g is None:
        return
    bpy.context.scene.tool_settings.use_uv_select_sync = False
    spec = g["stats_mesh"]
    ob = _hud_mesh(spec, "stats")
    s = _stats(ob)
    # Maya j_object: (0/4) UV shells, (0/0) overlapping UVs, (0/4) reversed UVs
    assert hud.statistics_text(s[1], s[0], s[3], s[2], s[5], s[4]) == \
        "(0/4) UV shells, (0/0) overlapping UVs, (0/4) reversed UVs", s
    _select_uvs(ob, spec, ids=(0, 1, 2, 3))                   # k_uvs_s0: 1 shell selected, U 0.2 V 0.2
    s = _stats(ob)
    assert s[1] == 1 and hud.position_text(s[6]) == "U:  0.2 V:  0.2", s
    _select_uvs(ob, spec, ids=(0, 1, 2, 4))                   # m_uvs_mean: bbox centre, not the mean
    assert hud.position_text(_stats(ob)[6]) == "U:  0.3 V:  0.2"
    _select_uvs(ob, spec, faces=(3,))                         # n_face_rev: (4/..) reversed UVs, U 0.7 V 0.7
    s = _stats(ob)
    assert s[5] == 4 and s[1] == 1 and hud.position_text(s[6]) == "U:  0.7 V:  0.7", s
    stack = g["stack_mesh"]                                   # p_stack_object: (0/3), (0/8) overlapping
    ob = _hud_mesh(stack, "stack")
    s = _stats(ob)
    assert (s[0], s[2], s[4]) == (3, 8, 0), s
    _select_uvs(ob, stack, ids=(8,))                          # q: U 0.123 V 0.654
    assert hud.position_text(_stats(ob)[6]) == "U:  0.123 V:  0.654"
    _select_uvs(ob, stack, faces=(0, 1))                      # r: (2/..) shells, (8/..) overlapping, U 0.2 V 0.6
    s = _stats(ob)
    assert (s[1], s[3]) == (2, 8) and hud.position_text(s[6]) == "U:  0.2 V:  0.6", s
    _select_uvs(ob, stack)
    assert hud.position_text(_stats(ob)[6]) == ""


def test_hud_factory_on_and_menu_toggles():
    wm = bpy.context.window_manager
    for name, _l, _t in hud.PROPS:
        assert getattr(wm, name) is True, name           # Maya factory: all three HUDs shown
    emap = import_module(kit.MODULE + ".ui.editor_menu_map")
    for label, prop in (("Isolate Select", "allset_uv_hud_isolate"), ("UV Position", "allset_uv_hud_position"),
                        ("UV Statistics", "allset_uv_hud_statistics")):
        act = emap.MAP["UV Editor/View/Heads-Up Display/" + label]
        assert act[0] == "prop" and act[1] == "window_manager." + prop, act


def test_hud_format():
    assert hud.fmt(0.2) == "0.2" and hud.fmt(0.123456) == "0.123" and hud.fmt(0.165) == "0.165"
    assert hud.fmt(0.0) == "0" and hud.fmt(1.0) == "1" and hud.fmt(-0.0001) == "0"


# --- UV sets / menu -----------------------------------------------------------------------------------------------

def test_uv_sets():
    ob = build([(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)], [(0, 1, 2, 3)], [[(0, 0), (1, 0), (1, 1), (0, 1)]])
    bpy.ops.object.mode_set(mode='OBJECT')
    layers = ob.data.uv_layers
    layers.new(name="uvSet1")
    second = layers["uvSet1"]                 # a reference kept across layers.new() crashes Blender
    layers.active = second
    for i, d in enumerate(second.data):
        d.uv = (0.5 + i * 0.1, 0.25)
    bpy.ops.object.mode_set(mode='EDIT')
    assert bpy.ops.allset.uv_set_copy_to(target="map1") == {'FINISHED'}
    bpy.ops.object.mode_set(mode='OBJECT')
    layers = ob.data.uv_layers
    assert [tuple(d.uv) for d in layers["map1"].data] == [tuple(d.uv) for d in layers["uvSet1"].data]
    bpy.ops.object.mode_set(mode='EDIT')
    assert bpy.ops.allset.uv_set_current(target="map1") == {'FINISHED'}
    assert ob.data.uv_layers.active.name == "map1"
    assert bpy.ops.allset.uv_set_rename('EXEC_DEFAULT', name="mainUVs") == {'FINISHED'}
    assert ob.data.uv_layers.active.name == "mainUVs"
    assert bpy.ops.allset.uv_set_current(target="map1") == {'FINISHED'}     # no map1 any more: the first set
    assert ob.data.uv_layers.active.name == "mainUVs"


def test_menu_items_mapped():
    emap = import_module(kit.MODULE + ".ui.editor_menu_map")
    for path, op in (("Cut/Sew/Auto Seams", "uv_auto_seams"), ("Cut/Sew/Create Shell (Grid)", "uv_grid_shell"),
                     ("Cut/Sew/Split", "uv_split"), ("Modify/Cycle", "uv_cycle"),
                     ("UV Sets/Rename Current UV Set...", "uv_set_rename"),
                     ("UV Sets/Copy UVs to UV Set/map1", "uv_set_copy_to"), ("UV Sets/map1", "uv_set_current")):
        act = emap.MAP["UV Editor/" + path]
        name = act if isinstance(act, str) else act[0]
        assert name == "allset." + op, (path, act)
        assert hasattr(bpy.ops.allset, op)
    notices = import_module(kit.MODULE + ".ui.notices")
    assert notices.notice("UV Editor/Modify/Warp Image")


def test_report_worst():
    print("WORST", json.dumps(WORST, indent=0, default=str))
