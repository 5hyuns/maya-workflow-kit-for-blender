"""Issue #429: Ctrl+Shift+drag with the Rotate / Scale tool keeps every vertex on one of its edges (Maya's edge
transform constraint): operators/edge_constraint.py (the rule), operators/edge_rotate.py (the Rotate drag),
manip_scale's ``edge`` option (the Scale drag) and the Ctrl+Shift keys on the Rotate / Scale handles and middle drag.
GUI (real handle drags): tests/gui/gui_issue429_edge_rotate_scale.py."""

import math
import random
from importlib import import_module

import bmesh
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

import kit

ec = import_module(kit.MODULE + ".operators.edge_constraint")
ms = import_module(kit.MODULE + ".operators.manip_scale")
mp = import_module(kit.MODULE + ".keymap.maya_patches")

TOL = 1e-4


def _override():
    return bpy.context.temp_override(window=bpy.context.window_manager.windows[0])


def _grid_cube(cuts=1, jitter=0.0):
    """A 2-unit cube (``cuts`` = faces per side) in edit mode, nothing selected; ``jitter`` moves every point."""
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    me = bpy.data.meshes.new("c")
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=2.0)
    if cuts > 1:
        bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=cuts - 1, use_grid_fill=True)
    rng = random.Random(7)
    for v in bm.verts:
        v.co += Vector([rng.uniform(-jitter, jitter) for _ in range(3)])
    bm.to_mesh(me)
    ob = bpy.data.objects.new("c", me)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    ts = bpy.context.scene.tool_settings
    ts.use_proportional_edit = False
    return ob


def _select(ob, test, mode='VERT'):
    bpy.ops.mesh.select_mode(type=mode)
    bm = bmesh.from_edit_mesh(ob.data)
    elems = {'VERT': bm.verts, 'EDGE': bm.edges, 'FACE': bm.faces}[mode]
    for e in elems:
        c = e.co if mode == 'VERT' else sum((v.co for v in e.verts), Vector()) / len(e.verts)
        e.select_set(test(c))
    bm.select_flush_mode()
    bmesh.update_edit_mesh(ob.data)
    return [v.index for v in bm.verts if v.select]


def _coords(ob):
    bm = bmesh.from_edit_mesh(ob.data)
    return [v.co.copy() for v in bm.verts]


def _on_own_edge(before, after, ob, idx):
    """Vertex ``idx`` sits on one of its original edges (or where it was)."""
    bm = bmesh.from_edit_mesh(ob.data)
    bm.verts.ensure_lookup_table()
    p, w = before[idx], after[idx]
    if (w - p).length < TOL:
        return True
    for e in bm.verts[idx].link_edges:
        u = before[e.other_vert(bm.verts[idx]).index]
        seg = u - p
        t = (w - p).dot(seg) / seg.length_squared
        if -TOL <= t <= 1 + TOL and ((p + seg * t) - w).length < TOL:
            return True
    return False


def _scale_about(ob, sel, factors, pivot):
    """Plain scale of the selected points (what the tool does before the constraint)."""
    bm = bmesh.from_edit_mesh(ob.data)
    bm.verts.ensure_lookup_table()
    for i in sel:
        r = bm.verts[i].co - pivot
        bm.verts[i].co = pivot + Vector([r[k] * factors[k] for k in range(3)])
    bmesh.update_edit_mesh(ob.data)


def _constrained_scale(ob, sel, factors, pivot):
    prep = ec.prepare(bpy.context)
    before = _coords(ob)
    _scale_about(ob, sel, factors, pivot)
    ec.apply(prep)
    return before, _coords(ob)


def test_every_vertex_ends_on_an_edge():
    """Faces, an edge loop, single vertices and a few vertices of a cube and a crooked grid cube, random scales:
    every selected vertex ends on one of its own edges, unselected ones stay."""
    rng = random.Random(429)
    for jitter in (0.0, 0.15):
        for mode, test in (('FACE', lambda c: c.y > 0.6), ('EDGE', lambda c: abs(c.y) < 0.4),
                           ('VERT', lambda c: c.x > 0.6 and c.y > 0.6 and c.z > 0.6),
                           ('VERT', lambda c: c.y > 0.6 and c.z < -0.6)):
            for _ in range(6):
                ob = _grid_cube(cuts=2, jitter=jitter)
                sel = _select(ob, test, mode)
                assert sel, mode
                f = [1 + rng.uniform(-0.4, 0.4) for _ in range(3)]
                piv = Vector([rng.uniform(-0.5, 0.5) for _ in range(3)])
                before, after = _constrained_scale(ob, sel, f, piv)
                for i in range(len(before)):
                    if i in sel:
                        assert _on_own_edge(before, after, ob, i), (mode, jitter, i, before[i], after[i])
                    else:
                        assert (after[i] - before[i]).length < TOL, (mode, i)


def test_top_face_scaled_up_slides_down_the_sides():
    """The top face of a cube scaled up across X and Z: its corners go down the vertical edges by the same amount."""
    ob = _grid_cube()
    sel = _select(ob, lambda c: c.y > 0.9, 'FACE')
    before, after = _constrained_scale(ob, sel, (1.2, 1.0, 1.2), Vector((0, 1, 0)))
    drops = []
    for i in sel:
        d = after[i] - before[i]
        assert abs(d.x) < TOL and abs(d.z) < TOL and d.y < -0.05, (i, d)
        drops.append(d.y)
    assert max(drops) - min(drops) < TOL, drops


def test_corner_vertex_outward_push_is_folded_onto_the_surface():
    """A cube corner moved straight out along one axis slides along one of the other two edges by that amount
    (the outward move is put back on the surface first)."""
    ob = _grid_cube()
    sel = _select(ob, lambda c: c.x > 0.9 and c.y > 0.9 and c.z > 0.9)
    prep = ec.prepare(bpy.context)[0]
    v = sel[0]
    p = prep.pos[v]
    w = ec.slide_point(p, Vector((0.3, 0.05, 0.0)), prep.normals[v], prep.cands[v], prep.pos, prep.bvh)
    d = w - p
    # put back onto the x = 1 face along the corner's normal, the move points 0.3 down -z and 0.25 down -y:
    # the vertex slides 0.3 down the -z edge
    assert abs(d.x) < TOL and abs(d.y) < TOL and abs(d.z + 0.3) < TOL, d


def test_move_beyond_the_edge_stops_at_its_end():
    ob = _grid_cube()
    sel = _select(ob, lambda c: c.x > 0.9 and c.y > 0.9 and c.z > 0.9)
    prep = ec.prepare(bpy.context)[0]
    v = sel[0]
    p = prep.pos[v]
    w = ec.slide_point(p, Vector((0.0, -5.0, 0.0)), prep.normals[v], prep.cands[v], prep.pos, prep.bvh)
    assert (w - (p + Vector((0, -2, 0)))).length < TOL, w


def test_angle_limit():
    """With the edges toward a selected neighbour and beyond it left out, a move almost along that line stays put:
    the vertex slides when the move is at most 85 degrees off its best edge."""
    ob = _grid_cube(cuts=2)
    sel = _select(ob, lambda c: c.y > 0.9 and abs(c.z) < 0.1 and c.x > -0.1)  # top centre + its +x neighbour
    assert len(sel) == 2
    prep = ec.prepare(bpy.context)[0]
    v = min(sel, key=lambda i: prep.pos[i].x)
    p = prep.pos[v]
    for deg, moves in ((4.9, False), (5.1, True)):
        a = math.radians(deg)
        w = ec.slide_point(p, Vector((0.3 * math.cos(a), 0, 0.3 * math.sin(a))), prep.normals[v], prep.cands[v],
                           prep.pos, prep.bvh)
        assert ((w - p).length > 1e-3) == moves, (deg, w - p)


def test_far_side_edge_left_out_by_topology():
    """A crooked grid cube: with a vertex and one neighbour selected, the edge across the vertex from that neighbour
    is left out too (whatever its direction); with faces selected nothing is left out."""
    ob = _grid_cube(cuts=2, jitter=0.15)
    bm = bmesh.from_edit_mesh(ob.data)
    bm.verts.ensure_lookup_table()
    v = next(x for x in bm.verts if len(x.link_edges) == 4 and len(x.link_faces) == 4)
    u = v.link_edges[0].other_vert(v)
    beside = {w for f in v.link_faces if u in f.verts for w in f.verts}
    far = [e.other_vert(v) for e in v.link_edges if e.other_vert(v) not in beside]
    assert len(far) == 1
    nbs = [e.other_vert(v).index for e in v.link_edges]
    faces = [[x.index for x in f.verts] for f in bm.faces]
    faces_of = [[fi for fi, f in enumerate(faces) if i in f] for i in range(len(bm.verts))]
    cands = ec.candidate_edges(v.index, nbs, faces_of, faces, {v.index, u.index}, False)
    assert u.index not in cands and far[0].index not in cands and len(cands) == 2, cands
    assert ec.candidate_edges(v.index, nbs, faces_of, faces, {v.index, u.index}, True) == nbs


def test_edge_rotate_one_undo_step():
    """allset.edge_rotate: the tilted edge loop sits on its edges, and one undo puts it back (turned about its own
    axis it stays: its own edges are left out)."""
    ob = _grid_cube(cuts=2)
    sel = _select(ob, lambda c: abs(c.y) < 0.1, 'EDGE')
    bpy.ops.ed.undo_push(message="before")
    before = _coords(ob)
    with _override():
        assert 'FINISHED' in bpy.ops.allset.edge_rotate('EXEC_DEFAULT', axis='Y', angle=math.radians(20))
    assert max((a - b).length for a, b in zip(_coords(ob), before)) < TOL
    with _override():
        assert 'FINISHED' in bpy.ops.allset.edge_rotate('EXEC_DEFAULT', axis='Z', angle=math.radians(20))
    after = _coords(ob)
    assert max((a - b).length for a, b in zip(after, before)) > 0.05
    for i in sel:
        assert _on_own_edge(before, after, ob, i), i
    bpy.ops.ed.undo()
    bm = bmesh.from_edit_mesh(bpy.context.object.data)
    assert max((v.co - b).length for v, b in zip(bm.verts, before)) < TOL


def test_keys():
    """Ctrl+Shift+drag on a manipulator handle (Move / Rotate / Scale) and Ctrl+Shift+middle-drag with the Rotate /
    Scale tool start the edge drags; the handle item passes the press on when it doesn't apply."""
    kc = kit.maya_kc()
    found = set()
    for km in kc.keymaps:
        for k in km.keymap_items:
            if k.idname == "allset.manip_mmb_edge" and k.type == 'MIDDLEMOUSE' and k.ctrl and k.shift:
                found.add((km.name, k.properties.mode))
    assert found == {("3D View Tool: Rotate", 'ROTATE'), ("3D View Tool: Scale", 'RESIZE')}, found
    assert "allset.manip_slide" in mp.PASS_THROUGH_FIRST
