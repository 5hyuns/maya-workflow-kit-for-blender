"""Step 152 (#101) lane B: Maya's default light for kit renders of a scene without lights, Render Settings > Render
Options > Enable Default Light, Render > Test Resolution, Render > Batch Render / Cancel / Show Batch Render.

Maya (Maya, Maya Software, ): a white directional light of intensity 1 from
the camera's view axis turned 25 deg up and 25 deg left, no shadows; any light node turns it off. Fresh scene, default
cube, persp at its factory direction (8x closer): top 76.8 / front 65.1 / side 10.0 of 255, background 0."""

import math
import os
import time
from importlib import import_module

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

import kit

dl = import_module(kit.MODULE + ".operators.default_light")
rb = import_module(kit.MODULE + ".operators.render_batch")
rp = import_module(kit.MODULE + ".operators.render_persp")
lights = import_module(kit.MODULE + ".operators.lights")
create = import_module(kit.MODULE + ".operators.create")
units = import_module(kit.MODULE + ".operators.units")
project = import_module(kit.MODULE + ".operators.project")
first_start = import_module(kit.MODULE + ".first_start")
preferences = import_module(kit.MODULE + ".preferences")
menu_map = import_module(kit.MODULE + ".ui.menu_map")
notices = import_module(kit.MODULE + ".ui.notices")
shelf_map = import_module(kit.MODULE + ".ui.shelf_map")
render_settings = import_module(kit.MODULE + ".ui.render_settings")
outliner = import_module(kit.MODULE + ".ui.outliner")
outliner_sets = import_module(kit.MODULE + ".ui.outliner_sets")

# Maya 2022 Software render, 8-bit, colour management on or off alike (output transform off): tmp/m152/m152d.json
MAYA = {"top": 76.84, "front": 65.12, "side": 10.0}
MAYA_DIFFUSE = 0.8          # lambert1 diffuse; the kit's lambert1 renders colour 0.5 without it (step 100)


def _clear():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for coll in (bpy.data.meshes, bpy.data.lights, bpy.data.cameras):
        for d in list(coll):
            coll.remove(d)
    bpy.context.scene.camera = None


def _small(sc, engine='BLENDER_WORKBENCH'):
    r = sc.render
    r.engine = engine
    r.resolution_x, r.resolution_y, r.resolution_percentage = 32, 18, 100
    r.filepath = os.path.join(bpy.app.tempdir, "step152_small.png")


class _Seen:
    """render_pre recorder: the scene's lights and resolution while a render runs (EXEC renders: main thread)."""

    def __init__(self):
        self.log = []

    def __call__(self, scene, *_a):
        r = scene.render
        self.log.append({"lights": [(o.name, o.type, bool(o.get(dl.MARK)), o.parent.name if o.parent else "",
                                     o.data.type, o.data.energy, o.data.use_shadow)
                                    for o in scene.objects if o.type == 'LIGHT'],
                         "res": (r.resolution_x, r.resolution_y, r.resolution_percentage)})

    def __enter__(self):
        bpy.app.handlers.render_pre.append(self)
        return self

    def __exit__(self, *_a):
        bpy.app.handlers.render_pre.remove(self)


def _render_frame(**kw):
    with _Seen() as seen:
        res = bpy.ops.allset.render_current_frame(**kw)
    assert res == {'FINISHED'}, res
    return seen.log


def _no_marked_data():
    assert not [o.name for o in bpy.data.objects if o.get(dl.MARK)], "default light object left behind"
    assert not [d.name for d in bpy.data.lights if d.get(dl.MARK)], "default light data left behind"


# --- default light ------------------------------------------------------------------------------------------------

def test_default_light_only_during_the_render():
    _clear()
    sc = bpy.context.scene
    _small(sc)
    create.create(bpy.context, 'CUBE')
    assert sc.allset_default_light is True, "Maya factory: Enable Default Light on"
    n_lights = len(bpy.data.lights)
    log = _render_frame()
    assert len(log) == 1 and len(log[0]["lights"]) == 1, log
    name, typ, marked, parent, ltype, energy, shadow = log[0]["lights"][0]
    assert (name, typ, marked, parent, ltype, shadow) == ("defaultLight", 'LIGHT', True, "persp", 'SUN', False), log
    assert math.isclose(energy, lights.power_factor('SUN', 0, 1.0), rel_tol=1e-6), energy      # Maya intensity 1
    _no_marked_data()
    assert len(bpy.data.lights) == n_lights
    assert not [o for o in sc.objects if o.type == 'LIGHT']


def test_light_direction_follows_the_camera_like_maya():
    """+Z of the sun (toward the light) = camera view axis turned 25 deg up, 25 deg left: camera space
    (-0.383, 0.423, 0.821), Maya fit (-0.384, 0.421, 0.819) from a turned plane (m152b.json)."""
    _clear()
    sc = bpy.context.scene
    cam = rp.persp_camera()
    cam.rotation_euler = (1.1, 0.2, 0.7)
    cam.location = (1, -2, 3)
    ob = dl.add(sc, cam)
    bpy.context.view_layer.update()
    try:
        toward = (ob.matrix_world.to_3x3() @ Vector((0, 0, 1))).normalized()
        local = (cam.matrix_world.to_3x3().inverted() @ toward).normalized()
        want = Vector((-0.383, 0.4226, 0.8214)).normalized()
        assert (local - want).length < 2e-3, local
        assert ob.hide_select and ob.parent == cam
    finally:
        dl.remove_all()
    _no_marked_data()


def test_scene_lights_turn_it_off():
    """Maya: a hidden light, an ambient light, a light outside defaultLightSet — any light node — turns it off."""
    _clear()
    sc = bpy.context.scene
    _small(sc)
    create.create(bpy.context, 'CUBE')
    lo = create.create(bpy.context, 'POINT_LIGHT')
    lo.hide_viewport = lo.hide_render = True
    log = _render_frame()
    assert [x[0] for x in log[0]["lights"]] == [lo.name], log
    assert not dl.needed(sc)
    _no_marked_data()


def test_enable_default_light_off():
    _clear()
    sc = bpy.context.scene
    _small(sc)
    create.create(bpy.context, 'CUBE')
    sc.allset_default_light = False
    try:
        log = _render_frame()
        assert log[0]["lights"] == [], log
    finally:
        sc.allset_default_light = True
    _no_marked_data()


def test_stray_default_lights_go_after_undo_and_load():
    _clear()
    sc = bpy.context.scene
    ob = dl.add(sc, rp.persp_camera())
    assert ob is not None
    for name in dl.HANDLERS:
        assert dl._stray in getattr(bpy.app.handlers, name), name
    dl._stray()             # = undo_post / redo_post / load_post
    _no_marked_data()
    # a render job running keeps it
    dl.add(sc, rp.persp_camera())
    dl._after.append(lambda: None)
    try:
        dl._stray()
        assert [o for o in bpy.data.objects if o.get(dl.MARK)], "kept while a kit render is pending"
    finally:
        dl.finish()
    _no_marked_data()


def test_outliner_and_default_light_set_skip_it():
    _clear()
    sc = bpy.context.scene
    create.create(bpy.context, 'CUBE')
    ob = dl.add(sc, rp.persp_camera())
    try:
        assert ob.name not in [r[1] for r in outliner.dag_rows(sc, False)]
        assert ob not in outliner_sets.default_set_members("defaultLightSet", sc)
        assert not dl.scene_has_lights(sc)
    finally:
        dl.remove_all()


def test_render_settings_common_has_enable_default_light():
    seen = []

    class Rec:
        use_property_split = enabled = False

        def __getattr__(self, name):
            return lambda *a, **kw: (seen.append((name, a, kw)) if name == "prop" else None) or (
                (self, self) if name == "panel" else self)

    render_settings.draw_common(Rec(), bpy.context)
    props = [(a[1], kw.get("text")) for n, a, kw in seen]
    assert ("allset_default_light", "Enable Default Light") in props, props


# --- Test Resolution ----------------------------------------------------------------------------------------------

def test_test_resolution_menu_and_render_size():
    _clear()
    sc = bpy.context.scene
    _small(sc)
    sc.render.resolution_x, sc.render.resolution_y = 960, 540
    labels = [e[1] if e else "-" for e in rb.menu_labels(sc)]
    assert labels == ["Camera Panel", "Render Settings (960x540)", "-", "10% Settings (96x54)", "25% Settings (240x135)",
                      "50% Settings (480x270)", "75% Settings (720x405)", "-", "110% Settings (1056x594)",
                      "125% Settings (1200x675)", "150% Settings (1440x810)"], labels
    assert menu_map.MAP["Render/Test Resolution"] == ("menu", "ALLSET_MT_test_resolution")
    prefs = preferences.get()
    assert prefs.test_resolution == "SETTINGS", "Maya default: Render Settings"
    create.create(bpy.context, 'CUBE')
    try:
        assert bpy.ops.allset.test_resolution(choice="25") == {'FINISHED'}
        assert prefs.test_resolution == "25"
        log = _render_frame()
        assert log[0]["res"] == (960, 540, 25), log
        assert (sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage) == (960, 540, 100)
        bpy.ops.allset.test_resolution(choice="150")
        assert _render_frame()[0]["res"] == (960, 540, 150)
        # the menu draws a check on the current choice
        rows = []

        class Rec:
            def operator(self, op, text="", icon=""):
                rows.append((text, icon))
                return type("P", (), {})()

            def separator(self):
                pass
        rb.ALLSET_MT_test_resolution.draw(type("M", (), {"layout": Rec()})(), bpy.context)
        assert [t for t, i in rows if i == 'CHECKBOX_HLT'] == ["150% Settings (1440x810)"], rows
    finally:
        prefs.test_resolution = "SETTINGS"
    assert _render_frame()[0]["res"] == (960, 540, 100)


def test_camera_panel_uses_the_view_size():
    _clear()
    sc = bpy.context.scene
    _small(sc)
    space, _rv3d = rp.find_view(bpy.context)
    region = rb._view_region(space) if space is not None else None
    restore = rb.scaled(bpy.context, "PANEL")
    r = sc.render
    try:
        if region is not None and region.width > 1:
            assert (r.resolution_x, r.resolution_y, r.resolution_percentage) == (region.width, region.height, 100)
    finally:
        restore()
    assert (r.resolution_x, r.resolution_y, r.resolution_percentage) == (32, 18, 100)


# --- Batch Render -------------------------------------------------------------------------------------------------

def test_batch_render_menu_items_mapped():
    m = menu_map.MAP
    assert m["Render/Batch Render"] == "allset.batch_render"
    assert m["Render/Cancel Batch Render"] == "allset.cancel_batch_render"
    assert m["Render/Show Batch Render"] == "allset.show_batch_render"
    assert shelf_map.BY_COMMAND["BatchRender"][0] == "allset.batch_render"
    assert "Render/Cancel Batch Render" not in notices.NOTICES


def test_batch_command_line_and_output():
    _clear()
    sc = bpy.context.scene
    sc.render.filepath = "/tmp\\"
    out = rb.output_path(sc)
    assert os.path.normpath(out) == os.path.join(project.current_root(), "images", "untitled"), out
    sc.render.filepath = "//shots/frame_####"
    assert rb.frame_args(sc) == ["-a"], (sc.render.filepath, rb.frame_args(sc))
    sc.render.filepath = "//shots/still"
    sc.frame_current = 7
    assert rb.frame_args(sc) == ["-f", "7"], (sc.render.filepath, rb.frame_args(sc))
    cmd = rb.command("C:/x/batch.blend", "C:/out/img", ["-a"])
    assert cmd == [bpy.app.binary_path, "-b", "C:/x/batch.blend", "-o", "C:/out/img", "-a"], cmd


def test_batch_copy_has_camera_and_light_open_file_unchanged():
    _clear()
    sc = bpy.context.scene
    create.create(bpy.context, 'CUBE')
    before = bpy.data.filepath
    path = rb.write_copy(bpy.context, sc)
    assert os.path.isfile(path) and bpy.data.filepath == before
    _no_marked_data()
    with bpy.data.libraries.load(path) as (src, dst):
        names = list(src.objects)
    assert "defaultLight" in names and "persp" in names, names


def test_batch_render_runs_cancel_and_show():
    _clear()
    sc = bpy.context.scene
    create.create(bpy.context, 'CUBE')
    sc.render.engine = 'CYCLES'
    if hasattr(sc, "cycles"):
        sc.cycles.samples = 4
        sc.cycles.use_denoising = False
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 64, 36, 100
    sc.render.image_settings.file_format = 'PNG'
    out_dir = os.path.join(bpy.app.tempdir, "step152_batch")
    sc.render.filepath = os.path.join(out_dir, "shot")
    cam = rp.persp_camera()
    cam.location = (0.0, -6.0, 4.0)
    cam.rotation_euler = (-cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.camera = cam
    assert bpy.ops.allset.show_batch_render() == {'CANCELLED'}, "nothing rendered yet"
    assert bpy.ops.allset.batch_render() == {'FINISHED'}
    proc = rb._batch["proc"]
    assert proc is not None and rb._batch["cmd"][-2:] == ["-f", str(sc.frame_current)], rb._batch["cmd"]
    proc.wait(timeout=180)
    assert proc.returncode == 0, open(rb._batch["log"], encoding="utf-8", errors="replace").read()[-2000:]
    img_path = rb.last_image()
    assert img_path and os.path.basename(img_path).startswith("shot"), (img_path, os.listdir(out_dir))
    assert bpy.ops.allset.show_batch_render() == {'FINISHED'}
    img = next(i for i in bpy.data.images if i.filepath and os.path.normpath(bpy.path.abspath(i.filepath))
               == os.path.normpath(img_path))
    w, h = img.size
    px = img.pixels[:]
    centre = sum(px[((h // 2) * w + w // 2) * 4 + c] for c in range(3)) / 3
    assert centre > 0.05, ("the batch copy carries the default light", centre)
    _no_marked_data()
    # Cancel: a long sequence, stopped at once
    sc.render.filepath = os.path.join(out_dir, "long_####")
    sc.frame_start, sc.frame_end = 1, 2000
    assert bpy.ops.allset.batch_render() == {'FINISHED'}
    assert rb.running()
    assert bpy.ops.allset.batch_render() == {'CANCELLED'}, "one batch at a time"
    t = time.time()
    assert bpy.ops.allset.cancel_batch_render() == {'FINISHED'}
    assert not rb.running() and time.time() - t < 10
    assert bpy.ops.allset.cancel_batch_render() == {'CANCELLED'}


# --- brightness against Maya (last: it loads the Maya Workflow Kit template) ----------------------------

def _face_values(path, cam, sc, k):
    img = bpy.data.images.load(path, check_existing=False)
    try:
        w, h = img.size
        px = img.pixels[:]
        out = {}
        for name, co in {"top": (0, 0, 0.5), "front": (0, -0.5, 0), "side": (0.5, 0, 0)}.items():
            u, v, _z = world_to_camera_view(sc, cam, Vector(co) * k)
            x, y = int(round(u * w)), int(round(v * h))
            vals = [px[((y + dy) * w + x + dx) * 4 + c] for dy in range(-2, 3) for dx in range(-2, 3) for c in range(3)]
            out[name] = sum(vals) / len(vals)
        return out
    finally:
        bpy.data.images.remove(img)


def _maya_view_render(engine=None, world=True):
    """Fresh Maya Workflow Kit scene (cm template), default cube, persp at factory direction 8x closer
    (Maya (3.5, 2.625, 3.5) units, 35 mm on 36 mm film), 640 x 360, Render Current Frame -> EXR (linear)."""
    first_start.new_maya_scene()
    win = bpy.context.window_manager.windows[0]
    with bpy.context.temp_override(window=win, screen=win.screen):
        return _maya_view_render_in(engine, world)


def _maya_view_render_in(engine, world):
    sc = bpy.context.scene
    k = units.maya_unit(sc)
    assert math.isclose(k, 0.01), k
    create.create(bpy.context, 'CUBE')
    cam = rp.persp_camera()
    cam.location = Vector((3.5, -3.5, 2.625)) * k                    # Maya Y-up -> Blender Z-up
    cam.rotation_euler = (-cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens, cam.data.sensor_width = 35.0, 36.0
    cam.data.clip_start, cam.data.clip_end = 0.1 * k, 1000 * k       # Maya persp near clip 0.1 units
    sc.camera = cam
    space, rv3d = rp.find_view(bpy.context)
    if rv3d is not None:
        rv3d.view_perspective = 'CAMERA'        # the view looks through persp: the render keeps its placement
        space.use_local_camera = False
    if engine:
        sc.render.engine = engine
    if sc.render.engine == 'CYCLES':
        sc.cycles.samples, sc.cycles.use_denoising = 32, False
    if not world:
        sc.world = None
    r = sc.render
    r.resolution_x, r.resolution_y, r.resolution_percentage = 640, 360, 100
    r.image_settings.file_format = 'OPEN_EXR'
    r.filepath = os.path.join(bpy.app.tempdir, f"step152_maya_{engine or 'template'}_{int(world)}.exr")
    _render_frame(write_still=True)
    _no_marked_data()
    return _face_values(r.filepath, cam, sc, k), r.engine


def test_cube_brightness_like_maya():
    """The light matches Maya: kit face value x 0.8 (Maya lambert1 diffuse, which the kit's lambert1 doesn't carry)
    = Maya's within 3 / 255 with no world; the template's grey world adds its ambient on top."""
    report = []
    for engine in (None, 'CYCLES'):
        for world in (False, True):
            vals, used = _maya_view_render(engine, world)
            got = {f: round(v * 255, 2) for f, v in vals.items()}
            report.append((used, world, got))
            print("STEP152_BRIGHTNESS", used, "world" if world else "no world", got,
                  {f: round(v * MAYA_DIFFUSE * 255, 2) for f, v in vals.items()}, MAYA)
            if not world:
                for face, maya in MAYA.items():
                    assert abs(vals[face] * MAYA_DIFFUSE * 255 - maya) < 3.0, (used, face, got, MAYA)
    assert report
