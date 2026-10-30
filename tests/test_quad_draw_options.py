"""Quad Draw's Ctrl+Shift+RMB options menu is Maya's marking menu (Multi-Cut N, Auto-weld W, Clear Dots E,
Soften/Harden NE, Relax NW, Extend SW, Snap to Backfaces / Reset Settings in the list)."""

from importlib import import_module

import bmesh
import bpy

import kit

mm = import_module(kit.MODULE + ".marking.menus")
qd = import_module(kit.MODULE + ".operators.quad_draw")


def test_tool_options_open_the_quad_draw_menu():
    assert mm.TOOL_OPTIONS[qd.TOOL] == "OPT_QUAD_DRAW"
    menu = mm.MENUS["OPT_QUAD_DRAW"]
    assert {d: e[0] for d, e in menu.radial.items()} == {
        "N": "Multi-Cut Tool", "W": "Auto-weld", "E": "Clear Dots", "NE": "Soften/Harden Edges",
        "NW": "Relax", "SW": "Extend"}
    assert [e[0] for e in menu.items if e is not mm.DIVIDER] == ["Snap to Backfaces", "Reset Settings"]


def test_radio_items_name_real_settings():
    s = bpy.context.scene.allset_poly_tools
    for _path, label, action in mm.walk(mm.MENUS["OPT_QUAD_DRAW"], "OPT_QUAD_DRAW"):
        if isinstance(action, tuple) and action[0] in ("wm.context_set_enum", "wm.context_toggle"):
            prop = action[1]["data_path"].rsplit(".", 1)[1]
            assert prop in s.bl_rna.properties, (label, prop)
            if "value" in action[1]:
                items = [i.identifier for i in s.bl_rna.properties[prop].enum_items]
                assert action[1]["value"] in items, (label, action[1]["value"], items)


def test_soften_harden_whole_mesh_clears_selection():
    bpy.ops.mesh.primitive_cube_add()
    ob = bpy.context.object
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(ob.data)
    for e in bm.edges:
        e.select_set(False)
    bm.edges.ensure_lookup_table()
    bm.edges[0].select_set(True)
    bmesh.update_edit_mesh(ob.data)
    bpy.ops.allset.soften_harden(whole=True)
    bm = bmesh.from_edit_mesh(ob.data)
    assert not any(v.select for v in bm.verts)
    assert all(not e.smooth for e in bm.edges)     # cube edges are 90 degrees: all hard at the default 30
    bpy.ops.object.mode_set(mode='OBJECT')
