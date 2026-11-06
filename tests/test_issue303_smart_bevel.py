"""Issue #303: Edit Mesh > Smart Bevel (Maya 2027). The width is a length in scene units kept below what the edges
around allow; a filter picks the selected edges, the mesh's hard edges or its edges by angle; the bevel's border
edges can be set hard; arcs weld within a tolerance. It is a polySmartBevel history node: Channel Box INPUTS rows,
In-View Editor rows and an edit operator that rebuilds it. The item sits below Bevel in Edit Mesh, in the Modeling
Toolkit and in the Shift+RMB edge / face menus, with an option window."""

from importlib import import_module

import bmesh
import bpy
from mathutils import Vector

import kit

sb = import_module(kit.MODULE + ".operators.smart_bevel")
extrude = import_module(kit.MODULE + ".operators.extrude")
ow = import_module(kit.MODULE + ".operators.option_windows")
in_view = import_module(kit.MODULE + ".ui.in_view")
menu_map = import_module(kit.MODULE + ".ui.menu_map")
menu_sets = import_module(kit.MODULE + ".ui.menu_sets")
menu_data = import_module(kit.MODULE + ".ui.menu_data")
toolkit = import_module(kit.MODULE + ".ui.modeling_toolkit")
mm = import_module(kit.MODULE + ".marking.menus")
TOL = 1e-4


def _fresh():
    bpy.ops.wm.read_homefile(use_empty=True)
    extrude.clear()


def _cube():
    bpy.ops.allset.create(kind='CUBE')
    return bpy.context.active_object


def _edit(ob):
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    if bpy.context.mode != 'EDIT_MESH':
        bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='EDGE')
    bm = bmesh.from_edit_mesh(ob.data)
    for el in (*bm.verts, *bm.edges, *bm.faces):
        el.select = False
    bm.select_flush_mode()
    return bm


def _select_edge(bm, pick):
    bm.edges.ensure_lookup_table()
    e = next(e for e in bm.edges if pick(e))
    e.select = True
    bm.select_flush_mode()
    return e


def _top_edge(e):
    return all(v.co.z > 0.0 for v in e.verts) and abs(e.verts[0].co.x - e.verts[1].co.x) > 0.5


def _verts(ob):
    bm = bmesh.from_edit_mesh(ob.data) if bpy.context.mode == 'EDIT_MESH' else None
    return [v.co.copy() for v in bm.verts] if bm else [v.co.copy() for v in ob.data.vertices]


def _one_edge(width=0.2, **kw):
    _fresh()
    ob = _cube()
    bm = _edit(ob)
    _select_edge(bm, _top_edge)
    res = bpy.ops.allset.smart_bevel(width=width, **kw)
    return ob, res


# --- the node ---------------------------------------------------------------------------------------------------

def test_one_edge_makes_a_poly_smart_bevel_node_with_the_width_in_scene_units():
    ob, res = _one_edge(width=0.2)
    assert res == {'FINISHED'}
    bm = bmesh.from_edit_mesh(ob.data)
    assert len(bm.verts) == 10 and len(bm.faces) == 7, (len(bm.verts), len(bm.faces))
    rec = extrude.RECORDS.get(ob.name)
    assert rec is not None and rec.spec is sb.SPEC and rec.name == "polySmartBevel1", rec and rec.name
    assert abs(rec.params["width"] - 0.2) < 1e-6 and rec.params["filter"] == 'SELECTED'
    # the strip is 0.2 wide along each face (not a fraction of the 1-unit edge): the new vertices sit 0.2 in
    top = [v.co for v in bm.verts if v.co.z > 0.5 - TOL and abs(v.co.y) < 0.5 - TOL]
    assert len(top) == 2 and all(abs(abs(c.y) - 0.3) < TOL for c in top), top
    side = [v.co for v in bm.verts if abs(v.co.y) > 0.5 - TOL and 0.0 < v.co.z < 0.5 - TOL]
    assert len(side) == 2 and all(abs(c.z - 0.3) < TOL for c in side), side


def test_limit_width_keeps_a_wide_value_below_what_the_edges_allow():
    _fresh()
    ob = _cube()
    bm = _edit(ob)
    for e in bm.edges:
        e.select = True
    bm.select_flush_mode()
    assert bpy.ops.allset.smart_bevel(width=100.0, segments=1) == {'FINISHED'}
    bm = bmesh.from_edit_mesh(ob.data)
    bm.normal_update()
    assert all(abs(c) <= 0.5 + TOL for v in bm.verts for c in v.co), "a vertex left the cube"
    assert all(f.calc_area() > 1e-6 for f in bm.faces), "a face collapsed"
    centre = sum((v.co for v in bm.verts), Vector()) / len(bm.verts)
    assert all(f.normal.dot(f.calc_center_median() - centre) > 0.0 for f in bm.faces), "a face turned inside out"
    rec = extrude.RECORDS[ob.name]
    assert rec.params["width"] == 100.0        # the node keeps the asked value; the geometry uses the safe one
    # without the limit the same value would collapse the cube: the kit refuses only through the limit
    pre_edges = [e for e in rec.pre.edges if len(e.link_faces) == 2]
    assert 0.0 < sb.safe_width(pre_edges, 1.0) <= 0.5 + TOL


def test_filter_hard_edges_bevels_the_hard_edges_of_the_whole_mesh():
    _fresh()
    ob = _cube()
    bm = _edit(ob)
    for f in bm.faces:
        f.smooth = True
    for e in bm.edges:
        e.smooth = not all(v.co.z > 0.0 for v in e.verts)      # the four top rim edges are hard
    n_hard = sum(1 for e in bm.edges if not e.smooth)
    assert n_hard == 4
    bmesh.update_edit_mesh(ob.data)
    assert bpy.ops.allset.smart_bevel(width=0.1, filter='HARD') == {'FINISHED'}     # nothing selected
    bm = bmesh.from_edit_mesh(ob.data)
    assert len(bm.verts) == 12, len(bm.verts)          # each top corner became two vertices
    assert all(abs(v.co.z + 0.5) < TOL for v in bm.verts if v.co.z < 0.0), "a bottom vertex moved"


def test_filter_edges_by_angle_uses_the_filter_angle():
    _fresh()
    ob = _cube()
    _edit(ob)
    assert bpy.ops.allset.smart_bevel(width=0.1, filter='ANGLE', filter_angle=100.0) == {'CANCELLED'}
    assert len(bmesh.from_edit_mesh(ob.data).verts) == 8
    assert bpy.ops.allset.smart_bevel(width=0.1, filter='ANGLE', filter_angle=60.0) == {'FINISHED'}
    assert len(bmesh.from_edit_mesh(ob.data).verts) == 24     # all twelve right-angle edges


def _made(bm):
    """The bevel's vertices: every vertex that is not an old cube corner."""
    return [v for v in bm.verts if not all(abs(abs(c) - 0.5) < TOL for c in v.co)]


def test_border_edges_can_be_set_hard_and_the_smoothing_angle_decides_the_rest():
    ob, res = _one_edge(width=0.2, segments=3, set_border_hard=True)
    assert res == {'FINISHED'}
    bm = bmesh.from_edit_mesh(ob.data)
    made = _made(bm)
    assert len(made) == 8, len(made)                       # four profile points at each end
    border = sb.border_edges(bm, made)
    assert len(border) >= 2, len(border)
    assert all(not e.smooth for e in border), "a border edge stayed soft"
    strip = [e for e in bm.edges if e not in border and all(v in made for v in e.verts)
             and abs(e.verts[0].co.x - e.verts[1].co.x) > 0.5]
    assert len(strip) == 2 and all(e.smooth for e in strip), "a strip edge at 30 degrees should be soft"
    # without the option the border edges follow the smoothing angle: the 15-degree step to the old faces is soft
    ob, res = _one_edge(width=0.2, segments=3)
    bm = bmesh.from_edit_mesh(ob.data)
    border = sb.border_edges(bm, _made(bm))
    long = [e for e in border if e.calc_length() > 0.5]       # strip to top / side face: 15 degrees
    short = [e for e in border if e.calc_length() < 0.5]      # strip to the cube's end faces: 90 degrees
    assert len(long) == 2 and all(e.smooth for e in long), "a 15-degree border edge should be soft"
    assert short and all(not e.smooth for e in short), "a 90-degree border edge should be hard"


def test_depth_follows_the_bevel_round_flat_concave():
    def mid(depth):
        ob, res = _one_edge(width=0.2, segments=2, depth=depth)
        assert res == {'FINISHED'}
        bm = bmesh.from_edit_mesh(ob.data)
        pts = [v.co.copy() for v in bm.verts if 0.3 + TOL < v.co.z < 0.5 - TOL and 0.3 + TOL < abs(v.co.y) < 0.5 - TOL]
        assert len(pts) == 2, pts
        p = pts[0]
        return Vector((p.x, abs(p.y), p.z))
    flat = mid(0.0)
    assert abs(flat.y + flat.z - 0.8) < 1e-3, flat          # on the chord between (0.3, 0.5) and (0.5, 0.3)
    assert mid(1.0).y + mid(1.0).z > 0.8 + 0.01              # round: bulges toward the old corner
    assert mid(-1.0).y + mid(-1.0).z < 0.8 - 0.01            # concave: dips inside


def test_weld_arcs_merges_the_bevel_vertices_within_the_tolerance():
    ob, res = _one_edge(width=0.2, segments=3)
    assert res == {'FINISHED'}
    n = len(bmesh.from_edit_mesh(ob.data).verts)
    ob2, res = _one_edge(width=0.2, segments=3, weld_all_arcs=0.5)
    assert res == {'FINISHED'}
    assert len(bmesh.from_edit_mesh(ob2.data).verts) < n


def test_edit_operator_rebuilds_the_same_node():
    ob, res = _one_edge(width=0.2)
    before = _verts(ob)
    assert bpy.ops.allset.smart_bevel_edit(width=0.3) == {'FINISHED'}
    rec = extrude.RECORDS[ob.name]
    assert rec.name == "polySmartBevel1" and abs(rec.params["width"] - 0.3) < 1e-6
    after = _verts(ob)
    assert len(after) == len(before) and any((a - b).length > 0.05 for a, b in zip(after, before))
    bm = bmesh.from_edit_mesh(ob.data)
    top = [v.co for v in bm.verts if v.co.z > 0.5 - TOL and abs(v.co.y) < 0.5 - TOL]
    assert len(top) == 2 and all(abs(abs(c.y) - 0.2) < TOL for c in top), top
    assert in_view.handle_fields(rec, "TZ") == ("width",)      # T: the arrow drags the Width


def test_segments_and_depth_rows_in_view_and_channel_box_kinds():
    assert sb.SPEC.view_fields == ("width", "segments", "depth")
    assert sb.SPEC.kinds["segments"] == "INT" and sb.SPEC.kinds["limit_width"] == "BOOL"
    assert sb.SPEC.node_type == "polySmartBevel" and sb.SPEC.arrow == "width" and sb.SPEC.component == 'EDGE'
    assert "segments" in in_view.INT_FIELDS and in_view.clamp("width", -1.0) == 0.0


# --- menus, option window, object mode ------------------------------------------------------------------------

def test_menu_places():
    items = menu_data.MENUS['mainEditMeshMenu'][3] if isinstance(menu_data.MENUS, dict) else None
    paths = [p for p, _it in menu_sets.children(items, "Edit Mesh") if p]
    i = paths.index("Edit Mesh/Bevel")
    assert paths[i + 1] == "Edit Mesh/Smart Bevel", paths[i:i + 3]
    assert menu_map.MAP["Edit Mesh/Smart Bevel"] == ("v3d", "allset.smart_bevel", {})
    w = ow.find_path("Edit Mesh/Smart Bevel")
    assert w is not None and w.key == "smart_bevel" and w.title == "Smart Bevel Options"
    assert w.defaults()["width"] == 0.2 and w.defaults()["filter"] == "Selected Edges"
    assert ("Smart Bevel", "Edit Mesh/Smart Bevel", 'MOD_BEVEL') in toolkit.COMPONENTS
    assert any(it[0] == "Smart Bevel" for it in mm.SHIFT_EDGE.items if it != mm.DIVIDER)
    assert any(it[0] == "Smart Bevel" for it in mm.SHIFT_FACE.items if it != mm.DIVIDER)


def test_option_window_runs_from_object_mode_on_the_whole_mesh():
    _fresh()
    ob = _cube()
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    res = ow.run(ow._BY_KEY["smart_bevel"], bpy.context, dict(ow._BY_KEY["smart_bevel"].defaults(), width=0.1,
                                                              segments=2))
    assert not isinstance(res, str), res
    assert bpy.context.mode == 'OBJECT' and len(ob.data.vertices) == 48, len(ob.data.vertices)
    rec = in_view.cb_record(bpy.context, ob)
    assert rec is not None and rec.name == "polySmartBevel1" and rec.params["segments"] == 2
    # the window's filter radio reaches the operator as its keyword
    _fresh()
    ob = _cube()
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    res = ow.run(ow._BY_KEY["smart_bevel"], bpy.context,
                 dict(ow._BY_KEY["smart_bevel"].defaults(), width=0.1, filter="Edges by Angle", filter_angle=100.0))
    assert isinstance(res, str) or len(ob.data.vertices) == 8, (res, len(ob.data.vertices))


def test_menu_item_from_object_mode_lists_the_node_in_the_channel_box():
    _fresh()
    ob = _cube()
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    assert bpy.ops.allset.menu_item(item="Edit Mesh/Smart Bevel") == {'FINISHED'}
    assert bpy.context.mode == 'OBJECT'
    rec = in_view.cb_record(bpy.context, ob)
    assert rec is not None and rec.name == "polySmartBevel1", rec
    assert len(ob.data.vertices) == 24
    assert bpy.ops.allset.smart_bevel_edit(segments=2) == {'FINISHED'}
    assert len(ob.data.vertices) == 48 and in_view.cb_record(bpy.context, ob).name == "polySmartBevel1"
