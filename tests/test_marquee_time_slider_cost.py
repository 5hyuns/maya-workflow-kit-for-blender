"""Box selection and the Time Slider stay light in big scenes. A marquee remembers and puts back the selection it
started from a collection at a time (thousands of objects, hundreds of joints) with the same result. The Time Slider
shares out a skeleton's curves with one look per curve, reads a curve's keys once until its Action changes (a new
selection reads no key again), asks for Sync Timeline Display's channels only when that is on, and a big mesh in
Edit Mode without point keys is not walked for its selected points. The ticks are the same as reading every key on
every redraw."""

import time
from importlib import import_module

import bmesh
import bpy
import numpy as np

import kit

jm = import_module(kit.MODULE + ".operators.joint_marquee")
cb = import_module(kit.MODULE + ".ui.channel_box")
cbc = import_module(kit.MODULE + ".ui.cb_channels")
ts = import_module(kit.MODULE + ".ui.time_slider")
tk = import_module(kit.MODULE + ".operators.time_keys")
pk = import_module(kit.MODULE + ".operators.point_keys")
compat = import_module(kit.MODULE + ".compat")


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
    for data in (bpy.data.armatures, bpy.data.meshes, bpy.data.actions):
        for d in list(data):
            data.remove(d)
    for coll in list(bpy.data.collections):
        bpy.data.collections.remove(coll)


def _armature(name, names):
    data = bpy.data.armatures.new(name)
    ob = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT')
    for i, n in enumerate(names):
        eb = data.edit_bones.new(n)
        eb.head, eb.tail = (0.1 * i, 0.0, 0.0), (0.1 * i, 0.0, 0.5)
    bpy.ops.object.mode_set(mode='OBJECT')
    return ob


def _state(skip=()):
    scene, layer = bpy.context.scene, bpy.context.view_layer
    objs = {ob.name: ob.select_get() for ob in scene.objects if ob.name not in skip}
    bones = {}
    for ob in scene.objects:
        if ob.type != 'ARMATURE':
            continue
        if ob.mode == 'EDIT':
            ebs = ob.data.edit_bones
            bones[ob.name] = ({eb.name: (eb.select, eb.select_head, eb.select_tail) for eb in ebs},
                              ebs.active.name if ebs.active else None)
        else:
            bones[ob.name] = (sorted(pb.name for pb in ob.pose.bones if pb.select),
                              ob.data.bones.active.name if ob.data.bones.active else None)
    act = layer.objects.active
    return objs, bones, act.name if act else None


def test_a_marquee_puts_back_the_selection_it_started_from():
    """``snapshot`` / ``restore`` (the selection before Blender's box, put back when the box hit joints): every
    object's selection (hidden and unlinked ones too), the active object and each skeleton's joint picks and lead
    joint come back; objects made since are left alone; only what differs is written, and no joint is asked one at a
    time."""
    _clear()
    scene, layer = bpy.context.scene, bpy.context.view_layer
    obs = []
    for i in range(300):
        ob = bpy.data.objects.new(f"e{i:03d}", None)
        scene.collection.objects.link(ob)
        obs.append(ob)
    off = bpy.data.collections.new("off")
    scene.collection.children.link(off)
    for i in range(5):
        off.objects.link(bpy.data.objects.new(f"off{i}", None))
    layer.layer_collection.children["off"].exclude = True
    rig_a = _armature("rigA", [f"a{i:03d}" for i in range(150)])
    rig_b = _armature("rigB", [f"b{i:02d}" for i in range(40)])
    for ob in obs[:100]:
        ob.select_set(True)
    obs[10].hide_set(True)                       # selected, then hidden: still selected
    layer.objects.active = obs[5]
    for pb in list(rig_a.pose.bones)[:50]:
        pb.select = True
    rig_a.data.bones.active = rig_a.data.bones["a010"]
    rig_b.data.bones.active = None
    want = _state()
    ctx = bpy.context
    snap = jm.snapshot(ctx)
    # what a box (and anything else) changed meanwhile
    for ob in obs[:50]:
        if ob is not obs[10]:
            ob.select_set(False)
    for ob in obs[150:250]:
        ob.select_set(True)
    layer.objects.active = obs[200]
    for pb in list(rig_a.pose.bones)[:25]:
        pb.select = False
    for pb in list(rig_a.pose.bones)[100:]:
        pb.select = True
    rig_a.data.bones.active = rig_a.data.bones["a120"]
    for pb in rig_b.pose.bones:
        pb.select = True
    late = bpy.data.objects.new("late", None)
    scene.collection.objects.link(late)
    late.select_set(True)
    with _Count(cb, "set_bone_selected") as writes, _Count(cb, "bone_selected") as asks:
        jm.restore(ctx, snap)
    assert _state(skip={"late"}) == want, "the selection the drag started from"
    assert late.select_get(), "an object made after the drag started is left alone"
    assert writes.calls == 25 + 50 + 40, f"only the joints that differ are written ({writes.calls})"
    assert asks.calls == 0, f"joint picks are read a skeleton at a time ({asks.calls} asked one by one)"
    with _Count(cb, "bone_selected") as asks:
        jm.snapshot(ctx)
    assert asks.calls == 0, f"the snapshot reads a skeleton's picks at once ({asks.calls} asked one by one)"
    # a skeleton in Edit Mode: its joints' select / head / tail flags and lead joint
    for ob in scene.objects:
        ob.select_set(False)
    rig_b.select_set(True)
    layer.objects.active = rig_b
    bpy.ops.object.mode_set(mode='EDIT')
    ebs = rig_b.data.edit_bones
    for i, eb in enumerate(ebs):
        eb.select, eb.select_head, eb.select_tail = i % 3 == 0, i % 2 == 0, i % 5 == 0
    ebs.active = ebs["b07"]
    want = _state()
    snap = jm.snapshot(ctx)
    for i, eb in enumerate(ebs):
        if i % 4 == 0:
            eb.select, eb.select_head, eb.select_tail = not eb.select, True, False
    ebs.active = ebs["b30"]
    jm.restore(ctx, snap)
    assert _state() == want, "Edit Mode joints come back with their head / tail flags and the lead"
    _object_mode()


def test_putting_back_many_objects_walks_the_scene_once():
    """A box that selected thousands of objects before its joint rules: putting the selection back costs about one
    pass over the scene (looking each object up by name walked the scene once per object)."""
    _clear()
    scene, layer = bpy.context.scene, bpy.context.view_layer
    obs = []
    for i in range(3000):
        ob = bpy.data.objects.new(f"m{i:04d}", None)
        scene.collection.objects.link(ob)
        obs.append(ob)
    _armature("rig", ["r0", "r1"])
    for ob in obs[:10]:
        ob.select_set(True)
    layer.objects.active = obs[0]
    ctx = bpy.context
    snap = jm.snapshot(ctx)
    for ob in obs[10:]:
        ob.select_set(True)                     # the box picked everything else
    t = time.perf_counter()
    names = [ob.name for ob in scene.objects]
    one_pass = time.perf_counter() - t
    t = time.perf_counter()
    jm.restore(ctx, snap)
    took = time.perf_counter() - t
    assert [ob.name for ob in scene.objects if ob.select_get()] == [ob.name for ob in obs[:10]]
    assert len(names) == 3001
    assert took < 40 * one_pass + 0.02, f"putting back 2990 objects took {took * 1000:.0f} ms " \
                                        f"(one pass {one_pass * 1000:.1f} ms)"


def test_time_slider_shares_out_curves_by_each_paths_bone():
    """Many selected bones: every bone gets exactly its own curves (names with dots, brackets, quotes and
    backslashes too); each curve's path is looked at once, whatever the number of name lengths, and a redraw with
    the same curves reuses that."""
    _clear()
    odd = ["a", "a.b", 'a"].x', "back\\slash", "q[1]", 'x"y', "a.b.c", 'n"]["m']
    names = odd + ["n" * k + f"{k}" for k in range(1, 55)] + [f"bone_{i:03d}" for i in range(400)]
    ob = _armature("keys", names)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode='POSE')
    for pb in ob.pose.bones:
        for f in (1, 7):
            pb.keyframe_insert("location", frame=f)
    for pb in list(ob.pose.bones)[:8]:
        pb["amount"] = 0.5
        pb.keyframe_insert('["amount"]', frame=3)
    bones = list(ob.pose.bones)
    want = {pb.as_pointer(): [fc.data_path + str(fc.array_index) for fc in tk.node_fcurves(pb)] for pb in bones}
    got = ts._bones_curves(bones)
    assert {k: [fc.data_path + str(fc.array_index) for fc in v] for k, v in got.items()} == want
    assert all(want[pb.as_pointer()] for pb in bones), "every bone has curves here"

    fcs = compat.id_fcurve_collection(ob)

    def best(fn, n=5):
        out = []
        for _i in range(n):
            t = time.perf_counter()
            fn()
            out.append(time.perf_counter() - t)
        return min(out)
    read = best(lambda: [fc.data_path for fc in fcs])
    share = best(lambda: ts._bones_curves(bones))
    # each curve's path is looked at once per skeleton and redraws reuse that: about reading the paths (a look per
    # path and name length took over ten times as long)
    assert share < 5 * read + 0.0005, (f"sharing out {len(fcs)} curves took {share * 1000:.1f} ms "
                                       f"(reading their paths {read * 1000:.1f} ms)")
    _object_mode()


def _reference_keys(nodes, path=None, index=None):
    """The Time Slider's keys read straight from the curves: sorted [(frame, all keys there are breakdowns)]."""
    frames = {}
    for node in nodes:
        for fc in tk.node_fcurves(node):
            if path is not None and (not fc.data_path.endswith(path) or fc.array_index != index):
                continue
            for kp in fc.keyframe_points:
                f = round(kp.co.x, 3)
                frames[f] = frames.get(f, True) and kp.type == 'BREAKDOWN'
    return sorted(frames.items())


def _keyed_rig():
    ob = _armature("anim", [f"c{i:02d}" for i in range(60)])
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode='POSE')
    for i, pb in enumerate(ob.pose.bones):
        for f in (1 + i % 5, 10 + i, 40):
            pb.location = (0.01 * f, 0.0, 0.0)
            pb.keyframe_insert("location", frame=f)
    for fc in compat.id_fcurves(ob)[::7]:
        fc.keyframe_points[0].type = 'BREAKDOWN'
    bpy.context.view_layer.update()
    return ob


class _Empties:
    """Counts ``numpy.empty`` (the Time Slider allocates two per curve it reads)."""

    def __enter__(self):
        self.real, self.calls = np.empty, 0

        def counted(*a, **k):
            self.calls += 1
            return self.real(*a, **k)
        np.empty = counted
        return self

    def __exit__(self, *exc):
        np.empty = self.real


def test_time_slider_reads_keys_once_until_their_action_changes():
    """A curve's keys are read once: redraws and a new selection of bones read none again. A key moved, retyped,
    deleted or set (each updates its Action), and an undo, show at once. The ticks always match the curves."""
    _clear()
    ob = _keyed_rig()
    bones = list(ob.pose.bones)
    first, other = bones[:40], bones[20:]
    curves = sum(len(tk.node_fcurves(pb)) for pb in first)
    assert ts.key_frames(first) == _reference_keys(first)
    with _Empties() as reads:
        for _redraw in range(3):
            assert ts.key_frames(first) == _reference_keys(first)
    assert reads.calls < curves, f"redraws read the keys again ({reads.calls} arrays for {curves} curves)"
    assert ts.key_frames(other) == _reference_keys(other)
    with _Empties() as reads:
        assert ts.key_frames(bones[25:35]) == _reference_keys(bones[25:35])
    assert reads.calls < 10, f"bones whose keys were read: none read again ({reads.calls})"
    fc = tk.node_fcurves(bones[31])[0]          # keys at 2, 40, 41
    edits = (
        ("moved", lambda: setattr(fc.keyframe_points[1], "co", (33.0, fc.keyframe_points[1].co.y))),
        ("retyped", lambda: setattr(fc.keyframe_points[2], "type", 'BREAKDOWN')),
        ("deleted", lambda: fc.keyframe_points.remove(fc.keyframe_points[0])),
        ("set", lambda: bones[31].keyframe_insert("location", frame=55)),
    )
    for what, edit in edits:
        assert ts.key_frames(other) == _reference_keys(other)
        edit()
        fc.update()
        bpy.context.view_layer.update()
        assert ts.key_frames(other) == _reference_keys(other), f"a {what} key shows"
    # a key moved, then the frame changes before any depsgraph update (keying during playback)
    assert ts.key_frames(other) == _reference_keys(other)
    fc.keyframe_points[-1].co.x = 61.0
    bpy.context.scene.frame_set(bpy.context.scene.frame_current + 1)
    assert ts.key_frames(other) == _reference_keys(other), "a key moved before a frame change shows"
    bpy.ops.ed.undo_push(message="before")
    moved = tk.node_fcurves(ob.pose.bones["c32"])[0]
    moved.keyframe_points[0].co.x = 77.0
    moved.update()
    bpy.context.view_layer.update()
    bpy.ops.ed.undo_push(message="moved")
    nodes = list(bpy.data.objects["anim"].pose.bones)[20:]
    assert 77.0 in [f for f, _b in ts.key_frames(nodes)]
    bpy.ops.ed.undo()
    nodes = list(bpy.data.objects["anim"].pose.bones)[20:]
    assert ts.key_frames(nodes) == _reference_keys(nodes), "an undo shows the keys from before"
    assert 77.0 not in [f for f, _b in ts.key_frames(nodes)]
    _object_mode()


def test_time_slider_asks_for_synced_channels_only_when_sync_is_on():
    """Sync Timeline Display off (or no channel selected): the selected nodes' keys are found without asking the
    Channel Box for each node's synced channels; on with a selected channel: each node is asked."""
    _clear()
    ob = _keyed_rig()
    nodes = list(ob.pose.bones)[:30]
    want = ts.key_frames(nodes)
    with _Count(cbc, "timeline_curves") as asks:
        assert ts.key_frames(nodes) == want
    assert asks.calls == 0, f"sync off: no per-node look ({asks.calls})"
    prefs = cbc._prefs()
    wm = bpy.context.window_manager
    old = (prefs.cb_sync_timeline, wm.allset_cb_selected)
    try:
        prefs.cb_sync_timeline = True
        with _Count(cbc, "timeline_curves") as asks:
            assert ts.key_frames(nodes) == want, "on without selected channels: every key"
        assert asks.calls == 0
        wm.allset_cb_selected = "tx"
        with _Count(cbc, "timeline_curves") as asks:
            synced = ts.key_frames(nodes)
        assert asks.calls == len(nodes), asks.calls
        assert synced == _reference_keys(nodes, "location", 0), "on: only Translate X keys"

    finally:
        prefs.cb_sync_timeline, wm.allset_cb_selected = old
    _object_mode()


def test_big_edit_mesh_without_point_keys_is_not_walked():
    """The Time Slider's point keys of a mesh in Edit Mode: with no keyed points the selected vertices are not
    collected (a big mesh took milliseconds per redraw); with keyed points the result is unchanged."""
    _clear()
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=150, y_subdivisions=150)
    ob = bpy.context.active_object
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    with _Count(pk, "point_paths") as walks:
        assert pk.selected_point_curves(ob) == []
    assert walks.calls == 0, "no point keys: the selection is not walked"
    bm = bmesh.from_edit_mesh(ob.data)
    for v in bm.verts:
        v.select = v.index in (3, 9)
    bm.select_flush_mode()
    bmesh.update_edit_mesh(ob.data)
    assert bpy.ops.allset.set_key('EXEC_DEFAULT', True) == {'FINISHED'}
    for v in bm.verts:
        v.select = v.index == 9
    bmesh.update_edit_mesh(ob.data)
    got = sorted((fc.data_path, fc.array_index) for fc in pk.selected_point_curves(ob))
    assert got == [("vertices[9].co", i) for i in range(3)], got
    _object_mode()


def test_time_slider_skips_the_curves_of_objects_without_animation():
    """Thousands of selected props: an object without animation data is not looked through for its curves or
    animation layers; keyed objects and keyed blendShape weights of an unkeyed mesh still give their ticks."""
    al = import_module(kit.MODULE + ".operators.anim_layers")
    _clear()
    scene = bpy.context.scene
    obs = []
    for i in range(400):
        ob = bpy.data.objects.new(f"p{i:03d}", None)
        scene.collection.objects.link(ob)
        obs.append(ob)
    keyed = obs[::50]
    for i, ob in enumerate(keyed):
        for f in (2 + i, 30):
            ob.location.x = 0.1 * f
            ob.keyframe_insert("location", index=0, frame=f)
    bpy.ops.mesh.primitive_cube_add()
    face = bpy.context.active_object
    face.shape_key_add(name="Basis")
    smile = face.shape_key_add(name="smile")
    smile.value = 0.5
    smile.keyframe_insert("value", frame=17)
    nodes = obs + [face]
    want = {}
    for ob in keyed:
        for fc in tk.node_fcurves(ob):
            for kp in fc.keyframe_points:
                want[round(kp.co.x, 3)] = False
    want[17.0] = False
    with _Count(tk, "node_fcurves") as looks, _Count(al, "hidden_base_curves") as layers:
        got = ts.key_frames(nodes)
    assert got == sorted(want.items()), got
    assert looks.calls == len(keyed) and layers.calls == len(keyed), \
        f"only the {len(keyed)} animated objects are looked through ({looks.calls}, {layers.calls})"
