"""Maya's component colours in Edit Mode stay light on big meshes: a click (a selection-only change) reads only the
selection flags the select mode draws, the mesh's points, edges and faces are kept; a geometry change reads the
mesh again. What is drawn is the same as reading the whole edit mesh after every change."""

from importlib import import_module

import bmesh
import bpy
import numpy as np
from mathutils import Matrix

import kit

cc = import_module(kit.MODULE + ".ui.component_colors")


class _Count:
    def __init__(self, owner, name):
        self.owner, self.name, self.calls = owner, name, 0
        self.real = getattr(owner, name)

    def __enter__(self):
        def counted(*a, **k):
            self.calls += 1
            return self.real(*a, **k)
        setattr(self.owner, self.name, counted)
        return self

    def __exit__(self, *exc):
        setattr(self.owner, self.name, self.real)


def _object_mode():
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')


def _clear():
    _object_mode()
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for me in list(bpy.data.meshes):
        bpy.data.meshes.remove(me)
    for cached in (cc._cache, cc._dirty, getattr(cc, "_dirty_sel", set()), cc._selection_snapshot):
        cached.clear()


def _grid(n=30, select='VERT'):
    _clear()
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=n, y_subdivisions=n, size=4)
    ob = bpy.context.object
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type=select)
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.context.view_layer.update()
    return ob


def _mixed():
    """Quads, an ngon, triangles, a loose edge and a loose vertex, in edit mode."""
    _clear()
    me = bpy.data.meshes.new("mixed")
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=6, y_segments=5, size=2.0)
    bmesh.ops.create_circle(bm, cap_ends=True, segments=7, radius=0.6, matrix=Matrix.Translation((3.5, 0, 0)))
    bmesh.ops.create_cone(bm, cap_ends=True, segments=5, radius1=0.5, radius2=0.0, depth=1.0,
                          matrix=Matrix.Translation((0, 3.5, 0)))
    a = bm.verts.new((5, 5, 0))
    b = bm.verts.new((6, 5, 0))
    bm.edges.new((a, b))
    bm.verts.new((7, 7, 1))
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("mixed", me)
    bpy.context.scene.collection.objects.link(ob)
    for o in bpy.context.scene.objects:
        o.select_set(o is ob)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT')
    return ob


def _same_as_full_read(ob, select_mode):
    """The cached arrays draw exactly what a full BMesh read draws: the same points, the same index layers."""
    dg = bpy.context.view_layer.depsgraph
    st = cc.state(ob, dg, select_mode[2], False, select_mode)
    assert st is not None
    full = cc.read_bmesh(bmesh.from_edit_mesh(ob.data))
    assert np.array_equal(st.arrays.co, full.co)
    want, got = cc.layers(full, select_mode), cc.layers(st.arrays, select_mode)
    assert set(got) == set(want), (set(got), set(want))
    for k in want:
        assert np.array_equal(want[k], got[k]), (k, select_mode)
    cc._dirty.difference_update((ob.name, ob.data.name))
    cc._dirty_sel.difference_update((ob.name, ob.data.name))
    return st


def test_click_reads_no_mesh():
    """A selection-only change (what a click or a box select sends) reads no mesh: no full BMesh read, no evaluated
    mesh copy, no membership pass over every element. (Before, every click read the whole edit mesh in Python.)"""
    ob = _grid(30)
    dg = bpy.context.view_layer.depsgraph
    st = cc.state(ob, dg, False, False)
    assert st is not None
    cc._dirty.clear()
    getattr(cc, "_dirty_sel", set()).clear()
    for step in range(3):
        bpy.ops.mesh.select_random(ratio=0.2, seed=step + 1)       # a selection-only depsgraph update
        bpy.context.view_layer.update()
        with _Count(cc, "read_bmesh") as rb, _Count(cc, "read_evaluated") as ev, \
                _Count(cc, "_selection_signature") as sig:
            st = cc.state(ob, dg, False, False)
        assert rb.calls == 0 and ev.calls == 0, "the points, edges and faces are kept"
        assert sig.calls == 0, "no membership pass over every element"
        bm = bmesh.from_edit_mesh(ob.data)
        assert st.arrays.vsel.tolist() == [v.select for v in bm.verts]
        assert st.arrays.esel.tolist() == [e.select for e in bm.edges]
        for names in (cc._dirty, getattr(cc, "_dirty_sel", set())):       # what a draw does after reading
            names.difference_update((ob.name, ob.data.name))
    _object_mode()


def test_selection_change_reads_only_the_drawn_flags():
    """Vertex select mode draws vertices: a selection change (here a box-like one, nothing in the selection history)
    reads only the vertices' select flags (not the edges', which are twice as many); switching to edge select mode
    reads the edges' then."""
    ob = _grid(30)
    dg = bpy.context.view_layer.depsgraph
    vert = (True, False, False)
    cc.state(ob, dg, False, False, vert)
    bpy.ops.mesh.select_random(ratio=0.3, seed=4)
    bpy.context.view_layer.update()
    seen = []
    real = cc._flags

    def counted(seq):
        seen.append(type(seq).__name__)
        return real(seq)
    cc._flags = counted
    try:
        st = cc.state(ob, dg, False, False, vert)
        assert seen == ["BMVertSeq"], seen
        cc._dirty_sel.clear()
        seen.clear()
        st = cc.state(ob, dg, False, False, (False, True, False))   # no update: the edge flags weren't read yet
        assert seen == ["BMEdgeSeq"], seen
    finally:
        cc._flags = real
    bm = bmesh.from_edit_mesh(ob.data)
    assert st.arrays.esel.tolist() == [e.select for e in bm.edges]
    _object_mode()


def test_geometry_change_reads_the_mesh_again():
    ob = _grid(12)
    dg = bpy.context.view_layer.depsgraph
    cc.state(ob, dg, False, False, (True, False, False))
    bpy.ops.mesh.select_random(ratio=0.3, seed=2)
    bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate={"value": (0, 0, 0.5)})
    bpy.context.view_layer.update()
    assert ob.data.name in cc._dirty or ob.name in cc._dirty
    with _Count(cc, "_read") as rd:
        st = cc.state(ob, dg, False, False, (True, False, False))
    assert rd.calls == 1
    assert len(st.arrays.co) == len(bmesh.from_edit_mesh(ob.data).verts)
    _object_mode()


def test_drawn_layers_match_a_full_read():
    """Through clicks, select modes, hide / reveal, an extrude and a delete the cached arrays draw what a full read
    of the edit mesh draws (points, every edge, vertices, selected vertices / edges, the face stipple)."""
    ob = _mixed()
    modes = [(True, False, False), (False, True, False), (False, False, True), (True, True, False)]
    steps = [
        lambda: bpy.ops.mesh.select_random(ratio=0.3, seed=1),
        lambda: bpy.ops.mesh.select_more(),
        lambda: bpy.ops.mesh.select_less(),
        lambda: bpy.ops.mesh.select_all(action='INVERT'),
        lambda: bpy.ops.mesh.hide(unselected=False),
        lambda: bpy.ops.mesh.select_random(ratio=0.5, seed=7),
        lambda: bpy.ops.mesh.reveal(select=False),
        lambda: bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate={"value": (0, 0, 0.3)}),
        lambda: bpy.ops.mesh.select_random(ratio=0.4, seed=3),
        lambda: bpy.ops.mesh.delete(type='FACE'),
        lambda: bpy.ops.mesh.select_all(action='SELECT'),
        lambda: bpy.ops.mesh.select_all(action='DESELECT'),
    ]
    for i, step in enumerate(steps):
        mode = modes[i % len(modes)]
        bpy.context.tool_settings.mesh_select_mode = mode
        step()
        bpy.context.view_layer.update()
        _same_as_full_read(ob, mode)
        for other in modes:                         # the select mode switched with no update
            _same_as_full_read(ob, other)
    _object_mode()


def test_poll_compares_counts_in_constant_time():
    """Outside the UV component the selection poll compares element and selection counts (the BMesh keeps the
    selected totals up to date, no update needed); it doesn't walk every element."""
    ob = _grid(20)
    me = ob.data
    bm = bmesh.from_edit_mesh(me)
    before = cc.counts_signature(me, bm)
    bm.verts.ensure_lookup_table()
    bm.verts[5].select_set(True)                    # no depsgraph update
    after = cc.counts_signature(me, bm)
    assert after != before and after[3] == before[3] + 1
    _object_mode()


def _click(ob, kind, i, extend=False, deselect=False, keep_history=False):
    """What a click does to the edit mesh: a plain click clears the selection and picks one element (it goes into
    the selection history); Shift adds one; Ctrl removes one. Then the selection-only update a click sends."""
    if not (extend or deselect):
        bpy.ops.mesh.select_all(action='DESELECT')          # clears the selection history too
    bm = bmesh.from_edit_mesh(ob.data)
    seq = {"v": bm.verts, "e": bm.edges, "f": bm.faces}[kind]
    seq.ensure_lookup_table()
    ele = seq[i]
    ele.select_set(not deselect)
    if deselect:
        if not keep_history:
            bm.select_history.remove(ele)
    else:
        bm.select_history.add(ele)
    bm.select_flush_mode()
    cc._dirty_sel.add(ob.name)                              # what the depsgraph handler marks for a click


def test_click_takes_the_picked_element_from_the_selection_history():
    """A click (plain, Shift, Ctrl, in vertex / edge / face select mode) leaves the picked elements in the selection
    history: they are the selection, so no element is walked; the drawn layers are what a full read draws. A
    selection the history doesn't hold (a box select) walks the elements once and is drawn the same."""
    ob = _grid(40)
    vert, edge, face = (True, False, False), (False, True, False), (False, False, True)
    clicks = [
        (vert, dict(kind="v", i=37)),
        (vert, dict(kind="v", i=500)),
        (vert, dict(kind="v", i=501, extend=True)),
        (vert, dict(kind="v", i=900, extend=True)),
        (vert, dict(kind="v", i=501, deselect=True)),
        (vert, dict(kind="v", i=900, deselect=True, keep_history=True)),   # a stale history entry
        (edge, dict(kind="e", i=100)),
        (edge, dict(kind="e", i=101, extend=True)),
        (face, dict(kind="f", i=300)),
        (face, dict(kind="f", i=301, extend=True)),
        (face, dict(kind="f", i=300, deselect=True)),
    ]
    for mode, click in clicks:
        bpy.context.tool_settings.mesh_select_mode = mode
        bpy.context.view_layer.update()
        _same_as_full_read(ob, mode)
        _click(ob, **click)
        with _Count(cc, "_flags") as walk, _Count(cc, "_read") as rd:
            cc.state(ob, bpy.context.view_layer.depsgraph, mode[2], False, mode)
        _same_as_full_read(ob, mode)
        assert rd.calls == 0, click
        assert walk.calls == 0, ("the picked elements are the selection", click)
    bpy.context.tool_settings.mesh_select_mode = vert
    bpy.ops.mesh.select_random(ratio=0.2, seed=9)            # nothing in the history
    bpy.context.view_layer.update()
    with _Count(cc, "_flags") as walk:
        cc.state(ob, bpy.context.view_layer.depsgraph, False, False, vert)
    _same_as_full_read(ob, vert)
    assert walk.calls == 1
    _click(ob, "v", 1200, extend=True)                      # history: one of many selected
    with _Count(cc, "_flags") as walk:
        cc.state(ob, bpy.context.view_layer.depsgraph, False, False, vert)
    _same_as_full_read(ob, vert)
    assert walk.calls == 1
    _object_mode()
