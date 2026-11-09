"""Issue #329 (Auto Key): with Auto Key on, a constraint target weight that already has keys is keyed at the current
frame when its value changes, like Maya — typed in the Channel Box (the weight row of a one-target constraint, a
node's W0 / W1 rows) or written anywhere else (the Attribute Editor). It is keyed at every frame the value changes,
also when the new value is one the weight showed at another frame (0 / 1 switches go back and forth). A weight
without keys is not keyed (Maya's Auto Key keys only attributes that already have keys), like the other channels.
One Undo takes back the typed weight and its key together. Scrubbing then follows the new keys: the weight follows
its curve and the constrained object or joint follows Maya's rule (one target: on the target for any weight above
0; several: the weighted average). Covers objects and joints, one and two targets, and an ordinary keyed channel."""

from importlib import import_module

import bpy

import kit
import test_issue329_weight_scrub as scenes

cb = import_module(kit.MODULE + ".ui.channel_box")
compat = import_module(kit.MODULE + ".compat")
multi = import_module(kit.MODULE + ".operators.constrain_multi")
auto_key = import_module(kit.MODULE + ".operators.auto_key")
undo_pairs = import_module(kit.MODULE + ".operators.undo_pairs")

CASES = (("object, 1 target", scenes._object_scene, 1), ("object, 2 targets", scenes._object_scene, 2),
         ("joint, 1 target", scenes._joint_scene, 1), ("joint, 2 targets", scenes._joint_scene, 2),
         ("joint, plain constraint", scenes._bone_scene, 1))


class _AutoKey:
    """Auto Key on (the Time Slider's key button) for the block; its timer is run by hand (none in background)."""

    def __enter__(self):
        auto_key._pending.clear()
        undo_pairs.reset()
        auto_key._reloaded[0] = False
        bpy.context.scene.allset_auto_key = True

    def __exit__(self, *_exc):
        bpy.context.scene.allset_auto_key = False
        auto_key._pending.clear()
        for fn in (auto_key._flush, undo_pairs.run_extra, auto_key._reload_seen):
            if bpy.app.timers.is_registered(fn):
                bpy.app.timers.unregister(fn)


def _settle():
    """The update after a change, then the Auto Key timer."""
    bpy.context.view_layer.update()
    if bpy.app.timers.is_registered(auto_key._flush):
        bpy.app.timers.unregister(auto_key._flush)
    auto_key._flush()


def _keys(fc):
    return [(round(k.co.x), round(k.co.y, 6)) for k in fc.keyframe_points] if fc is not None else None


def _row():
    return scenes._rows()[0]


def _type(frame, text):
    """Go to ``frame`` and type ``text`` in the first weight row (the kit's Channel Box entry)."""
    bpy.context.scene.frame_set(frame)
    _row().text = text
    _settle()


def _keyed_weight(make, n):
    """A scene whose first weight is keyed 1 at frame 1 and 0 at frame 10 with S; the time back at frame 1."""
    node, _targets, pos = make(n)
    key = cb.row_key(_row())
    scenes._key_weight("S", 1, "1")
    scenes._key_weight("S", 10, "0")
    bpy.context.scene.frame_set(1)
    fc = cb.fcurve(node, key)
    assert _keys(fc) == [(1, 1.0), (10, 0.0)], _keys(fc)
    return node, key, pos


def _check_scrub(tag, node, key, pos, n, want_keys):
    fc = cb.fcurve(node, key)
    assert _keys(fc) == want_keys, (tag, "keys", _keys(fc), want_keys)
    for frame in (1, 5, 10, 15, 20, 25, 30, 12, 1, 22):
        bpy.context.scene.frame_set(frame)
        want = fc.evaluate(frame)
        got = cb.get_value(node, key)
        assert abs(got - want) < 1e-5, (tag, frame, "weight", got, want)
        assert abs(float(_row().text) - want) < 1e-3, (tag, frame, "row text", _row().text, want)
        y = pos().y
        assert abs(y - scenes._expected_y(want, n)) < 1e-4, (tag, frame, "position", y, scenes._expected_y(want, n))


def test_typed_weight_is_keyed_at_each_frame_it_changes():
    """Auto Key on at frame 1 (weight 1). Frame 20 (the curve holds 0): type 1 -> key 1 at 20, though 1 is what the
    weight showed when Auto Key was turned on. Frame 30: type 0 -> key 0 at 30. Then scrub."""
    for tag, make, n in CASES:
        node, key, pos = _keyed_weight(make, n)
        with _AutoKey():
            _type(20, "1")
            fc = cb.fcurve(node, key)
            assert _keys(fc) == [(1, 1.0), (10, 0.0), (20, 1.0)], (tag, "frame 20", _keys(fc))
            _type(30, "0")
            assert _keys(fc) == [(1, 1.0), (10, 0.0), (20, 1.0), (30, 0.0)], (tag, "frame 30", _keys(fc))
        _check_scrub(tag, node, key, pos, n, [(1, 1.0), (10, 0.0), (20, 1.0), (30, 0.0)])
        scenes._leave_pose()


def test_typed_weight_replaces_the_key_at_a_keyed_frame():
    """Frame 10 holds the key 0: typing 1 there with Auto Key on replaces it (after Auto Key keyed 1 at frame 20, so
    1 is also the value it saw last)."""
    for tag, make, n in CASES:
        node, key, pos = _keyed_weight(make, n)
        with _AutoKey():
            _type(20, "1")
            _type(10, "1")
            _type(30, "0")
        _check_scrub(tag, node, key, pos, n, [(1, 1.0), (10, 1.0), (20, 1.0), (30, 0.0)])
        scenes._leave_pose()


def test_weight_written_elsewhere_is_keyed():
    """A weight written outside the Channel Box (the Attribute Editor field writes the node's weight property) is
    keyed by Auto Key too, also back to the value it showed at another frame."""
    for tag, make, n in CASES:
        node, key, pos = _keyed_weight(make, n)
        row = _row()
        prop = row.name if row.kind == "CUSTOM" else cb.constraint_weight(node, key)
        assert prop is not None and prop.startswith(multi.WEIGHT), (tag, prop)
        with _AutoKey():
            for frame, value in ((20, 1.0), (30, 0.0)):
                bpy.context.scene.frame_set(frame)
                node[prop] = value
                node.id_data.update_tag()
                _settle()
        _check_scrub(tag, node, key, pos, n, [(1, 1.0), (10, 0.0), (20, 1.0), (30, 0.0)])
        scenes._leave_pose()


def test_unkeyed_weight_is_not_keyed():
    """Like Maya (and the kit's other channels), Auto Key keys only a weight that already has keys: the node's own
    Translate is keyed, the weight is not, so typing a weight keys nothing."""
    for tag, make, n in CASES:
        node, _targets, pos = make(n)
        key = cb.row_key(_row())
        node.keyframe_insert("location", frame=1)
        with _AutoKey():
            _type(10, "0")
            assert abs(cb.get_value(node, key)) < 1e-9, (tag, "typed", cb.get_value(node, key))
            assert cb.fcurve(node, key) is None, (tag, "no key on a weight without keys", _keys(cb.fcurve(node, key)))
            curves = [(fc.data_path, fc.array_index, len(fc.keyframe_points)) for fc in kit.fcurves(node.id_data)]
            assert not [c for c in curves if multi.WEIGHT in c[0]], (tag, "no weight curve", curves)
            assert len(curves) == 3 and all(c[2] == 1 for c in curves), (tag, "Translate stays as keyed", curves)
        scenes._leave_pose()


def test_one_undo_takes_back_the_weight_and_its_key():
    """The typed weight and its Auto Key key are one step: one Undo puts both back (the weight shows its curve
    again), one Redo brings both back."""
    for tag, make, n in CASES:
        node, key, _pos = _keyed_weight(make, n)
        name = node.name
        bone = isinstance(node, bpy.types.PoseBone)
        arm = node.id_data.name

        def live():
            ob = bpy.data.objects[arm]
            return ob.pose.bones[name] if bone else ob

        with _AutoKey():
            bpy.context.scene.frame_set(20)
            bpy.ops.ed.undo_push(message="Frame")
            _row().text = "1"
            bpy.ops.ed.undo_push(message="Channel Box")       # the typed field's own step, like the UI pushes it
            _settle()
            assert _keys(cb.fcurve(live(), key)) == [(1, 1.0), (10, 0.0), (20, 1.0)], (tag, "keyed")
            bpy.ops.ed.undo()
            auto_key._reload_seen()
            if bpy.app.timers.is_registered(undo_pairs.run_extra):
                bpy.app.timers.unregister(undo_pairs.run_extra)
            undo_pairs.run_extra()
            got = (round(cb.get_value(live(), key), 6), _keys(cb.fcurve(live(), key)))
            assert got == (0.0, [(1, 1.0), (10, 0.0)]), (tag, "one Undo", got)
            bpy.ops.ed.redo()
            auto_key._reload_seen()
            if bpy.app.timers.is_registered(undo_pairs.run_extra):
                bpy.app.timers.unregister(undo_pairs.run_extra)
            undo_pairs.run_extra()
            got = (round(cb.get_value(live(), key), 6), _keys(cb.fcurve(live(), key)))
            assert got == (1.0, [(1, 1.0), (10, 0.0), (20, 1.0)]), (tag, "one Redo", got)
        scenes._leave_pose()


def test_keyed_channel_moved_back_to_an_earlier_value_is_keyed():
    """The same rule for an ordinary channel: Translate X keyed 0 at frame 1 and 5 at frame 10, Auto Key turned on at
    frame 1; at frame 10 the cube is moved back to 0 -> a key 0 at frame 10."""
    scenes._fresh()
    ob = scenes._cube("pCube1")
    ob.location.x = 0.0
    ob.keyframe_insert("location", index=0, frame=1)
    ob.location.x = 5.0
    ob.keyframe_insert("location", index=0, frame=10)
    bpy.context.scene.frame_set(1)
    with _AutoKey():
        bpy.context.scene.frame_set(10)
        assert abs(ob.location.x - 5.0) < 1e-6
        ob.location.x = 0.0
        _settle()
        fc = kit.fcurves(ob).find("location", index=0)
        assert _keys(fc) == [(1, 0.0), (10, 0.0)], _keys(fc)
        # a plain update after a frame change (a selection change) keys nothing
        bpy.context.scene.frame_set(5)
        ob.select_set(not ob.select_get())
        auto_key._pending[ob.name] = bpy.context.scene.frame_current
        _settle()
        assert _keys(fc) == [(1, 0.0), (10, 0.0)], ("no key from a selection change", _keys(fc))
