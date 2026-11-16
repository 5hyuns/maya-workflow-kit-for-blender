"""Issue #344 in a real UI: on each frame of playback the Maya layout redraws its viewports, not the Tool Box column or
the shelf.

A keyed cube plays (every frame) in the Maya layout three ways: the Time Slider's play button (playback started over
an animation editor makes Blender redraw every 3D View and Image Editor), Blender's own play from the viewport, and
Maya's Play key (Alt+V) with the mouse over the Time Slider. Each time the main viewport is drawn on (nearly) every
frame, while the Tool Box column (a narrow 3D View) and the shelf (an Image Editor) are not; afterwards the screen's
playback settings are as before. In the four view, with Maya's Update View: Active (the default), only the panel the
mouse was last in is drawn on every frame and every panel once playback stops; changing the frame without playing
draws every panel; with Update View: All all four are drawn on every frame, and a frame costs less with Active. Last,
played as fast as the PC draws (scene rate 1000, VSync off), a frame started by the Time Slider's play button costs
about what a frame started over the viewport does (a loose 30 % margin: other programs on the PC move the numbers)."""

import os
import sys
import time
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sim  # noqa: E402
from sim import MODULE, check, ev, load_maya_layout, run, setup, step, win  # noqa: E402

GUI_TIMEOUT = 300
GUI_ARGS = "--gpu-vsync off"
C = {"draws": {}, "played": {}, "frames": 0, "handles": []}


def mod(name):
    return import_module(f"{MODULE}.{name}")


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


def toolbox():
    tb = mod("ui.toolbox")
    return next(a for a in win().screen.areas if a.type == 'VIEW_3D' and tb.is_toolbox(a.spaces.active))


def views():
    tb = mod("ui.toolbox")
    return [a for a in win().screen.areas if a.type == 'VIEW_3D' and not tb.is_toolbox(a.spaces.active)]


def shelf():
    """The shelf row: the tallest Image Editor of the layout (the Status Line row is a header only)."""
    return max((a for a in win().screen.areas if a.type == 'IMAGE_EDITOR'),
               key=lambda a: next((r.height for r in a.regions if r.type == 'WINDOW'), 0))


def time_slider():
    return next(a for a in win().screen.areas if a.type == 'DOPESHEET_EDITOR')


def region(area, kind='WINDOW'):
    return next(r for r in area.regions if r.type == kind)


def _count():
    area = bpy.context.area
    if area is not None:
        C["draws"][area.as_pointer()] = C["draws"].get(area.as_pointer(), 0) + 1


@bpy.app.handlers.persistent
def _frame(*_a):
    C["frames"] += 1
    C.setdefault("times", []).append(time.perf_counter())


def start_counting():
    C["draws"].clear()
    C["frames"] = 0


def draws(area):
    """Draws of ``area`` while it played (counted up to the stop: stopping redraws everything once more)."""
    return C["played"].get(area.as_pointer(), 0)


def playing():
    return any(w.screen.is_animation_playing for w in bpy.context.window_manager.windows)


@step
def s_setup():
    setup()
    load_maya_layout()


for _i in range(8):          # the layout is fitted to the UI scale in the first seconds after a load
    step(redraw)


@step
def s_scene():
    sc = bpy.context.scene
    me = bpy.data.meshes.new("cube")
    me.from_pydata([(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)], [],
                   [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)])
    ob = bpy.data.objects.new("pCube1", me)
    sc.collection.objects.link(ob)
    for f, x in ((1, -3.0), (1000, 3.0)):
        ob.location.x = x
        ob.keyframe_insert("location", index=0, frame=f)
    sc.frame_start, sc.frame_end, sc.frame_current = 1, 1000, 1
    sc.use_preview_range = False
    sc.sync_mode = 'NONE'              # every frame is played and drawn
    C["handles"] = [(bpy.types.SpaceView3D, bpy.types.SpaceView3D.draw_handler_add(_count, (), 'WINDOW', 'POST_PIXEL')),
                    (bpy.types.SpaceImageEditor,
                     bpy.types.SpaceImageEditor.draw_handler_add(_count, (), 'WINDOW', 'POST_PIXEL'))]
    bpy.app.handlers.frame_change_post.append(_frame)
    scr = win().screen
    C["flags"] = (scr.use_play_3d_editors, scr.use_play_animation_editors)
    check(f"Maya layout: a Tool Box column ({toolbox().width} px), a shelf ({shelf().height} px), one viewport",
          toolbox() is not None and shelf() is not None and len(views()) == 1)


def play_and_check(label, start, stop, four=False, active=None):
    def go():
        start_counting()
        C["t0"] = time.perf_counter()
        start()

    def wait():
        pass                 # no redraw asked by the test while counting

    def end():
        C["played"] = dict(C["draws"])
        C["n"] = C["frames"]
        C["playing"] = playing()
        C["mark"] = mod("ui.playback_redraw").MARK in win().screen
        C["during"] = (win().screen.use_play_3d_editors, win().screen.use_play_animation_editors)
        stop()

    def verdict():
        n = C["n"]
        scr = win().screen
        vs = views()
        main = [draws(a) for a in vs]
        check(f"{label}: playback ran ({n} frames, playing {C['playing']})", C["playing"] and n >= 10)
        if active is None:
            check(f"{label}: the viewport{'s' if four else ''} drawn on each frame ({main} draws, {n} frames)",
                  all(d >= 0.8 * n for d in main) and len(vs) == (4 if four else 1))
        else:
            one = active()
            others = [draws(a) for a in vs if a != one]
            after = [C["draws"].get(a.as_pointer(), 0) - draws(a) for a in vs]
            check(f"{label}: only the active panel drawn on each frame ({draws(one) if one else None} draws, the others "
                  f"{others}, {n} frames)", one is not None and draws(one) >= 0.8 * n and all(d <= 3 for d in others)
                  and len(vs) == 4)
            check(f"{label}: every panel drawn once playback stopped ({after})", all(d >= 1 for d in after))
        check(f"{label}: the Tool Box column not drawn on each frame ({draws(toolbox())} draws)", draws(toolbox()) <= 3)
        check(f"{label}: the shelf not drawn on each frame ({draws(shelf())} draws)", draws(shelf()) <= 3)
        check(f"{label}: playback settings as before afterwards ({(scr.use_play_3d_editors, scr.use_play_animation_editors)}"
              f" vs {C['flags']}, mark {mod('ui.playback_redraw').MARK in scr}; while playing 3D off + mark: "
              f"{C['during']}, {C['mark']})",
              (scr.use_play_3d_editors, scr.use_play_animation_editors) == C["flags"]
              and mod("ui.playback_redraw").MARK not in scr and not C["during"][0] and C["mark"])
    step(go)
    for _ in range(5):
        step(wait)
    step(end)
    step(redraw)
    step(verdict)


def over(area):
    r = region(area)
    return bpy.context.temp_override(window=win(), screen=win().screen, area=area, region=r)


def time_slider_button():
    with over(time_slider()):
        bpy.ops.allset.play()        # what the Time Slider's play button runs


def time_slider_stop():
    with over(time_slider()):
        bpy.ops.allset.play()


def blender_play():
    with over(views()[0]):
        bpy.ops.screen.animation_play()


def blender_stop():
    with over(views()[0]):
        bpy.ops.screen.animation_cancel(restore_frame=False)


def alt_v():
    r = region(time_slider())
    x, y = r.x + r.width // 2, r.y + r.height // 2
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('LEFT_ALT', 'PRESS', x=x, y=y)
    ev('V', 'PRESS', x=x, y=y, alt=True)
    ev('V', 'RELEASE', x=x, y=y, alt=True)
    ev('LEFT_ALT', 'RELEASE', x=x, y=y)


play_and_check("Time Slider play button", time_slider_button, time_slider_stop)
play_and_check("Blender's play from the viewport", blender_play, blender_stop)


@step
def s_mouse_to_slider():
    r = region(time_slider())
    ev('MOUSEMOVE', 'NOTHING', x=r.x + r.width // 2, y=r.y + r.height // 2)


play_and_check("Alt+V over the Time Slider", alt_v, alt_v)


@step
def s_four():
    with over(views()[0]):
        mod("ui.four_view").toggle(bpy.context, views()[0], win())


step(redraw)
step(redraw)


@step
def s_four_check():
    check(f"four view on ({len(views())} viewports)", len(views()) == 4)
    prefs = mod("preferences").get()
    check(f"Update View: {prefs.playback_update_view} by default", prefs.playback_update_view == 'ACTIVE')


def role(name):
    return fv_roles()[name]


def fv_roles():
    return mod("ui.four_view").roles(win().screen)


@step
def s_mouse_to_side():
    r = region(role("side"))
    ev('MOUSEMOVE', 'NOTHING', x=r.x + r.width // 2, y=r.y + r.height // 2)


@step
def s_mouse_in_side():
    r = region(role("side"))
    ev('MOUSEMOVE', 'NOTHING', x=r.x + r.width // 2 + 3, y=r.y + r.height // 2 + 3)


play_and_check("four view, Update View: Active, mouse last in side, Time Slider play button", time_slider_button,
               time_slider_stop, four=True, active=lambda: role("side"))


@step
def s_active_ms():
    start_counting()
    bpy.context.scene.frame_current += 5          # a frame change without playback (scrubbing)


step(redraw)


@step
def s_scrub():
    got = [C["draws"].get(a.as_pointer(), 0) for a in views()]
    check(f"four view: a frame change without playback draws every panel ({got})", all(d >= 1 for d in got))
    mod("preferences").get().playback_update_view = 'ALL'


play_and_check("four view, Update View: All, Time Slider play button", time_slider_button, time_slider_stop,
               four=True)


@step
def s_all_back():
    mod("preferences").get().playback_update_view = 'ACTIVE'


def timed(label, start, stop):
    def go():
        C["times"] = []
        start()

    def end():
        t = C["times"][5:]           # the first frames include the start
        iv = sorted(b - a for a, b in zip(t, t[1:]))
        C.setdefault("ms", {})[label] = 1000 * iv[len(iv) // 2] if iv else None
        stop()
    step(go)
    for _ in range(4):
        step(lambda: None)
    step(end)
    step(redraw)


@step
def s_fast():
    bpy.context.scene.render.fps = 1000


timed("four active", time_slider_button, time_slider_stop)


@step
def s_fast_all():
    mod("preferences").get().playback_update_view = 'ALL'


timed("four all", time_slider_button, time_slider_stop)


@step
def s_fast_four_check():
    mod("preferences").get().playback_update_view = 'ACTIVE'
    one, every = C["ms"].get("four active"), C["ms"].get("four all")
    print(f"PLAYBACK four view ms/frame: Update View Active {one}, All {every}", flush=True)
    check(f"four view: a frame costs less with Update View: Active ({one} ms) than with All ({every} ms)",
          one and every and one <= every)
    with over(views()[0]):
        mod("ui.four_view").toggle(bpy.context, views()[0], win())        # back to one viewport


step(redraw)
step(redraw)
timed("view", blender_play, blender_stop)
timed("button", time_slider_button, time_slider_stop)


@step
def s_fast_check():
    view_ms, button_ms = C["ms"].get("view"), C["ms"].get("button")
    print(f"PLAYBACK ms/frame: over the viewport {view_ms}, Time Slider button {button_ms}", flush=True)
    check(f"a frame started by the Time Slider button costs about one started over the viewport ({button_ms} ms vs "
          f"{view_ms} ms)", view_ms and button_ms and button_ms <= 1.3 * view_ms)


@step
def s_cleanup():
    for cls, h in C["handles"]:
        cls.draw_handler_remove(h, 'WINDOW')
    if _frame in bpy.app.handlers.frame_change_post:
        bpy.app.handlers.frame_change_post.remove(_frame)


run()
