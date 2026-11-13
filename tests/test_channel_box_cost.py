"""The Channel Box stays light in big scenes:
- in Pose Mode the lead is the active joint, else the first picked shown one, found without a Python object for
  every picked joint (Blender reads every value field again after the panel's draw returns: many asks per redraw);
- the skeletons of the view layer are found once and kept until the scene changes (an object added, removed or
  linked, undo, a file load); a removed object is never handed out.
The answers are the same as looking through the whole scene each time."""

import time
from importlib import import_module

import bpy

import kit

cb = import_module(kit.MODULE + ".ui.channel_box")


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
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')


def _clear():
    _object_mode()
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for data in (bpy.data.armatures, bpy.data.meshes):
        for d in list(data):
            data.remove(d)
    bpy.context.view_layer.update()


def _skeleton(name, bones):
    """Armature ``name`` with ``bones`` bones in a row (b0 > b1 > ...), left in Object Mode."""
    arm = bpy.data.objects.new(name, bpy.data.armatures.new(name))
    bpy.context.scene.collection.objects.link(arm)
    _object_mode()
    for o in bpy.context.view_layer.objects:
        o.select_set(o == arm)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='EDIT')
    prev = None
    for i in range(bones):
        eb = arm.data.edit_bones.new(f"b{i}")
        eb.head, eb.tail = (0.0, 0.0, 0.1 * i), (0.0, 0.0, 0.1 * i + 0.1)
        eb.parent = prev
        prev = eb
    bpy.ops.object.mode_set(mode='OBJECT')
    return arm


def _plain(n):
    me = bpy.data.meshes.new("plain")
    coll = bpy.context.scene.collection
    for i in range(n):
        coll.objects.link(bpy.data.objects.new(f"plain{i}", me))


def _pose(*arms):
    """Pose Mode on ``arms`` (the first one active)."""
    _object_mode()
    for o in bpy.context.view_layer.objects:
        o.select_set(o in arms)
    bpy.context.view_layer.objects.active = arms[0]
    bpy.ops.object.mode_set(mode='POSE')
    for arm in arms:
        assert arm.mode == 'POSE'


def _pick(arm, names, active=None):
    for pb in arm.pose.bones:
        cb.set_bone_selected(pb, pb.name in names)
    arm.data.bones.active = arm.data.bones[active] if active else None


def _walk_pose_objects():
    """``pose_objects`` as a walk over every object of the view layer."""
    arm = cb.pose_armature()
    if arm is None:
        return []
    return [arm] + [o for o in bpy.context.view_layer.objects
                    if o is not arm and o.type == 'ARMATURE' and o.mode == 'POSE']


def _walk_lead():
    """``lead`` from the full list of picked joints."""
    arm = cb.pose_armature()
    act = arm.data.bones.active
    pb = arm.pose.bones.get(act.name) if act is not None else None
    if pb is not None and pb.select and not pb.hide:
        return pb
    sel = cb.selected_bones()
    return sel[0] if sel else None


def test_lead_is_the_active_or_first_picked_joint():
    _clear()
    a = _skeleton("rigA", 6)
    b = _skeleton("rigB", 6)
    _pose(a, b)
    cases = [
        ({"b2", "b4"}, set(), "b4"),          # active joint picked: it leads
        ({"b2", "b4"}, set(), "b1"),          # active joint not picked: the first picked of the active skeleton
        (set(), {"b3", "b5"}, "b0"),          # nothing picked on the active skeleton: the other one's first
        (set(), set(), "b0"),                 # nothing picked
        ({"b2", "b4"}, {"b1"}, None),         # no active joint
    ]
    for picked_a, picked_b, active in cases:
        _pick(a, picked_a, active)
        _pick(b, picked_b)
        want = _walk_lead()
        got = cb.lead()
        assert got == want, (picked_a, picked_b, active, got, want)
    # the active joint picked but hidden: the first shown picked one
    _pick(a, {"b1", "b3"}, "b1")
    a.pose.bones["b1"].hide = True
    assert cb.lead() == a.pose.bones["b3"] == _walk_lead()
    a.pose.bones["b1"].hide = False
    _object_mode()


def test_pose_objects_match_a_walk_over_the_view_layer():
    _clear()
    _plain(20)
    a = _skeleton("rigA", 3)
    b = _skeleton("rigB", 3)
    c = _skeleton("rigC", 3)
    bpy.context.view_layer.update()
    _pose(a, c)
    assert cb.pose_objects() == _walk_pose_objects() == [a, c]
    # another skeleton enters Pose Mode: its mode is read on every call
    _object_mode()
    _pose(b, a, c)
    assert cb.pose_objects() == _walk_pose_objects() == [b, a, c]
    # renamed, then removed without a depsgraph update in between: looked up again, never handed out stale
    c.name = "rigC_renamed"
    assert cb.pose_objects() == _walk_pose_objects()
    _object_mode()
    _pose(b, a, c)
    bpy.data.objects.remove(c)
    got = cb.pose_objects()
    assert [o.name for o in got] == [o.name for o in _walk_pose_objects()] == ["rigB", "rigA"]
    # a new skeleton linked in: the update drops the kept list
    d = _skeleton("rigD", 3)
    bpy.context.view_layer.update()
    _pose(d, a, b)
    assert cb.pose_objects() == _walk_pose_objects() == [d, a, b]
    _object_mode()


def test_lead_cost_does_not_grow_with_the_scene():
    """The value fields' getters ask for the lead with no picked active joint: no list of every picked joint and no
    walk over the 6,000 objects per call."""
    _clear()
    arm = _skeleton("rig", 300)
    _plain(6000)
    bpy.context.view_layer.update()
    _pose(arm)
    _pick(arm, {f"b{i}" for i in range(1, 300)}, "b0")      # 299 picked, the active joint is not
    want = _walk_lead()
    assert want == arm.pose.bones["b1"]
    scene = bpy.context.scene
    scene.allset_cb.tx_text                                    # the kept skeleton list is found here
    with _Count(cb, "selected_bones") as listed:
        t = time.perf_counter()
        for _ in range(50):
            scene.allset_cb.tx_text
            assert cb.lead() == want
        ms = 1000 * (time.perf_counter() - t)
    print(f"100 lead lookups among 6,000 objects: {ms:.2f} ms")
    assert listed.calls == 0, f"the lead listed every picked joint {listed.calls} times"
    # looking at every object (6,000) took > 1 ms per call; asking for the lead is a few array reads
    assert ms < 25, f"100 lead lookups took {ms:.1f} ms"
    _object_mode()
