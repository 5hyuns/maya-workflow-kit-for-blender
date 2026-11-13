"""Selecting and moving stay light in rig and modeling scenes: a click or a marquee on a skeleton measures every
joint's drawn lines in one go (control shapes read once, not per click), a display-layer / Visibility state of a big
skeleton is read in one pass over its joints, and Maya's component colours keep the mesh's edges, faces and selection
while a transform only moves points. The results are the same as measuring joint by joint."""

from importlib import import_module
from types import SimpleNamespace

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

import kit

mj = import_module(kit.MODULE + ".ui.maya_joints")
lj = import_module(kit.MODULE + ".ui.layer_joints")
cc = import_module(kit.MODULE + ".ui.component_colors")
joints = import_module(kit.MODULE + ".operators.joints")
preselect = import_module(kit.MODULE + ".operators.preselect")


class _Count:
    def __init__(self, owner, name):
        self.owner, self.name, self.calls = owner, name, 0
        self.real = getattr(owner, name)

    def __enter__(self):
        def counted(*a, **k):
            self.calls += 1
            return self.real(*a, **k)
        setattr(self.owner, self.name, counted)
        return self

    def __exit__(self, *exc):
        setattr(self.owner, self.name, self.real)


def _object_mode():
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')


def _clear():
    _object_mode()
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for data in (bpy.data.armatures, bpy.data.meshes):
        for d in list(data):
            data.remove(d)


def _front_view():
    """Front orthographic region 200 x 100: world (x, z) -> (100 + 20 x, 50 + 20 z) px."""
    view = Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, -1, 0, -10), (0, 0, 0, 1)))
    proj = Matrix(((0.2, 0, 0, 0), (0, 0.4, 0, 0), (0, 0, -0.01, 0), (0, 0, 0, 1)))
    return SimpleNamespace(region_data=SimpleNamespace(perspective_matrix=proj @ view),
                           region=SimpleNamespace(width=200, height=100), space_data=None, window=None,
                           scene=bpy.context.scene, evaluated_depsgraph_get=bpy.context.evaluated_depsgraph_get)


def _rig():
    """A kit skeleton (Maya joints: spheres and bones) and a rig whose bones carry circle / square control shapes."""
    skel = joints.new_skeleton(bpy.context)
    made, parent = [], None
    for z in range(4):
        parent = joints.add_joint(skel, Vector((-2.0, 0.0, 0.5 * z)), parent, length=0.4)
        made.append(parent)
    joints.finish(bpy.context, skel, made)
    _object_mode()
    widgets = []
    for name, verts in (("WGT_circle", 16), ("WGT_square", 4)):
        bpy.ops.mesh.primitive_circle_add(vertices=verts, radius=0.3)
        w = bpy.context.object
        w.name = name
        widgets.append(w)
    data = bpy.data.armatures.new("ctrl_rig")
    rig = bpy.data.objects.new("ctrl_rig", data)
    bpy.context.scene.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='EDIT')
    prev = None
    for i in range(12):
        eb = data.edit_bones.new(f"c{i:02d}")
        eb.head, eb.tail = (1.0 + 0.3 * (i % 4), 0.0, 0.4 * (i // 4)), (1.0 + 0.3 * (i % 4), 0.0, 0.4 * (i // 4) + 0.3)
        eb.parent = prev if i % 4 else None
        prev = eb
    bpy.ops.object.mode_set(mode='OBJECT')
    for i, pb in enumerate(rig.pose.bones):
        if i % 3 != 2:
            pb.custom_shape = widgets[i % 2]
    for ob in bpy.context.scene.objects:
        ob.select_set(False)
    bpy.context.view_layer.update()
    return skel, rig, widgets


def _reference_distance(ctx, ob, mouse):
    """Joint by joint: ``joint_segments`` with each control's own geometry (``shape_lines``)."""
    js = mj.skeleton(ob, ctx.scene)
    dg = ctx.evaluated_depsgraph_get()
    skip = mj._unpickable(ob, js)
    out = {}
    for n in js:
        if n in skip:
            continue
        pts = mj.joint_segments(js, n, dg)
        if not len(pts):
            continue
        a, b, ok = mj._screen(ctx, pts)
        if ok.any():
            out[n] = float(preselect.segment_distance(mouse, a[ok], b[ok])[0].min())
    return out


def _reference_region(ctx, ob, poly):
    js = mj.skeleton(ob, ctx.scene)
    dg = ctx.evaluated_depsgraph_get()
    maya_drawn = getattr(ob.data, "display_type", 'OCTAHEDRAL') not in mj.STICK_TYPES | mj.SHAPE_TYPES
    skip = mj._unpickable(ob, js)
    joints_hit, each = [], []
    for n in js:
        if n in skip:
            continue
        pts = mj.joint_segments(js, n, dg)
        if not len(pts):
            continue
        a, b, ok = mj._screen(ctx, pts)
        if ok.any() and mj.segments_touch([tuple(v) for v in a[ok]], [tuple(v) for v in b[ok]], poly):
            if maya_drawn and js[n].shape is None:
                joints_hit.append((mj.depth(js, n), list(js).index(n), n))
            else:
                each.append(n)
    return each + ([min(joints_hit)[2]] if joints_hit else [])


def test_click_distances_match_joint_by_joint_and_read_shapes_once():
    _clear()
    skel, rig, widgets = _rig()
    ctx = _front_view()
    mj._WIDGETS.clear()
    for ob in (skel, rig):
        for mouse in ((60.0, 52.0), (130.0, 60.0), (100.0, 50.0), (150.0, 75.0)):
            want = _reference_distance(ctx, ob, mouse)
            got = mj.screen_distance(ctx, ob, mouse)
            assert set(got) == set(want), (ob.name, mouse, set(got) ^ set(want))
            assert all(abs(got[n] - want[n]) < 1e-3 for n in want), (ob.name, mouse)
            assert mj.pick(ctx, ob, mouse, 8) == (min(((v, n) for n, v in want.items() if v <= 8),
                                                      default=(0, None))[1])
    # control shapes: read once, then every click reuses them
    mj._WIDGETS.clear()
    with _Count(mj, "_read_widget") as rw:
        mj.screen_distance(ctx, rig, (130.0, 60.0))
        first = rw.calls
        for _ in range(3):
            mj.screen_distance(ctx, rig, (130.0, 60.0))
    assert first == len(widgets) and rw.calls == first, (first, rw.calls)


def test_marquee_and_lasso_pick_the_same_joints_as_joint_by_joint():
    _clear()
    skel, rig, _widgets = _rig()
    ctx = _front_view()
    polys = ([(40, 40), (70, 40), (70, 100), (40, 100)],            # the kit skeleton's chain
             [(115, 40), (150, 40), (150, 70), (115, 70)],          # some controls
             [(0, 0), (200, 0), (200, 100), (0, 100)],              # everything
             [(120, 45), (160, 55), (140, 90), (110, 70)],          # a lasso
             [(180, 5), (195, 5), (195, 15)])                       # nothing
    for ob in (skel, rig):
        for poly in polys:
            assert mj.region_pick(ctx, ob, poly) == _reference_region(ctx, ob, poly), (ob.name, poly)


def test_touch_test_matches_the_segment_by_segment_rule():
    rng = np.random.default_rng(3)
    a, b = rng.uniform(0, 100, (400, 2)), rng.uniform(0, 100, (400, 2))
    for poly in ([(20, 20), (60, 20), (60, 70), (20, 70)], [(10, 50), (50, 10), (90, 50), (50, 90), (50, 50)]):
        want = [mj.segments_touch([tuple(p)], [tuple(q)], poly) for p, q in zip(a, b)]
        assert list(mj._touching(a, b, poly)) == want


def _chain(n):
    data = bpy.data.armatures.new("long")
    ob = bpy.data.objects.new("long", data)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT')
    prev = None
    for i in range(n):
        eb = data.edit_bones.new(f"b{i:03d}")
        eb.head, eb.tail = (0.0, 0.0, 0.1 * i), (0.0, 0.0, 0.1 * i + 0.1)
        eb.parent = prev if i % 25 else None        # several chains
        prev = eb
    bpy.ops.object.mode_set(mode='OBJECT')
    return ob


def test_hidden_joint_state_reads_the_skeleton_once():
    _clear()
    ob = _chain(150)
    hidden = ("b010", "b030", "b031", "b077", "b120")
    for name in hidden:
        ob.pose.bones[name].hide = True
    lj.bump(redraw=False)
    calls = [0]
    real = bpy.types.Bone.children_recursive          # Blender's own: walks every bone of the armature per call
    own = "children_recursive" in vars(bpy.types.Bone)

    def counted(self):
        calls[0] += 1
        return real.fget(self)
    bpy.types.Bone.children_recursive = property(counted)
    try:
        got = dict(lj.state(ob))
    finally:
        if own:
            bpy.types.Bone.children_recursive = real
        else:
            del bpy.types.Bone.children_recursive
    want = {}
    for name in hidden:
        b = ob.data.bones[name]
        for n in (name, *(c.name for c in b.children_recursive)):
            want[n] = lj.HIDDEN
    assert got == want, set(got) ^ set(want)
    assert calls[0] == 0, "the joints below are found from one pass over the bones"


def test_component_colours_keep_the_mesh_while_a_transform_moves_points():
    _clear()
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=30, y_subdivisions=20, size=4)
    ob = bpy.context.object
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bm = bmesh.from_edit_mesh(ob.data)
    for v in bm.verts[:40]:
        v.select = True
    bm.select_flush(True)
    bmesh.update_edit_mesh(ob.data)
    bpy.context.view_layer.update()
    dg = bpy.context.view_layer.depsgraph
    real_ptr = cc._transform_ptr
    cc._cache.clear()
    cc._dirty.clear()
    try:
        cc._transform_ptr = lambda: 4242                   # a transform runs
        with _Count(cc, "read_bmesh") as rb:
            st = cc.state(ob, dg, faces=True)
            assert rb.calls == 1
            before = st.arrays
            edges, vsel = before.edges.copy(), before.vsel.copy()
            for _step in range(3):
                for v in bm.verts:
                    if v.select:
                        v.co.z += 0.25
                bmesh.update_edit_mesh(ob.data)
                bpy.context.view_layer.update()
                cc._dirty.update((ob.name, ob.data.name))  # what the depsgraph handler marks
                with _Count(cc, "_selection_signature") as sig:
                    st = cc.state(ob, dg, faces=True)
                assert sig.calls == 0, "a transform changes no selection"
            assert rb.calls == 1, "only the points were read again"
        fresh = cc.read_bmesh(bm)
        assert np.allclose(st.arrays.co, fresh.co, atol=1e-6)
        assert np.array_equal(st.arrays.edges, fresh.edges) and np.array_equal(st.arrays.edges, edges)
        assert np.array_equal(st.arrays.vsel, fresh.vsel) and np.array_equal(st.arrays.vsel, vsel)
        assert np.array_equal(st.arrays.corner_vert, fresh.corner_vert)
        # the transform ended: the next change reads the mesh in full again
        cc._transform_ptr = lambda: 0
        cc._dirty.update((ob.name, ob.data.name))
        with _Count(cc, "read_bmesh") as rb:
            cc.state(ob, dg, faces=True)
        assert rb.calls == 1
        # a new transform (after an edit that may have changed the mesh) starts with one full read
        cc._transform_ptr = lambda: 5151
        cc._dirty.update((ob.name, ob.data.name))
        with _Count(cc, "read_bmesh") as rb:
            cc.state(ob, dg, faces=True)
            cc._dirty.update((ob.name, ob.data.name))
            cc.state(ob, dg, faces=True)
        assert rb.calls == 1
    finally:
        cc._transform_ptr = real_ptr
        cc._cache.clear()
        cc._dirty.clear()
        _object_mode()


def test_scrubbing_the_time_reuses_what_playback_reuses():
    """While the time is dragged in a Time Slider / timeline only the frame changes, as during playback: the joint
    list read on the first frame is used again."""
    _clear()
    skel, _rig_ob, _widgets = _rig()
    ctx = SimpleNamespace(screen=SimpleNamespace(is_animation_playing=False))
    assert {"ALLSET_OT_time_scrub", "ANIM_OT_change_frame"} <= mj.SCRUB_MODALS
    assert mj.scrubbing() is False, "no scrub modal runs here"
    real = mj.scrubbing
    try:
        mj.scrubbing = lambda: True
        assert mj._playing(ctx)
        mj._LISTS.clear()
        with _Count(mj, "_joint_list") as jl:
            for _frame in range(4):
                mj.joint_list(skel, playing=mj._playing(ctx))
        assert jl.calls == 1, jl.calls
        mj.scrubbing = lambda: False
        assert not mj._playing(ctx)
        with _Count(mj, "_joint_list") as jl:
            for _frame in range(2):
                mj.joint_list(skel, playing=mj._playing(ctx))
        assert jl.calls == 2, "not scrubbing: read each time"
    finally:
        mj.scrubbing = real
        mj._LISTS.clear()
