"""#319 follow-up: the Time Slider shows exactly the playback range (no zoom / scroll), the Range Slider row fits a
short timeline (no header scrollbar), the playback fields always show the range that plays, a one-frame range
still draws two handles, the layer list row's right-click gets Maya's layer menu, and the Playblast player /
Save to File helpers."""

import os
import sys
import types
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import MODULE  # noqa: E402

ts = import_module(f"{MODULE}.ui.time_slider")
rb = import_module(f"{MODULE}.ui.range_bar")
le = import_module(f"{MODULE}.ui.layer_editor")
pb = import_module(f"{MODULE}.operators.playblast")
mp = import_module(f"{MODULE}.keymap.maya_patches")


class Recorder:
    def __init__(self):
        self.items = []

    def label(self, text="", icon=None, **kw):
        self.items.append(("label", text))

    def operator(self, idname, text="", **kw):
        self.items.append(("op", text))
        return types.SimpleNamespace()

    def separator(self, **kw):
        self.items.append(("sep", ""))

    def texts(self):
        return [t for k, t in self.items if k == "op"]


# --- Time Slider view = playback range -----------------------------------------------------------------

def test_view_target_is_the_frame_cells():
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, 120
    sc.use_preview_range = False
    assert ts.view_target(sc) == (0.5, 120.5)
    rb.set_playback(sc, 10, 50)
    assert ts.view_target(sc) == (9.5, 50.5)
    sc.use_preview_range = False


def test_view_drifted_rules():
    target, size = (9.5, 50.5), (1600, 30)
    assert ts.view_drifted(None, target, (9.5, 50.5), size)                       # never fitted
    rec = (9.5, 50.5, 9.51, 50.49, 1600, 30)
    assert not ts.view_drifted(rec, target, (9.51, 50.49), size)                 # exactly what the fit reached
    assert not ts.view_drifted(rec, target, (9.512, 50.49), size)                # within a pixel (39 px / frame)
    assert ts.view_drifted(rec, target, (11.0, 49.0), size)                      # a wheel zoom
    assert ts.view_drifted(rec, (9.5, 60.5), (9.51, 50.49), size)                # another range
    assert ts.view_drifted(rec, target, (9.51, 50.49), (1200, 30))               # a resize
    # a fit that could not reach the target (zoom limits) is not retried while the view stays put
    rec2 = (0.5, 2.5, -3.0, 6.0, 1600, 30)
    assert not ts.view_drifted(rec2, (0.5, 2.5), (-3.0, 6.0), size)


def test_fit_timelines_records_and_runs_headless():
    # -b still has the startup window with its Timeline: the fit runs there (Frame Scene Range when the region
    # has no size) and records it
    n = ts.fit_timelines()
    assert n >= 1
    assert ts._fitted, "fit recorded"
    rec = next(iter(ts._fitted.values()))
    assert len(rec) == 6 and rec[0] < rec[1]


def test_view_lock_operator_and_keymap():
    assert "allset.time_view_lock" in mp.PASS_THROUGH_FIRST
    locks = [(km, ev) for km, idname, ev, _p, _s in mp.ADDED if idname == "allset.time_view_lock"]
    assert len(locks) == 7, locks
    assert all(km == "Dopesheet" for km, _ev in locks)
    types_ = sorted({ev["type"] for _km, ev in locks})
    assert types_ == ["MIDDLEMOUSE", "WHEELDOWNMOUSE", "WHEELUPMOUSE"]
    assert bpy.ops.allset.time_view_lock.get_rna_type() is not None


# --- Range Slider row budget -------------------------------------------------------------------------------

def test_row_plan_fits_short_headers():
    bar, shown = ts.row_plan(80.0)                 # a wide header: full bar, everything shown
    assert bar == rb.BAR_UNITS and shown == {"fps", "character_set", "anim_layer"}
    bar, shown = ts.row_plan(60.0)                 # 1500 px at 1.25: the bar gives first
    assert 8.0 <= bar < rb.BAR_UNITS and shown == {"fps", "character_set", "anim_layer"}
    bar, shown = ts.row_plan(48.0)                 # the anim layer dropdown goes
    assert bar >= 8.0 and "anim_layer" not in shown and "character_set" in shown
    bar, shown = ts.row_plan(44.0)                 # then the character set
    assert bar >= 8.0 and shown == {"fps"}
    bar, shown = ts.row_plan(40.0)                 # then the fps menu
    assert bar >= 8.0 and shown == set()
    bar, shown = ts.row_plan(32.0)                 # then the fps menu; the bar keeps its minimum
    assert bar >= rb.MIN_BAR_UNITS and shown == set()
    bar, shown = ts.row_plan(20.0)
    assert bar == rb.MIN_BAR_UNITS and shown == set()
    # the row never asks for more than the width (the core items are fixed)
    for width in (36.0, 44.0, 52.0, 70.0):
        bar, shown = ts.row_plan(width)
        used = ts.ROW_CORE_UNITS + bar + sum(u for n, u in ts.ROW_OPTIONAL if n in shown)
        assert used <= width + 1e-6 or bar == rb.MIN_BAR_UNITS, (width, used)
    # transport buttons in the header take their share
    assert ts.row_plan(60.0, transport=True)[0] < ts.row_plan(60.0)[0]


def test_next_extra_floor():
    unit = 20
    assert rb.next_extra(0, 0, unit) == 0                      # the old floor
    assert rb.next_extra(0, 0, unit, floor=-14) == -4          # a header with no room shrinks the label
    assert rb.next_extra(-12, 0, unit, floor=-14) == -14
    assert rb.next_extra(-4, 85, unit, floor=-14) == -1        # room again: grows back


def test_plan_units_per_area():
    area = types.SimpleNamespace(as_pointer=lambda: 12345)
    rb._planned.pop(12345, None)
    assert rb.plan_units(area) == rb.BAR_UNITS
    assert rb.plan_units(area, 9.0) == 9.0 and rb.plan_units(area) == 9.0
    assert rb.plan_units(None) == rb.BAR_UNITS
    rb._planned.pop(12345, None)


# --- Range Slider bar: a short range, the playback fields --------------------------------------------------

def test_visual_segment_keeps_two_handles():
    bar = dict(x0=100.0, x1=500.0, s=1, e=401)     # 1 px per frame
    assert rb.visual_segment(bar, 1, 201, 18.0) == (100.0, 300.0)             # wide enough: as is
    xs, xe = rb.visual_segment(bar, 160, 160, 18.0)                            # start = end
    assert xe - xs == 38.0 and abs((xs + xe) / 2 - 259.0) < 1e-6
    xs, xe = rb.visual_segment(bar, 1, 2, 18.0)                                # at the track start
    assert (xs, xe) == (100.0, 138.0)
    xs, xe = rb.visual_segment(bar, 400, 401, 18.0)                            # at the track end
    assert (xs, xe) == (462.0, 500.0)


def test_label_positions_outside_a_short_segment():
    assert rb.label_positions(100.0, 300.0, 18.0, 20.0, 20.0, 3.0) == (121.0, 259.0)    # inside
    xa, xb = rb.label_positions(100.0, 138.0, 18.0, 20.0, 20.0, 3.0)                     # outside
    assert xa == 77.0 and xb == 141.0


def test_playback_fields_show_the_range_that_plays():
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, 120
    sc.use_preview_range = False
    assert (sc.allset_playback_start, sc.allset_playback_end) == (1, 120)
    sc.frame_end = 200
    assert sc.allset_playback_end == 200                       # off: the animation range
    sc.allset_playback_start = 20                              # typing a number turns the playback range on
    assert sc.use_preview_range and rb.playback(sc) == (20, 200)
    sc.allset_playback_end = 10                                # end before the start pushes the start, like Blender
    assert rb.playback(sc) == (10, 10)
    sc.allset_playback_start = 30
    assert rb.playback(sc) == (30, 30)
    sc.use_preview_range = False
    assert (sc.allset_playback_start, sc.allset_playback_end) == (1, 200)
    sc.allset_playback_start = 1                               # the same number changes nothing
    assert not sc.use_preview_range
    rb.toggle_whole(sc)                                        # the double-click still finds the old range
    assert rb.playback(sc) == (30, 30)
    sc.use_preview_range = False


# --- layer list row right-click ---------------------------------------------------------------------------

def test_layer_row_button_gets_the_layer_menu():
    sc = bpy.context.scene
    prop = types.SimpleNamespace(identifier="allset_layer_index")
    ctx = types.SimpleNamespace(button_pointer=sc, button_prop=prop, button_operator=None, scene=sc)
    assert le.is_layer_row(ctx) and le.is_layer_button(ctx)
    other = types.SimpleNamespace(button_pointer=sc, button_prop=types.SimpleNamespace(identifier="frame_start"),
                                  button_operator=None, scene=sc)
    assert not le.is_layer_button(other)
    # a layer: the menu names it, then Maya's items
    ob = bpy.data.objects.new("pCube1", bpy.data.meshes.new("m"))
    sc.collection.objects.link(ob)
    coll = le.new_layer(sc, [ob])
    sc.allset_layer_index = le.layers(sc).index(coll)
    rec = Recorder()
    le.draw_button_menu(types.SimpleNamespace(layout=rec), ctx)
    assert rec.items[0] == ("label", coll.name), rec.items[:2]
    assert rec.texts()[:3] == ["Add Selected Objects", "Remove Selected Objects", "Select Objects"]
    rec = Recorder()
    le.draw_button_menu(types.SimpleNamespace(layout=rec), other)
    assert rec.items == []


# --- Playblast: Save to File, the player command, the render window ---------------------------------------

def test_playblast_save_to_file_and_player_command():
    sc = bpy.context.scene
    saved = pb.save_settings(sc)
    try:
        assert pb.movie_stem("C:/shots/take1.mp4").replace("\\", "/") == "C:/shots/take1"
        assert pb.movie_stem("C:/shots/take1").replace("\\", "/") == "C:/shots/take1"
        pb.apply_settings(sc, 'MOVIE', 70, 0.5, filepath="//playblasts/shot.mov")
        assert sc.render.filepath.replace("\\", "/").endswith("playblasts/shot")
        assert pb.movie_path(sc).replace("\\", "/").endswith(".mp4")
        pb.apply_settings(sc, 'MOVIE', 70, 0.5)
        assert sc.render.filepath.startswith(pb.output_dir())
        cmd = pb.player_command(sc, bpy.context.preferences, "x.mp4", backend=None)
        assert cmd[0] == bpy.app.binary_path and cmd[1] == "-a" and cmd[-1] == "x.mp4"
        a, b = pb.playback_range(sc)
        assert cmd[cmd.index("-s") + 1] == str(a) and cmd[cmd.index("-e") + 1] == str(b)
        assert pb.player_command(sc, bpy.context.preferences, "x.mp4", backend='OPENGL')[1:3] == \
            ["--gpu-backend", "opengl"]
    finally:
        pb.restore_settings(sc, saved)
    props = bpy.ops.allset.playblast.get_rna_type().properties
    assert "save_to_file" in props and "filepath" in props
    # window helpers: the startup window is not a render window
    wm = bpy.context.window_manager
    assert pb.window_ids(wm) and not any(pb.is_render_window(w) for w in wm.windows)
    assert pb.close_render_windows(bpy.context, pb.window_ids(wm)) == 0
    assert pb.bring_to_front(0, 0.0) is None
