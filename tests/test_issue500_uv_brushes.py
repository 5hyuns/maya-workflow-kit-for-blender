"""#500: UV Editor > Tools > Unfold, Optimize, Cut, Sew, Pin, Smear and Smudge are brush tools of the UV Editor, like
Maya: the menu item makes the tool active, a drag applies it under the brush, B / M + drag set size / strength.

Results under the brush (each mode's apply function called directly): UVs outside the brush never move, pinned UVs
stay, Pin pins (Ctrl unpins) only the UVs inside the brush, Unfold / Optimize take the distortion out of the UVs under
the brush (only the selected UVs when some are selected), Cut splits the edge lines a stroke runs along when it covers
enough of them, Sew joins the shell border under the brush, Smear pushes UVs along the stroke with a falloff to the rim
(no upper limit on the strength), Smudge moves only selected UVs with a steep falloff, Lattice bends the UVs as a
Bezier patch."""

import math
from importlib import import_module

import bmesh
import bpy
import numpy as np

import kit

brush = import_module(kit.MODULE + ".operators.uv_brush")
bmath = import_module(kit.MODULE + ".operators.uv_brush_math")
tools = import_module(kit.MODULE + ".ui.uv_brush_tools")
uv_tools = import_module(kit.MODULE + ".operators.uv_tools")
taphold = import_module(kit.MODULE + ".operators.taphold")
menu_map = import_module(kit.MODULE + ".ui.menu_map")
editor_map = import_module(kit.MODULE + ".ui.editor_menu_map")
menus = import_module(kit.MODULE + ".marking.menus")
lattice = import_module(kit.MODULE + ".operators.uv_lattice")

LABELS = ("Unfold", "Optimize", "Cut", "Sew", "Pin", "Smear", "Smudge")
TOOL_LABELS = (*LABELS, "Lattice")


def _reset():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)


def _grid(squash=1.0, n=10):
    """An n x n face grid (2 x 2 units); its UVs fill 0-1, the U axis multiplied by ``squash``."""
    _reset()
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=n, y_subdivisions=n, size=2, calc_uvs=True)
    ob = bpy.context.active_object
    uvl = ob.data.uv_layers.active.data
    for d in uvl:
        d.uv = (d.uv[0] * squash, d.uv[1])
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.scene.tool_settings.use_uv_select_sync = True
    bpy.ops.mesh.select_all(action='SELECT')
    return ob


def _mesh(ob):
    return brush.MeshUVs(ob, True)


def _distortion(m):
    """Mean squared difference between each UV edge length and its 3D length (scaled to the shell)."""
    rows = m.edges()
    a = np.array([r[0] for r in rows])
    b = np.array([r[1] for r in rows])
    luv = np.linalg.norm(m.U[a] - m.U[b], axis=1)
    l3 = np.linalg.norm(m.P[a] - m.P[b], axis=1)
    k = luv.sum() / l3.sum()
    return float(np.mean((luv - l3 * k) ** 2))


# --- maths -------------------------------------------------------------------------------------------

def test_falloff_and_pin_math():
    f = bmath.falloff(np.array([0.0, 0.05, 0.1, 0.2]), 0.1)
    assert abs(f[0] - 1.0) < 1e-12 and 0.0 < f[1] < 1.0 and f[2] == 0.0 and f[3] == 0.0, f
    sc = bmath.sculpt_falloff(np.array([0.0, 0.25, 0.5, 0.75, 1.0, 1.5]), 1.0)
    assert abs(sc[0] - 1) < 1e-12 and sc[4] == 0.0 and sc[5] == 0.0, sc
    assert abs(sc[1] - 0.95) < 0.02 and abs(sc[2] - 0.69) < 0.03 and abs(sc[3] - 0.19) < 0.02, \
        f"Smear falloff: nearly flat to half the radius, then down to the rim {sc}"
    ex = bmath.smudge_falloff(np.array([0.0, 0.05, 0.07, 0.075, 0.1]), 0.075)
    assert abs(ex[0] - 1) < 1e-12 and 0.07 < ex[1] < 0.14 and ex[2] < 0.02 and ex[3] == 0.0 and ex[4] == 0.0, \
        f"Smudge Exponential falloff: steep {ex}"
    lin = bmath.smudge_falloff(np.array([0.0, 0.5, 1.0]), 1.0, "LINEAR")
    const = bmath.smudge_falloff(np.array([0.0, 0.9, 1.1]), 1.0, "CONSTANT")
    assert np.allclose(lin, [1, 0.5, 0]) and np.allclose(const, [1, 1, 0]), (lin, const)
    U = np.array([[0.5, 0.5], [0.55, 0.5], [0.8, 0.5]])
    assert list(bmath.pin(np.zeros(3, bool), U, (0.5, 0.5), 0.1)) == [True, True, False]
    assert list(bmath.pin(np.ones(3, bool), U, (0.5, 0.5), 0.1, on=False)) == [False, False, True]


def test_smear_math_outside_and_pins_stay():
    U = np.array([[0.5, 0.5], [0.55, 0.5], [0.8, 0.5], [0.5, 0.52]])
    held = np.array([False, False, False, True])
    out = bmath.smear(U, (0.5, 0.5), 0.1, (0.02, 0.0), 1.0, held=held)
    assert abs(out[0, 0] - 0.52) < 1e-12, "the UV at the centre moves the whole stroke at full strength"
    assert 0.5 < out[1, 0] < 0.57 and out[1, 0] - 0.55 < 0.02, "a UV off centre moves less"
    assert np.allclose(out[2], U[2]) and np.allclose(out[3], U[3]), "outside and pinned UVs stay"
    big = bmath.smear(U, (0.5, 0.5), 0.1, (0.02, 0.0), 5.0)
    assert abs(big[0, 0] - 0.6) < 1e-12, f"Smear strength has no upper limit ({big[0, 0]})"


def test_spaced_dabs_skip_a_tiny_move():
    pts, carry = bmath.spaced_points((0.0, 0.0), (0.01, 0.0), 0.025, 0.0)
    assert pts == [] and abs(carry - 0.01) < 1e-12, (pts, carry)
    pts, carry = bmath.spaced_points((0.01, 0.0), (0.03, 0.0), 0.025, carry)
    assert len(pts) == 1 and abs(pts[0][0] - 0.025) < 1e-12 and abs(carry - 0.005) < 1e-12, (pts, carry)


def _line_edges(n=10):
    """The inner edges of an n x n grid over 0-1 (UV segments a, b)."""
    a, b = [], []
    for i in range(1, n):
        for j in range(n):
            a += [(j / n, i / n), (i / n, j / n)]
            b += [((j + 1) / n, i / n), (i / n, (j + 1) / n)]
    return np.array(a), np.array(b)


def _cut(a, b, p0, p1, sensitivity=0.2, moves=30):
    stroke = bmath.CutStroke(p0)
    pick = bmath.CutPick(a, b)
    for k in range(1, moves + 1):
        stroke.add((p0[0] + (p1[0] - p0[0]) * k / moves, p0[1] + (p1[1] - p0[1]) * k / moves))
        pick.update(*stroke.take())
    pick.update(*stroke.take(final=True))
    hit = pick.picked(sensitivity, stroke.length)
    return sorted((round(float(x0), 3), round(float(y0), 3), round(float(x1), 3), round(float(y1), 3))
                  for (x0, y0), (x1, y1) in zip(a[hit], b[hit]))


def test_cut_stroke_snaps_to_the_nearest_edge_line():
    a, b = _line_edges()
    row = [(0.3, 0.5, 0.4, 0.5), (0.4, 0.5, 0.5, 0.5), (0.5, 0.5, 0.6, 0.5), (0.6, 0.5, 0.7, 0.5)]
    for off in (0.0, 0.02, 0.04, -0.04):
        assert _cut(a, b, (0.25, 0.5 + off), (0.75, 0.5 + off)) == row, f"a stroke {off} off the edges cuts them"
    up = _cut(a, b, (0.25, 0.56), (0.75, 0.56))
    assert up == [(x0, 0.6, x1, 0.6) for x0, _y, x1, _y2 in row], f"0.06 off: the next edge line ({up})"
    side = _cut(a, b, (0.5, 0.25), (0.5, 0.75))
    assert side == [(0.5, 0.3, 0.5, 0.4), (0.5, 0.4, 0.5, 0.5), (0.5, 0.5, 0.5, 0.6), (0.5, 0.6, 0.5, 0.7)], side


def test_cut_sensitivity_is_the_part_of_an_edge_left_out():
    a, b = _line_edges()
    assert len(_cut(a, b, (0.25, 0.5), (0.75, 0.5), 0.2)) == 4, "the half-covered end edges are not cut at 0.2"
    assert len(_cut(a, b, (0.25, 0.5), (0.75, 0.5), 0.1)) == 4
    assert len(_cut(a, b, (0.25, 0.5), (0.75, 0.5), 0.5)) == 6, "at 0.5 the half-covered end edges are cut too"
    assert len(_cut(a, b, (0.215, 0.5), (0.785, 0.5), 0.2)) == 6, "an end edge covered 85 % is cut at 0.2"


def test_short_cut_stroke_cuts_nothing():
    a, b = _line_edges()
    for ln in (0.03, 0.1, 0.12):
        assert _cut(a, b, (0.5, 0.5), (0.5 + ln, 0.5)) == [], ln
    assert _cut(a, b, (0.5, 0.5), (0.65, 0.5)) == [(0.5, 0.5, 0.6, 0.5)]


# --- on a mesh ---------------------------------------------------------------------------------------

def test_pin_brush_pins_inside_only_and_ctrl_unpins():
    ob = _grid()
    m = _mesh(ob)
    centre, r = (0.5, 0.5), 0.15
    assert brush.apply_dab("PIN", m, centre, r, 1.0)
    inside = bmath.in_brush(m.U, centre, r)
    assert inside.any() and not inside.all()
    bm = m.bm
    for i, ls in enumerate(m.loops):
        assert all(l[m.uv].pin_uv == bool(inside[i]) for l in ls), i
    m2 = _mesh(ob)
    assert brush.apply_dab("PIN", m2, centre, 0.06, 1.0, invert=True)
    small = bmath.in_brush(m2.U, centre, 0.06)
    assert small.any()
    for i, ls in enumerate(m2.loops):
        assert all(l[m2.uv].pin_uv == bool(inside[i] and not small[i]) for l in ls), i
    assert bm.is_valid


def _jitter(ob, amount=0.02, seed=5):
    """Move every inner UV of the grid by a random amount (uneven distortion)."""
    bpy.ops.object.mode_set(mode='OBJECT')
    rng = np.random.default_rng(seed)
    uvl = ob.data.uv_layers.active.data
    off = {}
    for loop in ob.data.loops:
        d = uvl[loop.index]
        if 0.01 < d.uv[1] < 0.99 and 0.01 < d.uv[0] < 0.49:
            o = off.setdefault(loop.vertex_index, rng.uniform(-amount, amount, 2))
            d.uv = (d.uv[0] + o[0], d.uv[1] + o[1])
    bpy.ops.object.mode_set(mode='EDIT')


def _select(ob, pred):
    """Select the vertices (UV sync on) whose UV point passes ``pred(u, v)``."""
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.active
    for v in bm.verts:
        v.select_set(False)
    for f in bm.faces:
        for l in f.loops:
            if pred(*l[uv].uv):
                l.vert.select_set(True)
    bm.select_flush_mode()
    bmesh.update_edit_mesh(ob.data)


def _relax_case(mode):
    ob = _grid(squash=0.5)
    _jitter(ob)
    m = _mesh(ob)
    m.write_pins(bmath.in_brush(m.U, (0.25, 0.5), 0.05))     # a pinned spot under the brush
    pinned0 = m.U[m.pinned].copy()
    centre, r = (0.25, 0.5), 0.2
    inside = bmath.in_brush(m.U, centre, r)
    before = _distortion(m)
    for _ in range(8):
        brush.apply_dab(mode, m, centre, r, 0.5, surfangle=1.0)
    m2 = _mesh(ob)
    assert np.allclose(m2.U[~inside], m.U0[~inside], atol=1e-9), f"{mode}: UVs outside the brush moved"
    assert np.allclose(m2.U[m2.pinned], pinned0, atol=1e-9), f"{mode}: pinned UVs moved"
    assert np.abs(m2.U[inside] - m.U0[inside]).max() > 1e-3, f"{mode}: nothing under the brush moved"
    return before, _distortion(m2)


def test_unfold_and_optimize_relax_under_the_brush_only():
    for mode in ("UNFOLD", "OPTIMIZE"):
        before, after = _relax_case(mode)
        assert after < before, (mode, before, after)


def test_unfold_and_optimize_move_only_selected_uvs():
    for mode in ("UNFOLD", "OPTIMIZE"):
        ob = _grid(squash=0.5)
        _jitter(ob)
        _select(ob, lambda u, v: u < 0.22)
        m = _mesh(ob)
        assert m.selected.any() and not m.selected.all()
        held = brush.relax_held([m])[0]
        assert held[~m.selected].all() and not held[m.selected].all()
        for _ in range(6):
            brush.apply_dab(mode, m, (0.22, 0.5), 0.2, 0.5, held=held)
        m2 = _mesh(ob)
        assert np.allclose(m2.U[~m.selected], m.U0[~m.selected], atol=1e-9), f"{mode}: unselected UVs moved"
        assert np.abs(m2.U[m.selected] - m.U0[m.selected]).max() > 1e-3, f"{mode}: no selected UV moved"
        _select(ob, lambda u, v: False)
        m3 = _mesh(ob)
        assert not brush.relax_held([m3])[0].any(), "with nothing selected the brush works on every UV"


def test_relax_whole_shell_keeps_area():
    ob = _grid(squash=0.5, n=6)
    m = _mesh(ob)
    area0 = abs(np.cross(m.U[m.T[:, 1]] - m.U[m.T[:, 0]], m.U[m.T[:, 2]] - m.U[m.T[:, 0]])).sum()
    brush.apply_dab("OPTIMIZE", m, (0.25, 0.5), 1000.0, 1.0)     # the whole shell under the brush centre
    area1 = abs(np.cross(m.U[m.T[:, 1]] - m.U[m.T[:, 0]], m.U[m.T[:, 2]] - m.U[m.T[:, 0]])).sum()
    assert abs(area1 - area0) < 1e-4 * area0, (area0, area1)
    assert np.abs(m.U - m.U0).max() > 1e-3, "the squashed shell relaxed"


def test_cut_stroke_splits_the_shell_and_sew_joins_it():
    ob = _grid(n=4)
    m = _mesh(ob)
    pick = brush.cut_pick(m)
    stroke = bmath.CutStroke((0.02, 0.53))
    for x in np.linspace(0.02, 0.98, 60)[1:]:      # along the middle row of edges (v = 0.5), a little off it
        stroke.add((x, 0.53))
        pick.update(*stroke.take())
    pick.update(*stroke.take(final=True))
    picked = brush.cut_edges(pick, 0.2, stroke.length)
    assert len(picked) == 4, picked
    assert brush.finish_edges("CUT", m, picked) == 4
    bmesh.update_edit_mesh(ob.data)
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.active
    assert len(uv_tools.islands(bm, uv, list(bm.faces), seams=True)) == 2
    m = _mesh(ob)
    picked = set()
    for x in np.linspace(0.02, 0.98, 30):
        brush.collect_sew_edges(m, (x, 0.5), 0.04, picked)
    assert len(picked) == 4, picked
    assert brush.finish_edges("SEW", m, picked) == 4
    bmesh.update_edit_mesh(ob.data)
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.active
    assert len(uv_tools.islands(bm, uv, list(bm.faces))) == 1
    assert not any(e.seam for e in bm.edges)


def test_sew_picks_only_borders_under_the_brush():
    ob = _grid(n=4)
    m = _mesh(ob)
    picked = set()
    brush.collect_sew_edges(m, (0.5, 0.5), 0.04, picked)
    assert not picked, "no shell border inside the shell"


def test_smear_and_smudge_on_a_mesh():
    ob = _grid()
    m = _mesh(ob)
    centre, r = (0.5, 0.5), 0.15
    outside = ~bmath.in_brush(m.U, centre, r)
    brush.apply_dab("SMEAR", m, centre, r, 0.5, delta=(0.02, 0.0))
    m2 = _mesh(ob)
    assert np.allclose(m2.U[outside], m.U0[outside]) and (m2.U[:, 0] - m.U0[:, 0]).max() > 0.009
    w = bmath.grab_weights(m2.U, centre, r, only=m2.U[:, 1] > 0.5)
    brush.apply_dab("SMUDGE", m2, centre, r, 1.0, delta=(0.0, 0.03), weights=w)
    m3 = _mesh(ob)
    lower = m2.U0[:, 1] <= 0.5
    assert np.allclose(m3.U[lower], m2.U0[lower]), "Smudge moves only the selected UVs"
    assert (m3.U[:, 1] - m2.U0[:, 1]).max() > 0.002


def test_smudge_fixed_follows_with_a_steep_falloff_selected_only():
    U = np.array([[0.45, 0.5], [0.5, 0.5], [0.45, 0.55], [0.4, 0.45], [0.6, 0.5]])
    sel = np.ones(len(U), bool)
    w = bmath.grab_weights(U, (0.45, 0.5), 0.075, only=sel)
    assert abs(w[0] - 1) < 1e-12, "the UV under the press follows the mouse fully"
    assert 0.07 < w[1] < 0.14 and 0.07 < w[2] < 0.14, f"0.05 away about a tenth {w}"
    assert w[3] < 0.02 and w[4] == 0.0, w
    none = bmath.grab_weights(U, (0.45, 0.5), 0.075, only=np.zeros(len(U), bool))
    assert not none.any(), "with no UV selected Smudge moves nothing"
    out = bmath.smudge(U, (0.45, 0.5), 0.075, (0.005, 0.0), 0.01, only=sel)
    assert abs(out[0, 0] - 0.45 - 0.00005) < 1e-12, "Smudge effect: each move pulls by the Pressure"
    assert np.allclose(bmath.smudge(U, (0.45, 0.5), 0.075, (0.005, 0.0), 0.01, only=~sel), U)


# --- tools, keys, menus ------------------------------------------------------------------------------

def test_tools_registered_with_keys():
    from bl_ui.space_toolsystem_common import ToolSelectPanelHelper
    cls = ToolSelectPanelHelper._tool_class_from_space_type('IMAGE_EDITOR')
    ids = [it.idname for it, _i in ToolSelectPanelHelper._tools_flatten_with_tool_index(
        cls.tools_from_context(bpy.context, 'UV')) if it is not None]
    for label in LABELS:
        tid = brush.TOOL_IDS[label.upper()]
        assert tid in ids, (tid, ids)
        km = bpy.context.window_manager.keyconfigs.addon.keymaps.get(f"Image Editor Tool: Uv, {label}")
        assert km is not None, label
        got = {(k.type, k.ctrl, k.idname, getattr(k.properties, "mode", None) if k.idname.endswith("stroke") else
                getattr(k.properties, "binding", None)) for k in km.keymap_items}
        if label == "Cut":          # Ctrl / Shift + drag with the Cut tool does nothing
            assert any(k.type == 'LEFTMOUSE' and k.shift and k.properties.invert for k in km.keymap_items), label
        want = {('LEFTMOUSE', False, "allset.uv_brush_stroke", label.upper()),
                ('LEFTMOUSE', True, "allset.uv_brush_stroke", label.upper()),
                ('B', False, "allset.tap_hold", "uv_brush_size"), ('M', False, "allset.tap_hold", "uv_brush_strength")}
        assert want <= got, (label, got)
    assert taphold.get_binding("uv_brush_size") and taphold.get_binding("uv_brush_strength")


def test_settings_defaults():
    s = bpy.context.scene.allset_uv_brush
    assert (round(s.relax_size, 6), round(s.relax_strength, 6), round(s.surfangle, 6)) == (0.1, 0.5, 1.0)
    assert (round(s.cut_sensitivity, 6), round(s.sew_size, 6)) == (0.2, 0.04)
    assert (round(s.pin_size, 6), round(s.pin_strength, 6)) == (0.1, 100.0)
    assert (round(s.smear_size, 6), round(s.smear_strength, 6)) == (0.1, 0.05)
    assert (round(s.smudge_size, 6), round(s.smudge_pressure, 6), s.smudge_effect, s.smudge_falloff) == \
        (0.075, 0.01, 'FIXED', 'EXPONENTIAL')
    assert (s.lattice_columns, s.lattice_rows) == (3, 3)


def test_menu_items_set_the_tools():
    for label in LABELS:
        path = f"UV Editor/Tools/{label}"
        act = editor_map.MAP.get(path) if hasattr(editor_map, "MAP") else None
        act = act or menu_map.MAP.get(path)
        assert act == ("wm.tool_set_by_id", {"name": brush.TOOL_IDS[label.upper()], "space_type": 'IMAGE_EDITOR'}), \
            (path, act)
        assert path not in menu_map.TWINS, path
    tools_sub = dict(e for e in menus.MENUS["SHIFT_UV"].items if e != menus.DIVIDER)["Tools"]
    got = dict(e for e in tools_sub.items if e != menus.DIVIDER)
    assert got["Smear Tool"] == ("item", "UV Editor/Tools/Smear"), got["Smear Tool"]
    assert got["Lattice Tool"] == ("item", "UV Editor/Tools/Lattice"), got["Lattice Tool"]


def test_brush_marking_menu():
    """RMB with a brush tool: Maya's brush marking menu (Invert Pin, Cut / Grab / Pin UV Tool, Last Tool)."""
    m = menus.MENUS["UV_BRUSH"]
    got = {pos: (label, action) for pos, (label, action) in m.radial.items()}
    assert got["N"] == ("Invert Pin", ("allset.uv_invert_pin", {})), got["N"]
    assert got["NE"] == ("Cut UV Tool", ("item", "UV Editor/Tools/Cut")), got["NE"]
    assert got["SE"] == ("Grab UV Tool", ("item", "UV Editor/Tools/Grab")), got["SE"]
    assert got["S"] == ("Pin UV Tool", ("item", "UV Editor/Tools/Pin")), got["S"]
    assert got["E"][1] == ("allset.uv_brush_last", {}) and got["W"][0] == "Falloff Type"
    ob = _grid(n=4)
    m = _mesh(ob)
    m.write_pins(m.U[:, 0] < 0.3)
    bmesh.update_edit_mesh(ob.data)
    assert bpy.ops.allset.uv_invert_pin() == {'FINISHED'}
    m2 = _mesh(ob)
    assert list(m2.pinned) == list(m2.U[:, 0] >= 0.3)


def test_lattice_math_and_mesh():
    rect = (0.0, 0.0, 1.0, 1.0)
    U = np.random.default_rng(1).uniform(0, 1, (50, 2))
    st = lattice.params(U, rect)
    for n in (2, 3, 4, 6):
        assert np.allclose(lattice.deform(lattice.grid(rect, n, n), st), U), f"an untouched {n} x {n} lattice"
    pts = lattice.grid(rect, 3, 3)
    pts[0, 0] += (-0.1, -0.1)                     # the bottom-left point
    out = lattice.deform(pts, st)
    w = (1 - U[:, 0]) ** 2 * (1 - U[:, 1]) ** 2      # its quadratic Bernstein weight
    assert np.allclose(out - U, -0.1 * w[:, None]), "a lattice point pulls every UV by its Bezier weight"
    far = (U[:, 0] > 0.5) & (U[:, 1] > 0.5)
    assert np.abs(out[far] - U[far]).max() > 1e-4, "the whole lattice bends, not only the corner cell"
    ob = _grid(n=4)
    bm = bmesh.from_edit_mesh(ob.data)
    for v in bm.verts:
        v.select_set(v.co.x > 0.1)                 # the right half
    bm.select_flush_mode()
    m = _mesh(ob)
    lat = lattice.Lattice([m], 3, 3)
    assert lat.ok and abs(lat.rect[0] - 0.75) < 0.01 and lat.rect[2] > 0.99, lat.rect
    lat.pts[-1, -1] += (0.1, 0.1)
    assert lat.apply([m])
    m2 = _mesh(ob)
    assert np.allclose(m2.U[~m2.selected], m.U0[~m.selected]), "UVs outside the selection stay"
    assert lat.matches([m2], 3, 3) and not lat.matches([m2], 4, 3)
