"""Graph Editor tangent handles like Maya (#296): non-weighted tangents drawn at a fixed length on screen along
their direction, weighted ones at their real end; a drag turns a non-weighted tangent (its time length stays a
third of the way to the neighbour key); the kit takes Blender's handle display over in Maya mode and gives it back."""

import math
from importlib import import_module
from types import SimpleNamespace

import bpy
import numpy as np

import kit

gh = import_module(kit.MODULE + ".ui.graph_handles")
gk = import_module(kit.MODULE + ".ui.graph_keys_draw")
drag = import_module(kit.MODULE + ".operators.graph_handle_drag")
weights = import_module(kit.MODULE + ".operators.graph_weights")
prefs_mod = import_module(kit.MODULE + ".preferences")


class View2D:
    """A linear view: ``px_frame`` pixels per frame, ``px_value`` per display unit, frame 0 / value 0 at (x0, y0)."""

    def __init__(self, px_frame=20.0, px_value=10.0, x0=100.0, y0=200.0):
        self.f, self.v, self.x0, self.y0 = px_frame, px_value, x0, y0

    def view_to_region(self, x, y, clip=True):
        return self.x0 + x * self.f, self.y0 + y * self.v

    def region_to_view(self, x, y):
        return (x - self.x0) / self.f, (y - self.y0) / self.v


def _region(**kw):
    return SimpleNamespace(type='WINDOW', width=800, height=600, x=0, y=0, view2d=View2D(**kw))


def _space(**kw):
    base = dict(type='GRAPH_EDITOR', mode='FCURVES', use_normalization=False, show_handles=True,
                use_only_selected_keyframe_handles=False)
    base.update(kw)
    return SimpleNamespace(**base)


def _curve(keys=((1, 0.0), (10, 5.0), (19, 0.0))):
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    ob = bpy.data.objects.new("pCube1", bpy.data.meshes.new("pCubeShape1"))
    bpy.context.scene.collection.objects.link(ob)
    for f, v in keys:
        ob.location.y = v
        ob.keyframe_insert("location", index=1, frame=f)
    fc = kit.fcurves(ob).find("location", index=1)
    for kp in fc.keyframe_points:
        kp.select_control_point = kp.select_left_handle = kp.select_right_handle = False
        kp.handle_left_type = kp.handle_right_type = 'ALIGNED'
    return fc


def _ctx(fcurves, space):
    return SimpleNamespace(visible_fcurves=list(fcurves), scene=bpy.context.scene, space_data=space,
                           preferences=bpy.context.preferences)


def _ui():
    return bpy.context.preferences.system.ui_scale or 1.0


def test_fixed_ends_rule():
    ends = gh.fixed_ends([(0, 0), (0, 0), (10, 10), (10, 10)], [(-3, 4), (300, 400), (10, 10), (10, 10)],
                         [0, 1, 0, 1], 50.0)
    assert np.allclose(ends[0], (-30, 40)), ends           # along the arm, 50 px
    assert np.allclose(ends[1], (30, 40)), ends            # a long arm is shortened to 50 px
    assert np.allclose(ends[2], (-40, 10)), ends           # no arm: left points back in time
    assert np.allclose(ends[3], (60, 10)), ends            # right forward


def test_arm_rule_non_weighted_turns_only():
    # 20 px per frame, 10 px per unit; end 40 px right / 40 px up from the key
    arm = drag.arm_for(1, 40.0, 40.0, 20.0, 10.0, 1.0, False, third=3.0)
    assert arm == (3.0, 3.0 * 2.0), arm                    # time length stays the third; slope 4 units / 2 frames
    left = drag.arm_for(0, -40.0, 40.0, 20.0, 10.0, 1.0, False, third=3.0)
    assert left == (-3.0, 6.0), left                  # up-left: the arm rises before the key
    # crossing the key in time: held at half a pixel, nearly vertical
    steep = drag.arm_for(1, -10.0, 40.0, 20.0, 10.0, 1.0, False, third=3.0)
    assert steep[0] == 3.0 and steep[1] > 100.0, steep
    # display units per stored unit (degrees): the stored arm is in radians
    rot = drag.arm_for(1, 20.0, 10.0, 20.0, 10.0, 180.0 / math.pi, False, third=1.0)
    assert abs(rot[1] - math.radians(1.0)) < 1e-12, rot
    assert drag.arm_for(1, 20.0, 10.0, 20.0, 10.0, 1.0, False, third=None) is None    # a one-key curve


def test_arm_rule_weighted_follows_the_end():
    assert drag.arm_for(1, 40.0, 30.0, 20.0, 10.0, 1.0, True) == (2.0, 3.0)
    locked = drag.arm_for(1, 40.0, 30.0, 20.0, 10.0, 1.0, True, length=1.0)
    assert abs(math.hypot(*locked) - 1.0) < 1e-12 and abs(locked[1] / locked[0] - 1.5) < 1e-12, locked


def test_opposite_and_types():
    assert drag.opposite_arm((3.0, 6.0), third=1.5, weighted=False) == (-1.5, -3.0)
    opp = drag.opposite_arm((3.0, 4.0), length=10.0)
    assert np.allclose(opp, (-6.0, -8.0)), opp
    assert drag.dragged_types(('AUTO_CLAMPED', 'AUTO_CLAMPED'), 1) == ('ALIGNED', 'ALIGNED')
    assert drag.dragged_types(('VECTOR', 'VECTOR'), 0) == ('FREE', 'VECTOR')
    assert drag.dragged_types(('FREE', 'ALIGNED'), 1) == ('FREE', 'ALIGNED')


def test_handles_fixed_length_for_non_weighted():
    fc = _curve()
    weights.set_weighted(fc, False)
    weights.third_arms(fc)
    space, region = _space(), _region()
    h = gh.Handles(_ctx([fc], space), space, region)
    # 3 keys x 2 sides
    assert len(h) == 6, len(h)
    length = np.hypot(*(h.end_px - h.key_px).T)
    assert np.allclose(length, gh.FIXED_PX * _ui()), length
    # direction = the arm's direction on screen
    kp = fc.keyframe_points[1]
    r = next(i for i in range(len(h)) if h.keys[i] == 1 and h.sides[i] == 1)
    ax, ay = (kp.handle_right[0] - kp.co[0]) * 20.0, (kp.handle_right[1] - kp.co[1]) * 10.0
    d = h.end_px[r] - h.key_px[r]
    assert abs(math.atan2(d[1], d[0]) - math.atan2(ay, ax)) < 1e-6, (d, ax, ay)
    # weighted: the real handle
    weights.set_weighted(fc, True)
    h = gh.Handles(_ctx([fc], space), space, region)
    r = next(i for i in range(len(h)) if h.keys[i] == 1 and h.sides[i] == 1)
    want = region.view2d.view_to_region(*kp.handle_right)
    assert np.allclose(h.end_px[r], want), (h.end_px[r], want)


def test_handles_selection_and_display_rules():
    fc = _curve()
    weights.set_weighted(fc, False)
    kps = fc.keyframe_points
    kps[0].select_right_handle = True                  # a picked handle
    kps[1].select_control_point = True                 # a selected key: Blender sets its handle flags too
    kps[1].select_left_handle = kps[1].select_right_handle = True
    space, region = _space(), _region()
    h = gh.Handles(_ctx([fc], space), space, region)
    sel = {(int(h.keys[i]), int(h.sides[i])) for i in range(len(h)) if h.selected[i]}
    assert sel == {(0, 1)}, sel
    # On Active Keys: only around selected keys / handles
    active = _space(use_only_selected_keyframe_handles=True)
    h = gh.Handles(_ctx([fc], active), active, region)
    assert {int(k) for k in h.keys} == {0, 1}, h.keys
    # Show Handles off: none
    assert not len(gh.Handles(_ctx([fc], _space(show_handles=False)), _space(show_handles=False), region))


def test_pick_nearest_end():
    fc = _curve()
    weights.set_weighted(fc, False)
    space, region = _space(), _region()
    h = gh.Handles(_ctx([fc], space), space, region)
    r = next(i for i in range(len(h)) if h.keys[i] == 1 and h.sides[i] == 0)
    x, y = h.end_px[r]
    assert h.nearest(x + 3, y - 2, 10.0) == r
    assert h.nearest(x + 30, y, 10.0) is None
    assert h.row(r) == (fc, 1, 0)


def _drag_items(fc, rows_wanted, space, region):
    h = gh.Handles(_ctx([fc], space), space, region)
    rows = [i for i in range(len(h)) if (int(h.keys[i]), int(h.sides[i])) in rows_wanted]
    ctx = SimpleNamespace(region=region)
    return drag.Drag(ctx, h, rows)


def test_drag_turns_a_non_weighted_tangent():
    fc = _curve()
    weights.set_weighted(fc, False)
    weights.third_arms(fc)
    kp = fc.keyframe_points[1]
    space, region = _space(), _region()
    d = _drag_items(fc, {(1, 1)}, space, region)
    assert d
    d.apply(0.0, 25.0)                                  # the end 25 px up
    third = (19 - 10) / 3.0
    ax, ay = kp.handle_right[0] - kp.co[0], kp.handle_right[1] - kp.co[1]
    assert abs(ax - third) < 1e-5, ax                   # time length kept
    assert ay > 0.5, ay                                 # turned up
    # aligned: the left side turned along, its own third, opposite direction
    lx, ly = kp.handle_left[0] - kp.co[0], kp.handle_left[1] - kp.co[1]
    assert abs(lx + third) < 1e-5 and abs(ly / lx - ay / ax) < 1e-4, (lx, ly, ax, ay)
    d.restore()
    assert abs(kp.handle_right[1] - kp.co[1]) < 1e-5     # the flat peak again


def test_drag_moves_a_weighted_end_and_breaks_free_sides_alone():
    fc = _curve()
    weights.set_weighted(fc, True)
    kp = fc.keyframe_points[1]
    kp.handle_left_type = kp.handle_right_type = 'FREE'
    left = tuple(kp.handle_left)
    space, region = _space(), _region()
    d = _drag_items(fc, {(1, 1)}, space, region)
    before = region.view2d.view_to_region(*kp.handle_right)
    d.apply(40.0, -20.0)
    after = region.view2d.view_to_region(*kp.handle_right)
    assert np.allclose((after[0] - before[0], after[1] - before[1]), (40.0, -20.0), atol=1e-3), (before, after)
    assert tuple(kp.handle_left) == left                # a free side stays
    # an automatic tangent becomes aligned
    kp.handle_left_type = kp.handle_right_type = 'AUTO_CLAMPED'
    fc.update()
    kp = fc.keyframe_points[1]
    d = _drag_items(fc, {(1, 1)}, space, region)
    d.apply(0.0, 30.0)
    assert (kp.handle_left_type, kp.handle_right_type) == ('ALIGNED', 'ALIGNED')
    d.restore()
    assert (kp.handle_left_type, kp.handle_right_type) == ('AUTO_CLAMPED', 'AUTO_CLAMPED')


def test_box_rows_and_modes():
    fc = _curve()
    weights.set_weighted(fc, False)
    space, region = _space(), _region()
    h = gh.Handles(_ctx([fc], space), space, region)
    r = next(i for i in range(len(h)) if h.keys[i] == 1 and h.sides[i] == 1)
    x, y = h.end_px[r]
    rows = drag.box_rows(h, x - 2, y - 2, x + 2, y + 2)
    assert rows == [r], rows
    kp = fc.keyframe_points[1]
    assert drag.apply_box(h, rows, 'SET') == 1 and kp.select_right_handle
    before = drag.selected_handles(gh.Handles(_ctx([fc], space), space, region))
    assert drag.apply_box(h, rows, 'XOR', before) == 1 and not kp.select_right_handle
    assert drag.apply_box(h, rows, 'KEEP', before) == 1 and kp.select_right_handle
    assert drag.apply_box(h, rows, 'SUB') == 1 and not kp.select_right_handle


def test_box_keys_rule():
    keys = {("a", 0): (10.0, 10.0), ("a", 1): (50.0, 10.0), ("b", 0): (12.0, 30.0)}
    inside = drag.keys_in_box(keys, 0, 0, 20, 20)
    assert inside == {("a", 0)}, inside
    before = {("b", 0)}
    assert drag.box_key_rule('SET', before, inside) == {("a", 0)}       # not the whole curve the box crosses
    assert drag.box_key_rule('ADD', before, inside) == {("a", 0), ("b", 0)}
    assert drag.box_key_rule('SUB', {("a", 0), ("b", 0)}, inside) == {("b", 0)}


def _graph_area():
    win = bpy.context.window_manager.windows[0]
    area = max(win.screen.areas, key=lambda a: a.width * a.height)
    return win, area


def test_takeover_and_give_back():
    win, area = _graph_area()
    old = area.ui_type
    try:
        area.ui_type = 'FCURVES'
        space = area.spaces.active
        space.show_handles = True
        assert gh.feature_on(bpy.context), "on in Maya mode by default"
        gh.sync(bpy.context)
        assert gh.owns(space) and not space.show_handles and gh.shows_handles(space)
        # Maya View > Tangents
        with bpy.context.temp_override(window=win, area=area):
            wm = bpy.context.window_manager
            assert wm.allset_graph_tangents in {'ALWAYS', 'ACTIVE'}
            wm.allset_graph_tangents = 'NEVER'
            assert not gh.shows_handles(space) and not space.show_handles
            wm.allset_graph_tangents = 'ALWAYS'
            assert gh.shows_handles(space) and not space.use_only_selected_keyframe_handles
            wm.allset_graph_tangents = 'NEVER'
        # Blender's own Show Handles turned on = the kit value on
        space.show_handles = True
        gh.sync(bpy.context)
        assert gh.shows_handles(space) and not space.show_handles
        # the pref off gives the editor's value back
        prefs = prefs_mod.get(bpy.context)
        prefs.graph_fixed_tangents = False
        try:
            gh.sync(bpy.context)
            assert not gh.owns(space) and space.show_handles
        finally:
            prefs.graph_fixed_tangents = True
        gh.sync(bpy.context)
        space.show_handles = False
        gh.sync(bpy.context)
        gh._owned[space.as_pointer()] = False            # the user hid them while the kit draws
        # saving keeps the user's value in the file, the kit keeps drawing after
        gh._save_pre()
        assert space.show_handles is False and gh._state["saving"]
        gh._save_post()
        assert gh.owns(space) and not gh._state["saving"]
        gh._owned[space.as_pointer()] = True
        gh._save_pre()
        assert space.show_handles is True
        gh._save_post()
        assert space.show_handles is False
        # disable gives every editor its value back
        kit.disable()
        try:
            assert space.show_handles is True, "Show Handles restored on disable"
        finally:
            kit.enable()
        gh.sync(bpy.context)
        assert gh.owns(space)
        # Maya mode off too
        switch = import_module(kit.MODULE + ".switch")
        switch.set_mode(False, layout=False)
        try:
            assert space.show_handles is True, "Show Handles restored with Maya mode off"
        finally:
            switch.set_mode(True, layout=False)
    finally:
        area.ui_type = old


def test_keymap_items_go_first():
    patches = import_module(kit.MODULE + ".keymap.maya_patches")
    ic_data = import_module(kit.MODULE + ".keymap.ic_data")
    patch = import_module(kit.MODULE + ".keymap.patch")
    assert "allset.graph_handle_drag" in patches.PASS_THROUGH_FIRST
    assert "allset.graph_handle_box" in patches.PASS_THROUGH_FIRST
    kd = patch.KeyconfigData(patches.apply(ic_data.generate()))
    items = kd.items("Graph Editor")

    def first(type_, value, shift=False, ctrl=False):
        return next(it for it in items if it[1]["type"] == type_ and it[1].get("value") == value
                    and bool(it[1].get("shift")) == shift and bool(it[1].get("ctrl")) == ctrl
                    and not it[1].get("alt") and not it[1].get("any"))
    for shift, ctrl in ((False, False), (True, False), (False, True), (True, True)):
        assert first("LEFTMOUSE", "PRESS", shift, ctrl)[0] == "allset.graph_handle_drag", (shift, ctrl)
        assert first("LEFTMOUSE", "CLICK_DRAG", shift, ctrl)[0] == "allset.graph_handle_box", (shift, ctrl)
    assert first("MIDDLEMOUSE", "PRESS")[0] == "allset.graph_handle_drag"
