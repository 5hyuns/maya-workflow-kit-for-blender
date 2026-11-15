"""The kit's depsgraph handlers share one pass over each update (``update_summary``) and still see what a pass of
their own would show: the shared walk on or off gives the same results step by step (mesh edit, move, pose, deformer,
material, keys, hide, file open), every reuse matches a new walk, and a handler that isn't the kit's, a kit handler
that writes during the round, or a nested evaluation makes the handlers after it walk the update again."""

import os
import re
from importlib import import_module

import bmesh
import bpy

import kit

M = kit.MODULE
OUT = os.path.join(kit.ROOT, "tmp", os.environ.get("ALLSET_SANDBOX", "test_env"), "update_summary")


def _m(name):
    return import_module(M + "." + name)


us = _m("update_summary")


def _update():
    bpy.context.view_layer.update()


def _object_mode():
    if bpy.context.object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')


def _clear():
    _object_mode()
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for coll in (bpy.data.meshes, bpy.data.armatures, bpy.data.curves, bpy.data.lattices, bpy.data.materials,
                 bpy.data.actions):
        for d in list(coll):
            coll.remove(d)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    _update()


def _link(ob):
    bpy.context.scene.collection.objects.link(ob)
    return ob


def _cube(name, size=1.0):
    me = bpy.data.meshes.new(name + "Shape")
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=size)
    bm.to_mesh(me)
    bm.free()
    return _link(bpy.data.objects.new(name, me))


def _select(ob):
    for o in bpy.context.scene.objects:
        o.select_set(False)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob


def _scene():
    """Meshes with a material, a parent and child, a skinned mesh on a three-joint skeleton, a curve, a lattice
    deformer and a keyed locator."""
    _clear()
    cube = _cube("pCube1")
    red = bpy.data.materials.new("red")
    cube.data.materials.append(red)
    parent = _link(bpy.data.objects.new("parent1", None))
    child = _cube("child1", 0.5)
    child.parent = parent
    arm = _link(bpy.data.objects.new("joint1", bpy.data.armatures.new("joint1")))
    _select(arm)
    bpy.ops.object.mode_set(mode='EDIT')
    prev = None
    for i in range(3):
        b = arm.data.edit_bones.new(f"joint{i + 1}")
        b.head, b.tail = (0, 0, i), (0, 0, i + 1)
        b.parent = prev
        prev = b
    bpy.ops.object.mode_set(mode='OBJECT')
    skin = _cube("skin1")
    skin.modifiers.new("skin", 'ARMATURE').object = arm
    for i in range(3):
        skin.vertex_groups.new(name=f"joint{i + 1}").add(list(range(8)), 1.0 / (i + 1), 'REPLACE')
    crv = bpy.data.curves.new("curve1", 'CURVE')
    spline = crv.splines.new('POLY')
    spline.points.add(2)
    for i, p in enumerate(spline.points):
        p.co = (i, 0, 0, 1)
    _link(bpy.data.objects.new("curve1", crv))
    lat = _link(bpy.data.objects.new("ffd1Lattice", bpy.data.lattices.new("ffd1Lattice")))
    target = _cube("latTarget")
    target.modifiers.new("ffd1", 'LATTICE').object = lat
    loc = _link(bpy.data.objects.new("locator1", None))
    loc.keyframe_insert("location", frame=1)
    bpy.context.scene.allset_auto_key = True
    _update()
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "scene.blend")
    bpy.ops.wm.save_as_mainfile(filepath=path, copy=True)
    return path


# --- what the handlers that share the walk keep, by name ----------------------------------------------------------

class _Seed:
    """A cache entry stand-in: kept or dropped by the handler that owns the cache."""
    _sel = True
    editing = False
    bm = None


def _uid_names():
    names = {}
    for coll in (bpy.data.objects, bpy.data.meshes, bpy.data.curves, bpy.data.armatures, bpy.data.actions):
        for d in coll:
            names[d.session_uid] = d.name
    return names


def _ptr_names():
    return {ob.as_pointer(): ob.name for ob in bpy.data.objects}


def _seed():
    """Give every walking handler something to keep or drop, and read the counters before an update."""
    uids = [ob.session_uid for ob in bpy.data.objects]
    sw, gh, live = _m("ui.selection_wire"), _m("ui.ghosting"), _m("operators.live")
    sw._batches.clear()
    sw._edges.clear()
    for uid in uids:
        sw._batches[uid] = None
        sw._edges[uid] = None
    gh._geom.clear()
    for uid in uids:
        gh._geom[(uid, 1)] = None
    live._trees.clear()
    for ob in bpy.data.objects:
        if ob.type == 'MESH':
            live._trees[ob.session_uid] = (None, ob.data.session_uid)
    _m("ui.soft_overlay")._dirty["any"].clear()
    _m("ui.soft_overlay")._dirty["geom"].clear()
    cc = _m("ui.component_colors")
    cc._cache.clear()
    cc._cache[(-1, -1)] = None
    cc._dirty.clear()
    cc._dirty_sel.clear()
    _m("ui.weight_numbers")._cache["dirty"] = False
    for name in ("ui.uv_display", "ui.uv_shell_preview", "operators.cut_sew"):
        mod = _m(name)
        cache = mod._border_cache if name == "operators.cut_sew" else mod._cache
        cache.clear()
        cache[-1] = None
    pre = _m("operators.preselect")
    pre._cache.clear()
    pre._cache[-1] = _Seed()
    _m("operators.bridge_curve")._dirty.clear()
    _m("operators.blend_shapes_227")._pending.clear()
    _m("operators.surfaces_maya")._pending.clear()
    _m("operators.graph_curves_203")._state["scheduled"] = False
    _m("operators.graph_key_menu")._frames.clear()
    pf = _m("operators.pivot_follow")
    pf._snap["points"] = []
    pf._geom[0] = 0
    _m("operators.auto_key")._pending.clear()
    mj = _m("ui.maya_joints_cache")
    return {"structure": _m("ui.outliner").structure_version(), "objects": _m("ui.outliner").objects_version(),
            "channels": _m("ui.channel_box")._generation[0], "layers": _m("ui.layer_joints")._REV[0],
            "joints": (mj._GEN[0], mj._EDITS[0], mj._LAYER_GEN[0])}


def _read(before):
    """What the handlers made of the update (names, not pointers: two passes over the same steps compare)."""
    names, ptrs = _uid_names(), _ptr_names()
    sw, gh, live = _m("ui.selection_wire"), _m("ui.ghosting"), _m("operators.live")
    mj = _m("ui.maya_joints_cache")
    touched = mj._TOUCHED.get(mj._GEN[0])
    if touched is not None:
        levels, every, scene = touched
        touched = (sorted((ptrs.get(p, "?"), lv) for p, lv in levels.items()), every, scene)
    cc = _m("ui.component_colors")
    pre = _m("operators.preselect")
    got = {
        "structure": _m("ui.outliner").structure_version() - before["structure"],
        "objects": _m("ui.outliner").objects_version() - before["objects"],
        "channels": _m("ui.channel_box")._generation[0] - before["channels"],
        "layers": _m("ui.layer_joints")._REV[0] - before["layers"],
        "joints": tuple(a - b for a, b in zip((mj._GEN[0], mj._EDITS[0], mj._LAYER_GEN[0]), before["joints"])),
        "joints_touched": touched,
        "wire_batches": sorted(names.get(u, "?") for u in sw._batches),
        "wire_edges": sorted(names.get(u, "?") for u in sw._edges),
        "ghosts": sorted(names.get(k[0], "?") for k in gh._geom),
        "live": sorted(names.get(u, "?") for u in live._trees),
        "soft": (sorted(_m("ui.soft_overlay")._dirty["any"]), sorted(_m("ui.soft_overlay")._dirty["geom"])),
        "colors": (sorted(cc._dirty), sorted(cc._dirty_sel)),
        "weights": _m("ui.weight_numbers")._cache["dirty"],
        "uv": (-1 in _m("ui.uv_display")._cache, -1 in _m("ui.uv_shell_preview")._cache),
        "borders": -1 in _m("operators.cut_sew")._border_cache,
        "preselect": (-1 in pre._cache, pre._cache[-1]._sel if -1 in pre._cache else None),
        "bridge": sorted(names.get(u, "?") for u in _m("operators.bridge_curve")._dirty),
        "blend": sorted(_m("operators.blend_shapes_227")._pending),
        "surfaces": sorted(_m("operators.surfaces_maya")._pending),
        "curves_sync": _m("operators.graph_curves_203")._state["scheduled"],
        "key_frames": sorted(_m("operators.graph_key_menu")._frames),
        "pivot_geom": _m("operators.pivot_follow")._geom[0],
        "auto_key": sorted(_m("operators.auto_key")._pending),
        "hidden": sorted(ob.name for ob in bpy.context.scene.objects if ob.hide_get()),
    }
    _m("operators.pivot_follow")._snap["points"] = None
    gc = _m("operators.graph_curves_203")
    if bpy.app.timers.is_registered(gc._sync_tick):
        bpy.app.timers.unregister(gc._sync_tick)
    gc._state["scheduled"] = False
    return got


def _ob(name):
    return bpy.data.objects[name]


def _edit_mesh():
    ob = _ob("pCube1")
    _select(ob)
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(ob.data)
    bm.verts.ensure_lookup_table()
    bm.verts[0].co.x += 0.25
    bmesh.update_edit_mesh(ob.data)


def _pose():
    arm = _ob("joint1")
    _select(arm)
    bpy.ops.object.mode_set(mode='POSE')
    arm.pose.bones["joint2"].rotation_quaternion = (0.9, 0.3, 0.0, 0.0)


def _pose_select():
    arm = _ob("joint1")
    for pb in arm.pose.bones:
        pb.select = pb.name == "joint3"


def _add():
    _link(bpy.data.objects.new("new1", None))


STEPS = (
    ("move", lambda: setattr(_ob("pCube1"), "location", (1.0, 0.0, 0.0))),
    ("select", lambda: _select(_ob("locator1"))),
    ("rename", lambda: setattr(_ob("child1"), "name", "child2")),
    ("parent", lambda: setattr(_ob("pCube1"), "parent", _ob("parent1"))),
    ("add", _add),
    ("delete", lambda: bpy.data.objects.remove(_ob("new1"))),
    ("mesh edit", _edit_mesh),
    ("object mode", _object_mode),
    ("pose", _pose),
    ("joint pick", _pose_select),
    ("object mode 2", _object_mode),
    ("key", lambda: _ob("locator1").keyframe_insert("location", frame=5)),
    ("material", lambda: setattr(bpy.data.materials["red"], "diffuse_color", (0.2, 0.3, 0.4, 1.0))),
    ("hide", lambda: setattr(_ob("parent1"), "hide_viewport", True)),
    ("show", lambda: setattr(_ob("parent1"), "hide_viewport", False)),
    ("curve", lambda: setattr(bpy.data.curves["curve1"].splines[0].points[1], "co", (1.0, 1.0, 0.0, 1.0))),
    ("lattice", lambda: setattr(bpy.data.lattices["ffd1Lattice"].points[0], "co_deform", (-0.8, -0.6, -0.5))),
    ("skeleton move", lambda: setattr(_ob("joint1"), "location", (0.0, 2.0, 0.0))),
)


def _run(path, enabled, check=False):
    """Open the scene, do every step and read what the handlers made of each update."""
    bpy.ops.wm.open_mainfile(filepath=path)
    us.ENABLED, us.CHECK = enabled, check
    us.MISMATCHES.clear()
    try:
        _m("ui.layer_joints").state(_ob("joint1"))
        rows = []
        for name, step in STEPS:
            before = _seed()
            step()
            _update()
            rows.append((name, _read(before)))
        # a file open in the middle of a session, then a move
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "steps.blend"), copy=True)
        bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT, "steps.blend"))
        before = _seed()
        _ob("pCube1").location.y += 1
        _update()
        rows.append(("open + move", _read(before)))
        return rows, list(us.MISMATCHES)
    finally:
        _object_mode()
        us.ENABLED, us.CHECK = True, False


def _diff(a, b):
    out = []
    for (name, ra), (_n, rb) in zip(a, b):
        for k in ra:
            if ra[k] != rb[k]:
                out.append(f"{name} / {k}: {ra[k]} != {rb[k]}")
    return out


# --- tests --------------------------------------------------------------------------------------------------------

def test_round_markers_go_first_and_last():
    lst = bpy.app.handlers.depsgraph_update_post
    assert lst[0] is us._round_start and lst[-1] is us._round_end, [us.key(h) for h in lst]
    assert hasattr(us._round_start, "_bpy_persistent") and hasattr(us._round_end, "_bpy_persistent")


_SETS = ("READERS", "REPORTERS", "WRITERS")


def _sets_of(k):
    return [n for n in _SETS if k in getattr(us, n)]


def test_every_kit_handler_is_declared():
    """Each kit depsgraph handler is listed once: writes nothing during a round, says when it writes, or may write
    (the handlers after it walk again). A handler not listed counts as one that may write."""
    kit_keys = [us.key(h) for h in bpy.app.handlers.depsgraph_update_post
                if us.key(h) is not None and h not in (us._round_start, us._round_end)]
    assert len(kit_keys) > 50, kit_keys
    wrong = {k: _sets_of(k) for k in kit_keys if len(_sets_of(k)) != 1}
    assert not wrong, wrong
    listed = set().union(*(getattr(us, n) for n in _SETS))
    assert listed - set(kit_keys) == {"operators.joint_marquee:_count"}, sorted(listed - set(kit_keys))


_ASK = re.compile(r"\b(?:update_summary\.updates|depsgraph_filter\.look|only_motion|_what_changed)\(([^()]*)\)")


def test_every_handler_that_shares_the_walk_is_declared():
    """A handler that asks for the shared entries is listed (``_SETS``): one that writes during the round and isn't a
    reader or a reporter keeps the handlers after it walking again."""
    root = os.path.dirname(us.__file__)
    asked = set()
    for folder, _dirs, files in os.walk(root):
        for f in files:
            if not f.endswith(".py") or f in ("update_summary.py", "depsgraph_filter.py"):
                continue
            path = os.path.join(folder, f)
            mod = os.path.relpath(path, root)[:-3].replace(os.sep, ".")
            with open(path, encoding="utf-8") as fh:
                for args in _ASK.findall(fh.read()):
                    last = args.split(",")[-1].strip()
                    if "," in args and last.isidentifier() and last != "me":
                        asked.add(f"{mod}:{last}")
    assert len(asked) >= 28, sorted(asked)
    missing = sorted(k for k in asked if len(_sets_of(k)) != 1)
    assert not missing, missing


def test_shared_walk_gives_the_same_results():
    """Every step, with the shared walk off, on, and on with each reuse compared with a new walk: the same."""
    path = _scene()
    off, _ = _run(path, enabled=False)
    on, _ = _run(path, enabled=True)
    checked, mismatches = _run(path, enabled=True, check=True)
    assert not mismatches, mismatches[:3]
    assert not _diff(off, on), _diff(off, on)
    assert not _diff(off, checked), _diff(off, checked)
    # the steps reach the handlers: the comparison isn't between empty readings
    by = dict(off)
    assert by["move"]["soft"][1] == ["pCube1"], by["move"]
    assert "pCube1" in by["move"]["wire_batches"] and "latTarget" not in by["lattice"]["wire_batches"], by["lattice"]
    assert len(by["key"]["key_frames"]) == 1 and by["key"]["curves_sync"] is True, by["key"]
    assert by["add"]["structure"] >= 1 and by["move"]["structure"] == 0, (by["add"], by["move"])
    assert "child2" in by["hide"]["hidden"] and "child2" not in by["show"]["hidden"], (by["hide"], by["show"])
    assert by["curve"]["bridge"] == ["curve1"] and by["mesh edit"]["pivot_geom"] >= 1, (by["curve"], by["mesh edit"])


def test_quiet_rounds_share_one_walk():
    """A move, a selection and a pose step each walk the update fewer times than handlers ask for it."""
    path = _scene()
    bpy.ops.wm.open_mainfile(filepath=path)
    _m("ui.layer_joints").state(_ob("joint1"))
    for step in (lambda: setattr(_ob("pCube1"), "location", (2.0, 0.0, 0.0)), lambda: _select(_ob("pCube1"))):
        walks, reuses = us.STATS["walks"], us.STATS["reuses"]
        step()
        _update()
        walks, reuses = us.STATS["walks"] - walks, us.STATS["reuses"] - reuses
        assert walks >= 1 and reuses >= 1, (walks, reuses)


def _seen_by_the_last(lst_pos, act, recompute=True, enabled=True):
    """Move pCube1 with ``act`` run by a handler that isn't the kit's at ``lst_pos`` of the list; the names the
    kit's last walking handler (soft_overlay) and a probe just before the round's end saw."""
    so = _m("ui.soft_overlay")
    seen = []

    def foreign(scene, depsgraph):
        act(scene, depsgraph)

    def probe(scene, depsgraph):
        seen.append(sorted(u.id.name for u in us.updates(depsgraph, probe)
                           if isinstance(u.id, bpy.types.Object)))
    lst = bpy.app.handlers.depsgraph_update_post
    lst.insert(lst_pos if lst_pos >= 0 else len(lst) + lst_pos, foreign)
    lst.insert(len(lst) - 1, probe)
    us.ENABLED, us.RECOMPUTE = enabled, recompute
    try:
        so._dirty["any"].clear()
        so._dirty["geom"].clear()
        _ob("pCube1").location.x += 1
        _update()
        return sorted(so._dirty["geom"]), seen
    finally:
        us.ENABLED, us.RECOMPUTE = True, True
        lst.remove(foreign)
        lst.remove(probe)


def _position(k):
    return next(i for i, h in enumerate(bpy.app.handlers.depsgraph_update_post) if us.key(h) == k)


def test_a_handler_not_the_kits_in_the_middle():
    """Another add-on's handler before, between or after the kit's: the kit handlers after it see every update it
    makes, as when each walks the update itself; one that writes nothing still costs only a new walk. With the walk
    again rule off the later handlers miss its update (the risk the rule prevents)."""
    _clear()
    _cube("pCube1")
    other = _cube("pOther")
    _update()

    def move_other(_scene, _dg):
        other.location.z += 1

    def read_only(_scene, dg):
        sum(1 for _u in dg.updates)
    middle = _position("ui.outliner:_on_depsgraph")
    for pos in (1, middle, -1):
        off = _seen_by_the_last(pos, move_other, enabled=False)
        on = _seen_by_the_last(pos, move_other)
        assert on == off, (pos, on, off)
        if pos != -1:
            assert on[0] == ["pCube1", "pOther"] and on[1] == [["pCube1", "pOther"]], (pos, on)
    # the last kit handler runs before the one at the end: it sees only the kit's move, both ways
    assert _seen_by_the_last(-1, move_other)[0] == ["pCube1"]
    walks = us.STATS["walks"]
    plain = _seen_by_the_last(middle, read_only)
    assert plain == (["pCube1"], [["pCube1"]]), plain
    assert us.STATS["walks"] - walks >= 2, "a handler that isn't the kit's makes the next asker walk again"
    risky = _seen_by_the_last(middle, move_other, recompute=False)
    assert risky[0] == ["pCube1"] and risky[1] == [["pCube1"]], f"without the rule the move is missed: {risky}"


def test_a_nested_evaluation_empties_the_rest_of_the_round_as_before():
    """A handler that evaluates the depsgraph again (a nested round) leaves the rest of the outer round an empty
    update: the kit handlers after it see that, shared walk on or off."""
    _clear()
    _cube("pCube1")
    other = _cube("pOther")
    _update()

    def nested(_scene, _dg):
        if other.location.z < 50:
            other.location.z += 100
            bpy.context.view_layer.update()
    middle = _position("ui.outliner:_on_depsgraph")
    got = []
    for enabled in (False, True):
        other.location.z = 0
        _update()
        got.append(_seen_by_the_last(middle, nested, enabled=enabled))
    assert got[0] == got[1], got
    soft, probe = got[1]
    assert soft == ["pCube1", "pOther"], soft          # the nested round's own pass saw both
    assert probe == [["pCube1", "pOther"], []], probe   # nested round, then the rest of the outer one: nothing


def test_outside_a_round_the_update_itself():
    """A handler called directly (a stand-in depsgraph, another depsgraph) reads the update as before."""
    class _Dg:
        updates = ()
    fake = _Dg()
    so = _m("ui.soft_overlay")
    assert us.updates(fake, so._on_depsgraph) is fake.updates
    dg = bpy.context.evaluated_depsgraph_get()
    assert us.shared(dg, so._on_depsgraph) is None
    assert not us._rounds, "no round left running"


def test_switching_maya_mode_off_takes_the_markers():
    sw = _m("switch")
    assert sw.set_mode(False, layout=False) is True
    try:
        lst = bpy.app.handlers.depsgraph_update_post
        assert us._round_start not in lst and us._round_end not in lst
        assert not [us.key(h) for h in lst if us.key(h) is not None]
    finally:
        assert sw.set_mode(True, layout=False) is True
    lst = bpy.app.handlers.depsgraph_update_post
    assert lst[0] is us._round_start and lst[-1] is us._round_end
