"""Connect Tool like Maya (#322): Tool Settings Slide 0.5 / Segments 1 / Pinch 0 with a choice of the value a
middle-drag changes (Segments by default), a middle-drag that re-does the last connection with the new value, and
the rules for the components selected before the tool starts."""

from importlib import import_module

import bmesh
import bpy

import kit

connect_tool = import_module(kit.MODULE + ".operators.connect_tool")
edge_loops = import_module(kit.MODULE + ".operators.edge_loops")


def _grid(n=4):
    """A plane of n x n quads (vertices at whole numbers 0..n), in edit mode with nothing selected."""
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for me in list(bpy.data.meshes):
        bpy.data.meshes.remove(me)
    me = bpy.data.meshes.new("grid")
    bm = bmesh.new()
    vs = {(x, y): bm.verts.new((x, y, 0.0)) for x in range(n + 1) for y in range(n + 1)}
    for x in range(n):
        for y in range(n):
            bm.faces.new((vs[x, y], vs[x + 1, y], vs[x + 1, y + 1], vs[x, y + 1]))
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("grid", me)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    connect_tool.end_path()
    return ob


def _settings():
    return edge_loops.settings(bpy.context)


def _reset():
    s = _settings()
    s.ct_slide, s.ct_segments, s.ct_pinch, s.ct_mode = 0.5, 1, 0.0, 'SEGMENTS'


def _pick(ob, mode, pts):
    """Select the vertices at points ``pts`` ('VERT') or the edges between point pairs ('EDGE')."""
    bpy.context.tool_settings.mesh_select_mode = (mode == 'VERT', mode == 'EDGE', False)
    bm = bmesh.from_edit_mesh(ob.data)

    def at(p):
        return next(v for v in bm.verts if (v.co.x - p[0]) ** 2 + (v.co.y - p[1]) ** 2 < 1e-8)
    for p in pts:
        if mode == 'VERT':
            at(p).select = True
        else:
            a, b = at(p[0]), at(p[1])
            next(e for e in a.link_edges if e.other_vert(a) is b).select = True
    bm.select_flush_mode()
    bmesh.update_edit_mesh(ob.data)


def _counts(ob):
    bm = bmesh.from_edit_mesh(ob.data)
    return len(bm.verts), len(bm.edges), len(bm.faces)


def _enter(ob, mode, pts):
    _reset()
    _pick(ob, mode, pts)
    before = _counts(ob)
    assert bpy.ops.allset.connect_tool_enter() == {'FINISHED'}
    after = _counts(ob)
    return after[0] - before[0], after[1] - before[1]


def test_tool_settings_defaults():
    _grid(1)
    s = _settings()
    props = type(s).bl_rna.properties
    assert props["ct_slide"].default == 0.5 and props["ct_segments"].default == 1
    assert props["ct_pinch"].default == 0.0
    assert props["ct_mode"].default == 'SEGMENTS'
    assert [i.identifier for i in props["ct_mode"].enum_items] == ['SLIDE', 'SEGMENTS', 'PINCH']


def test_one_edge_connects_its_ring():
    ob = _grid(4)
    nv, ne = _enter(ob, 'EDGE', [((1, 0), (1, 1))])       # a vertical edge of the bottom row
    assert nv == 5, (nv, ne)                               # a new loop across the whole row (5 ring edges)


def test_ring_edges_connect_only_between_them():
    ob = _grid(4)
    nv, ne = _enter(ob, 'EDGE', [((1, 0), (1, 1)), ((2, 0), (2, 1)), ((3, 0), (3, 1))])
    assert nv == 3, (nv, ne)


def test_two_edges_at_a_corner_connect_their_middles():
    ob = _grid(4)
    nv, ne = _enter(ob, 'EDGE', [((1, 1), (2, 1)), ((2, 1), (2, 2))])   # bottom and right side of one quad
    assert nv == 2, (nv, ne)


def test_vertex_rules():
    ob = _grid(4)
    assert _enter(ob, 'VERT', [(1, 1), (2, 2)]) == (0, 1)               # a quad's diagonal
    ob = _grid(4)
    assert _enter(ob, 'VERT', [(0, 0), (3, 3)]) == (0, 0)               # no shared face: nothing
    ob = _grid(4)
    assert _enter(ob, 'VERT', [(1, 1), (2, 2), (3, 1)]) == (0, 2)       # across two neighbouring quads


def _drag(dx, mode=None, ctrl=False):
    """A middle-drag of ``dx`` pixels to the right (negative = left), released at the end."""
    if mode is not None:
        _settings().ct_mode = mode
    return connect_tool.drag_value(_settings(), dx, connect_tool.drag_start(_settings()))


def test_drag_rule():
    _grid(1)
    _reset()
    s = _settings()
    start = connect_tool.drag_start(s)
    assert connect_tool.drag_value(s, 0, start) == 1
    assert connect_tool.drag_value(s, 2, start) == 1, "a tiny jitter changes nothing"
    assert connect_tool.drag_value(s, 10, start) == 2, "a short drag to the right adds one"
    assert connect_tool.drag_value(s, 60, start) == 3
    assert connect_tool.drag_value(s, 90, start) == 4
    assert connect_tool.drag_value(s, -60, start) == 1, "never below one segment"
    s.ct_mode = 'SLIDE'
    start = connect_tool.drag_start(s)
    assert abs(connect_tool.drag_value(s, 40, start) - 0.7) < 1e-6
    assert connect_tool.drag_value(s, 1000, start) == 1.0 and connect_tool.drag_value(s, -1000, start) == 0.0
    s.ct_mode = 'PINCH'
    start = connect_tool.drag_start(s)
    assert abs(connect_tool.drag_value(s, 40, start) - 20.0) < 1e-6
    assert connect_tool.hud_text(s) == "Connect Pinch: 0"
    s.ct_mode, s.ct_segments = 'SEGMENTS', 3
    assert connect_tool.hud_text(s) == "Connect Segments: 3"
    s.ct_mode = 'SLIDE'
    assert connect_tool.hud_text(s) == "Connect Slide: 0.5"


def test_redo_last_connection_with_more_segments():
    """Entering with one edge selected makes a loop across its ring; more Segments re-do it as more loops, Slide
    moves them, and the path end (Enter) makes the connection final."""
    ob = _grid(4)
    _enter(ob, 'EDGE', [((1, 0), (1, 1))])
    base = _counts(ob)
    s = _settings()
    s.ct_segments = 3
    assert connect_tool.redo_last(bpy.context)
    v, e, f = _counts(ob)
    assert v - (base[0] - 5) == 15, (v, base)          # three loops of five new vertices from the original grid
    s.ct_segments = 1
    s.ct_slide = 0.25
    assert connect_tool.redo_last(bpy.context)
    assert _counts(ob) == base
    bm = bmesh.from_edit_mesh(ob.data)
    ys = sorted({round(v.co.y, 4) for v in bm.verts if 0.9 < v.co.x < 2.1 and 0 < v.co.y < 1})
    assert ys == [0.25] or ys == [0.75], ys
    assert bpy.ops.allset.connect_end() == {'FINISHED'}
    assert not connect_tool.redo_last(bpy.context), "after Enter the connection stays as it is"


def test_redo_click_connection():
    """Two edges clicked on one face, then Segments 2: two edges between them."""
    ob = _grid(1)
    _reset()
    bm = bmesh.from_edit_mesh(ob.data)
    left = next(e for e in bm.edges if all(abs(v.co.x) < 1e-6 for v in e.verts)).index
    right = next(e for e in bm.edges if all(abs(v.co.x - 1) < 1e-6 for v in e.verts)).index
    bpy.ops.allset.connect_click(object=ob.name, kind='EDGE', index=left)
    bpy.ops.allset.connect_click(object=ob.name, kind='EDGE', index=right)
    assert _counts(ob) == (6, 7, 2)
    _settings().ct_segments = 2
    assert connect_tool.redo_last(bpy.context)
    assert _counts(ob) == (8, 10, 3), _counts(ob)


def test_pinch_moves_segments_together():
    ob = _grid(1)
    _reset()
    s = _settings()
    s.ct_segments, s.ct_pinch = 3, 0.0
    _pick(ob, 'EDGE', [((0, 0), (0, 1)), ((1, 0), (1, 1))])
    assert bpy.ops.allset.connect_tool_enter() == {'FINISHED'}

    def spread():
        bm = bmesh.from_edit_mesh(ob.data)
        ys = sorted(v.co.y for v in bm.verts if abs(v.co.x) < 1e-6 and 0 < v.co.y < 1)
        return ys[-1] - ys[0]
    flat = spread()
    s.ct_pinch = 50.0
    assert connect_tool.redo_last(bpy.context)
    assert spread() < flat - 1e-3, (spread(), flat)
    s.ct_pinch = -50.0
    assert connect_tool.redo_last(bpy.context)
    assert spread() > flat + 1e-3, (spread(), flat)


def test_drag_keys_in_the_tool():
    ui = import_module(kit.MODULE + ".ui.mesh_tools_loop")
    keys = [(k[0], k[1]["type"], k[1].get("ctrl", False)) for k in ui.ALLSET_TL_connect.bl_keymap]
    assert ("allset.connect_drag", 'MIDDLEMOUSE', False) in keys
    assert ("allset.connect_drag", 'MIDDLEMOUSE', True) in keys
