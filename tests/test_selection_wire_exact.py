"""Thousands of selected objects keep the selection wire light without changing it: the matrices and depth offsets the
instanced draw uploads are exactly the single-precision values drawing one object at a time uploads, the array depth
offsets are bit for bit the earlier arithmetic, the whole-file reads of mode and type give each object's own answer,
finding the highlighted objects makes no Python object per object (no garbage collector runs from a redraw), and a
frame change only asks about the objects a redraw still uses."""

import gc
import math
import random
from importlib import import_module
from types import SimpleNamespace

import bpy
import numpy as np
from mathutils import Euler, Matrix, Vector

import kit

wire = import_module(kit.MODULE + ".ui.selection_wire")


def _clear():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    wire._batches.clear()
    wire._edges.clear()
    wire._corners.clear()
    wire._used.clear()
    wire._draws[0] = 0


def _perspective(fov=0.9, aspect=1.6, near=0.1, far=200.0):
    f = 1.0 / math.tan(fov / 2)
    return Matrix(((f / aspect, 0, 0, 0), (0, f, 0, 0),
                   (0, 0, (far + near) / (near - far), 2 * far * near / (near - far)), (0, 0, -1, 0)))


def _ortho(size=20.0, aspect=1.6, near=-100.0, far=100.0):
    return Matrix(((1 / (size * aspect), 0, 0, 0), (0, 1 / size, 0, 0), (0, 0, -2 / (far - near), -(far + near) / (far - near)),
                   (0, 0, 0, 1)))


def _view(eye=(6.0, -14.0, 5.0), target=(0.0, 0.0, 0.0)):
    eye = Vector(eye)
    rot = (Vector(target) - eye).to_track_quat('-Z', 'Y').to_matrix().to_4x4()
    return (Matrix.Translation(eye) @ rot).inverted()


def _bits(a):
    a = np.ascontiguousarray(a)
    return a.view(np.uint32 if a.dtype == np.float32 else np.uint64)


def test_projected_matrices_match_mathutils():
    """Each object's matrix in the instanced draw is bit for bit ``view.perspective_matrix @ object.matrix_world``, the
    matrix drawing it by itself uploads: scene objects (parents, rotations, tiny and huge scales) and random float
    matrices of every magnitude."""
    _clear()
    rng = random.Random(11)
    me = bpy.data.meshes.new("m")
    parent = None
    objs = []
    for i in range(300):
        ob = bpy.data.objects.new(f"o{i}", me)
        bpy.context.scene.collection.objects.link(ob)
        ob.parent = parent if i % 4 else None
        ob.location = (rng.uniform(-500, 500), rng.uniform(-500, 500), rng.uniform(-50, 50))
        ob.rotation_euler = Euler((rng.uniform(-7, 7), rng.uniform(-7, 7), rng.uniform(-7, 7)))
        ob.scale = tuple(rng.uniform(0.1, 9) * 10 ** rng.randint(-5, 5) for _ in range(3))
        objs.append(ob)
        parent = ob
    bpy.context.view_layer.update()
    worlds, ok = wire.world_matrices(objs)
    assert ok.all()
    bad = 0
    for pm in (_perspective() @ _view(), _ortho() @ _view((40, 30, 80)), _perspective(0.2, 0.7, 0.01, 1e5) @ _view()):
        got = wire.projected_matrices(pm, worlds)
        for ob, m in zip(objs, got):
            bad += not np.array_equal(_bits(np.array(pm @ ob.matrix_world, np.float32)), _bits(m))
    for _ in range(3000):
        a = Matrix([[rng.uniform(-1, 1) * 10 ** rng.randint(-8, 8) for _ in range(4)] for _ in range(4)])
        b = Matrix([[rng.uniform(-1, 1) * 10 ** rng.randint(-8, 8) for _ in range(4)] for _ in range(4)])
        got = wire.projected_matrices(a, np.array(b, np.float32)[None])[0]
        bad += not np.array_equal(_bits(np.array(a @ b, np.float32)), _bits(got))
    assert bad == 0, f"{bad} matrices differ from mathutils"


def _previous_biases(worlds, ok, boxes, projection, viewport):
    """The array depth offsets as computed before (one numpy reduction per row and axis): the reference."""
    width, height = viewport
    if not all(math.isfinite(v) and v > 0 for v in (width, height)):
        return np.zeros(len(boxes))
    n = len(boxes)
    ok = ok.copy()
    corners = np.array([[0.0] * 24 if b is None else b for b in boxes], np.float64).reshape(n, 8, 3)
    ok[[k for k, b in enumerate(boxes) if b is None]] = False
    pairs = [(i, j) for i in range(8) for j in range(i + 1, 8)]
    with np.errstate(all='ignore'):
        ok &= np.isfinite(corners).all(axis=(1, 2)) & np.isfinite(worlds).all(axis=(1, 2))
        clip = np.einsum('nij,nkj->nki', np.array(projection, np.float64) @ worlds,
                         np.concatenate((corners, np.ones((n, 8, 1))), axis=2))
        w, z = clip[..., 3], clip[..., 2]
        ok &= np.isfinite(clip).all(axis=(1, 2)) & (w > 1e-8).all(1) & (z > -w).all(1) & (z < w).all(1)
        xs, ys, depths = clip[..., 0] / w, clip[..., 1] / w, z / w
        ok &= np.isfinite(xs).all(1) & np.isfinite(ys).all(1) & np.isfinite(depths).all(1)
        span = depths.max(1) - depths.min(1)
        pixels = np.maximum(np.maximum(1.0, (xs.max(1) - xs.min(1)) * width * 0.5),
                            (ys.max(1) - ys.min(1)) * height * 0.5)
        ok &= np.isfinite(span) & np.isfinite(pixels) & (span > 0.0)
        bias = np.minimum(np.minimum(wire.DEPTH_BIAS, span * wire.DEPTH_BIAS_MAX_SPAN),
                          span * wire.DEPTH_BIAS_PIXELS / pixels)
        sizes = corners.max(1) - corners.min(1)
        lengths = np.sqrt(((worlds[:, :3, :3] * sizes[:, None, :]) ** 2).sum(axis=1))
        ok &= np.isfinite(lengths).all(1)
        longest = lengths.max(1)
        a = np.array([p[0] for p in pairs])
        b = np.array([p[1] for p in pairs])
        for axis in range(3):
            thin = np.flatnonzero((lengths[:, axis] > 0.0) & (lengths[:, axis] < longest * wire.DEPTH_BIAS_THIN_RATIO))
            if not thin.size:
                continue
            others = [i for i in range(3) if i != axis]
            c, d = corners[thin], depths[thin]
            along = ((c[:, a, axis] != c[:, b, axis])
                     & (c[:, a, others[0]] == c[:, b, others[0]])
                     & (c[:, a, others[1]] == c[:, b, others[1]]))
            found = along.any(1)
            ok[thin] &= found
            least = np.where(along, np.abs(d[:, a] - d[:, b]), np.inf).min(1)
            bias[thin] = np.where(found, np.minimum(bias[thin], least * wire.DEPTH_BIAS_THIN_SPAN), bias[thin])
    return np.where(ok, bias, 0.0)


def _box(lo, hi):
    return tuple(v for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2]) for v in (x, y, z))


def test_array_biases_are_the_previous_arithmetic():
    """The depth offset of many objects at once is bit for bit what it was: boxes, thin plates, flat cards, points,
    objects behind the eye or across a clip plane, unreadable or non-finite boxes and matrices, two views."""
    rng = np.random.default_rng(5)
    n = 2400
    worlds = np.zeros((n, 4, 4))
    boxes = []
    for k in range(n):
        rot = Euler(tuple(rng.uniform(-3.2, 3.2, 3))).to_matrix().to_4x4()
        scale = rng.choice([1.0, 0.02, 1e-4, 3.0, 0.0], size=3, p=[0.55, 0.15, 0.1, 0.15, 0.05])
        m = Matrix.Translation(tuple(rng.uniform(-40, 40, 3))) @ rot @ Matrix.Diagonal((*scale, 1.0))
        worlds[k] = np.array(m, np.float32)
        kind = k % 11
        if kind == 0:
            boxes.append(None)
        elif kind == 1:
            boxes.append(_box((-1, -1, 0), (1, 1, 0)))                       # a flat card
        elif kind == 2:
            boxes.append(_box((0, 0, 0), (0, 0, 0)))                         # a point (an empty)
        elif kind == 3:
            boxes.append(_box((-1, -1, -1e-3), (1, 1, 1e-3)))                # a thin plate
        elif kind == 4:
            boxes.append(_box((-1, -1, float('nan')), (1, 1, 1)))
        elif kind == 5:
            boxes.append(_box((-1, float('-inf'), -1), (1, 1, 1)))
        else:
            lo = tuple(float(v) for v in np.float32(rng.uniform(-3, 0, 3)))
            hi = tuple(float(v) for v in np.float32(rng.uniform(0, 3, 3)))
            boxes.append(_box(lo, hi))
    worlds[7] = np.nan
    worlds[8, 1, 3] = np.inf
    worlds[9, 2, 2] = -0.0
    ok = np.ones(n, bool)
    ok[10] = False
    objs = [None] * n
    positive = zero = capped = 0
    for pm in (_perspective(far=400.0) @ _view((6, -90, 30)), _ortho(60.0) @ _view((30, -60, 40)),
               _perspective(1.6, 1.0, 1.0, 30.0) @ _view()):
        for viewport in ((1280, 800), (37, 911), (0, 600)):
            wire._corners.clear()
            want = _previous_biases(worlds, ok, boxes, pm, viewport)
            got = wire._biases_array(objs, None, pm, viewport, boxes, None, (worlds, ok))
            assert np.array_equal(_bits(want), _bits(got)), (viewport, np.flatnonzero(_bits(want) != _bits(got))[:10])
            again = wire._biases_array(objs, None, pm, viewport, boxes, None, (worlds, ok))     # the kept corners
            assert np.array_equal(_bits(want), _bits(again))
            if viewport[0]:
                positive += (want > 0).sum()
                zero += (want == 0).sum()
                capped += ((want > 0) & (want < wire.DEPTH_BIAS)).sum()
    print(f"depth offsets compared: {positive} positive ({capped} below the limit), {zero} zero")
    assert positive > n and zero > n // 2 and capped > n // 4, "every kind of result is covered"


def test_some_rows_alone_are_the_rows_of_the_whole_set():
    """When only some objects moved, only their rows are computed again: the matrix and depth offset of rows computed
    alone (1, 2, 7, 300 rows, any of them) are bit for bit the ones the whole set gives them."""
    rng = np.random.default_rng(9)
    n = 1500
    worlds = np.zeros((n, 4, 4))
    boxes = []
    for k in range(n):
        rot = Euler(tuple(rng.uniform(-3.2, 3.2, 3))).to_matrix().to_4x4()
        scale = rng.choice([1.0, 0.03, 2.5], size=3)
        m = Matrix.Translation(tuple(rng.uniform(-30, 30, 3))) @ rot @ Matrix.Diagonal((*scale, 1.0))
        worlds[k] = np.array(m, np.float32)
        lo = tuple(float(v) for v in np.float32(rng.uniform(-2, 0, 3)))
        hi = tuple(float(v) for v in np.float32(rng.uniform(0, 2, 3)))
        boxes.append(None if k % 13 == 0 else _box(lo, hi))
    ok = np.ones(n, bool)
    pm = _perspective(far=400.0) @ _view((6, -70, 30))
    wire._corners.clear()
    corners, unread, homogeneous, finite, sizes = wire._corner_array(boxes)
    readable = ok.copy()
    readable[unread] = False
    full = wire._biases_rows(worlds, readable.copy(), corners, homogeneous, finite, sizes, pm, 1280, 800)
    whole = wire.projected_matrices(pm, worlds)
    assert (full > 0).sum() > n // 3
    for size in (1, 2, 7, 300):
        for _ in range(6):
            rows = np.sort(rng.choice(n, size, replace=False))
            got = wire._biases_rows(worlds[rows], readable[rows], corners[rows], homogeneous[rows], finite[rows],
                                    sizes[rows], pm, 1280, 800)
            assert np.array_equal(_bits(got), _bits(full[rows])), (size, rows[:5])
            assert np.array_equal(_bits(wire.projected_matrices(pm, worlds[rows])), _bits(whole[rows]))


def _view_space():
    return next(a.spaces.active for s in bpy.data.screens for a in s.areas if a.type == 'VIEW_3D')


def _ctx(space):
    c = bpy.context
    return SimpleNamespace(space_data=space, screen=None, view_layer=c.view_layer,
                           selected_objects=c.selected_objects, scene=c.scene)


def _objects_of_every_kind():
    me = bpy.data.meshes.new("m")
    me.from_pydata([(0, 0, 0), (1, 0, 0), (1, 1, 0)], [], [(0, 1, 2)])
    datas = [me, bpy.data.curves.new("c", 'CURVE'), bpy.data.curves.new("s", 'SURFACE'),
             bpy.data.curves.new("f", 'FONT'), bpy.data.metaballs.new("b"), bpy.data.lattices.new("l"),
             None, bpy.data.armatures.new("a"), bpy.data.cameras.new("cam"), bpy.data.lights.new("li", 'POINT'),
             bpy.data.hair_curves.new("h"), bpy.data.pointclouds.new("p"), bpy.data.volumes.new("v")]
    obs = []
    for i in range(130):
        ob = bpy.data.objects.new(f"k{i:03d}", datas[i % len(datas)])
        bpy.context.scene.collection.objects.link(ob)
        obs.append(ob)
    return obs


def test_whole_file_mode_and_type_reads_match_each_object():
    """Many selected objects: their mode and type come from two reads of the whole file, the same answers as asking
    each object (every object type; a mesh in Edit Mode and a skeleton in Pose Mode among them)."""
    _clear()
    obs = _objects_of_every_kind()
    bpy.context.view_layer.update()
    edit = next(o for o in obs if o.type == 'MESH')
    pose = next(o for o in obs if o.type == 'ARMATURE')
    for ob in obs:
        ob.select_set(True)
    try:
        for ob, mode in ((edit, 'EDIT'), (pose, 'POSE')):
            bpy.context.view_layer.objects.active = ob
            with bpy.context.temp_override(active_object=ob, object=ob, selected_objects=[ob]):
                bpy.ops.object.mode_set(mode=mode)
        sel = bpy.context.selected_objects
        assert len(sel) >= wire.ROOT_ARRAYS_FROM
        in_object, wire_type, _rows, found = wire._root_flags(sel, np.array([o.session_uid for o in sel], np.int64))
        assert found.all()
        assert in_object.tolist() == [o.mode == 'OBJECT' for o in sel]
        assert wire_type.tolist() == [o.type in wire.WIRE_TYPES for o in sel]
        assert not all(in_object) and any(in_object) and not all(wire_type) and any(wire_type)
        assert {o.type for o in sel} >= {'MESH', 'CURVE', 'SURFACE', 'FONT', 'META', 'LATTICE', 'EMPTY', 'ARMATURE',
                                         'CAMERA', 'LIGHT', 'CURVES', 'POINTCLOUD', 'VOLUME'}
    finally:
        for ob in (edit, pose):
            bpy.context.view_layer.objects.active = ob
            with bpy.context.temp_override(active_object=ob, object=ob, selected_objects=[ob]):
                bpy.ops.object.mode_set(mode='OBJECT')


def _rule(context):
    """The highlight rule written out plainly (each selected object in Object Mode and its unselected descendants, in
    the colour of the nearest selected ancestor; drawn when a wire type in Object Mode shown in the view)."""
    space, active = context.space_data, context.view_layer.objects.active
    out, seen = [], set()

    def visit(ob, lead):
        if ob.name in seen:
            return
        seen.add(ob.name)
        if ob.type in wire.WIRE_TYPES and ob.mode == 'OBJECT' and ob.visible_get(viewport=space):
            out.append((ob.name, lead))
        for child in ob.children:
            if not child.select_get():
                visit(child, lead)
    for ob in context.selected_objects:
        if ob.mode == 'OBJECT':
            visit(ob, ob == active)
    return out


def test_many_selected_objects_highlight_by_the_rule():
    """Many selected objects of every kind, with and without children under them: the objects that get the wire,
    their order and their colour follow the rule, whether the selected objects are known to be shown (a view's own
    redraw) or are asked."""
    _clear()
    obs = _objects_of_every_kind()
    bpy.context.view_layer.update()
    for ob in obs:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = obs[40]
    space = _view_space()
    for step in ("flat", "children"):
        if step == "children":
            kid = bpy.data.objects.new("kid", obs[0].data)
            bpy.context.scene.collection.objects.link(kid)
            kid.parent = obs[40]
            grand = bpy.data.objects.new("grand", obs[0].data)
            bpy.context.scene.collection.objects.link(grand)
            grand.parent = kid
            bpy.context.view_layer.update()
        ctx = _ctx(space)
        want = _rule(ctx)
        for shown in (True, False):
            objs, leads, uids = wire._highlight(ctx, roots_shown=shown)
            got = [(o.name, lead) for o, lead in zip(objs, leads)]
            assert got == want, (step, shown, got[:5], want[:5])
            assert uids == [o.session_uid for o in objs]
        assert sum(lead for _name, lead in want) == (1 if step == "flat" else 3), want


def test_finding_the_highlight_makes_no_object_per_selected_object():
    """2,000 selected objects: finding what gets the wire makes a handful of Python lists, not an object per selected
    object (thousands of short-lived tuples a redraw set off the garbage collector every few redraws, and its full
    collections took tens of milliseconds)."""
    _clear()
    me = bpy.data.meshes.new("m")
    me.from_pydata([(0, 0, 0), (1, 0, 0), (1, 1, 0)], [], [(0, 1, 2)])
    for i in range(2000):
        bpy.context.scene.collection.objects.link(bpy.data.objects.new(f"o{i:04d}", me))
    bpy.context.view_layer.update()
    for ob in bpy.context.view_layer.objects:
        ob.select_set(True)
    ctx = _ctx(_view_space())
    find = getattr(wire, "_highlight", None) or wire.highlighted
    find(ctx)
    was = gc.isenabled()
    gc.disable()
    try:
        before = gc.get_count()[0]
        got = find(ctx)
        made = gc.get_count()[0] - before
    finally:
        if was:
            gc.enable()
    count = len(got[0]) if isinstance(got, tuple) else len(got)
    print(f"highlight of {count} objects: {made} tracked Python objects made")
    assert count == 2000
    assert made < 50, f"{made} Python objects made for 2,000 selected objects"


def test_frame_change_asks_only_about_drawn_objects():
    """After a redraw, a frame change asks only about the objects that redraw drew: the batches no redraw used go (a
    let-go selection of thousands of objects was asked about on every frame of playback); a drawn object that can
    change with time still loses its batch and a static one keeps it. Without a redraw since the last frame change,
    every kept batch is asked about as before."""
    _clear()
    me = bpy.data.meshes.new("m")
    me.from_pydata([(0, 0, 0), (1, 0, 0), (1, 1, 0)], [], [(0, 1, 2)])
    obs = []
    for i in range(1000):
        ob = bpy.data.objects.new(f"o{i:04d}", me)
        bpy.context.scene.collection.objects.link(ob)
        obs.append(ob)
    bent = obs[3]
    bent.modifiers.new("bend", 'SIMPLE_DEFORM')
    bpy.context.view_layer.update()
    scene = bpy.context.scene
    real, asked = wire.time_dependent, []

    def counted(ob, *args):
        asked.append(ob.name)
        return real(ob, *args)
    wire.time_dependent = counted
    try:
        for ob in obs:
            wire._batches[ob.session_uid] = (None, 0, None)
        wire._used.update(o.session_uid for o in obs[:10])
        wire._draws[0] = 1
        wire._on_frame(scene)
        assert len(asked) == 10, f"{len(asked)} objects asked about, 10 drawn"
        assert set(wire._batches) == {o.session_uid for o in obs[:10]} - {bent.session_uid}
        assert not wire._used and wire._draws[0] == 0
        asked.clear()
        wire._on_frame(scene)                       # no redraw since: every kept batch is asked about
        assert len(asked) == 9 and len(wire._batches) == 9
    finally:
        wire.time_dependent = real
        _clear()


def test_shared_data_is_asked_once_with_the_same_answer():
    """A frame asks each object data shared by many objects once; the answer is each object's own (modifiers, shape
    keys, animated data, none)."""
    _clear()
    plain = bpy.data.meshes.new("plain")
    keyed = bpy.data.meshes.new("keyed")
    keyed.from_pydata([(0, 0, 0), (1, 0, 0), (1, 1, 0)], [], [(0, 1, 2)])
    animated = bpy.data.meshes.new("animated")
    animated.animation_data_create()
    obs = []
    for i in range(40):
        ob = bpy.data.objects.new(f"o{i}", (plain, keyed, animated, None)[i % 4])
        bpy.context.scene.collection.objects.link(ob)
        obs.append(ob)
    obs[1].shape_key_add(name="Basis")
    obs[4].modifiers.new("w", 'WAVE')
    memo = {}
    assert [wire.time_dependent(o, memo) for o in obs] == [wire.time_dependent(o) for o in obs]
    assert len(memo) == 3, memo
    assert any(wire.time_dependent(o) for o in obs) and not all(wire.time_dependent(o) for o in obs)
