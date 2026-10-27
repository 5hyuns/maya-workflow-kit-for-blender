"""Step 257 (#149): the kit numbers a Create > Cylinder -> Extrude -> Bevel chain like Maya 2026, by index.

Maya truth: tests/maya257_chain_data.py (primitives' edge ids, polyExtrudeFacet before / after) and
tests/maya257_bevel_data.py CASES["chain_rim"] (polyBevel3 of the extruded cap's rim). Rules:
research/maya/re/bevel_numbering_257.md §6 (primitive edge ids), §7 (extrusion). Maya (x, y, z) -> Blender (x, -z, y)
x Maya unit."""

from importlib import import_module

import bmesh
import bpy
from mathutils import Vector

import kit
from maya257_bevel_data import CASES
from maya257_chain_data import EXT, PRIMS

ex = import_module(kit.MODULE + ".operators.extrude")
bev = import_module(kit.MODULE + ".operators.bevel_maya")
create = import_module(kit.MODULE + ".operators.create")
units = import_module(kit.MODULE + ".operators.units")
ps = import_module(kit.MODULE + ".operators.prim_shapes")
ph = import_module(kit.MODULE + ".operators.prim_history")

TOL = 1e-4


def b(p, k=1.0):
    return Vector((p[0], -p[2], p[1])) * k


def vertex_error(bm, points, k=1.0):
    bm.verts.ensure_lookup_table()
    if len(bm.verts) != len(points):
        return f"{len(bm.verts)} vertices, Maya {len(points)}"
    for i, p in enumerate(points):
        if (bm.verts[i].co - b(p, k)).length > TOL * k:
            return f"vertex {i} at {tuple(round(c / k, 5) for c in bm.verts[i].co)}, Maya {tuple(b(p))}"
    return None


def face_error(bm, faces, corners=True):
    """Faces by index; ``corners``: the same first corner too, else only the same cycle."""
    bm.faces.ensure_lookup_table()
    if len(bm.faces) != len(faces):
        return f"{len(bm.faces)} faces, Maya {len(faces)}"
    for i, f in enumerate(faces):
        got = [v.index for v in bm.faces[i].verts]
        if corners and got != f:
            return f"face {i} = {got}, Maya {f}"
        if not corners and not any(got[r:] + got[:r] == f for r in range(len(got))):
            return f"face {i} = {got}, Maya {f}"
    return None


def edge_error(bm, edges, ordered=True):
    """Edges by index; ``ordered``: Maya's vertex order inside each edge too."""
    bm.edges.ensure_lookup_table()
    if len(bm.edges) != len(edges):
        return f"{len(bm.edges)} edges, Maya {len(edges)}"
    for i, e in enumerate(edges):
        got = [v.index for v in bm.edges[i].verts]
        if (got != e) if ordered else (set(got) != set(e)):
            return f"edge {i} = {got}, Maya {e}"
    return None


def same_shape(bm, points, k=1.0):
    left = [b(p, k) for p in points]
    if len(left) != len(bm.verts):
        return False
    for v in bm.verts:
        j = min(range(len(left)), key=lambda j: (left[j] - v.co).length)
        if (left[j] - v.co).length > TOL * k:
            return False
        left.pop(j)
    return True


def build(before, k=1.0):
    """A bmesh of Maya's mesh with Maya's vertex, edge and face ids."""
    bm = bmesh.new()
    verts = [bm.verts.new(b(p, k)) for p in before["points"]]
    for a, c in before["edges"]:
        bm.edges.new((verts[a], verts[c]))
    for f in before["faces"]:
        bm.faces.new([verts[i] for i in f])
    for seq in (bm.verts, bm.edges, bm.faces):
        seq.index_update()
        seq.ensure_lookup_table()
    bm.normal_update()
    return bm


# --- primitives: Maya's vertex, edge and face ids ------------------------------------------------------------------

def test_kit_primitives_have_mayas_edge_ids():
    """polyCylinder (Subdivisions Caps 0 - 3, round caps) and polyCube (every subdivision mix measured): the kit's
    bmesh = Maya's mesh by index - vertices, faces (first corner too), edges (Maya's vertex order too)."""
    bad, n = [], 0
    for name, d in PRIMS.items():
        a = ps.defaults(d["node"])
        a.update(d["attrs"])
        bm = bmesh.new()
        ph.fill_bmesh(bm, ps.build(d["node"], a), 1.0)
        for seq in (bm.verts, bm.edges, bm.faces):
            seq.index_update()
        errs = [face_error(bm, d["faces"]), edge_error(bm, d["edges"])]
        if d["points"] is not None:
            errs.append(vertex_error(bm, d["points"]))
        bad += [(name, e) for e in errs if e]
        n += 1
        bm.free()
    assert not bad, bad
    assert n == 57, n


def test_menu_cylinder_object_keeps_mayas_edge_ids():
    """Create > Cylinder (object, through the mesh datablock) and back into edit mode: still Maya's ids."""
    ob = _kit_cylinder()
    k = units.maya_unit(bpy.context.scene)
    d = PRIMS["menu_cyl"]
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    for seq in (bm.verts, bm.edges, bm.faces):
        seq.index_update()
    assert vertex_error(bm, d["points"], k) is None, vertex_error(bm, d["points"], k)
    assert face_error(bm, d["faces"]) is None, face_error(bm, d["faces"])
    assert edge_error(bm, d["edges"]) is None, edge_error(bm, d["edges"])
    bm.free()
    _edit(ob)
    bm = bmesh.from_edit_mesh(ob.data)
    bm.verts.index_update()
    assert edge_error(bm, d["edges"]) is None, edge_error(bm, d["edges"])
    bpy.ops.object.mode_set(mode='OBJECT')


# --- polyExtrudeFacet ----------------------------------------------------------------------------------------------

def _extrude_case(d, k=1.0):
    bm = build(d["before"], k)
    faces = [bm.faces[i] for i in d["sel"]]
    ex.extrude(bm, faces, local_translate_z=d["ltz"] * k, divisions=d["div"], keep_faces_together=d["kft"])
    for seq in (bm.verts, bm.edges, bm.faces):
        seq.index_update()
    return bm


# the kit's extrusion *shape* (positions, not numbering) differs from Maya's here - farthest vertex 0.21 Maya units
# (corner of three extruded faces, closed shells), 0.41 (cyl5_2_2_cap), 0.09 (sphere_all); faces and edges are still
# checked by index, which checks the vertex numbering through the faces' vertex ids. Not checked: which end comes
# first inside an edge, and the first corner of the side faces of faces extruded apart (Keep Faces Together off)
SHAPE_OPEN = {"cube_f014", "cube_f410", "cyl5_2_2_cap", "cube_all", "cube_all_div2", "c222_all", "sphere_all"}


def test_kit_extrude_numbered_like_maya():
    """Every measured polyExtrudeFacet (cube / cylinder / sphere / plane / face-list meshes; single, connected and
    separate faces; Keep Faces Together on and off; Divisions 1 - 3; inner vertices; whole closed shells): the kit's
    result has Maya's vertex, edge and face ids."""
    bad, shape = [], set()
    for name, d in EXT.items():
        bm = _extrude_case(d)
        if not same_shape(bm, d["after"]["points"]):
            shape.add(name)            # numbering can't be told by position: faces / edges still by index
        else:
            err = vertex_error(bm, d["after"]["points"])
            if err:
                bad.append((name, err))
        for err in (face_error(bm, d["after"]["faces"], corners=False),
                    edge_error(bm, d["after"]["edges"], ordered=False)):
            if err:
                bad.append((name, err))
        bm.free()
    assert not bad, bad
    assert shape == SHAPE_OPEN, (sorted(shape - SHAPE_OPEN), sorted(SHAPE_OPEN - shape))
    assert len(EXT) == 57, len(EXT)


def test_extrude_record_edit_keeps_mayas_numbering():
    """allset.extrude (Ctrl+E) on the menu cylinder's cap, then an edit of its polyExtrudeFace node (step 65
    record): Maya's numbering both times."""
    ob = _kit_cylinder()
    k = units.maya_unit(bpy.context.scene)
    d = EXT["menucyl_cap_api"]
    _edit(ob)
    _select_faces(ob, d["sel"])
    assert bpy.ops.allset.extrude() == {'FINISHED'}
    assert ex.set_params(bpy.context, local_translate_z=0.4) == {'FINISHED'}
    assert ex.set_params(bpy.context, local_translate_z=1.0) == {'FINISHED'}
    bm = bmesh.from_edit_mesh(ob.data)
    for seq in (bm.verts, bm.edges, bm.faces):
        seq.index_update()
    assert vertex_error(bm, d["after"]["points"], k) is None, vertex_error(bm, d["after"]["points"], k)
    assert face_error(bm, d["after"]["faces"], corners=False) is None
    assert edge_error(bm, d["after"]["edges"], ordered=False) is None
    bpy.ops.object.mode_set(mode='OBJECT')


# --- the #149 chain, live -------------------------------------------------------------------------------------------

def _kit_cylinder():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    ob = create.create(bpy.context, 'CYLINDER')
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    return ob


def _edit(ob):
    for o in bpy.context.view_layer.objects:
        o.select_set(o == ob)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT')


def _select_faces(ob, ids):
    bpy.ops.mesh.select_mode(type='FACE')
    bm = bmesh.from_edit_mesh(ob.data)
    bm.faces.index_update()
    want = set(ids)
    for f in bm.faces:
        f.select_set(False)
    for f in bm.faces:
        if f.index in want:
            f.select_set(True)
    bm.select_flush_mode()
    bmesh.update_edit_mesh(ob.data)


def test_issue_149_chain_numbered_like_maya():
    """Create > Cylinder -> Ctrl+E on the cap + Local Translate Z 1 -> Ctrl+B on the cap rim, through the kit's
    operators: vertices (82) and faces (100) by index = Maya's polyBevel3 result."""
    ob = _kit_cylinder()
    k = units.maya_unit(bpy.context.scene)
    _edit(ob)
    _select_faces(ob, EXT["menucyl_cap_api"]["sel"])
    assert bpy.ops.allset.extrude() == {'FINISHED'}
    assert ex.set_params(bpy.context, local_translate_z=1.0) == {'FINISHED'}
    case = CASES["chain_rim"]
    bpy.ops.mesh.select_mode(type='EDGE')
    bm = bmesh.from_edit_mesh(ob.data)
    bm.edges.index_update()
    want = set(case["sel"])
    for e in bm.edges:
        e.select_set(False)
    for e in bm.edges:
        if e.index in want:
            e.select_set(True)
    bmesh.update_edit_mesh(ob.data)
    assert bpy.ops.allset.bevel('INVOKE_DEFAULT') == {'FINISHED'}
    bm = bmesh.from_edit_mesh(ob.data)
    for seq in (bm.verts, bm.edges, bm.faces):
        seq.index_update()
    assert len(bm.verts) == 82 and len(bm.faces) == 100, (len(bm.verts), len(bm.faces))
    assert vertex_error(bm, case["after"]["points"], k) is None, vertex_error(bm, case["after"]["points"], k)
    assert face_error(bm, case["after"]["faces"], corners=False) is None, \
        face_error(bm, case["after"]["faces"], corners=False)
    bpy.ops.object.mode_set(mode='OBJECT')


# --- modeling regression scenario ---------------------------------------------------------------------------------

def _snapshot(me):
    return ([tuple(round(c, 6) for c in v.co) for v in me.vertices], [tuple(e.vertices) for e in me.edges],
            [tuple(p.vertices) for p in me.polygons])


def test_modeling_regression_scenario():
    """Cube / Cylinder -> Extrude (Maya ids checked) -> Bevel -> Multi-Cut -> Merge -> UV Automatic -> Delete History
    -> save / open: every step runs and the saved file keeps the numbering by index."""
    import os
    import tempfile
    mc = import_module(kit.MODULE + ".operators.multi_cut")
    folder = tempfile.mkdtemp(prefix="s257_")
    for kind, case in (('CUBE', "cube_f1"), ('CYLINDER', "menucyl_cap_api")):
        for ob in list(bpy.data.objects):
            bpy.data.objects.remove(ob)
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        ob = create.create(bpy.context, kind)
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        k = units.maya_unit(bpy.context.scene)
        d = EXT[case]
        _edit(ob)
        _select_faces(ob, d["sel"])
        assert bpy.ops.allset.extrude() == {'FINISHED'}, kind
        assert ex.set_params(bpy.context, local_translate_z=d["ltz"]) == {'FINISHED'}, kind
        bm = bmesh.from_edit_mesh(ob.data)
        for seq in (bm.verts, bm.edges, bm.faces):
            seq.index_update()
        assert vertex_error(bm, d["after"]["points"], k) is None, (kind, vertex_error(bm, d["after"]["points"], k))
        assert face_error(bm, d["after"]["faces"], corners=False) is None, kind
        assert edge_error(bm, d["after"]["edges"], ordered=False) is None, kind
        # Bevel the new cap's rim
        bpy.ops.mesh.select_mode(type='EDGE')
        caps = {bm.faces[i] for i in d["sel"]}
        rim = {e for e in bm.edges if sum(1 for f in e.link_faces if f in caps) == 1}
        for e in bm.edges:
            e.select_set(e in rim)
        bmesh.update_edit_mesh(ob.data)
        n0 = len(bm.verts)
        assert bpy.ops.allset.bevel('INVOKE_DEFAULT') == {'FINISHED'}, kind
        bm = bmesh.from_edit_mesh(ob.data)
        assert len(bm.verts) == n0 + len(rim), (kind, len(bm.verts), n0, len(rim))
        # Multi-Cut across a side face (two of its opposite edges, halfway)
        bm.faces.ensure_lookup_table()
        bm.edges.index_update()
        quad = next(f for f in bm.faces if len(f.verts) == 4)
        e0, e2 = quad.edges[0], quad.edges[2]
        n1 = len(bm.verts)
        assert mc.cut(bm, [('EDGE', e0.index, 0.5), ('EDGE', e2.index, 0.5)]), kind
        assert len(bm.verts) == n1 + 2, kind
        bmesh.update_edit_mesh(ob.data)
        # Merge the two cut vertices
        bpy.ops.mesh.select_mode(type='VERT')
        bm = bmesh.from_edit_mesh(ob.data)
        bm.verts.ensure_lookup_table()
        for v in bm.verts:
            v.select_set(v.index >= n1)
        bmesh.update_edit_mesh(ob.data)
        assert bpy.ops.allset.merge() == {'FINISHED'}, kind
        bm = bmesh.from_edit_mesh(ob.data)
        assert len(bm.verts) == n1 + 1, (kind, len(bm.verts), n1)
        # UV > Automatic on everything, Delete History, save / open
        bpy.ops.mesh.select_all(action='SELECT')
        assert bpy.ops.allset.uv_automatic() == {'FINISHED'}, kind
        bpy.ops.object.mode_set(mode='OBJECT')
        assert bpy.ops.allset.delete_history() == {'FINISHED'}, kind
        before = _snapshot(ob.data)
        name = ob.name
        path = os.path.join(folder, f"{kind.lower()}.blend")
        bpy.ops.wm.save_as_mainfile(filepath=path)
        bpy.ops.wm.open_mainfile(filepath=path)
        assert _snapshot(bpy.data.objects[name].data) == before, kind
