"""Visualize > Time Slider Bookmarks like Maya: Edit (the bookmark at the current time), Show Bookmarks, Bookmark
Manager (rows edited in place, Update / Frame / Delete, Frame all, the Add line), each bookmark's own colour on the Time
Slider ruler, and a bookmark keeping its end and colour when renamed."""

from importlib import import_module
from types import SimpleNamespace
from unittest.mock import patch

import bpy

import kit

bookmarks = import_module(kit.MODULE + ".operators.bookmarks")
manager = import_module(kit.MODULE + ".ui.bookmark_manager")
menu_map = import_module(kit.MODULE + ".ui.menu_map")
preferences = import_module(kit.MODULE + ".preferences")
ts = import_module(kit.MODULE + ".ui.time_slider")

PATH = "Visualize/Time Slider Bookmarks/"
RED = (0.8, 0.1, 0.1)
BLUE = (0.1, 0.2, 0.9)


def _scene():
    scene = bpy.context.scene
    scene.timeline_markers.clear()
    scene.pop(bookmarks.ENDS, None)
    scene.frame_start, scene.frame_end = 1, 120
    scene.use_preview_range = False
    bpy.context.window_manager.allset_time_range_on = False
    preferences.get().show_time_slider_bookmarks = True
    return scene


def _make(name, start, end, colour=RED):
    return bookmarks.create(bpy.context, name, start, end, colour)


def _close(a, b):
    return all(abs(x - y) < 1e-4 for x, y in zip(a, b))


def test_menu_items_are_wired():
    for item, target in (("Edit", "allset.bookmark_edit"), ("Bookmark Manager", "allset.bookmark_manager")):
        spec = menu_map.spec(PATH + item)
        assert spec is not None and spec[1] == target, (item, spec)
    spec = menu_map.spec(PATH + "Show Bookmarks")
    assert spec is not None and spec[0] == "prop" and spec[1] == "addon_prefs.show_time_slider_bookmarks", spec
    assert preferences.get().bl_rna.properties["show_time_slider_bookmarks"].default is True, "on by default"


def test_create_covers_the_range_or_the_current_frame_with_a_colour():
    scene = _scene()
    scene.frame_current = 40
    assert bpy.ops.allset.bookmark_create(quick=True) == {'FINISHED'}
    m = scene.timeline_markers[0]
    assert bookmarks.bookmark_range(scene, m) == (40, 40), "no selected range: the current frame only"
    palette = [bookmarks.rgb(c) for c in bookmarks.PALETTE]
    assert any(_close(bookmarks.color(m), c) for c in palette), bookmarks.color(m)
    wm = bpy.context.window_manager
    wm.allset_time_range, wm.allset_time_range_on = (10, 30), True
    assert bpy.ops.allset.bookmark_create(quick=True) == {'FINISHED'}
    assert scene.frame_current == 30, "the time moves to the new bookmark's end"
    wm.allset_time_range_on = False
    assert bpy.ops.allset.bookmark_create('EXEC_DEFAULT', name="run", start=70, end=60, color=BLUE) == {'FINISHED'}
    run = scene.timeline_markers["run"]
    assert bookmarks.bookmark_range(scene, run) == (60, 70) and _close(bookmarks.color(run), BLUE)


def test_edit_changes_the_bookmark_at_the_current_time():
    scene = _scene()
    a = _make("bookmark1", 10, 20)
    _make("bookmark2", 40, 50, BLUE)
    scene.frame_current = 15
    assert bpy.ops.allset.bookmark_edit('EXEC_DEFAULT', name="walk", start=30, end=5, color=BLUE) == {'FINISHED'}
    assert a.name == "walk" and bookmarks.bookmark_range(scene, a) == (5, 30), "start > end swaps like Maya"
    assert _close(bookmarks.color(a), BLUE)
    scene.frame_current = 35
    assert bpy.ops.allset.bookmark_edit('EXEC_DEFAULT', name="x") == {'CANCELLED'}, "no bookmark at frame 35"
    assert [m.name for m in bookmarks.markers(scene)] == ["walk", "bookmark2"]


def test_rename_keeps_end_and_colour_and_old_files_keep_their_ends():
    scene = _scene()
    m = _make("bookmark1", 10, 25, BLUE)
    m.name = "renamed"
    assert bookmarks.bookmark_range(scene, m) == (10, 25) and _close(bookmarks.color(m), BLUE)
    old = scene.timeline_markers.new("old", frame=60)
    scene[bookmarks.ENDS] = {"old": 80}
    assert bookmarks.bookmark_range(scene, old) == (60, 80), "an older file's kept end"
    bare = scene.timeline_markers.new("bare", frame=100)
    assert bookmarks.bookmark_range(scene, bare) == (100, 120), "a plain marker: up to the scene end"


def test_end_field_and_frame_like_maya():
    scene = _scene()
    a = _make("a", 10, 20)
    b = _make("b", 40, 50)
    a.allset_end = 4                       # the Manager's End field before the start: swapped
    assert bookmarks.bookmark_range(scene, a) == (4, 10)
    a.allset_end = 20
    a.frame = 10
    scene.frame_current = 15
    assert bpy.ops.allset.bookmark_frame(which='CURRENT') == {'FINISHED'}
    assert (scene.frame_preview_start, scene.frame_preview_end) == (10, 20) and scene.frame_current == 15, \
        "a current time inside the bookmark stays"
    scene.frame_current = 60
    assert bpy.ops.allset.bookmark_frame(which='NEXT') == {'FINISHED'}
    assert scene.frame_current == 10, "past the last bookmark: Next wraps round to the first"
    assert bpy.ops.allset.bookmark_frame(which='ALL') == {'FINISHED'}
    assert (scene.frame_preview_start, scene.frame_preview_end) == (10, 50)
    assert bpy.ops.allset.bookmark_frame(bookmark="b") == {'FINISHED'}
    assert (scene.frame_preview_start, scene.frame_preview_end) == (40, 50)
    scene.use_preview_range = False


def test_manager_row_buttons_and_add_line():
    scene = _scene()
    wm = bpy.context.window_manager
    _make("a", 10, 20)
    wm.allset_time_range, wm.allset_time_range_on = (30, 36), True
    assert bpy.ops.allset.bookmark_update(bookmark="a") == {'FINISHED'}
    assert bookmarks.bookmark_range(scene, scene.timeline_markers["a"]) == (30, 36)
    wm.allset_time_range_on = False
    scene.frame_current = 70
    wm.allset_bm_new_name, wm.allset_bm_new_start, wm.allset_bm_new_end = "", "", ""
    wm.allset_bm_new_color = BLUE
    assert bpy.ops.allset.bookmark_add_line() == {'FINISHED'}
    new = [m for m in scene.timeline_markers if m.name != "a"][0]
    assert bookmarks.bookmark_range(scene, new) == (70, 70) and _close(bookmarks.color(new), BLUE)
    wm.allset_bm_new_name, wm.allset_bm_new_start, wm.allset_bm_new_end = "fight", "80", "95"
    assert bpy.ops.allset.bookmark_add_line() == {'FINISHED'}
    assert bookmarks.bookmark_range(scene, scene.timeline_markers["fight"]) == (80, 95)
    wm.allset_bm_new_start = "abc"
    assert bpy.ops.allset.bookmark_add_line() == {'CANCELLED'}
    assert [m.name for m in manager.rows(scene)] == ["a", new.name, "fight"]
    assert bpy.ops.allset.bookmark_delete(bookmark="a") == {'FINISHED'}
    assert "a" not in scene.timeline_markers


class _Layout:
    """Records the properties a panel draws."""
    def __init__(self, log):
        self.log = log
        self.ui_units_x = 0
        self.enabled = True

    def prop(self, data, name, **kw):
        assert hasattr(data, name), name
        self.log.append((getattr(data, "name", None) if data.__class__.__name__ == "TimelineMarker" else None, name))

    def operator(self, idname, **kw):
        self.log.append((None, idname))
        return SimpleNamespace()

    def __getattr__(self, name):
        return lambda *a, **k: _Layout(self.log)


def test_manager_draws_one_row_per_bookmark_in_start_order():
    scene = _scene()
    _make("late", 50, 60)
    _make("early", 5, 9)
    log = []
    manager.draw(_Layout(log), bpy.context)
    names = [n for n, p in log if p == "name" and n]
    assert names == ["early", "late"], names
    for field in ("allset_color", "frame", "allset_end"):
        assert sum(1 for n, p in log if p == field and n) == 2, field
    assert ("allset_bm_new_name" in {p for _n, p in log}) and ("show_time_slider_bookmarks" in {p for _n, p in log})


def _ruler_colours():
    import blf
    import gpu
    import gpu_extras.batch

    class View:
        def view_to_region(self, x, y, clip=False):
            return (x * 4, y)

        def region_to_view(self, x, y):
            return (x / 4, y)
    colours = []

    class Shader:
        def uniform_float(self, name, value):
            colours.append(tuple(round(v, 3) for v in value))
    context = SimpleNamespace(scene=bpy.context.scene, preferences=bpy.context.preferences,
                              window_manager=bpy.context.window_manager)
    batch = SimpleNamespace(draw=lambda shader: None)
    with patch.object(gpu.shader, "from_builtin", return_value=Shader()), patch.object(gpu.state, "blend_set"), \
            patch.object(gpu_extras.batch, "batch_for_shader", return_value=batch), \
            patch.object(blf, "size"), patch.object(blf, "color"), patch.object(blf, "position"), \
            patch.object(blf, "draw"):
        ts._draw_ruler(context, SimpleNamespace(width=800, height=32, view2d=View()))
    return colours


def test_ruler_draws_each_colour_and_show_bookmarks_hides_them():
    _scene()
    _make("a", 10, 20, RED)
    _make("b", 40, 50, BLUE)
    drawn = _ruler_colours()
    for c in (RED, BLUE):
        assert (*[round(v, 3) for v in c], 0.8) in drawn and (*[round(v, 3) for v in c], 1.0) in drawn, (c, drawn)
    assert bookmarks.shown(bpy.context)
    preferences.get().show_time_slider_bookmarks = False
    try:
        assert bookmarks.shown(bpy.context) == []
        drawn = _ruler_colours()
        assert not any(c[:3] == tuple(round(v, 3) for v in RED) for c in drawn), drawn
    finally:
        preferences.get().show_time_slider_bookmarks = True
