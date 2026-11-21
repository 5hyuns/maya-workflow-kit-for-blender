"""#435: Selection Constraint > Angle. A pick grows to the connected components whose normal is within the tolerance
of the picked one's (faces: face normal; edges / vertices: mean of their faces' normals), compared with the
picked component, never jumping over a steep fold; Maya's Shift / Ctrl / Ctrl+Shift rules; tolerance 0 = no change;
the Modeling Toolkit row and the tool option menus' Selection Constraints items set it."""

import math
from importlib import import_module

import bmesh
import bpy

import kit

sc = import_module(kit.MODULE + ".operators.sel_constraint")
menus = import_module(kit.MODULE + ".marking.menus")
notices = import_module(kit.MODULE + ".ui.notices")


def _strip(name, turns):
    """Faces along a polyline in the XY plane (width along Z), column i turning by turns[i - 1] degrees; face i
    lies between columns i and i + 1. Returns the object in Edit Mode."""
    pts, d, p = [(0.0, 0.0)], 0.0, (0.0, 0.0)
    for i in range(len(turns) + 1):
        if i > 0:
            d += math.radians(turns[i - 1])
        p = (p[0] + math.cos(d), p[1] + math.sin(d))
        pts.append(p)
    verts = [(x, y, z) for x, y in pts for z in (0.0, 1.0)]          # column c: 2c (z 0), 2c + 1 (z 1)
    faces = [(2 * c, 2 * c + 2, 2 * c + 3, 2 * c + 1) for c in range(len(pts) - 1)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    if bpy.context.object is not None and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for o in bpy.context.view_layer.objects.selected:
        o.select_set(False)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT')
    return ob


def _bm(ob):
    return bmesh.from_edit_mesh(ob.data)


def test_faces_against_the_picked_face():
    ob = _strip("smallConst", [1] * 12)
    bm = _bm(ob)
    assert sc.grow(bm, 'FACE', {0}, 5.0) == set(range(5))
    assert sc.grow(bm, 'FACE', {0}, 12.0) == set(range(12))
    bpy.ops.object.mode_set(mode='OBJECT')
    ob = _strip("flatThenTurn", [0, 0, 0, 1, 3, 6, 10, 15, 25, 35, 50, 70])
    bm = _bm(ob)
    for tol, last in ((5, 5), (12, 6), (30, 7), (80, 9)):
        assert sc.grow(bm, 'FACE', {0}, tol) == set(range(last + 1)), (tol, sorted(sc.grow(bm, 'FACE', {0}, tol)))
    bpy.ops.object.mode_set(mode='OBJECT')


def test_no_jump_over_a_fold():
    ob = _strip("backFlat", [0, 0, 40, -40, 0])
    assert sc.grow(_bm(ob), 'FACE', {0}, 30.0) == {0, 1, 2}
    bpy.ops.object.mode_set(mode='OBJECT')


def test_vertices_and_edges():
    # face normals 0, 0, 0, 5, 15, 30, 50, 80, 125 degrees from face 0
    ob = _strip("grow", [0, 0, 5, 10, 15, 20, 30, 45])
    bm = _bm(ob)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    cols = lambda vs: sorted({v // 2 for v in vs})       # noqa: E731
    assert cols(sc.grow(bm, 'VERT', {0}, 12.0)) == [0, 1, 2, 3, 4]       # column normals 0 0 0 2.5 10 | 22.5
    assert cols(sc.grow(bm, 'VERT', {0}, 30.0)) == [0, 1, 2, 3, 4, 5]    # 22.5 in, 40 out
    bm.edges.ensure_lookup_table()
    seed = next(e.index for e in bm.edges if {v.index for v in e.verts} == {0, 2})      # a long edge of face 0

    def mean_angle(e):
        n = sc._normal(e, 'EDGE')
        return math.degrees(bm.faces[0].normal.angle(n))
    for tol, inside, outside in ((12.0, 10.0, 15.0), (30.0, 22.5, 40.0)):
        got = sc.grow(bm, 'EDGE', {seed}, tol)
        angles = {round(mean_angle(bm.edges[i]), 1) for i in got}
        assert max(angles) >= inside - 0.1 and all(a <= tol for a in angles), (tol, sorted(angles))
        assert not any(round(mean_angle(e), 1) >= outside - 0.1 for e in bm.edges if e.index in got)
    bpy.ops.object.mode_set(mode='OBJECT')


def test_modifier_rules_and_tolerance_zero():
    ob = _strip("flatRun", [0, 0, 60, 0, 0])          # faces 0-2 flat, 3-5 flat at 60 degrees
    wm = bpy.context.window_manager
    wm.allset_sel_constraint = 'ANGLE'
    wm.allset_sel_constraint_angle = 0.0
    assert not sc.active(bpy.context)                  # tolerance 0 = picks stay as they are
    wm.allset_sel_constraint_angle = 10.0
    assert sc.active(bpy.context)
    bpy.context.scene.tool_settings.mesh_select_mode = (False, False, True)
    bm = _bm(ob)

    def pick(before, now, shift=False, ctrl=False):
        sc.write(ob, bm, 'FACE', before)
        _kind, snap = sc.snapshot(bpy.context)
        sc.write(ob, bm, 'FACE', now)
        sc.apply(bpy.context, 'FACE', snap, 10.0, shift, ctrl)
        return sc._selected(_bm(ob), 'FACE')
    assert pick({4}, {0}) == {0, 1, 2}                                   # plain click: replace
    assert pick({0, 1, 2}, {0, 1, 2, 4}, shift=True, ctrl=True) == {0, 1, 2, 3, 4, 5}    # Ctrl+Shift: add
    assert pick({0, 1, 2, 3, 4, 5}, {0, 1, 2, 3, 5}, ctrl=True) == {0, 1, 2}              # Ctrl: remove
    assert pick({0, 1, 2}, {0, 1, 2, 4}, shift=True) == {0, 1, 2, 3, 4, 5}                # Shift: toggle on
    assert pick({0, 1, 2, 3, 4, 5}, {1, 2, 3, 4, 5}, shift=True) == {3, 4, 5}             # Shift: toggle off
    wm.allset_sel_constraint = 'OFF'
    assert not sc.active(bpy.context)
    bpy.ops.object.mode_set(mode='OBJECT')


def test_menus_set_the_constraint():
    items = dict(menus._constraints())
    sub = items["Selection Constraints"]
    labels = [i[0] for i in sub.items]
    assert labels == ["Off", "Angle", "Border", "Edge Loop", "Edge Ring", "Shell", "UV Edge Loop"], labels
    angle = dict(sub.items)["Angle"]
    assert angle[0] == "wm.context_set_enum" and angle[1]["value"] == 'ANGLE'
    for label in ("Border", "Edge Loop", "Edge Ring", "Shell", "UV Edge Loop"):
        assert dict(sub.items)[label] is None
        assert f"OPT_MOVE/Selection Constraints/{label}" in notices.MARKING, label
    wm = bpy.context.window_manager
    bpy.ops.wm.context_set_enum(data_path="window_manager.allset_sel_constraint", value='ANGLE')
    assert wm.allset_sel_constraint == 'ANGLE'
    wm.allset_sel_constraint = 'OFF'


def test_marquee_over_a_flat_grid_is_quick():
    import time
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=80, y_subdivisions=80, size=10.0)
    ob = bpy.context.view_layer.objects.active
    bpy.ops.object.mode_set(mode='EDIT')
    bm = _bm(ob)
    seeds = {f.index for f in bm.faces}
    t0 = time.perf_counter()
    got = sc.grow(bm, 'FACE', seeds, 10.0)
    dt = time.perf_counter() - t0
    assert got == seeds
    assert dt < 2.0, dt                  # one region for every picked face of the same plane
    bpy.ops.object.mode_set(mode='OBJECT')
