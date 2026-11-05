"""Graph Editor Curves > Clamp Curves and Offset Curves like Maya: they act on the selected keys (all keys of the shown
curves when none is selected). Clamp: values above the limit (default 0) become the limit, or values below it;
Offset: keys move by a number of frames (default 1), or so the first one lands on a frame."""

from importlib import import_module

import bpy

import kit
from test_remove_keys import Editor, _fc, _scene, _select, _times

menu_map = import_module(kit.MODULE + ".ui.editor_menu_map")


def _values(ob, index=0):
    return [round(kp.co.y, 3) for kp in _fc(ob, index).keyframe_points]


def test_menu_items():
    m = menu_map.MAP
    assert m["Graph Editor/Curves/Clamp Curves"] == "allset.clamp_curves"
    assert m["Graph Editor/Curves/Offset Curves"] == "allset.offset_curves"


def test_clamp_selected_keys_above_zero():
    a, b = _scene()
    _select(a, (3.5, 5, 6))                       # values 2, 3, 4
    with Editor():
        assert bpy.ops.allset.clamp_curves() == {'FINISHED'}
    assert _values(a) == [0, 1, 0, 0, 0, 5, 6], "only the selected keys"
    assert _values(b) == [1, 2.5, 5, 7, 10]


def test_clamp_below_a_limit_and_handles_follow():
    a, _b = _scene()
    _select(a, (1, 2, 3.5, 5))
    kp = _fc(a).keyframe_points[0]
    hl = kp.handle_left.y - kp.co.y
    with Editor():
        assert bpy.ops.allset.clamp_curves(limit=2.5, side='BELOW') == {'FINISHED'}
    assert _values(a) == [2.5, 2.5, 2.5, 3, 4, 5, 6]
    kp = _fc(a).keyframe_points[0]
    assert abs((kp.handle_left.y - kp.co.y) - hl) < 1e-4, "the tangent keeps its shape"


def test_clamp_without_selection_uses_shown_curves():
    a, b = _scene()
    with Editor():
        assert bpy.ops.allset.clamp_curves(limit=4.0) == {'FINISHED'}
    assert _values(a) == [0, 1, 2, 3, 4, 4, 4]
    assert _values(a, 1) == [1, 4, 4]
    assert _values(b) == [1, 2.5, 4, 4, 4]


def test_offset_by_frames_and_to_start():
    a, b = _scene()
    _select(a, (5, 6, 8))
    with Editor():
        assert bpy.ops.allset.offset_curves() == {'FINISHED'}
    assert _times(a) == [1, 2, 3.5, 6, 7, 9, 10], "default: one frame later"
    assert _values(a) == [0, 1, 2, 3, 4, 5, 6]
    a, b = _scene()
    _select(a, (5, 6, 8))
    _select(b, (7,))
    with Editor():
        assert bpy.ops.allset.offset_curves(frames=20, mode='START') == {'FINISHED'}
    assert _times(a) == [1, 2, 3.5, 10, 20, 21, 23], "the first selected key (5) lands on 20"
    assert _times(b) == [1, 2.5, 5, 10, 22]


def test_offset_without_selection_moves_shown_curves():
    a, b = _scene()
    with Editor():
        assert bpy.ops.allset.offset_curves(frames=-2.5) == {'FINISHED'}
    assert _times(a, 1) == [-1.5, 2.5, 7.5]
    assert _times(b) == [-1.5, 0, 2.5, 4.5, 7.5]


def test_time_ranges():
    a, b = _scene()
    sc = bpy.context.scene
    sc.use_preview_range = True
    sc.frame_preview_start, sc.frame_preview_end = 3, 6
    _select(a, (1, 2, 3.5, 5, 6, 8, 10))
    with Editor():
        assert bpy.ops.allset.clamp_curves(limit=0.0, time_range='TIME_SLIDER') == {'FINISHED'}
    assert _values(a) == [0, 1, 0, 0, 0, 5, 6], "only the keys in the playback range 3..6"
    assert _values(b) == [1, 2.5, 5, 7, 10], "the curves of the selected keys only"
    sc.use_preview_range = False
    a, b = _scene()
    with Editor():
        assert bpy.ops.allset.offset_curves(frames=3, time_range='START_END', start=4, end=7) == {'FINISHED'}
    assert _times(a) == [1, 2, 3.5, 8, 9, 10], _times(a)   # 5, 6 -> 8, 9; the old key on 8 gives way
    assert _times(b) == [1, 2.5, 8, 10], _times(b)
