"""#502: the UV Editor's Modify option boxes (Align, Distribute Shells / UVs, Flip, Layout Along, Match UVs, Normalize,
Rotate, Snap Together, Stack Similar Shells, Straighten Border, Unitize, Unstack Shells) open their option windows;
the saved settings drive the menu item, and a plain click with nothing saved runs the window's defaults."""

from importlib import import_module

import bmesh
import bpy

import kit

uvt = import_module(kit.MODULE + ".operators.uv_tools")
um = import_module(kit.MODULE + ".operators.uv_modify")
ow = import_module(kit.MODULE + ".operators.option_windows")
box = import_module(kit.MODULE + ".ui.menu_option_box")
menu_map = import_module(kit.MODULE + ".ui.menu_map")

M = "UV Editor/Modify/"
ITEMS = {"Align": "uv_align", "Distribute Shells": "uv_distribute_shells", "Distribute UVs": "uv_distribute_uvs",
         "Flip": "uv_flip", "Layout Along": "uv_layout_along", "Match UVs": "uv_match_uvs",
         "Normalize": "uv_normalize", "Rotate": "uv_rotate", "Snap Together": "uv_snap_together",
         "Stack Similar Shells": "uv_stack_similar", "Straighten Border": "uv_straighten_border",
         "Unitize": "uv_unitize", "Unstack Shells": "uv_unstack"}


def _clear(settings=True):
    if settings:
        for key in ITEMS.values():
            ow.store(key, None)
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)


def _edit(ob, select=True):
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.scene.tool_settings.use_uv_select_sync = True
    bpy.ops.mesh.select_all(action='SELECT' if select else 'DESELECT')
    return ob


def _plane(sx=1.0, sy=1.0, ox=0.0, oy=0.0, settings=True):
    """A one-face plane whose UVs fill 0-1 scaled by ``sx`` / ``sy`` and moved by ``ox`` / ``oy``."""
    _clear(settings)
    bpy.ops.mesh.primitive_plane_add(size=2)
    ob = bpy.context.active_object
    for d in ob.data.uv_layers.active.data:
        d.uv = (d.uv[0] * sx + ox, d.uv[1] * sy + oy)
    return _edit(ob)


def _cube_shells():
    """A cube with six one-face shells (Automatic), every face selected."""
    _clear()
    bpy.ops.mesh.primitive_cube_add(size=2)
    ob = _edit(bpy.context.active_object)
    assert bpy.ops.allset.uv_automatic() == {'FINISHED'}
    bpy.ops.mesh.select_all(action='SELECT')
    return ob


def _bm(ob):
    bm = bmesh.from_edit_mesh(ob.data)
    bm.faces.ensure_lookup_table()
    return bm, bm.loops.layers.uv.active


def _uvs(ob):
    bm, uv = _bm(ob)
    return [l[uv].uv.copy() for f in bm.faces for l in f.loops]


def _span(ob):
    us = _uvs(ob)
    return min(p.x for p in us), max(p.x for p in us), min(p.y for p in us), max(p.y for p in us)


def _close(a, b, tol=1e-4):
    return abs(a - b) <= tol


def test_windows_open_from_the_option_boxes():
    for item, key in ITEMS.items():
        w = ow.find_path(M + item)
        assert w is not None and w.key == key, (item, w and w.key)
        assert box.option_kind(M + item) == "window", item
        assert hasattr(bpy.ops.allset, "opt_" + key), key
    assert ow.find_path(M + "Align").defaults() == {"align": "Minimum U value"}
    assert ow.find_path(M + "Rotate").defaults() == {"angle": 90.0}
    assert ow.find_path(M + "Normalize").defaults() == {"along": "UV", "each": "Collectively", "keep_aspect": False,
                                                        "closest_tile": True}
    assert ow.find_path(M + "Unstack Shells").defaults() == {"flip_reversed": True}
    assert ow.find_path(M + "Match UVs").defaults() == {"tolerance": 0.01}
    assert menu_map.MAP[M + "Match UVs"] == ("uv.remove_doubles", {"threshold": 0.01}), "the plain click: 0.01"


def test_align_plain_click_aligns_to_minimum_u_and_saved_choice_is_used():
    ob = _plane(0.5, 0.5, 0.2, 0.3)
    assert bpy.ops.allset.menu_item(item=M + "Align") == {'FINISHED'}
    lo_u, hi_u, _lo_v, _hi_v = _span(ob)
    assert _close(lo_u, 0.2) and _close(hi_u, 0.2), "every UV on the minimum U"
    ob = _plane(0.5, 0.5, 0.2, 0.3)
    assert bpy.ops.allset.opt_uv_align('EXEC_DEFAULT', align="Maximum V value") == {'FINISHED'}
    ob = _plane(0.5, 0.5, 0.2, 0.3, settings=False)
    assert bpy.ops.allset.menu_item(item=M + "Align") == {'FINISHED'}
    _lo_u, _hi_u, lo_v, hi_v = _span(ob)
    assert _close(lo_v, 0.8) and _close(hi_v, 0.8), "the saved Maximum V value"


def test_distribute_shells_up_with_padding():
    ob = _cube_shells()
    assert bpy.ops.allset.opt_uv_distribute_shells('EXEC_DEFAULT', direction="Up", padding=0.05) == {'FINISHED'}
    bm, uv = _bm(ob)
    boxes = sorted((uvt.uv_bounds(isl, uv) for isl in uvt.islands(bm, uv)), key=lambda b: b[0].y)
    assert len(boxes) == 6
    for (alo, ahi), (blo, bhi) in zip(boxes, boxes[1:]):
        assert _close(blo.y - ahi.y, 0.05, 1e-3), ("stacked upwards 0.05 apart", ahi.y, blo.y)
        assert _close((alo.x + ahi.x) / 2, (blo.x + bhi.x) / 2, 1e-3), "centred on one U"


def test_distribute_uvs_custom_distance():
    ob = _plane()
    assert bpy.ops.allset.opt_uv_distribute_uvs('EXEC_DEFAULT', spacing="Custom", distance=0.25, along="V") == \
        {'FINISHED'}
    vs = sorted({round(p.y, 4) for p in _uvs(ob)})
    steps = [round(b - a, 4) for a, b in zip(vs, vs[1:])]
    assert steps and all(_close(s, 0.25, 1e-3) for s in steps), vs


def test_normalize_options():
    ob = _plane(0.5, 0.25, 2.2, 0.1)
    assert bpy.ops.allset.opt_uv_normalize('EXEC_DEFAULT', along="U", closest_tile=True) == {'FINISHED'}
    lo_u, hi_u, lo_v, hi_v = _span(ob)
    assert _close(lo_u, 2.0) and _close(hi_u, 3.0), ("U fills the tile under it", lo_u, hi_u)
    assert _close(hi_v - lo_v, 0.25), "V untouched"
    ob = _plane(0.5, 0.25, 2.2, 0.1)
    assert bpy.ops.allset.opt_uv_normalize('EXEC_DEFAULT', keep_aspect=True, closest_tile=False) == {'FINISHED'}
    lo_u, hi_u, lo_v, hi_v = _span(ob)
    assert _close(lo_u, 0.0) and _close(hi_u, 1.0) and _close(lo_v, 0.0) and _close(hi_v, 0.5), \
        ("aspect kept, in 0-1", lo_u, hi_u, lo_v, hi_v)
    ob = _cube_shells()
    assert bpy.ops.allset.opt_uv_normalize('EXEC_DEFAULT', each="Each face separately") == {'FINISHED'}
    bm, uv = _bm(ob)
    for f in bm.faces:
        lo, hi = uvt.uv_bounds([f], uv)
        assert _close(hi.x - lo.x, 1.0) and _close(hi.y - lo.y, 1.0), "each face fills a tile"


def test_match_uvs_tolerance():
    ob = _cube_shells()
    n = len(uvt.islands(*_bm(ob)))
    assert bpy.ops.allset.opt_uv_match_uvs('EXEC_DEFAULT', tolerance=0.0) in ({'FINISHED'}, {'CANCELLED'})
    assert len(uvt.islands(*_bm(ob))) == n
    assert ow.saved("uv_match_uvs") == {"tolerance": 0.0}


def test_stack_similar_tolerance_and_unstack_flip_reversed():
    ob = _cube_shells()
    assert bpy.ops.allset.opt_uv_stack_similar('EXEC_DEFAULT', tolerance=0.1) == {'FINISHED'}
    bm, uv = _bm(ob)
    centres = {(round(c.x, 3), round(c.y, 3)) for c in (uvt.uv_centre(isl, uv) for isl in uvt.islands(bm, uv))}
    assert len(centres) == 1, "the six squares stacked"
    # one shell mirrored: Unstack flips it back by default, keeps it with the option off
    ob = _cube_shells()
    bm, uv = _bm(ob)
    isl = uvt.islands(bm, uv)[0]
    c = uvt.uv_centre(isl, uv)
    for f in isl:
        for loop in f.loops:
            loop[uv].uv.x = 2 * c.x - loop[uv].uv.x
    bmesh.update_edit_mesh(ob.data)
    bm, uv = _bm(ob)
    assert sum(1 for g in uvt.islands(bm, uv) if um._signed_area(g, uv) < 0) == 1
    assert bpy.ops.allset.opt_uv_unstack('EXEC_DEFAULT', flip_reversed=False) == {'FINISHED'}
    bm, uv = _bm(ob)
    assert sum(1 for g in uvt.islands(bm, uv) if um._signed_area(g, uv) < 0) == 1, "option off: stays mirrored"
    assert bpy.ops.allset.menu_item(item=M + "Unstack Shells") == {'FINISHED'}
    bm, uv = _bm(ob)
    assert sum(1 for g in uvt.islands(bm, uv) if um._signed_area(g, uv) < 0) == 1, "the saved option off is used"
    ow.store("uv_unstack", None)
    assert bpy.ops.allset.menu_item(item=M + "Unstack Shells") == {'FINISHED'}
    bm, uv = _bm(ob)
    assert all(um._signed_area(g, uv) > 0 for g in uvt.islands(bm, uv)), "default: reversed shells flipped back"


def test_operators_take_the_window_values():
    for op, props in (("uv_straighten_border", ("gap",)), ("uv_stack_similar", ("tolerance",)),
                      ("uv_distribute", ("direction", "padding")), ("uv_distribute_uvs", ("axis", "distance")),
                      ("uv_normalize", ("along", "each_face", "keep_aspect", "closest_tile")),
                      ("uv_unstack", ("flip_reversed",))):
        rna = getattr(bpy.ops.allset, op).get_rna_type()
        for p in props:
            assert p in rna.properties, (op, p)
