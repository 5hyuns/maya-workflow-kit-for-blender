"""#535: the UV Toolkit's buttons sit where Maya's do, two to a row with Maya's full names (Create: Automatic |
Normal-Based, Cylindrical | Planar ...; Arrange and Layout: Stack Shells | Unstack Shells ...), one button with U / V
choices beside it instead of a button per direction (Unfold Along, Layout Along, Flip, Scale, Normalize), the Align
pictures in Maya's order, A to B / B to A for Stitch Together, AB / BA for Snap Together, Measure with its four kinds,
and Texel Density starting at 32 px per unit on a 512 map."""
from importlib import import_module

import bmesh
import bpy

import kit
import test_issue264_uv_toolkit as base

uvtk = import_module(kit.MODULE + ".ui.uv_toolkit")
menu_map = import_module(kit.MODULE + ".ui.menu_map")
compat = import_module(kit.MODULE + ".compat")


def _labels(rows):
    return [r[0] if r else None for r in rows]


def test_create_rows_like_maya():
    assert _labels(uvtk.CREATE) == ["Automatic", "Normal-Based", "Cylindrical", "Planar", "Spherical", "Best Plane",
                                    "Camera-Based", "Contour Stretch"]


def test_cut_and_sew_groups_like_maya():
    groups = [_labels(g) for g in uvtk.CUT_SEW_GROUPS]
    assert groups == [["Auto-Seams", None], ["Cut", "Cut Tool", "Create UV Shell", "Create Shell (Grid)"],
                      ["Sew", "Sew Tool"]]
    assert uvtk.STITCH[0] == "Stitch Together"
    tk = bpy.context.scene.allset_uv_toolkit
    names = {it.identifier: it.name for it in tk.bl_rna.properties["stitch_order"].enum_items}
    assert names == {'SMALL_TO_LARGE': "A to B", 'LARGE_TO_SMALL': "B to A"} and tk.stitch_order == 'SMALL_TO_LARGE'


def test_arrange_rows_like_maya():
    assert _labels(uvtk.ARRANGE_ROWS) == ["Orient Shells", "Orient to Edges", "Stack Shells", "Unstack Shells",
                                          "Stack and Orient", "Stack Similar", "Gather Shells", "Randomize Shells"]


def test_every_button_path_is_a_kit_command():
    paths = [uvtk._path(p) for rows in (uvtk.CREATE, uvtk.CUT_SEW, uvtk.SNAP, uvtk.ARRANGE) for _t, p in rows]
    paths += [uvtk._path(f"Tools/{t}") for t in ("Cut", "Sew", "Optimize", "Unfold", "Pin", "Grab", "Lattice",
                                                 "Pinch", "Smear")]
    missing = [p for p in paths if p not in menu_map.MAP]
    assert not missing, missing


def test_align_pictures_in_maya_order():
    assert [(a, w) for a, w, _l in uvtk.ALIGN] == [('U', 'MIN'), ('U', 'AVG'), ('U', 'MAX'), ('V', 'MAX'),
                                                   ('V', 'AVG'), ('V', 'MIN')]


def test_one_button_with_u_v_choices():
    tk = bpy.context.scene.allset_uv_toolkit
    for prop in ("unfold_axis", "layout_axis", "flip_axis"):
        assert [it.identifier for it in tk.bl_rna.properties[prop].enum_items] == ['U', 'V'], prop
        assert getattr(tk, prop) == 'U', prop
    assert tk.snap_order == '0' and tk.normalize_u and tk.normalize_v
    # Scale U / V: both on = UV; one alone; the last one left stays on
    assert tk.scale_axis == 'UV' and tk.scale_u and tk.scale_v
    tk.scale_v = False
    assert tk.scale_axis == 'U' and tk.scale_u and not tk.scale_v
    tk.scale_u = False
    assert tk.scale_axis == 'U', "the only scale direction left stays on"
    tk.scale_v = True
    tk.scale_u = False
    assert tk.scale_axis == 'V'
    tk.scale_u = True
    assert tk.scale_axis == 'UV'


def test_texel_density_start_values():
    s = bpy.context.scene.allset_uv
    assert s.map_size == 512 and abs(s.texel_density - 32.0) < 1e-9


def _select_uvs(ob, picks):
    """Select only the UVs at the given coordinates (UV component, sync off)."""
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.active
    ts = bpy.context.scene.tool_settings
    sync = ts.use_uv_select_sync
    for f in bm.faces:
        for lp in f.loops:
            on = any(abs(lp[uv].uv[0] - u) < 1e-6 and abs(lp[uv].uv[1] - v) < 1e-6 for u, v in picks)
            if sync:
                lp.vert.select = lp.vert.select or on
            compat.set_uv_vert_selected(lp, uv, on)
            compat.set_uv_edge_selected(lp, uv, False)
    bmesh.update_edit_mesh(ob.data)


def test_measure_kinds():
    base._clear()
    ob = base._quads("M", [[(0.1, 0.2), (0.4, 0.2), (0.4, 0.6), (0.1, 0.6)]])
    base._edit(ob)
    tk = bpy.context.scene.allset_uv_toolkit
    bpy.context.scene.allset_uv.map_size = 512
    tk.measure_type = 'U'
    assert bpy.ops.allset.uv_measure() == {'FINISHED'}
    assert abs(tk.measure_result - 0.3) < 1e-4, tk.measure_result
    tk.measure_type = 'V'
    assert bpy.ops.allset.uv_measure() == {'FINISHED'}
    assert abs(tk.measure_result - 0.4) < 1e-4, tk.measure_result
    tk.measure_type = 'PIXEL'
    assert bpy.ops.allset.uv_measure() == {'FINISHED'}
    assert abs(tk.measure_result - 0.5 * 512) < 1e-3, tk.measure_result
    # Angle Between needs two UVs: the line from the left one to the right one
    tk.measure_type = 'ANGLE'
    assert bpy.ops.allset.uv_measure() == {'CANCELLED'}
    _select_uvs(ob, [(0.4, 0.6), (0.1, 0.2)])
    assert bpy.ops.allset.uv_measure() == {'FINISHED'}
    assert abs(tk.measure_result - 53.1301) < 1e-3, tk.measure_result
