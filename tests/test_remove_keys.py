"""Graph Editor / Dope Sheet Keys > Remove Key like Maya: Unsnapped, Before / After Current Frame, Outside Selected
Range and Ripple Delete act on the curves of the selected keys; the range is the selected keys' first to last time."""

from importlib import import_module

import bpy

import kit

menu_map = import_module(kit.MODULE + ".ui.editor_menu_map")


def _scene():
    """Object A: X keys 1, 2, 3.5, 5, 6, 8, 10 (values 0..6) and Y keys 1, 5, 10; object B: X keys 1, 2.5, 5, 7, 10."""
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    obs = []
    for name, keys in (("A", {0: ((1, 0), (2, 1), (3.5, 2), (5, 3), (6, 4), (8, 5), (10, 6)),
                              1: ((1, 1), (5, 5), (10, 10))}),
                       ("B", {0: ((1, 1), (2.5, 2.5), (5, 5), (7, 7), (10, 10))})):
        bpy.ops.object.empty_add()
        ob = bpy.context.active_object
        ob.name = name
        for index, pairs in keys.items():
            for t, v in pairs:
                ob.location[index] = v
                ob.keyframe_insert("location", index=index, frame=t)
        for fc in kit.fcurves(ob):
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'
                kp.select_control_point = kp.select_left_handle = kp.select_right_handle = False
        obs.append(ob)
    for ob in obs:
        ob.select_set(True)
    bpy.context.scene.frame_set(5)
    return obs


def _fc(ob, index=0):
    return next(fc for fc in kit.fcurves(ob) if fc.data_path == "location" and fc.array_index == index)


def _times(ob, index=0):
    return [round(kp.co.x, 3) for kp in _fc(ob, index).keyframe_points]


def _select(ob, times, index=0):
    for kp in _fc(ob, index).keyframe_points:
        if any(abs(kp.co.x - t) < 1e-4 for t in times):
            kp.select_control_point = True


class Editor:
    def __init__(self, ui_type='FCURVES'):
        self.ui_type = ui_type

    def __enter__(self):
        self.area = bpy.context.window_manager.windows[0].screen.areas[0]
        self.old = self.area.ui_type
        self.area.ui_type = self.ui_type
        region = next(r for r in self.area.regions if r.type == 'WINDOW')
        self.ctx = bpy.context.temp_override(area=self.area, region=region)
        self.ctx.__enter__()
        return self

    def __exit__(self, *exc):
        self.ctx.__exit__(*exc)
        self.area.ui_type = self.old


def _run(mode, ui_type='FCURVES'):
    with Editor(ui_type):
        return bpy.ops.allset.remove_keys(mode=mode)


def test_menu_items_run_the_command_in_both_editors():
    for ed in ("Graph Editor", "Dope Sheet"):
        m = menu_map.MAP
        for item, mode in (("Unsnapped", "UNSNAPPED"), ("Before Current Frame", "BEFORE"),
                           ("After Current Frame", "AFTER"), ("Outside Selected Range", "OUTSIDE"),
                           ("Ripple Delete", "RIPPLE")):
            assert m[f"{ed}/Keys/Remove Key/{item}"] == ("allset.remove_keys", {"mode": mode}), (ed, item)


def test_unsnapped_on_the_curves_of_selected_keys():
    a, b = _scene()
    _select(a, [3.5, 6])
    _select(b, [2.5])
    assert _run("UNSNAPPED") == {'FINISHED'}
    assert _times(a) == [1, 2, 5, 6, 8, 10]
    assert _times(b) == [1, 5, 7, 10]
    assert _times(a, 1) == [1, 5, 10], "a curve without selected keys is left alone"


def test_before_and_after_current_frame_keep_the_key_on_it():
    a, b = _scene()
    _select(a, [3.5])
    assert _run("BEFORE") == {'FINISHED'}
    assert _times(a) == [5, 6, 8, 10]
    assert _times(b) == [1, 2.5, 5, 7, 10] and _times(a, 1) == [1, 5, 10]
    a, b = _scene()
    _select(a, [3.5])
    _select(b, [2.5])
    assert _run("AFTER", 'DOPESHEET') == {'FINISHED'}, "the Dope Sheet runs the same command"
    assert _times(a) == [1, 2, 3.5, 5] and _times(b) == [1, 2.5, 5]


def test_outside_selected_range_adds_keys_at_the_range_ends():
    a, b = _scene()
    _select(a, [3.5])
    _select(b, [2.5])                   # range 2.5 .. 3.5 over both curves
    va = _fc(a).evaluate(2.5)
    assert _run("OUTSIDE") == {'FINISHED'}
    assert _times(a) == [2.5, 3.5] and _times(b) == [2.5, 3.5]
    assert abs(_fc(a).keyframe_points[0].co.y - va) < 1e-4, "the new end key holds the curve's value"
    assert abs(_fc(b).keyframe_points[1].co.y - 3.5) < 1e-4


def test_ripple_delete_closes_the_gap():
    a, b = _scene()
    _select(a, [3.5, 6])                # range 3.5 .. 6, gap 2.5
    assert _run("RIPPLE") == {'FINISHED'}
    t = _times(a)
    assert t[:3] == [1, 2, 3.5] and t[4:] == [5.5, 7.5] and len(t) == 6, t
    assert 3.5 < _fc(a).keyframe_points[3].co.x < 3.53, "the end key lands just after the start"
    assert [round(kp.co.y, 3) for kp in _fc(a).keyframe_points] == [0, 1, 2, 4, 5, 6]
    assert _times(b) == [1, 2.5, 5, 7, 10], "curves without selected keys keep their keys"


def test_range_commands_need_selected_keys():
    a, _b = _scene()
    for mode in ("OUTSIDE", "RIPPLE"):
        assert _run(mode) == {'CANCELLED'}
    assert _times(a) == [1, 2, 3.5, 5, 6, 8, 10]
    assert _run("AFTER") == {'FINISHED'}, "without selected keys the shown curves are used"
    assert _times(a) == [1, 2, 3.5, 5] and _times(a, 1) == [1, 5]



def test_delete_keys_window_removes_exactly_the_selected_keys():
    gkm = import_module(kit.MODULE + ".operators.graph_key_menu")
    a, b = _scene()
    _select(a, [2, 3.5, 6])
    _select(b, [1, 10])
    with Editor():
        assert gkm.delete_selected(bpy.context) == 5
    assert _times(a) == [1, 5, 8, 10] and _times(b) == [2.5, 5, 7]
