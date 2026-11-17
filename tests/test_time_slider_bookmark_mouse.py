"""Time Slider bookmarks like Maya: Next / Previous Bookmark move the current time to the start of the next / previous
bookmark and wrap round; on the Time Slider's bookmark strip the mouse over a bookmark shows its name and range, a
right-click opens the bookmark menu whose actions work at the frame under the mouse, a click on a bookmark leaves the
time where it is; Ctrl + drag moves a bookmark or one of its ends."""

from importlib import import_module
from types import SimpleNamespace

import bpy

import kit

bookmarks = import_module(kit.MODULE + ".operators.bookmarks")
menu_map = import_module(kit.MODULE + ".ui.menu_map")
mapping = import_module(kit.MODULE + ".keymap.mapping")

PATH = "Visualize/Time Slider Bookmarks/"


def _scene():
    scene = bpy.context.scene
    scene.timeline_markers.clear()
    scene.pop(bookmarks.ENDS, None)
    scene.frame_start, scene.frame_end = 1, 120
    scene.use_preview_range = False
    bpy.context.window_manager.allset_time_range_on = False
    return scene


def _go(previous=False):
    return bpy.ops.allset.bookmark_go(previous=previous)


def test_next_and_previous_bookmark_wrap_round():
    scene = _scene()
    scene.frame_current = 1
    assert _go() == {'CANCELLED'}, "no bookmark: nothing to go to"
    bookmarks.create(bpy.context, "alpha", 20, 40)
    bookmarks.create(bpy.context, "beta", 60, 70)
    for start, previous, want in ((1, False, 20), (20, False, 60), (30, False, 60), (60, False, 20),
                                  (90, False, 20), (1, True, 60), (20, True, 60), (30, True, 20), (60, True, 20),
                                  (65, True, 60), (90, True, 60)):
        scene.frame_current = start
        assert _go(previous) == {'FINISHED'}
        assert scene.frame_current == want, (start, previous, scene.frame_current, want)
    assert not scene.use_preview_range, "the playback range stays"


def test_next_and_previous_bookmark_are_wired():
    for item, props in (("Next Bookmark", {}), ("Previous Bookmark", {"previous": True})):
        spec = menu_map.spec(PATH + item)
        assert spec is not None and spec[1] == "allset.bookmark_go", (item, spec)
        assert spec[2] == props, (item, spec)
    for name, props in (("NextTimeSliderBookmark", {}), ("PreviousTimeSliderBookmark", {"previous": True})):
        row = mapping.ENTRIES[name]
        assert "allset.bookmark_go" in repr(row) and repr(props)[1:-1] in repr(row), (name, row)
    km = kit.maya_kc().keymaps["Screen"]
    got = {(i.type, i.properties.previous) for i in km.keymap_items if i.idname == "allset.bookmark_go"}
    assert got == {('QUOTE', False), ('SEMI_COLON', True)}, got


# --- the bookmark strip on the Time Slider ---------------------------------------------------------------------

tsb = import_module(kit.MODULE + ".ui.time_slider_bookmarks")
tsm = import_module(kit.MODULE + ".ui.time_slider_menu")

STRIP_MENU = ["Create", "Edit", "Next Bookmark", "Previous Bookmark", "Frame Bookmark", "Frame Previous Bookmark",
             "Frame Next Bookmark", "Unframe", "Update Bookmark with selection", "Delete", "|", "Bookmark Manager"]


class _Layout:
    """Records what a menu draws: (text, operator id, props)."""

    def __init__(self):
        self.rows = []

    def operator(self, idname, text=""):
        props = SimpleNamespace()
        self.rows.append((text, idname, props))
        return props

    def separator(self):
        self.rows.append(("|", None, None))


def test_strip_zone_rule():
    strip, bar = (23, 31), (27, 31)
    assert tsb.strip_zone(29, strip, bar, True) == 'BAR'
    assert tsb.strip_zone(29, strip, bar, False) == 'STRIP', "no bookmark there: the strip"
    assert tsb.strip_zone(24, strip, bar, True) == 'STRIP', "under the coloured bar"
    assert tsb.strip_zone(10, strip, bar, True) is None, "the ruler below the strip"


def test_hover_shows_name_and_range():
    scene = _scene()
    m = bookmarks.create(bpy.context, "alpha", 20, 40)
    assert tsb.tip_text(scene, m) == "alpha  20 - 40"


def test_strip_menu_is_mayas_and_acts_at_the_mouse_frame():
    _scene()
    tsb._menu_at["frame"] = 30
    lay = _Layout()
    tsb.ALLSET_MT_time_slider_bookmarks.draw(SimpleNamespace(layout=lay), bpy.context)
    assert [r[0] for r in lay.rows] == STRIP_MENU, [r[0] for r in lay.rows]
    at = {r[0]: r[2] for r in lay.rows if r[2] is not None and getattr(r[2], "use_at_frame", False)}
    assert set(at) == {"Edit", "Next Bookmark", "Previous Bookmark", "Frame Bookmark", "Frame Previous Bookmark",
                       "Frame Next Bookmark", "Update Bookmark with selection", "Delete"}, sorted(at)
    assert all(p.at_frame == 30 for p in at.values())
    tsb._menu_at.clear()


def test_strip_menu_items_use_the_frame_not_the_current_time():
    scene = _scene()
    bookmarks.create(bpy.context, "alpha", 20, 40)
    bookmarks.create(bpy.context, "beta", 60, 70)
    scene.frame_current = 5
    assert bpy.ops.allset.bookmark_frame(which='CURRENT', use_at_frame=True, at_frame=30) == {'FINISHED'}
    assert (scene.frame_preview_start, scene.frame_preview_end, scene.frame_current) == (20, 40, 20)
    scene.use_preview_range = False
    scene.frame_current = 5
    assert bpy.ops.allset.bookmark_frame(which='NEXT', use_at_frame=True, at_frame=30) == {'FINISHED'}
    assert (scene.frame_preview_start, scene.frame_preview_end, scene.frame_current) == (60, 70, 60)
    scene.use_preview_range = False
    scene.frame_current = 5
    assert bpy.ops.allset.bookmark_go(previous=True, use_at_frame=True, at_frame=30) == {'FINISHED'}
    assert scene.frame_current == 20, "previous from frame 30, not from the current time 5"
    scene.frame_current = 5
    wm = bpy.context.window_manager
    wm.allset_time_range, wm.allset_time_range_on = (44, 54), True
    assert bpy.ops.allset.bookmark_update(use_at_frame=True, at_frame=30) == {'FINISHED'}
    assert bookmarks.bookmark_range(scene, scene.timeline_markers["alpha"]) == (44, 54)
    wm.allset_time_range_on = False
    scene.frame_current = 5
    assert bpy.ops.allset.bookmark_delete(use_at_frame=True, at_frame=65) == {'FINISHED'}
    assert [m.name for m in scene.timeline_markers] == ["alpha"], "the bookmark under the mouse went"
    assert bpy.ops.allset.bookmark_delete() == {'CANCELLED'}, "none at the current time 5"


def test_strip_keymap_items():
    """The Time Slider's right-click asks the strip first; the bookmark clicks run before the scrub."""
    import inspect
    assert "time_slider_bookmarks.open_menu" in inspect.getsource(tsm.ALLSET_OT_time_slider_menu.invoke)
    km = kit.maya_kc().keymaps["Time Scrub"]
    ids = [(i.idname, i.type, i.value, bool(i.ctrl), bool(i.shift)) for i in km.keymap_items if i.active]
    clicks = [i for i in ids if i[0] == "allset.time_slider_bookmark_click"]
    assert {c[1:] for c in clicks} == {('LEFTMOUSE', 'PRESS', False, False), ('LEFTMOUSE', 'PRESS', False, True),
                                       ('LEFTMOUSE', 'PRESS', True, False),
                                       ('LEFTMOUSE', 'DOUBLE_CLICK', True, False)}, clicks
    first_scrub = next(n for n, i in enumerate(ids) if i[0] == "allset.time_scrub")
    assert all(ids.index(c) < first_scrub for c in clicks), "in front of the scrub"
    assert any(i[0] == "allset.time_slider_bookmark_hover" and i[1] == 'MOUSEMOVE' for i in ids)


def test_ctrl_drag_zone_rule():
    """Like Maya: on a 20-frame bookmark 20..40 a Ctrl + drag pressed in about its first two and a half frames takes
    the start, in its last frame before the end line the end, between them the whole bookmark; past the end line
    (the rest of its last frame) nothing; the zones follow the length (10 frames: half as wide)."""
    z = tsb.drag_zone
    for t, want in ((20.06, 'START'), (21.5, 'START'), (22.2, 'START'), (22.6, 'MOVE'), (30.5, 'MOVE'),
                    (38.5, 'MOVE'), (38.8, 'MOVE'), (39.15, 'END'), (39.7, 'END'), (40.0, 'END'), (40.1, 'END'),
                    (40.19, None), (40.8, None), (19.8, None), (41.2, None)):
        assert z(t, 20, 40, past=0.13) == want, (t, z(t, 20, 40, past=0.13), want)
    for t, want in ((80.6, 'START'), (81.0, 'START'), (81.4, 'MOVE'), (89.4, 'MOVE'), (89.6, 'END')):
        assert z(t, 80, 90) == want, (t, z(t, 80, 90), want)
    assert z(5.5, 5, 6) == 'MOVE', "a short bookmark only moves"


def test_ctrl_drag_result_rule():
    d = tsb.dragged
    assert d('MOVE', 20, 40, 10) == (30, 50) and d('MOVE', 20, 40, -25) == (-5, 15)
    assert d('START', 20, 40, -5) == (15, 40) and d('START', 20, 40, 3) == (23, 40)
    assert d('START', 20, 40, 30) == (39, 40), "the start stops a frame before the end"
    assert d('END', 20, 40, 5) == (20, 45) and d('END', 20, 40, -30) == (20, 21)
    assert d(None, 20, 40, 7) == (20, 40)


def test_ctrl_drag_keymap_item():
    """The Ctrl + drag item runs before the Ctrl click item (a second press, the Ctrl + double-click, passes on)."""
    km = kit.maya_kc().keymaps["Time Scrub"]
    ids = [(i.idname, i.type, i.value, bool(i.ctrl)) for i in km.keymap_items if i.active]
    drag = ("allset.time_slider_bookmark_drag", 'LEFTMOUSE', 'PRESS', True)
    click = ("allset.time_slider_bookmark_click", 'LEFTMOUSE', 'PRESS', True)
    assert drag in ids and ids.index(drag) < ids.index(click), ids


def test_tip_is_drawn_outside_the_kept_ruler_draw():
    """The hovered bookmark's name box and end lines are drawn anew at every draw, outside the kept ruler calls (a
    kept call list never holds them). While a window is dragged or resized (the ruler drawn again from its kept
    calls) the mouse holds the window's frame, off the Time Slider: the name goes, like Maya."""
    ts = import_module(kit.MODULE + ".ui.time_slider")
    replay = import_module(kit.MODULE + ".ui.draw_replay")
    region = SimpleNamespace(width=800, height=32, as_pointer=lambda: 1234, type='WINDOW')
    area = SimpleNamespace(as_pointer=lambda: 4321)
    fake = SimpleNamespace(window_manager=bpy.context.window_manager, region=region, area=area, space_data=None,
                           preferences=bpy.context.preferences)
    seen = []
    saved = {n: getattr(ts, n) for n in ("_is_timeline", "_check_view", "_redo_panel_shown", "_draw_slider",
                                        "has_slider_panel")}
    saved_tip, saved_again = tsb.draw_tip, replay.again
    try:
        ts._is_timeline = lambda c: True
        ts._check_view = lambda c, r: None
        ts._redo_panel_shown = lambda c: False
        ts.has_slider_panel = lambda sp: True
        ts._draw_slider = lambda c, r, wm: seen.append(("slider", len(replay._lists)))
        tsb.draw_tip = lambda c, r: seen.append(("tip", len(replay._lists)))
        ts.bpy = SimpleNamespace(context=fake, app=bpy.app, types=bpy.types, props=bpy.props)
        tsb._hover[4321] = ("alpha", 10)
        replay.again = lambda key, sig: False
        ts._draw_range()
        assert tsb._hover, "a plain draw keeps the name"
        replay.again = lambda key, sig: True
        ts._draw_range()
    finally:
        for n, v in saved.items():
            setattr(ts, n, v)
        tsb.draw_tip, replay.again = saved_tip, saved_again
        ts.bpy = bpy
        left = dict(tsb._hover)
        tsb._hover.clear()
    assert seen == [("slider", 1), ("tip", 0)], seen
    assert not left, "a window drag drops the name"
