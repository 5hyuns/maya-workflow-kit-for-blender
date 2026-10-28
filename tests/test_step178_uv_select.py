"""Step 178 lane B: Maya UV Editor Select / Edit / View isolate commands against mayapy ground truth
(research/maya/re/uv_select_178.json, rules in research/maya/re/uv_select_178.md, src/allset/operators/uv_select_178.py,
src/allset/ui/uv_display.py). Each case rebuilds the Maya test mesh (corner k of face f = loop k, Maya vertex / face ids
= Blender indices), sets Maya's component mask (facet / edge / vertex = UV Sync Selection on with that mesh select
mode, polymeshUV = sync off UV vertex mode, meshUVShell = sync off island mode), runs the kit operator and compares the
selected components with Maya's."""

import json
import os
from importlib import import_module

import bmesh
import bpy

import kit

compat = import_module(kit.MODULE + ".compat")
sel_mod = import_module(kit.MODULE + ".operators.uv_select_178")
uvd = import_module(kit.MODULE + ".ui.uv_display")

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "research", "maya", "re", "uv_select_178.json")
_D = None


def data():
    global _D
    if _D is None:
        if not os.path.exists(DATA):
            return None
        with open(DATA, encoding="utf-8") as fh:
            _D = json.load(fh)
    return _D


def _skip():
    if data() is None:
        print("SKIP: research/ is missing (", DATA, ")")
        return True
    return False


# --- building and selecting --------------------------------------------------------------------------

def _clear():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)


def build(*names):
    _clear()
    obs = []
    for name in names:
        m = data()["meshes"][name]
        me = bpy.data.meshes.new(name)
        me.from_pydata([tuple(v) for v in m["verts"]], [], [tuple(f) for f in m["faces"]])
        uvl = me.uv_layers.new(name="map1")
        deleted = set(m.get("deleted_faces", ()))
        for f, poly in enumerate(me.polygons):
            for k in range(poly.loop_total):
                # Maya's polyMapDel faces: the kit's Delete UVs collapses them to (0, 0) (uv_shells.DELETED)
                uvl.data[poly.loop_start + k].uv = (0.0, 0.0) if f in deleted else m["uvs"][m["face_uv_ids"][f][k]]
        ob = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(ob)
        ob.select_set(True)
        obs.append(ob)
    bpy.context.view_layer.objects.active = obs[0]
    bpy.ops.object.mode_set(mode='EDIT')
    return obs


MASKS = {"facet": (True, (False, False, True)), "edge": (True, (False, True, False)),
         "vertex": (True, (True, False, False)), "polymeshUV": (False, 'VERTEX'), "meshUVShell": (False, 'SHELL'),
         "uvface": (False, 'FACE')}


def set_mask(maskname):
    ts = bpy.context.scene.tool_settings
    synced, mode = MASKS[maskname]
    ts.use_uv_select_sync = synced
    if synced:
        ts.mesh_select_mode = mode
        compat.set_uv_island_mode(ts, False)
    else:
        compat.set_uv_island_mode(ts, mode == 'SHELL')
        if mode != 'SHELL':
            ts.uv_select_mode = mode
    for ob in bpy.context.objects_in_mode_unique_data:
        bm = bmesh.from_edit_mesh(ob.data)
        uv = bm.loops.layers.uv.active
        for f in bm.faces:
            f.select_set(not synced)          # the kit's UV mode: every face selected, no UV picked
            if not synced:
                compat.set_uv_face_selected(f, uv, False)
        bmesh.update_edit_mesh(ob.data)


def pick(ob, maskname, comps):
    """Select Maya components {'f': [...], 'e': [[a, b]...], 'vtx': [...], 'map': [...]} on ``ob``."""
    m = data()["meshes"][ob.name]
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.active
    bm.faces.ensure_lookup_table()
    bm.verts.ensure_lookup_table()
    synced = MASKS[maskname][0]
    for i in comps.get("f", ()):
        if synced:
            bm.faces[i].select_set(True)
        else:
            compat.set_uv_face_selected(bm.faces[i], uv, True)
    for a, b in comps.get("e", ()):
        e = next(e for e in bm.edges if {v.index for v in e.verts} == {a, b})
        e.select_set(True)
    for i in comps.get("vtx", ()):
        bm.verts[i].select_set(True)
    for i in comps.get("map", ()):
        for f, ids in enumerate(m["face_uv_ids"]):
            for k, uid in enumerate(ids):
                if uid == i:
                    compat.set_uv_vert_selected(bm.faces[f].loops[k], uv, True)
    if synced:
        bm.select_flush_mode()
    bmesh.update_edit_mesh(ob.data)


def maya_names(names):
    """Maya component names (as the JSON 'selection' lists them) -> pick() dict per mesh."""
    out = {}
    for n in names:
        obj, comp = n.split(".", 1)
        kind, idx = comp.split("[")[0], int(comp.split("[")[1].rstrip("]"))
        rec = out.setdefault(obj, {})
        if kind == "e":
            raise ValueError("decode edges from 'after' only")
        rec.setdefault(kind, []).append(idx)
    return out


def got(ob, maskname):
    """The kit selection of ``ob`` in Maya terms for ``maskname``."""
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.active
    m = data()["meshes"][ob.name]
    synced, mode = MASKS[maskname]
    if synced:
        if mode[2]:
            return {"f": sorted(f.index for f in bm.faces if f.select)}
        if mode[1]:
            return {"e": sorted(sorted(v.index for v in e.verts) for e in bm.edges if e.select)}
        return {"vtx": sorted(v.index for v in bm.verts if v.select)}
    if mode in ('SHELL', 'FACE'):
        return {"f": sorted(f.index for f in bm.faces
                            if f.select and all(compat.uv_vert_selected(lp, uv) for lp in f.loops))}
    loops = {(f.index, k) for f in bm.faces if f.select for k, lp in enumerate(f.loops)
             if compat.uv_vert_selected(lp, uv)}
    ids = {m["face_uv_ids"][f][k] for f, k in loops}
    # every loop of a picked Maya UV is selected, and nothing else
    want_loops = {(f, k) for f, row in enumerate(m["face_uv_ids"]) for k, i in enumerate(row) if i in ids}
    assert loops == want_loops, f"{ob.name}: partial Maya UVs selected {sorted(want_loops - loops)}"
    return {"map": sorted(ids)}


def expected(case, name, maskname):
    rec = case["after"].get(name, {})
    key = {"facet": "f", "edge": "e", "vertex": "vtx", "polymeshUV": "map", "meshUVShell": "f", "uvface": "f"}[maskname]
    return {key: sorted(rec.get(key, []))}


def run(key, op, maskname=None, **props):
    case = data()["cases"][key]
    assert "ERROR" not in case, (key, case.get("ERROR"))
    maskname = maskname or case["mask"]
    obs = build(*case["meshes"])
    set_mask(maskname)
    res = getattr(bpy.ops.allset, op)(**props)
    assert res == {'FINISHED'}, (key, res)
    for ob in obs:
        g, w = got(ob, maskname), expected(case, ob.name, maskname)
        assert g == w, f"{key} ({maskname}) {ob.name}: kit {g} != Maya {w}"
    bpy.ops.object.mode_set(mode='OBJECT')


# --- tests ---------------------------------------------------------------------------------------------

def test_facing():
    if _skip():
        return
    n = 0
    for key, case in data()["cases"].items():
        if not key.startswith("facing_"):
            continue
        if key.endswith("_polymeshUV_fold_end_cut"):
            # Maya keeps two UV ids at one place on one vertex (a cut with nothing moved); Blender can't tell them
            # apart: one vertex + one coordinate is one UV for the kit (uv_shells.uv_points), so this case can't exist
            continue
        front = key.startswith("facing_front")
        run(key, "uv_select_facing", front=front)
        n += 1
        if case["mask"] == "facet":
            run(key, "uv_select_facing", maskname="uvface", front=front)       # sync off Face = same faces
    assert n >= 30, n


def test_facing_rule_shared_uvs():
    """The 'fold' strip: the clockwise middle quad is back-facing and, all its UVs used by front faces, front too."""
    if _skip():
        return
    c = data()["cases"]
    assert c["facing_back_facet"]["after"]["fold"]["f"] == [1, 3]
    assert c["facing_front_facet"]["after"]["fold"]["f"] == [0, 1, 2, 4]


def test_texture_borders():
    if _skip():
        return
    for mask in ("facet", "edge", "vertex", "polymeshUV"):
        run("borders_" + mask, "uv_select_texture_borders")
    # UV Shell mask: Maya selects nothing and keeps the selection (research/maya/re/uv_select_178.md)
    assert data()["cases"]["borders_meshUVShell"]["after"] == {}
    build("borders")
    set_mask("meshUVShell")
    assert bpy.ops.allset.uv_select_texture_borders() == {'CANCELLED'}


def test_non_overlapping():
    if _skip():
        return
    for mask in ("facet", "edge", "vertex", "polymeshUV", "meshUVShell"):
        run("nonoverlap_" + mask, "uv_select_non_overlapping")
    run("nonoverlap_fold_facet", "uv_select_non_overlapping")
    run("nonoverlap_objects_ab", "uv_select_non_overlapping")       # two meshes compared together (perObject 0)
    run("nonoverlap_objects_ac", "uv_select_non_overlapping")


def test_overlapping_rule():
    """The pure rule with overlapping=True gives Maya's Overlapping (selectUVOverlappingComponents 1 0) too."""
    if _skip():
        return
    for mask in ("facet", "edge", "vertex", "polymeshUV", "meshUVShell"):
        case = data()["cases"]["overlap_" + mask]
        ob, = build("overlap")
        set_mask(mask)
        ts = bpy.context.scene.tool_settings
        bm = bmesh.from_edit_mesh(ob.data)
        uv = bm.loops.layers.uv.active
        kind = sel_mod.mask(ts)
        res, = sel_mod.non_overlapping(kind, [(bm, uv, sel_mod.shown_faces(bm, ts.use_uv_select_sync))],
                                       overlapping=True)
        sel_mod.apply(bm, uv, ts, kind, res)
        bmesh.update_edit_mesh(ob.data)
        assert got(ob, mask) == expected(case, "overlap", mask), (mask, got(ob, mask), expected(case, "overlap", mask))
        bpy.ops.object.mode_set(mode='OBJECT')


def test_unmapped_faces():
    if _skip():
        return
    case = data()["cases"]["unmapped"]
    assert case["after"]["unmapped"]["f"] == [1, 2, 3, 4, 6]
    for start in ("vertex", "polymeshUV"):
        ob, = build("unmapped")
        set_mask(start)
        assert bpy.ops.allset.uv_select_unmapped() == {'FINISHED'}
        ts = bpy.context.scene.tool_settings
        assert ts.use_uv_select_sync and tuple(ts.mesh_select_mode) == (False, False, True), "Maya: face mask"
        assert got(ob, "facet") == expected(case, "unmapped", "facet"), (start, got(ob, "facet"))
        bpy.ops.object.mode_set(mode='OBJECT')
    # nothing unmapped: Maya warns and leaves nothing selected
    ob, = build("borders")
    set_mask("facet")
    pick(ob, "facet", {"f": [0]})
    assert bpy.ops.allset.uv_select_unmapped() == {'FINISHED'}
    assert got(ob, "facet") == {"f": []}
    bpy.ops.object.mode_set(mode='OBJECT')


def test_to_connected_and_contained_faces():
    if _skip():
        return
    masks = {"vtx": "vertex", "edge": "edge", "uv": "polymeshUV", "uv_square": "polymeshUV", "face": "facet"}
    for tag, maskname in masks.items():
        for rule in ("touch", "in"):
            case = data()["cases"]["conv_%s_%s" % (rule, tag)]
            ob, = build("borders")
            set_mask(maskname)
            sel = {}
            if tag == "edge":
                sel = {"e": [[6, 7]]}
            else:
                sel = maya_names(case["selection"])["borders"]
            pick(ob, maskname, sel)
            want = sorted(case["after"].get("borders", {}).get("f", []))
            ts = bpy.context.scene.tool_settings
            bm = bmesh.from_edit_mesh(ob.data)
            uv = bm.loops.layers.uv.active
            fn = sel_mod.connected_faces if rule == "touch" else sel_mod.contained_faces
            have = sorted(f.index for f in fn(bm, uv, ts))
            assert have == want, f"conv_{rule}_{tag}: kit {have} != Maya {want}"
            if rule == "touch":
                assert bpy.ops.allset.uv_to_connected_faces() == {'FINISHED'}
                gm = "facet" if MASKS[maskname][0] else "uvface"
                assert got(ob, gm) == {"f": want}, (tag, got(ob, gm), want)
            bpy.ops.object.mode_set(mode='OBJECT')


def test_unpin_all():
    if _skip():
        return
    case = data()["cases"]["unpin_all"]
    assert any(case["pins_before"]) and not any(case["pins_after"])
    ob, = build("borders")
    set_mask("facet")
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.active
    m = data()["meshes"]["borders"]
    for f in bm.faces:
        for k, lp in enumerate(f.loops):
            lp[uv].pin_uv = m["face_uv_ids"][f.index][k] in case["pinned"]
    bmesh.update_edit_mesh(ob.data)
    pick(ob, "facet", {"f": [0]})
    assert bpy.ops.allset.uv_unpin_all() == {'FINISHED'}
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.active
    assert not any(lp[uv].pin_uv for f in bm.faces for lp in f.loops), "every pin off (polyPinUV -op 2)"
    bpy.ops.object.mode_set(mode='OBJECT')


def test_isolate_set_matches_maya():
    """View > Isolate Select > Add / Remove / Remove All change the set like textureEditorIsolateSelect 1 / 2 / 0."""
    if _skip():
        return
    steps = data()["cases"]["isolate"]["steps"]
    ob, = build("borders")
    actions = {1: 'ADD', 2: 'REMOVE', 0: 'CLEAR'}
    masks = {"facet": "facet", "vertex": "vertex", "edge": "edge", "polymeshUV": "polymeshUV"}
    for st in steps:
        set_mask(masks[st["mask"]])
        comps = {}
        for n in st["selection"]:
            comp = n.split(".", 1)[1]
            kind, idx = comp.split("[")[0], int(comp.split("[")[1].rstrip("]"))
            if kind == "e":
                comps["e"] = [[6, 7]]          # the only edge the script picks (edge_of v6 - v7)
            else:
                comps.setdefault(kind, []).append(idx)
        pick(ob, st["mask"], comps)
        assert bpy.ops.allset.uv_isolate_edit(action=actions[st["mode"]]) == {'FINISHED'}
        want = sorted((st["members_decoded"] or {}).get("borders", {}).get("f", []))
        assert uvd.iso_set(ob) == want, f"{st['label']}: kit set {uvd.iso_set(ob)} != Maya {want}"
    bpy.ops.object.mode_set(mode='OBJECT')
    # a first Add with a vertex selection: the faces around it (the set can't hold vertices)
    st = data()["cases"]["isolate_fresh_vertex"]["steps"][0]
    uvd._iso_sets.clear()
    ob, = build("borders")
    set_mask("vertex")
    pick(ob, "vertex", {"vtx": [6]})
    bpy.ops.allset.uv_isolate_edit(action='ADD')
    assert uvd.iso_set(ob) == st["members_decoded"]["borders"]["f"]
    bpy.ops.object.mode_set(mode='OBJECT')


def _shown(ob, synced):
    bm = bmesh.from_edit_mesh(ob.data)
    return sorted(f.index for f in uvd.shown_faces(bm, synced))


def test_isolate_view_add_remove_sync_off():
    """While Ctrl+1 is on, Add / Remove / Remove All change what the UV Editor shows (sync off = selected faces)."""
    if _skip():
        return
    uvd._iso_sets.clear()
    wm = bpy.context.window_manager
    ob, = build("borders")
    set_mask("polymeshUV")
    pick(ob, "polymeshUV", {"f": [0]})
    assert bpy.ops.allset.uv_isolate() == {'FINISHED'} and wm.allset_uv_isolate
    assert _shown(ob, False) == [0] and uvd.iso_set(ob) == [0]
    # the user picks face f5 in the 3D View (sync off: it then shows in the UV Editor with its UVs selected); UV Face
    # mode, so the selection is that face (in UV mode f0, sharing a UV with f5, would count as touched too)
    bpy.context.scene.tool_settings.uv_select_mode = 'FACE'
    bm = bmesh.from_edit_mesh(ob.data)
    bm.faces.ensure_lookup_table()
    for f in bm.faces:
        compat.set_uv_face_selected(f, bm.loops.layers.uv.active, False)
    bm.faces[5].select = True
    compat.set_uv_face_selected(bm.faces[5], bm.loops.layers.uv.active, True)
    bmesh.update_edit_mesh(ob.data)
    assert bpy.ops.allset.uv_isolate_edit(action='ADD') == {'FINISHED'}
    assert uvd.iso_set(ob) == [0, 5] and _shown(ob, False) == [0, 5]
    assert bpy.ops.allset.uv_isolate_edit(action='REMOVE') == {'FINISHED'}      # f5 still selected: out again
    assert uvd.iso_set(ob) == [0] and _shown(ob, False) == [0]
    assert bpy.ops.allset.uv_isolate_edit(action='CLEAR') == {'FINISHED'}
    assert uvd.iso_set(ob) == [] and _shown(ob, False) == []
    assert bpy.ops.allset.uv_isolate() == {'FINISHED'} and not wm.allset_uv_isolate
    assert _shown(ob, False) == list(range(12)), _shown(ob, False)
    bpy.ops.object.mode_set(mode='OBJECT')


def test_isolate_view_sync_on():
    if _skip():
        return
    uvd._iso_sets.clear()
    ob, = build("borders")
    set_mask("facet")
    pick(ob, "facet", {"f": [0, 1]})
    assert bpy.ops.allset.uv_isolate() == {'FINISHED'}
    assert _shown(ob, True) == [0, 1]
    bm = bmesh.from_edit_mesh(ob.data)
    bm.faces.ensure_lookup_table()
    for f in bm.faces:
        f.select_set(False)
    bm.faces[0].select_set(True)
    bmesh.update_edit_mesh(ob.data)
    assert bpy.ops.allset.uv_isolate_edit(action='REMOVE') == {'FINISHED'}
    assert uvd.iso_set(ob) == [1] and _shown(ob, True) == [1], _shown(ob, True)
    assert bpy.ops.allset.uv_isolate() == {'FINISHED'}
    assert _shown(ob, True) == list(range(12))
    # with the view off Add only changes the set (Maya: shown with View Selected)
    pick(ob, "facet", {"f": [7]})
    assert bpy.ops.allset.uv_isolate_edit(action='ADD') == {'FINISHED'}
    assert _shown(ob, True) == list(range(12))
    bpy.ops.object.mode_set(mode='OBJECT')


def test_filter_selection():
    """Filter Selection > Connected / Contained Faces: only those faces shown, the same item again shows all."""
    if _skip():
        return
    wm = bpy.context.window_manager
    ob, = build("borders")
    set_mask("polymeshUV")
    m = data()["meshes"]["borders"]
    pick(ob, "polymeshUV", {"map": [m["face_uv_ids"][5][k] for k in range(4)]})
    assert bpy.ops.allset.uv_filter_faces(kind='CONNECTED') == {'FINISHED'}
    assert wm.allset_uv_filter == 'CONNECTED'
    want = data()["cases"]["conv_touch_uv_square"]["after"]["borders"]["f"]
    assert _shown(ob, False) == want, _shown(ob, False)
    assert bpy.ops.allset.uv_filter_faces(kind='CONTAINED') == {'FINISHED'}       # switches the filter
    assert wm.allset_uv_filter == 'CONTAINED' and _shown(ob, False) == [5], _shown(ob, False)
    assert bpy.ops.allset.uv_filter_faces(kind='CONTAINED') == {'FINISHED'}       # off
    assert wm.allset_uv_filter == 'NONE' and _shown(ob, False) == list(range(12))
    bpy.ops.object.mode_set(mode='OBJECT')


def test_no_redo_panel():
    """Maya has no redo panel: no kit op of this step is REGISTER + UNDO with a visible property."""
    for name in ("uv_select_facing", "uv_select_texture_borders", "uv_select_non_overlapping", "uv_select_unmapped",
                 "uv_to_connected_faces", "uv_unpin_all", "uv_filter_faces", "uv_isolate_edit"):
        op = getattr(bpy.types, "ALLSET_OT_" + name)
        opts = op.bl_options
        if 'REGISTER' in opts and 'UNDO' in opts:
            rna = getattr(bpy.ops.allset, name).get_rna_type()
            props = [p for p in rna.properties if p.identifier != "rna_type" and not p.is_hidden]
            assert not props, (name, [p.identifier for p in props])
