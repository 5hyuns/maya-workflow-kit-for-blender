"""Issue #208: snapping in the Maya curve drawing tools (operators/curve_snap.py, operators/curve_draw.py).
Maya: hold C = the nearest curve / polygon edge under the cursor, hold V = the nearest CV / vertex / pivot on screen,
X = grid; middle-drag = move the last point; Blender's scene snapping (Status Line snap buttons) inverted by Ctrl.
GUI: tests/gui/gui_issue208_curve_snap.py."""

import math
import types
from importlib import import_module

import bpy
from mathutils import Matrix, Vector

import kit

cd = import_module(kit.MODULE + ".operators.curve_draw")
cs = import_module(kit.MODULE + ".operators.curve_snap")
cm = import_module(kit.MODULE + ".operators.curves_math")
curves_maya = import_module(kit.MODULE + ".operators.curves_maya")


def _view(eye, target, persp=True, w=800, h=600, fov=math.radians(50), ortho_size=10.0):
    eye, target = Vector(eye), Vector(target)
    fwd = (target - eye).normalized()
    up = Vector((0, 0, 1)) if abs(fwd.z) < 0.999 else Vector((0, 1, 0))
    right = fwd.cross(up).normalized()
    up = right.cross(fwd)
    view = (Matrix.Translation(eye) @ Matrix((right, up, -fwd)).transposed().to_4x4()).inverted()
    aspect, n, f = w / h, 0.1, 1000.0
    if persp:
        t = 1.0 / math.tan(fov / 2)
        proj = Matrix(((t / aspect, 0, 0, 0), (0, t, 0, 0), (0, 0, (f + n) / (n - f), 2 * f * n / (n - f)),
                       (0, 0, -1, 0)))
    else:
        s = ortho_size / 2
        proj = Matrix(((1 / (s * aspect), 0, 0, 0), (0, 1 / s, 0, 0), (0, 0, -2 / (f - n), -(f + n) / (f - n)),
                       (0, 0, 0, 1)))
    rv3d = types.SimpleNamespace(view_matrix=view, perspective_matrix=proj @ view, is_perspective=persp)
    return types.SimpleNamespace(width=w, height=h), rv3d


def _screen(region, rv3d, p):
    v = rv3d.perspective_matrix @ Vector((*p, 1.0))
    return ((v.x / v.w + 1) * region.width / 2, (v.y / v.w + 1) * region.height / 2)


def _clear():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for c in list(bpy.data.curves):
        bpy.data.curves.remove(c)
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)


def test_scene_snapping_modes_and_ctrl_inverts():
    assert cs.modes_of_elements({'VERTEX'}) == {cs.POINT}
    assert cs.modes_of_elements({'EDGE', 'GRID'}) == {cs.CURVE, cs.GRID}
    assert cs.modes_of_elements({'FACE_PROJECT', 'VOLUME'}) == {cs.SURFACE}
    # Blender: Ctrl while clicking inverts the snapping toggle
    assert cs.scene_modes(False, {'VERTEX'}, ctrl=False) == set()
    assert cs.scene_modes(False, {'VERTEX'}, ctrl=True) == {cs.POINT}
    assert cs.scene_modes(True, {'EDGE'}, ctrl=False) == {cs.CURVE}
    assert cs.scene_modes(True, {'EDGE'}, ctrl=True) == set()


def test_perspective_correct_segment_point():
    region, rv3d = _view((10, -12, 7), (0, 0, 0))
    a, b = Vector((-6, 4, 0)), Vector((5, -9, 3))       # strongly foreshortened
    for s in (0.0, 0.2, 0.5, 0.83, 1.0):
        target = a.lerp(b, s)
        p, d = cs.nearest_on_segments(_screen(region, rv3d, target), [a], [b], rv3d.perspective_matrix,
                                      region.width, region.height, 5.0)
        assert p is not None and d < 1e-3 and (Vector(p) - target).length < 1e-4, (s, p, tuple(target))


def test_curve_snap_lands_on_the_curve_near_the_cursor():
    region, rv3d = _view((8, -14, 9), (2, 0, 0))
    curve = cm.ep_curve([(0, 0, 0), (2, 3, 0), (4, 1, 1), (6, 4, 0)], 3)
    curve = (*curve, None)
    for u in (0.0, 0.37, 1.5, 2.9, 3.0):
        on = Vector(cm.evaluate(*curve[:3], u))
        mx, my = _screen(region, rv3d, on)
        p, pu, d = cs.nearest_on_curve((mx, my), curve, rv3d.perspective_matrix, region.width, region.height, 16)
        assert p is not None and (Vector(p) - on).length < 1e-4 and abs(pu - u) < 1e-3, (u, p, pu, tuple(on))
        # a few pixels off the curve: still a point exactly on the curve
        p, pu, d = cs.nearest_on_curve((mx + 3, my - 4), curve, rv3d.perspective_matrix, region.width,
                                       region.height, 16)
        assert p is not None and 0 < d <= 5.01
        assert (Vector(p) - Vector(cm.evaluate(*curve[:3], pu))).length < 1e-9
    # far from the curve: no snap (Maya snaps to the curve under the cursor)
    p, _u, _d = cs.nearest_on_curve((5, 5), curve, rv3d.perspective_matrix, region.width, region.height, 16)
    assert p is None


def test_periodic_curve_snap_stays_in_range():
    region, rv3d = _view((0, 0, 30), (0, 0, 0), persp=False, ortho_size=20)
    pts = [(math.cos(a) * 4, math.sin(a) * 4, 0) for a in (i * math.pi / 4 for i in range(8))]
    cvs = pts + pts[:3]
    knots = curves_maya._periodic_knots(len(pts), 3)
    assert len(knots) == len(cvs) + 2
    p, _u, _d = cs.nearest_on_curve(_screen(region, rv3d, (0, 3.6, 0)), (cvs, knots, 3, None),
                                    rv3d.perspective_matrix, region.width, region.height, 40)
    assert p is not None and abs(Vector(p).length - 3.6) < 0.5, p


def test_point_snap_picks_nearest_on_screen_anywhere():
    region, rv3d = _view((0, 0, 30), (0, 0, 0), persp=False, ortho_size=20)
    co = [(5, 5, 0), (-3, 2, 0), (1, -6, 4)]
    i = cs.nearest_point(_screen(region, rv3d, (-2.2, 1.0, 0)), co, rv3d.perspective_matrix, 800, 600)
    assert i == 1
    # V snaps to the nearest point even far from the cursor
    i = cs.nearest_point(_screen(region, rv3d, (9, -9, 0)), co, rv3d.perspective_matrix, 800, 600)
    assert i == 2
    assert cs.nearest_point((1, 1), [], rv3d.perspective_matrix, 800, 600) is None


def test_snap_to_order_and_misses():
    region, rv3d = _view((0, 0, 30), (0, 0, 0), persp=False, ortho_size=20)
    curve = (*cm.cv_curve([(-8, -2, 0), (-3, 4, 0), (3, -4, 0), (8, 2, 0)], 3), None)
    t = cs.Targets(points=[(9, 9, 0)], edge_a=[(-9, -9, 0)], edge_b=[(9, -9, 0)], curves=[curve])
    on = Vector(cm.evaluate(*curve[:3], 0.5))
    mouse = _screen(region, rv3d, on)
    pm = rv3d.perspective_matrix
    p = cs.snap_to(t, {cs.CURVE}, mouse, pm, 800, 600)
    assert p is not None and (p - on).length < 1e-4
    assert (cs.snap_to(t, {cs.POINT}, mouse, pm, 800, 600) - Vector((9, 9, 0))).length < 1e-9
    assert (cs.snap_to(t, {cs.POINT, cs.CURVE}, mouse, pm, 800, 600) - Vector((9, 9, 0))).length < 1e-9
    # a polygon edge under the cursor
    p = cs.snap_to(t, {cs.CURVE}, _screen(region, rv3d, (2, -9.05, 0)), pm, 800, 600)
    assert p is not None and (p - Vector((2, -9, 0))).length < 1e-6, p
    # nothing near: no curve snap (the caller places the point on the plane)
    assert cs.snap_to(t, {cs.CURVE}, _screen(region, rv3d, (0, 7, 0)), pm, 800, 600) is None
    assert cs.snap_to(t, {cs.GRID}, mouse, pm, 800, 600) is None
    assert cs.snap_to(t, {cs.SURFACE}, mouse, pm, 800, 600, surface=lambda m: (1, 2, 3)) == Vector((1, 2, 3))


def test_gather_reads_visible_curves_meshes_and_pivots():
    _clear()
    ctx = bpy.context
    ep = curves_maya.make_ep_curve(ctx, [Vector((0, 0, 0)), Vector((2, 3, 0)), Vector((4, 1, 0))], 3)
    me = bpy.data.meshes.new("m")
    me.from_pydata([(0, 0, 0), (1, 0, 0), (1, 1, 0)], [(0, 1), (1, 2)], [])
    ob = bpy.data.objects.new("tri", me)
    ctx.scene.collection.objects.link(ob)
    ob.location = (10, 0, 0)
    hidden = bpy.data.objects.new("hid", bpy.data.meshes.new("h"))
    ctx.scene.collection.objects.link(hidden)
    hidden.location = (50, 50, 50)
    hidden.hide_viewport = True
    ctx.view_layer.update()
    t = cs.gather(ctx)
    pts = {tuple(round(c, 6) for c in p) for p in t.points}
    assert (10.0, 0.0, 0.0) in pts and (11.0, 1.0, 0.0) in pts, pts          # vertices in world space + pivot
    assert (50.0, 50.0, 50.0) not in pts                                     # hidden objects are no target
    sp = ep.data.splines[0]
    cv0 = tuple(round(c, 6) for c in (ep.matrix_world @ sp.points[0].co.xyz))
    assert cv0 in pts                                                        # curve CVs
    assert len(t.curves) == 1 and len(t.edge_a) == 2
    # the gathered EP curve passes through its edit points: a curve snap at an end = the old curve's end
    region, rv3d = _view((0, 0, 30), (2, 1, 0), persp=False, ortho_size=12)
    p = cs.snap_to(t, {cs.CURVE}, _screen(region, rv3d, (4.02, 1.0, 0)), rv3d.perspective_matrix, 800, 600)
    assert p is not None and (p - Vector((4, 1, 0))).length < 1e-3, p
    _clear()


def test_drawing_move_last():
    d = cd.Drawing(cd.EP)
    assert not d.move_last((1, 1, 1))
    d.press((0, 0, 0))
    assert not d.move_last((5, 5, 5)) and d.points[-1] == Vector((0, 0, 0))   # LMB drag owns the point
    d.release()
    d.press((2, 0, 0))
    d.release()
    assert d.move_last((3, 4, 0)) and d.points == [Vector((0, 0, 0)), Vector((3, 4, 0))]


def test_status_names_the_snap_holds():
    for kind in (cd.CV, cd.EP, cd.ARC3, cd.ARC2):
        assert "X / C / V" in cd.STATUS[kind], kind
    assert cd.SNAP_KEYS == {'X': cs.GRID, 'C': cs.CURVE, 'V': cs.POINT}
