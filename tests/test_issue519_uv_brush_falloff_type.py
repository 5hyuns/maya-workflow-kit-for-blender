"""#519: the UV brush marking menu's Falloff Type items set how the Pin and Smear brushes reach the UVs, like Maya:
Volume = every UV inside the circle (a nearby shell and the far side of a cut too); Surface/Volume (the start value)
and Surface = only the UVs joined, inside the circle, to the part of the shell under the brush centre (Surface/Volume
by straight distance, Surface by the distance along the UV edges)."""

from importlib import import_module

import bmesh
import bpy
import numpy as np

import kit

brush = import_module(kit.MODULE + ".operators.uv_brush")
bmath = import_module(kit.MODULE + ".operators.uv_brush_math")
menus = import_module(kit.MODULE + ".marking.menus")


def _grid(n=20):
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=n, y_subdivisions=n, size=2, calc_uvs=True)
    ob = bpy.context.active_object
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.scene.tool_settings.use_uv_select_sync = True
    bpy.ops.mesh.select_all(action='SELECT')
    return ob


def _two_shells(ob, gap=0.02):
    """Faces right of u = 0.5 move ``gap`` to the right: two shells side by side."""
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.active
    for f in bm.faces:
        if f.calc_center_median().x > 0:
            for l in f.loops:
                l[uv].uv.x += gap
    bmesh.update_edit_mesh(ob.data)


def _slit(ob, u_end=0.6):
    """A cut along v = 0.5 from u = 0 to ``u_end``: the faces above it move up a hair (still one shell)."""
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.active
    for f in bm.faces:
        c = f.calc_center_median()
        if c.y > 0:
            for l in f.loops:
                if abs(l[uv].uv.y - 0.5) < 1e-6 and l[uv].uv.x < u_end - 1e-6:
                    l[uv].uv.y += 1e-4
    bmesh.update_edit_mesh(ob.data)


def _reached(ob, centre, kind, r=0.1):
    m = brush.MeshUVs(ob, True)
    d = brush.brush_distances(m, centre, r, kind)
    return m, np.isfinite(d), d


def test_menu_items_set_the_type():
    s = bpy.context.scene.allset_uv_brush
    assert s.falloff_type == 'SURFACE_VOLUME'
    sub = menus.MENUS["UV_BRUSH"].radial["W"][1]
    got = {k: (label, action) for k, (label, action) in sub.radial.items()}
    for key, label, value in (("W", "Surface/Volume", 'SURFACE_VOLUME'), ("SW", "Surface", 'SURFACE'),
                              ("S", "Volume", 'VOLUME')):
        assert got[key][0] == label
        op, props = got[key][1]
        assert op == "wm.context_set_enum" and props["value"] == value, got[key]
        getattr(bpy.ops.wm, "context_set_enum")(**props)
        assert s.falloff_type == value
    s.falloff_type = 'SURFACE_VOLUME'


def test_other_shell():
    ob = _grid()
    _two_shells(ob)
    for kind, want_other in (("VOLUME", True), ("SURFACE_VOLUME", False), ("SURFACE", False)):
        m, reach, _d = _reached(ob, (0.47, 0.5), kind)
        right = m.U[:, 0] > 0.51
        assert reach[~right].any()
        assert bool(reach[right].any()) == want_other, kind


def test_across_a_cut():
    ob = _grid()
    _slit(ob)
    for kind, want_above in (("VOLUME", True), ("SURFACE_VOLUME", False), ("SURFACE", False)):
        m, reach, _d = _reached(ob, (0.3, 0.48), kind)
        above = m.U[:, 1] > 0.5 + 5e-5
        assert reach[~above].any()
        assert bool(reach[above].any()) == want_above, kind


def test_surface_distance_runs_along_the_edges():
    """Near the end of a cut both surface kinds reach round it; Surface counts the way round, Surface/Volume the
    straight distance."""
    ob = _grid()
    _slit(ob)
    centre = (0.55, 0.48)
    m, reach, d_sv = _reached(ob, centre, "SURFACE_VOLUME", r=0.15)
    _m, reach_s, d_s = _reached(ob, centre, "SURFACE", r=0.15)
    above = (np.abs(m.U[:, 0] - 0.55) < 1e-6) & (np.abs(m.U[:, 1] - 0.55) < 1e-6)
    assert above.any() and np.isfinite(d_sv[above]).all(), "joined round the end of the cut"
    assert abs(d_sv[above][0] - 0.07) < 1e-6, d_sv[above]
    assert not np.isfinite(d_s[above]).any() or d_s[above][0] > 0.1, d_s[above]
    assert reach_s.sum() < reach.sum(), "the way round is longer, so fewer UVs are in reach"


def test_pin_and_smear_follow_the_type():
    ob = _grid()
    _two_shells(ob)
    s = bpy.context.scene.allset_uv_brush
    for kind in ("VOLUME", "SURFACE_VOLUME"):
        m = brush.MeshUVs(ob, True)
        m.write_pins(np.zeros(len(m.U), bool))
        brush.apply_dab("PIN", m, (0.47, 0.5), 0.1, 1.0, falloff=kind)
        right = m.U[:, 0] > 0.51
        assert bool(m.pinned[right].any()) == (kind == "VOLUME"), kind
        m2 = brush.MeshUVs(ob, True)
        m2.write_pins(np.zeros(len(m2.U), bool))
        U0 = m2.U.copy()
        brush.apply_dab("SMEAR", m2, (0.47, 0.5), 0.1, 0.5, delta=(0.0, 0.02), falloff=kind)
        moved = np.abs(m2.U - U0).max(axis=1) > 1e-9
        assert bool(moved[right].any()) == (kind == "VOLUME"), kind
        m2.restore()
    s.falloff_type = 'SURFACE_VOLUME'
