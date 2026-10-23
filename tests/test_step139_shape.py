"""Step 139 lane SHAPE: edge / vertex Extrude and Bevel at once with Maya's results (#70 M4, #16), editable afterwards
like step 65's polyExtrudeFace. Maya 2022 numbers measured with mayapy: research/maya/re/edit_mesh_139_shape.md
(data: tests/maya139_shape_data.py). Maya Y-up -> Blender Z-up: Maya (x, y, z) = Blender (x, -z, y).

The geometry tests build the mesh from Maya's own polyCube (vertex, edge and face order), so a Maya edge index is the
same Blender edge and an edge's direction (which side Offset goes) is Maya's."""

from importlib import import_module

import bmesh
import bpy

import kit
from maya139_shape_data import MAYA

ex = import_module(kit.MODULE + ".operators.extrude")
bev = import_module(kit.MODULE + ".operators.bevel_maya")
in_view = import_module(kit.MODULE + ".ui.in_view")
menu_map = import_module(kit.MODULE + ".ui.menu_map")

CUBE_EDGES = [(0, 1), (2, 3), (4, 5), (6, 7), (0, 2), (1, 3), (2, 4), (3, 5), (4, 6), (5, 7), (6, 0), (7, 1)]
CUBE_FACES = [(0, 1, 3, 2), (2, 3, 5, 4), (4, 5, 7, 6), (6, 7, 1, 0), (1, 7, 5, 3), (6, 0, 2, 4)]
TOP_EDGES = [1, 2, 6, 7]      # Maya polyListComponentConversion pCube1.f[1] -> edges (measured)


def b(p):
    x, y, z = p
    return (x, -z, y)


def maya_cube(size=(1.0, 1.0, 1.0), shells=((0.0, 0.0, 0.0),)):
    """bmesh of Maya polyCube(s) in Maya's vertex / edge / face order (Blender coordinates)."""
    unit = [p for p in MAYA["cube"][1]]
    bm = bmesh.new()
    for i, off in enumerate(shells):
        s = size if i == 0 else (4.0, 4.0, 4.0)
        verts = [bm.verts.new(b((x * s[0] + off[0], y * s[1] + off[1], z * s[2] + off[2]))) for x, y, z in unit]
        for a, c in CUBE_EDGES:
            bm.edges.new((verts[a], verts[c]))
        for f in CUBE_FACES:
            bm.faces.new([verts[k] for k in f])
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    bm.normal_update()
    return bm


def same_points(got, want, tol=2e-4):
    """Multiset equality with a tolerance (Maya prints 5 decimals)."""
    left = [tuple(p) for p in got]
    for p in want:
        i = next((k for k, q in enumerate(left) if all(abs(a - c) <= tol for a, c in zip(p, q))), None)
        if i is None:
            return False, p
        left.pop(i)
    return not left, left[:3]


def check(bm, key, what=""):
    counts, pts = MAYA[key]
    got = (len(bm.verts), len(bm.edges), len(bm.faces))
    assert all(c is None or c == g for c, g in zip(counts, got)), (key, what, got, counts)
    ok, bad = same_points([tuple(v.co) for v in bm.verts], [b(p) for p in pts])
    assert ok, (key, what, bad)


# --- polyExtrudeEdge ---------------------------------------------------------------------------------

EDGE_CASES = [
    ("extrude_e01", [0, 1], {}), ("extrude_e01:thickness05", [0, 1], {"thickness": 0.5}),
    ("extrude_e01:offset01", [0, 1], {"offset": 0.1}), ("extrude_e01:ltz05", [0, 1], {"local_translate_z": 0.5}),
    ("extrude_e01:div2_ltz05", [0, 1], {"divisions": 2, "local_translate_z": 0.5}),
    ("extrude_e01:div2_thick05", [0, 1], {"divisions": 2, "thickness": 0.5}),
    ("extrude_e0", [0], {}), ("extrude_e0:offset01", [0], {"offset": 0.1}),
    ("extrude_e0:thickness05", [0], {"thickness": 0.5}),
    ("extrude_top4", TOP_EDGES, {}), ("extrude_top4:ltz05", TOP_EDGES, {"local_translate_z": 0.5}),
    ("extrude_top4:thickness05", TOP_EDGES, {"thickness": 0.5}),
]


def test_edge_extrude_matches_maya():
    for key, idx, params in EDGE_CASES:
        bm = maya_cube()
        new = ex.extrude_edges(bm, [bm.edges[i] for i in idx], **params)
        check(bm, key, params)
        assert len(new) == len(MAYA[key][1]) - 8, key
        # Maya selects the new outer edges (pCube1.e[14], e[17] for two edges)
        assert sum(e.select for e in bm.edges) == len(idx) and not any(f.select for f in bm.faces), key
        bm.free()
    bm = maya_cube((4.0, 1.0, 2.0))
    for key, params in (("extrude_box_e0:thickness05", {"thickness": 0.5}), ("extrude_box_e0:offset01", {"offset": 0.1})):
        bm = maya_cube((4.0, 1.0, 2.0))
        ex.extrude_edges(bm, [bm.edges[0]], **params)
        check(bm, key, params)
        bm.free()


# --- polyExtrudeVertex ---------------------------------------------------------------------------------

VERTEX_CASES = [
    ("extrude_v0", [0], {}), ("extrude_v0:width02", [0], {"width": 0.2}), ("extrude_v0:length05", [0], {"length": 0.5}),
    ("extrude_v0:div2", [0], {"divisions": 2}), ("extrude_v0:div2_len05", [0], {"divisions": 2, "length": 0.5}),
    ("extrude_v0:width02_len05", [0], {"width": 0.2, "length": 0.5}),
    ("extrude_v01", [0, 1], {}), ("extrude_v01:length05", [0, 1], {"length": 0.5}),
]


def test_vertex_extrude_matches_maya():
    for key, idx, params in VERTEX_CASES:
        bm = maya_cube()
        ex.extrude_vertices(bm, [bm.verts[i] for i in idx], **params)
        check(bm, key, params)
        assert sum(v.select for v in bm.verts) == len(idx), key       # Maya: the tip (pCube1.vtx[0]) selected
        bm.free()
    for key, params in (("vext_box_v0", {}), ("vext_box_v0:width02", {"width": 0.2}),
                        ("vext_box_v0:width09", {"width": 0.9}), ("vext_box_v0:length2", {"length": 2.0})):
        bm = maya_cube((4.0, 1.0, 2.0))
        ex.extrude_vertices(bm, [bm.verts[0]], **params)
        check(bm, key, params)
        bm.free()


# --- polyBevel3 -------------------------------------------------------------------------------------------

BEVEL_CASES = [
    ("bevel_e0", [0], {}), ("bevel_e0:frac02", [0], {"fraction": 0.2}), ("bevel_e0:seg2", [0], {"segments": 2}),
    ("bevel_e0:seg3", [0], {"segments": 3}),
    ("bevel_e0:abs01", [0], {"offset_as_fraction": False, "offset": 0.1}),
    ("bevel_e0:seg2_depth0", [0], {"segments": 2, "depth": 0.0}),
    ("bevel_e0:seg2_depth-1.0", [0], {"segments": 2, "depth": -1.0}),
    ("bevel_e0:seg2_depth-0.5", [0], {"segments": 2, "depth": -0.5}),
    ("bevel_e0:seg2_depth0.5", [0], {"segments": 2, "depth": 0.5}),
    ("bevel_top4", TOP_EDGES, {}), ("bevel_top4:frac02", TOP_EDGES, {"fraction": 0.2}),
    ("bevel_top4:seg2", TOP_EDGES, {"segments": 2}),
    ("bevel_obj", list(range(12)), {}), ("bevel_obj:frac02", list(range(12)), {"fraction": 0.2}),
    ("bevel_obj:seg2", list(range(12)), {"segments": 2}),
    ("bev_unit_e0_e1", [0, 1], {}), ("bev_unit_e0_e2", [0, 2], {}),
]
BOX_CASES = [
    ("bevel_box_e0", [0], {}), ("bevel_box_e0:frac02", [0], {"fraction": 0.2}),
    ("bevel_box_vertical", [4], {}), ("bevel_box_vertical:frac02", [4], {"fraction": 0.2}),
    ("bevel_box_depth", [10], {}), ("bevel_box_depth:frac02", [10], {"fraction": 0.2}),
    ("bev_box_e0_e9", [0, 9], {}), ("bev_box_e4_e9", [4, 9], {}), ("bev_box_e4_e2", [4, 2], {}),
    ("bev_box_e0_e5", [0, 5], {}),
]


def test_bevel_matches_maya():
    for cases, size in ((BEVEL_CASES, (1.0, 1.0, 1.0)), (BOX_CASES, (4.0, 1.0, 2.0))):
        for key, idx, params in cases:
            bm = maya_cube(size)
            made = bev.bevel_edges(bm, [bm.edges[i] for i in idx], **params)
            assert made, key
            check(bm, key, params)
            assert not any(v.select for v in bm.verts), key     # Maya leaves nothing selected (mayapy ls -sl)
            bm.free()


def test_bevel_face_is_its_edges():
    bm = maya_cube()
    face = bm.faces[1]
    bev.bevel_edges(bm, list(face.edges))
    check(bm, "bevel_f1")
    bm.free()


def test_bevel_fraction_is_one_length_for_the_selection():
    # a unit cube and a 4-unit cube in one mesh: both get 0.5 (= 0.5 x the unit cube's shortest slide edge)
    bm = maya_cube(shells=((0.0, 0.0, 0.0), (10.0, 0.0, 0.0)))
    bev.bevel_edges(bm, [bm.edges[0], bm.edges[12]])
    check(bm, "two_shells_e0_e12")
    bm.free()


def test_chamfer_vertex_matches_maya():
    for key, size in (("chamfer_unit_v0", (1.0, 1.0, 1.0)), ("chamfer_box_v0", (4.0, 1.0, 2.0))):
        bm = maya_cube(size)
        bev.chamfer_vertices(bm, [bm.verts[0]])
        check(bm, key)
        bm.free()


# --- operators, records, Channel Box / AE ------------------------------------------------------------

def _fresh(size=(1.0, 1.0, 1.0)):
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for k in list(bpy.context.scene.keys()):
        if k.startswith("allset_poly"):
            del bpy.context.scene[k]
    me = bpy.data.meshes.new("pCubeShape1")
    bm = maya_cube(size)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("pCube1", me)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    return ob


def _select(ob, mode, idx):
    bpy.context.tool_settings.mesh_select_mode = mode
    bm = bmesh.from_edit_mesh(ob.data)
    ex.deselect_all(bm)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    seq = bm.verts if mode == (True, False, False) else bm.edges
    for i in idx:
        seq[i].select_set(True)
    bm.select_flush_mode()
    bmesh.update_edit_mesh(ob.data)


def _counts(ob):
    bm = bmesh.from_edit_mesh(ob.data)
    return len(bm.verts), len(bm.edges), len(bm.faces)


def _matches(ob, key):
    bm = bmesh.from_edit_mesh(ob.data)
    counts = (len(bm.verts), len(bm.edges), len(bm.faces))
    ok, bad = same_points([tuple(v.co) for v in bm.verts], [b(p) for p in MAYA[key][1]])
    return counts == MAYA[key][0] and ok, (counts, bad)


EDGE_MODE, VERT_MODE = (False, True, False), (True, False, False)


def _close(params, want):
    """Operator float properties are 32-bit: 0.2 comes back as 0.20000000298."""
    return params.keys() == want.keys() and all(abs(float(params[k]) - float(want[k])) < 1e-6 for k in want)


def test_ctrl_e_edges_at_once_and_edit():
    ob = _fresh()
    _select(ob, EDGE_MODE, [0, 1])
    # invoke (Ctrl+E / the menu) no longer starts Blender's extrude + drag: polyExtrudeEdge at once
    assert bpy.ops.allset.extrude('INVOKE_DEFAULT') == {'FINISHED'}
    ok, info = _matches(ob, "extrude_e01")
    assert ok, info
    o, rec = ex.active(bpy.context)
    assert o is ob and rec.name == "polyExtrudeEdge1" and rec.spec is ex.EDGE and rec.params == ex.EDGE.defaults
    assert ex.caps_selected(ob, rec)
    assert ex.set_params(bpy.context, thickness=0.5) == {'FINISHED'}
    ok, info = _matches(ob, "extrude_e01:thickness05")
    assert ok, info
    assert ex.set_params(bpy.context, thickness=0.0, divisions=2, local_translate_z=0.5) == {'FINISHED'}
    ok, info = _matches(ob, "extrude_e01:div2_ltz05")
    assert ok, info
    _o, rec = ex.active(bpy.context)
    assert rec.name == "polyExtrudeEdge1" and rec.params["divisions"] == 2
    # a second extrusion is a new node, counted per node type
    assert bpy.ops.allset.extrude() == {'FINISHED'}
    assert ex.active(bpy.context)[1].name == "polyExtrudeEdge2"


def test_ctrl_e_vertex_at_once_and_edit():
    ob = _fresh()
    _select(ob, VERT_MODE, [0])
    assert bpy.ops.allset.extrude('INVOKE_DEFAULT') == {'FINISHED'}
    ok, info = _matches(ob, "extrude_v0")
    assert ok, info
    _o, rec = ex.active(bpy.context)
    assert rec.name == "polyExtrudeVertex1" and rec.params == {"width": 0.5, "length": 1.0, "divisions": 1}
    assert ex.set_params(bpy.context, divisions=2) == {'FINISHED'}
    ok, info = _matches(ob, "extrude_v0:div2")
    assert ok, info
    assert ex.set_params(bpy.context, divisions=1, width=0.2) == {'FINISHED'}
    ok, info = _matches(ob, "extrude_v0:width02")
    assert ok, info


def test_ctrl_b_bevels_at_once_and_edit():
    ob = _fresh()
    _select(ob, EDGE_MODE, [0])
    assert bpy.ops.allset.bevel('INVOKE_DEFAULT') == {'FINISHED'}
    ok, info = _matches(ob, "bevel_e0")
    assert ok, info
    o, rec = ex.active(bpy.context)
    assert o is ob and rec.name == "polyBevel1" and rec.spec is bev.BEVEL and _close(rec.params, bev.BEVEL.defaults)
    assert ex.caps_selected(ob, rec)          # nothing selected = what the bevel left
    for changes, key in (({"fraction": 0.2}, "bevel_e0:frac02"), ({"fraction": 0.5, "segments": 3}, "bevel_e0:seg3"),
                         ({"segments": 2, "depth": 0.0}, "bevel_e0:seg2_depth0"),
                         ({"segments": 1, "depth": 1.0, "offset_as_fraction": False, "offset": 0.1}, "bevel_e0:abs01")):
        assert ex.set_params(bpy.context, **changes) == {'FINISHED'}, changes
        ok, info = _matches(ob, key)
        assert ok, (key, info)
    _o, rec = ex.active(bpy.context)
    assert rec.name == "polyBevel1" and abs(rec.params["offset"] - 0.1) < 1e-6


def test_bevel_vertex_mode_is_chamfer():
    ob = _fresh()
    _select(ob, VERT_MODE, [0])
    assert bpy.ops.allset.bevel() == {'FINISHED'}
    ok, info = _matches(ob, "chamfer_unit_v0")
    assert ok, info


def test_bevel_from_object_mode_bevels_every_edge():
    # Maya Edit Mesh > Bevel with the object selected: polyBevel1 on every edge (24/48/26, measured)
    ob = _fresh()
    bpy.ops.object.mode_set(mode='OBJECT')
    assert menu_map.MAP["Edit Mesh/Bevel"][:2] == ("v3d", "allset.bevel")
    assert menu_map.OBJECT_MODE["Edit Mesh/Bevel"] == ('ALL', 'EDGE')
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.tool_settings.mesh_select_mode = EDGE_MODE
    bpy.ops.mesh.select_all(action='SELECT')
    assert bpy.ops.allset.bevel() == {'FINISHED'}
    ok, info = _matches(ob, "bevel_obj")
    assert ok, info


def test_redo_keeps_node_name_and_maya_units():
    ob = _fresh()
    _select(ob, EDGE_MODE, [0])
    us = bpy.context.scene.unit_settings
    old = (us.system, us.length_unit, us.scale_length)
    us.system, us.length_unit, us.scale_length = 'METRIC', 'CENTIMETERS', 1.0
    try:
        units = import_module(kit.MODULE + ".operators.units")
        unit = units.maya_unit(bpy.context.scene)
        assert bpy.ops.allset.bevel(offset_as_fraction=False, offset=10.0) == {'FINISHED'}
        bm = bmesh.from_edit_mesh(ob.data)
        # absolute offset in Maya units: 10 cm in a 1 m cube (x 0.9999 like Maya)
        assert any(abs(v.co.y - (-0.5 + 10 * unit * bev.FIT)) < 1e-5 for v in bm.verts), unit
    finally:
        us.system, us.length_unit, us.scale_length = old


def test_record_states_follow_undo():
    ob = _fresh()
    _select(ob, EDGE_MODE, [0])
    bpy.ops.allset.bevel()
    ex.set_params(bpy.context, segments=2)
    _o, rec = ex.active(bpy.context)
    # back to the first state (what Ctrl+Z does): the record follows with that state's values
    ex.run(ob, rec, dict(bev.BEVEL.defaults), 1.0)
    rec.states.pop()
    _o, rec = ex.active(bpy.context)
    assert rec is not None and rec.params["segments"] == 1
    # moving a bevel vertex by hand: no longer the kit's bevel
    bm = bmesh.from_edit_mesh(ob.data)
    bm.verts.ensure_lookup_table()
    bm.verts[rec.cap_verts[0]].co.z += 0.3
    bmesh.update_edit_mesh(ob.data)
    assert ex.active(bpy.context) == (None, None)
    assert bpy.ops.allset.bevel_edit(segments=3) == {'CANCELLED'}


def test_channel_box_and_in_view_rows():
    ob = _fresh()
    _select(ob, EDGE_MODE, [0])
    bpy.ops.allset.bevel()
    hist = bpy.context.window_manager.allset_history
    assert hist.fraction_text == "0.5" and hist.segments_text == "1" and hist.offset_as_fraction_text == "on", (
        hist.fraction_text, hist.segments_text, hist.offset_as_fraction_text)
    hist.segments_text = "2"
    ok, info = _matches(ob, "bevel_e0:seg2")
    assert ok, info
    hist.fraction_text = "*=0.4"             # Maya Channel Box arithmetic: 0.5 * 0.4 = 0.2
    _o, rec = ex.active(bpy.context)
    assert abs(rec.params["fraction"] - 0.2) < 1e-6, rec.params
    # In-View Editor rows = the node's fields with Maya names
    lay = in_view.layout(type("R", (), {"width": 800, "height": 600})(), (300, 300), 1.0, rec.spec.fields)
    assert [r[0] for r in lay["rows"]] == list(bev.BEVEL.fields)
    assert [rec.spec.labels[f] for f in rec.spec.fields] == ["Fraction", "Offset As Fraction", "Offset", "Segments",
                                                               "Depth"]
    assert in_view.value_text(rec, "offset_as_fraction") == "On" and in_view.value_text(rec, "segments") == "2"
    # the AE history tab names the Maya node type
    ae = import_module(kit.MODULE + ".ui.attribute_editor")
    assert ("H", "polyBevel1", "polyBevel3") in ae.tabs(ob)
    # edge extrusion rows
    _select(ob, EDGE_MODE, [1])
    bpy.ops.allset.extrude()
    _o, rec = ex.active(bpy.context)
    assert rec.spec.fields == ("thickness", "local_translate_z", "offset", "divisions")
    assert ("H", "polyExtrudeEdge1", "polyExtrudeEdge") in ae.tabs(ob)
    hist.thickness_text = "0.5"
    assert ex.active(bpy.context)[1].params["thickness"] == 0.5


def test_bindings_and_menus():
    assert menu_map.MAP["Edit Mesh/Extrude"][:2] == ("v3d", "allset.extrude")
    assert menu_map.MAP["Edit Mesh/Bevel"][:2] == ("v3d", "allset.bevel")
    kc = kit.maya_kc()
    items = [(km.name, ki.idname, ki.type, ki.ctrl) for km in kc.keymaps for ki in km.keymap_items
             if ki.idname in ("allset.extrude", "allset.bevel") and ki.active]
    assert ("Mesh", "allset.extrude", 'E', True) in items and ("Mesh", "allset.bevel", 'B', True) in items, items
    assert hasattr(bpy.types, "ALLSET_OT_bevel_edit") or "bevel_edit" in dir(bpy.ops.allset)
