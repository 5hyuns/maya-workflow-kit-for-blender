"""Hypergraph: Hierarchy window (ui/hypergraph.py, ui/hypergraph_layout.py): tree layout, view maths, Maya
selection rules, MMB-drop parenting, menu wiring and keymap items."""

from importlib import import_module

import bpy

import kit

hl = import_module(kit.MODULE + ".ui.hypergraph_layout")
hg = import_module(kit.MODULE + ".ui.hypergraph")
marked_window = import_module(kit.MODULE + ".ui.marked_window")
menu_map = import_module(kit.MODULE + ".ui.menu_map")
notices = import_module(kit.MODULE + ".ui.notices")
panel_menu_data = import_module(kit.MODULE + ".ui.panel_menu_data")


# --- pure layout ------------------------------------------------------------------------------------------------

def test_layout_parent_centred_over_children():
    nodes = [("g", None), ("a", "g"), ("b", "g"), ("c", None), ("a1", "a")]
    pos = hl.layout(nodes)
    pitch_x, pitch_y = hl.NODE_W + hl.GAP_X, hl.NODE_H + hl.GAP_Y
    assert pos["a1"] == (0.0, 2 * pitch_y)
    assert pos["a"] == (0.0, pitch_y)            # a parent with one child stands over it
    assert pos["b"] == (pitch_x, pitch_y)
    assert pos["g"] == (pitch_x / 2, 0.0)        # centred over a and b
    assert pos["c"] == (2 * pitch_x, 0.0)        # the next root to the right of the whole first tree


def test_collapsed_hides_subtree():
    nodes = [("g", None), ("a", "g"), ("b", "g"), ("a1", "a")]
    pos = hl.layout(nodes, collapsed={"g"})
    assert set(pos) == {"g"}
    assert hl.hidden_children(nodes, {"g", "b"}) == {"g"}     # b has no children: no mark
    pos = hl.layout(nodes, collapsed={"a"})
    assert "a1" not in pos and {"g", "a", "b"} <= set(pos)


def test_layout_survives_unknown_parent_and_cycles():
    pos = hl.layout([("x", "missing"), ("y", "y")])
    assert set(pos) == {"x", "y"}
    assert pos["x"][1] == pos["y"][1] == 0.0


def test_view_roundtrip_frame_and_zoom():
    v = hl.View(scale=1.25)
    v.frame((0.0, 0.0, 400.0, 100.0), 800, 600, top=30)
    for g in ((0.0, 0.0), (400.0, 100.0), (123.0, 45.0)):
        r = v.to_region(*g)
        back = v.to_graph(*r)
        assert abs(back[0] - g[0]) < 1e-6 and abs(back[1] - g[1]) < 1e-6
    x0, y0 = v.to_region(0.0, 0.0)
    x1, y1 = v.to_region(400.0, 100.0)
    assert 0 < x0 < x1 < 800 and 0 < y1 < y0 < 570         # inside, below the strip, y flips
    assert abs((x0 + x1) / 2 - 400) < 1e-6
    before = v.to_graph(300, 200)
    v.zoom_at(1.7, 300, 200)
    after = v.to_graph(300, 200)
    assert abs(before[0] - after[0]) < 1e-6 and abs(before[1] - after[1]) < 1e-6
    z = v.zoom
    v.zoom_at(1e6, 0, 0)
    assert v.zoom == hl.ZOOM_MAX and z < hl.ZOOM_MAX


def test_hit_and_box():
    v = hl.View()
    cents = {"a": (0.0, 0.0), "b": (200.0, 0.0)}
    v.ox, v.oy = 100.0, 300.0
    assert hl.hit(v, cents, 100, 300) == "a"
    assert hl.hit(v, cents, 300, 300) == "b"
    assert hl.hit(v, cents, 200, 300) is None
    assert hl.in_box(v, cents, (90, 290), (110, 310)) == ["a"]
    assert sorted(hl.in_box(v, cents, (0, 0), (400, 400))) == ["a", "b"]


def test_selection_rules():
    assert hl.select_rule(False, False) == 'REPLACE'
    assert hl.select_rule(True, False) == 'TOGGLE'
    assert hl.select_rule(False, True) == 'REMOVE'
    assert hl.select_rule(True, True) == 'ADD'
    cur = {"a", "b"}
    assert hl.apply_rule(cur, ["c"], 'REPLACE') == {"c"}
    assert hl.apply_rule(cur, ["b", "c"], 'TOGGLE') == {"a", "c"}
    assert hl.apply_rule(cur, ["b", "c"], 'REMOVE') == {"a"}
    assert hl.apply_rule(cur, ["c"], 'ADD') == {"a", "b", "c"}


def test_icons_differ_by_kind():
    kinds = ('GROUP', 'MESH', 'CURVE', 'SURFACE', 'JOINT', 'CAMERA', 'LIGHT', 'LOCATOR', 'LATTICE', 'OTHER')
    shapes = [repr(hl.icon_shapes(k)) for k in kinds]
    assert len(set(shapes)) == len(kinds)
    assert hl.node_kind('EMPTY') == 'GROUP' and hl.node_kind('EMPTY', True) == 'LOCATOR'
    assert hl.node_kind('ARMATURE') == 'JOINT'


def test_strip_rects():
    rects = hl.strip_rects([50, 70], top=100, height=20, x0=5, gap=4)
    assert rects == [(5, 80, 55, 100), (59, 80, 129, 100)]


# --- scene ------------------------------------------------------------------------------------------------------

def _scene():
    bpy.ops.wm.read_homefile(use_empty=True)
    sc = bpy.context.scene

    def ob(name, data=None, parent=None):
        o = bpy.data.objects.new(name, data)
        sc.collection.objects.link(o)
        if parent is not None:
            o.parent = parent
        return o
    g = ob("group1")
    g.location = (1.0, 2.0, 3.0)
    me = bpy.data.meshes.new("pCubeShape1")
    me.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [], [(0, 1, 2)])
    cube = ob("pCube1", me, parent=g)
    other = ob("null1")
    bpy.context.view_layer.update()
    return g, cube, other


def test_graph_lists_scene_objects():
    g, cube, other = _scene()
    nodes, by = hg.graph(bpy.context.scene)
    assert set(by) == {g.session_uid, cube.session_uid, other.session_uid}
    assert dict(nodes)[cube.session_uid] == g.session_uid
    assert dict(nodes)[g.session_uid] is None


def test_select_from_graph():
    g, cube, other = _scene()
    _nodes, by = hg.graph(bpy.context.scene)
    ctx = bpy.context
    hg.select(ctx, by, [cube.session_uid], 'REPLACE', lead=cube.session_uid)
    assert cube.select_get() and not g.select_get() and ctx.view_layer.objects.active == cube
    hg.select(ctx, by, [g.session_uid], 'TOGGLE', lead=g.session_uid)
    assert cube.select_get() and g.select_get() and ctx.view_layer.objects.active == g
    hg.select(ctx, by, [cube.session_uid], 'REMOVE')
    assert not cube.select_get() and g.select_get()
    hg.select(ctx, by, [], 'REPLACE')
    assert not any(o.select_get() for o in ctx.scene.objects)


def test_mmb_drop_parents_and_unparents_keeping_world():
    g, cube, other = _scene()
    _nodes, by = hg.graph(bpy.context.scene)
    world = cube.matrix_world.copy()
    for o in bpy.context.scene.objects:
        o.select_set(False)
    n, msg = hg.drop(bpy.context, by, cube.session_uid, other.session_uid)
    bpy.context.view_layer.update()
    assert n == 1 and not msg and cube.parent == other
    assert (cube.matrix_world.translation - world.translation).length < 1e-6
    n, msg = hg.drop(bpy.context, by, cube.session_uid, None)       # empty space: to the world
    bpy.context.view_layer.update()
    assert n == 1 and cube.parent is None
    assert (cube.matrix_world.translation - world.translation).length < 1e-6
    # a parent can't go under its own child
    cube.parent = g
    bpy.context.view_layer.update()
    n, msg = hg.drop(bpy.context, by, g.session_uid, cube.session_uid)
    assert n == 0 and "own child" in msg and g.parent is None
    # a selected dragged node takes the whole selection along
    g.select_set(True)
    other.select_set(True)
    n, _msg = hg.drop(bpy.context, by, other.session_uid, cube.session_uid)
    assert other.parent == cube and g.parent is None        # g is cube's parent: skipped as a cycle


def test_collapse_state_is_session_only():
    g, cube, other = _scene()
    hg.COLLAPSED.clear()
    hg.toggle_collapsed(g.session_uid)
    cents, _n, _b = hg.centres(bpy.context.scene)
    assert cube.session_uid not in cents and g.session_uid in cents
    hg.set_all_collapsed(bpy.context.scene, False)
    cents, _n, _b = hg.centres(bpy.context.scene)
    assert cube.session_uid in cents
    hg.set_all_collapsed(bpy.context.scene, True)
    assert hg.COLLAPSED == {g.session_uid}
    hg.COLLAPSED.clear()
    assert "allset_hg" not in " ".join(k for o in bpy.data.objects for k in o.keys())


def test_double_click_timing():
    hg._LAST_CLICK.update(key=None, time=0.0)
    ctx = bpy.context
    limit = ctx.preferences.inputs.mouse_double_click_time / 1000.0
    assert not hg.is_double_click(ctx, "a", now=10.0)
    assert hg.is_double_click(ctx, "a", now=10.0 + limit * 0.5)
    assert not hg.is_double_click(ctx, "a", now=10.0 + limit * 0.6)       # a third press starts over
    assert not hg.is_double_click(ctx, "b", now=10.0 + limit * 0.7)       # another node
    assert not hg.is_double_click(ctx, "b", now=10.0 + limit * 3)         # too slow


# --- wiring -----------------------------------------------------------------------------------------------------

def test_menus_open_the_hypergraph():
    assert menu_map.MAP["Windows/General Editors/Hypergraph: Hierarchy"][0] == "allset.hypergraph"
    assert "Windows/General Editors/Hypergraph: Hierarchy" not in notices.NOTICES
    assert not [k for k in notices.PANEL_MENU if k.endswith("Hypergraph Panel")]
    row = next(r for r in panel_menu_data.PANELS if len(r) > 1 and r[1] == "Hypergraph Panel")
    assert "allset.hypergraph" in row, row
    assert hasattr(bpy.ops.allset, "hypergraph")


def test_marked_kind_is_unique():
    flags = marked_window.KINDS[hg.KIND]
    others = [v for k, v in marked_window.KINDS.items() if k != hg.KIND]
    assert flags not in others


def test_keymap_items():
    km = kit.maya_kc().keymaps["View2D Buttons List"]
    ids = [(k.idname, k.type, k.value) for k in km.keymap_items]
    for want in (("allset.hg_click", 'LEFTMOUSE', 'PRESS'), ("allset.hg_mmb", 'MIDDLEMOUSE', 'PRESS'),
                 ("allset.hg_rmb", 'RIGHTMOUSE', 'PRESS'),
                 ("allset.hg_zoom", 'WHEELUPMOUSE', 'PRESS'), ("allset.hg_frame", 'F', 'PRESS'),
                 ("allset.hg_frame", 'A', 'PRESS')):
        assert want in ids, want


def test_operators_pass_outside_the_window():
    # no Hypergraph region in the context: every input item polls False (other Properties editors keep their keys)
    for name in ("hg_click", "hg_mmb", "hg_rmb", "hg_zoom", "hg_frame"):
        assert not getattr(bpy.ops.allset, name).poll(), name
