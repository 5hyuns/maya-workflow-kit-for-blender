"""Graph Editor list and Stats fields with a keyed rig: the channel list and the Maya list sync give the same nodes
and drivers as looking at every driver once per node, but read each driver path a fixed number of times (not joints
x drivers); the Stats fields show the same text as reading every selected key, and stop at the second value."""

import contextlib
import math
import re
import time
from importlib import import_module
from types import SimpleNamespace

import bpy
import numpy as np

import kit

chrome = import_module(kit.MODULE + ".ui.editor_chrome")
cb = import_module(kit.MODULE + ".ui.channel_box")


def _clear():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for coll in (bpy.data.meshes, bpy.data.armatures, bpy.data.actions):
        for d in list(coll):
            coll.remove(d)
    chrome._expanded.clear()
    chrome._picked["ids"], chrome._picked["sig"] = set(), None
    chrome._pinned.clear()
    chrome._kit_hidden.clear()


def _space(only_selected=True):
    return SimpleNamespace(type='GRAPH_EDITOR', mode='FCURVES',
                           dopesheet=SimpleNamespace(show_only_selected=only_selected, show_hidden=True,
                                                     filter_text="", filter_collection=None))


def _driver(owner, path, index=-1, expr="var"):
    fc = owner.driver_add(path, index) if index >= 0 else owner.driver_add(path)
    fc.driver.type = 'SCRIPTED'
    fc.driver.expression = expr
    return fc


def _rig(bones=24, quote_name=True):
    """An armature whose joints are all keyed and driven, plus a driver of the armature itself; every joint
    selected."""
    _clear()
    arm = bpy.data.objects.new("skeleton1", bpy.data.armatures.new("skeleton1"))
    bpy.context.scene.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    names = [f"joint{i}" for i in range(bones)] + (['arm"L'] if quote_name else [])
    bpy.ops.object.mode_set(mode='EDIT')
    for i, name in enumerate(names):
        eb = arm.data.edit_bones.new(name)
        eb.head, eb.tail = (0, 0, i), (0, 0, i + 1)
    bpy.ops.object.mode_set(mode='POSE')
    for pb in arm.pose.bones:
        pb.keyframe_insert("location", index=0, frame=1)
        pb.keyframe_insert("location", index=0, frame=10)
        _driver(pb, "rotation_euler", 1)
        cb.set_bone_selected(pb, True)
    _driver(arm, "location", 2)                          # the armature's own driver
    for ob in bpy.context.scene.objects:
        ob.select_set(ob == arm)
    return arm


_JOINT = re.compile(r'^pose\.bones\["((?:[^"\\]|\\.)*)"\]')


def _joint(path):
    m = _JOINT.match(path)
    return m.group(1).replace('\\"', '"') if m else None


def _pass():
    """The list's pass (a no-op where the list has none)."""
    return getattr(chrome, "one_pass", contextlib.nullcontext)()


def _old_node_drivers(node):
    """Reference: every driver curve of the owner looked at once per node."""
    if isinstance(node, bpy.types.KeyingSet):
        return []
    owner = node.id_data if isinstance(node, bpy.types.PoseBone) else node
    ad = getattr(owner, "animation_data", None)
    if ad is None:
        return []
    out = []
    for fc in ad.drivers:
        name = _joint(fc.data_path) if isinstance(owner, bpy.types.Object) else None
        if isinstance(node, bpy.types.PoseBone):
            if name == node.name:
                out.append(fc)
        elif name is None or owner.type != 'ARMATURE':
            out.append(fc)
    return out


# --- channel list ------------------------------------------------------------------------------------------------

def test_node_drivers_by_joint():
    arm = _rig(bones=6)
    cube = bpy.data.objects.new("pCube1", bpy.data.meshes.new("pCubeShape1"))
    bpy.context.scene.collection.objects.link(cube)
    _driver(cube, "location", 0)
    _driver(cube, "scale", 1)
    for node in [arm, cube, *arm.pose.bones]:
        got = chrome.node_drivers(node)
        assert got == _old_node_drivers(node), (node.name, [f.data_path for f in got])
    quoted = arm.pose.bones['arm"L']
    assert [f.data_path for f in chrome.node_drivers(quoted)] == ['pose.bones["arm\\"L"].rotation_euler']
    assert [f.data_path for f in chrome.node_drivers(arm)] == ["location"]
    assert len(chrome.node_drivers(cube)) == 2
    with _pass():                                        # the same inside a pass
        for node in [arm, cube, *arm.pose.bones]:
            assert chrome.node_drivers(node) == _old_node_drivers(node), node.name


def test_list_reads_each_driver_once():
    """The list (and what the editors' sync asks of it) reads every curve / driver path a fixed number of times, not
    once per joint: joints x drivers grows with the square of the rig."""
    arm = _rig(bones=40)
    sp = _space()
    paths = len(kit.fcurves(arm)) + len(arm.animation_data.drivers)
    real, calls = chrome._bone_name, [0]

    def counted(path):
        calls[0] += 1
        return real(path)
    chrome._bone_name = counted
    try:
        nodes = chrome.listed_nodes(bpy.context, sp)
        one = calls[0]
        calls[0] = 0
        chrome.needs_kit_list(bpy.context, sp)
        chrome.drawn_objects(bpy.context, sp)
    finally:
        chrome._bone_name = real
    assert len([n for k, n, _c in nodes if k == "JOINT"]) == 41
    # 41 joints x 42 drivers would be ~1,700 reads
    assert one <= 2 * paths, (one, paths)
    assert calls[0] <= 4 * paths, (calls[0], paths)


def test_one_sync_builds_each_list_once():
    """Inside one sync of the editors (a pass) an editor's list is built once, however many helpers ask for it."""
    _rig(bones=6)
    sp = _space()
    real, calls = chrome._listed_nodes, [0]

    def counted(*a):
        calls[0] += 1
        return real(*a)
    chrome._listed_nodes = counted
    try:
        with chrome.one_pass():
            first = chrome.listed_nodes(bpy.context, sp)
            chrome.listed_curves(bpy.context, sp)
            chrome.rows(bpy.context, sp)
            again = chrome.listed_nodes(bpy.context, sp)
        assert calls[0] == 1, calls[0]
        chrome.listed_nodes(bpy.context, sp)              # outside a pass: built anew
        assert calls[0] == 2, calls[0]
    finally:
        chrome._listed_nodes = real
    assert [(k, n.name, c) for k, n, c in first] == [(k, n.name, c) for k, n, c in again]


def test_list_follows_the_selection_between_passes():
    arm = _rig(bones=4, quote_name=False)
    sp = _space()

    def joints():
        return [n.name for k, n, _c in chrome.listed_nodes(bpy.context, sp) if k == "JOINT"]
    assert joints() == ["joint0", "joint1", "joint2", "joint3"]
    for pb in arm.pose.bones:
        cb.set_bone_selected(pb, pb.name == "joint2")
    assert joints() == ["joint2"]
    with _pass():
        assert joints() == ["joint2"]
        assert joints() == ["joint2"]
    cb.set_bone_selected(arm.pose.bones["joint0"], True)
    assert joints() == ["joint0", "joint2"]
    rows = chrome.rows(bpy.context, sp)
    assert [(k, n.name) for k, n, _f in rows if k == "JOINT"] == [("JOINT", "joint0"), ("JOINT", "joint2")]
    # a joint's rows: its keyed channel, then its driven one
    attrs = [chrome.attr_label(f) for k, n, f in rows if k == "ATTR" and n.name == "joint0"]
    assert attrs == ["Translate X", "Rotate Y"], attrs


# --- Stats fields ---------------------------------------------------------------------------------------------------

def _keyed(keys=7):
    """A cube's nine curves with keys every 4 frames, some selected."""
    _clear()
    ob = bpy.data.objects.new("pCube1", bpy.data.meshes.new("pCubeShape1"))
    bpy.context.scene.collection.objects.link(ob)
    for f in range(keys):
        ob.location = (math.sin(f), math.cos(f) * 3, f * 0.5)
        ob.rotation_euler = (0.1 * f, 0.2 * f, -0.3 * f)
        ob.scale = (1.0, 1.0 + 0.1 * f, 1.0)
        for path in ("location", "rotation_euler", "scale"):
            ob.keyframe_insert(path, frame=1 + 4 * f)
    fcs = list(kit.fcurves(ob))
    rng = np.random.default_rng(7)
    for fc in fcs:
        for kp in fc.keyframe_points:
            kp.select_control_point = bool(rng.integers(0, 3) == 0)
    return fcs


def _old_stats(field, fcurves):
    pts = [(fc, kp) for fc in fcurves for kp in fc.keyframe_points if kp.select_control_point]
    if not pts:
        return ""
    values = {round(kp.co.x if field == "time" else kp.co.y, 6) for _fc, kp in pts}
    if len(values) > 1:
        return "-"
    cbe = import_module(kit.MODULE + ".ui.cb_entry")
    fc, kp = pts[0]
    if field == "time":
        return cbe.fmt_number(kp.co.x)
    return cbe.format_value(kp.co.y, chrome._kind(fc), bpy.context.scene)


def test_stats_fields_match_every_selected_key():
    fcs = _keyed()
    sc = bpy.context.scene

    def check():
        with bpy.context.temp_override(editable_fcurves=fcs):
            got = (sc.allset_key_time, sc.allset_key_value)
        assert got == (_old_stats("time", fcs), _old_stats("value", fcs)), got
        return got
    assert check() == ("-", "-")
    for fc in fcs:
        for kp in fc.keyframe_points:
            kp.select_control_point = False
    assert check() == ("", "")
    fcs[3].keyframe_points[2].select_control_point = True                  # one key: rotation in degrees
    t, v = check()
    assert t == "9" and v not in ("", "-"), (t, v)
    fcs[4].keyframe_points[2].select_control_point = True                  # same frame, another value
    assert check() == ("9", "-")
    fcs[4].keyframe_points[2].co.y = fcs[3].keyframe_points[2].co.y        # same frame, same value
    assert check() == ("9", v)


def test_stats_fields_stop_at_the_second_value():
    """Mixed values show "-" as soon as two differ: a big selection isn't read key by key."""
    _clear()
    ob = bpy.data.objects.new("pCube1", bpy.data.meshes.new("pCubeShape1"))
    bpy.context.scene.collection.objects.link(ob)
    fcs = []
    for i in range(60):
        name = f'["c{i}"]'
        ob[f"c{i}"] = 0.0
        fc = kit.fcurves(ob).new(name) if hasattr(kit.fcurves(ob), "new") else None
        if fc is None:
            ob.keyframe_insert(name, frame=1)
            fc = kit.fcurves(ob).find(name)
        fc.keyframe_points.add(1500 - len(fc.keyframe_points))
        co = np.zeros(1500 * 2, dtype=np.float32)
        co[0::2] = np.arange(1500)
        co[1::2] = i
        fc.keyframe_points.foreach_set("co", co)
        fc.keyframe_points.foreach_set("select_control_point", np.ones(1500, dtype=bool))
        fcs.append(fc)
    sc = bpy.context.scene
    with bpy.context.temp_override(editable_fcurves=fcs):
        t0 = time.perf_counter()
        got = (sc.allset_key_time, sc.allset_key_value)
        ms = (time.perf_counter() - t0) * 1000
    assert got == ("-", "-"), got
    # every key in Python: 90,000 keys, hundreds of ms; a few curves read: a few ms at most
    assert ms < 10.0, ms
