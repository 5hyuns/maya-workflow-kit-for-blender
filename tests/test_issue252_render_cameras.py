"""Render Sequence with All Render-Enabled Cameras, the camera Renderable check and Skip existing frames
(operators/render_cameras.py)."""

import os
import shutil
from importlib import import_module

import bpy

import kit

rc = import_module(kit.MODULE + ".operators.render_cameras")
rp = import_module(kit.MODULE + ".operators.render_persp")
ow = import_module(kit.MODULE + ".operators.option_windows")
startup = import_module(kit.MODULE + ".operators.startup_cameras")
render_settings = import_module(kit.MODULE + ".ui.render_settings")
ae_layout = import_module(kit.MODULE + ".ui.ae_layout")

OUT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(kit.__file__)), "..", "tmp", "test_env",
                                    "issue252"))


def _clear():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    bpy.context.scene.camera = None


def _camera(name, x):
    ob = bpy.data.objects.new(name, bpy.data.cameras.new(name + "Shape"))
    bpy.context.scene.collection.objects.link(ob)
    ob.location = (x, -10.0, 0.0)
    ob.rotation_euler = (1.5708, 0.0, 0.0)
    return ob


def _tiny(scene, path):
    scene.render.engine = 'BLENDER_WORKBENCH'
    scene.render.resolution_x = scene.render.resolution_y = 16
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.frame_start, scene.frame_end, scene.frame_step = 1, 2, 1
    scene.render.filepath = path


def _fresh_out():
    shutil.rmtree(OUT, ignore_errors=True)
    os.makedirs(OUT, exist_ok=True)


def test_renderable_check_defaults_and_storage():
    _clear()
    cam = _camera("shotCam", 0.0)
    assert cam.data.allset_renderable, "new cameras are renderable"
    cam.data.allset_renderable = False
    assert not cam.data.allset_renderable and not rc.is_renderable(cam)
    cam.data.allset_renderable = True
    assert rc.is_renderable(cam)


def test_startup_cameras_only_persp_renderable():
    _clear()
    made = startup.ensure(bpy.context.scene)
    on = {ob.name for ob in made if ob.data.allset_renderable}
    assert on == {"persp"}, on
    other = _camera("shotCam", 0.0)
    assert [ob.name for ob in rc.renderable_cameras(bpy.context.scene)] == ["persp", other.name]


def test_camera_output_paths():
    assert rc.camera_output("//render/scene_", "camFront") == "//render/camFront/scene_"
    assert rc.camera_output("C:\\out\\", "camSide") == "C:\\out\\camSide\\"
    assert rc.camera_output("shot", "cam") == "cam/shot"
    assert rc.folder_name("ns:cam|a") == "ns_cam_a"


def test_plan_one_camera_keeps_the_output():
    _clear()
    a = _camera("camA", 0.0)
    b = _camera("camB", 2.0)
    b.data.allset_renderable = False
    assert rc.plan(bpy.context.scene, "//r/s_") == [(a, "//r/s_")]
    b.data.allset_renderable = True
    assert rc.plan(bpy.context.scene, "//r/s_") == [(a, "//r/camA/s_"), (b, "//r/camB/s_")]


def test_all_render_enabled_cameras_renders_each_into_its_folder():
    _clear()
    _fresh_out()
    scene = bpy.context.scene
    bpy.ops.mesh.primitive_cube_add(size=2.0)
    a, b = _camera("camFront", 0.0), _camera("camSide", 3.0)
    off = _camera("camOff", 6.0)
    off.data.allset_renderable = False
    keep = scene.camera = off
    base = os.path.join(OUT, "scene_")
    _tiny(scene, base)
    assert bpy.ops.allset.render_sequence(all_cameras=True) == {'FINISHED'}
    for name in ("camFront", "camSide"):
        files = sorted(os.listdir(os.path.join(OUT, name)))
        assert files == ["scene_0001.png", "scene_0002.png"], (name, files)
    assert not os.path.exists(os.path.join(OUT, "camOff"))
    # settings come back, no default light left behind
    assert scene.render.filepath == base and scene.camera == keep
    assert not any(o.get("allset_default_light") for o in bpy.data.objects)
    assert (a.name, b.name) == ("camFront", "camSide")


def test_alternate_output_with_all_cameras():
    _clear()
    _fresh_out()
    scene = bpy.context.scene
    _camera("c1", 0.0)
    _camera("c2", 2.0)
    _tiny(scene, os.path.join(OUT, "elsewhere", "img_"))
    alt = os.path.join(OUT, "alt")
    assert bpy.ops.allset.render_sequence(all_cameras=True, output=alt) == {'FINISHED'}
    assert sorted(os.listdir(os.path.join(alt, "c1"))) == ["img_0001.png", "img_0002.png"]
    assert sorted(os.listdir(os.path.join(alt, "c2"))) == ["img_0001.png", "img_0002.png"]
    assert not os.path.exists(os.path.join(OUT, "elsewhere"))


def test_no_renderable_camera_cancels():
    _clear()
    cam = _camera("only", 0.0)
    cam.data.allset_renderable = False
    try:
        res = bpy.ops.allset.render_sequence(all_cameras=True)
    except RuntimeError:
        res = {'CANCELLED'}
    assert res == {'CANCELLED'}


def test_current_camera_mode_unchanged():
    _clear()
    _fresh_out()
    scene = bpy.context.scene
    _camera("c1", 0.0)
    two = _camera("c2", 2.0)
    _tiny(scene, os.path.join(OUT, "cur_"))
    assert bpy.ops.allset.render_sequence(camera="c2") == {'FINISHED'}
    assert scene.camera == two
    assert sorted(f for f in os.listdir(OUT) if f.startswith("cur_")) == ["cur_0001.png", "cur_0002.png"]


def test_skip_existing_frames_maps_to_overwrite_and_placeholders():
    scene = bpy.context.scene
    r = scene.render
    r.use_overwrite, r.use_placeholder = True, False
    assert not scene.allset_skip_existing
    scene.allset_skip_existing = True
    assert (r.use_overwrite, r.use_placeholder) == (False, True)
    scene.allset_skip_existing = False
    assert (r.use_overwrite, r.use_placeholder) == (True, False)


def test_skip_existing_frames_leaves_rendered_frames():
    _clear()
    _fresh_out()
    scene = bpy.context.scene
    _camera("cam", 0.0)
    _tiny(scene, os.path.join(OUT, "skip_"))
    first = os.path.join(OUT, "skip_0001.png")
    with open(first, "wb") as f:
        f.write(b"kept")
    scene.allset_skip_existing = True
    try:
        assert bpy.ops.allset.render_sequence(all_cameras=True) == {'FINISHED'}
    finally:
        scene.allset_skip_existing = False
    with open(first, "rb") as f:
        assert f.read() == b"kept", "an existing frame is not rendered again"
    assert os.path.getsize(os.path.join(OUT, "skip_0002.png")) > 4


def test_window_menu_and_panels():
    w = next(w for w in ow.WINDOWS if w.key == "render_sequence")
    names = [f.name for f in w.fields]
    assert names == ["camera", "all_cameras", "output"], names
    assert "All Render-Enabled Cameras" not in w.missing
    rows = [r for sec in ae_layout.CAMERA if sec.name == "Output Settings" for r in sec.rows]
    assert ("prop", "data", "allset_renderable", "Renderable") in rows
    seen = []

    class Rec:
        use_property_split = enabled = False

        def __getattr__(self, name):
            return lambda *a, **kw: (seen.append((name, a, kw)) if name == "prop" else None) or (
                (self, self) if name == "panel" else self)

    _clear()
    _camera("shotCam", 0.0)
    render_settings.draw_common(Rec(), bpy.context)
    props = [(a[1], kw.get("text")) for n, a, kw in seen]
    assert ("allset_skip_existing", "Skip existing frames") in props, props
    assert ("allset_renderable", "shotCam") in props, props
