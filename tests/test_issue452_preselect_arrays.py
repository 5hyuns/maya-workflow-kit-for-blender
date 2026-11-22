"""Pre-selection highlight in Edit Mode on a dense mesh (#452): the arrays it reads again after an edit (points,
edges, hidden flags, faces and their corners) come in block copies, so the first hover after a move or a click
doesn't stall; the arrays are the same as reading every BMesh element one by one."""

import time
from importlib import import_module

import bmesh
import bpy
import numpy as np

import kit

pre = import_module(kit.MODULE + ".operators.preselect")


def _edit_mesh(segments, rings):
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings)
    bpy.ops.object.mode_set(mode='EDIT')
    return bmesh.from_edit_mesh(bpy.context.active_object.data)


def _by_element(bm):
    bm.verts.index_update()
    bm.edges.index_update()
    co = np.array([v.co[:] for v in bm.verts], np.float64)
    edges = np.array([(e.verts[0].index, e.verts[1].index) for e in bm.edges], np.int64)
    vok = np.array([not v.hide for v in bm.verts])
    eok = np.array([not e.hide for e in bm.edges])
    counts = np.zeros(len(bm.edges), np.int64)
    for f in bm.faces:
        for e in f.edges:
            counts[e.index] += 1
    shown = np.array([not f.hide for f in bm.faces])
    faces = {f.index: [v.index for v in f.verts] for f in bm.faces}
    return co, edges, vok, eok, counts, shown, faces


def test_arrays_match_the_bmesh():
    bm = _edit_mesh(24, 12)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    bmesh.ops.dissolve_edges(bm, edges=[bm.faces[30].edges[0]])     # an n-gon among quads and triangles
    bm.faces.ensure_lookup_table()
    bm.verts.ensure_lookup_table()
    bm.verts[5].hide_set(True)
    bm.faces[40].hide_set(True)
    bmesh.update_edit_mesh(bpy.context.active_object.data)
    co, edges, vok, eok, counts, border, shown, groups = pre.mesh_arrays(bm)
    r_co, r_edges, r_vok, r_eok, r_counts, r_shown, r_faces = _by_element(bm)
    if not np.allclose(co, r_co, atol=1e-6) or co.dtype != np.float64:
        raise AssertionError("points differ from the BMesh")
    if not np.array_equal(edges, r_edges):
        raise AssertionError("edges differ from the BMesh")
    if not (np.array_equal(vok, r_vok) and np.array_equal(eok, r_eok) and np.array_equal(shown, r_shown)):
        raise AssertionError(f"hidden flags differ: {(~vok).sum()} / {(~r_vok).sum()} points, "
                             f"{(~shown).sum()} / {(~r_shown).sum()} faces")
    if vok.all() or shown.all():
        raise AssertionError("the hidden point is missing")
    if not np.array_equal(counts, r_counts):
        raise AssertionError("faces per edge differ")
    got = {}
    for idx, corners in groups:
        for i, row in zip(idx.tolist(), corners.tolist()):
            got[i] = row
    if got != r_faces:
        raise AssertionError(f"face corners differ ({len(got)} / {len(r_faces)} faces)")
    sizes = {len(v) for v in got.values()}
    if not {3, 4} <= sizes or max(sizes) < 5:
        raise AssertionError(f"the mesh should hold triangles, quads and an n-gon: {sorted(sizes)}")


def test_dense_mesh_reads_quickly():
    bm = _edit_mesh(512, 256)             # 130k points
    pre.mesh_arrays(bm)
    best = min(_timed(bm) for _ in range(3))
    # reading element properties one by one took about a quarter of a second here
    if best > 0.12:
        raise AssertionError(f"reading a 130k point edit mesh took {best * 1000:.0f} ms")


def _timed(bm):
    t = time.perf_counter()
    pre.mesh_arrays(bm)
    return time.perf_counter() - t
