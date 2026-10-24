"""Step 155: Maya UV shell commands against mayapy ground truth (research/maya/re/uv_shells_155.json, rules in
research/maya/re/uv_shells_155.md). Each case rebuilds the Maya test mesh (corner k of face f = loop k), applies Maya's
selection with UV sync off (the kit's UV mode), runs the kit operator and compares every face-corner UV."""

import json
import math
import os
from importlib import import_module

import bmesh
import bpy

import kit

compat = import_module(kit.MODULE + ".compat")
shells_mod = import_module(kit.MODULE + ".operators.uv_shells")

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "research", "maya", "re", "uv_shells_155.json")
_D = None


def data():
    global _D
    if _D is None:
        with open(DATA, encoding="utf-8") as fh:
            _D = json.load(fh)
    return _D


def _maya_edges(faces):
    """Maya edge ids of a mesh built face by face: each new (sorted) vertex pair in face-corner order."""
    order = {}
    for f in faces:
        for k in range(len(f)):
            pair = tuple(sorted((f[k], f[(k + 1) % len(f)])))
            if pair not in order:
                order[pair] = len(order)
    return {i: p for p, i in order.items()}


def build(name):
    m = data()["meshes"][name]
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
    """Maya component names -> Blender selection with UV sync off (every face selected, like the kit's UV mode)."""
    ts = bpy.context.scene.tool_settings
    ts.use_uv_select_sync = False
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.verify()
    bm.faces.ensure_lookup_table()
    edges = _maya_edges(m["faces"])
    for f in bm.faces:
        f.select = True
        for l in f.loops:
            compat.set_uv_vert_selected(l, uv, False)
            compat.set_uv_edge_selected(l, uv, False)
    kinds = set()
    for name in selection:
        comp = name.split(".", 1)[1]
        kind, idx = comp.split("[")[0], int(comp.split("[")[1].rstrip("]"))
        kinds.add(kind)
        if kind == "map":
            for f, ids in enumerate(m["face_uv_ids"]):
                for k, i in enumerate(ids):
                    if i == idx:
                        compat.set_uv_vert_selected(bm.faces[f].loops[k], uv, True)
        elif kind == "f":
            for l in bm.faces[idx].loops:
                compat.set_uv_vert_selected(l, uv, True)
                compat.set_uv_edge_selected(l, uv, True)
        elif kind == "e":
            a, b = edges[idx]
            for f in bm.faces:
                for l in f.loops:
                    if {l.vert.index, l.link_loop_next.vert.index} == {a, b}:
                        compat.set_uv_edge_selected(l, uv, True)
                        compat.set_uv_vert_selected(l, uv, True)
                        compat.set_uv_vert_selected(l.link_loop_next, uv, True)
    ts.uv_select_mode = 'FACE' if kinds == {"f"} else 'EDGE' if kinds == {"e"} else 'VERTEX'
    bmesh.update_edit_mesh(ob.data)


def uvs(ob):
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.verify()
    return [[tuple(l[uv].uv) for l in f.loops] for f in bm.faces]


def run_case(key, op, tol=1e-4, **props):
    case = data()["cases"][key]
    name = case["meshes"][0]
    ob, m = build(name)
    select(ob, m, case["selection"])
    res = getattr(bpy.ops.allset, op)(**props)
    assert res == {'FINISHED'}, (key, res)
    got = uvs(ob)
    want = case["after"][name]["face_uvs"]
    worst = 0.0
    for f, (gf, wf) in enumerate(zip(got, want)):
        if wf is None:
            continue
        for k, (g, w) in enumerate(zip(gf, wf)):
            worst = max(worst, abs(g[0] - w[0]), abs(g[1] - w[1]))
    assert worst <= tol, f"{key}: worst UV difference {worst:.6f} > {tol} (got {got}, want {want})"
    bpy.ops.object.mode_set(mode='OBJECT')
    return worst


def test_stack():
    run_case("stack", "uv_stack")
    run_case("stack_one_uv_per_shell", "uv_stack")


def test_orient_shells():
    # Maya's angle search lands up to 0.19 deg off the exact optimum (uv_shells_155.md §4 Orient): ~3.5e-4 UV
    for key in ("orient", "orient_shells_rot", "orient_shells_rot2", "orient_skew"):
        run_case(key, "uv_orient_shells", tol=6e-4)


def test_stack_and_orient():
    for key in ("stack_orient", "stack_orient_shells_rot", "stack_orient_shells_rot2"):
        run_case(key, "uv_stack", tol=6e-4, orient='ORIENT')


def test_orient_to_edges():
    for key in ("orient_edges_edge_B", "orient_edges_uvpair_B", "orient_edges_edges_AB",
                "orient_edges_shells_rot_A", "orient_edges_shells_rot2_A"):
        run_case(key, "uv_orient_edges")


def test_snap_and_stack():
    run_case("snap_stack", "uv_snap_stack")


def test_snap_together():
    run_case("snap_together_AB", "uv_snap_together")
    run_case("snap_together_BA", "uv_snap_together")
    run_case("snap_together_method1", "uv_snap_together", method='1')


def test_distribute():
    run_case("distribute", "uv_distribute")


def test_normalize():
    for key in ("normalize", "normalize_tile1", "normalize_shell_B", "normalize_uvs"):
        run_case(key, "uv_normalize")


def test_move_and_sew():
    for key in ("move_sew_small_off", "move_sew_big_off", "move_sew_small_scaled", "move_sew_one_edge",
                "move_sew_faces"):
        run_case(key, "uv_move_sew")


def _shell_count(ob):
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.verify()
    return len(shells_mod.shells(bm, uv))


def test_create_uv_shell():
    # positions stay (the kit's step-66 Cut moves the smaller side NUDGE = 2e-4 so the islands really split)
    for key, n in (("create_shell_f0", 2), ("create_shell_f0f1", 2)):
        case = data()["cases"][key]
        ob, m = build(case["meshes"][0])
        select(ob, m, case["selection"])
        assert bpy.ops.allset.uv_create_shell() == {'FINISHED'}
        got = uvs(ob)
        want = case["after"][case["meshes"][0]]["face_uvs"]
        worst = max(abs(g - w) for gf, wf in zip(got, want) for gk, wk in zip(gf, wf) for g, w in zip(gk, wk))
        assert worst <= 3e-4, (key, worst)
        assert _shell_count(ob) == n == len(case["after"][case["meshes"][0]]["shells"]), key
        bpy.ops.object.mode_set(mode='OBJECT')


def test_delete_uvs():
    # Maya: the faces using the selection become unmapped; Blender keeps a UV per corner, so they collapse to (0, 0)
    for key in ("delete_uvs_f0", "delete_uvs_centre_uv", "delete_uvs_corner_uv", "delete_uvs_edge"):
        case = data()["cases"][key]
        name = case["meshes"][0]
        ob, m = build(name)
        select(ob, m, case["selection"])
        assert bpy.ops.allset.uv_delete() == {'FINISHED'}
        got = uvs(ob)
        after = case["after"][name]
        for f, wf in enumerate(after["face_uvs"]):
            if wf is None:
                assert all(abs(u) < 1e-9 and abs(v) < 1e-9 for u, v in got[f]), (key, f, got[f])
            else:
                assert all(abs(g[0] - w[0]) < 1e-6 and abs(g[1] - w[1]) < 1e-6 for g, w in zip(got[f], wf)), (key, f)
        assert sorted(after["unmapped_faces"]) == [f for f, wf in enumerate(after["face_uvs"]) if wf is None]
        bpy.ops.object.mode_set(mode='OBJECT')


def _area(face_uvs):
    return sum(abs(sum(p[i][0] * p[i - 1][1] - p[i - 1][0] * p[i][1] for i in range(len(p)))) / 2 for p in face_uvs)


def test_unfold_keeps_area_and_mean():
    # Unfold3D's solver turn can't be reproduced: compare area and the mean of the shell's UVs (uv_shells_155.md §4)
    for key in ("unfold_fold", "unfold_quad2_distorted"):
        case = data()["cases"][key]
        name = case["meshes"][0]
        ob, m = build(name)
        select(ob, m, case["selection"])
        assert bpy.ops.allset.uv_unfold() == {'FINISHED'}
        got = uvs(ob)
        want = case["after"][name]["face_uvs"]
        assert abs(_area(got) - _area(want)) < 1e-4 * max(1.0, _area(want)) * 10, (key, _area(got), _area(want))
        mean_w = case["after"][name]["shells"][0]["centre"]
        bm = bmesh.from_edit_mesh(ob.data)
        uv = bm.loops.layers.uv.verify()
        shell = shells_mod.shells(bm, uv)[0]
        mean = shells_mod.point_mean(shell, uv)
        # Maya's "centre" is the bbox centre; the kept quantity is the UV mean — compare with the mean of Maya's UVs
        ids = {}
        for f, wf in enumerate(want):
            for k, p in enumerate(wf):
                ids[m["face_uv_ids"][f][k]] = p
        mw = (sum(p[0] for p in ids.values()) / len(ids), sum(p[1] for p in ids.values()) / len(ids))
        assert abs(mean.x - mw[0]) < 1e-4 and abs(mean.y - mw[1]) < 1e-4, (key, tuple(mean), mw, mean_w)
        bpy.ops.object.mode_set(mode='OBJECT')


def test_unstack_separates_and_keeps_centre():
    case = data()["cases"]["unstack_after_stack"]
    name = case["meshes"][0]
    ob, m = build(name)
    # start from Maya's stacked state
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.verify()
    for f, wf in zip(bm.faces, case["before"][name]["face_uvs"]):
        for l, p in zip(f.loops, wf):
            l[uv].uv = p
    bmesh.update_edit_mesh(ob.data)
    select(ob, m, case["selection"])
    assert bpy.ops.allset.uv_unstack() == {'FINISHED'}
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.verify()
    groups = shells_mod.shells(bm, uv)
    boxes = [shells_mod.uv_bounds(g, uv) for g in groups]
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a, b = boxes[i], boxes[j]
            overlap = min(a[1].x, b[1].x) - max(a[0].x, b[0].x) > 1e-6 and min(a[1].y, b[1].y) - max(a[0].y, b[0].y) > 1e-6
            assert not overlap, ("shells overlap after Unstack", i, j)
    lo, hi = shells_mod._group_bounds(groups, uv)
    c0 = case["before"][name]
    xs = [p[0] for wf in c0["face_uvs"] for p in wf]
    ys = [p[1] for wf in c0["face_uvs"] for p in wf]
    centre = ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)
    assert abs((lo.x + hi.x) / 2 - centre[0]) < 1e-4 and abs((lo.y + hi.y) / 2 - centre[1]) < 1e-4
    bpy.ops.object.mode_set(mode='OBJECT')


def test_no_redo_panel_and_undo():
    for cls in shells_mod.classes:
        assert 'UNDO' in cls.bl_options, cls
