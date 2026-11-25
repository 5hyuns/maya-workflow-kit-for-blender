"""#498: UV Editor > Modify > Optimize evens out the UV distortion like Maya's Optimize (not Blender's Minimize
Stretch) and opens the Optimize UVs Options window; the saved settings drive the menu item, the UV Toolkit button and
the marking menu items.

Like Maya: the selected UVs relax against the 3D surface, unselected and pinned UVs stay, the shell border is free,
a fully selected shell keeps its UV area and one of its UVs stays in place; an evenly squashed shell comes back undistorted in one iteration, more
iterations relax more; Power below 100 or 0 iterations change nothing; nothing selected = nothing happens."""

import inspect
import math
import random
from importlib import import_module

import bmesh
import bpy

import kit

ow = import_module(kit.MODULE + ".operators.option_windows")
box = import_module(kit.MODULE + ".ui.menu_option_box")
menu_map = import_module(kit.MODULE + ".ui.menu_map")
marking = import_module(kit.MODULE + ".marking.menus")
opt_math = import_module(kit.MODULE + ".operators.uv_optimize_math")

OPTIMIZE = "UV Editor/Modify/Optimize"


def _reset():
    ow.store("uv_optimize", None)
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)


def _grid(name="grid", x=0.0, uv_fn=None):
    """A 10 x 10 face grid (2 x 2 units) whose UVs fill 0-1, changed by ``uv_fn(u, v) -> (u, v)`` per UV."""
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=10, y_subdivisions=10, size=2, location=(x, 0, 0),
                                    calc_uvs=True)
    ob = bpy.context.active_object
    ob.name = name
    if uv_fn is not None:
        seen = {}
        for loop in ob.data.loops:
            d = ob.data.uv_layers.active.data[loop.index]
            key = loop.vertex_index
            if key not in seen:
                seen[key] = uv_fn(d.uv[0], d.uv[1], key)
            d.uv = seen[key]
    return ob


def _edit(*obs, select_all=True):
    for o in bpy.context.view_layer.objects:
        o.select_set(o in obs)
    bpy.context.view_layer.objects.active = obs[0]
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.scene.tool_settings.use_uv_select_sync = True
    bpy.ops.mesh.select_mode(type='FACE')
    bpy.ops.mesh.select_all(action='SELECT' if select_all else 'DESELECT')


def _bm(ob):
    bm = bmesh.from_edit_mesh(ob.data)
    return bm, bm.loops.layers.uv.active


def _uv_by_vert(ob):
    bm, uv = _bm(ob)
    return {l.vert.index: l[uv].uv.copy() for f in bm.faces for l in f.loops}


def _uv_area(ob):
    bm, uv = _bm(ob)
    total = 0.0
    for f in bm.faces:
        ps = [l[uv].uv for l in f.loops]
        for i in range(1, len(ps) - 1):
            a, b = ps[i] - ps[0], ps[i + 1] - ps[0]
            total += abs(a.x * b.y - a.y * b.x) / 2
    return total


def _distortion(ob):
    """Area-weighted mean |log(s1 / s2)| of the 3D -> UV map over the triangles (0 = no angle distortion)."""
    bm, uv = _bm(ob)
    num = den = 0.0
    for tri in bm.calc_loop_triangles():
        p = [l.vert.co for l in tri]
        q = [l[uv].uv for l in tri]
        e1, e2 = p[1] - p[0], p[2] - p[0]
        ex = e1.normalized()
        n = e1.cross(e2)
        if n.length < 1e-12:
            continue
        ey = n.normalized().cross(ex)
        x1, x2, y2 = e1.length, e2.dot(ex), e2.dot(ey)
        f1, f2 = q[1] - q[0], q[2] - q[0]
        # J = F @ inv(E), E = [[x1, x2], [0, y2]]
        a, c = f1.x / x1, f1.y / x1
        b, d = (f2.x - a * x2) / y2, (f2.y - c * x2) / y2
        s = a * a + b * b + c * c + d * d
        det = abs(a * d - b * c)
        root = math.sqrt(max(s * s / 4 - det * det, 0.0))
        s1, s2 = math.sqrt(s / 2 + root), math.sqrt(max(s / 2 - root, 1e-30))
        w = n.length / 2
        num += w * abs(math.log(s1 / s2))
        den += w
    return num / den


def _flipped(ob):
    bm, uv = _bm(ob)
    out = 0
    for tri in bm.calc_loop_triangles():
        a, b, c = (l[uv].uv for l in tri)
        if (b - a).x * (c - a).y - (b - a).y * (c - a).x <= 0:
            out += 1
    return out


def _squash(u, v, _i):
    return (u * 0.5, v)


def _jitter(amount, seed=3):
    rnd = random.Random(seed)

    def fn(u, v, _i):
        if min(u, v) < 1e-6 or max(u, v) > 1 - 1e-6:
            return (u, v)          # the border stays a square
        return (u + rnd.uniform(-amount, amount), v + rnd.uniform(-amount, amount))
    return fn


def _run(**values):
    v = {**ow.current("uv_optimize"), **values}
    return bpy.ops.allset.opt_uv_optimize('EXEC_DEFAULT', **v)


def test_window_opens_from_the_option_box_and_the_items_run_optimize():
    w = ow.find_path(OPTIMIZE)
    assert w is not None and w.key == "uv_optimize" and w.action == "Optimize" and w.title == "Optimize UVs Options"
    assert box.option_kind(OPTIMIZE) == "window"
    assert {k: w.defaults()[k] for k in ("method", "iterations", "surfangle", "power", "prevent_flips")} ==         {"method": "Unfold3D", "iterations": 1, "surfangle": 1.0, "power": 100, "prevent_flips": True}, w.defaults()
    assert w.missing, "fields Blender has no counterpart for are listed greyed"
    spec = menu_map.spec(OPTIMIZE)
    assert spec is not None and spec[1] == "allset.uv_optimize", spec
    # the marking menu items reach the same menu path (so the same command and option window)
    assert inspect.getsource(marking).count('_uve("Modify/Optimize")') >= 3, "the Shift+RMB menus hold the menu item"


def test_evenly_squashed_shell_comes_back_undistorted_keeping_area_and_one_uv():
    _reset()
    ob = _grid(uv_fn=_squash)
    _edit(ob)
    before = _uv_by_vert(ob)
    area0 = _uv_area(ob)
    assert _distortion(ob) > 0.5
    assert bpy.ops.allset.menu_item(item=OPTIMIZE) == {'FINISHED'}
    assert _distortion(ob) < 1e-3, _distortion(ob)
    assert abs(_uv_area(ob) - area0) < 1e-5, (area0, _uv_area(ob))
    after = _uv_by_vert(ob)
    bm, _uv = _bm(ob)
    bm.faces.ensure_lookup_table()
    first = bm.faces[0].loops[0].vert.index
    assert (after[first] - before[first]).length < 1e-6, "one UV of the free shell (its first) stays in place"
    assert sum((after[i] - before[i]).length < 1e-6 for i in before) == 1
    border = [i for i in before if min(before[i]) < 1e-6 and i != first]
    assert max((after[i] - before[i]).length for i in border) > 0.05, "the shell border moves too (not pinned)"
    assert _flipped(ob) == 0


def test_more_iterations_relax_more():
    _reset()
    errs = []
    for it in (1, 3):
        ob = _grid(uv_fn=_jitter(0.03))
        _edit(ob)
        e0 = _distortion(ob)
        assert _run(iterations=it) == {'FINISHED'}
        errs.append(_distortion(ob))
        _reset()
    assert errs[0] < e0 * 0.5, (e0, errs)
    assert errs[1] < errs[0] * 0.5, errs


def test_unselected_and_pinned_uvs_stay():
    _reset()
    ob = _grid(uv_fn=_jitter(0.03))
    _edit(ob, select_all=False)
    bm, uv = _bm(ob)
    left = [f for f in bm.faces if f.calc_center_median().x < 0]
    for f in left:
        f.select_set(True)
    for f in bm.faces:            # pin the UVs of the lowest face row
        if f.calc_center_median().y < -0.8:
            for l in f.loops:
                l[uv].pin_uv = True
    bmesh.update_edit_mesh(ob.data)
    free = {l.vert.index for f in left for l in f.loops}
    pinned = {l.vert.index for f in bm.faces for l in f.loops if l[uv].pin_uv}
    before = _uv_by_vert(ob)
    assert _run() == {'FINISHED'}
    after = _uv_by_vert(ob)
    moved = {i for i in before if (after[i] - before[i]).length > 1e-7}
    assert moved, "the selected UVs relax"
    assert moved <= free - pinned, sorted(moved - (free - pinned))[:10]
    assert any(i in moved for i in free if before[i].x > 0.49), "UVs shared with unselected faces are selected too"


def test_nothing_selected_power_below_100_and_no_iterations_change_nothing():
    _reset()
    ob = _grid(uv_fn=_squash)
    _edit(ob, select_all=False)
    before = _uv_by_vert(ob)
    assert bpy.ops.allset.uv_optimize() == {'CANCELLED'}
    bpy.ops.mesh.select_all(action='SELECT')
    assert _run(power=99) == {'FINISHED'}
    assert _run(iterations=0) == {'FINISHED'}
    after = _uv_by_vert(ob)
    assert all((after[i] - before[i]).length < 1e-9 for i in before)


def test_saved_values_drive_the_menu_item():
    _reset()
    ob = _grid(uv_fn=_squash)
    _edit(ob)
    ow.store("uv_optimize", {**ow.current("uv_optimize"), "power": 50})
    before = _uv_by_vert(ob)
    assert bpy.ops.allset.menu_item(item=OPTIMIZE) == {'FINISHED'}
    after = _uv_by_vert(ob)
    assert all((after[i] - before[i]).length < 1e-9 for i in before), "Power 50 (saved) leaves the UVs"
    ow.store("uv_optimize", None)
    assert bpy.ops.allset.menu_item(item=OPTIMIZE) == {'FINISHED'}
    assert _distortion(ob) < 1e-3


def test_each_shell_keeps_its_own_area_and_undistorted_shells_stay():
    _reset()
    a = _grid("a", 0.0, uv_fn=lambda u, v, i: (u * 0.2, v * 0.4))
    b = _grid("b", 3.0, uv_fn=lambda u, v, i: (0.5 + u * 0.3, v * 0.3))      # already undistorted
    _edit(a, b)
    area_a, area_b = _uv_area(a), _uv_area(b)
    before_b = _uv_by_vert(b)
    assert _run() == {'FINISHED'}
    assert abs(_uv_area(a) - area_a) < 1e-6 and abs(_uv_area(b) - area_b) < 1e-6
    assert _distortion(a) < 1e-3
    after_b = _uv_by_vert(b)
    assert all((after_b[i] - before_b[i]).length < 1e-6 for i in before_b)


def test_no_new_flips_on_a_strongly_tangled_shell():
    _reset()
    ob = _grid(uv_fn=_jitter(0.07, seed=11))
    _edit(ob)
    flips0 = _flipped(ob)
    e0 = _distortion(ob)
    assert _run(iterations=2) == {'FINISHED'}
    assert _flipped(ob) <= flips0, (flips0, _flipped(ob))
    assert _distortion(ob) < e0


def test_solver_reads_a_mirrored_shell_and_keeps_held_uvs():
    # the maths alone: a mirrored (flipped-over) squashed square relaxes to a mirrored square, held UVs stay put
    P = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0), (0.5, 0.5, 0)]
    U = [(0, 0), (-0.5, 0), (-0.5, 1), (0, 1), (-0.3, 0.6)]
    T = [(0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4)]
    out = opt_math.optimize(P, U, T, [False] * 5, iterations=30)
    sides = [math.dist(out[i], out[(i + 1) % 4]) for i in range(4)]
    assert max(sides) - min(sides) < 1e-3 and abs(math.dist(out[0], out[2]) - sides[0] * math.sqrt(2)) < 1e-3, out
    signed = sum(out[i][0] * out[(i + 1) % 4][1] - out[(i + 1) % 4][0] * out[i][1] for i in range(4)) / 2
    assert abs(signed + 0.5) < 1e-3, ("still mirrored, same UV area", signed)
    held = [True, False, False, False, False]
    out = opt_math.optimize(P, U, T, held, iterations=1)
    assert tuple(out[0]) == (0.0, 0.0)
    assert opt_math.optimize(P, U, T, [False] * 5, iterations=0).tolist() == [list(map(float, u)) for u in U]


def test_one_pinned_uv_does_not_hold_the_shell():
    """Like Maya, one pinned UV alone doesn't hold a fully selected shell: the shell relaxes as a free one, keeps its
    UV area and the mean of its UVs stays where it was (the pinned UV moves); two pinned UVs stay."""
    for pins in (1, 2):
        _reset()
        ob = _grid(uv_fn=_squash)
        _edit(ob)
        bm, uv = _bm(ob)
        bm.faces.ensure_lookup_table()
        corner = [bm.faces[0].loops[0], bm.faces[-1].loops[2]][:pins]
        pinned = {l.vert.index for l in corner}
        for f in bm.faces:
            for l in f.loops:
                if l.vert.index in pinned:
                    l[uv].pin_uv = True
        bmesh.update_edit_mesh(ob.data)
        before = _uv_by_vert(ob)
        area0 = _uv_area(ob)
        assert bpy.ops.allset.menu_item(item=OPTIMIZE) == {'FINISHED'}
        after = _uv_by_vert(ob)
        moved = [i for i in pinned if (after[i] - before[i]).length > 1e-6]
        if pins == 1:
            assert moved, "a single pinned UV moves with the shell"
            c0 = sum(before.values(), before[0] * 0) / len(before)
            c1 = sum(after.values(), after[0] * 0) / len(after)
            assert (c1 - c0).length < 1e-5, (c0, c1)
            assert abs(_uv_area(ob) - area0) < 1e-5 and _distortion(ob) < 1e-3
        else:
            assert not moved, moved
