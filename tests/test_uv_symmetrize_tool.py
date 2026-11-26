"""UV Editor > Tools > Symmetrize is a brush tool of the UV Editor, like Maya: the first click picks an edge on the mesh's
symmetry line (the Mirror Axis follows the edge), then each dab gives the UVs under the brush, on its side of the
Axis Position line, the mirror of their counterpart's UV; UVs of the symmetry line move onto the line, UVs on the other
side and outside the brush stay. Flood Shells does the brush's whole side of a touched shell. Modify > Symmetrize and
the Tools menu item make the tool active."""

import random
from importlib import import_module

import bmesh
import bpy
import numpy as np

import kit

brush = import_module(kit.MODULE + ".operators.uv_brush")
sym = import_module(kit.MODULE + ".operators.uv_symmetrize")
tools = import_module(kit.MODULE + ".ui.uv_brush_tools")
editor_map = import_module(kit.MODULE + ".ui.editor_menu_map")
menus = import_module(kit.MODULE + ".marking.menus")

NU, NV = 4, 2


def _plane(jitter=0.04, seed=1):
    """A 4 x 2 face plane; UV of vertex (i, j) = (i / 4, j / 2) moved a little at random (both halves differ)."""
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    me = bpy.data.meshes.new("pl")
    ob = bpy.data.objects.new("pl", me)
    bpy.context.collection.objects.link(ob)
    bm = bmesh.new()
    vs = {(i, j): bm.verts.new((i / NU - 0.5, j / NV - 0.5, 0.0)) for j in range(NV + 1) for i in range(NU + 1)}
    for j in range(NV):
        for i in range(NU):
            bm.faces.new((vs[i, j], vs[i + 1, j], vs[i + 1, j + 1], vs[i, j + 1]))
    uv = bm.loops.layers.uv.new("UVMap")
    rnd = random.Random(seed)
    off = {k: (rnd.uniform(-jitter, jitter), rnd.uniform(-jitter, jitter)) for k in vs}
    key = {v: k for k, v in vs.items()}
    for f in bm.faces:
        for lp in f.loops:
            i, j = key[lp.vert]
            lp[uv].uv = (i / NU + off[i, j][0], j / NV + off[i, j][1])
    bm.to_mesh(me)
    bm.free()
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.scene.tool_settings.use_uv_select_sync = True
    bpy.ops.mesh.select_all(action='SELECT')
    return ob


def _setup(edge_mid_uv):
    ob = _plane()
    m = brush.MeshUVs(ob, True)
    d, e, direction = sym.nearest_edge(m, edge_mid_uv)
    assert d < 0.05, d
    mir = sym.Mirror(m, e)
    assert mir.ok
    return m, mir, direction


def _ij(m):
    """UV point index -> grid (i, j)."""
    out = {}
    for k, loops in enumerate(m.loops):
        co = loops[0].vert.co
        out[k] = (round((co.x + 0.5) * NU), round((co.y + 0.5) * NV))
    return out


def _by_ij(m):
    return {v: k for k, v in _ij(m).items()}


def test_pick_sets_axis_and_sides():
    m, mir, direction = _setup((0.5, 0.25))
    assert sym.axis_of(direction) == 'U'
    ij = _ij(m)
    for k, (i, j) in ij.items():
        if i == 2:
            assert mir.side[k] == sym.ON_LINE, (i, j)
        else:
            assert ij[int(mir.other[k])] == (4 - i, j), ((i, j), ij[int(mir.other[k])])
    assert len(mir.line_edges) == NV, "the symmetry line = the middle column of edges"
    m2, mir2, direction2 = _setup((0.625, 0.5))
    assert sym.axis_of(direction2) == 'V', "a side-to-side edge mirrors V"


def _dab(m, mir, centre, r, axis='U', pos=0.5, flood=False):
    return sym.dab(m.U, mir.side, mir.other, mir.shell, centre, r, axis, pos, flood)


def test_dab_mirrors_the_brush_side_only():
    m, mir, _ = _setup((0.5, 0.25))
    U0 = m.U.copy()
    centre, r = (0.1, 0.25), 0.3
    new = _dab(m, mir, centre, r)
    inside = np.hypot(U0[:, 0] - centre[0], U0[:, 1] - centre[1]) <= r
    ij = _ij(m)
    for k, (i, j) in ij.items():
        if inside[k] and i < 2:
            o = int(mir.other[k])
            assert np.allclose(new[k], (1.0 - U0[o, 0], U0[o, 1])), (i, j)
        else:
            assert np.allclose(new[k], U0[k]), f"{(i, j)} outside the brush or on the other side stays"
    assert inside.any() and not np.allclose(new, U0)


def test_dab_on_the_right_and_line_points():
    m, mir, _ = _setup((0.5, 0.25))
    U0 = m.U.copy()
    new = _dab(m, mir, (0.75, 0.5), 2.0)          # a brush over everything, centre right of the line
    for k, (i, j) in _ij(m).items():
        o = int(mir.other[k])
        if i == 2:
            assert abs(new[k, 0] - 0.5) < 1e-12 and abs(new[k, 1] - U0[k, 1]) < 1e-12, "line UVs move onto it"
        elif i > 2:
            assert np.allclose(new[k], (1.0 - U0[o, 0], U0[o, 1]))
        else:
            assert np.allclose(new[k], U0[k])


def test_axis_position_moves_the_mirror_line():
    m, mir, _ = _setup((0.5, 0.25))
    U0 = m.U.copy()
    new = _dab(m, mir, (0.1, 0.25), 2.0, pos=0.4)
    for k, (i, j) in _ij(m).items():
        o = int(mir.other[k])
        if i < 2:
            assert np.allclose(new[k], (0.8 - U0[o, 0], U0[o, 1]))
        elif i == 2:
            assert abs(new[k, 0] - 0.4) < 1e-12


def test_v_axis_mirrors_across_a_row():
    m, mir, _ = _setup((0.625, 0.5))
    U0 = m.U.copy()
    new = _dab(m, mir, (0.3, 0.1), 2.0, axis='V')
    for k, (i, j) in _ij(m).items():
        o = int(mir.other[k])
        if j == 0:
            assert np.allclose(new[k], (U0[o, 0], 1.0 - U0[o, 1]))
        elif j == 1:
            assert abs(new[k, 1] - 0.5) < 1e-12 and abs(new[k, 0] - U0[k, 0]) < 1e-12
        else:
            assert np.allclose(new[k], U0[k])


def test_flood_shells_does_the_whole_side():
    m, mir, _ = _setup((0.5, 0.25))
    U0 = m.U.copy()
    centre = tuple(U0[_by_ij(m)[0, 0]] + 0.01)
    small = _dab(m, mir, centre, 0.05)
    changed = np.any(np.abs(small - U0) > 1e-12, axis=1)
    assert changed.sum() == 1, "without Flood Shells only the UV under the brush"
    flood = _dab(m, mir, centre, 0.05, flood=True)
    for k, (i, j) in _ij(m).items():
        if i <= 2:
            assert not np.allclose(flood[k], U0[k]), (i, j)
        else:
            assert np.allclose(flood[k], U0[k])


def test_nothing_without_a_seam_and_not_symmetric():
    ob = _plane()
    m = brush.MeshUVs(ob, True)
    sym.clear()
    assert sym.seam_of(m) is None
    _d, e, _dir = sym.nearest_edge(m, (0.25, 0.25))       # an off-centre column: the halves don't match
    assert not sym.Mirror(m, e).ok


def test_remember_and_clear():
    m, mir, _ = _setup((0.5, 0.25))
    e = int(next(iter(mir.line_edges)))
    sym.remember(m, e, mir)
    assert sym.seam_of(m) == e and len(sym.segments()) == NV
    sym.clear()
    assert sym.seam_of(m) is None and not sym.segments()


def test_tool_registered_and_settings():
    t = next(t for t in tools.TOOLS if getattr(t, "mode", "") == "SYMMETRIZE")
    assert t.bl_idname == "allset.uv_brush_symmetrize" and t.bl_label == "Symmetrize"
    ctrl = [k for k in t.bl_keymap if k[0] == "allset.uv_brush_stroke" and k[1].get("ctrl")]
    assert ctrl, "Ctrl+click is bound (it does nothing, like Maya)"
    s = bpy.context.scene.allset_uv_brush
    assert abs(s.sym_size - 0.1) < 1e-6 and s.sym_axis == "U" and abs(s.sym_axis_pos - 0.5) < 1e-6
    assert not s.sym_flood
    assert brush.BRUSH_PROPS["SYMMETRIZE"] == ("sym_size", None)


def test_menus_open_the_tool():
    for path in ("UV Editor/Tools/Symmetrize", "UV Editor/Modify/Symmetrize"):
        entry = editor_map.MAP.get(path)
        assert entry is not None and entry[1]["name"] == "allset.uv_brush_symmetrize", (path, entry)
