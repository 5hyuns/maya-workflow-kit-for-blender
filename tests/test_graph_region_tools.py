"""Graph Editor tools like Maya: the Region Keys tool (a marquee leaves its region as a box that scales / moves the keys
inside), Select > Pre-Select Highlight (the curve under the mouse drawn brighter), Select > Prefer Selected Curves
(clicks and marquees pick the keys of the curves with selected keys first) and the Dope Sheet's Channels > Offset Keys
(the selected keys move by a number of frames)."""

from importlib import import_module

import bpy

import kit
from test_remove_keys import Editor, _fc, _scene, _select, _times

menu_map = import_module(kit.MODULE + ".ui.editor_menu_map")
notices = import_module(kit.MODULE + ".ui.notices")
icon_data = import_module(kit.MODULE + ".ui.editor_icon_data")
gr = import_module(kit.MODULE + ".operators.graph_region")
gh = import_module(kit.MODULE + ".operators.graph_hover")
sb = import_module(kit.MODULE + ".operators.graph_scale_box")
select_2d = import_module(kit.MODULE + ".operators.select_2d")
preferences = import_module(kit.MODULE + ".preferences")

GE, DS = "Graph Editor", "Dope Sheet"
ITEMS = {f"{GE}/Edit/Transformation Tools/Region Keys Tool": ("prop", "window_manager.allset_graph_key_tool",
                                                              {"value": 'REGION'}),
         f"{GE}/Select/Pre-Select Highlight": ("prop", "addon_prefs.graph_preselect"),
         f"{GE}/Select/Prefer Selected Curves": ("prop", "addon_prefs.graph_prefer_selected"),
         f"{DS}/Channels/Offset Keys": "allset.offset_curves"}


def test_menu_items_and_toolbar_button():
    for path, action in ITEMS.items():
        got = menu_map.MAP.get(path)
        assert got is not None, f"{path} is not wired"
        assert got[:len(action)] == action if isinstance(action, tuple) else got == action, (path, got)
        assert path not in notices.NOTICES, f"{path} still has its greyed notice"
    row = {it[0]: it for it in icon_data.GRAPH_ICONS if isinstance(it, tuple)}
    assert row["key_region_tool"][2] == ("prop", "window_manager.allset_graph_key_tool", {"value": 'REGION'})


def test_check_items_are_off_like_maya():
    p = preferences.get()
    assert p.graph_preselect is False and p.graph_prefer_selected is False


def test_keymap_items_run_before_blenders_click_and_marquee():
    km = kit.maya_kc().keymaps["Graph Editor"]
    items = [i for i in km.keymap_items if i.active]

    def ids(value, shift=False, ctrl=False):
        return [i.idname for i in items if i.type == 'LEFTMOUSE' and i.value == value and
                (i.any or (bool(i.shift) == shift and bool(i.ctrl) == ctrl and not i.alt))]
    for shift, ctrl in ((False, False), (True, False), (False, True), (True, True)):
        press = ids('PRESS', shift, ctrl)
        assert "allset.graph_prefer_click" in press, press
        assert press.index("allset.graph_prefer_click") < press.index("graph.clickselect"), press
        drag = ids('CLICK_DRAG', shift, ctrl)
        assert drag.index("allset.graph_marquee_watch") < drag.index("graph.select_box"), drag
    assert any(i.idname == "allset.graph_hover" and i.type == 'MOUSEMOVE' for i in items)


# --- Prefer Selected Curves ---------------------------------------------------------------------------------------

def test_prefer_pick_rule():
    # (distance, on a preferred curve, key)
    assert gr.prefer_pick([(3, False, "other"), (7, True, "mine")], 10) == "mine", "a preferred key wins"
    assert gr.prefer_pick([(2, True, "mine"), (1, True, "mine2")], 10) is None, "only preferred keys: own pick"
    assert gr.prefer_pick([(2, True, "mine"), (4, False, "other")], 10) == "mine", "the first curve is not taken"
    assert gr.prefer_pick([(3, False, "other")], 10) is None, "no preferred key: own pick"
    assert gr.prefer_pick([(3, False, "other"), (12, True, "mine")], 10) is None, "out of reach: own pick"
    assert gr.prefer_pick([], 10) is None
    assert gr.caught_keys('SET', {1}, {2, 3}) == {2, 3}
    assert gr.caught_keys('ADD', {1}, {1, 2}) == {2}
    assert gr.caught_keys('SUB', {1}, set()) == set()
    a, b = (100, 0), (200, 0)
    assert gr.prefer_drop({a, b}, {100}) == {b}, "the other curve's caught keys are dropped"
    assert gr.prefer_drop({b}, {100}) == set(), "caught nothing of the preferred curves: as usual"


def test_prefer_marquee_drops_the_other_curves_keys():
    a, b = _scene()
    _select(a, (2,))
    p = preferences.get()
    p.graph_prefer_selected = True
    try:
        with Editor() as ed:
            ctx = bpy.context
            preferred = gr.preferred_curves(ctx)
            assert preferred == {_fc(a).as_pointer()}, "only A's X curve has a selected key"
            before = select_2d.key_state()
            # the marquee caught A's X keys at 5 and 6 and B's key at 5 (Blender's box select, Set)
            for kp in _fc(a).keyframe_points:
                kp.select_control_point = kp.co.x in (5.0, 6.0)
            for kp in _fc(b).keyframe_points:
                kp.select_control_point = kp.co.x == 5.0
            gr.finish_marquee(ctx, {"preferred": preferred, "before": before, "region": False}, 'SET',
                              (0, 0, 10, 10))
            assert ed
    finally:
        p.graph_prefer_selected = False
    assert [kp.co.x for kp in _fc(a).keyframe_points if kp.select_control_point] == [5.0, 6.0]
    assert not any(kp.select_control_point for kp in _fc(b).keyframe_points), "B's key is left unselected"


def test_prefer_click_takes_the_selected_curves_key():
    a, b = _scene()
    _select(a, (2,))
    with Editor():
        ctx = bpy.context
        fa, fb = _fc(a), _fc(b)
        i = next(n for n, kp in enumerate(fa.keyframe_points) if kp.co.x == 1.0)
        gr.apply_click(ctx, fa, i, 'SET')
        assert [kp.co.x for kp in fa.keyframe_points if kp.select_control_point] == [1.0], "only the clicked key"
        assert not any(kp.select_control_point for kp in fb.keyframe_points)
        gr.apply_click(ctx, fa, 0, 'TOGGLE')
        assert not fa.keyframe_points[0].select_control_point, "Shift toggles it off"
        gr.apply_click(ctx, fa, 2, 'ADD')
        assert fa.keyframe_points[2].select_control_point


# --- Region Keys tool ---------------------------------------------------------------------------------------------

def test_region_rules():
    assert gr.region_moved((0, 0, 10, 4), 2, -1) == (2, -1, 12, 3)
    assert gr.region_scaled((0, 0, 10, 4), (0, 0), 1.5, 1.0) == (0, 0, 15, 4), "right side out, left side stays"
    assert gr.region_scaled((0, 0, 10, 4), (10, 4), -1.0, 1.0) == (10, 0, 20, 4), "flipped: still ordered"


def test_region_box_is_the_marquee_while_the_keys_stay():
    a, _b = _scene()
    wm = bpy.context.window_manager
    wm.allset_graph_key_tool = 'REGION'
    try:
        with Editor():
            ctx = bpy.context
            _select(a, (5, 6))
            region = ctx.region
            v2d = region.view2d
            # a marquee from frame 4 to 7 and value -1 to 10 (region pixels from the view)
            x0, y0 = v2d.view_to_region(4.0, -1.0, clip=False)
            x1, y1 = v2d.view_to_region(7.0, 10.0, clip=False)
            gr.finish_marquee(ctx, {"region": True}, 'SET', (x0, y0, x1, y1))
            view = gr.region_of(ctx)
            assert view is not None
            want = (*v2d.region_to_view(x0, y0), *v2d.region_to_view(x1, y1))
            assert all(abs(a - b) < 1e-3 for a, b in zip(view, want)), (view, want)
            assert view[0] < 5.0 and view[2] > 6.0, "wider than the keys inside it"
            boxes = sb.current_boxes(ctx)
            assert boxes is not None and boxes[1] == view, "the box is the marquee's region, not the keys' box"
            # another selection: the box is the selected keys' own box again
            _select(a, (8,))
            assert gr.region_of(ctx) is None
            assert sb.current_boxes(ctx)[1][0] == 5.0, "keys 5, 6, 8"
            wm.allset_graph_key_tool = 'MOVE'
            assert sb.current_boxes(ctx) is None, "no box with the Move tool"
    finally:
        wm.allset_graph_key_tool = 'MOVE'
        gr.clear()


def test_region_tool_shows_its_box_with_the_scale_box_pref_off():
    wm = bpy.context.window_manager
    p = preferences.get()
    p.graph_scale_manipulator = False
    try:
        wm.allset_graph_key_tool = 'REGION'
        assert sb.enabled(bpy.context), "the Region Keys tool is the box"
        wm.allset_graph_key_tool = 'SCALE'
        assert not sb.enabled(bpy.context)
    finally:
        p.graph_scale_manipulator = True
        wm.allset_graph_key_tool = 'MOVE'


def test_region_tool_from_the_menu_item():
    wm = bpy.context.window_manager
    with Editor():
        assert bpy.ops.allset.graph_key_tool(tool='REGION') == {'FINISHED'}
    assert wm.allset_graph_key_tool == 'REGION'
    wm.allset_graph_key_tool = 'MOVE'


# --- Pre-Select Highlight -----------------------------------------------------------------------------------------

def test_hover_rules():
    assert gh.segment_distance((5, 3), (0, 0), (10, 0)) == 3
    assert gh.segment_distance((-4, 3), (0, 0), (10, 0)) == 5, "past the end: distance to the end point"
    lines = {"a": [(0, 0), (10, 0)], "b": [(0, 4), (10, 4)]}
    assert gh.nearest_curve((5, 1), lines, 6) == "a"
    assert gh.nearest_curve((5, 3), lines, 6) == "b"
    assert gh.nearest_curve((5, 20), lines, 6) is None
    assert gh.lighter((0.0, 0.5, 1.0), 0.5) == (0.5, 0.75, 1.0)
    # like Maya the mouse must be on the line: about 2 px off it still picks, 3 px off no longer
    flat = {"a": [(0, 0), (10, 0)]}
    assert gh.nearest_curve((5, 2), flat, gh.HOVER_PX) == "a"
    assert gh.nearest_curve((5, 3), flat, gh.HOVER_PX) is None


def test_hover_picks_the_curve_under_the_mouse():
    a, b = _scene()
    with Editor():
        ctx = bpy.context
        v2d = ctx.region.view2d
        # A's X: frame 5 = value 3, B's X: frame 5 = value 5 (absolute view)
        ctx.space_data.use_normalization = False
        x, y = v2d.view_to_region(5.0, 3.0, clip=False)
        assert gh.pick(ctx, x, y) == _fc(a).as_pointer()
        x, y = v2d.view_to_region(5.0, 5.0, clip=False)
        assert gh.pick(ctx, x, y) in (_fc(b).as_pointer(), _fc(a, 1).as_pointer()), "B's X and A's Y meet here"


def test_hover_stays_when_the_mouse_leaves_the_curve_view():
    """Like Maya: a move outside the Graph Editor's curve view (its channel list, another area) keeps the highlight
    (the next move over the curve view decides again); the "Window" item only drops the Time Slider's bookmark
    name."""
    from types import SimpleNamespace
    km = kit.maya_kc().keymaps["Window"]
    assert any(i.idname == "allset.hover_leave" and i.type == 'MOUSEMOVE' and i.active
               for i in km.keymap_items), "a Window keymap item sees moves over every area"
    assert gh.inside(5, 5, (0, 0, 10, 10)) and not gh.inside(10, 5, (0, 0, 10, 10))
    tsb = import_module(kit.MODULE + ".ui.time_slider_bookmarks")
    wm = bpy.context.window_manager
    window = wm.windows[0]
    area = max(window.screen.areas, key=lambda a: a.width * a.height)
    region = next(r for r in area.regions if r.type == 'WINDOW')
    try:
        gh._hover[area.as_pointer()] = 1
        tsb._hover[area.as_pointer()] = ("alpha", 0)
        outside = SimpleNamespace(mouse_x=region.x - 1, mouse_y=region.y + region.height // 2)
        with bpy.context.temp_override(window=window, area=area, region=region):
            gh.ALLSET_OT_hover_leave.invoke(None, bpy.context, outside)
        assert gh._hover == {area.as_pointer(): 1}, "the curve stays highlighted"
        assert not tsb._hover, "the bookmark name goes"
    finally:
        gh._hover.clear()
        tsb._hover.clear()


def test_a_drag_drops_the_highlight():
    """Maya shows no pre-selection highlight while a drag runs in the curve view: a left-button drag start and a
    middle-button press (any modifiers) drop it in front of the Graph Editor's own items; it passes them on."""
    km = kit.maya_kc().keymaps["Graph Editor"]
    items = [i for i in km.keymap_items if i.active]
    drops = [(i.type, i.value, i.any) for i in items if i.idname == "allset.graph_hover_drop"]
    assert sorted(drops) == [('LEFTMOUSE', 'CLICK_DRAG', True), ('MIDDLEMOUSE', 'PRESS', True)], drops
    first_other = next(n for n, i in enumerate(items) if i.type in {'LEFTMOUSE', 'MIDDLEMOUSE'}
                       and i.idname != "allset.graph_hover_drop" and i.idname != "allset.graph_marquee_watch")
    assert all(n < first_other for n, i in enumerate(items) if i.idname == "allset.graph_hover_drop")
    wm = bpy.context.window_manager
    area = max(wm.windows[0].screen.areas, key=lambda a: a.width * a.height)
    try:
        gh._hover[area.as_pointer()] = 1
        with bpy.context.temp_override(window=wm.windows[0], area=area):
            assert gh.ALLSET_OT_graph_hover_drop.invoke(None, bpy.context, None) == {'PASS_THROUGH'}
        assert not gh._hover
    finally:
        gh._hover.clear()


# --- Dope Sheet Offset Keys ---------------------------------------------------------------------------------------

def test_dope_sheet_offset_keys_moves_the_selected_keys():
    a, b = _scene()
    _select(a, (5, 6, 8))
    with Editor('DOPESHEET'):
        assert bpy.ops.allset.offset_curves() == {'FINISHED'}
    assert _times(a) == [1, 2, 3.5, 6, 7, 9, 10], "one frame later (default 1)"
    assert _times(b) == [1, 2.5, 5, 7, 10], "unselected keys stay"
