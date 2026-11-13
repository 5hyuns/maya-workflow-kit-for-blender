"""A joint click or marquee that leaves one mode and enters Pose Mode does both switches and the selection in one
operator call, so the scene is evaluated once instead of after each switch, with the same end state, undo steps,
pivot and pick order; a marquee's joints are found without walking up each hit joint's parents.

Blender evaluates the scene before and after each operator call from Python, not between the operators of a macro.
When a depsgraph handler of the kit would act on the Object Mode state between the switches (the Maya pivot point of
Object Mode, pivot axes that follow the lead), the switches go one by one as before."""

from importlib import import_module

import bpy
import numpy as np

import kit

js = import_module(kit.MODULE + ".operators.joint_selection")
jm = import_module(kit.MODULE + ".operators.joint_marquee")
mj = import_module(kit.MODULE + ".ui.maya_joints")
po = import_module(kit.MODULE + ".operators.pick_order")
pv = import_module(kit.MODULE + ".operators.pivot")
up = import_module(kit.MODULE + ".operators.undo_pairs")
cb = import_module(kit.MODULE + ".ui.channel_box")

RIGS = (("rigA", "a", 6), ("rigB", "b", 5), ("rigC", "c", 4))
MODS = {"SET": (False, False), "XOR": (True, False), "SUB": (False, True), "ADD": (True, True)}
POLY = [(0, 0), (10, 0), (10, 10), (0, 10)]


class _Ctx:
    """bpy.context with a 3D View's space (the marquee checks each skeleton is shown there)."""

    def __init__(self, space):
        self.space_data = space

    def __getattr__(self, name):
        return getattr(bpy.context, name)


def _space():
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                return area.spaces.active
    raise AssertionError("no 3D View in the startup file")


def _object_mode():
    for ob in bpy.context.scene.objects:
        ob.hide_viewport = False
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in bpy.context.scene.objects:
        if ob.mode != 'OBJECT':
            bpy.context.view_layer.objects.active = ob
            bpy.ops.object.mode_set(mode='OBJECT')


def _scene():
    """Three skeletons (the first deforms a mesh) and a plain mesh."""
    _object_mode()
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for data in (bpy.data.armatures, bpy.data.meshes):
        for d in list(data):
            data.remove(d)
    scene = bpy.context.scene
    for name, prefix, n in RIGS:
        data = bpy.data.armatures.new(name)
        ob = bpy.data.objects.new(name, data)
        scene.collection.objects.link(ob)
        bpy.context.view_layer.objects.active = ob
        bpy.ops.object.mode_set(mode='EDIT')
        prev = None
        for i in range(n):
            eb = data.edit_bones.new(f"{prefix}{i}")
            eb.head, eb.tail = (i, 0.0, 0.0), (i, 0.0, 1.0)
            if i % 2:
                eb.parent = prev
            prev = eb
        bpy.ops.object.mode_set(mode='OBJECT')
    me = bpy.data.meshes.new("box")
    me.from_pydata([(0, 0, 0), (1, 0, 0), (1, 1, 0)], [], [(0, 1, 2)])
    scene.collection.objects.link(bpy.data.objects.new("box", me))
    skin = bpy.data.objects.new("skin", me.copy())
    scene.collection.objects.link(skin)
    skin.modifiers.new("Armature", 'ARMATURE').object = bpy.data.objects["rigA"]
    _maya_pivot_axes()                      # the kit's "Maya Pivot" orientation exists from here on


def _reset():
    _object_mode()
    scene = bpy.context.scene
    for ob in scene.objects:
        ob.select_set(False)
        if ob.type == 'ARMATURE':
            for pb in ob.pose.bones:
                pb.select = False
            ob.data.bones.active = None
    bpy.context.view_layer.objects.active = None
    scene.tool_settings.transform_pivot_point = 'ACTIVE_ELEMENT'
    for slot in scene.transform_orientation_slots:
        if slot.type != 'GLOBAL':
            slot.type = 'GLOBAL'
    bpy.context.view_layer.update()         # the kit's handlers see the empty selection (pick order, lead)


def _pose(active, others=(), picks=()):
    obs = bpy.context.scene.objects
    for name in (active,) + tuple(others):
        obs[name].select_set(True)
    bpy.context.view_layer.objects.active = obs[active]
    bpy.ops.object.mode_set(mode='POSE')
    for rig, bone in picks:
        obs[rig].pose.bones[bone].select = True
        obs[rig].data.bones.active = obs[rig].data.bones[bone]


def _maya_pivot_axes():
    """The Move / Rotate axes on the kit's "Maya Pivot" orientation (a turned object pivot)."""
    from mathutils import Matrix
    layer = bpy.context.view_layer
    keep = layer.objects.active
    layer.objects.active = bpy.context.scene.objects["box"]
    assert pv.set_custom_orientation(bpy.context, Matrix.Identity(3))
    layer.objects.active = keep


def _start(kind):
    _reset()
    obs = bpy.context.scene.objects
    base, _sep, extra = kind.partition("+")
    if base == "object_mesh":
        obs["box"].select_set(True)
        bpy.context.view_layer.objects.active = obs["box"]
    elif base == "object_C":
        obs["rigC"].select_set(True)
        bpy.context.view_layer.objects.active = obs["rigC"]
    elif base == "pose_A":
        _pose("rigA", picks=(("rigA", "a1"),))
    elif base == "pose_AB":
        _pose("rigB", ("rigA",), (("rigA", "a1"), ("rigB", "b2")))
    elif base == "edit_mesh":
        obs["box"].select_set(True)
        bpy.context.view_layer.objects.active = obs["box"]
        bpy.ops.object.mode_set(mode='EDIT')
    elif base != "object":
        raise AssertionError(kind)
    bpy.context.view_layer.update()         # (the handlers see the start, then the pivot / axes are set)
    if extra == "bbc":
        bpy.context.scene.tool_settings.transform_pivot_point = 'BOUNDING_BOX_CENTER'
    elif extra == "axes":
        for i in pv.PIVOT_SLOTS:
            bpy.context.scene.transform_orientation_slots[i].type = pv.ORIENT_NAME
    bpy.context.view_layer.update()


def _dump():
    layer = bpy.context.view_layer
    scene = bpy.context.scene
    out = {"mode": bpy.context.mode, "active": layer.objects.active.name if layer.objects.active else None,
           "lead": [getattr(n, "name", None) for n in cb.targets(bpy.context)],
           "pivot": scene.tool_settings.transform_pivot_point,
           "slots": [slot.type for slot in scene.transform_orientation_slots],
           "order": [o.name for o in po.ordered(bpy.context)]}
    for ob in scene.objects:
        rec = {"mode": ob.mode, "selected": ob.select_get()}
        if ob.type == 'ARMATURE':
            rec["picked"] = sorted(pb.name for pb in ob.pose.bones if pb.select)
            rec["lead"] = ob.data.bones.active.name if ob.data.bones.active else None
        out[ob.name] = rec
    return out


def _outcome(run):
    """``run``'s end state and the states after Undo and Redo of its undo step."""
    bpy.ops.ed.undo_push(message="before")
    try:
        run()
        err = None
    except RuntimeError as e:
        err = str(e)
    bpy.context.view_layer.update()
    bpy.ops.ed.undo_push(message="Select")
    after = _dump()
    bpy.ops.ed.undo()
    undone = _dump()
    bpy.ops.ed.redo()
    redone = _dump()
    return {"err": err, "after": after, "undone": undone, "redone": redone}


class _OneByOne:
    """The switches one by one (the way without the one-call switch)."""

    def __enter__(self):
        self.real = getattr(js, "_one_switch", None)
        js._one_switch = lambda *_a, **_k: None

    def __exit__(self, *exc):
        if self.real is None:
            del js._one_switch
        else:
            js._one_switch = self.real


def _box_takes_joints_off(mode):
    """Blender's own box in Pose Mode (no Blender bone inside): a replace takes every joint off."""
    if mode == 'SET':
        for ob in bpy.context.scene.objects:
            if ob.mode == 'POSE':
                for pb in ob.pose.bones:
                    pb.select = False


STARTS = ("object", "object_mesh", "object_C", "pose_A", "pose_AB", "edit_mesh", "pose_AB+bbc", "pose_A+axes",
          "object_C+axes", "edit_mesh+bbc")


def test_a_click_in_one_call_ends_as_with_the_switches_one_by_one():
    """Every start (Object / Pose / mesh Edit Mode, a Bounding Box Center pivot, Maya pivot axes), joint and
    modifier: the same objects, modes, joints, leads, pivot, orientation and pick order, before and after Undo /
    Redo."""
    _scene()
    ctx = bpy.context
    try:
        for start in STARTS:
            for rig, bone in (("rigA", "a2"), ("rigA", "a1"), ("rigB", "b3"), ("rigC", "c2")):
                for mod, (shift, ctrl) in MODS.items():
                    results = []
                    for one_by_one in (False, True):
                        _start(start)
                        ob = bpy.context.scene.objects[rig]
                        if one_by_one:
                            with _OneByOne():
                                results.append(_outcome(lambda: js.select(ctx, ob, bone, shift, ctrl)))
                        else:
                            results.append(_outcome(lambda: js.select(ctx, ob, bone, shift, ctrl)))
                    assert results[0] == results[1], (start, rig, bone, mod, results)
    finally:
        _reset()


def test_a_marquee_in_one_call_ends_as_with_the_switches_one_by_one():
    """A marquee over joints of one or two skeletons from Object / Pose Mode (Blender's box took the joints off),
    every mode: the same end, Undo and Redo states, pivot, orientation and pick order."""
    _scene()
    real = mj.region_pick
    hits = {}
    mj.region_pick = lambda _ctx, ob, _poly: list(hits.get(ob.name, ()))
    try:
        for start in ("object", "object_mesh", "pose_A", "pose_AB", "pose_AB+bbc", "pose_A+axes", "object_C+axes"):
            for chosen in ({"rigA": ["a1", "a2"], "rigB": ["b2", "b4"]}, {"rigA": ["a0", "a4"], "rigB": ["b1"]},
                           {"rigB": ["b1", "b3"], "rigC": ["c0"]}, {"rigA": ["a1", "a3"]}):
                for mode in MODS:
                    results = []
                    for one_by_one in (False, True):
                        _start(start)
                        hits.clear()
                        hits.update(chosen)
                        ctx = _Ctx(_space())
                        snap = jm.snapshot(ctx)
                        _box_takes_joints_off(mode)
                        if one_by_one:
                            with _OneByOne():
                                results.append(_outcome(lambda: jm.apply(ctx, POLY, mode, snap)))
                        else:
                            results.append(_outcome(lambda: jm.apply(ctx, POLY, mode, snap)))
                    assert results[0] == results[1], (start, chosen, mode, results)
    finally:
        mj.region_pick = real
        _reset()


class _Rounds:
    """Counts depsgraph evaluations that ran the update handlers."""

    def __enter__(self):
        self.n = 0

        def count(*_a):
            self.n += 1
        self._fn = count
        bpy.app.handlers.depsgraph_update_post.append(count)
        return self

    def __exit__(self, *exc):
        bpy.app.handlers.depsgraph_update_post.remove(self._fn)


def test_a_click_on_another_skeleton_evaluates_once():
    """Pose Mode on one skeleton (or Object Mode), a click on another skeleton's joint: out of the mode, the
    selection and into Pose Mode in one evaluation. With a Bounding Box Center pivot (mesh Edit Mode's) the switches
    go one by one: Object Mode's Maya pivot point is set between them, as before."""
    _scene()
    ctx = bpy.context
    try:
        for start, rig, bone, most in (("pose_A", "rigB", "b3", 1), ("pose_AB", "rigC", "c2", 1),
                                       ("object", "rigB", "b3", 1), ("object_mesh", "rigA", "a2", 1),
                                       ("edit_mesh", "rigB", "b3", 2), ("pose_A+bbc", "rigB", "b3", 2)):
            _start(start)
            with _Rounds() as r:
                js.select(ctx, bpy.context.scene.objects[rig], bone)
                bpy.context.view_layer.update()
            assert r.n <= most, (start, rig, r.n, most)
            assert bpy.context.scene.objects[rig].mode == 'POSE'
            assert [pb.name for pb in bpy.context.scene.objects[rig].pose.bones if pb.select] == [bone]
            assert bpy.context.scene.tool_settings.transform_pivot_point == 'ACTIVE_ELEMENT', start
    finally:
        _reset()


def test_a_replace_marquee_over_posed_skeletons_evaluates_once():
    """Two posed skeletons with their joints picked, a replace box over the same joints (Blender's box took them
    off): out of Pose Mode, the selection and the joints, into Pose Mode in one evaluation; the joints are written
    once each and the undo step evaluates nothing."""
    _scene()
    picks = {"rigA": ["a0", "a1", "a2", "a3", "a4", "a5"], "rigB": ["b0", "b1", "b2", "b3"]}
    real = mj.region_pick
    mj.region_pick = lambda _ctx, ob, _poly: list(picks.get(ob.name, ()))
    try:
        _start("pose_AB")
        ctx = _Ctx(_space())
        jm.apply(ctx, POLY, 'SET', jm.snapshot(ctx))      # the joints of a first box
        bpy.context.view_layer.update()
        for _rep in range(2):
            snap = jm.snapshot(ctx)
            _box_takes_joints_off('SET')
            bpy.context.view_layer.update()
            writes = []
            real_write = cb.set_bone_selected
            cb.set_bone_selected = lambda pb, state: (writes.append(pb.name), real_write(pb, state))
            try:
                with _Rounds() as r:
                    jm.apply(ctx, POLY, 'SET', snap)
                    with _Rounds() as in_push:
                        up.push(bpy.context.scene, "Select")
                    bpy.context.view_layer.update()
            finally:
                cb.set_bone_selected = real_write
            assert r.n <= 1, r.n
            assert in_push.n == 0, in_push.n
            assert len(writes) == sum(map(len, picks.values())), writes
            obs = bpy.context.scene.objects
            assert {n: sorted(pb.name for pb in obs[n].pose.bones if pb.select) for n in picks} == picks
            assert (obs["rigA"].mode, obs["rigB"].mode, bpy.context.view_layer.objects.active.name) == \
                ('POSE', 'POSE', "rigB")
    finally:
        mj.region_pick = real
        _reset()


def _touching_one_by_one(a, b, poly):
    """The touch rule edge by edge for every segment (each end inside by the crossing rule, or a proper crossing of
    an edge), as plain arrays."""
    pg = np.asarray(poly, np.float64).reshape(-1, 2)

    def inside(p):
        x, y = p[:, 0], p[:, 1]
        res = np.zeros(len(p), bool)
        for i in range(len(pg)):
            (x1, y1), (x2, y2) = pg[i], pg[i - 1]
            if y1 != y2:
                res ^= ((y1 > y) != (y2 > y)) & (x < (x2 - x1) * (y - y1) / (y2 - y1) + x1)
        return res

    out = inside(a) | inside(b)
    ax, ay, bx, by = a[:, 0], a[:, 1], b[:, 0], b[:, 1]
    for i in range(len(pg)):
        (ex0, ey0), (ex1, ey1) = pg[i - 1], pg[i]
        d1 = (ex1 - ex0) * (ay - ey0) - (ey1 - ey0) * (ax - ex0)
        d2 = (ex1 - ex0) * (by - ey0) - (ey1 - ey0) * (bx - ex0)
        d3 = (bx - ax) * (ey0 - ay) - (by - ay) * (ex0 - ax)
        d4 = (bx - ax) * (ey1 - ay) - (by - ay) * (ex1 - ax)
        out |= (d1 * d2 < 0) & (d3 * d4 < 0)
    return out


def test_the_touch_test_matches_edge_by_edge_on_edges_and_corners():
    """Segments on a coarse grid (ends on the box's edges and corners, segments along its sides) and random ones:
    boxes given from any corner, a flat and a thin box, lassos — the same hits as the edge-by-edge rule."""
    rng = np.random.default_rng(7)
    grid = rng.integers(0, 12, (6000, 4)).astype(np.float64)
    a, b = grid[:, :2], grid[:, 2:]
    ra, rb = rng.uniform(-5, 15, (3000, 2)), rng.uniform(-5, 15, (3000, 2))
    polys = ([(2, 3), (9, 3), (9, 8), (2, 8)], [(9, 8), (2, 8), (2, 3), (9, 3)], [(2, 3), (2, 8), (9, 8), (9, 3)],
             [(9, 3), (2, 3), (2, 8), (9, 8)], [(2, 5), (9, 5), (9, 5), (2, 5)], [(4, 1), (4, 1), (4, 10), (4, 10)],
             [(5, 5), (5, 5), (5, 5), (5, 5)], [(1, 1), (10, 2), (8, 9), (2, 7)], [(2, 2), (10, 2), (6, 9)],
             [(1, 1), (6, 4), (11, 1), (11, 11), (6, 7), (1, 11)])
    for poly in polys:
        for p, q in ((a, b), (ra, rb)):
            assert np.array_equal(mj._touching(p, q, poly), _touching_one_by_one(p, q, poly)), poly


def _chain(n):
    """A skeleton of ``n`` joints, each the child of the one before (Maya joints)."""
    data = bpy.data.armatures.new("chain")
    ob = bpy.data.objects.new("chain", data)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT')
    prev = None
    for i in range(n):
        eb = data.edit_bones.new(f"j{i:03d}")
        eb.head, eb.tail = (0.05 * i, 0.0, 0.0), (0.05 * (i + 1), 0.0, 0.0)
        eb.parent = prev
        eb.use_connect = prev is not None
        prev = eb
    bpy.ops.object.mode_set(mode='OBJECT')
    return ob


def _region_joint_by_joint(ctx, ob, poly):
    """The marquee's joints the long way: every hit joint's depth walked up to the root, the top one kept."""
    js_ = mj.skeleton(ob, ctx.scene)
    names, a, b, ok, owner = mj._pick_lines(ctx, ob, js_)
    hit = np.zeros(len(names), bool)
    use = np.flatnonzero(ok)
    hit[owner[use[_touching_one_by_one(a[use], b[use], poly)]]] = True
    order = list(js_)
    joints = [(mj.depth(js_, n), order.index(n), n) for i, n in enumerate(names) if hit[i] and js_[n].shape is None]
    return [min(joints)[2]] if joints else []


class _Count:
    def __init__(self, mod, name):
        self.mod, self.name, self.calls = mod, name, 0

    def __enter__(self):
        self.real = getattr(self.mod, self.name)

        def wrapped(*a, **k):
            self.calls += 1
            return self.real(*a, **k)
        setattr(self.mod, self.name, wrapped)
        return self

    def __exit__(self, *exc):
        setattr(self.mod, self.name, self.real)


def test_a_marquee_over_a_long_chain_walks_no_parents_per_joint():
    """A box around a chain of 120 joints picks its top joint, the same one as before, without walking up from each
    hit joint to the root (that walk grows with the joints times their depth)."""
    _scene()
    ob = _chain(120)
    try:
        from mathutils import Matrix
        region = type("R", (), {"width": 400, "height": 400, "x": 0, "y": 0})()
        persp = Matrix.OrthoProjection('XY', 4) @ Matrix.Scale(0.2, 4)
        rv3d = type("V", (), {"perspective_matrix": persp})()

        class _View(_Ctx):
            def __getattr__(self, name):
                if name == "region":
                    return region
                if name == "region_data":
                    return rv3d
                return getattr(bpy.context, name)
        ctx = _View(_space())
        box = [(150, 150), (250, 150), (250, 250), (150, 250)]
        want = _region_joint_by_joint(ctx, ob, box)
        with _Count(mj, "depth") as walks:
            got = [mj.region_pick(ctx, ob, box) for _ in range(3)]
        assert got[0] == got[1] == got[2] == want and want == ["j000"], (got, want)
        assert walks.calls == 0, f"a parent walk per hit joint: {walks.calls}"
    finally:
        bpy.data.objects.remove(ob)
        _reset()
