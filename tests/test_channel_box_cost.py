"""The Channel Box stays light in big scenes and long animations:
- in Pose Mode the lead is the active joint, else the first picked shown one, found without a Python object for
  every picked joint (Blender reads every value field again after the panel's draw returns: many asks per redraw);
- the skeletons of the view layer and the kit deformers a handle (Empty / lattice) drives are found once and kept
  until the scene changes (an object added, removed or linked, a modifier edit, undo, a file load); a removed object
  or a renamed / removed modifier is never handed out;
- a channel's key state (keyed on this frame or not) reads a long curve's key frames in one call.
The answers are the same as looking through the whole scene (or every key) each time."""

import time
from importlib import import_module

import bpy
import numpy as np

import kit

cb = import_module(kit.MODULE + ".ui.channel_box")
deformers = import_module(kit.MODULE + ".operators.deformers")


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


def _handle_scene(extra=300):
    """Empty ``handle`` driving bend1 on ``host``, plus ``extra`` meshes with a modifier each."""
    _clear()
    handle = bpy.data.objects.new("bend1Handle", None)
    bpy.context.scene.collection.objects.link(handle)
    me = bpy.data.meshes.new("m")
    host = bpy.data.objects.new("host", me)
    bpy.context.scene.collection.objects.link(host)
    md = host.modifiers.new("bend1", 'SIMPLE_DEFORM')
    md.origin = handle
    for i in range(extra):
        o = bpy.data.objects.new(f"other{i}", me)
        bpy.context.scene.collection.objects.link(o)
        o.modifiers.new("Subdivision", 'SUBSURF')
    bpy.context.view_layer.update()
    return handle, host


def _driven_names(handle):
    return [(m.id_data.name, m.name) for m in cb.driven_modifiers(handle)]


def _walk_names(handle):
    return [(m.id_data.name, m.name) for m in deformers.driven_modifiers(handle)]


def test_handle_inputs_are_found_once_until_the_scene_changes():
    handle, host = _handle_scene()
    with _Count(deformers, "driven_modifiers") as scans:
        for _ in range(20):
            names = [m.name for m in cb._inputs(handle)]
            assert names == ["bend1"], names
    # a Channel Box redraw asked about 2 + rows times; every one looked through every object's modifiers
    assert scans.calls == 1, f"{scans.calls} walks over every object for one unchanged handle"
    # a second deformer on another mesh: the update finds it
    host2 = bpy.data.objects.new("host2", host.data)
    bpy.context.scene.collection.objects.link(host2)
    host2.modifiers.new("bend2", 'SIMPLE_DEFORM').origin = handle
    bpy.context.view_layer.update()
    assert _driven_names(handle) == _walk_names(handle) == [("host", "bend1"), ("host2", "bend2")]
    # removed / renamed without a depsgraph update in between: looked up again
    bpy.data.objects.remove(host)
    assert _driven_names(handle) == _walk_names(handle) == [("host2", "bend2")]
    host2.modifiers["bend2"].name = "Deform"
    assert _driven_names(handle) == _walk_names(handle) == []
    host2.modifiers["Deform"].name = "bend2"
    bpy.context.view_layer.update()
    assert _driven_names(handle) == _walk_names(handle) == [("host2", "bend2")]
    # the deformer handed to another handle
    other = bpy.data.objects.new("bend2Handle", None)
    bpy.context.scene.collection.objects.link(other)
    host2.modifiers["bend2"].origin = other
    bpy.context.view_layer.update()
    assert _driven_names(handle) == _walk_names(handle) == []
    assert _driven_names(other) == _walk_names(other) == [("host2", "bend2")]
    # a mesh is no handle
    assert cb.driven_modifiers(host2) == deformers.driven_modifiers(host2) == []


def test_moving_the_handle_keeps_its_inputs():
    """A move (transform-only updates) keeps the kept deformers; a selection change finds them again."""
    handle, _host = _handle_scene()
    cb._inputs(handle)
    with _Count(deformers, "driven_modifiers") as scans:
        for i in range(10):
            handle.location.x = 0.1 * i
            bpy.context.view_layer.update()
            assert [m.name for m in cb._inputs(handle)] == ["bend1"]
    assert scans.calls == 0, f"a move looked through every object {scans.calls} times"
    with _Count(deformers, "driven_modifiers") as scans:
        handle.select_set(True)
        bpy.context.view_layer.update()
        assert [m.name for m in cb._inputs(handle)] == ["bend1"]
    assert scans.calls == 1


def _long_curve(ob, frames):
    """A Translate X curve on ``ob`` with a key on each of ``frames`` (float32, like Blender stores them)."""
    ob.keyframe_insert("location", index=0, frame=1)
    fc = kit.fcurves(ob).find("location", index=0)
    fc.keyframe_points.add(len(frames) - len(fc.keyframe_points))
    co = np.zeros(2 * len(frames), dtype=np.float32)
    co[0::2] = frames
    fc.keyframe_points.foreach_set("co", co)
    fc.update()
    return fc


def test_key_state_of_a_long_curve_is_the_same():
    _clear()
    ob = bpy.data.objects.new("pCube1", bpy.data.meshes.new("pCubeShape1"))
    bpy.context.scene.collection.objects.link(ob)
    frames = np.arange(0, 3000, dtype=np.float32) * 1.5 + 0.25     # 0.25, 1.75, 3.25 ...
    fc = _long_curve(ob, frames)
    assert len(fc.keyframe_points) == 3000
    for frame in (0, 1, 2, 3, 4, 10, 100, 101, 4499, 4500, 5000, -1, 0.75, 0.7499999, 1.25, 2.2500001, 1000.6):
        want = any(abs(kp.co[0] - frame) < 0.5 for kp in fc.keyframe_points)
        assert cb.keyed_at(fc, frame) == want, (frame, want)
        assert cb.channel_state(ob, "tx", frame) == ('KEYED' if want else 'ANIMATED'), frame
    short = _long_curve(bpy.data.objects.new("pCube2", None), np.array([1.0, 5.0, 9.5], dtype=np.float32))
    for frame in (1, 2, 5, 9, 10, 10.5):
        assert cb.keyed_at(short, frame) == any(abs(kp.co[0] - frame) < 0.5 for kp in short.keyframe_points)


def test_key_state_of_a_long_curve_costs_little():
    """A key on every frame (motion capture): ten rows' states on every redraw were a Python loop over every key."""
    _clear()
    ob = bpy.data.objects.new("pCube1", bpy.data.meshes.new("pCubeShape1"))
    bpy.context.scene.collection.objects.link(ob)
    _long_curve(ob, np.arange(1, 20001, dtype=np.float32))
    t = time.perf_counter()
    states = [cb.channel_state(ob, "tx", 19000.4) for _ in range(10)]
    ms = 1000 * (time.perf_counter() - t)
    print(f"10 key states of a 20,000-key curve: {ms:.2f} ms")
    assert states == ['KEYED'] * 10
    assert ms < 40, f"10 key states of a 20,000-key curve took {ms:.1f} ms"
