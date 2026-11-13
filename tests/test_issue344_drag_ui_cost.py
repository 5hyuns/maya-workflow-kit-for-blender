"""Issue #344: the Maya UI that redraws on every step of a drag stays cheap.

While a rig control is dragged in Maya mode the top bar (Status Line), the Channel Box dock and the Time Slider redraw
on every mouse step. What they ask on each redraw is answered without walking everything again: the Status Line's
workspace list looks each workspace up once, a dock area's role and a marked editor's kind read the Properties tab
list of the space type once, the picked bones are read in one call per skeleton, and the Time Slider reads a curve's
keys in one call. The answers are the same as before."""

import math
from importlib import import_module
from types import SimpleNamespace

import bpy
from mathutils import Vector

import kit

sw = import_module(kit.MODULE + ".switch")
ws_mod = import_module(kit.MODULE + ".ui.workspaces")
user_ws = import_module(kit.MODULE + ".ui.user_workspaces")
cb = import_module(kit.MODULE + ".ui.channel_box")
md = import_module(kit.MODULE + ".ui.maya_dock")
mw = import_module(kit.MODULE + ".ui.marked_window")
ts = import_module(kit.MODULE + ".ui.time_slider")
compat = import_module(kit.MODULE + ".compat")


def _reference_entries():
    """The Status Line workspace list built the long way: one search of the file per Maya workspace."""
    out = [(name, ws_mod.find(name), ws_mod.LABELS[name]) for name in ws_mod.IN_TEMPLATE]
    saved = user_ws.saved_names()
    out += [(("user", name), user_ws.find(name), name) for name in saved]
    out += [(None, ws, ws.name) for ws in bpy.data.workspaces
            if sw.template_of(ws) is None and user_ws.user_name(ws) not in saved]
    return out


def test_workspace_list_looks_each_workspace_up_once():
    bpy.ops.wm.read_homefile(use_factory_startup=True)
    win = bpy.context.window_manager.windows[0]
    sw.enter_layout(win)                                       # Maya Classic, appended
    ws_mod.activate(bpy.context, win, "Animation")
    twin = next(ws for ws in bpy.data.workspaces if sw.template_of(ws) is None)
    twin[sw.TEMPLATE_KEY] = "Animation"                        # two workspaces of one template: the first one counts
    try:
        calls = []
        real = sw.template_of
        sw.template_of = lambda ws: calls.append(ws.name) or real(ws)
        try:
            got = ws_mod.entries()
            n = len(calls)
            calls.clear()
            want = _reference_entries()
            long_way = len(calls)
        finally:
            sw.template_of = real
        assert got == want, (got, want)
        count = len(bpy.data.workspaces)
        assert n <= count, f"one template lookup per workspace ({n} lookups, {count} workspaces)"
        assert long_way > n, (long_way, n)
        anim = [r for r in got if r[0] == "Animation"]
        assert anim and anim[0][1] == ws_mod.find("Animation"), anim
        with bpy.context.temp_override(window=win):
            assert ws_mod.dropdown_get(None) == next(i for i, r in enumerate(got) if r[1] == win.workspace)
    finally:
        del twin[sw.TEMPLATE_KEY]


def test_is_maya_workspace_answers_stay_the_same():
    """A workspace is a Maya one by its keys, or by the Status Line strip's mask in one of its Image Editors."""
    bpy.ops.wm.read_homefile(use_factory_startup=True)
    plain = [ws for ws in bpy.data.workspaces]
    assert not any(sw.is_maya_workspace(ws) for ws in plain)
    win = bpy.context.window_manager.windows[0]
    maya = sw.enter_layout(win)
    assert sw.is_maya_workspace(maya)
    keys = {k: maya[k] for k in (sw.PREV_KEY, sw.TEMPLATE_KEY, sw.USER_KEY) if k in maya}
    for k in keys:
        del maya[k]
    try:
        assert sw.is_maya_workspace(maya), "the strip's mask marks it"
        assert sw.template_of(maya) == sw.TEMPLATE_WORKSPACE
    finally:
        for k, v in keys.items():
            maya[k] = v


def _rig(name, count, x):
    arm = bpy.data.objects.new(name, bpy.data.armatures.new(name))
    bpy.context.scene.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    prev = None
    for i in range(count):
        eb = arm.data.edit_bones.new(f"{name}{i}")
        eb.head, eb.tail = Vector((x, 0, 0.1 * i)), Vector((x, 0, 0.1 * i + 0.1))
        eb.parent = prev
        prev = eb
    bpy.ops.object.mode_set(mode='OBJECT')
    return arm


def test_picked_bones_are_read_in_one_call_per_skeleton():
    bpy.ops.wm.read_homefile(use_factory_startup=True)
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    a, b = _rig("a", 60, 0.0), _rig("b", 40, 1.0)
    for ob in (a, b):
        ob.select_set(True)
    bpy.context.view_layer.objects.active = a
    bpy.ops.object.mode_set(mode='POSE')                      # both skeletons in Pose Mode
    try:
        assert b.mode == 'POSE'
        for arm, step in ((a, 3), (b, 4)):
            for i, pb in enumerate(arm.pose.bones):
                cb.set_bone_selected(pb, i % step == 0)
                compat.set_bone_hidden(pb, i % 5 == 0)
        a.data.bones.active = a.data.bones["a3"]
        want = [pb for arm in cb.pose_objects() for pb in arm.pose.bones
                if pb.select and not pb.hide]
        calls = []
        real = cb.bone_selected
        cb.bone_selected = lambda pb: calls.append(pb.name) or real(pb)
        try:
            got = cb.selected_bones()
        finally:
            cb.bone_selected = real
        assert [pb.name for pb in got] == [pb.name for pb in want] and len(got) > 10, \
            ([pb.name for pb in got], [pb.name for pb in want])
        assert all(isinstance(pb, bpy.types.PoseBone) and pb.id_data in (a, b) for pb in got)
        assert not calls, f"no bone is asked one by one ({len(calls)})"
        assert cb.lead() == a.pose.bones["a3"]
        assert [n.name for n in cb.targets()][:1] == ["a3"]
        for pb in a.pose.bones:
            cb.set_bone_selected(pb, False)
        for pb in b.pose.bones:
            cb.set_bone_selected(pb, False)
        assert cb.selected_bones() == [] and cb.lead() is None
    finally:
        bpy.ops.object.mode_set(mode='OBJECT')


class _Counted:
    """The RNA struct of SpaceProperties, counting how often its property list is walked."""

    def __init__(self, rna, walks):
        self._rna, self._walks = rna, walks
        self.identifier = rna.identifier

    @property
    def properties(self):
        self._walks.append(1)
        return self._rna.properties


def _space(walks, on=(), header=False):
    rna = bpy.types.SpaceProperties.bl_rna
    flags = {p.identifier: p.identifier in on for p in rna.properties if p.identifier.startswith("show_properties_")}
    space = SimpleNamespace(bl_rna=_Counted(rna, walks), show_region_header=header, **flags)
    return SimpleNamespace(type='PROPERTIES', spaces=SimpleNamespace(active=space))


def test_dock_roles_and_editor_kinds_read_the_tab_list_once():
    walks = []
    mw._FLAG_NAMES.clear()
    later = sorted(compat.LATER_PROPERTIES_TABS)
    for _round in range(20):
        for kind, mark in mw.KINDS.items():
            area = _space(walks, ("show_properties_tool", *mark))
            assert mw.kind_of(area) == kind and md.role(area) is None, kind
            assert mw.kind_of(_space(walks, ("show_properties_tool", *mark, *later))) == kind, "newer tabs don't count"
            assert mw.kind_of(_space(walks, ("show_properties_tool", *mark), header=True)) is None
        for role, flag in md.ROLE_FLAGS.items():
            area = _space(walks, ("show_properties_tool", flag))
            assert md.role(area) == role and mw.kind_of(area) is None, role
            assert md.role(_space(walks, ("show_properties_tool", flag, *later))) == role
            assert md.role(_space(walks, ("show_properties_tool", flag, "show_properties_render"))) is None
            assert md.role(_space(walks, (flag,))) is None, "the Tool tab is part of the mark"
        assert md.role(_space(walks, ("show_properties_tool",))) is None, "the Tool Settings dock has no role"
    assert len(walks) <= 1, f"the tab list of a space type is read once ({len(walks)} reads)"
    flags = md._flags(_space(walks).spaces.active)
    assert "show_properties_tool" in flags and all(f.startswith("show_properties_") for f in flags)


def test_time_slider_reads_a_curves_keys_in_one_call():
    """The Time Slider's ticks: every key frame (rounded to 1/1000), a frame with only breakdown keys is a
    breakdown; read the same from several curves of a node."""
    bpy.ops.wm.read_homefile(use_factory_startup=True)
    ob = bpy.data.objects.new("e", None)
    bpy.context.scene.collection.objects.link(ob)
    for f in (1, 4.25, 8, 12.0004, 20):
        ob.location.x = f
        ob.keyframe_insert("location", index=0, frame=f)
    for f in (4.25, 9, 20):
        ob.keyframe_insert("rotation_euler", index=2, frame=f)
    curves = kit.fcurves(ob)
    loc = next(c for c in curves if c.data_path == "location")
    rot = next(c for c in curves if c.data_path == "rotation_euler")
    loc.keyframe_points[1].type = 'BREAKDOWN'
    rot.keyframe_points[0].type = 'BREAKDOWN'                # 4.25: breakdown on both curves
    rot.keyframe_points[2].type = 'BREAKDOWN'                # 20: a regular key on the other curve wins
    loc.keyframe_points[2].type = 'EXTREME'
    want = {}
    for fc in (loc, rot):
        for kp in fc.keyframe_points:
            f = round(kp.co.x, 3)
            want[f] = want.get(f, True) and kp.type == 'BREAKDOWN'
    ob.select_set(True)
    got = ts.key_frames([ob])
    assert got == sorted(want.items()), (got, sorted(want.items()))
    assert dict(got)[4.25] is True and dict(got)[20.0] is False and dict(got)[8.0] is False
    assert [f for f, _b in got] == [1.0, 4.25, 8.0, 9.0, 12.0, 20.0]
    assert ts._breakdown_value() == bpy.types.Keyframe.bl_rna.properties["type"].enum_items["BREAKDOWN"].value


def _circle(name, n=12, r=0.15):
    me = bpy.data.meshes.new(name)
    me.from_pydata([(r * math.cos(2 * math.pi * i / n), r * math.sin(2 * math.pi * i / n), 0.0) for i in range(n)],
                   [(i, (i + 1) % n) for i in range(n)], [])
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def test_dragging_one_skeleton_keeps_the_other_skeletons_lines():
    """Two skeletons with control shapes; a pose of one is dragged: each drag step builds the lines of the skeleton
    that moved only (another one moved by the update is built too), and the joined lines equal a fresh build of
    both. A control shape's own geometry changing or a new frame looks at every skeleton again; the update after the
    drag only at the skeleton it touched."""
    mj = import_module(kit.MODULE + ".ui.maya_joints")
    import numpy as np
    bpy.ops.wm.read_homefile(use_factory_startup=True)
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    a, b = _rig("a", 12, 0.0), _rig("b", 12, 1.5)
    ctrl = _circle("ctrl")
    for arm in (a, b):
        for i, pb in enumerate(arm.pose.bones):
            if i % 3 == 1:
                pb.custom_shape = ctrl
    for ob in bpy.data.objects:
        ob.select_set(False)
    bpy.context.view_layer.objects.active = a
    a.select_set(True)
    bpy.ops.object.mode_set(mode='POSE')
    space = next(ar.spaces.active for s in bpy.data.screens for ar in s.areas if ar.type == 'VIEW_3D')
    view = SimpleNamespace(space_data=space, region_data=SimpleNamespace(is_perspective=True),
                           scene=bpy.context.scene, view_layer=bpy.context.view_layer, visible_objects=[a, b],
                           mode='POSE', screen=None)
    built = []
    real_parts, real_moving = mj._parts, mj.transforming
    mj._parts = lambda ob, *args, **kw: built.append(ob.name) or real_parts(ob, *args, **kw)
    mj.transforming = lambda: True                    # a move / rotate / scale runs

    def fresh():
        """Both skeletons built again from scratch (what the view would draw without anything kept)."""
        mj._forget()                                  # nothing kept
        got = mj._joined(view)
        return np.array(got[0]), np.array(got[1])

    try:
        mj.changed()
        mj._joined(view)
        assert sorted(built) == ["a", "b"], built
        pb = a.pose.bones[4]
        pb.rotation_mode = 'XYZ'
        for step in range(1, 4):
            built.clear()
            pb.rotation_euler = (0.25 * step, 0.0, 0.1 * step)
            bpy.context.view_layer.update()           # this drag step's depsgraph update
            got = mj._joined(view)
            assert built == ["a"], f"step {step}: only the dragged skeleton is built ({built})"
            pts, cols = np.array(got[0]), np.array(got[1])
            want = fresh()
            assert pts.shape == want[0].shape and np.allclose(pts, want[0], atol=1e-6), f"step {step}: points"
            assert np.array_equal(cols, want[1]), f"step {step}: colours"
        built.clear()
        b.location.x += 0.3                           # moved by the same update (a parented / constrained rig)
        pb.rotation_euler = (0.0, 0.2, 0.0)
        bpy.context.view_layer.update()
        mj._joined(view)
        assert sorted(built) == ["a", "b"], f"a skeleton the update moved is built too ({built})"
        built.clear()
        ctrl.data.vertices[0].co.x += 0.05            # a control shape's geometry
        ctrl.data.update()
        bpy.context.view_layer.update()
        mj._joined(view)
        assert sorted(built) == ["a", "b"], f"a changed control shape builds every skeleton ({built})"
        built.clear()
        bpy.context.scene.frame_set(bpy.context.scene.frame_current + 1)
        mj._joined(view)
        assert sorted(built) == ["a", "b"], f"a new frame builds every skeleton ({built})"
        built.clear()
        mj.transforming = lambda: False               # the drag has ended: an update is an edit
        pb.rotation_euler = (0.0, 0.0, 0.0)
        bpy.context.view_layer.update()
        got = mj._joined(view)
        assert built == ["a"], f"after the drag the skeleton the update touched is built ({built})"
        pts, cols = np.array(got[0]), np.array(got[1])
        want = fresh()
        assert pts.shape == want[0].shape and np.allclose(pts, want[0], atol=1e-6), "after the drag: points"
        assert np.array_equal(cols, want[1]), "after the drag: colours"
    finally:
        mj._parts, mj.transforming = real_parts, real_moving
        bpy.ops.object.mode_set(mode='OBJECT')
