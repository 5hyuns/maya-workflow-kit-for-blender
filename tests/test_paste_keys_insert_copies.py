"""Paste Keys with Copies 2: where two copies meet, Insert keeps the earlier copy's key and Merge the later one's
(like Maya). Keys 1 = 0, 10 = 5, 20 = 2 pasted at frame 5 onto a curve with keys at 1, 5, 8, 15 and 30."""

from importlib import import_module

import bpy

import kit

ow = import_module(kit.MODULE + ".operators.option_windows")
gkm = import_module(kit.MODULE + ".operators.graph_key_menu")
compat = import_module(kit.MODULE + ".compat")


def _cube(name, keys):
    ob = bpy.data.objects.new(name, bpy.data.meshes.new(name))
    bpy.context.scene.collection.objects.link(ob)
    for t, v in keys:
        ob.location[0] = v
        ob.keyframe_insert("location", index=0, frame=t)
        gkm.after_insert(ob, "location", 0, t)
    return ob


def _sel(ob):
    for o in bpy.data.objects:
        o.select_set(False)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob


def _paste(method):
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    a = _cube("a", [(1, 0.0), (10, 5.0), (20, 2.0)])
    b = _cube("b", [(1, 10.0), (5, 10.0), (8, 12.0), (15, 10.0), (30, 11.0)])
    _sel(a)
    assert ow.run(next(w for w in ow.WINDOWS if w.key == "copy_keys"), bpy.context, {}) == {'FINISHED'}
    bpy.context.scene.frame_set(5)
    _sel(b)
    assert ow.run(next(w for w in ow.WINDOWS if w.key == "paste_keys"), bpy.context,
                  {"time_range": "Current", "method": method, "copies": 2}) == {'FINISHED'}
    fc = next(f for f in compat.id_fcurves(b) if f.data_path == "location" and f.array_index == 0)
    return [(round(k.co.x, 4), round(k.co.y, 4)) for k in fc.keyframe_points]


def test_insert_copies_keep_the_earlier_key_where_they_meet():
    got = _paste("Insert")
    assert got == [(1, 10), (5, 0), (14, 5), (24, 2), (33, 5), (43, 2), (46, 12), (53, 10), (68, 11)], got


def test_merge_copies_take_the_later_key_where_they_meet():
    got = _paste("Merge")
    assert got == [(1, 10), (5, 0), (8, 12), (14, 5), (15, 10), (24, 0), (30, 11), (33, 5), (43, 2)], got
