"""Step 206: UV Editor depth 2 against Maya 2022.
Each case rebuilds Maya's mesh (corner k of face f = loop k, vertex ids
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
TOL = 2e-7
_D = {}
WORST = {}


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


# --- Cycle --------------------------------------------------------------------------------------------------------


# --- Split --------------------------------------------------------------------------------------------------------


# --- Create Shell (Grid) ------------------------------------------------------------------------------------------


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


# --- HUD ----------------------------------------------------------------------------------------------------------


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
