"""Step 257 (#149): Edit Mesh > Bevel numbers its result like Maya 2026 polyBevel3 (vertex index i = Maya's vertex i).

Maya truth: tests/maya257_bevel_data.py (mayapy, tmp/s257_bevel/m_bev.py / m_adj.py); rules:
research/maya/re/bevel_numbering_257.md. Maya (x, y, z) -> Blender (x, -z, y); the meshes are built at Maya unit 1 from
Maya's own vertex / face order, so the only kit input that can differ from Maya is the edge numbering, which is passed
explicitly (``edge_ids``) for histories the kit can't number itself and left to the kit (the mesh's edge index) for
the kit's own cube and for meshes whose edges were made in face-corner order. The live #149 chain (kit cylinder ->
Extrude -> Bevel): tests/test_step257_chain.py."""

from importlib import import_module

import bmesh
import bpy
from mathutils import Vector

import kit
from maya257_bevel_data import ADJ, CASES

bev = import_module(kit.MODULE + ".operators.bevel_maya")
create = import_module(kit.MODULE + ".operators.create")
units = import_module(kit.MODULE + ".operators.units")
ex = import_module(kit.MODULE + ".operators.extrude")

TOL = 1e-4
# Cases whose bevel *shape* the kit doesn't reproduce (steps 139 / 239 fitted the cube and the cylinder cap): numbering
# can't be checked by position there. Kept exact, so a shape fix (or a new shape miss) shows up here.
SHAPE_OPEN = {"cube_0_2_8_10", "created2_1_2_7", "cyl8_rim", "sphere_3", "sphere_pole", "c232_0", "c232_20",
              "c232_50", "c232_55", "c232_0_1_20", "c232_20_21_22", "c232_50_54_55_56", "created2s_0_9_17",
              "created2s_4_30_31_40", "chain_both_rims", "cyl8_both_rims", "cyl8_bottom_rim", "plane_inner_square"}


def b(p, k=1.0):
    return Vector((p[0], -p[2], p[1])) * k


def corner_order(faces):
    """Edges in face-corner creation order (corner k -> k + 1): Maya's ids of a mesh made from a face list."""
    seen, out = set(), []
    for f in faces:
        for k in range(len(f)):
            pair = (f[k], f[(k + 1) % len(f)])
            if frozenset(pair) not in seen:
                seen.add(frozenset(pair))
                out.append(pair)
    return out


def build(before, k=1.0, edges=None):
    """``edges``: vertex pairs made first, in this order (the bmesh edge index = their position)."""
    bm = bmesh.new()
    verts = [bm.verts.new(b(p, k)) for p in before["points"]]
    for a, c in edges or ():
        bm.edges.new((verts[a], verts[c]))
    for f in before["faces"]:
        bm.faces.new([verts[i] for i in f])
    bm.verts.index_update()
    bm.edges.index_update()
    bm.faces.index_update()
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    bm.normal_update()
    return bm


def edge_map(bm, maya_edges):
    by_pair = {frozenset(e): i for i, e in enumerate(maya_edges)}
    return {e: by_pair[frozenset((e.verts[0].index, e.verts[1].index))] for e in bm.edges}


def selected(bm, ids, sel):
    want = set(sel)
    return [e for e in bm.edges if ids[e] in want]


def compare_vertices(bm, after, k=1.0):
    """Index of the first vertex not at Maya's position (None = all match)."""
    bm.verts.ensure_lookup_table()
    if len(bm.verts) != len(after["points"]):
        return f"{len(bm.verts)} vertices, Maya {len(after['points'])}"
    for i, p in enumerate(after["points"]):
        if (bm.verts[i].co - b(p, k)).length > TOL * k:
            return f"vertex {i} at {tuple(round(c / k, 5) for c in bm.verts[i].co)}, Maya {b(p)[:]}"
    return None


def compare_faces(bm, after):
    bm.faces.ensure_lookup_table()
    if len(bm.faces) != len(after["faces"]):
        return f"{len(bm.faces)} faces, Maya {len(after['faces'])}"
    for i, f in enumerate(after["faces"]):
        if {v.index for v in bm.faces[i].verts} != set(f):
            return f"face {i} = {[v.index for v in bm.faces[i].verts]}, Maya {f}"
    return None


def closed(case):
    """Every bevelled vertex ends two or more bevelled edges: the face order is Maya's only then (research §4)."""
    count = {}
    for i in case["sel"]:
        for v in case["before"]["edges"][i]:
            count[v] = count.get(v, 0) + 1
    return all(n >= 2 for n in count.values())


def same_shape(bm, after, k=1.0):
    left = [b(p, k) for p in after["points"]]
    if len(left) != len(bm.verts):
        return False
    for v in bm.verts:
        j = min(range(len(left)), key=lambda j: (left[j] - v.co).length)
        if (left[j] - v.co).length > TOL * k:
            return False
        left.pop(j)
    return True


# --- Maya's vertex -> edge order ---------------------------------------------------------------------------------

def test_vertex_edge_order_is_mayas():
    """E(v) (MItMeshVertex.getConnectedEdges) from the faces + Maya edge ids, closed and border vertices."""
    total = 0
    for name, d in ADJ.items():
        bm = build({"points": [(0.0, 0.0, 0.0)] * len(d["e"]), "faces": d["faces"]})
        ids = edge_map(bm, d["edges"])
        for v in bm.verts:
            got = bev.vertex_edges(v, ids)
            assert got is not None and [ids[e] for e in got] == d["e"][v.index], (name, v.index, got, d["e"][v.index])
            total += 1
        bm.free()
    assert total == 184, total


# --- the numbering on Maya-ordered input with Maya edge ids -------------------------------------------------------

def test_bevel_numbering_like_maya():
    bad, shape_miss, faces_checked = [], set(), 0
    for name, case in CASES.items():
        bm = build(case["before"])
        ids = edge_map(bm, case["before"]["edges"])
        bev.bevel_edges(bm, selected(bm, ids, case["sel"]), edge_ids=ids)
        if not same_shape(bm, case["after"]):
            shape_miss.add(name)
        else:
            err = compare_vertices(bm, case["after"])
            if err:
                bad.append((name, err))
            if closed(case):
                faces_checked += 1
                err = compare_faces(bm, case["after"])
                if err:
                    bad.append((name, err))
        bm.free()
    assert not bad, bad
    assert shape_miss == SHAPE_OPEN, (sorted(shape_miss - SHAPE_OPEN), sorted(SHAPE_OPEN - shape_miss))
    assert len(CASES) - len(SHAPE_OPEN) == 61 and faces_checked == 13, (len(CASES) - len(SHAPE_OPEN), faces_checked)


def test_chain_rim_is_issue_149():
    """The #149 case itself: extruded cylinder cap rim, 62 -> 82 vertices, by index."""
    case = CASES["chain_rim"]
    bm = build(case["before"])
    ids = edge_map(bm, case["before"]["edges"])
    bev.bevel_edges(bm, selected(bm, ids, case["sel"]), edge_ids=ids)
    assert len(bm.verts) == 82
    assert compare_vertices(bm, case["after"]) is None, compare_vertices(bm, case["after"])
    assert compare_faces(bm, case["after"]) is None, compare_faces(bm, case["after"])
    bm.free()


# --- the kit numbers the edges itself ------------------------------------------------------------------------------

def _kit_cube():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    ob = create.create(bpy.context, 'CUBE')
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    return ob


def test_kit_cube_bevel_numbered_like_maya():
    """Kit polyCube: its edge index is Maya's polyCube edge id (no ``edge_ids``)."""
    ob = _kit_cube()
    k = units.maya_unit(bpy.context.scene)
    bad = []
    n = 0
    for name, case in CASES.items():
        if not name.startswith("cube_") or name in SHAPE_OPEN:
            continue
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        bm.verts.ensure_lookup_table()
        ids = edge_map(bm, case["before"]["edges"])
        assert bev.maya_edge_ids(bm) == ids, "kit cube edge ids"
        bev.bevel_edges(bm, selected(bm, ids, case["sel"]), unit=k)
        err = compare_vertices(bm, case["after"], k)
        if err:
            bad.append((name, err))
        if closed(case):
            err = compare_faces(bm, case["after"])
            if err:
                bad.append((name, err))
        bm.free()
        n += 1
    assert n == 40, n
    assert not bad, bad


def test_face_list_mesh_numbered_like_maya():
    """A mesh made from a face list: Maya numbers its edges in face-corner order; a bmesh with its edges made in that
    order has them as its edge index, which the kit takes as Maya's ids."""
    bad = []
    n = 0
    for name, case in CASES.items():
        if not name.startswith("created") or name in SHAPE_OPEN:
            continue
        bm = build(case["before"], edges=corner_order(case["before"]["faces"]))
        ids = edge_map(bm, case["before"]["edges"])
        assert bev.maya_edge_ids(bm) == ids, (name, "face-corner edge order")
        bev.bevel_edges(bm, selected(bm, ids, case["sel"]))
        err = compare_vertices(bm, case["after"])
        if err:
            bad.append((name, err))
        if closed(case):
            err = compare_faces(bm, case["after"])
            if err:
                bad.append((name, err))
        bm.free()
        n += 1
    assert n == 14, n
    assert not bad, bad


def test_ctrl_b_record_keeps_maya_numbering():
    """Edit Mesh > Bevel (allset.bevel) and an edit of its polyBevel node (step 65 record) both number like Maya."""
    ob = _kit_cube()
    k = units.maya_unit(bpy.context.scene)
    for o in bpy.context.view_layer.objects:
        o.select_set(o == ob)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='EDGE')
    case = CASES["cube_top_loop"]
    bm = bmesh.from_edit_mesh(ob.data)
    ids = bev.maya_edge_ids(bm)
    for e in bm.edges:
        e.select_set(ids[e] in case["sel"])
    bmesh.update_edit_mesh(ob.data)
    assert bpy.ops.allset.bevel('INVOKE_DEFAULT') == {'FINISHED'}
    bm = bmesh.from_edit_mesh(ob.data)
    assert compare_vertices(bm, case["after"], k) is None, compare_vertices(bm, case["after"], k)
    assert ex.set_params(bpy.context, fraction=0.3) == {'FINISHED'}
    assert ex.set_params(bpy.context, fraction=0.5) == {'FINISHED'}
    bm = bmesh.from_edit_mesh(ob.data)
    assert compare_vertices(bm, case["after"], k) is None, compare_vertices(bm, case["after"], k)
    assert compare_faces(bm, case["after"]) is None, compare_faces(bm, case["after"])
    bpy.ops.object.mode_set(mode='OBJECT')
