"""Enable Stepped Preview with animation layers and Trax clips: each layer's (and clip's) curves are stepped before
they are blended, like Maya; NLA stacks the kit did not make are left to Blender."""

from importlib import import_module

import bpy

import kit

pm = import_module(kit.MODULE + ".operators.playback_maya")
al = import_module(kit.MODULE + ".operators.anim_layers")
compat = import_module(kit.MODULE + ".compat")


def _clear():
    sc = bpy.context.scene
    sc.allset_stepped_preview = False
    sc.allset_auto_key = False
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for act in list(bpy.data.actions):
        bpy.data.actions.remove(act)
    sc.allset_anim_layers.clear()
    sc.allset_anim_layer_index = 0
    sc.frame_start, sc.frame_end, sc.use_preview_range = 1, 120, False
    return sc


def _cube(sc, keys):
    ob = bpy.data.objects.new("pCube1", bpy.data.meshes.new("pCubeShape1"))
    sc.collection.objects.link(ob)
    for f, x in keys:
        ob.location.x = x
        ob.keyframe_insert("location", index=0, frame=f)
    for o in sc.objects:
        o.select_set(o == ob)
    bpy.context.view_layer.objects.active = ob
    return ob


def _x(sc, ob, f):
    sc.frame_set(f)
    return round(ob.location.x, 4)


def _layered():
    """Base tx 0@1 5@12 0@24, AnimLayer1 (additive) adds 2 at 6 and -1 at 18."""
    sc = _clear()
    ob = _cube(sc, ((1, 0.0), (12, 5.0), (24, 0.0)))
    bpy.ops.allset.anim_layer_create(from_selected=True)
    for f, d in ((6, 2.0), (18, -1.0)):
        al.key(ob, "location", 0, frame=f, value=al.base_curve(ob, "location", 0).evaluate(f) + d, scene=sc)
    layer = next(fc for fc in al.layer_curves(ob, "AnimLayer1") if fc.data_path == "location")
    return sc, ob, al.base_curve(ob, "location", 0), layer


def test_layers_step_each_curve_then_blend():
    sc, ob, base, layer = _layered()
    assert ob.animation_data.action_influence == 0.0, "the shown layer action plays only through its strip"
    smooth = {f: _x(sc, ob, f) for f in (1, 6, 9, 12, 15, 18, 20, 24)}
    sc.allset_stepped_preview = True
    for f in (1, 24):
        assert _x(sc, ob, f) == smooth[f], f"where no curve is between keys the result is unchanged ({f})"

    def held(fc, f):
        return max(k.co.x for k in fc.keyframe_points if k.co.x <= f)
    for f in (6, 9, 12, 15, 18, 20):
        want = round(base.evaluate(held(base, f)) + layer.evaluate(held(layer, f)), 4)
        assert _x(sc, ob, f) == want, (f, _x(sc, ob, f), want)
        if f not in (6, 12, 18):
            assert want != smooth[f]
    assert _x(sc, ob, 9) == 2.0, "base holds 0 (key 1), the layer holds +2 (key 6)"
    sc.frame_set(15)
    sc.allset_stepped_preview = False
    assert round(ob.location.x, 4) == smooth[15], "off: the blended curve values again"
    assert {f: _x(sc, ob, f) for f in smooth} == smooth


def test_keyed_layer_weight_is_stepped_too():
    sc, ob, base, layer = _layered()
    st = al.tracks(ob)["AnimLayer1"].strips[0]
    wc = al.weight_curve(st)
    wc.keyframe_points.insert(1, 0.0)
    wc.keyframe_points.insert(20, 1.0)
    st.influence = 0.0
    sc.allset_stepped_preview = True
    assert _x(sc, ob, 15) == round(base.evaluate(12), 4), "weight held at 0 until its key at 20"
    assert _x(sc, ob, 20) == round(base.evaluate(12) + layer.evaluate(18), 4)
    sc.allset_stepped_preview = False


def test_auto_key_on_a_layer_keys_nothing_while_scrubbing():
    auto_key = import_module(kit.MODULE + ".operators.auto_key")
    sc, ob, base, layer = _layered()
    sc.allset_stepped_preview = True
    sc.allset_auto_key = True
    counts = (len(base.keyframe_points), len(layer.keyframe_points))
    for f in (3, 9, 15, 20):
        sc.frame_set(f)
        bpy.context.view_layer.update()
        auto_key._flush()
    assert (len(base.keyframe_points), len(layer.keyframe_points)) == counts
    sc.allset_auto_key = False
    sc.allset_stepped_preview = False


def test_trax_clip_is_stepped():
    sc = _clear()
    ob = _cube(sc, ((1, 0.0), (10, 4.0), (24, 10.0)))
    assert bpy.ops.allset.trax_create_clip() == {'FINISHED'}
    smooth = _x(sc, ob, 15)
    assert 4.0 < smooth < 10.0
    sc.allset_stepped_preview = True
    assert _x(sc, ob, 15) == 4.0
    assert _x(sc, ob, 5) == 0.0
    assert _x(sc, ob, 24) == 10.0
    sc.frame_set(15)
    sc.allset_stepped_preview = False
    assert round(ob.location.x, 4) == smooth


def test_other_nla_stacks_are_left_to_blender():
    sc = _clear()
    ob = _cube(sc, ((1, 0.0), (10, 10.0)))
    ad = ob.animation_data
    act = ad.action
    tr = ad.nla_tracks.new()
    tr.strips.new("mine", 1, act)
    ad.action = None
    smooth = _x(sc, ob, 5)
    sc.allset_stepped_preview = True
    assert _x(sc, ob, 5) == smooth, "a plain NLA strip plays its own curve values"
    sc.allset_stepped_preview = False
