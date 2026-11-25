"""UV Editor commands change only the UVs of the selection, like Maya.

With UV Sync Selection a selected face takes its own corner UVs, a selected edge the UVs at its ends on the faces
beside it and a selected vertex every UV on it; shells of other faces that only share a vertex stay where they are
(Flip, Normalize, Snap and Stack, Optimize, Orient Shells to Edges). Without UV Sync Selection a selected UV edge
belongs to its own face. Cut UV Edges on edges that already separate two shells moves nothing. With two meshes in
UV editing, the mesh with nothing selected stays as it is."""

import bmesh
import bpy

import kit
from importlib import import_module

compat = import_module(kit.MODULE + ".compat")

TOP, BOTTOM = 4, 5


def _cube(name="c", off=0.0):
    """A cube whose six faces are six separate UV shells, each a slightly uneven square in its own spot."""
    v = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0), (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]
    faces = [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (4, 5, 6, 7), (3, 2, 1, 0)]
    me = bpy.data.meshes.new(name)
    me.from_pydata([(x + off, y, z) for x, y, z in v], [], faces)
    me.uv_layers.new(name="UVMap")
    bm = bmesh.new()
    bm.from_mesh(me)
    uv = bm.loops.layers.uv.active
    for f in bm.faces:
        for k, (lp, (x, y)) in enumerate(zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1)))):
            lp[uv].uv = (0.05 + 0.15 * f.index + 0.1 * x + 0.01 * k * (f.index % 2), 0.4 + 0.1 * y + 0.007 * k)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    ob.select_set(True)
    return ob


def _scene(count=1):
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    obs = [_cube(f"c{i}", 3.0 * i) for i in range(count)]
    bpy.context.view_layer.objects.active = obs[0]
    bpy.ops.object.mode_set(mode='EDIT')
    return obs


def _edge(bm, a, b):
    bm.edges.ensure_lookup_table()
    return next(e for e in bm.edges if {v.index for v in e.verts} == {a, b})


def _select_mesh(ob, mode, faces=(), edges=(), verts=()):
    """UV Sync Selection on: the mesh selection."""
    ts = bpy.context.scene.tool_settings
    ts.use_uv_select_sync = True
    ts.mesh_select_mode = (mode == 'VERT', mode == 'EDGE', mode == 'FACE')
    bm = bmesh.from_edit_mesh(ob.data)
    for seq in (bm.verts, bm.edges, bm.faces):
        seq.ensure_lookup_table()
        for el in seq:
            el.select = False
    for i in faces:
        bm.faces[i].select_set(True)
    for a, b in edges:
        _edge(bm, a, b).select_set(True)
    for i in verts:
        bm.verts[i].select_set(True)
    bm.select_mode = {mode}
    bm.select_flush_mode()
    compat.uv_sync_from_mesh(bm)
    bmesh.update_edit_mesh(ob.data)


def _select_uv(ob, faces=(), face_edges=()):
    """UV Sync Selection off: whole faces' UVs, or the UV edge (face, vertex a, vertex b) of one face."""
    ts = bpy.context.scene.tool_settings
    ts.use_uv_select_sync = False
    ts.mesh_select_mode = (False, False, True)
    compat.set_uv_island_mode(ts, False)
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.active
    for f in bm.faces:
        f.select = True
        compat.set_uv_face_selected(f, uv, f.index in faces)
        for lp in f.loops:
            if any(f.index == fi and {lp.vert.index, lp.link_loop_next.vert.index} == {a, b}
                   for fi, a, b in face_edges):
                compat.set_uv_edge_selected(lp, uv, True)
                compat.set_uv_vert_selected(lp, uv, True)
                compat.set_uv_vert_selected(lp.link_loop_next, uv, True)
    bmesh.update_edit_mesh(ob.data)


def _uvs(obs):
    out = {}
    for ob in obs:
        bm = bmesh.from_edit_mesh(ob.data)
        uv = bm.loops.layers.uv.active
        bm.faces.ensure_lookup_table()
        out.update({(ob.name, f.index): [tuple(round(c, 6) for c in lp[uv].uv) for lp in f.loops]
                    for f in bm.faces})
    return out


def _run(op, **props):
    scr = bpy.context.window.screen
    a = next(a for a in scr.areas if a.type in ('VIEW_3D', 'IMAGE_EDITOR'))
    a.ui_type = 'UV'
    r = next(r for r in a.regions if r.type == 'WINDOW')
    with bpy.context.temp_override(area=a, region=r, space_data=a.spaces.active):
        res = getattr(bpy.ops.allset, op)(**props)
    assert res == {'FINISHED'}, (op, res)


def _changed(obs, op, **props):
    before = _uvs(obs)
    _run(op, **props)
    after = _uvs(obs)
    return {k[1] if len(obs) == 1 else k for k in before if before[k] != after[k]}


def test_flip_edge_takes_the_faces_beside_it():
    ob, = _scene()
    _select_mesh(ob, 'EDGE', edges=((1, 5),))           # between sides 0 and 1; top and bottom share its ends
    assert _changed([ob], "uv_flip") == {0, 1}


def test_flip_vertex_takes_every_uv_on_it():
    ob, = _scene()
    _select_mesh(ob, 'VERT', verts=(5,))
    assert _changed([ob], "uv_flip") == {0, 1, TOP}


def test_normalize_edge_takes_the_shells_beside_it():
    ob, = _scene()
    _select_mesh(ob, 'EDGE', edges=((1, 5),))
    assert _changed([ob], "uv_normalize") <= {0, 1}


def test_snap_stack_and_optimize_face_leave_other_shells():
    for op in ("uv_snap_stack", "uv_optimize"):
        ob, = _scene()
        _select_mesh(ob, 'FACE', faces=(1,))
        moved = _changed([ob], op)
        assert moved <= {1}, (op, moved)


def test_orient_edges_face_turns_only_its_own_shell():
    ob, = _scene()
    _select_mesh(ob, 'FACE', faces=(1,))
    assert _changed([ob], "uv_orient_edges") == {1}
    ob, = _scene()
    _select_uv(ob, faces=(1,))
    assert _changed([ob], "uv_orient_edges") == {1}


def test_cut_on_separate_shells_moves_nothing():
    ob, = _scene()
    _select_mesh(ob, 'FACE', faces=(1,))                # every edge of the face already separates two shells
    bpy.context.scene.tool_settings.mesh_select_mode = (False, True, False)
    assert _changed([ob], "uv_cut") == set()


def test_cut_still_splits_a_joined_edge():
    ob, = _scene()
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.active
    bm.faces.ensure_lookup_table()
    bm.verts.ensure_lookup_table()
    f0, f1 = bm.faces[0], bm.faces[1]
    for v in (bm.verts[1], bm.verts[5]):                  # join sides 0 and 1 along edge 1-5
        p = next(lp for lp in f0.loops if lp.vert is v)[uv].uv.copy()
        next(lp for lp in f1.loops if lp.vert is v)[uv].uv = p
    bmesh.update_edit_mesh(ob.data)
    _select_mesh(ob, 'EDGE', edges=((1, 5),))
    moved = _changed([ob], "uv_cut")
    assert len(moved) == 1 and moved <= {0, 1}, moved


def test_second_mesh_without_selection_stays():
    for select in ("mesh", "uv"):
        obs = _scene(2)
        if select == "mesh":
            _select_mesh(obs[0], 'FACE', faces=(1,))
            _select_mesh(obs[1], 'FACE')
        else:
            _select_uv(obs[0], faces=(1,))
            _select_uv(obs[1])
        for op, props in (("uv_flip", {}), ("uv_normalize", {}), ("uv_optimize", {}), ("uv_snap_stack", {}),
                          ("uv_orient_edges", {}), ("uv_nudge", {"direction": 'UP'})):
            moved = _changed(obs, op, **props)
            assert {k[0] for k in moved} <= {"c0"}, (select, op, moved)
