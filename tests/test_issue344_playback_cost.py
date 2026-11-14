"""Issue #344: playback in Maya mode costs little more per frame than in Blender mode.

The two per-frame costs were the Maya joints of every skeleton (rebuilt every frame while the pose changes) and the
Range Slider bar (it found its gap by reading a header row every time the header redrew). Here:
- the joint lines drawn in Object / Pose Mode are the same lines and colours as the per-joint geometry picking uses
  (spheres, bone pyramids, sticks, custom shapes, local axes of selected joints, hidden bones left out), built
  without a Python object per joint per frame, and within a loose time budget;
- the Range Slider reads its header row once while playback runs and the header keeps its size, and on every
  redraw otherwise;
- controls (bones with a custom shape) draw their shapes where the per-control geometry puts them, every control at
  once: a shape is read once while playback runs unless it changes with the frame, and again after an edit;
- B-Bone and Envelope display build the same per-bone lines in arrays;
- 3D Views that show the same skeletons share one build of their lines per frame;
- with nothing selected the selection wire draws nothing at once, and the frame handlers don't look through every
  object each frame.
GUI: tests/gui/gui_issue344_playback_fps.py plays a heavy scene in both modes."""

import math
import time
from importlib import import_module
from types import SimpleNamespace

import bpy
import numpy as np
from mathutils import Quaternion, Vector

import kit

mj = import_module(kit.MODULE + ".ui.maya_joints")
joints = import_module(kit.MODULE + ".operators.joints")
cb = import_module(kit.MODULE + ".ui.channel_box")
rb = import_module(kit.MODULE + ".ui.range_bar")
compat = import_module(kit.MODULE + ".compat")


def _clear():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for arm in list(bpy.data.armatures):
        bpy.data.armatures.remove(arm)


def _rig(x=0.0, count=12):
    """A skeleton of ``count`` joints with branches (every fifth joint hangs from an earlier one)."""
    arm = joints.new_skeleton(bpy.context)
    made = [joints.add_joint(arm, Vector((x, 0, 0)), None, length=0.5)]
    for i in range(1, count):
        parent = made[(i - 1) // 2 if i % 5 == 0 else i - 1]
        made.append(joints.add_joint(arm, Vector((x + 0.3 * math.sin(i), 0.2 * (i % 3), 0.15 * i)), parent,
                                     length=0.1))
    joints.finish(bpy.context, arm, made)
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    return arm, made


def _pose(arm, k):
    for i, pb in enumerate(arm.pose.bones):
        pb.rotation_mode = 'XYZ'
        pb.rotation_euler = (0.1 * math.sin(k * 0.1 + i), 0.05 * i, 0.05 * k)
    bpy.context.view_layer.update()


def _animate(*rigs):
    """Keys on every joint at frames 1, 10 and 20, so a frame change (like playback) moves the joints."""
    for arm in rigs:
        for k in (1, 10, 20):
            for i, pb in enumerate(arm.pose.bones):
                pb.rotation_mode = 'XYZ'
                pb.rotation_euler = (0.1 * math.sin(k * 0.1 + i), 0.05 * i, 0.05 * k)
                pb.keyframe_insert("rotation_euler", frame=k)
    bpy.context.scene.frame_set(1)


def _rows(pts, cols):
    """Segments as rows (x0 y0 z0 x1 y1 z1 r g b a)."""
    if not len(pts):
        return np.zeros((0, 10))
    return np.concatenate((np.asarray(pts, np.float64).reshape(-1, 6),
                           np.asarray(cols, np.float64).reshape(-1, 2, 4)[:, 0]), axis=1)


def _gap(a, b):
    """Largest distance from a segment of ``a`` to its nearest one in ``b`` and back: 0 when both draw the same
    segments in the same colours, whatever their order."""
    if not len(a) or not len(b):
        return 0.0 if len(a) == len(b) else float("inf")
    d = np.abs(a[:, None, :] - b[None, :, :]).max(axis=2)
    return float(max(d.min(axis=1).max(), d.min(axis=0).max()))


def _reference(ob, perspective, stick=False):
    """What the view draws for ``ob``, joint by joint from the per-joint geometry (``skeleton``, ``sphere_lines``,
    ``bone_lines``, ``shape_lines``)."""
    scene = bpy.context.scene
    js = mj.skeleton(ob, scene)
    sel, lead = mj.selection(ob, js)
    col = mj.colours(js, sel, lead)
    dg = bpy.context.evaluated_depsgraph_get()
    pts, cols = [], []

    def add(segs, colour):
        pts.extend(tuple(v) for v in segs)
        cols.extend([(*colour, 1.0)] * len(segs))

    for n, j in js.items():
        if j.state == "HIDDEN":
            continue        # below a hidden joint (or in a hidden display layer): only its parent's bone to it
        if j.shape is not None:
            add(mj.shape_lines(j.shape[0], j.shape[1], dg), col[n])
            continue
        if not stick:
            add(mj.sphere_lines(j.centre, j.frame, j.radius), col[n])
        for cn in j.children:
            if js[cn].shape is None:
                add([j.centre, js[cn].centre] if stick else mj.bone_lines(j, js[cn]), col[n])
        if n in sel and perspective:
            for i in range(3):
                add([j.centre, j.centre + j.frame.col[i] * j.radius], mj.AXIS_COLORS[i])
    return _rows(pts, cols)


def _drawn(ob, perspective, stick=False, kind=None, playing=False):
    extra = dict(playing=True) if playing else {}
    if kind is not None:
        extra["kind"] = kind
    pts, cols = mj._fast_lines(ob, bpy.context.scene, perspective, bpy.context.evaluated_depsgraph_get(), stick,
                               **extra)
    if not pts:
        return _rows([], [])
    return _rows(np.concatenate(pts), np.concatenate(cols))


def _same(a, b, what):
    assert a.shape == b.shape, f"{what}: {len(a)} segments drawn, {len(b)} in the per-joint lines"
    err = _gap(a, b)
    assert err < 1e-4, f"{what}: drawn lines differ from the per-joint lines by {err}"


def _busy_rig():
    """A posed, turned, scaled skeleton with a hidden joint (the joints below it are hidden with it, like Maya), a
    joint in a hidden bone collection, a joint turned off its bone (Maya joint frame) and a control with a custom
    shape."""
    _clear()
    arm, names = _rig(count=14)
    arm.location = (0.5, -1.0, 0.25)
    arm.rotation_euler = (0.3, -0.2, 0.7)
    arm.scale = (1.5, 1.5, 1.5)
    bones = arm.data.bones
    compat.set_bone_hidden(arm.pose.bones[names[4]], True)
    hidden = arm.data.collections.new("hidden_joints")
    hidden.assign(bones[names[7]])
    hidden.is_visible = False
    bones[names[2]][joints.MAYA_FRAME] = tuple(Quaternion(Vector((0.3, 0.2, 0.9)).normalized(), 0.6))
    bones[names[3]][joints.RADIUS] = 2.5
    me = bpy.data.meshes.new("ctrl_shape")
    me.from_pydata([(1, 0, 0), (0, 1, 0), (-1, 0, 0), (0, -1, 0)], [(0, 1), (1, 2), (2, 3), (3, 0)], [])
    shape = bpy.data.objects.new("ctrl_shape", me)
    bpy.context.scene.collection.objects.link(shape)
    arm.pose.bones[names[9]].custom_shape = shape
    _pose(arm, 3)
    return arm, names


def test_joint_lines_are_the_per_joint_lines_in_object_mode():
    arm, _names = _busy_rig()
    arm.select_set(False)
    for persp in (True, False):
        _same(_drawn(arm, persp), _reference(arm, persp), f"Object Mode, nothing selected, perspective {persp}")
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    _same(_drawn(arm, True), _reference(arm, True), "Object Mode, skeleton selected (its root joints)")
    _same(_drawn(arm, True, stick=True), _reference(arm, True, stick=True), "Stick display")


def test_joint_lines_are_the_per_joint_lines_in_pose_mode():
    arm, names = _busy_rig()
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    bpy.ops.object.mode_set(mode='POSE')
    try:
        for pb in arm.pose.bones:
            cb.set_bone_selected(pb, pb.name in (names[1], names[5], names[9]))
        arm.data.bones.active = arm.data.bones[names[5]]
        for k in (0, 7):
            _pose(arm, k)
            drawn, ref = _drawn(arm, True), _reference(arm, True)
            _same(drawn, ref, f"Pose Mode, frame {k}: selected joints, lead, local axes")
            assert len(ref) and np.any(np.all(np.isclose(ref[:, 6:9], mj.LEAD), axis=1)), "the lead is drawn green"
    finally:
        bpy.ops.object.mode_set(mode='OBJECT')


def test_joint_arrays_follow_the_pose_like_the_joints():
    arm, _names = _busy_rig()
    js = mj.skeleton(arm, bpy.context.scene)
    got, names, parents, centres, frames, radii, shapes = mj._pose_arrays(arm, bpy.context.scene)
    assert names == list(js), "the same joints in the same order (hidden ones left out)"
    assert _names[4] not in names and _names[7] not in names, "a hidden joint and one in a hidden collection"
    for k, n in enumerate(names):
        j = js[n]
        assert (Vector(tuple(centres[k])) - j.centre).length < 1e-5, n
        assert max(abs(frames[k][r][c] - j.frame[r][c]) for r in range(3) for c in range(3)) < 1e-5, n
        assert abs(radii[k] - j.radius) < 1e-6, n
        assert (k in shapes) == (j.shape is not None), n
        assert (parents[k] >= 0 and names[parents[k]] == j.parent) or (parents[k] < 0 and j.parent not in js), n


def _view_context(objects):
    space = next(a.spaces.active for s in bpy.data.screens for a in s.areas if a.type == 'VIEW_3D')
    return SimpleNamespace(space_data=space, region_data=SimpleNamespace(is_perspective=True),
                           scene=bpy.context.scene, view_layer=bpy.context.view_layer, visible_objects=objects,
                           mode='OBJECT')


def test_playback_frame_builds_no_joint_objects_and_stays_in_budget():
    """Two 65-joint skeletons, a new pose every frame: the view's lines are built from arrays (no per-joint
    ``skeleton`` call) and stay far under a frame's time (budget loose for slow machines: 12 ms)."""
    _clear()
    rigs = [_rig(0.0, 65)[0], _rig(3.0, 65)[0]]
    ctx = _view_context(rigs)
    calls = []
    real = mj.skeleton
    mj.skeleton = lambda *a, **k: calls.append(1) or real(*a, **k)
    times = []
    try:
        for k in range(15):
            for r in rigs:
                _pose(r, k)
            t0 = time.perf_counter()
            pts, _cols = mj.view_lines(ctx)
            times.append(time.perf_counter() - t0)
    finally:
        mj.skeleton = real
    assert not calls, f"Object Mode joints built through skeleton() {len(calls)} times"
    assert len(pts) > 2 * 65 * 3 * mj.SEGMENTS * 2, "every joint's sphere is drawn"
    med = sorted(times)[len(times) // 2] * 1000
    print(f"joint lines of 2 x 65 joints: median {med:.2f} ms per frame")
    assert med < 12.0, f"joint lines take {med:.2f} ms per frame"


def test_joint_list_is_read_once_while_playing():
    """While playback runs the joints of a skeleton (names, parents, Radius, hidden ones, custom shapes) are read on
    the first frame and only the pose afterwards; an edit (depsgraph update, undo, a Radius typed) or a new playback
    reads them again, and outside playback every draw reads them."""
    arm, names = _busy_rig()
    _animate(arm)
    scene = bpy.context.scene
    mj._LISTS.clear()
    a = mj.joint_list(arm, playing=True)
    assert mj.joint_list(arm, playing=True) is a, "playing: the list is used again"
    first = None
    for f in (4, 15, 20):
        scene.frame_set(f)                              # a new frame: no depsgraph update, the pose moves
        pts, cols = mj._fast_lines(arm, scene, True, bpy.context.evaluated_depsgraph_get(), False, playing=True)
        drawn = _rows(np.concatenate(pts), np.concatenate(cols))
        _same(drawn, _reference(arm, True), f"playing, frame {f}")
        assert first is None or _gap(drawn, first) > 1e-3, "the joints move"
        first = drawn
    assert mj.joint_list(arm, playing=True) is a, "still the list of the first frame"
    scene.frame_set(1)
    mj.changed()
    b = mj.joint_list(arm, playing=True)
    assert b is not a, "an edit reads the joints again"
    mj._reload()
    assert mj.joint_list(arm, playing=True) is not b, "a new playback (or undo / load) reads them again"
    assert mj.joint_list(arm) is not mj.joint_list(arm), "not playing: every draw reads them"
    assert arm.as_pointer() not in mj._LISTS
    bones = arm.data.bones
    gen = mj._EDITS[0]
    bones[names[1]].allset_joint_radius = 3.0                 # the Channel Box / Attribute Editor Radius field
    assert mj._EDITS[0] > gen, "a typed Radius counts as an edit"


def test_joint_labels_follow_playback_and_edits():
    """Draw Label joints: while playing their names are found once and their places follow every frame; turning a
    label on (an edit) shows it at once, also while playing."""
    labels = import_module(kit.MODULE + ".operators.joint_labels")
    arm, names = _busy_rig()
    _animate(arm)
    scene = bpy.context.scene
    playing = SimpleNamespace(screen=SimpleNamespace(is_animation_playing=True), view_layer=bpy.context.view_layer)
    labels.set_label(arm.data.bones[names[3]], side=labels.LEFT, type=labels.T_KNEE, draw=True)
    labels._labelled.clear()
    try:
        for f in (2, 12):
            scene.frame_set(f)
            pts = labels.label_points(playing)
            want = arm.matrix_world @ arm.pose.bones[names[3]].head
            assert len(pts) == 1 and (pts[0][0] - want).length < 1e-6, f"frame {f}: the label follows its joint"
            assert pts[0][1] == labels.label_text(arm.data.bones[names[3]])
        cached = labels._labelled[arm.as_pointer()][1]
        assert labels._pose_labels(arm, True) is cached, "playing: the labelled joints are found once"
        labels.set_label(arm.data.bones[names[5]], draw=True)
        assert len(labels.label_points(playing)) == 2, "a label turned on while playing shows at once"
        assert len(labels.label_points(SimpleNamespace(view_layer=bpy.context.view_layer))) == 2, "not playing"
    finally:
        labels._labelled.clear()
        scene.frame_set(1)


def test_playing_joint_lines_cost_little():
    """Two 65-joint skeletons while playing (loose budget 8 ms)."""
    _clear()
    rigs = [_rig(0.0, 65)[0], _rig(3.0, 65)[0]]
    _animate(*rigs)
    scene, times = bpy.context.scene, []
    mj._LISTS.clear()
    for k in range(15):
        scene.frame_set(2 + k)
        dg = bpy.context.evaluated_depsgraph_get()
        t0 = time.perf_counter()
        for r in rigs:
            mj._fast_lines(r, scene, True, dg, False, playing=True)
        times.append(time.perf_counter() - t0)
    mj._LISTS.clear()
    med = sorted(times)[len(times) // 2] * 1000
    print(f"joint lines of 2 x 65 joints while playing: median {med:.2f} ms per frame")
    assert med < 8.0, f"joint lines take {med:.2f} ms per frame while playing"


def _skinned(rings=150, segs=96):
    """A 14k-point tube skinned to a two-joint skeleton, the top joint keyed turning over frames 1-20."""
    import bmesh
    _clear()
    arm, names = _rig(0.0, 2)
    bm = bmesh.new()
    rows = [[bm.verts.new((0.3 * math.cos(2 * math.pi * s / segs), 0.3 * math.sin(2 * math.pi * s / segs),
                           0.15 * r / (rings - 1))) for s in range(segs)] for r in range(rings)]
    for r in range(rings - 1):
        for s in range(segs):
            bm.faces.new((rows[r][s], rows[r][(s + 1) % segs], rows[r + 1][(s + 1) % segs], rows[r + 1][s]))
    me = bpy.data.meshes.new("skin")
    bm.to_mesh(me)
    bm.free()
    body = bpy.data.objects.new("skin", me)
    bpy.context.scene.collection.objects.link(body)
    lo, hi = body.vertex_groups.new(name=names[0]), body.vertex_groups.new(name=names[1])
    for v in me.vertices:
        t = v.co.z / 0.15
        lo.add([v.index], 1.0 - t, 'REPLACE')
        hi.add([v.index], t, 'REPLACE')
    body.modifiers.new("Armature", 'ARMATURE').object = arm
    pb = arm.pose.bones[names[0]]
    pb.rotation_mode = 'XYZ'
    for f, a in ((1, 0.0), (20, 1.2)):
        pb.rotation_euler = (a, 0.0, 0.0)
        pb.keyframe_insert("rotation_euler", frame=f)
    return body


def _evaluated(ob):
    me = ob.evaluated_get(bpy.context.evaluated_depsgraph_get()).data
    co = np.empty(len(me.vertices) * 3, np.float32)
    me.vertices.foreach_get("co", co)
    ed = np.empty(len(me.edges) * 2, np.int32)
    me.edges.foreach_get("vertices", ed)
    return co.reshape(-1, 3), ed.reshape(-1, 2)


def test_selected_skinned_mesh_wire_reads_only_its_points_on_a_new_frame():
    """The Maya selection wire of a selected skinned mesh follows every frame (its points), but a mesh that only
    deforms keeps its edges, so a frame no longer reads them (several ms for 28k edges); a mesh whose modifiers can
    change its edges reads them again every frame."""
    sw = import_module(kit.MODULE + ".ui.selection_wire")
    body = _skinned()
    scene = bpy.context.scene
    sw._edges.clear()
    times, first, seen = [], None, []
    try:
        for f in (1, 7, 14, 20, 3):
            scene.frame_set(f)
            sw._on_frame(scene)
            dg = bpy.context.evaluated_depsgraph_get()
            t0 = time.perf_counter()
            co, ed = sw.edges_of(body, dg)
            times.append(time.perf_counter() - t0)
            want_co, want_ed = _evaluated(body)
            assert np.allclose(co, want_co, atol=1e-6), f"frame {f}: the wire follows the skinned points"
            assert np.array_equal(ed, want_ed), f"frame {f}: the same edges"
            if first is None:
                first = ed
            assert ed is first, f"frame {f}: the edges read on the first frame are used again"
            seen.append(co.copy())
        assert not np.allclose(seen[0], seen[3]), "frames 1 and 20 draw different points"
        med = sorted(times[1:])[len(times[1:]) // 2] * 1000
        print(f"selection wire of a 14k-point skinned mesh: {med:.3f} ms a frame")
        assert med < 2.0, f"reading the wire takes {med:.3f} ms a frame"
        body.modifiers.new("sub", 'SUBSURF').levels = 1
        scene.frame_set(5)
        sw._on_frame(scene)
        co, ed = sw.edges_of(body, bpy.context.evaluated_depsgraph_get())
        want_co, want_ed = _evaluated(body)
        assert np.array_equal(ed, want_ed) and np.allclose(co, want_co, atol=1e-6), "subdivided: new edges"
        assert body.session_uid not in sw._edges, "a modifier that can change the edges: read every frame"
    finally:
        sw._edges.clear()
        scene.frame_set(1)


def test_range_slider_reads_its_header_row_once_while_playing():
    bg, a, b, c = (0.1, 0.1, 0.1), (0.5, 0.5, 0.5), (0.6, 0.6, 0.6), (0.7, 0.7, 0.7)
    row = [bg] * 4 + [a] * 20 + [bg] * 3 + [b] * 20 + [bg] * 300 + [c] * 30 + [bg] * 5
    reads = []
    real = rb._read_row
    rb._read_row = lambda region, y: reads.append(y) or list(row)
    area = SimpleNamespace(as_pointer=lambda: 344)
    region = SimpleNamespace(width=len(row), height=30)
    want = rb.bar_span(row, bg, min_w=rb.BAR_UNITS * 20 * 0.6)
    try:
        rb._gaps.clear()
        assert want is not None
        for _i in range(3):
            assert rb.find_gap(area, region, 20, playing=False)[0] == want
        assert len(reads) == 3, "not playing: every header redraw reads its row"
        reads.clear()
        for _i in range(5):
            assert rb.find_gap(area, region, 20, playing=True) == (want, rb.spare_after(row, want[1], bg))
        assert len(reads) == 0, "playing with the header as it was: the gap found last time is used again"
        region.width -= 1
        rb.find_gap(area, region, 20, playing=True)
        rb.find_gap(area, region, 20, playing=True)
        assert len(reads) == 1, "a resized header is read again, once"
        rb._extra[344] = 2
        rb.find_gap(area, region, 20, playing=True)
        assert len(reads) == 2, "a wider bar label is read again"
    finally:
        rb._read_row = real
        rb._gaps.clear()
        rb._extra.pop(344, None)


# --- controls, B-Bone / Envelope, views sharing the lines, the fixed cost --------------------------------------------

def _widget(name, points, edges):
    me = bpy.data.meshes.new(name)
    me.from_pydata(points, edges, [])
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def _circle(name, n=12, r=1.0):
    pts = [(r * math.cos(2 * math.pi * i / n), r * math.sin(2 * math.pi * i / n), 0.0) for i in range(n)]
    return _widget(name, pts, [(i, (i + 1) % n) for i in range(n)])


def _control_rig():
    """``_busy_rig`` with more controls: a circle shared by two controls (one following a hidden joint, moved /
    turned / scaled, not by the bone length; one scaled by its bone length), a curve control, a control following
    a turned joint, and a control in a hidden bone collection (not drawn). The hidden joint is the one above the
    first control here (that control is hidden with it, like Maya), so the other controls are drawn."""
    arm, names = _busy_rig()
    pbs = arm.pose.bones
    compat.set_bone_hidden(pbs[names[4]], False)
    compat.set_bone_hidden(pbs[names[8]], True)
    circle = _circle("ctrl_circle")
    cu = bpy.data.curves.new("ctrl_curve", 'CURVE')
    cu.dimensions = '3D'
    sp = cu.splines.new('POLY')
    sp.points.add(4)
    for i, p in enumerate(sp.points):
        p.co = (0.3 * math.cos(i), 0.2 * i, 0.1 * math.sin(2 * i), 1.0)
    sp.use_cyclic_u = True
    curve = bpy.data.objects.new("ctrl_curve", cu)
    bpy.context.scene.collection.objects.link(curve)
    pb = pbs[names[10]]
    pb.custom_shape = circle
    pb.custom_shape_transform = pbs[names[8]]
    pb.custom_shape_translation = (0.1, -0.2, 0.05)
    pb.custom_shape_rotation_euler = (0.4, -0.7, 1.2)
    pb.custom_shape_scale_xyz = (1.5, 0.6, 2.0)
    pb.use_custom_shape_bone_size = False
    pbs[names[11]].custom_shape = circle
    pbs[names[11]].custom_shape_scale_xyz = (0.5, 0.5, 0.5)
    pbs[names[12]].custom_shape = curve
    pbs[names[13]].custom_shape = circle
    pbs[names[13]].custom_shape_transform = pbs[names[2]]
    pbs[names[13]].custom_shape_rotation_euler = (0.0, 0.9, 0.0)
    pbs[names[7]].custom_shape = circle
    _pose(arm, 5)
    return arm, names


def test_controls_draw_their_shapes_like_the_per_control_lines():
    """Controls draw their shape where the per-control geometry (``shape_lines`` with ``_shape_matrix``) puts it,
    in their joint colour, mesh and curve shapes alike, shared shapes, offsets, turns, scales, a shape following
    another (also hidden) joint; a control in a hidden collection is not drawn. Object and Pose Mode."""
    arm, names = _control_rig()
    arm.select_set(False)
    shaped = [n for n, j in mj.skeleton(arm, bpy.context.scene).items() if j.shape is not None]
    assert sorted(shaped) == sorted(names[k] for k in (9, 10, 11, 12, 13)), shaped
    for persp in (True, False):
        _same(_drawn(arm, persp), _reference(arm, persp), f"Object Mode, controls, perspective {persp}")
        _same(_drawn(arm, persp, stick=True), _reference(arm, persp, stick=True), f"Stick, perspective {persp}")
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    bpy.ops.object.mode_set(mode='POSE')
    try:
        for pb in arm.pose.bones:
            cb.set_bone_selected(pb, pb.name in (names[1], names[10], names[11]))
        arm.data.bones.active = arm.data.bones[names[11]]
        for k in (2, 9):
            _pose(arm, k)
            ref = _reference(arm, True)
            _same(_drawn(arm, True), ref, f"Pose Mode, frame {k}: selected and lead controls")
            assert np.any(np.all(np.isclose(ref[:, 6:9], mj.LEAD), axis=1)), "the lead control is drawn green"
            _same(_drawn(arm, False), _reference(arm, False), f"Pose Mode, frame {k}, orthographic")
    finally:
        bpy.ops.object.mode_set(mode='OBJECT')


def test_control_shapes_are_read_once_while_playing():
    """While playing, each control's shape is read on the first frame only; the controls still follow the pose and
    their keyed offset / scale every frame. A shape that changes with the frame (a keyed shape key) is read every
    frame; an edited shape (a depsgraph update) and a new playback read the shapes again."""
    arm, names = _control_rig()
    _animate(arm)
    pbs = arm.pose.bones
    for f, v in ((1, 0.5), (20, 1.4)):
        pbs[names[11]].custom_shape_scale_xyz = (v, v, v)
        pbs[names[11]].keyframe_insert("custom_shape_scale_xyz", frame=f)
        pbs[names[10]].custom_shape_translation = (0.1 * v, -0.2, 0.3 * v)
        pbs[names[10]].keyframe_insert("custom_shape_translation", frame=f)
    moving = _circle("ctrl_moving", 8, 0.4)
    moving.shape_key_add(name="Basis")
    wide = moving.shape_key_add(name="wide")
    for p in wide.data:
        p.co = p.co * 2.5
    for f, v in ((1, 0.0), (20, 1.0)):
        wide.value = v
        wide.keyframe_insert("value", frame=f)
    pbs[names[12]].custom_shape = moving
    bpy.data.objects["ctrl_shape"].modifiers.new("smooth", 'SUBSURF')   # still: read once
    bpy.context.view_layer.update()
    scene = bpy.context.scene
    reads = []
    real = mj._read_widget
    mj._read_widget = lambda shape, dg: reads.append(shape.name) or real(shape, dg)
    mj._reload()                                       # a new playback
    try:
        prev = None
        for i, f in enumerate((1, 6, 13, 20)):
            scene.frame_set(f)
            reads.clear()
            drawn = _drawn(arm, True, playing=True)
            _same(drawn, _reference(arm, True), f"playing, frame {f}")
            if i == 0:
                assert sorted(reads) == ["ctrl_circle", "ctrl_moving", "ctrl_shape"], f"first frame reads {reads}"
            else:
                assert reads == ["ctrl_moving"], f"frame {f}: only the shape keyed over time is read again ({reads})"
            assert prev is None or _gap(drawn, prev) > 1e-3, "the controls move"
            prev = drawn
        circle = bpy.data.objects["ctrl_circle"]
        circle.data.vertices[0].co.x += 0.5            # an edit: the depsgraph update reads the shapes again
        circle.data.update()
        bpy.context.view_layer.update()
        reads.clear()
        _same(_drawn(arm, True, playing=True), _reference(arm, True), "an edited shape")
        assert "ctrl_circle" in reads, f"the edited shape is read again ({reads})"
        reads.clear()
        mj._reload()
        _drawn(arm, True, playing=True)
        assert "ctrl_circle" in reads and "ctrl_shape" in reads, f"a new playback reads them again ({reads})"
    finally:
        mj._read_widget = real
        scene.frame_set(1)


def test_which_control_shapes_change_with_the_frame():
    """A control's shape is read again every frame only when its geometry can change with the frame: shape keys,
    animated data, deforming / generating modifiers, a keyed modifier setting. A plain shape or one with only a
    Subdivision Surface (Bevel, Solidify ...) modifier is read once."""
    _clear()
    plain = _circle("plain")
    assert not mj.shape_moves(plain), "a plain mesh"
    smooth = _circle("smooth")
    smooth.modifiers.new("sub", 'SUBSURF')
    smooth.modifiers.new("bevel", 'BEVEL')
    assert not mj.shape_moves(smooth), "Subdivision Surface and Bevel alone"
    keyed = _circle("keyed")
    keyed.modifiers.new("sub", 'SUBSURF')
    keyed.modifiers["sub"].keyframe_insert("levels", frame=1)
    assert mj.shape_moves(keyed), "a keyed modifier setting"
    deformed = _circle("deformed")
    deformed.modifiers.new("wave", 'WAVE')
    assert mj.shape_moves(deformed), "a modifier that reads the time"
    shaped = _circle("shaped")
    shaped.shape_key_add(name="Basis")
    assert mj.shape_moves(shaped), "shape keys"
    animated = _circle("animated")
    animated.data.vertices[0].keyframe_insert("co", frame=1)
    assert mj.shape_moves(animated), "keyed mesh data"
    moved = _circle("moved")
    moved.keyframe_insert("location", frame=1)
    assert not mj.shape_moves(moved), "an animated object without modifiers: its transform doesn't shape a control"


def _reference_own(ob, perspective, kind):
    """What the view draws for ``ob`` shown as Blender's B-Bone / Envelope ``kind``, in drawing order: the controls'
    shapes, the selected joints' axes, then every other bone's shape (``own_shape_lines``)."""
    scene = bpy.context.scene
    js = mj.skeleton(ob, scene)
    sel, lead = mj.selection(ob, js)
    col = mj.colours(js, sel, lead)
    dg = bpy.context.evaluated_depsgraph_get()
    pts, cols = [], []

    def add(segs, colour):
        pts.extend(tuple(v) for v in segs)
        cols.extend([(*colour, 1.0)] * len(segs))

    for n, j in js.items():
        if j.shape is not None and j.state != "HIDDEN":
            add(mj.shape_lines(j.shape[0], j.shape[1], dg), col[n])
    if perspective:
        for n, j in js.items():
            if j.shape is None and n in sel and j.state != "HIDDEN":
                for i in range(3):
                    add([j.centre, j.centre + j.frame.col[i] * j.radius], mj.AXIS_COLORS[i])
    for n, segs in mj.own_shape_lines(ob, kind).items():
        add(segs, col[n])
    return _rows(pts, cols)


def test_bbone_and_envelope_lines_are_the_per_bone_lines():
    """B-Bone (straight boxes and bent boxes of 3 and 4 segments, mixed) and Envelope display: the same lines, in
    the same order and colours, as the per-bone shapes; controls keep their shape, hidden bones draw nothing."""
    arm, names = _busy_rig()
    bones, pbs = arm.data.bones, arm.pose.bones
    for i, b in enumerate(bones):
        b.bbone_x, b.bbone_z = 0.02 + 0.01 * (i % 4), 0.03 + 0.005 * (i % 3)
        b.head_radius, b.tail_radius = 0.03 + 0.01 * (i % 5), 0.02 + 0.015 * (i % 3)
    for n, segs in ((names[1], 4), (names[5], 3), (names[6], 4), (names[12], 3)):
        bones[n].bbone_segments = segs
    for n in (names[1], names[5]):
        pbs[n].bbone_curveinx, pbs[n].bbone_curveoutz, pbs[n].bbone_rollin = 0.2, -0.15, 0.3
    bpy.context.view_layer.update()
    arm.select_set(False)

    def check(what):
        for kind in ('BBONE', 'ENVELOPE'):
            arm.data.display_type = kind
            for persp in (True, False):
                drawn, ref = _drawn(arm, persp, kind=kind), _reference_own(arm, persp, kind)
                _same(drawn, ref, f"{what}, {kind}, perspective {persp}")
                assert float(np.abs(drawn - ref).max()) < 1e-4, f"{what}, {kind}: drawn in the per-bone order"

    check("Object Mode")
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    bpy.ops.object.mode_set(mode='POSE')
    try:
        for pb in pbs:
            cb.set_bone_selected(pb, pb.name in (names[1], names[3], names[9]))
        arm.data.bones.active = bones[names[3]]
        _pose(arm, 4)
        check("Pose Mode, selected joints and a lead")
    finally:
        bpy.ops.object.mode_set(mode='OBJECT')
        arm.data.display_type = 'OCTAHEDRAL'


def test_envelope_and_bbone_cost_little_for_many_bones():
    """300 bones in B-Bone (one segment) and Envelope display: well under a frame (loose budget 25 ms)."""
    _clear()
    arm = _rig(0.0, 300)[0]
    _animate(arm)
    scene = bpy.context.scene
    for kind in ('BBONE', 'ENVELOPE'):
        arm.data.display_type = kind
        times = []
        for k in range(8):
            scene.frame_set(2 + k)
            dg = bpy.context.evaluated_depsgraph_get()
            t0 = time.perf_counter()
            mj._fast_lines(arm, scene, True, dg, False, playing=True, kind=kind)
            times.append(time.perf_counter() - t0)
        med = sorted(times)[len(times) // 2] * 1000
        print(f"{kind} lines of 300 bones while playing: median {med:.2f} ms per frame")
        assert med < 25.0, f"{kind} lines take {med:.2f} ms per frame"
    arm.data.display_type = 'OCTAHEDRAL'
    mj._LISTS.clear()


def _spaces(count):
    out = []
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D' and area.spaces.active not in out:
                out.append(area.spaces.active)
    assert len(out) >= count, "the start file has several 3D Views"
    return out[:count]


def test_views_share_one_build_of_each_skeleton():
    """Two 3D Views showing the same skeletons draw one build of their lines (the same arrays); an orthographic view
    and a view showing one skeleton only (local view) join the same skeleton lines without building them again; a
    new frame builds them once more. The lines are the view's own ``view_lines``."""
    _clear()
    rigs = [_rig(0.0, 20)[0], _rig(3.0, 20)[0]]
    bpy.context.view_layer.objects.active = rigs[0]
    rigs[0].select_set(True)                          # its root joint is selected: axes in perspective views
    one, two = _spaces(2)

    def view(space, persp, objects=rigs):
        return SimpleNamespace(space_data=space, region_data=SimpleNamespace(is_perspective=persp),
                               scene=bpy.context.scene, view_layer=bpy.context.view_layer, visible_objects=objects,
                               mode='OBJECT', screen=None)

    builds = []
    real = mj._parts
    mj._parts = lambda ob, *a, **k: builds.append(ob.name) or real(ob, *a, **k)
    try:
        mj._frame_post()
        a = mj._joined(view(one, True))
        b = mj._joined(view(two, True))
        assert a is b, "two perspective views showing the same skeletons share their lines"
        assert sorted(builds) == sorted(r.name for r in rigs), f"each skeleton built once ({builds})"
        c = mj._joined(view(one, False))
        d = mj._joined(view(two, True, [rigs[0]]))
        assert len(builds) == 2, f"orthographic / local views join the same skeleton lines ({builds})"
        assert c is not a and len(c[0]) < len(a[0]), "an orthographic view draws no axes"
        assert d is not a and len(d[0]) < len(a[0]), "a view showing one skeleton draws only that one"
        for got, ctx in ((a, view(one, True)), (c, view(one, False)), (d, view(two, True, [rigs[0]]))):
            pts, cols = mj.view_lines(ctx)
            seg_pts, seg_cols = mj.joined_segments(got)
            assert np.array_equal(seg_pts, pts) and np.array_equal(seg_cols, cols), "the view's own lines"
        builds.clear()
        mj._frame_post()                               # a new frame
        mj._joined(view(one, True))
        mj._joined(view(two, True))
        assert len(builds) == 2, f"a new frame builds each skeleton once more ({builds})"
        assert mj._CACHE[two.as_pointer()][0][0] == mj._GEN[0], "each view keeps the generation it drew"
    finally:
        mj._parts = real


def test_selection_wire_without_a_selection_draws_nothing_at_once():
    """Nothing selected, no wireframe shading: the selection wire returns before looking for objects to draw."""
    sw = import_module(kit.MODULE + ".ui.selection_wire")
    _clear()
    _rig(0.0, 3)
    for ob in bpy.context.view_layer.objects:
        ob.select_set(False)
    screen = next(s for s in bpy.data.screens if any(a.type == 'VIEW_3D' for a in s.areas))
    area = next(a for a in screen.areas if a.type == 'VIEW_3D')
    region = next(r for r in area.regions if r.type == 'WINDOW')
    looks = []
    real = sw.highlighted, sw.live_wire_objects, sw.dormant_objects
    sw.highlighted = lambda c, **_kw: looks.append("highlighted") or []
    sw.live_wire_objects = lambda c: looks.append("live") or []
    sw.dormant_objects = lambda c: looks.append("dormant") or []
    try:
        with bpy.context.temp_override(screen=screen, area=area, region=region):
            assert bpy.context.region_data is not None and not bpy.context.selected_objects
            area.spaces.active.shading.type = 'SOLID'
            area.spaces.active.overlay.show_overlays = True
            sw._draw()
            assert looks == [], f"nothing selected: no look for objects ({looks})"
            bpy.context.view_layer.objects[0].select_set(True)
            sw._draw()
            assert looks, "a selection is looked at"
    finally:
        sw.highlighted, sw.live_wire_objects, sw.dormant_objects = real


def test_frame_changes_dont_look_through_every_object():
    """A new frame: vertex keys are applied only in mesh Edit Mode, and the RP IK handles are found once while the
    scene keeps its objects (an added object finds them again)."""
    pk = import_module(kit.MODULE + ".operators.point_keys")
    rp = import_module(kit.MODULE + ".operators.ik_rp")
    _clear()
    _rig(0.0, 3)
    for i in range(20):
        bpy.context.scene.collection.objects.link(bpy.data.objects.new(f"prop{i}", None))
    bpy.context.view_layer.update()
    scene = bpy.context.scene
    applied, looks = [], []
    real = pk.apply_frame, rp.rp_handles
    pk.apply_frame = lambda sc: applied.append(1) or real[0](sc)
    rp.rp_handles = lambda: looks.append(1) or real[1]()
    try:
        for f in range(2, 8):
            scene.frame_set(f)
        assert not applied, f"Object Mode: no Edit Mode mesh to move ({len(applied)} looks)"
        assert len(looks) <= 1, f"the RP handles are found once, not every frame ({len(looks)} looks)"
        looks.clear()
        scene.collection.objects.link(bpy.data.objects.new("added", None))
        bpy.context.view_layer.update()
        scene.frame_set(9)
        scene.frame_set(10)
        assert len(looks) == 1, f"an added object: the handles are found again once ({len(looks)})"
        me = bpy.data.meshes.new("editable")
        me.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [], [(0, 1, 2)])
        ob = bpy.data.objects.new("editable", me)
        scene.collection.objects.link(ob)
        bpy.context.view_layer.objects.active = ob
        bpy.ops.object.mode_set(mode='EDIT')
        try:
            scene.frame_set(11)
            assert applied, "mesh Edit Mode: a frame change applies the vertex keys"
        finally:
            bpy.ops.object.mode_set(mode='OBJECT')
    finally:
        pk.apply_frame, rp.rp_handles = real
        scene.frame_set(1)
