"""UV Editor > Image > Measure Pixel Distance (and the Shift+right-click UV menu item): a Pixel Distance window with the
width (U Distance), height (V Distance) and diagonal (Distance) of the selected UVs' bounding box in pixels for map
sizes 4096, 2048, 1024, 512, 256 and 128; nothing selected = a warning and no window."""

import math
from importlib import import_module

import bmesh
import bpy

import kit

tk = import_module(kit.MODULE + ".operators.uv_toolkit_ops")
menu_map = import_module(kit.MODULE + ".ui.menu_map")
menus = import_module(kit.MODULE + ".marking.menus")

PATH = "UV Editor/Image/Measure Pixel Distance"


def _plane_with_two_uvs_picked():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    kit.enable()
    bpy.ops.mesh.primitive_plane_add(size=2)
    ob = bpy.context.object
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.scene.tool_settings.use_uv_select_sync = True
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.active
    for el in (*bm.verts, *bm.edges, *bm.faces):
        el.select = False
    bm.faces.ensure_lookup_table()
    f = bm.faces[0]
    f.loops[0][uv].uv = (0.25, 0.5)
    f.loops[2][uv].uv = (0.5, 0.625)
    f.loops[1][uv].uv = (0.4, 0.55)
    f.loops[3][uv].uv = (0.3, 0.6)
    f.loops[0].vert.select = True
    f.loops[2].vert.select = True
    bmesh.update_edit_mesh(ob.data)
    return ob


def test_rows_for_each_map_size():
    rows = tk.pixel_distance_rows(0.25, 0.125)
    assert [r[0] for r in rows] == [4096, 2048, 1024, 512, 256, 128]
    assert rows[0][1:3] == (1024.0, 512.0) and abs(rows[0][3] - math.hypot(1024, 512)) < 1e-9
    assert all(abs(a[i] / b[i] - 2.0) < 1e-12 for a, b in zip(rows, rows[1:]) for i in range(4))


def test_measures_the_selected_uvs_box():
    _plane_with_two_uvs_picked()
    du, dv = tk.selected_box(bpy.context)
    assert abs(du - 0.25) < 1e-6 and abs(dv - 0.125) < 1e-6, (du, dv)
    assert bpy.ops.allset.uv_measure_pixel_distance('EXEC_DEFAULT') == {'FINISHED'}


def test_nothing_selected_warns():
    """Nothing selected: no box, the command warns and stops."""
    ob = _plane_with_two_uvs_picked()
    bm = bmesh.from_edit_mesh(ob.data)
    for el in (*bm.verts, *bm.edges, *bm.faces):
        el.select = False
    bmesh.update_edit_mesh(ob.data)
    assert bpy.ops.allset.uv_measure_pixel_distance('EXEC_DEFAULT') == {'CANCELLED'}


def test_menu_items_reach_the_window():
    spec = menu_map.spec(PATH)
    assert spec is not None and spec[1] == "allset.uv_measure_pixel_distance", spec
    # the Shift+right-click UV menu item runs the same menu path
    assert menus._uve("Image/Measure Pixel Distance") == menus._item(PATH)
    src = open(menus.__file__, encoding="utf-8").read()
    assert '("Measure Pixel Distance", _uve("Image/Measure Pixel Distance"))' in src
