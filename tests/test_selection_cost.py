"""Selecting and moving stay light in rig and modeling scenes: a click or a marquee on a skeleton measures every
joint's drawn lines in one go (control shapes read once, not per click; each skeleton read once per click), a
display-layer / Visibility state of a big skeleton is read in one pass over its joints and kept while only the joint
selection changes, clearing a joint selection writes only the selected joints, and Maya's component colours keep the mesh's edges, faces and selection
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
                           region=SimpleNamespace(width=200, height=100, as_pointer=lambda: 1), space_data=None,
                           window=None,
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


def _drawn(*obs):
    """What a Maya view's draw keeps for ``obs`` (``maya_joints._joined``): each skeleton's lines and the lines a
    click picks, for the current state."""
    scene, layer = bpy.context.scene, bpy.context.view_layer
    mj._WORLD[0] = mj._world_key(scene, layer)
    for ob in obs:
        pick = []
        mj._PARTS[ob.as_pointer()] = mj._parts(ob, scene, layer.depsgraph, None, False, pick)
        mj._PICK[ob.as_pointer()] = pick[0] if pick else None


def _forget_drawn():
    mj._PARTS.clear()
    mj._PICK.clear()
    mj._WORLD[0] = None


def test_a_click_after_a_draw_uses_the_drawn_lines():
    """Once a view has drawn the skeletons, a click or a marquee uses the drawn lines without reading the
    skeleton again and finds the same joints at the same distances (Template / Reference joints and unselectable
    bones left out); after any change, or for a skeleton not drawn as Maya joints, the skeleton is read again."""
    _clear()
    skel, rig, _widgets = _rig()
    rig.data.bones["c01"].hide_select = True                   # a control Blender won't select
    real_state = lj.state
    lj.state = lambda ob: {"c05": lj.TEMPLATE, "c09": lj.REFERENCE} if ob == rig else real_state(ob)
    try:
        bpy.context.view_layer.update()
        ctx = _front_view()
        ctx.view_layer = bpy.context.view_layer
        mice = ((60.0, 52.0), (130.0, 60.0), (100.0, 50.0), (150.0, 75.0), (121.0, 58.0))
        polys = ([(40, 40), (70, 40), (70, 100), (40, 100)], [(115, 40), (150, 40), (150, 70), (115, 70)],
                 [(0, 0), (200, 0), (200, 100), (0, 100)], [(120, 45), (160, 55), (140, 90), (110, 70)])
        want = {(ob.name, m): _reference_distance(ctx, ob, m) for ob in (skel, rig) for m in mice}
        want_box = {(ob.name, i): _reference_region(ctx, ob, p) for ob in (skel, rig) for i, p in enumerate(polys)}
        near = set(want[("ctrl_rig", mice[4])])
        assert near and not {"c01", "c05", "c09"} & near, near     # beside c05 / c01 / c09: other joints are hit
        _drawn(skel, rig)
        with _Count(mj, "skeleton") as sk:
            for ob in (skel, rig):
                for m in mice:
                    got, ref = mj.screen_distance(ctx, ob, m), want[(ob.name, m)]
                    assert set(got) == set(ref), (ob.name, m, set(got) ^ set(ref))
                    assert all(abs(got[n] - ref[n]) < 1e-3 for n in ref), (ob.name, m)
                    assert mj.pick(ctx, ob, m, 8) == min(((v, n) for n, v in ref.items() if v <= 8),
                                                         default=(0, None))[1]
                for i, p in enumerate(polys):
                    assert mj.region_pick(ctx, ob, p) == want_box[(ob.name, i)], (ob.name, p)
        assert sk.calls == 0, f"the drawn lines are used, got {sk.calls} skeleton reads"
        mj.changed()                                               # an edit: the drawn lines are out of date
        with _Count(mj, "skeleton") as sk:
            got, ref = mj.screen_distance(ctx, rig, mice[1]), want[("ctrl_rig", mice[1])]
        assert set(got) == set(ref) and all(abs(got[n] - ref[n]) < 1e-3 for n in ref)
        assert sk.calls == 1, sk.calls
        rig.data.display_type = 'STICK'                            # not drawn as Maya joints: read joint by joint
        bpy.context.view_layer.update()
        _drawn(rig)
        assert mj._PICK[rig.as_pointer()] is None
        with _Count(mj, "skeleton") as sk:
            mj.screen_distance(ctx, rig, mice[1])
        assert sk.calls == 1, sk.calls
    finally:
        lj.state = real_state
        _forget_drawn()


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
        with _Count(cc, "_read") as rb:
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
        with _Count(cc, "_read") as rb:
            cc.state(ob, dg, faces=True)
        assert rb.calls == 1
        # a new transform (after an edit that may have changed the mesh) starts with one full read
        cc._transform_ptr = lambda: 5151
        cc._dirty.update((ob.name, ob.data.name))
        with _Count(cc, "_read") as rb:
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


def test_marquees_in_quick_succession_are_each_finished_in_order():
    """A marquee's joint rules run once Blender's box has ended. When the next drag starts first, the drags before it
    are finished (in order) before the new one is remembered; a box that ended between two checks and registered its
    result is finished too, instead of being given up."""
    jm = import_module(kit.MODULE + ".operators.joint_marquee")
    done = []
    saved = (jm._running, jm._finish, jm._registered, list(jm._pending))
    try:
        jm._running = lambda entry: entry.get("running", False)
        jm._finish = lambda entry: done.append(entry["id"])
        jm._registered = lambda entry: entry.get("op")
        jm._pending[:] = [{"id": 1, "seen": True}, {"id": 2, "seen": False, "op": object()},
                          {"id": 3, "seen": False}, {"id": 4, "seen": True, "running": True}]
        jm._flush()
        assert done == [1, 2], done                     # 3 never started, 4 still runs
        assert [e["id"] for e in jm._pending] == [4]
        done.clear()
        jm._pending[:] = [{"id": 5, "seen": False, "op": object(), "waited": 0.0}]
        jm._watch()
        assert done == [5] and not jm._pending, "a box that ended unseen but registered is finished"
    finally:
        jm._running, jm._finish, jm._registered = saved[:3]
        jm._pending[:] = saved[3]
        jm.cancel_all()


def test_one_click_reads_each_skeleton_once():
    """The coarse object test and the joint pick of one click read each skeleton once; the distances are the same
    as without it."""
    _clear()
    skel, rig, _widgets = _rig()
    ctx = _front_view()
    mouse = (130.0, 60.0)
    want = {ob.name: mj.screen_distance(ctx, ob, mouse) for ob in (skel, rig)}
    with _Count(mj, "skeleton") as sk:
        with mj.pick_memo():
            got = {ob.name: mj.screen_distance(ctx, ob, mouse) for ob in (skel, rig)}
            picked = mj.pick(ctx, rig, mouse, 8)
            with mj.pick_memo():                       # nested: still the same click
                mj.screen_distance(ctx, skel, mouse)
            moved = mj.screen_distance(ctx, rig, (60.0, 52.0))
    assert got == want, "same distances"
    assert picked == min(((v, n) for n, v in want["ctrl_rig"].items() if v <= 8), default=(0, None))[1]
    assert moved == mj.screen_distance(ctx, rig, (60.0, 52.0)), "another mouse position is read again"
    assert sk.calls == 3, f"each skeleton once per mouse position, got {sk.calls}"
    assert mj._PICK_MEMO[0] is None, "the click's memo ends with it"


def _updated_ids(fn):
    seen = []

    def rec(_scene, dg):
        seen.extend(u.id.original.name for u in dg.updates if isinstance(u.id, bpy.types.Object))
    bpy.app.handlers.depsgraph_update_post.append(rec)
    try:
        fn()
        bpy.context.view_layer.update()
    finally:
        bpy.app.handlers.depsgraph_update_post.remove(rec)
    return set(seen)


def test_a_joint_click_keeps_layer_states_and_leaves_other_skeletons_alone():
    """Picking another joint writes only the joints whose selection changes (a write makes Blender evaluate the
    skeleton and what it deforms again, even with the same value) and keeps every skeleton's display layer state.
    A joint hidden or renamed in Blender is read again."""
    js = import_module(kit.MODULE + ".operators.joint_selection")
    cb = import_module(kit.MODULE + ".ui.channel_box")
    _clear()
    skel, rig, _widgets = _rig()
    rig.pose.bones["c01"].hide = True               # a joint hidden by its own Visibility: a non-empty state
    skel.pose.bones[0].hide = True
    lj.bump(redraw=False)
    ctx = bpy.context
    js.select(ctx, rig, "c00")
    bpy.context.view_layer.update()
    assert lj.state(rig) and lj.state(skel)
    with _Count(lj, "_compute") as comp, _Count(cb, "set_bone_selected") as writes:
        touched = _updated_ids(lambda: js.select(ctx, rig, "c04"))
        assert lj.state(rig).get("c01") == lj.HIDDEN and lj.state(skel)
    assert comp.calls == 0, f"a joint selection keeps the states, read {comp.calls}x"
    assert writes.calls == 2, f"c00 off, c04 on: {writes.calls} writes"
    assert skel.name not in touched, touched
    assert [pb.name for pb in rig.pose.bones if pb.select] == ["c04"]
    with _Count(cb, "set_bone_selected") as writes:
        js.clear(ctx)
    assert writes.calls == 1 and not any(pb.select for pb in rig.pose.bones)
    # Blender's own Hide (H) and a rename reach the state
    for pb in rig.pose.bones:
        pb.select = pb.name == "c05"
    bpy.context.view_layer.update()
    bpy.ops.pose.hide(unselected=False)
    bpy.context.view_layer.update()
    assert lj.state(rig).get("c05") == lj.HIDDEN, "a joint hidden in Blender"
    rig.pose.bones["c01"].name = "c01_renamed"
    bpy.context.view_layer.update()
    st = lj.state(rig)
    assert st.get("c01_renamed") == lj.HIDDEN and "c01" not in st, "a renamed joint"
    _object_mode()


def test_control_shapes_stay_read_across_a_selection():
    """A joint or object selection doesn't change a control's custom shape: the shapes read for the drawn lines stay
    (they are read again once a shape's own geometry is edited)."""
    _clear()
    skel, rig, widgets = _rig()
    ctx = _front_view()
    mouse = (130.0, 60.0)
    mj._WIDGETS.clear()
    mj.screen_distance(ctx, rig, mouse)
    assert len(mj._WIDGETS) == len(widgets)
    with _Count(mj, "_read_widget") as rw:
        rig.pose.bones["c00"].select = True
        skel.select_set(True)
        bpy.context.view_layer.update()
        mj.screen_distance(ctx, rig, mouse)
    assert rw.calls == 0, f"selection re-read {rw.calls} shapes"
    before = mj.screen_distance(ctx, rig, mouse)
    me = widgets[0].data
    for v in me.vertices:
        v.co *= 2.0
    me.update()
    bpy.context.view_layer.update()
    with _Count(mj, "_read_widget") as rw:
        after = mj.screen_distance(ctx, rig, mouse)
    assert rw.calls >= 1 and after != before, "an edited shape is read again"
    rig.pose.bones["c00"].select = False


def _pick_state():
    out = {}
    for ob in bpy.context.scene.objects:
        if ob.type == 'ARMATURE':
            out[ob.name] = (ob.mode, ob.select_get(), sorted(pb.name for pb in ob.pose.bones if pb.select),
                            ob.data.bones.active.name if ob.data.bones.active else None)
    act = bpy.context.view_layer.objects.active
    return out, act.name if act else None


def _reset_picks(skel, rig):
    _object_mode()
    for ob in (skel, rig):
        for pb in ob.pose.bones:
            pb.select = False
        ob.data.bones.active = None
        ob.select_set(False)
    bpy.context.view_layer.objects.active = None


def test_a_marquee_adds_a_skeletons_joints_at_once_with_the_same_result():
    """A marquee's joints of one skeleton are written at once: the same selection, lead object, lead bone and modes
    as picking them one by one (the first with the drag's modifiers, the rest added), with one write per bone."""
    js = import_module(kit.MODULE + ".operators.joint_selection")
    jm = import_module(kit.MODULE + ".operators.joint_marquee")
    cb = import_module(kit.MODULE + ".ui.channel_box")
    _clear()
    skel, rig, _widgets = _rig()
    ctx = bpy.context
    names = ["c00", "c01", "c03", "c04", "c06", "c07"]
    for shift, ctrl, start in ((False, False, ["c09"]), (True, True, ["c09"]), (False, False, [])):
        results = []
        for batched in (False, True):
            _reset_picks(skel, rig)
            if start:
                js.select(ctx, rig, start[0])
            if batched:
                with _Count(cb, "set_bone_selected") as writes:
                    js.select_many(ctx, rig, names, shift, ctrl)
                assert writes.calls <= len(names) + len(start), writes.calls
            else:
                js.select(ctx, rig, names[0], shift, ctrl)
                for n in names[1:]:
                    js.select(ctx, rig, n, True, True)
            results.append(_pick_state())
        assert results[0] == results[1], (shift, ctrl, results)
    # the snapshot a marquee restores writes only what differs
    _reset_picks(skel, rig)
    js.select(ctx, rig, "c00")
    snap = jm.snapshot(ctx)
    js.select(ctx, rig, "c04", True, True)
    with _Count(cb, "set_bone_selected") as writes:
        jm.restore(ctx, snap)
    assert writes.calls == 1, writes.calls
    assert sorted(pb.name for pb in rig.pose.bones if pb.select) == ["c00"]
    assert rig.data.bones.active.name == "c00"
    _object_mode()


def test_joint_labels_are_found_once_between_edits():
    """Draw Label joints are found once and used again on every redraw until something is edited (a view turned or
    zoomed redraws without an edit); a label turned on or a renamed joint shows at once."""
    labels = import_module(kit.MODULE + ".operators.joint_labels")
    _clear()
    skel, _rig_ob, _widgets = _rig()
    ctx = SimpleNamespace(screen=None, view_layer=bpy.context.view_layer)
    bones = skel.data.bones
    labels.set_label(bones[1], side=labels.LEFT, type=labels.T_KNEE, draw=True)
    labels._labelled.clear()
    try:
        first = labels.label_points(ctx)
        assert len(first) == 1
        kept = labels._labelled[skel.as_pointer()][1]
        for _redraw in range(3):
            assert labels.label_points(ctx) == first
        assert labels._labelled[skel.as_pointer()][1] is kept, "no edit: found once"
        labels.set_label(bones[2], draw=True)
        assert len(labels.label_points(ctx)) == 2, "a label turned on shows at once"
        name = bones[2].name
        skel.pose.bones[name].name = name + "_x"
        bpy.context.view_layer.update()
        assert {t for _p, t, _s in labels.label_points(ctx)} == {labels.label_text(b) for b in bones
                                                               if b.get(labels.DRAW)}, "a renamed joint"
    finally:
        labels._labelled.clear()


def test_outliner_rows_stay_through_a_joint_selection():
    """Selecting joints changes no row of the kit Outliner (names, parents, joints): its structure is kept; a renamed
    joint or skeleton is read again."""
    outliner = import_module(kit.MODULE + ".ui.outliner")
    js = import_module(kit.MODULE + ".operators.joint_selection")
    _clear()
    skel, rig, _widgets = _rig()
    ctx = bpy.context
    js.select(ctx, rig, "c00")
    bpy.context.view_layer.update()
    js.select(ctx, rig, "c03")
    bpy.context.view_layer.update()
    v = outliner.structure_version()
    for name in ("c04", "c06", "c07"):
        js.select(ctx, rig, name, True, True)
        bpy.context.view_layer.update()
    js.clear(ctx)
    bpy.context.view_layer.update()
    assert outliner.structure_version() == v, "a joint selection keeps the rows"
    rig.pose.bones["c06"].name = "c06_x"
    bpy.context.view_layer.update()
    assert outliner.structure_version() > v, "a renamed joint"
    v = outliner.structure_version()
    rig.name = "ctrl_rig_x"
    bpy.context.view_layer.update()
    assert outliner.structure_version() > v, "a renamed skeleton"
    _object_mode()


def test_outliner_skips_the_steps_of_a_pose_drag():
    """While a move runs in Pose Mode every step updates the skeleton: the kit Outliner neither reads the skeleton
    nor rebuilds its rows; after the move a changed skeleton is read again."""
    outliner = import_module(kit.MODULE + ".ui.outliner")
    js = import_module(kit.MODULE + ".operators.joint_selection")
    _clear()
    skel, rig, _widgets = _rig()
    js.select(bpy.context, rig, "c03")
    bpy.context.view_layer.update()
    assert rig.mode == 'POSE'
    reads = []
    real_rows, real_moving = outliner._skeleton_rows, mj.transforming

    def rows(ob):
        reads.append(ob.name)
        return real_rows(ob)

    outliner._skeleton_rows = rows
    try:
        mj.transforming = lambda: True
        v = outliner.structure_version()
        pb = rig.pose.bones["c03"]
        for step in range(4):
            pb.location.x = 0.1 * (step + 1)
            rig.data.update_tag()
            bpy.context.view_layer.update()
        assert outliner.structure_version() == v and not reads, (outliner.structure_version(), v, reads)
        mj.transforming = lambda: False
        pb.location.x = 0.0
        rig.data.update_tag()
        bpy.context.view_layer.update()
        assert reads and outliner.structure_version() == v, "with no move running the skeleton is checked"
        pb.name = "c03_x"
        rig.data.update_tag()
        bpy.context.view_layer.update()
        assert outliner.structure_version() > v, "after the move a renamed joint is read again"
    finally:
        outliner._skeleton_rows, mj.transforming = real_rows, real_moving
    _object_mode()


def test_time_slider_reads_many_selected_bones_curves_in_one_pass():
    """Hundreds of selected controls: the Time Slider shares out each skeleton's curves in one pass instead of
    looking through every curve once per bone; every bone gets exactly the curves it had (its own channels and
    custom properties, also for names with dots, brackets or quotes), and the key frames are the same."""
    ts = import_module(kit.MODULE + ".ui.time_slider")
    tk = import_module(kit.MODULE + ".operators.time_keys")
    _clear()
    data = bpy.data.armatures.new("keys")
    ob = bpy.data.objects.new("keys", data)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT')
    names = ["a", "a.b", "a.b.c", 'ar"m', "a[1]", "spine", "spine.001", "x"]
    for i, n in enumerate(names):
        eb = data.edit_bones.new(n)
        eb.head, eb.tail = (i, 0, 0), (i, 0, 1)
    bpy.ops.object.mode_set(mode='POSE')
    for i, pb in enumerate(ob.pose.bones):
        for f in (1 + i, 10 + 2 * i):
            pb.location = (0.1 * f, 0, 0)
            pb.keyframe_insert("location", frame=f)
        if i % 2:
            pb["amount"] = 0.5
            pb.keyframe_insert('["amount"]', frame=30 + i)
    bones = list(ob.pose.bones)[:-1]                       # "x" not selected: its curves go to nobody
    want = {pb.as_pointer(): [fc.data_path + str(fc.array_index) for fc in tk.node_fcurves(pb)] for pb in bones}
    with _Count(tk, "node_fcurves") as looks:
        got = ts._bones_curves(bones)
    assert looks.calls == 0, "several bones: no per-bone look through the curves"
    assert {k: [fc.data_path + str(fc.array_index) for fc in v] for k, v in got.items()} == want
    per_bone = sorted({f for pb in bones for f, _b in ts.key_frames([pb])})
    assert [f for f, _b in ts.key_frames(bones)] == per_bone
    assert [f for f, _b in ts.key_frames(bones, keep=True)] == per_bone
    _object_mode()
