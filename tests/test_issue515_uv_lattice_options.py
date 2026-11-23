"""#515: the UV Editor Lattice tool has Maya's Falloff, Use bounding rectangle, Show move manipulator and Snap
corner / Snap center settings. Falloff scales how far the UVs follow the lattice; without the bounding rectangle a
drawn lattice bends only the targeted UVs inside it; the pixel snap puts a value on a pixel corner or centre."""

from importlib import import_module

import bmesh
import bpy
import numpy as np

import kit

brush = import_module(kit.MODULE + ".operators.uv_brush")
lattice = import_module(kit.MODULE + ".operators.uv_lattice")


def _grid(n=8):
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


def test_settings():
    s = bpy.context.scene.allset_uv_brush
    assert (round(s.lattice_falloff, 6), s.lattice_bounding_rect, s.lattice_move_manipulator, s.lattice_snap) == \
        (1.0, True, True, 'CENTER')


def test_falloff_scales_the_bend():
    ob = _grid()
    m = brush.MeshUVs(ob, True)
    lat = lattice.Lattice([m], 3, 3)
    lat.pts[0, 0] += (-0.1, -0.1)
    full = lattice.deform(lat.pts, lat.st[0]) - lat.base[0]
    lat.apply([m], 0.5)
    got = m.U[lat.targets[0]] - lat.base[0]
    assert np.allclose(got, 0.5 * full, atol=1e-6), "Falloff 0.5 = half the bend"
    lat.apply([m], 0.0)
    assert np.allclose(m.U[lat.targets[0]], lat.base[0], atol=1e-7), "Falloff 0 = no bend"


def test_drawn_lattice_targets_the_uvs_inside():
    ob = _grid()
    m = brush.MeshUVs(ob, True)
    rect = (0.2, 0.2, 0.6, 0.6)
    lat = lattice.Lattice([m], 3, 3, rect=rect)
    inside = m.U[lat.targets[0]]
    assert lat.drawn and lat.rect == rect
    assert len(inside) and (inside >= 0.2 - 1e-9).all() and (inside <= 0.6 + 1e-9).all()
    assert len(inside) < len(m.U)
    lat.pts[-1, -1] += (0.1, 0.1)
    U0 = m.U.copy()
    lat.apply([m])
    out = np.setdiff1d(np.arange(len(U0)), lat.targets[0])
    assert np.allclose(m.U[out], U0[out]), "UVs outside the drawn lattice stay"
    assert lat.matches([brush.MeshUVs(ob, True)], 3, 3), "the drawn lattice stays while the UVs are where it left them"


def test_lattice_for_follows_the_bounding_rect_setting():
    ob = _grid()
    s = bpy.context.scene.allset_uv_brush
    lattice._state.update(lattice=None)
    assert lattice.lattice_for(bpy.context, [brush.MeshUVs(ob, True)]) is not None
    s.lattice_bounding_rect = False
    assert lattice.lattice_for(bpy.context, [brush.MeshUVs(ob, True)]) is None, "off: no lattice until one is drawn"
    s.lattice_bounding_rect = True
    lattice._state.update(lattice=None)


def test_pixel_snap():
    assert abs(lattice.snap_pixel(0.1234, 256, 'CORNER') - 32 / 256) < 1e-12
    assert abs(lattice.snap_pixel(0.1234, 256, 'CENTER') - 31.5 / 256) < 1e-12
    assert lattice.snap_pixel(0.5, 0, 'CENTER') == 0.5
    assert lattice.segment_hit((5, 1), (0, 0), (10, 0)) == 1.0
