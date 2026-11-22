"""Issue #453: Aim vector / Up vector (Constrain > Aim / Normal / Tangent) and Motion Path Front / Up axis are the
constrained node's own axes, as the Channel Box shows them: an object's local X / Y / Z, a joint's X down the bone.
Defaults keep the upright result (+X at the target, the object's Z up); option values saved with the older reading
keep their result."""

import json
from importlib import import_module

import bpy
from mathutils import Vector

import kit

ow = import_module(kit.MODULE + ".operators.option_windows")
rt = import_module(kit.MODULE + ".operators.rig_tools")
mp = import_module(kit.MODULE + ".operators.motion_path_228")
sa = import_module(kit.MODULE + ".operators.scene_axes")
preferences = import_module(kit.MODULE + ".preferences")


def _clear():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    preferences.get().option_settings = ""


def _empty(name, loc=(0.0, 0.0, 0.0)):
    ob = bpy.data.objects.new(name, None)
    ob.location = loc
    bpy.context.scene.collection.objects.link(ob)
    return ob


def _select(*obs):
    for o in bpy.context.scene.objects:
        o.select_set(False)
    for o in obs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = obs[-1]


def _aim(values):
    _clear()
    tgt, drv = _empty("locator1", (5.0, 0.0, 0.0)), _empty("locator2")
    _select(tgt, drv)
    res = ow.run(ow._BY_KEY["aim_constraint"], bpy.context, values)
    assert not isinstance(res, str), res
    bpy.context.view_layer.update()
    return drv.matrix_world.to_3x3()


def _near(a, b):
    return (Vector(a) - Vector(b)).length < 1e-5


def test_defaults_read_the_nodes_own_axes():
    d = ow._BY_KEY["aim_constraint"].defaults()
    assert d["aim_vector"] == (1.0, 0.0, 0.0) and d["up_vector"] == (0.0, 0.0, 1.0)
    for key in ("normal_constraint", "tangent_constraint"):
        assert ow._BY_KEY[key].defaults()["up_vector"] == (0.0, 0.0, 1.0)
    m = ow._BY_KEY["motion_path_attach"].defaults()
    assert (m["front_axis"], m["up_axis"]) == ("X", "Z")
    assert rt.local_axis((0.0, 1.0, 0.0)) == Vector((0.0, 1.0, 0.0))
    assert rt.local_axis((0.0, 1.0, 0.0), bone=True) == Vector((0.0, 0.0, 1.0))     # a joint's Y = bone Z


def test_default_aim_stays_upright():
    m = _aim({})
    assert _near(m.col[0], (1.0, 0.0, 0.0)) and _near(m.col[2], (0.0, 0.0, 1.0)), m


def test_up_vector_y_turns_the_objects_y_up():
    m = _aim({"up_vector": (0.0, 1.0, 0.0)})
    assert _near(m.col[0], (1.0, 0.0, 0.0)) and _near(m.col[1], (0.0, 0.0, 1.0)), m


def test_aim_vector_y_points_the_objects_y_at_the_target():
    m = _aim({"aim_vector": (0.0, 1.0, 0.0), "up_vector": (0.0, 0.0, 1.0)})
    assert _near(m.col[1], (1.0, 0.0, 0.0)) and _near(m.col[2], (0.0, 0.0, 1.0)), m


def test_motion_path_axes_are_local_axes():
    assert mp.axes("X", "Z") == ('FORWARD_X', 'UP_Z', None)
    assert mp.axes("X", "Y") == ('FORWARD_X', 'UP_Y', None)
    assert mp.axes("Y", "Z", inverse_front=True) == ('TRACK_NEGATIVE_Y', 'UP_Z', None)


def test_saved_values_keep_their_result():
    prefs = preferences.get()
    _clear()
    prefs.option_settings = json.dumps({
        ow.AXES_KEY: 2,
        "aim_constraint": {"aim_vector": [1.0, 0.0, 0.0], "up_vector": [0.0, 1.0, 0.0]},
        "normal_constraint": {"up_vector": [0.0, 0.0, 1.0]},
        "motion_path_attach": {"front_axis": "Z", "up_axis": "Y", "inverse_front": False}})
    a = ow.saved("aim_constraint")
    assert _near(a["up_vector"], (0.0, 0.0, 1.0)) and _near(a["aim_vector"], (1.0, 0.0, 0.0)), a
    assert _near(ow.saved("normal_constraint")["up_vector"], (0.0, -1.0, 0.0))
    m = ow.saved("motion_path_attach")
    assert (m["front_axis"], m["up_axis"], m["inverse_front"]) == ("Y", "Z", True), m
    # older files (no marker) also get the earlier conversion, once
    prefs.option_settings = json.dumps({"aim_constraint": {"up_vector": [0.0, 1.0, 0.0],
                                                           "world_up_vector": [0.0, 1.0, 0.0]}})
    a = ow.saved("aim_constraint")
    assert _near(a["up_vector"], (0.0, 0.0, 1.0)) and _near(a["world_up_vector"], (0.0, 0.0, 1.0)), a
    ow.store("poly_cube", {"width": 2.0})
    assert json.loads(prefs.option_settings)[ow.AXES_KEY] == sa.VERSION == 3
    assert _near(ow.saved("aim_constraint")["up_vector"], (0.0, 0.0, 1.0))
    prefs.option_settings = ""
