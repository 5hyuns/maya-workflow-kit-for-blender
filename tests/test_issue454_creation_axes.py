"""Issue #454: a creation node's Axis / Pivot / Normal / Center show in Channel Box INPUTS and the Attribute Editor on
the scene's axes, the same numbers the Create option windows take (Axis Z = upright); typing one turns the shape
the same way."""

from importlib import import_module

import bpy

import kit

ph = import_module(kit.MODULE + ".operators.prim_history")
cbv = import_module(kit.MODULE + ".ui.cb_values")
ci = import_module(kit.MODULE + ".ui.creation_inputs")
na = import_module(kit.MODULE + ".ui.node_attributes")
keys = import_module(kit.MODULE + ".ui.cb_keys")


def _new(kind, values=None):
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    return ph.create_object(bpy.context, kind, values)


def _cb(ob, name):
    return cbv._history_get(ob, keys.HISTORY_PREFIX + name)


def _extent(ob):
    vs = [v.co for v in ob.data.vertices]
    return [max(v[i] for v in vs) - min(v[i] for v in vs) for i in range(3)]


def test_upright_cylinder_shows_axis_z():
    ob = _new('CYLINDER')
    assert (_cb(ob, "axisX"), _cb(ob, "axisY"), _cb(ob, "axisZ")) == (0.0, 0.0, 1.0)
    text = bpy.context.scene.allset_creation.axisZ_text
    assert float(text) == 1.0, text


def test_typing_axis_y_lays_the_cylinder_along_scene_y():
    ob = _new('CYLINDER', {"height": 6.0})
    cbv._history_set(ob, keys.HISTORY_PREFIX + "axisZ", 0.0)
    cbv._history_set(ob, keys.HISTORY_PREFIX + "axisY", 1.0)
    assert (_cb(ob, "axisX"), _cb(ob, "axisY"), _cb(ob, "axisZ")) == (0.0, 1.0, 0.0)
    ex = _extent(ob)
    assert ex[1] > ex[0] * 1.5 and ex[1] > ex[2] * 1.5, ex     # the height runs along Y


def test_nurbs_circle_normal_and_center():
    ob = _new('NURBS_CIRCLE')
    assert (_cb(ob, "normalX"), _cb(ob, "normalY"), _cb(ob, "normalZ")) == (0.0, 0.0, 1.0)
    k = ph.node_of(ob)[1].get("unit", 1.0)
    cbv._history_set(ob, keys.HISTORY_PREFIX + "centerY", 2.0 * k)
    assert abs(_cb(ob, "centerY") - 2.0 * k) < 1e-9
    ys = [p.co[1] for sp in ob.data.splines for p in sp.points]
    assert abs((max(ys) + min(ys)) / 2 - 2.0 * k) < 1e-6, ys


def test_attribute_editor_rows_and_defaults_on_scene_axes():
    ob = _new('NURBS_SPHERE')
    owner, node = ph.node_of(ob)
    ed = na.PrimitiveNode(ob, owner, node)
    p = ed.params
    assert (p["axisX"], p["axisY"], p["axisZ"]) == (0.0, 0.0, 1.0)
    assert ed.spec.defaults["axisZ"] == 1.0 and ed.spec.defaults["axisY"] == 0.0
    ed.preview(bpy.context, dict(p, pivotY=1.0))
    assert abs(ed.params["pivotY"] - 1.0) < 1e-9 and abs(ph.attrs(ph.owner_of(ob))["pivotZ"] + 1.0) < 1e-9


def test_round_trip_is_exact():
    vals = {"axisX": 0.25, "axisY": -0.5, "axisZ": 0.75, "pivotX": 1.0, "pivotY": 2.0, "pivotZ": 3.0}
    shown = ph.to_scene(vals)
    assert (shown["axisY"], shown["axisZ"]) == (-0.75, -0.5)
    assert ph.from_scene(shown) == vals
