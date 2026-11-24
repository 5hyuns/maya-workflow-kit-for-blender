"""#540: with UV Sync Selection the UV Toolkit's Move / Rotate / Scale buttons move only the UVs of the selection.
A selected face takes its own corner UVs, not the UVs of other shells that share its vertices; a selected edge takes
the UVs at its ends on the faces beside it; a selected vertex takes every UV on it."""

from importlib import import_module

import bmesh
import bpy

import kit

uvx = import_module(kit.MODULE + ".operators.uv_transform")

SIDES = (0, 1, 2, 3)          # cube faces built below: four sides, then top and bottom
TOP, BOTTOM = 4, 5


def _cube():
    """A cube whose six faces are six separate UV shells (each face its own square in UV space)."""
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    v = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0), (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]
    faces = [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (4, 5, 6, 7), (3, 2, 1, 0)]
    me = bpy.data.meshes.new("c")
    me.from_pydata(v, [], faces)
    me.uv_layers.new(name="UVMap")
    ob = bpy.data.objects.new("c", me)
    bpy.context.collection.objects.link(ob)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.scene.tool_settings.use_uv_select_sync = True
    bm = bmesh.from_edit_mesh(me)
    uv = bm.loops.layers.uv.active
    corners = ((0, 0), (1, 0), (1, 1), (0, 1))
    for f in bm.faces:
        for lp, (x, y) in zip(f.loops, corners):
            lp[uv].uv = (0.05 + 0.15 * f.index + 0.1 * x, 0.4 + 0.1 * y)
    bmesh.update_edit_mesh(me)
    return ob


def _select(ob, mode, faces=(), edges=(), verts=()):
    ts = bpy.context.scene.tool_settings
    ts.mesh_select_mode = (mode == 'VERT', mode == 'EDGE', mode == 'FACE')
    bm = bmesh.from_edit_mesh(ob.data)
    for seq in (bm.verts, bm.edges, bm.faces):
        seq.ensure_lookup_table()
        for el in seq:
            el.select = False
    for i in faces:
        bm.faces[i].select_set(True)
    for e in edges:
        bm.edges[e].select_set(True)
    for i in verts:
        bm.verts[i].select_set(True)
    bm.select_mode = {mode}
    bm.select_flush_mode()
    bmesh.update_edit_mesh(ob.data)


def _uvs(ob):
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.active
    bm.faces.ensure_lookup_table()
    return {f.index: [tuple(round(c, 6) for c in lp[uv].uv) for lp in f.loops] for f in bm.faces}


def _run(op, **props):
    scr = bpy.context.window.screen
    a = next(a for a in scr.areas if a.type in ('VIEW_3D', 'IMAGE_EDITOR'))
    a.ui_type = 'UV'
    r = next(r for r in a.regions if r.type == 'WINDOW')
    with bpy.context.temp_override(area=a, region=r):
        res = getattr(bpy.ops.allset, op)(**props)
    assert res == {'FINISHED'}, (op, res)


def _moved(before, after):
    return {i for i in before if before[i] != after[i]}


def test_face_selection_rotates_only_its_faces():
    ob = _cube()
    _select(ob, 'FACE', faces=SIDES)
    before = _uvs(ob)
    _run("uv_rotate_step", clockwise=True)
    after = _uvs(ob)
    assert before[TOP] == after[TOP] and before[BOTTOM] == after[BOTTOM], (before[TOP], after[TOP])
    assert _moved(before, after) == set(SIDES), _moved(before, after)


def test_face_selection_nudge_and_scale_leave_other_shells():
    for op, props in (("uv_nudge", {"direction": 'UP'}), ("uv_scale_step", {})):
        ob = _cube()
        _select(ob, 'FACE', faces=(1,))
        before = _uvs(ob)
        _run(op, **props)
        assert _moved(before, _uvs(ob)) == {1}, (op, _moved(before, _uvs(ob)))


def test_edge_selection_takes_the_faces_beside_it():
    ob = _cube()
    bm = bmesh.from_edit_mesh(ob.data)
    bm.edges.ensure_lookup_table()
    edge = next(e.index for e in bm.edges if {v.index for v in e.verts} == {1, 5})   # between sides 0 and 1
    _select(ob, 'EDGE', edges=(edge,))
    before = _uvs(ob)
    _run("uv_nudge", direction='UP')
    after = _uvs(ob)
    assert _moved(before, after) == {0, 1}, _moved(before, after)     # not top / bottom at vertices 1 and 5
    for i in (0, 1):
        changed = sum(b != a for b, a in zip(before[i], after[i]))
        assert changed == 2, (i, changed)                             # only the edge's two corners


def test_vertex_selection_takes_every_uv_on_it():
    ob = _cube()
    _select(ob, 'VERT', verts=(5,))       # corner of sides 0 and 1 and the top
    before = _uvs(ob)
    _run("uv_nudge", direction='UP')
    assert _moved(before, _uvs(ob)) == {0, 1, TOP}, _moved(before, _uvs(ob))


def test_picked_follows_the_face_selection():
    ob = _cube()
    _select(ob, 'FACE', faces=SIDES)
    found = uvx.picked(bpy.context)
    loops = found[0][3]
    assert {lp.face.index for lp in loops} == set(SIDES), sorted({lp.face.index for lp in loops})
