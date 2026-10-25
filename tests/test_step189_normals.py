"""Step 189 (audit 13 #6): Maya Mesh Display normal commands against mayapy.

Ground truth: tests/maya189_normals_data.py (research/maya/re/mesh_display_184_normals.json). Every case builds the
Maya mesh (corner k of face f = faces[f][k]), gives it Maya's edge smoothing, runs the kit command on the same selection
and compares within 1e-3 (custom-normal storage) every corner normal the command changed in Maya; the corners Maya left alone must stay as
the kit had them (Blender's computed smooth normals are corner-angle weighted, Maya's face-area weighted — the bent
strip's (0.8507, 0, 0.5257) vs (0.8321, 0, 0.5547) — which is not a Mesh Display command). Blender can't keep a lock on a corner whose normal equals the computed
one, so locked flags are checked one way: the kit never locks a corner Maya leaves unlocked, and a corner Maya locked
whose kit normal isn't the result's computed one is locked (a lock on the computed normal can't be stored).
"""

import re
from importlib import import_module

import bmesh
import bpy

import kit
from maya189_normals_data import CASES, INITIAL, MESHES

nm = import_module(kit.MODULE + ".operators.normals_maya")
menu_map = import_module(kit.MODULE + ".ui.menu_map")
option_windows = import_module(kit.MODULE + ".operators.option_windows")

TOL = 1e-3   # Blender stores a custom normal as two 16-bit angles in the corner's normal space: up to ~3e-4 off (measured)
SET = "performPolySetNormal 0"


def _fresh():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for me in list(bpy.data.meshes):
        bpy.data.meshes.remove(me)


def _build(mesh, soft):
    m = MESHES[mesh]
    me = bpy.data.meshes.new(mesh)
    me.from_pydata([tuple(v) for v in m["verts"]], [], [tuple(f) for f in m["faces"]])
    me.update()
    init = INITIAL[f"{mesh}_{'soft' if soft else 'hard'}"]
    hard = {tuple(sorted(e)) for e, s in zip(init["edges"], init["smooth"]) if not s}
    for p in me.polygons:
        p.use_smooth = True
    for e in me.edges:
        e.use_edge_sharp = tuple(sorted(e.vertices)) in hard
    ob = bpy.data.objects.new("m", me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def _select(ob, sel):
    for o in bpy.context.selected_objects:
        o.select_set(False)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    comps = [s for s in sel if "." in s]
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    if not comps:
        return
    bpy.ops.object.mode_set(mode='EDIT')
    faces = any(".f[" in s for s in comps)
    bpy.context.tool_settings.mesh_select_mode = (not faces, False, faces)
    bm = bmesh.from_edit_mesh(ob.data)
    for el in (*bm.verts, *bm.edges, *bm.faces):
        el.select = False
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    for s in comps:
        i = int(re.search(r"\[(\d+)\]", s).group(1))
        if ".vtx[" in s:
            bm.verts[i].select = True
        else:
            bm.faces[i].select_set(True)
    bm.select_flush_mode()
    bmesh.update_edit_mesh(ob.data)


def _run(cmd):
    ops = bpy.ops.allset
    if cmd == "select -cl":
        return
    m = re.match(r"optionVar -fv polySetNormalX (\S+) -fv polySetNormalY (\S+) -fv polySetNormalZ (\S+);", cmd)
    if m:
        assert ops.set_vertex_normal(x=float(m.group(1)), y=float(m.group(2)), z=float(m.group(3))) == {'FINISHED'}
        return
    if "polyAverageNormalTol 0.0" in cmd:
        assert ops.average_normals(distance=0.0) == {'FINISHED'}
        return
    if "polySetToFaceNormalUserNormal 1" in cmd:
        assert ops.set_to_face_normal(user_normal=True) == {'FINISHED'}
        return
    run = {SET: lambda: ops.set_vertex_normal(), "performPolyAverageNormal 0": lambda: ops.average_normals(),
           "performPolySetToFaceNormal 0": lambda: ops.set_to_face_normal(),
           "expandPolyGroupSelection; polyNormalPerVertex -fn true": lambda: ops.lock_normals(),
           "expandPolyGroupSelection; polyNormalPerVertex -ufn true": lambda: ops.lock_normals(unlock=True)}[cmd]
    assert run() == {'FINISHED'}, cmd


def _check(key, c):
    _fresh()
    ob = _build(c["mesh"], c["soft"])
    kit_base = [tuple(n.vector) for n in ob.data.corner_normals]
    if c["pre"]:
        _select(ob, c["pre"][0])
        _run(c["pre"][1])
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    kit_before = [tuple(n.vector) for n in ob.data.corner_normals]
    tag = f"{c['mesh']}_{'soft' if c['soft'] else 'hard'}"
    pre_key = f"set_obj_{tag}" if c["pre"] and list(c["pre"][0]) == ["{tr}"] and c["pre"][1] == SET else None
    maya_before = [n for row in CASES[pre_key]["faces"] for n in row] if pre_key else None
    _select(ob, c["sel"])
    _run(c["cmd"])
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    me = ob.data
    got = [tuple(n.vector) for n in me.corner_normals]
    want = [n for row in c["faces"] for n in row]
    before = [n for row in CASES[f"before_{c['mesh']}_{'soft' if c['soft'] else 'hard'}"]["faces"] for n in row]
    ref = maya_before or before

    def near(p, q):
        return max(abs(a - b) for a, b in zip(p, q)) < TOL

    for i, (g, w) in enumerate(zip(got, want)):
        if near(w, ref[i]):              # Maya left it: the kit leaves it too
            assert near(g, kit_before[i]), (key, i, "changed", g, kit_before[i])
        elif near(w, before[i]):         # Maya went back to its computed normal: the kit to Blender's
            assert near(g, kit_base[i]), (key, i, "computed", g, kit_base[i])
        else:
            assert near(g, w), (key, i, g, w)
    locked = nm.locked_corners(me)
    plain = me.copy()                       # the computed normals of the result (custom normals dropped)
    if plain.attributes.get("custom_normal") is not None:
        plain.attributes.remove(plain.attributes["custom_normal"])
    auto = [tuple(n.vector) for n in plain.corner_normals]
    bpy.data.meshes.remove(plain)
    for i, (lk, mk) in enumerate(zip(locked, c["locked"])):
        assert not lk or mk, (key, i, "kit locked a corner Maya left unlocked")
        if mk and max(abs(a - b) for a, b in zip(got[i], auto[i])) > TOL:
            assert lk, (key, i, "Maya locked a normal the computed one doesn't give, the kit didn't")


def test_every_measured_case_matches_maya():
    skipped = {k for k in CASES if k.startswith("toface_obj_strip")}   # Maya: no change, unexplained [U]
    for key, c in sorted(CASES.items()):
        if key in skipped or not c["ok"]:
            continue
        _check(key, c)


def test_pure_rules():
    normals = [(0.0, 0.0, 1.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)]
    locked = [False] * 3
    nm.average(normals, locked, [[0, 1, 2]])
    assert all(abs(x - 0.57735) < 1e-5 for x in normals[0]) and all(locked)
    nm.set_vertex_normal(normals, locked, [1], (3.0, 4.0, 0.0))
    assert max(abs(a - b) for a, b in zip(normals[1], (0.6, 0.8, 0.0))) < 1e-6, normals[1]
    groups = nm.distance_groups([(0, 0, 0), (0.05, 0, 0), (1, 0, 0)], {0, 1, 2}, {0: [0], 1: [1], 2: [2]}, 0.1)
    assert groups == [[0, 1], [2]], groups


def test_menu_items_and_windows():
    for path, op in (("Mesh Display/Set Vertex Normal", "allset.set_vertex_normal"),
                     ("Mesh Display/Average", "allset.average_normals"),
                     ("Mesh Display/Set to Face", "allset.set_to_face_normal"),
                     ("Mesh Display/Lock Normals", "allset.lock_normals"),
                     ("Mesh Display/Unlock Normals", "allset.lock_normals")):
        assert menu_map.spec(path)[1] == op, path
    for path, title in (("Mesh Display/Set Vertex Normal", "Set Vertex Normal Options"),
                        ("Mesh Display/Average", "Average Normals Options"),
                        ("Mesh Display/Set to Face", "Set to Face Normal Options")):
        w = option_windows.find_path(path)
        assert w is not None and w.title == title, (path, w and w.title)
