"""The shelf row, the Maya Outliner, the Range Slider and the Time Slider redraw on every frame change and every
selection change (Blender redraws those editors for any of them), so what each redraw reads must not grow with the
file: the Outliner finds its rows' objects without walking every object of the file, a named rig's joints are not
read to place the rows above a selection, the lights of defaultLightSet are listed once while the objects stay the
same, the Range Slider finds its gap in the header row with array operations, one shelf redraw reads its layout and
button records once, and one picked control's keys are found from its rig's curves split once. The results are the
same as before (same objects, same rows, same gap, same slots, same curves)."""

import random
import time
from importlib import import_module
from types import SimpleNamespace

import bpy

import kit

tree = import_module(kit.MODULE + ".ui.outliner_tree")
tree_edit = import_module(kit.MODULE + ".ui.outliner_tree_edit")
outliner = import_module(kit.MODULE + ".ui.outliner")
rb = import_module(kit.MODULE + ".ui.range_bar")
shelf = import_module(kit.MODULE + ".ui.shelf")
shelf_data = import_module(kit.MODULE + ".ui.shelf_data")
ts = import_module(kit.MODULE + ".ui.time_slider")
time_keys = import_module(kit.MODULE + ".operators.time_keys")
joints = import_module(kit.MODULE + ".operators.joints")


class _Count:
    """Counts the calls of a module attribute (function or class) while installed."""

    def __init__(self, module, name):
        self.module, self.name, self.calls = module, name, 0
        self.real = getattr(module, name)

    def __enter__(self):
        real = self.real

        def counted(*a, **k):
            self.calls += 1
            return real(*a, **k)
        setattr(self.module, self.name, counted)
        return self

    def __exit__(self, *exc):
        setattr(self.module, self.name, self.real)


def _clear():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for data in (bpy.data.armatures, bpy.data.meshes, bpy.data.lights):
        for d in list(data):
            data.remove(d)


def _many(n, me=None):
    me = me or bpy.data.meshes.new("pCubeShape")
    coll = bpy.context.scene.collection
    obs = []
    for i in range(n):
        ob = bpy.data.objects.new(f"pCube{i + 1}", me)
        coll.objects.link(ob)
        obs.append(ob)
    bpy.context.view_layer.update()
    return obs


# --- Outliner ------------------------------------------------------------------------------------------------------

def test_outliner_rows_find_their_objects_like_get():
    _clear()
    obs = _many(40)
    names = [o.name for o in obs] + ["nothing here", ""]
    for n in names:
        assert tree.object_named(n) == bpy.data.objects.get(n), n
    obs[3].name = "renamed"                          # no depsgraph update in between
    obs[5].name = "pCube4"                           # takes the old name of obs[3]
    for n in names + ["renamed", "pCube4"]:
        assert tree.object_named(n) == bpy.data.objects.get(n), n
    gone = obs[7].name
    version = outliner.objects_version()
    bpy.data.objects.remove(obs[7])
    bpy.context.view_layer.update()                  # as before every redraw
    assert outliner.objects_version() != version, "a removed object drops the kept names (none is kept removed)"
    lone = bpy.data.objects.new("lone", None)        # in no collection: no update flags it
    for n in names + ["renamed", "pCube4", gone, "lone"]:
        assert tree.object_named(n) == bpy.data.objects.get(n), n
    bpy.data.objects.remove(lone)
    assert tree.object_named("lone") is None


def test_outliner_row_states_do_not_walk_the_file():
    """Drawing rows looks each row's object up by name: in a file of 6,000 objects that cost a quarter of a
    millisecond per row (Blender walks the objects to find a name); the rows of the last objects are the slowest."""
    _clear()
    obs = _many(6000)
    rows = [tree.Row('OBJECT', o.name, "", 0, False, False, o.name, 'MESH', ('O', o.session_uid)) for o in obs[-300:]]
    ctx = bpy.context
    want = [(o.select_get(), False, not o.visible_get(), False) for o in obs[-300:]]
    t0 = time.perf_counter()
    # as one redraw does: the names read once for the redraw (when the build has them), then every row
    kw = {"names": tree.object_names()} if hasattr(tree, "object_names") else {}
    got = [tree.row_state(ctx, r, set(), set(), **kw) for r in rows]
    ms = (time.perf_counter() - t0) * 1000.0
    print("OUTLINER rows 300 of 6000 objects ms", round(ms, 2))
    assert got == want
    assert ms < 25.0, f"300 rows took {ms:.1f} ms"
    _clear()


def test_selection_ancestors_skip_a_named_rigs_joints():
    """The dim highlight on the rows above the selection: a named rig's joints are only read for a kit skeleton
    (``skeleton<N>``), whose root joint stands for it; the keys are the same."""
    _clear()
    arm = bpy.data.objects.new("hero", bpy.data.armatures.new("hero"))
    bpy.context.scene.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='EDIT')
    root = arm.data.edit_bones.new("root")
    root.tail = (0, 0, 1)
    for i in range(60):
        b = arm.data.edit_bones.new(f"b{i}")
        b.head, b.tail, b.parent = (0, 0, 1 + i), (0, 0, 2 + i), root
    bpy.ops.object.mode_set(mode='OBJECT')
    body = bpy.data.objects.new("body", bpy.data.meshes.new("bodyShape"))
    bpy.context.scene.collection.objects.link(body)
    body.parent = arm
    sk = joints.new_skeleton(bpy.context)
    joints.add_joint(sk, (0, 0, 0), None, length=0.5)
    bpy.ops.object.mode_set(mode='OBJECT')
    prop = bpy.data.objects.new("prop", bpy.data.meshes.new("propShape"))
    bpy.context.scene.collection.objects.link(prop)
    prop.parent = sk
    bpy.context.view_layer.update()
    for ob in bpy.data.objects:
        ob.select_set(False)
    body.select_set(True)
    bpy.context.view_layer.objects.active = body
    with _Count(tree, "_Bones") as built:
        keys = tree.selected_ancestors(bpy.context)
    assert keys == {('O', arm.session_uid)}, keys
    assert built.calls == 0, f"the named rig's joints were read ({built.calls})"
    body.select_set(False)
    prop.select_set(True)
    bpy.context.view_layer.objects.active = prop
    keys = tree.selected_ancestors(bpy.context)
    root_name = tree._Bones(sk).roots[0]
    assert keys == {('B', sk.session_uid, root_name)}, keys        # under the kit skeleton's root joint
    assert tree_edit._kit_skeleton(sk) and not tree_edit._kit_skeleton(arm)
    _clear()


def test_picked_joints_ancestors_walk_shared_parents_once():
    """Many picked joints of one skeleton: the rows above them are the same set as every joint's ``ancestor_keys``
    together, and each parent joint is walked once (not once per joint below it)."""
    _clear()
    arm = bpy.data.objects.new("rig", bpy.data.armatures.new("rig"))
    bpy.context.scene.collection.objects.link(arm)
    holder = bpy.data.objects.new("holder", None)
    bpy.context.scene.collection.objects.link(holder)
    arm.parent = holder
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='EDIT')
    prev = None
    names = []
    for i in range(40):                      # a chain with a short side branch at every joint
        b = arm.data.edit_bones.new(f"spine{i}")
        b.head, b.tail, b.parent = (0, 0, i), (0, 0, i + 1), prev
        side = arm.data.edit_bones.new(f"side{i}")
        side.head, side.tail, side.parent = (0, 0, i), (1, 0, i), b
        prev = b
        names += [b.name, side.name]
    bpy.ops.object.mode_set(mode='POSE')
    for pb in arm.pose.bones:
        pb.select = pb.name.startswith("side") or pb.name in ("spine39", "spine7")
    items = tree_edit.selected_items(bpy.context)
    assert len(items) == 42, len(items)
    want = set()
    for ob, bone in items:
        want.update(tree_edit.ancestor_keys(ob, bone))
    steps = []
    real = tree_edit._bone_parents_until
    tree_edit._bone_parents_until = lambda ob, name, done: steps.append(len(r := real(ob, name, done))) or r
    try:
        got = tree.selected_ancestors(bpy.context)
    finally:
        tree_edit._bone_parents_until = real
    assert got == want, (len(got), len(want), want - got, got - want)
    assert ('O', holder.session_uid) in got and ('O', arm.session_uid) in got
    assert len(steps) == 42 and sum(steps) == 40, (len(steps), sum(steps))   # each spine joint walked once
    bpy.ops.object.mode_set(mode='OBJECT')
    _clear()


def test_default_light_set_lists_the_lights_once():
    _clear()
    _many(50)
    for i in range(3):
        lt = bpy.data.objects.new(f"light{i}", bpy.data.lights.new(f"light{i}", 'POINT'))
        bpy.context.scene.collection.objects.link(lt)
    bpy.context.view_layer.update()
    scene = bpy.context.scene
    want = tree.default_set_members("defaultLightSet", scene)
    assert len(want) == 3
    tree._lights["key"] = None
    with _Count(tree, "default_set_members") as listed:
        for _i in range(5):
            assert tree._default_set_members("defaultLightSet", scene) == want
    assert listed.calls == 1, listed.calls
    lt = bpy.data.objects.new("light9", bpy.data.lights.new("light9", 'SPOT'))
    scene.collection.objects.link(lt)
    bpy.context.view_layer.update()
    assert tree._default_set_members("defaultLightSet", scene) == tree.default_set_members("defaultLightSet", scene)
    assert lt in tree._default_set_members("defaultLightSet", scene)
    assert tree._default_set_members("defaultObjectSet", scene) == []
    _clear()


# --- Range Slider --------------------------------------------------------------------------------------------------

def test_range_slider_gap_from_runs_matches_the_pixel_walk():
    rnd = random.Random(5)
    for _t in range(3000):
        n = rnd.randint(3, 200)
        palette = [(rnd.randint(0, 3), 7, 9) for _c in range(rnd.randint(1, 4))]
        row = []
        while len(row) < n:
            row += [rnd.choice(palette)] * rnd.randint(1, 40)
        row = row[:n]
        bg = row[2]
        min_w, skip = rnd.choice((0, 1, 3, 10, 40)), rnd.choice((0, 1, 2, 3))
        span = rb.bar_span(row, bg, min_w, skip)
        want = (span, rb.spare_after(row, span[1], bg, skip) if span is not None else 0)
        codes = rb._codes(row)
        assert rb.gap_of_runs(rb.row_runs(codes), len(codes), min_w, skip) == want, (row, min_w, skip)


def test_range_slider_reads_a_wide_header_row_quickly():
    """The header row comes from the framebuffer as bytes; finding the gap no longer makes a Python colour per pixel
    (an 8,000 px row took several milliseconds)."""
    import numpy as np
    w = 8000
    px = np.zeros((w, 4), np.uint8)
    px[:, :3] = 40                                             # header background
    for a, b in ((10, 200), (230, 400), (2800, 3000), (3050, 3300)):
        px[a:b, :3] = 90                                       # fields
    gpu = import_module("gpu")
    buf = px.reshape(1, w, 4)          # stands in for the framebuffer read: [row][pixel][RGBA] bytes
    compat = import_module(kit.MODULE + ".compat")
    real_read, real_fb = compat.read_region_row, gpu.state.active_framebuffer_get
    compat.read_region_row = lambda fb, region, y: buf
    gpu.state.active_framebuffer_get = lambda: None
    area = SimpleNamespace(as_pointer=lambda: 4242)
    region = SimpleNamespace(width=w, height=40)
    try:
        rb._gaps.clear()
        rb.find_gap(area, region, 20, playing=False)
        t0 = time.perf_counter()
        for _i in range(5):
            got = rb.find_gap(area, region, 20, playing=False)
        ms = (time.perf_counter() - t0) * 1000.0 / 5
    finally:
        compat.read_region_row, gpu.state.active_framebuffer_get = real_read, real_fb
        rb._gaps.clear()
    row = [tuple(p[:3]) for p in px.tolist()]
    span = rb.bar_span(row, row[2], min_w=rb.BAR_UNITS * 20 * 0.6)
    assert got == (span, rb.spare_after(row, span[1], row[2])), got
    print("RANGE gap 8000 px row ms", round(ms, 3))
    assert ms < 4.0, f"{ms:.2f} ms per header row"


# --- Shelf ---------------------------------------------------------------------------------------------------------

def test_shelf_redraw_reads_the_records_once():
    cur = shelf.current(None)
    data = shelf.user_data()
    saved = data.get("extra")
    added = {"label": "Mine", "icon": 'SCRIPT', "script": "", "menu": ""}
    sep = {"label": "Separator", "type": "separator"}
    data["extra"] = {cur: [added, sep, added, sep, added]}
    region = SimpleNamespace(width=900, height=80, tag_redraw=lambda: None, as_pointer=lambda: 9)
    try:
        n = shelf.factory_count(cur)
        want_seps = {n + 1, n + 3}
        want = [shelf.icon_rect(region, slot, 1.25) for slot in range(n + 7)]
        with _Count(shelf, "button_record") as rec, _Count(shelf, "_plan") as plans:
            plan = shelf._plan(region, 1.25)
            got = [shelf._plan_rect(plan, region, slot, 1.25) for slot in range(n + 7)]
            shelf.scroll_rects(region, 1.25, plan)
            shelf.rows_of(region, 1.25, plan)
        assert got == want
        assert set(plan[4]) == want_seps, plan[4]
        assert rec.calls == 0, f"records read per slot ({rec.calls})"
        assert plans.calls == 1, plans.calls
    finally:
        if saved is None:
            data.pop("extra", None)
        else:
            data["extra"] = saved
        shelf._factory_cache.clear()


# --- Time Slider ---------------------------------------------------------------------------------------------------

def _keyed_rig(bones=120, keys=(1, 10, 20)):
    _clear()
    arm = bpy.data.objects.new("rig", bpy.data.armatures.new("rig"))
    bpy.context.scene.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='EDIT')
    for i in range(bones):
        b = arm.data.edit_bones.new(f'ctl.{i}"q')               # a quote in the name: escaped in curve paths
        b.head, b.tail = (i, 0, 0), (i, 0, 1)
    bpy.ops.object.mode_set(mode='POSE')
    for k, pb in enumerate(arm.pose.bones):
        for f in keys:
            pb.location = (0.01 * f, 0, 0)
            pb.keyframe_insert("location", frame=f + (k % 3))
            pb.keyframe_insert("rotation_quaternion", frame=f)
    return arm


def test_one_picked_controls_keys_come_from_the_rigs_split_curves():
    """One picked control of a rig: its curves are the rig's curves split once (kept until the curves change), not
    every curve path of the rig read again on each redraw; same curves and keys as before."""
    arm = _keyed_rig()
    try:
        for pb in (arm.pose.bones[0], arm.pose.bones[57], arm.pose.bones[-1]):
            want = [(fc.data_path, fc.array_index) for fc in time_keys.node_fcurves(pb)]
            got = [(fc.data_path, fc.array_index) for fc in ts._bones_curves([pb])[pb.as_pointer()]]
            assert got == want and len(want) == 7, (pb.name, got, want)
        pb = arm.pose.bones[58]                           # location keys a frame after the rotation keys
        frames = ts.key_frames([pb])
        want = sorted({round(kp.co.x, 3) for fc in time_keys.node_fcurves(pb) for kp in fc.keyframe_points})
        assert [f for f, _b in frames] == want and len(want) == 6, (frames, want)
        with _Count(time_keys, "node_fcurves") as walked, _Count(ts, "_skeleton_parts") as parts:
            for _i in range(5):
                assert ts.key_frames([pb]) == frames
        assert walked.calls == 0, f"every curve of the rig read again ({walked.calls})"
        assert parts.calls == 0, f"redraws take the control's kept keys ({parts.calls} curve splits)"
        assert len(ts._PARTS) >= 1
    finally:
        bpy.ops.object.mode_set(mode='OBJECT')
        _clear()
