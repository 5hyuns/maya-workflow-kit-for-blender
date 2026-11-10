"""#252: Render > Render Sequence ❒ with All Render-Enabled Cameras renders the frame range once per Renderable
camera, one after another, each camera's frames in a folder named after the camera (when more than one renders);
the render camera and output path come back afterwards, a cancel stops the remaining cameras. Every camera has
Maya's Renderable check (new cameras and persp on, top / front / side off). Skip existing frames is Blender's
Overwrite off + Placeholders on."""

import os
import shutil
import types
from importlib import import_module

import bpy

import kit

ow = import_module(kit.MODULE + ".operators.option_windows")
startup = import_module(kit.MODULE + ".operators.startup_cameras")
rp = import_module(kit.MODULE + ".operators.render_persp")
menu_map = import_module(kit.MODULE + ".ui.menu_map")
menu_sets = import_module(kit.MODULE + ".ui.menu_sets")
shelf_map = import_module(kit.MODULE + ".ui.shelf_map")
ae_layout = import_module(kit.MODULE + ".ui.ae_layout")

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(kit.__file__)), ".."))
OUT = os.path.join(ROOT, "tmp", os.environ.get("ALLSET_SANDBOX", "test_env"), "issue252")
PATH = "Render/Render Sequence"


def _rc():
    return import_module(kit.MODULE + ".operators.render_cameras")


def _clear():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for cam in list(bpy.data.cameras):
        bpy.data.cameras.remove(cam)
    bpy.context.scene.camera = None


def _camera(name, x):
    ob = bpy.data.objects.new(name, bpy.data.cameras.new(name + "Shape"))
    bpy.context.scene.collection.objects.link(ob)
    ob.location = (x, -10.0, 0.0)
    ob.rotation_euler = (1.5708, 0.0, 0.0)
    return ob


def _tiny(scene, path, frames=2):
    r = scene.render
    r.engine = 'BLENDER_WORKBENCH'
    r.resolution_x = r.resolution_y = 16
    r.resolution_percentage = 100
    r.image_settings.file_format = 'PNG'
    r.use_overwrite, r.use_placeholder = True, False
    scene.frame_start, scene.frame_end, scene.frame_step = 1, frames, 1
    r.filepath = path


def _fresh_out():
    shutil.rmtree(OUT, ignore_errors=True)
    os.makedirs(OUT, exist_ok=True)


def _files(folder):
    return sorted(f for f in os.listdir(folder) if f.endswith(".png")) if os.path.isdir(folder) else []


def _idle():
    """Nothing of the sequence is left running: no handler, no timer."""
    rc = _rc()
    hs = bpy.app.handlers
    return (not bpy.app.timers.is_registered(rc._tick) and rc._on_cancel not in hs.render_cancel
            and rc._on_complete not in hs.render_complete)


# --- output paths -----------------------------------------------------------------------------------------------

def test_camera_output_paths():
    rc = _rc()
    assert rc.camera_output("//render/scene_", "camFront") == "//render/camFront/scene_"
    assert rc.camera_output("C:\\out\\", "camSide") == "C:\\out\\camSide\\"
    assert rc.camera_output("shot", "cam") == "cam/shot"
    assert rc.camera_output("//shot_####", "cam") == "//cam/shot_####"
    assert rc.folder_name("ns:cam|a") == "ns_cam_a"
    assert rc.folder_name(" .") == "camera"
    sc = bpy.context.scene
    sc.render.filepath = "//render/shot_"
    alt = os.path.join(OUT, "alt")
    assert rc.alternate_path(sc, alt) == os.path.join(alt, "shot_")


# --- Renderable -------------------------------------------------------------------------------------------------

def test_renderable_defaults_and_storage():
    rc = _rc()
    _clear()
    cam = _camera("shotCam", 0.0)
    assert cam.data.allset_renderable, "a new camera is renderable"
    cam.data.allset_renderable = False
    assert not cam.data.allset_renderable and not rc.is_renderable(cam)
    assert cam.data.get(rc.STORE) is False or cam.data.get(rc.STORE) == 0
    cam.data.allset_renderable = True
    assert rc.is_renderable(cam)


def test_startup_cameras_only_persp_renderable():
    rc = _rc()
    _clear()
    made = startup.ensure(bpy.context.scene)
    on = {ob.name for ob in made if ob.data.allset_renderable}
    assert on == {"persp"}, on
    other = _camera("shotCam", 0.0)
    assert [ob.name for ob in rc.candidates(bpy.context.scene)] == ["persp", "top", "front", "side", other.name]
    assert [ob.name for ob in rc.renderable_cameras(bpy.context.scene)] == ["persp", other.name]


def test_kit_persp_is_renderable():
    rc = _rc()
    _clear()
    persp = rp.persp_camera(create=True)
    assert persp.data.allset_renderable
    cam = _camera("camA", 0.0)
    assert rc.renderable_cameras(bpy.context.scene) == [persp, cam], "the kit persp (in no collection) counts too"


def test_plan_one_camera_keeps_the_output():
    rc = _rc()
    _clear()
    a = _camera("camA", 0.0)
    b = _camera("camB", 2.0)
    b.data.allset_renderable = False
    assert rc.plan(bpy.context.scene, "//r/s_") == [(a, "//r/s_")]
    b.data.allset_renderable = True
    assert rc.plan(bpy.context.scene, "//r/s_") == [(a, "//r/camA/s_"), (b, "//r/camB/s_")]


# --- real renders (Workbench, 16 px, 2 frames) ------------------------------------------------------------------

def test_all_render_enabled_cameras_renders_each_into_its_folder():
    _clear()
    _fresh_out()
    scene = bpy.context.scene
    bpy.ops.mesh.primitive_cube_add(size=2.0)
    _camera("camFront", 0.0)
    _camera("camSide", 3.0)
    off = _camera("camOff", 6.0)
    off.data.allset_renderable = False
    scene.camera = off
    base = os.path.join(OUT, "shot_")
    _tiny(scene, base)
    assert bpy.ops.allset.render_sequence(all_cameras=True) == {'FINISHED'}
    for name in ("camFront", "camSide"):
        assert _files(os.path.join(OUT, name)) == ["shot_0001.png", "shot_0002.png"], name
    assert not os.path.exists(os.path.join(OUT, "camOff"))
    assert not _files(OUT), "nothing next to the camera folders"
    assert scene.render.filepath == base and scene.camera == off, "output path and render camera come back"
    assert _idle()


def test_one_renderable_camera_renders_into_the_output_folder():
    _clear()
    _fresh_out()
    scene = bpy.context.scene
    _camera("solo", 0.0)
    _tiny(scene, os.path.join(OUT, "one_"))
    assert bpy.ops.allset.render_sequence(all_cameras=True) == {'FINISHED'}
    assert _files(OUT) == ["one_0001.png", "one_0002.png"]
    assert not os.path.exists(os.path.join(OUT, "solo"))


def test_alternate_output_with_all_cameras():
    _clear()
    _fresh_out()
    scene = bpy.context.scene
    _camera("c1", 0.0)
    _camera("c2", 2.0)
    base = os.path.join(OUT, "elsewhere", "img_")
    _tiny(scene, base)
    alt = os.path.join(OUT, "alt")
    assert bpy.ops.allset.render_sequence(all_cameras=True, output=alt) == {'FINISHED'}
    assert _files(os.path.join(alt, "c1")) == ["img_0001.png", "img_0002.png"]
    assert _files(os.path.join(alt, "c2")) == ["img_0001.png", "img_0002.png"]
    assert not os.path.exists(os.path.join(OUT, "elsewhere"))
    assert scene.render.filepath == base


def test_current_camera_picked_renders_through_it_and_comes_back():
    _clear()
    _fresh_out()
    scene = bpy.context.scene
    one = _camera("c1", 0.0)
    _camera("c2", 2.0)
    scene.camera = one
    _tiny(scene, os.path.join(OUT, "cur_"))
    assert bpy.ops.allset.render_sequence(camera="c2") == {'FINISHED'}
    assert _files(OUT) == ["cur_0001.png", "cur_0002.png"]
    assert scene.camera == one, "the picked camera renders for this sequence only"
    assert _idle()


def test_default_is_the_plain_render_sequence():
    """No options = Blender's Render Animation through the scene camera; a scene without one renders persp."""
    _clear()
    _fresh_out()
    scene = bpy.context.scene
    _tiny(scene, os.path.join(OUT, "def_"), frames=1)
    assert bpy.ops.allset.render_sequence() == {'FINISHED'}
    assert scene.camera is not None and rp.is_persp(scene.camera)
    assert _files(OUT) == ["def_0001.png"]


def test_no_renderable_camera_cancels():
    _clear()
    cam = _camera("only", 0.0)
    cam.data.allset_renderable = False
    try:
        res = bpy.ops.allset.render_sequence(all_cameras=True)
    except RuntimeError:
        res = {'CANCELLED'}
    assert res == {'CANCELLED'}
    assert _idle()


# --- Skip existing frames ---------------------------------------------------------------------------------------

def test_skip_existing_frames_maps_to_overwrite_and_placeholders():
    scene = bpy.context.scene
    r = scene.render
    r.use_overwrite, r.use_placeholder = True, False
    assert not scene.allset_skip_existing
    scene.allset_skip_existing = True
    assert (r.use_overwrite, r.use_placeholder) == (False, True)
    r.use_overwrite = True          # Blender's own Output properties switch it back
    assert not scene.allset_skip_existing
    r.use_overwrite = False
    assert scene.allset_skip_existing
    scene.allset_skip_existing = False
    assert (r.use_overwrite, r.use_placeholder) == (True, False)


def test_skip_existing_frames_leaves_rendered_frames():
    _clear()
    _fresh_out()
    scene = bpy.context.scene
    _camera("a", 0.0)
    _camera("b", 2.0)
    _tiny(scene, os.path.join(OUT, "skip_"))
    os.makedirs(os.path.join(OUT, "a"))
    first = os.path.join(OUT, "a", "skip_0001.png")
    with open(first, "wb") as f:
        f.write(b"kept")
    scene.allset_skip_existing = True
    try:
        assert bpy.ops.allset.render_sequence(all_cameras=True) == {'FINISHED'}
    finally:
        scene.allset_skip_existing = False
    with open(first, "rb") as f:
        assert f.read() == b"kept", "an existing frame is not rendered again"
    assert os.path.getsize(os.path.join(OUT, "a", "skip_0002.png")) > 4
    assert _files(os.path.join(OUT, "b")) == ["skip_0001.png", "skip_0002.png"]


# --- the sequence of render jobs (Blender's INVOKE render: one job per camera) ----------------------------------

def _fake_jobs(rc, monkey):
    """Replace the INVOKE render start: record (camera, path) instead of starting a render job."""
    started = []
    old = rc._launch

    def launch(scene):
        started.append((scene.camera.name, scene.render.filepath))
        return True
    rc._launch = launch
    monkey.append(lambda: setattr(rc, "_launch", old))
    return started


def test_job_chain_runs_each_camera_then_restores():
    rc = _rc()
    _clear()
    scene = bpy.context.scene
    a, b = _camera("camA", 0.0), _camera("camB", 2.0)
    scene.camera = None
    scene.render.filepath = "//r/s_"
    undo = []
    started = _fake_jobs(rc, undo)
    try:
        assert rc.begin(bpy.context, rc.plan(scene, "//r/s_"))
        assert started == [("camA", "//r/camA/s_")]
        assert rc.running() and rc._on_cancel in bpy.app.handlers.render_cancel
        rc._on_complete()              # the render thread reports the end of camA's job
        assert rc._tick() is not None  # the job is over: camB starts
        assert started[-1] == ("camB", "//r/camB/s_")
        rc._on_complete()
        assert rc._tick() is None      # last camera done: the sequence ends
        assert scene.camera is None and scene.render.filepath == "//r/s_"
        assert not rc.running() and _idle()
    finally:
        for fn in undo:
            fn()
        rc.stop()
    assert (a.name, b.name) == ("camA", "camB")


def test_cancel_stops_the_remaining_cameras():
    rc = _rc()
    _clear()
    scene = bpy.context.scene
    _camera("c1", 0.0)
    _camera("c2", 2.0)
    _camera("c3", 4.0)
    keep = scene.camera = bpy.data.objects["c3"]
    scene.render.filepath = "//r/s_"
    undo = []
    started = _fake_jobs(rc, undo)
    try:
        assert rc.begin(bpy.context, rc.plan(scene, "//r/s_"))
        rc._on_cancel()                # Esc in the Render window
        assert rc._tick() is None
        assert [n for n, _p in started] == ["c1"], started
        assert scene.camera == keep and scene.render.filepath == "//r/s_"
        assert _idle()
        # a job that ended without Blender's render-complete call (an error) stops the sequence too
        assert rc.begin(bpy.context, rc.plan(scene, "//r/s_"))
        assert rc._tick() is None
        assert [n for n, _p in started] == ["c1", "c1"], started
        assert _idle()
    finally:
        for fn in undo:
            fn()
        rc.stop()


def test_a_second_sequence_waits_for_the_first():
    rc = _rc()
    _clear()
    scene = bpy.context.scene
    _camera("c1", 0.0)
    _camera("c2", 2.0)
    undo = []
    _fake_jobs(rc, undo)
    try:
        assert rc.begin(bpy.context, rc.plan(scene, "//r/s_"))
        try:
            res = bpy.ops.allset.render_sequence(all_cameras=True)
        except RuntimeError:
            res = {'CANCELLED'}
        assert res == {'CANCELLED'}, "a render is already running"
    finally:
        for fn in undo:
            fn()
        rc.stop()
    assert _idle()


# --- the window, the menu item, the Attribute Editor ------------------------------------------------------------

def test_render_sequence_window_is_maya():
    w = ow._BY_KEY["render_sequence"]
    assert (w.title, w.action, w.apply_text) == ("Render Sequence (Current Frame)", "Render Sequence and Close",
                                                "Render Sequence")
    assert [(f.name, f.label, f.default) for f in w.fields] == [
        ("camera", "Current Camera:", "persp"), ("all_cameras", "", False),
        ("output", "Alternate Output File Location:", "")]
    assert "All Render-Enabled Cameras" not in w.missing and "Render Region" in w.missing
    assert menu_sets.option_kind(PATH) == "window"
    assert menu_sets.option_kind("Render/Batch Render") == "generic", "Batch Render keeps Blender's render"
    assert menu_map.MAP[PATH] == "allset.render_sequence"
    assert shelf_map.BY_COMMAND["RenderSequence"][0] == ("allset.render_sequence", {})
    assert ow.find(("allset.render_sequence", {})) is w, "the shelf button uses the window's values too"
    # Current Camera is greyed while All Render-Enabled Cameras is on (like Maya)
    assert w.enabled({"all_cameras": True}, "camera") is False
    assert w.enabled({"all_cameras": False}, "camera") is True


def test_current_camera_items():
    rc = _rc()
    _clear()
    _camera("shotCam", 0.0)
    owr = import_module(kit.MODULE + ".operators.option_windows_render")
    items = owr._cameras(None, bpy.context)
    assert items[0][:2] == ("persp", "persp") and "shotCam" in [i[0] for i in items]
    bpy.context.scene.camera = bpy.data.objects["shotCam"]
    assert owr._cameras(None, bpy.context)[0][1] == "shotCam (scene camera)", "the default renders the scene camera"
    assert rc is not None


class _Rec:
    """A layout that records prop() calls."""

    def __init__(self, seen):
        self.seen = seen
        self.use_property_split = self.use_property_decorate = self.enabled = False

    def prop(self, data, name, **kw):
        self.seen.append((data, name, kw.get("text")))

    def __getattr__(self, name):
        return lambda *a, **kw: self


def test_window_lists_renderable_cameras_and_skip_existing():
    _clear()
    cam = _camera("shotCam", 0.0)
    seen = []
    w = ow._BY_KEY["render_sequence"]
    holder = types.SimpleNamespace(camera="persp", all_cameras=True, output="")
    ow.draw_fields(w, _Rec(seen), holder)
    props = [(name, text) for data, name, text in seen]
    assert ("allset_skip_existing", "Skip existing frames") in props, props
    assert any(data == cam.data and name == "allset_renderable" and text == "shotCam"
               for data, name, text in seen), seen


def test_attribute_editor_camera_output_settings():
    rows = [r for sec in ae_layout.CAMERA if sec.name == "Output Settings" for r in sec.rows]
    assert ("prop", "data", "allset_renderable", "Renderable") in rows


def test_saved_options_run_on_a_plain_click():
    """Maya: a menu item runs with its option values once they were saved."""
    _clear()
    _fresh_out()
    scene = bpy.context.scene
    _camera("m1", 0.0)
    _camera("m2", 2.0)
    _tiny(scene, os.path.join(OUT, "menu_"), frames=1)
    ow.store("render_sequence", {"camera": "persp", "all_cameras": True, "output": ""})
    try:
        from_menu = import_module(kit.MODULE + ".marking.modal")
        from_menu.run_action(bpy.context, menu_map.MAP[PATH], path=PATH)
    finally:
        ow.store("render_sequence", None)
    assert _files(os.path.join(OUT, "m1")) == ["menu_0001.png"]
    assert _files(os.path.join(OUT, "m2")) == ["menu_0001.png"]


def test_renderable_values_survive_saving_and_opening():
    _clear()
    cam = _camera("keepOff", 0.0)
    cam.data.allset_renderable = False
    path = os.path.join(bpy.app.tempdir, "issue252_renderable.blend")
    bpy.ops.wm.save_as_mainfile(filepath=path)
    bpy.ops.wm.read_homefile(use_empty=True)
    bpy.ops.wm.open_mainfile(filepath=path)
    assert not bpy.data.objects["keepOff"].data.allset_renderable, "the Renderable choice is kept in the file"


def test_unregister_removes_the_properties():
    kit.disable()
    try:
        assert not hasattr(bpy.types.Camera, "allset_renderable")
        assert not hasattr(bpy.types.Scene, "allset_skip_existing")
        assert _idle()
    finally:
        kit.enable()
