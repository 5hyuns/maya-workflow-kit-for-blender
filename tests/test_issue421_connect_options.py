"""Connect Tool options (GitHub #421): a Segments / Slide / Pinch value typed into the tool's options re-does the
connection the tool just made, like Maya; the Modeling Toolkit's Connect button enters the tool and shows its
Connect Options. GUI: tests/gui/gui_issue421_connect_options.py."""

from importlib import import_module

import bmesh
import bpy

import kit

connect_tool = import_module(kit.MODULE + ".operators.connect_tool")
edge_loops = import_module(kit.MODULE + ".operators.edge_loops")
mtk = import_module(kit.MODULE + ".ui.modeling_toolkit")
menu_map = import_module(kit.MODULE + ".ui.menu_map")


def _grid():
    """A plane of 2 x 2 quads in edit mode (vertices at -1, 0, 1), edge select mode, nothing selected."""
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=2, y_subdivisions=2, size=2)
    ob = bpy.context.active_object
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.tool_settings.mesh_select_mode = (False, True, False)
    bpy.ops.mesh.select_all(action='DESELECT')
    return ob


def _edge(bm, a, b):
    def near(p):
        return min(bm.verts, key=lambda v: (v.co.x - p[0]) ** 2 + (v.co.y - p[1]) ** 2)
    va, vb = near(a), near(b)
    return next(e for e in va.link_edges if e.other_vert(va) is vb)


def _counts(ob):
    bm = bmesh.from_edit_mesh(ob.data)
    return len(bm.verts), len(bm.edges), len(bm.faces)


def _select_two_ring_edges(ob):
    bm = bmesh.from_edit_mesh(ob.data)
    for e in (_edge(bm, (-1, -1), (-1, 0)), _edge(bm, (0, -1), (0, 0))):   # both sides of the lower-left quad
        e.select = True
    bm.select_flush_mode()
    bmesh.update_edit_mesh(ob.data)


def _reset():
    s = edge_loops.settings(bpy.context)
    connect_tool.end_path()
    edge_loops.reset_settings(s, 'CONNECT')
    return s


def test_segments_typed_in_redo_the_connection():
    s = _reset()
    ob = _grid()
    n0 = _counts(ob)
    _select_two_ring_edges(ob)
    assert bpy.ops.allset.connect_tool_enter() == {'FINISHED'}
    assert _counts(ob) == (n0[0] + 2, n0[1] + 3, n0[2] + 1), _counts(ob)      # Segments 1: one edge
    s.ct_segments = 5
    assert _counts(ob) == (n0[0] + 10, n0[1] + 15, n0[2] + 5), _counts(ob)    # five edges instead
    s.ct_segments = 2
    assert _counts(ob) == (n0[0] + 4, n0[1] + 6, n0[2] + 2), _counts(ob)
    connect_tool.end_path()                       # Enter: the connection is final, a new value changes nothing
    s.ct_segments = 3
    assert _counts(ob) == (n0[0] + 4, n0[1] + 6, n0[2] + 2), _counts(ob)
    _reset()
    bpy.ops.object.mode_set(mode='OBJECT')


def test_slide_typed_in_moves_the_cut():
    s = _reset()
    ob = _grid()
    _select_two_ring_edges(ob)
    bpy.ops.allset.connect_tool_enter()
    s.ct_slide = 0.2
    bm = bmesh.from_edit_mesh(ob.data)
    new = [round(v.co.y, 4) for v in bm.verts if abs(v.co.x + 1) < 1e-6 and -1 < v.co.y < 0]
    assert len(new) == 1 and abs(abs(new[0] + 0.5) - 0.3) < 1e-4, new   # no longer in the middle
    _reset()
    bpy.ops.object.mode_set(mode='OBJECT')


def test_option_window_values_do_not_change_the_previous_connection():
    s = _reset()
    ob = _grid()
    _select_two_ring_edges(ob)
    bpy.ops.allset.connect_tool_enter()
    n1 = _counts(ob)
    bpy.ops.mesh.select_all(action='DESELECT')
    assert bpy.ops.allset.connect_tool_enter(segments=4) == {'FINISHED'}
    assert s.ct_segments == 4
    assert _counts(ob) == n1, (_counts(ob), n1)
    _reset()
    bpy.ops.object.mode_set(mode='OBJECT')


def test_modeling_toolkit_connect_button_is_the_tool():
    row = next(r for r in mtk.TOOLS if r[0] == "Connect")
    assert row[1] == "Mesh Tools/Connect" and menu_map.MAP[row[1]] == "allset.connect_tool_enter"
    assert mtk._tool_ids()["Connect"] == connect_tool.TOOL
