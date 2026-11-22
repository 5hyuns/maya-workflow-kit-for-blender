"""Bake Simulation keys get the default tangents (Auto), like any new key in Maya: with Sample by 2 the values between
the baked keys follow a smooth curve, not straight lines."""

from importlib import import_module

import bpy

import kit

ow = import_module(kit.MODULE + ".operators.option_windows")
gkm = import_module(kit.MODULE + ".operators.graph_key_menu")
compat = import_module(kit.MODULE + ".compat")


def _scene():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    lead = bpy.data.objects.new("leader", bpy.data.meshes.new("leader"))
    bpy.context.scene.collection.objects.link(lead)
    for t, x in ((1, 0.0), (10, 10.0)):
        lead.location.x = x
        lead.keyframe_insert("location", index=0, frame=t)
        gkm.after_insert(lead, "location", 0, t)
    fol = bpy.data.objects.new("follower", bpy.data.meshes.new("follower"))
    bpy.context.scene.collection.objects.link(fol)
    for o in bpy.data.objects:
        o.select_set(False)
    fol.select_set(True)
    lead.select_set(True)
    bpy.context.view_layer.objects.active = fol
    assert ow.run(next(w for w in ow.WINDOWS if w.key == "point_constraint"), bpy.context, {}) == {'FINISHED'}
    lead.select_set(False)
    return fol


def test_baked_keys_are_auto_and_smooth_between_samples():
    fol = _scene()
    assert ow.run(next(w for w in ow.WINDOWS if w.key == "bake_simulation"), bpy.context,
                  {"time_range": "Start/End", "start": 1.0, "end": 10.0, "sample_by": 2.0}) == {'FINISHED'}
    fc = next(f for f in compat.id_fcurves(fol) if f.data_path == "location" and f.array_index == 0)
    assert [k.co.x for k in fc.keyframe_points] == [1.0, 3.0, 5.0, 7.0, 9.0]
    assert all(k.interpolation == 'BEZIER' for k in fc.keyframe_points)
    k1, k3 = fc.keyframe_points[0].co.y, fc.keyframe_points[1].co.y
    # an Auto first key is flat: the curve starts slower than the straight line between the samples
    assert fc.evaluate(2.0) < (k1 + k3) / 2.0 - 0.1, (fc.evaluate(2.0), k1, k3)
    assert abs(fc.evaluate(3.0) - k3) < 1e-5
