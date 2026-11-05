"""Playback > Playback Looping (Once / Oscillate) and Playback > Enable Stepped Preview, like Maya."""

from importlib import import_module

import bpy

from kit import MODULE

pm = import_module(MODULE + ".operators.playback_maya")
compat = import_module(MODULE + ".compat")
menu_map = import_module(MODULE + ".ui.menu_map")


def _keyed():
    sc = bpy.context.scene
    sc.allset_stepped_preview = False
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for act in list(bpy.data.actions):
        bpy.data.actions.remove(act)
    bpy.ops.mesh.primitive_cube_add()
    ob = bpy.context.active_object
    for f, v in ((1, 0.0), (10, 10.0)):
        ob.location.x = v
        ob.keyframe_insert("location", index=0, frame=f)
    for f, v in ((1, 0.0), (3.5, 5.0), (10, 9.0)):
        ob.location.y = v
        ob.keyframe_insert("location", index=1, frame=f)
    fcs = {fc.array_index: fc for fc in compat.id_fcurves(ob)}
    fcs[1].keyframe_points[1].interpolation = 'LINEAR'
    return sc, ob, fcs


def _at(sc, ob, f):
    sc.frame_set(int(f), subframe=f - int(f))
    return round(ob.location.x, 4), round(ob.location.y, 4)


def test_loop_step():
    s = pm.loop_step
    assert s('CONTINUOUS', 9, 1, 1, 1, 10, False) == (1, None, 1)
    assert s('ONCE', 5, 6, 0, 1, 10, False) == (1, None, 6)
    assert s('ONCE', 9, 10, 1, 1, 10, False) == (1, 'STOP', 10), "stops on the last frame"
    assert s('ONCE', 8, 1, 1, 1, 10, False) == (1, 'STOP', 10), "a wrap that skipped the end stops on the end too"
    assert s('ONCE', 2, 1, -1, 1, 10, False) == (-1, 'STOP', 1), "backward: stops on the first frame"
    assert s('OSCILLATE', 9, 10, 1, 1, 10, False) == (1, 'TURN', 10)
    assert s('OSCILLATE', 2, 1, -1, 1, 10, False) == (-1, 'TURN', 1)
    assert s('ONCE', 10, 1, 0, 1, 10, True) == (1, None, 1), "play pressed on the last frame starts again"
    assert s('ONCE', 1, 10, 0, 1, 10, True) == (-1, None, 10), "backward play from the first frame wraps"


def test_menu_items():
    m = menu_map.MAP
    assert m["Playback/Playback Looping/Oscillate"] == ("prop", "scene.allset_playback_loop", {"value": "OSCILLATE"})
    assert m["Playback/Enable Stepped Preview"] == ("prop", "scene.allset_stepped_preview", {})
    sc = bpy.context.scene
    assert sc.allset_playback_loop == 'CONTINUOUS' and not sc.allset_stepped_preview
    for want in ('ONCE', 'OSCILLATE', 'CONTINUOUS'):
        assert bpy.ops.allset.playback_loop_cycle() == {'FINISHED'}
        assert sc.allset_playback_loop == want


def test_stepped_preview_values_and_restore():
    sc, ob, fcs = _keyed()
    before = {i: [(k.interpolation, tuple(k.handle_left), tuple(k.handle_right)) for k in fc.keyframe_points]
              for i, fc in fcs.items()}
    smooth = [_at(sc, ob, f) for f in (1, 3, 3.6, 7, 10, 12)]
    sc.allset_stepped_preview = True
    got = [_at(sc, ob, f) for f in (1, 3, 3.5, 3.6, 7, 9.9, 10, 12)]
    assert got == [(0, 0), (0, 0), (0, 5), (0, 5), (0, 5), (0, 5), (10, 9), (10, 9)], got
    sc.allset_stepped_preview = False
    after = {i: [(k.interpolation, tuple(k.handle_left), tuple(k.handle_right)) for k in fc.keyframe_points]
             for i, fc in fcs.items()}
    assert after == before, (after, before)
    assert [_at(sc, ob, f) for f in (1, 3, 3.6, 7, 10, 12)] == smooth
    assert pm.STASH not in ob.animation_data.action


def test_keys_added_and_moved_while_on():
    sc, ob, fcs = _keyed()
    sc.allset_stepped_preview = True
    ob.location.x = 4.0
    ob.keyframe_insert("location", index=0, frame=5)
    bpy.context.view_layer.update()
    fx = fcs[0]
    assert all(k.interpolation == 'CONSTANT' for k in fx.keyframe_points), "a new key is stepped too"
    assert _at(sc, ob, 7) == (4.0, 5.0)
    fy = fcs[1]
    fy.keyframe_points[1].co.x = 4.5         # the Linear key moves while the preview is on
    fy.update()
    sc.allset_stepped_preview = False
    assert [k.interpolation for k in fx.keyframe_points] == ['BEZIER'] * 3
    assert [k.interpolation for k in fy.keyframe_points] == ['BEZIER', 'LINEAR', 'BEZIER']


def test_driver_curves_untouched_and_disable_restores():
    sc, ob, fcs = _keyed()
    d = ob.driver_add("location", 2)
    d.keyframe_points.insert(0, 0)
    d.keyframe_points.insert(10, 1)
    sc.allset_stepped_preview = True
    assert all(k.interpolation == 'BEZIER' for k in d.keyframe_points), "driver curves are not time curves"
    from kit import disable
    disable()
    assert [k.interpolation for k in fcs[1].keyframe_points] == ['BEZIER', 'LINEAR', 'BEZIER']
    assert pm.STASH not in ob.animation_data.action.keys()
