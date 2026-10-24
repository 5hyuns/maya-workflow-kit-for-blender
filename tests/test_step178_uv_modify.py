"""Step 178 lane A: Maya UV Editor Modify commands against mayapy ground truth (research/maya/re/uv_modify_178.json and
uv_modify_178_straighten.json, rules in research/maya/re/uv_modify_178.md). Each case rebuilds the Maya test mesh
(corner k of face f = loop k), applies Maya's selection with UV sync off (the kit's UV mode), runs the kit operator and
compares every face-corner UV with Maya's result (1e-4)."""

import json
import os
from importlib import import_module

import bmesh
import bpy

import kit

compat = import_module(kit.MODULE + ".compat")
mod = import_module(kit.MODULE + ".operators.uv_modify")

RE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "maya", "re")
FILES = ("uv_modify_178.json", "uv_modify_178_straighten.json")
_D = None
TOL = 1e-4
WORST = {}


def data():
    """{"meshes": ..., "cases": ...} merged from both measurement files, or None when research/ is missing."""
    global _D
    if _D is None:
        if not all(os.path.exists(os.path.join(RE, f)) for f in FILES):
            print("research/ missing: skipped")
            return None
        _D = {"meshes": {}, "cases": {}}
        for f in FILES:
            with open(os.path.join(RE, f), encoding="utf-8") as fh:
                d = json.load(fh)
            _D["meshes"].update(d["meshes"])
            _D["cases"].update(d["cases"])
    return _D


def _maya_edges(faces):
    order = {}
    for f in faces:
        for k in range(len(f)):
            pair = tuple(sorted((f[k], f[(k + 1) % len(f)])))
            if pair not in order:
                order[pair] = len(order)
    return {i: p for p, i in order.items()}


def build(name):
    m = data()["meshes"][name]
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in m["verts"]], [], [tuple(f) for f in m["faces"]])
    uvl = me.uv_layers.new(name="map1")
    for f, poly in enumerate(me.polygons):
        for k in range(poly.loop_total):
            uvl.data[poly.loop_start + k].uv = m["uvs"][m["face_uv_ids"][f][k]]
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    return ob, m


def select(ob, m, selection):
    """Maya component names -> Blender selection with UV sync off (every face shown, like the kit's UV mode)."""
    ts = bpy.context.scene.tool_settings
    ts.use_uv_select_sync = False
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.verify()
    bm.faces.ensure_lookup_table()
    edges = _maya_edges(m["faces"])
    kinds = {name.split(".", 1)[1].split("[")[0] for name in selection if "." in name}
    ts.uv_select_mode = 'FACE' if kinds == {"f"} else 'EDGE' if kinds == {"e"} else 'VERTEX'
    for f in bm.faces:
        f.select = True
        compat.set_uv_face_selected(f, uv, False)
    for name in selection:
        if "." not in name:
            continue
        comp = name.split(".", 1)[1]
        kind, idx = comp.split("[")[0], int(comp.split("[")[1].rstrip("]"))
        if kind == "map":
            for f, ids in enumerate(m["face_uv_ids"]):
                for k, i in enumerate(ids):
                    if i == idx:
                        compat.set_uv_vert_selected(bm.faces[f].loops[k], uv, True)
        elif kind == "f":
            compat.set_uv_face_selected(bm.faces[idx], uv, True)
        elif kind == "e":
            a, b = edges[idx]
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


def run_case(key, op, **props):
    """Run one Maya case; when Maya changed nothing the kit op may report CANCELLED, but the UVs must still match."""
    case = data()["cases"][key]
    assert "ERROR" not in case, (key, case.get("ERROR"))
    name = case["meshes"][0]
    ob, m = build(name)
    select(ob, m, case["selection"])
    res = getattr(bpy.ops.allset, op)(**props)
    want = case["after"][name]["face_uvs"]
    unchanged = want == case["before"][name]["face_uvs"]
    assert res == {'FINISHED'} or (unchanged and res == {'CANCELLED'}), (key, res)
    got = uvs(ob)
    worst = 0.0
    for gf, wf in zip(got, want):
        for g, w in zip(gf, wf):
            worst = max(worst, abs(g[0] - w[0]), abs(g[1] - w[1]))
    WORST[key] = worst
    assert worst <= TOL, f"{key}: worst UV difference {worst:.6f} > {TOL} (got {got}, want {want})"
    bpy.ops.object.mode_set(mode='OBJECT')
    return worst


def _keys(prefix):
    return sorted(k for k in data()["cases"] if k.startswith(prefix))


def test_distribute_uvs():
    if data() is None:
        return
    for key in ("distribute_uvs_row", "distribute_uvs_diag", "distribute_uvs_all", "distribute_uvs_shells",
                "distribute_uvs_perform"):
        run_case(key, "uv_distribute_uvs")


def test_match_grid():
    if data() is None:
        return
    for key in ("match_grid_all", "match_grid_lines", "match_grid_some", "match_grid_perform"):
        run_case(key, "uv_match_grid")


def test_layout_along():
    if data() is None:
        return
    for key in ("layout_along_shells", "layout_along_shells_rot2", "layout_along_similar", "layout_along_grid3",
                "layout_along_shells_AB"):
        run_case(key, "uv_layout_along")
    run_case("layout_along_v", "uv_layout_along", direction='V')


def test_stack_similar():
    if data() is None:
        return
    for key in ("stack_similar_all", "stack_similar_S1", "stack_similar_S2S0", "stack_similar_uvs",
                "stack_similar_shells"):
        run_case(key, "uv_stack_similar")


def test_map_border():
    if data() is None:
        return
    for key in ("map_border_grid3", "map_border_grid42", "map_border_disc", "map_border_shells",
                "map_border_grid3_uv", "map_border_grid3_face", "map_border_grid3_uvs"):
        run_case(key, "uv_map_border")


def test_straighten_border():
    if data() is None:
        return
    keys = [k for k in data()["cases"] if k.startswith("straighten_")]
    keys += [k for k in data()["cases"] if k.split("_")[0].rstrip("0123456789") in ("arc", "kink", "wob", "straight")]
    assert len(keys) >= 40, len(keys)
    for key in keys:
        run_case(key, "uv_straighten_border")


def test_report_worst():
    if data() is None:
        return
    if WORST:
        groups = {}
        for k, w in WORST.items():
            g = "straighten" if k.startswith(("arc", "kink", "wob", "straight")) else k.split("_")[0]
            groups[g] = max(groups.get(g, 0.0), w)
        print("worst UV difference per command:", {g: "%.2e" % w for g, w in sorted(groups.items())})


def test_no_redo_panel_and_undo():
    ids = {c.bl_idname for c in mod.classes}
    assert ids == {"allset.uv_map_border", "allset.uv_straighten_border", "allset.uv_match_grid",
                   "allset.uv_layout_along", "allset.uv_stack_similar", "allset.uv_distribute_uvs"}, ids
    for cls in mod.classes:
        assert 'UNDO' in cls.bl_options, cls
        assert hasattr(bpy.ops.allset, cls.bl_idname.split(".", 1)[1]), cls
