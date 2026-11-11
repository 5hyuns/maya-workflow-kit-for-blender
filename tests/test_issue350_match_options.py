"""#350: Modify > Match Transformations option boxes open their option windows, like Maya:

- Match All Transforms Options: Transforms Translate / Rotate / Scale (all on), Match bounding box size (off, only with
  Scale);
- Match Translation / Rotation / Scaling Options: All (on) or X / Y / Z; Scaling also Match bounding box size (off);
- Match Pivots Options: Pivots Rotate / Scale (on), Orientation (off).

The kit's results: only the checked transforms / channels change (a checked channel takes the value the full match
gives it, also under a turned and stretched parent); Match bounding box size scales each axis so the boxes get the
same size; nothing checked runs nothing; Orientation turns the object to the target's orientation while its geometry
and children stay; a plain menu click runs with the saved options."""

import math
from importlib import import_module

import bpy
from mathutils import Euler, Matrix, Vector

import kit

ow = import_module(kit.MODULE + ".operators.option_windows")
owm = import_module(kit.MODULE + ".operators.option_windows_match")
menu_sets = import_module(kit.MODULE + ".ui.menu_sets")
editor = import_module(kit.MODULE + ".ui.option_editor")

TOL = 1e-4
MENU = "Modify/Match Transformations/"
WINDOWS = {
    "Match All Transforms": ("match_all", "Match All Transforms Options",
                             {"translate": True, "rotate": True, "scale": True, "box": False}),
    "Match Translation": ("match_translation", "Match Translation Options",
                          {"all": True, "x": False, "y": False, "z": False}),
    "Match Rotation": ("match_rotation", "Match Rotation Options", {"all": True, "x": False, "y": False, "z": False}),
    "Match Scaling": ("match_scaling", "Match Scaling Options",
                      {"all": True, "x": False, "y": False, "z": False, "box": False}),
    "Match Pivots": ("match_pivots", "Match Pivots Options", {"rotate": True, "scale": True, "orient": False}),
}


def _clear():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for me in list(bpy.data.meshes):
        bpy.data.meshes.remove(me)
    for key in ("match_all", "match_translation", "match_rotation", "match_scaling", "match_pivots"):
        ow.store(key, None)


def _box(name, size=(1, 1, 1), loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), parent=None):
    """A box mesh of ``size`` around its origin."""
    sx, sy, sz = (s / 2 for s in size)
    me = bpy.data.meshes.new(name)
    me.from_pydata([(x, y, z) for x in (-sx, sx) for y in (-sy, sy) for z in (-sz, sz)], [],
                   [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)])
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.parent = parent
    ob.location, ob.rotation_euler, ob.scale = loc, Euler([math.radians(a) for a in rot]), scale
    bpy.context.view_layer.update()
    return ob


def _empty(name, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1)):
    ob = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(ob)
    ob.location, ob.rotation_euler, ob.scale = loc, Euler([math.radians(a) for a in rot]), scale
    bpy.context.view_layer.update()
    return ob


def _pick(*obs):
    """Pick ``obs`` in order: the last one is the target."""
    for o in bpy.data.objects:
        o.select_set(False)
    for o in obs:
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        bpy.context.view_layer.update()


def _channels(ob):
    return (Vector(ob.location), Vector(ob.rotation_euler), Vector(ob.scale))


def _world_verts(ob):
    bpy.context.view_layer.update()
    return [ob.matrix_world @ v.co for v in ob.data.vertices]


def _scene():
    """A source under a turned, stretched parent and a target under another one."""
    lp = _empty("lead_parent", (3, -1, 2), (0, 45, 20), (2, 1, 1))
    lead = _box("lead", (2, 3, 4), (1, 2, 3), (30, 40, 50), (1.5, 0.5, 2.0), parent=lp)
    sp = _empty("src_parent", (-2, 1, 0), (60, 0, -30), (1, 3, 0.5))
    src = _box("src", (1, 1, 1), (-1, 0.5, 4), (10, -20, 70), (0.5, 1.5, 2.5), parent=sp)
    return lead, src


def _full(kind):
    """Channels of a full match of ``kind`` (a fresh scene), for the per-axis checks."""
    _clear()
    lead, src = _scene()
    _pick(src, lead)
    assert bpy.ops.allset.match_transform(kind=kind) == {'FINISHED'}
    bpy.context.view_layer.update()
    return _channels(src)


def test_option_boxes_open_maya_windows():
    for label, (key, title, defaults) in WINDOWS.items():
        path = MENU + label
        w = ow.find_path(path)
        assert w is not None and w.key == key and w.title == title, (path, w and w.key)
        assert w.action == label and w.defaults() == defaults, (w.action, w.defaults())
        assert menu_sets.option_kind(path) == "window", path
        assert getattr(bpy.ops.allset, "opt_" + key).get_rna_type() is not None
    w = ow._BY_KEY["match_all"]
    assert w.enabled({"scale": False}, "box") is False and w.enabled({"scale": True}, "box") is True


def test_all_and_axes_turn_each_other_off():
    editor.prepare("match_translation")
    owner = editor.owner(bpy.context.window_manager, "match_translation")
    owner.all = True
    owner.x = True
    assert owner.all is False and owner.x is True
    owner.z = True
    assert owner.x is True and owner.z is True and owner.all is False
    owner.all = True
    assert (owner.x, owner.y, owner.z) == (False, False, False)


def test_match_all_only_the_checked_transforms():
    _clear()
    lead = _box("lead", (2, 3, 4), (1, 2, 3), (30, 40, 50), (1.5, 0.5, 2.0))
    src = _box("src", (1, 1, 1), (-1, 0.5, 4), (10, -20, 70), (0.5, 1.5, 2.5))
    t0, r0, s0 = _channels(src)
    _pick(src, lead)
    ow.run(ow._BY_KEY["match_all"], bpy.context, {"translate": True, "rotate": False, "scale": False})
    bpy.context.view_layer.update()
    t, r, s = _channels(src)
    assert (t - Vector(lead.location)).length < TOL and (r - r0).length < TOL and (s - s0).length < TOL
    # nothing checked: nothing runs
    res = ow.run(ow._BY_KEY["match_all"], bpy.context, {"translate": False, "rotate": False, "scale": False})
    assert res == {'CANCELLED'}, res
    assert (_channels(src)[0] - t).length < TOL


def test_match_bounding_box_size():
    _clear()
    lead = _box("lead", (2, 3, 4), (1, 2, 3), (0, 0, 0), (1.0, 2.0, 1.0))
    src = _box("src", (1, 1, 1), (-1, 0.5, 4), (0, 45, 0), (2.0, 1.0, 1.0))
    _pick(src, lead)
    ow.run(ow._BY_KEY["match_all"], bpy.context, {"box": True})
    bpy.context.view_layer.update()
    assert (Vector(src.scale) - Vector((2, 6, 4))).length < TOL, tuple(src.scale)     # lead box 2 x 6 x 4
    # Match Scaling Y only with the box: only Scale Y, sized by the box
    src.scale = (2.0, 1.0, 1.0)
    bpy.context.view_layer.update()
    ow.run(ow._BY_KEY["match_scaling"], bpy.context, {"all": False, "y": True, "box": True})
    bpy.context.view_layer.update()
    assert (Vector(src.scale) - Vector((2, 6, 1))).length < TOL, tuple(src.scale)
    # the box without Scale does nothing to the scale
    src.scale = (2.0, 1.0, 1.0)
    bpy.context.view_layer.update()
    ow.run(ow._BY_KEY["match_all"], bpy.context, {"scale": False, "box": True})
    bpy.context.view_layer.update()
    assert (Vector(src.scale) - Vector((2, 1, 1))).length < TOL, tuple(src.scale)


def test_one_channel_takes_the_full_match_value():
    for kind, key, slot in (('TRANSLATE', "match_translation", 0), ('ROTATE', "match_rotation", 1),
                            ('SCALE', "match_scaling", 2)):
        full = _full(kind)[slot]
        for axis in "xz":
            _clear()
            lead, src = _scene()
            before = _channels(src)
            _pick(src, lead)
            res = ow.run(ow._BY_KEY[key], bpy.context, {"all": False, axis: True})
            assert res == {'FINISHED'}, (kind, axis, res)
            bpy.context.view_layer.update()
            after = _channels(src)
            i = "xyz".index(axis)
            for j in range(3):
                want = full[j] if j == i else before[slot][j]
                assert abs(after[slot][j] - want) < TOL, (kind, axis, j, tuple(after[slot]), tuple(full))
            for other in {0, 1, 2} - {slot}:
                assert (after[other] - before[other]).length < TOL, (kind, axis, "other transform moved")
        # no axis: nothing runs
        _clear()
        lead, src = _scene()
        _pick(src, lead)
        assert ow.run(ow._BY_KEY[key], bpy.context, {"all": False}) == {'CANCELLED'}


def test_plain_click_runs_with_the_saved_options():
    _clear()
    lead = _box("lead", (1, 1, 1), (1, 2, 3))
    src = _box("src", (1, 1, 1), (-1, 0.5, 4))
    ow.store("match_translation", {"all": False, "x": True, "y": False, "z": False})
    _pick(src, lead)
    assert bpy.ops.allset.menu_item(item=MENU + "Match Translation") == {'FINISHED'}
    bpy.context.view_layer.update()
    assert (Vector(src.location) - Vector((1, 0.5, 4))).length < TOL, tuple(src.location)
    ow.store("match_translation", None)


def test_match_pivots_options():
    _clear()
    lead = _box("lead", (1, 1, 1), (1, 2, 3), (30, 40, 50))
    src = _box("src", (1, 2, 3), (-1, 0.5, 4), (10, -20, 70))
    child = _box("child", (0.2, 0.2, 0.2), (0, 3, 4), parent=src)
    child.matrix_world = Matrix.Translation((0, 3, 4))
    bpy.context.view_layer.update()
    # nothing checked: nothing runs
    _pick(src, lead)
    assert ow.run(ow._BY_KEY["match_pivots"], bpy.context, {"rotate": False, "scale": False}) == {'CANCELLED'}
    # Scale only: the one kit pivot moves onto the target's, the geometry stays
    verts = _world_verts(src)
    ow.run(ow._BY_KEY["match_pivots"], bpy.context, {"rotate": False, "scale": True})
    bpy.context.view_layer.update()
    assert (src.matrix_world.translation - lead.matrix_world.translation).length < TOL
    assert all((p - q).length < TOL for p, q in zip(verts, _world_verts(src)))
    # Orientation only: the object turns to the target's orientation, its geometry and child stay
    _clear()
    lead = _box("lead", (1, 1, 1), (1, 2, 3), (30, 40, 50))
    src = _box("src", (1, 2, 3), (-1, 0.5, 4), (10, -20, 70), (1, 2, 0.5))
    child = _box("child", (0.2, 0.2, 0.2), parent=src)
    child.matrix_world = Matrix.Translation((0, 3, 4))
    bpy.context.view_layer.update()
    verts, child_at, pivot_at = _world_verts(src), child.matrix_world.translation.copy(), src.matrix_world.translation.copy()
    _pick(src, lead)
    assert ow.run(ow._BY_KEY["match_pivots"], bpy.context, {"rotate": False, "scale": False, "orient": True}) \
        == {'FINISHED'}
    bpy.context.view_layer.update()
    turn = src.matrix_world.to_quaternion().rotation_difference(lead.matrix_world.to_quaternion())
    assert math.degrees(turn.angle) < 1e-3, math.degrees(turn.angle)
    assert (src.matrix_world.translation - pivot_at).length < TOL
    assert all((p - q).length < TOL for p, q in zip(verts, _world_verts(src)))
    assert (child.matrix_world.translation - child_at).length < TOL


def test_apply_runs_and_keeps_the_values():
    # the window's Apply button: runs with the window's values, keeps them, the window stays open
    _clear()
    lead = _box("lead", (1, 1, 1), (1, 2, 3))
    src = _box("src", (1, 1, 1), (-1, 0.5, 4))
    _pick(src, lead)
    window = ow._BY_KEY["match_translation"]
    holder = type("Holder", (), {})()
    for name, value in {"all": False, "x": False, "y": False, "z": True, "apply_now": True}.items():
        setattr(holder, name, value)
    ow._apply_update(window)(holder, bpy.context)
    bpy.context.view_layer.update()
    assert (Vector(src.location) - Vector((-1, 0.5, 3))).length < TOL, tuple(src.location)
    assert holder.apply_now is False
    assert ow.saved("match_translation") == {"all": False, "x": False, "y": False, "z": True}
    ow.store("match_translation", None)
