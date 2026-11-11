"""#252 in a real UI: Maya Workflow Kit layout -> new Maya scene -> cube + two cameras (one with Renderable off) ->
Render > Render Sequence ❒ (the Maya window, All Render-Enabled Cameras on) -> Return -> one Blender render job
after another, each renderable camera's frames in its own folder (persp, camA), the off camera not rendered, the
output path and render camera restored. Then a second sequence cancelled during the first camera's job: the
camera still waiting doesn't render, the settings come back. Render Settings opens Blender's Render properties with
Maya's Common panel (Skip existing frames, Renderable Cameras). Screenshots: gui_issue252_window.png,
gui_issue252_render.png, gui_issue252_render_settings.png."""

import os
import shutil
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, load_maya_layout, run, setup, step, win  # noqa: E402

GUI_TIMEOUT = 300
SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
OUT = os.path.join(ROOT, "tmp", os.environ.get("ALLSET_SANDBOX", "test_env"), "gui_issue252")
PATH = "Render/Render Sequence"
C = {}


def mod(name):
    return import_module(MODULE + name)


def shot(name, window=None):
    if SHOTS:
        with bpy.context.temp_override(window=window or win()):
            bpy.ops.screen.screenshot(filepath=os.path.join(SHOTS, name))


def v3d():
    area = max((a for a in win().screen.areas if a.type == 'VIEW_3D'), key=lambda a: a.width * a.height)
    return area, next(r for r in area.regions if r.type == 'WINDOW')


def wait(fn, cond, limit=600):
    """Run ``fn`` again next tick until ``cond()`` or ``limit`` ticks."""
    C.setdefault(fn.__name__, 0)
    if not cond() and C[fn.__name__] < limit:
        C[fn.__name__] += 1
        sys.modules["sim"]._steps.insert(0, fn)
        return True
    return False


def _camera(name, x):
    ob = bpy.data.objects.new(name, bpy.data.cameras.new(name + "Shape"))
    bpy.context.scene.collection.objects.link(ob)
    ob.location = (x, -30.0, 0.0)
    ob.rotation_euler = (1.5708, 0.0, 0.0)
    return ob


def _folders():
    return {d: sorted(f for f in os.listdir(os.path.join(OUT, d)) if f.endswith(".png"))
            for d in sorted(os.listdir(OUT)) if os.path.isdir(os.path.join(OUT, d))}


def _settings():
    sc = bpy.context.scene
    return (sc.render.filepath, sc.camera)


def _render_window():
    for w in bpy.context.window_manager.windows[1:]:
        for a in w.screen.areas:
            if a.type == 'IMAGE_EDITOR':
                return w, a
    return None, None


def _idle():
    return not mod(".operators.render_cameras").running() and not bpy.app.is_job_running('RENDER')


@step
def s_setup():
    setup()
    bpy.ops.allset.make_maya(open_layout=False)
    load_maya_layout()


@step
def s_scene():
    bpy.ops.allset.keymap_activate()
    shutil.rmtree(OUT, ignore_errors=True)
    os.makedirs(OUT, exist_ok=True)
    sc = bpy.context.scene
    area, region = v3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.allset.create(kind='CUBE')
    _camera("camA", 0.0)
    off = _camera("camOff", 5.0)
    off.data.allset_renderable = False
    r = sc.render
    r.engine = 'BLENDER_WORKBENCH'
    r.resolution_x = r.resolution_y = 16
    r.resolution_percentage = 100
    r.image_settings.file_format = 'PNG'
    sc.frame_start, sc.frame_end = 1, 2
    r.filepath = os.path.join(OUT, "shot_")
    C["before"] = _settings()
    names = [o.name for o in mod(".operators.render_cameras").renderable_cameras(sc)]
    check(f"renderable cameras of a new Maya scene + camA + camOff (off): persp, camA ({names})",
          names == ["persp", "camA"])
    # the window opens with the values saved last time (Maya keeps option values): All Render-Enabled Cameras on
    mod(".operators.option_windows").store("render_sequence", {"camera": "persp", "all_cameras": True, "output": ""})
    ev('MOUSEMOVE', 'NOTHING', x=region.x + region.width // 2, y=region.y + region.height // 2)
    with bpy.context.temp_override(window=win(), area=area, region=region):
        menu_map = mod(".ui.menu_map")
        C["box"] = mod(".marking.modal").run_action(bpy.context, menu_map.MAP[PATH], option=True, path=PATH)


@step
def s_window():
    check(f"Render > Render Sequence ❒ opens the Render Sequence window ({C['box']})", C["box"] == {'RUNNING_MODAL'})


@step
def s_window_shot():
    shot("gui_issue252_window.png")
    ev('RET', 'PRESS')
    ev('RET', 'RELEASE')


@step
def s_started():
    rc = mod(".operators.render_cameras")
    if wait(s_started, lambda: rc.running() or bpy.app.is_job_running('RENDER'), limit=20):
        return
    check("Return in the window starts the sequence (render job + the sequence's timer)", rc.running())


@step
def s_done():
    if wait(s_done, _idle):
        return
    want = ["shot_0001.png", "shot_0002.png"]
    found = _folders()
    rc = mod(".operators.render_cameras")
    check(f"All Render-Enabled Cameras: one folder per renderable camera, camOff none ({found}, "
          f"{rc._run['done']} render jobs)", found == {"persp": want, "camA": want} and rc._run["done"] == 2)
    after = _settings()
    check(f"output path and render camera restored ({after[0]}, {after[1]})", after == C["before"])
    hs = bpy.app.handlers
    check("no handler or timer of the sequence left",
          rc._on_cancel not in hs.render_cancel and rc._on_complete not in hs.render_complete and not rc.running())
    w, _a = _render_window()
    check(f"Blender's Render window shows the renders ({w is not None})", w is not None)
    shot("gui_issue252_render.png", w)


@step
def s_long():
    """A longer sequence (persp, camA) cancelled during persp's render job."""
    sc = bpy.context.scene
    sc.frame_end = 60
    shutil.rmtree(OUT, ignore_errors=True)
    os.makedirs(OUT, exist_ok=True)
    C["before"] = _settings()
    rc = mod(".operators.render_cameras")
    area, region = v3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        C["ret"] = bpy.ops.allset.render_sequence('INVOKE_DEFAULT', all_cameras=True)
    check(f"second sequence started ({C['ret']}, running {rc.running()})", C["ret"] == {'FINISHED'} and rc.running())


def _first_frames():
    d = os.path.join(OUT, "persp")
    return os.path.isdir(d) and len(os.listdir(d)) >= 3


@step
def s_cancel():
    if wait(s_cancel, _first_frames, limit=100):
        return
    rc = mod(".operators.render_cameras")
    C["job_running"] = bpy.app.is_job_running('RENDER')
    # Blender's render_cancel call of a cancelled render job (Esc reaches Blender from the OS keyboard only, which
    # simulated events skip; the key itself is in docs/manual_checks.md)
    rc._on_cancel()


@step
def s_cancel_done():
    if wait(s_cancel_done, _idle, limit=600):
        return
    found = _folders()
    check(f"a cancelled render job (cancel during persp's job: {C.get('job_running')}) stops the cameras still "
          f"waiting ({ {k: len(v) for k, v in found.items()} })", C.get("job_running") and "camA" not in found)
    after = _settings()
    check(f"output path and render camera restored after the cancel ({after[0]}, {after[1]})",
          after == C["before"])
    rc = mod(".operators.render_cameras")
    hs = bpy.app.handlers
    check("no handler or timer of the sequence left after the cancel",
          rc._on_cancel not in hs.render_cancel and rc._on_complete not in hs.render_complete and not rc.running())
    mod(".operators.option_windows").store("render_sequence", None)
    for w in list(bpy.context.window_manager.windows[1:]):
        with bpy.context.temp_override(window=w):
            bpy.ops.wm.window_close()


def _properties_render():
    """(window, area) of a Properties editor on the Render tab in a window other than the main one."""
    for w in bpy.context.window_manager.windows[1:]:
        for a in w.screen.areas:
            if a.type == 'PROPERTIES' and a.spaces.active.context == 'RENDER':
                return w, a
    return None, None


@step
def s_settings():
    """Render Settings (the Status Line button's operator) opens Blender's Render properties with Maya's Common."""
    cls = bpy.types.ALLSET_PT_render_common
    C["drawn"] = 0
    C["draw"] = draw = cls.draw

    def counting(self, context):
        C["drawn"] += 1
        draw(self, context)
    cls.draw = counting
    # each Renderable row reads its check while the panel draws, from the startup cameras found once for the draw
    # (the interface reads the rows once more after the draw; those reads look at the objects themselves)
    rc = mod(".operators.render_cameras")
    C["reads"] = reads = {"in_draw": 0, "outside": 0}
    C["default"] = default = rc.default_renderable

    def counted(cam):
        reads["in_draw" if rc._drawing else "outside"] += 1
        return default(cam)
    rc.default_renderable = counted
    with bpy.context.temp_override(window=win()):
        C["rs"] = bpy.ops.allset.render_settings()


@step
def s_settings_shown():
    if wait(s_settings_shown, lambda: _properties_render()[0] is not None and C["drawn"] > 0, limit=60):
        for w in bpy.context.window_manager.windows:
            for a in w.screen.areas:
                a.tag_redraw()
        return
    w, _a = _properties_render()
    check(f"Render Settings ({C['rs']}) opens Properties > Render with the Common panel drawn "
          f"(window {w is not None}, panel draws {C['drawn']})", w is not None and C["drawn"] > 0)
    shot("gui_issue252_render_settings.png", w)
    cls = bpy.types.ALLSET_PT_render_common
    cls.draw = C["draw"]
    rc = mod(".operators.render_cameras")
    rc.default_renderable = C["default"]
    unset = sum(rc.STORE not in ob.data for ob in rc.candidates(bpy.context.scene))
    reads = C["reads"]
    check(f"each Renderable row without a value of its own reads it in the draw from the startup cameras found once "
          f"({unset} rows, {C['drawn']} draws, reads in the draw {reads['in_draw']}, after it {reads['outside']})",
          unset > 0 and reads["in_draw"] >= unset * C["drawn"] and not rc._drawing)
    sw = mod(".switch")
    sw.set_mode(False, layout=False)
    try:
        off = cls.poll(bpy.context)
        gone = not hasattr(bpy.types, "ALLSET_PT_render_common")
    finally:
        sw.set_mode(True, layout=False)
    check(f"plain Blender (Maya mode off) has no Common panel (poll {off}, unregistered {gone})", off is False and gone)
    check("Maya mode on again: the panel is back", hasattr(bpy.types, "ALLSET_PT_render_common"))
    for w in list(bpy.context.window_manager.windows[1:]):
        with bpy.context.temp_override(window=w):
            bpy.ops.wm.window_close()


run()
