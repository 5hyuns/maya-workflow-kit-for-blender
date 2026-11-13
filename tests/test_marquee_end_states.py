"""A marquee over joints ends in the same state however its picks are written: for replace, Shift (toggle), Ctrl
(remove) and Ctrl+Shift (add), over one skeleton or two, with a plain object in the box too, starting from Object
Mode (nothing / a mesh / another skeleton selected) or Pose Mode (the boxed skeleton, two skeletons, another
skeleton), every object's mode and selection, the active object and each skeleton's picked and lead joints are those
of picking the joints skeleton by skeleton (the first group with the drag's modifiers, the rest added; a toggle or a
removal joint by joint). Picking writes no undo step of its own."""

import json
from importlib import import_module

import bpy

import kit

jm = import_module(kit.MODULE + ".operators.joint_marquee")
js = import_module(kit.MODULE + ".operators.joint_selection")
mj = import_module(kit.MODULE + ".ui.maya_joints")

HITS_ONE = {"rigA": ["a0", "a2", "a3"]}
HITS_TWO = {"rigA": ["a0", "a2", "a3"], "rigB": ["b1", "b3"]}


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
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')


def _scene():
    _object_mode()
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for data in (bpy.data.armatures, bpy.data.meshes):
        for d in list(data):
            data.remove(d)
    scene = bpy.context.scene
    for name, prefix, n in (("rigA", "a", 6), ("rigB", "b", 5), ("rigC", "c", 4)):
        data = bpy.data.armatures.new(name)
        ob = bpy.data.objects.new(name, data)
        scene.collection.objects.link(ob)
        bpy.context.view_layer.objects.active = ob
        bpy.ops.object.mode_set(mode='EDIT')
        for i in range(n):
            eb = data.edit_bones.new(f"{prefix}{i}")
            eb.head, eb.tail = (i, 0.0, 0.0), (i, 0.0, 1.0)
        bpy.ops.object.mode_set(mode='OBJECT')
    mesh = bpy.data.meshes.new("box")
    scene.collection.objects.link(bpy.data.objects.new("box", mesh))


def _reset():
    """Object Mode, nothing selected, no lead joint."""
    layer = bpy.context.view_layer
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in bpy.context.scene.objects:
        ob.select_set(False)
        if ob.type == 'ARMATURE':
            for pb in ob.pose.bones:
                pb.select = False
            ob.data.bones.active = None
    layer.objects.active = None


def _pose(active, others=(), picks=()):
    obs = bpy.context.scene.objects
    for name in (active,) + tuple(others):
        obs[name].select_set(True)
    bpy.context.view_layer.objects.active = obs[active]
    bpy.ops.object.mode_set(mode='POSE')
    for rig, bone in picks:
        obs[rig].pose.bones[bone].select = True
        obs[rig].data.bones.active = obs[rig].data.bones[bone]


def _start(kind):
    _reset()
    obs = bpy.context.scene.objects
    if kind == "object":
        return
    if kind == "object_mesh":
        obs["box"].select_set(True)
        bpy.context.view_layer.objects.active = obs["box"]
    elif kind == "object_rigC":
        obs["rigC"].select_set(True)
        bpy.context.view_layer.objects.active = obs["rigC"]
    elif kind == "pose_A":
        _pose("rigA", picks=(("rigA", "a1"),))
    elif kind == "pose_AB":
        _pose("rigB", ("rigA",), (("rigA", "a1"), ("rigB", "b2")))
    elif kind == "pose_C":
        _pose("rigC", picks=(("rigC", "c0"),))
    elif kind == "pose_AC":
        _pose("rigA", ("rigC",), (("rigA", "a4"), ("rigC", "c1")))
    else:
        raise AssertionError(kind)


def _box_result():
    """What Blender's box changes before the joint rules run: the plain object in the box is selected (and a joint
    in Pose Mode)."""
    obs = bpy.context.scene.objects
    if bpy.context.mode == 'OBJECT':
        obs["box"].select_set(True)
    else:
        for ob in obs:
            if ob.mode == 'POSE':
                ob.pose.bones[0].select = True


def _dump():
    layer = bpy.context.view_layer
    out = {"mode": bpy.context.mode, "active": layer.objects.active.name if layer.objects.active else None}
    for ob in bpy.context.scene.objects:
        rec = {"mode": ob.mode, "selected": ob.select_get(), "props": sorted(ob.keys())}
        if ob.type == 'ARMATURE':
            rec["picked"] = sorted(pb.name for pb in ob.pose.bones if pb.select)
            rec["lead"] = ob.data.bones.active.name if ob.data.bones.active else None
        out[ob.name] = rec
    return out


def _per_skeleton(ctx, hits, mode, snap):
    """The joint rules written skeleton by skeleton (``joint_selection.select_many`` / ``select``)."""
    jm.restore(ctx, snap)
    obs = bpy.context.scene.objects
    picks = [(obs[rig], name) for rig in ("rigA", "rigB", "rigC") for name in hits.get(rig, ())]
    shift, ctrl = jm.modifiers(mode)
    if mode in {'SET', 'ADD'}:
        for i, rig in enumerate(r for r in ("rigA", "rigB", "rigC") if r in hits):
            if i > 0:
                shift, ctrl = True, True
            js.select_many(ctx, obs[rig], hits[rig], shift, ctrl)
    else:
        for ob, name in picks:
            js.select(ctx, ob, name, shift, ctrl)
    return [n for _o, n in picks]


STARTS = ("object", "object_mesh", "object_rigC", "pose_A", "pose_AB", "pose_C", "pose_AC")
POLY = [(0, 0), (10, 0), (10, 10), (0, 10)]


def _run(how, start, hits, mode):
    _start(start)
    ctx = _Ctx(_space())
    snap = jm.snapshot(ctx)
    _box_result()
    if how == "marquee":
        picked = jm.apply(ctx, POLY, mode, snap)
    else:
        picked = _per_skeleton(ctx, hits, mode, snap)
    return picked, _dump()


def test_marquee_end_states_match_picking_skeleton_by_skeleton():
    _scene()
    real = mj.region_pick
    hits = {}
    mj.region_pick = lambda _ctx, ob, _poly: list(hits.get(ob.name, ()))
    states = {}
    try:
        for start in STARTS:
            for label, chosen in (("one", HITS_ONE), ("two", HITS_TWO)):
                for mode in ('SET', 'ADD', 'SUB', 'XOR'):
                    hits.clear()
                    hits.update(chosen)
                    got = _run("marquee", start, hits, mode)
                    want = _run("per_skeleton", start, hits, mode)
                    key = f"{start} {label} {mode}"
                    states[key] = got[1]
                    assert got == want, (key, got, want)
    finally:
        mj.region_pick = real
        _reset()
    print("MARQUEE_END_STATES " + json.dumps(states, sort_keys=True))
    # replace over two skeletons from Object Mode: both skeletons end in Pose Mode, the last one leads
    two = states["object two SET"]
    assert (two["rigA"]["mode"], two["rigB"]["mode"], two["active"]) == ('POSE', 'POSE', "rigB"), two
    assert two["rigA"]["picked"] == ["a0", "a2", "a3"] and two["rigB"]["picked"] == ["b1", "b3"], two
    assert (two["rigA"]["lead"], two["rigB"]["lead"]) == ("a3", "b3"), two
    assert not two["box"]["selected"], "joints in the box drop the plain object"
    # add with another skeleton selected: it goes to Pose Mode with the boxed ones
    add = states["object_rigC two ADD"]
    assert [add[r]["mode"] for r in ("rigA", "rigB", "rigC")] == ['POSE'] * 3 and add["active"] == "rigB", add


def test_a_marquee_pushes_no_undo_step_while_picking():
    """The marquee's joint rules push no undo step of their own: with the drag's one step pushed after them, one undo
    goes back to the selection from before the drag."""
    _scene()
    real = mj.region_pick
    mj.region_pick = lambda _ctx, ob, _poly: list(HITS_TWO.get(ob.name, ()))
    try:
        for start in ("object", "pose_AB"):
            _start(start)
            bpy.ops.ed.undo_push(message="before the marquee")
            before = _dump()
            ctx = _Ctx(_space())
            snap = jm.snapshot(ctx)
            _box_result()
            jm.apply(ctx, POLY, 'SET', snap)
            bpy.ops.ed.undo_push(message="Select")
            assert _dump() != before
            bpy.ops.ed.undo()
            assert _dump() == before, (start, _dump(), before)
    finally:
        mj.region_pick = real
        _reset()


class _ModeSwitches:
    """Counts ``bpy.ops.object.mode_set`` calls made by joint_selection (each switch evaluates the scene before and
    after it)."""

    def __enter__(self):
        real = js.bpy
        self.calls, self.real = 0, real
        outer = self

        class _Object:
            def __getattr__(self, name):
                op = getattr(real.ops.object, name)
                if name != "mode_set":
                    return op

                def counted(*a, **k):
                    outer.calls += 1
                    return op(*a, **k)
                return counted

        class _Ops:
            object = _Object()

            def __getattr__(self, name):
                return getattr(real.ops, name)

        class _Bpy:
            ops = _Ops()

            def __getattr__(self, name):
                return getattr(real, name)
        js.bpy = _Bpy()
        return self

    def __exit__(self, *exc):
        js.bpy = self.real


def test_a_marquee_over_two_skeletons_switches_mode_once_each_way():
    """Replace / add over two skeletons: at most one switch out of the mode the drag started in and one into Pose
    Mode (skeleton by skeleton took a switch out and back in per added skeleton)."""
    _scene()
    real = mj.region_pick
    mj.region_pick = lambda _ctx, ob, _poly: list(HITS_TWO.get(ob.name, ()))
    counts = {}
    try:
        for start, mode in (("object", 'SET'), ("object_rigC", 'ADD'), ("pose_AB", 'SET'), ("pose_C", 'ADD')):
            _start(start)
            ctx = _Ctx(_space())
            snap = jm.snapshot(ctx)
            _box_result()
            with _ModeSwitches() as switches:
                jm.apply(ctx, POLY, mode, snap)
            counts[(start, mode)] = switches.calls
    finally:
        mj.region_pick = real
        _reset()
    print("MARQUEE_MODE_SWITCHES", counts)
    assert counts[("object", 'SET')] == 1 and counts[("object_rigC", 'ADD')] == 1, counts
    assert counts[("pose_AB", 'SET')] == 2 and counts[("pose_C", 'ADD')] == 2, counts
