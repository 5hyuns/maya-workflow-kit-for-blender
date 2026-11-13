"""A joint click or a marquee over joints evaluates the scene as few times as its mode switches allow, with the same end
state and the same undo steps.

Every mode switch evaluates what is pending before it and what it changed after it, and each evaluation runs every
depsgraph handler (in a scene of thousands of objects each one costs several milliseconds even when it changes
little). A click on another skeleton's joint is three evaluations (out of Pose Mode, the selection with the joint,
into Pose Mode); a replace marquee over two posed skeletons is three as well, and its undo step evaluates nothing.
The joint is written before the switch into Pose Mode, which changes no bone selection; picks that are already
selected are not written off and on again."""

from importlib import import_module

import bpy

import kit

js = import_module(kit.MODULE + ".operators.joint_selection")
jm = import_module(kit.MODULE + ".operators.joint_marquee")
mj = import_module(kit.MODULE + ".ui.maya_joints")
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


def _edit_round(clear):
    """The skeletons through Edit Mode together: what each shows selected there (its bones' own selection and lead),
    or (``clear``) that selection taken off."""
    _object_mode()
    obs = bpy.context.scene.objects
    for ob in obs:
        ob.select_set(False)
    rigs = [obs[name] for name, _p, _n in RIGS]
    for ob in rigs:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = rigs[0]
    bpy.ops.object.mode_set(mode='EDIT')
    out = {}
    for ob in rigs:
        ebs = ob.data.edit_bones
        out[ob.name] = (sorted((e.name, e.select, e.select_head, e.select_tail) for e in ebs
                               if e.select or e.select_head or e.select_tail), ebs.active.name if ebs.active else None)
        if clear:
            for e in ebs:
                e.select = e.select_head = e.select_tail = False
            ebs.active = None
    bpy.ops.object.mode_set(mode='OBJECT')
    return out


def _reset():
    """Object Mode, nothing selected, no joint picked and no bone flag left from Edit Mode."""
    _edit_round(clear=True)
    for ob in bpy.context.scene.objects:
        ob.select_set(False)
        if ob.type == 'ARMATURE':
            for pb in ob.pose.bones:
                pb.select = False
            ob.data.bones.active = None
    bpy.context.view_layer.objects.active = None


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
    elif kind == "pose_A":
        _pose("rigA", picks=(("rigA", "a1"),))
    elif kind == "pose_A3":
        _pose("rigA", picks=(("rigA", "a1"), ("rigA", "a2"), ("rigA", "a4")))
    elif kind == "pose_AB":
        _pose("rigB", ("rigA",), (("rigA", "a1"), ("rigB", "b2")))
    elif kind == "pose_AC":
        _pose("rigA", ("rigC",), (("rigA", "a4"), ("rigC", "c1")))
    elif kind == "edit_B":
        obs["rigB"].select_set(True)
        bpy.context.view_layer.objects.active = obs["rigB"]
        bpy.ops.object.mode_set(mode='EDIT')
        eb = obs["rigB"].data.edit_bones["b1"]
        eb.select = eb.select_head = eb.select_tail = True
        obs["rigB"].data.edit_bones.active = eb
    elif kind == "pose_A_hidden_B":
        _pose("rigA", picks=(("rigA", "a1"),))
        obs["rigB"].hide_viewport = True
    else:
        raise AssertionError(kind)


def _dump():
    layer = bpy.context.view_layer
    out = {"mode": bpy.context.mode, "active": layer.objects.active.name if layer.objects.active else None,
           "lead": [getattr(n, "name", None) for n in cb.targets(bpy.context)]}
    for ob in bpy.context.scene.objects:
        rec = {"mode": ob.mode, "selected": ob.select_get(), "props": sorted(ob.keys())}
        if ob.type == 'ARMATURE':
            rec["picked"] = sorted(pb.name for pb in ob.pose.bones if pb.select)
            rec["lead"] = ob.data.bones.active.name if ob.data.bones.active else None
            if ob.mode == 'EDIT':
                rec["edit"] = sorted((e.name, e.select, e.select_head, e.select_tail) for e in ob.data.edit_bones
                                     if e.select or e.select_head or e.select_tail)
        out[ob.name] = rec
    return out


def _outcome(run):
    """``run``'s end state, the states after Undo and Redo of its undo step and the bones' own flags."""
    bpy.ops.ed.undo_push(message="before")
    try:
        run()
        err = None
    except RuntimeError as e:
        err = str(e)
    bpy.ops.ed.undo_push(message="Select")
    after = _dump()
    bpy.ops.ed.undo()
    undone = _dump()
    bpy.ops.ed.redo()
    redone = _dump()
    return {"err": err, "after": after, "undone": undone, "redone": redone, "bones": _edit_round(clear=False)}


def _joint_after_switch(ctx, ob, name, shift, ctrl):
    """A joint click written in this order: out of the other skeleton's mode, the replace's clearing, the skeleton
    selected and active, into Pose Mode, then the joint and its lead."""
    pb = ob.pose.bones[name]
    if (ctrl and not shift) or (shift and not ctrl and pb.select):
        pb.select = False
        if ob.data.bones.active == pb.bone:
            ob.data.bones.active = next((b.bone for b in ob.pose.bones if b.select), None)
        if not any(b.select for b in ob.pose.bones):
            if ctx.active_object == ob and ob.mode == 'POSE':
                bpy.ops.object.mode_set(mode='OBJECT')
            ob.select_set(False)
            if ctx.view_layer.objects.active == ob:
                ctx.view_layer.objects.active = next(iter(ctx.selected_objects), None)
        return
    if ctx.mode != 'OBJECT' and ctx.active_object != ob:
        bpy.ops.object.mode_set(mode='OBJECT')
    if not shift and not ctrl:
        for o in ctx.view_layer.objects:
            if o.type != 'ARMATURE':
                continue
            if o.mode == 'EDIT':
                for e in o.data.edit_bones:
                    if e.select or e.select_head or e.select_tail:
                        e.select = e.select_head = e.select_tail = False
                if o.data.edit_bones.active is not None:
                    o.data.edit_bones.active = None
            for p in o.pose.bones:
                if p.select:
                    p.select = False
            if o.data.bones.active is not None:
                o.data.bones.active = None
        for other in ctx.selected_objects:
            if other != ob:
                other.select_set(False)
    ob.select_set(True)
    ctx.view_layer.objects.active = ob
    if ob.mode != 'POSE':
        bpy.ops.object.mode_set(mode='POSE')
    ob.pose.bones[name].select = True
    ob.data.bones.active = ob.data.bones[name]


def test_a_joint_click_ends_as_with_the_joint_written_after_the_mode_switch():
    """Every start (Object Mode, Pose Mode on one or two skeletons, Edit Mode, a hidden target), joint (same
    skeleton, an already picked one, another skeleton) and modifier: the same objects, modes, joints, leads and
    Channel Box lead, the same states after Undo and Redo, the same bone flags in Edit Mode."""
    _scene()
    ctx = bpy.context
    try:
        for start in ("object", "object_mesh", "pose_A", "pose_A3", "pose_AB", "edit_B", "pose_A_hidden_B"):
            for rig, bone in (("rigA", "a2"), ("rigA", "a1"), ("rigB", "b3")):
                for mod, (shift, ctrl) in MODS.items():
                    _start(start)
                    ob = bpy.context.scene.objects[rig]
                    got = _outcome(lambda: js.select(ctx, ob, bone, shift, ctrl))
                    _start(start)
                    ob = bpy.context.scene.objects[rig]
                    want = _outcome(lambda: _joint_after_switch(ctx, ob, bone, shift, ctrl))
                    assert got == want, (start, rig, bone, mod, got, want)
    finally:
        _reset()


def _box_takes_joints_off(mode):
    """Blender's own box in Pose Mode (no Blender bone inside): a replace takes every joint off."""
    if mode == 'SET':
        for ob in bpy.context.scene.objects:
            if ob.mode == 'POSE':
                for pb in ob.pose.bones:
                    pb.select = False


def _skeleton_by_skeleton(ctx, hits, mode, snap):
    obs = bpy.context.scene.objects
    hits = {rig: names for rig, names in hits.items() if obs[rig].visible_get()}    # a hidden skeleton is no hit
    jm.restore(ctx, snap)
    shift, ctrl = jm.modifiers(mode)
    if mode in {'SET', 'ADD'}:
        for i, rig in enumerate(r for r in ("rigA", "rigB", "rigC") if r in hits):
            if i > 0:
                shift, ctrl = True, True
            js.select_many(ctx, obs[rig], hits[rig], shift, ctrl)
        return
    for rig in ("rigA", "rigB", "rigC"):
        for name in hits.get(rig, ()):
            js.select(ctx, obs[rig], name, shift, ctrl)


def test_a_marquee_over_picked_joints_ends_as_skeleton_by_skeleton():
    """A marquee whose joints Blender's box took off (and put back by the joint rules): the same end, Undo and Redo
    states as picking the joints skeleton by skeleton after putting the drag's selection back."""
    _scene()
    real = mj.region_pick
    hits = {}
    mj.region_pick = lambda _ctx, ob, _poly: list(hits.get(ob.name, ()))
    try:
        for start in ("object", "pose_A3", "pose_AB", "pose_AC", "pose_A_hidden_B"):
            for chosen in ({"rigA": ["a1", "a2"], "rigB": ["b2", "b4"]}, {"rigA": ["a0", "a4"], "rigB": ["b1"]},
                           {"rigA": ["a1", "a3"]}):
                for mode in MODS:
                    results = []
                    for how in ("marquee", "skeletons"):
                        _start(start)
                        hits.clear()
                        hits.update(chosen)
                        ctx = _Ctx(_space())
                        snap = jm.snapshot(ctx)
                        _box_takes_joints_off(mode)
                        if how == "marquee":
                            results.append(_outcome(lambda: jm.apply(ctx, POLY, mode, snap)))
                        else:
                            results.append(_outcome(lambda: _skeleton_by_skeleton(ctx, hits, mode, snap)))
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


def test_a_click_on_another_skeleton_evaluates_three_times():
    """Pose Mode on one skeleton, a click on another's joint: out of Pose Mode, the selection with the joint, into
    Pose Mode (the window's update after it finds nothing left). From Object Mode: two."""
    _scene()
    ctx = bpy.context
    try:
        for start, rig, bone, most in (("pose_A", "rigB", "b3", 3), ("pose_AB", "rigC", "c2", 3),
                                       ("object", "rigB", "b3", 2), ("object_mesh", "rigA", "a2", 2)):
            _start(start)
            bpy.context.view_layer.update()
            with _Rounds() as r:
                js.select(ctx, bpy.context.scene.objects[rig], bone)
                bpy.context.view_layer.update()
            assert r.n <= most, (start, rig, r.n, most)
            assert bpy.context.scene.objects[rig].mode == 'POSE'
            assert [pb.name for pb in bpy.context.scene.objects[rig].pose.bones if pb.select] == [bone]
    finally:
        _reset()


def test_a_replace_marquee_over_posed_skeletons_evaluates_three_times():
    """Two posed skeletons with their joints picked, a replace box over the same joints (Blender's box took them
    off): out of Pose Mode, the selection with the joints, into Pose Mode; the joints are written once each and the
    marquee's undo step evaluates nothing."""
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
            assert r.n <= 3, r.n
            assert in_push.n == 0, in_push.n
            assert len(writes) == sum(map(len, picks.values())), writes
            obs = bpy.context.scene.objects
            assert {n: sorted(pb.name for pb in obs[n].pose.bones if pb.select) for n in picks} == picks
            assert (obs["rigA"].mode, obs["rigB"].mode, bpy.context.view_layer.objects.active.name) == \
                ('POSE', 'POSE', "rigB")
    finally:
        mj.region_pick = real
        _reset()
