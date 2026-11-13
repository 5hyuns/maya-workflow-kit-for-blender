"""Depsgraph and draw hooks in a big scene: a joint click, a selection and a move read only what the update touched
(one pass over the update, no list of every object), and they keep their results: skeleton layer states, the
Outliner's structure version, RP IK handles, Morph rest helpers, type handles and camera aim lines."""

import time
from importlib import import_module

import bpy

import kit
import test_step223_ik_fk as IK


def _m(name):
    return import_module(kit.MODULE + "." + name)


def _update():
    bpy.context.view_layer.update()


def _clear():
    if bpy.context.object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    _update()


def _skeleton(name, x=0.0, n=3):
    """A skeleton object with a chain of ``n`` joints <name>0 > <name>1 > ..."""
    ob = bpy.data.objects.new(name, bpy.data.armatures.new(name))
    bpy.context.scene.collection.objects.link(ob)
    ob.location.x = x
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    prev = None
    for i in range(n):
        eb = ob.data.edit_bones.new(f"{name}{i}")
        eb.head, eb.tail = (0, 0, i), (0, 0, i + 1)
        if prev is not None:
            eb.parent = prev
        prev = eb
    bpy.ops.object.mode_set(mode='OBJECT')
    return ob


def _props(n):
    coll = bpy.data.collections.new("props")
    bpy.context.scene.collection.children.link(coll)
    for i in range(n):
        coll.objects.link(bpy.data.objects.new(f"prop{i}", None))
    return coll


class _Counting:
    """A scene / view layer / depsgraph stand-in that counts reads of one collection (``objects`` or ``updates``)."""

    def __init__(self, real, attr):
        object.__setattr__(self, "_real", real)
        object.__setattr__(self, "_attr", attr)
        object.__setattr__(self, "reads", 0)

    def __getattr__(self, name):
        if name == self._attr:
            object.__setattr__(self, "reads", self.reads + 1)
        return getattr(self._real, name)


class _Spy:
    """While active, the named kit depsgraph handlers get counting stand-ins: how often each read the scene's objects
    and passed over the update, per call."""

    def __init__(self, *names):
        self.names = set(names)
        self.scene_reads = {n: 0 for n in names}
        self.passes = {n: [] for n in names}

    def __enter__(self):
        lst = bpy.app.handlers.depsgraph_update_post
        self.saved = list(lst)
        new = []
        for h in self.saved:
            key = f"{getattr(h, '__module__', '?').split('.')[-1]}.{getattr(h, '__name__', '?')}"
            if key not in self.names:
                new.append(h)
                continue

            def w(scene, depsgraph=None, _h=h, _k=key):
                sc = _Counting(scene, "objects")
                dg = _Counting(depsgraph, "updates") if depsgraph is not None else None
                try:
                    return _h(sc, dg)
                finally:
                    self.scene_reads[_k] += sc.reads
                    self.passes[_k].append(dg.reads if dg is not None else 0)
            new.append(w)
        lst.clear()
        lst.extend(new)
        return self

    def __exit__(self, *_exc):
        lst = bpy.app.handlers.depsgraph_update_post
        lst.clear()
        lst.extend(self.saved)
        return False


HOOKS = ("layer_joints._on_depsgraph", "outliner._on_depsgraph", "type_manip._on_depsgraph")


def _pick(ob, name):
    """A joint pick: the bone's selection (an update of the skeleton and its data)."""
    for pb in ob.pose.bones:
        pb.select = pb.name == name
    _update()


def _rig_scene(props=400):
    _clear()
    a, b = _skeleton("ska"), _skeleton("skb", 3.0)
    _props(props)
    _update()
    lj = _m("ui.layer_joints")
    lj.state(a)
    lj.state(b)
    for _ in range(2):              # every skeleton seen once by the Outliner check
        _pick(a, "ska1")
        _pick(b, "skb1")
    return a, b


def test_joint_picks_and_moves_read_no_object_list():
    """A joint pick, an object selection and a move: the skeleton-state, Outliner and type handle hooks read the
    update once and no list of the scene's objects; the RP handles and Morph rest helpers aren't looked up again."""
    a, b = _rig_scene()
    tm, ik = _m("operators.type_manip"), _m("operators.ik_rp")
    armed = tm._armed[0]
    tm._armed[0] = True                 # a type with the manipulator in the file
    looks = []
    real = ik.rp_handles
    try:
        _pick(a, "ska2")                # (the type handle list is read once here)
        ik.rp_handles = lambda: looks.append(1) or real()
        with _Spy(*HOOKS) as spy:
            for i in range(4):
                _pick(a, f"ska{i % 3}")
                _pick(b, f"skb{i % 3}")
                prop = bpy.data.objects[f"prop{i}"]
                prop.select_set(True)
                _update()
                prop.location.x += 0.5
                _update()
                a.location.y += 0.1
                _update()
        assert all(n == 0 for n in spy.scene_reads.values()), f"no object list read: {spy.scene_reads}"
        worst = {k: max(v) for k, v in spy.passes.items()}
        assert all(n <= 1 for n in worst.values()), f"one pass over each update at most: {worst}"
        assert not looks, f"no object came or went: the RP handles aren't looked up ({len(looks)} looks)"
    finally:
        ik.rp_handles = real
        tm._armed[0] = armed


def test_skeleton_states_follow_joint_visibility_renames_and_picks():
    """A joint's Visibility set from Python (an update that only moves) reaches the skeleton's state at the next
    update that isn't a move, wherever it is; a joint pick keeps the states."""
    a, b = _rig_scene(props=20)
    lj = _m("ui.layer_joints")
    assert dict(lj.state(a)) == {}
    a.pose.bones["ska1"].hide = True
    _update()
    bpy.data.objects["prop0"].name = "prop0_renamed"     # an update of another object only
    _update()
    assert dict(lj.state(a)) == {"ska1": lj.HIDDEN, "ska2": lj.HIDDEN}, dict(lj.state(a))
    a.pose.bones["ska1"].hide = False
    _update()
    _pick(b, "skb2")                    # the other skeleton's pick
    assert dict(lj.state(a)) == {}, dict(lj.state(a))
    lj.state(a)
    lj.state(b)
    rev = lj._REV[0]
    _pick(b, "skb1")
    _pick(a, "ska2")
    assert lj._REV[0] == rev, "joint picks keep the states"
    a.pose.bones["ska2"].name = "ska2x"
    _update()
    assert lj._REV[0] != rev, "a renamed joint reads the states again"


def test_outliner_structure_follows_skeleton_edits_and_shared_skeleton_data():
    """The structure version: a joint pick keeps it, a renamed joint or skeleton moves it; a second skeleton object
    on the same data is compared too (it is first seen at a pick of the other one)."""
    a, _b = _rig_scene(props=20)
    ol = _m("ui.outliner")
    v = ol.structure_version()
    _pick(a, "ska0")
    assert ol.structure_version() == v, "a joint pick keeps the structure"
    a.pose.bones["ska0"].name = "ska0x"
    _update()
    assert ol.structure_version() > v, "a renamed joint moves it"
    twin = a.copy()                     # the same skeleton data
    bpy.context.scene.collection.objects.link(twin)
    _update()
    _pick(a, "ska1")
    v = ol.structure_version()
    _pick(a, "ska2")
    assert ol.structure_version() == v, "picks on a skeleton that shares its data keep it once both were seen"
    twin.name = "twin2"
    _update()
    assert ol.structure_version() > v, "a renamed skeleton moves it"


def test_lists_are_found_again_when_objects_come_and_go():
    """RP handles: found again once when an object is added, removed or the collection is excluded — not on picks or
    moves; a new RP handle is found and its pole helper follows the twist. Morph rest helpers: a new one is found
    before any update and follows its owner's new mesh."""
    ik, d205 = _m("operators.ik_rp"), _m("operators.deformers_205b")
    arm, handle, _con = IK._arm()
    _update()
    assert handle in ik._found[1], "a new RP handle is found"
    helper = handle[ik.HELPER]
    before = helper.matrix_world.translation.copy()
    handle["twist"] = 40.0
    handle.update_tag()                 # (a custom property alone sends no update)
    _update()
    assert (helper.matrix_world.translation - before).length > 1e-4, "the pole helper follows the twist"
    looks = []
    real = ik.rp_handles
    ik.rp_handles = lambda: looks.append(1) or real()
    try:
        for _ in range(3):
            handle.location.x += 0.1
            _update()
            arm.select_set(not arm.select_get())
            _update()
        assert not looks, f"moves and selections: no look ({len(looks)})"
        coll = bpy.data.collections.new("more")
        bpy.context.scene.collection.children.link(coll)
        extra = bpy.data.objects.new("extra", None)
        coll.objects.link(extra)
        _update()
        assert len(looks) == 1, f"an added object: found again once ({len(looks)})"
        bpy.context.view_layer.layer_collection.children["more"].exclude = True
        _update()
        bpy.data.objects.remove(extra)
        _update()
        assert len(looks) == 3, f"an excluded collection, a removed object: found again each time ({len(looks)})"
        assert ik._found[1] == real(), "the same handles as a full look"
    finally:
        ik.rp_handles = real
    me = bpy.data.meshes.new("owner")
    me.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [], [(0, 1, 2)])
    owner = bpy.data.objects.new("owner", me)
    bpy.context.scene.collection.objects.link(owner)
    _update()
    d205.sync_rest()
    rest = d205._rest("ownerOrig", owner)          # in no collection
    assert rest in d205._rest_helpers(), "a new rest helper is found before any update"
    me2 = me.copy()
    owner.data = me2
    _update()
    assert rest.data == me2, "the rest helper follows its owner's new mesh"


def test_type_handles_are_found_when_objects_come_and_go():
    """The Type Manipulator's handle list: a new handle is found, a removed one is dropped even before the next
    depsgraph update (a click right after a Delete)."""
    tm = _m("operators.type_manip")
    _clear()
    _props(20)
    _update()
    scene = bpy.context.scene
    assert tm._handles_of(scene) == tm.handles(scene) == []
    h = bpy.data.objects.new("typeManipulator", None)
    h[tm.HANDLE] = "type1"
    scene.collection.objects.link(h)
    _update()
    assert tm._handles_of(scene) == tm.handles(scene) == [h]
    bpy.data.objects.remove(h)
    assert tm._handles_of(scene) == tm.handles(scene) == []


def test_rest_helpers_are_not_looked_up_on_every_update():
    """Morph rest helpers with thousands of objects: keeping them on their owners' meshes costs little per update."""
    _clear()
    _props(3000)
    _update()
    d205 = _m("operators.deformers_205b")
    d205.sync_rest()
    t = time.perf_counter()
    for _ in range(200):
        d205.sync_rest()
    ms = 1000 * (time.perf_counter() - t)
    assert ms < 25, f"200 updates with 3,000 objects: {ms:.1f} ms"


def test_camera_list_follows_objects_coming_and_going():
    """The camera aim lines' camera list: read once while objects stay, read again when a camera is added, its
    collection excluded or included, or it is removed; the lines are the same as from every object."""
    cal = _m("ui.camera_aim_lines")
    _clear()
    _props(50)
    coll = bpy.data.collections.new("rig")
    bpy.context.scene.collection.children.link(coll)
    group = bpy.data.objects.new("cameraGroup", None)
    cam = bpy.data.objects.new("camera1", bpy.data.cameras.new("camera1"))
    aim = bpy.data.objects.new("camera1_aim", None)
    for ob in (group, cam, aim):
        coll.objects.link(ob)
    cam.parent = aim.parent = group
    aim.location = (0, 5, 0)
    con = cam.constraints.new('TRACK_TO')
    con.target = aim
    _update()
    vl = bpy.context.view_layer
    counting = _Counting(vl, "objects")
    for _ in range(20):
        assert cal.cameras(counting) == [cam]
    assert counting.reads <= 1, f"read once while objects stay ({counting.reads})"
    assert cal.segments(vl, None, cal.cameras(vl)) == cal.segments(vl) and cal.segments(vl)
    lc = vl.layer_collection.children["rig"]
    lc.exclude = True
    _update()
    assert cal.cameras(vl) == [] and cal.segments(vl, None, cal.cameras(vl)) == cal.segments(vl) == []
    lc.exclude = False
    _update()
    cam = bpy.data.objects["camera1"]
    assert cal.cameras(vl) == [cam]
    cam2 = bpy.data.objects.new("camera2", bpy.data.cameras.new("camera2"))
    bpy.context.scene.collection.objects.link(cam2)
    _update()
    assert set(cal.cameras(vl)) == {cam, cam2}
    bpy.data.objects.remove(cam2)
    _update()
    assert cal.cameras(vl) == [cam]
    assert cal.segments(vl, None, cal.cameras(vl)) == cal.segments(vl)


def test_one_pass_answers_like_the_single_tests():
    """``depsgraph_filter.Look`` (one pass) answers only_scene / only_motion / outliner_skip like the tests that each
    pass over the update."""
    df = _m("depsgraph_filter")
    seen = []

    def check(_scene, dg):
        look = df.Look(dg)
        ups = list(dg.updates)
        scene_only = bool(ups) and all(isinstance(u.id, bpy.types.Scene) for u in ups)
        motion = bool(ups) and all(not isinstance(u.id, (bpy.types.Scene, bpy.types.Collection))
                                   and (u.is_updated_transform or u.is_updated_geometry) for u in ups)
        skip = not any(isinstance(u.id, bpy.types.Armature) for u in ups) and (scene_only or motion)
        seen.append((look.scene_only, look.motion, look.outliner_skip(), df.only_scene(dg), df.only_motion(dg),
                     scene_only, motion, skip))
    a, _b = _rig_scene(props=10)
    bpy.app.handlers.depsgraph_update_post.append(check)
    try:
        _pick(a, "ska0")
        a.select_set(True)
        _update()
        a.location.x += 1
        _update()
        bpy.data.objects["prop2"].location.x += 1
        _update()
        bpy.data.objects["prop1"].name = "prop1x"
        _update()
        bpy.context.scene.collection.objects.link(bpy.data.objects.new("new", None))
        _update()
        a.pose.bones["ska1"].hide = True
        _update()
    finally:
        bpy.app.handlers.depsgraph_update_post.remove(check)
    assert len(seen) >= 6, seen
    for row in seen:
        assert row[0] == row[3] == row[5] and row[1] == row[4] == row[6] and row[2] == row[7], row
    assert {r[5] for r in seen} == {True, False} and {r[6] for r in seen} == {True, False}, seen
