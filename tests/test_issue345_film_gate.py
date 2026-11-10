"""Issue #345: the camera gates match the render, like Maya.

Maya: the resolution gate is the render frame and the film gate is the film back (Horizontal x Vertical Film
Aperture); Fit Resolution Gate places one on the other (Fill: the resolution gate fits inside the film gate,
Horizontal / Vertical: as wide / as tall, Overscan: the film gate fits inside the resolution gate). Cameras have a
36 x 24 mm film back; a Create > Cameras camera starts with Fill, a new scene's cameras with Horizontal.

In the kit Blender's camera frame is the resolution gate (it is what renders) and Blender's sensor frame is the Film
Gate. The kit sets Blender's Sensor Fit from the camera's Fit Resolution Gate, so the render frame has Maya's size on
the film back, and the sensor frame (drawn from Sensor Width x Height for a Horizontal / Vertical fit; a square of
Sensor Width for Auto) is Maya's film gate on it. The drawn gates are read from the screen in
tests/gui/gui_issue345_film_gate.py."""

import os
import tempfile
from importlib import import_module

import bpy
import numpy as np
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

import kit

try:
    ff = import_module(kit.MODULE + ".operators.film_fit")
except ImportError:          # a kit without Fit Resolution Gate: the checks below fail on what it renders / draws
    ff = None
ae = import_module(kit.MODULE + ".ui.ae_layout")
startup_cameras = import_module(kit.MODULE + ".operators.startup_cameras")
render_persp = import_module(kit.MODULE + ".operators.render_persp")

RESOLUTIONS = {"16:9": (1920, 1080), "4:3": (1440, 1080), "1:1": (1080, 1080), "9:16": (1080, 1920),
               "2.39:1": (2048, 858)}


def _scene(res=(1920, 1080), pixel_aspect=(1.0, 1.0)):
    sc = bpy.context.scene
    r = sc.render
    r.resolution_x, r.resolution_y = res
    r.resolution_percentage = 100
    r.pixel_aspect_x, r.pixel_aspect_y = pixel_aspect
    return sc


def _clean():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for cam in list(bpy.data.cameras):
        bpy.data.cameras.remove(cam)


def _new_camera():
    """Create > Cameras > Camera."""
    assert bpy.ops.allset.create(kind='CAMERA') == {'FINISHED'}
    cam = bpy.context.view_layer.objects.active
    assert cam is not None and cam.type == 'CAMERA'
    return cam


def frame_mm(data, scene):
    """Size and centre of Blender's camera frame (the render) on the film back, in mm (perspective camera)."""
    pts = data.view_frame(scene=scene)
    k = data.lens / abs(pts[0].z)
    xs, ys = [p.x * k for p in pts], [p.y * k for p in pts]
    return (max(xs) - min(xs), max(ys) - min(ys)), (sum(xs) / 4, sum(ys) / 4)


def sensor_frame_mm(data, scene):
    """Blender's sensor frame (the kit's Film Gate) in mm on the film back, for the frame ``frame_mm`` gives: drawn
    from Sensor Width x Height placed by the fitted side, or a square of Sensor Width for Auto."""
    (fw, fh), _c = frame_mm(data, scene)
    aspect = render_aspect(scene)
    sx = data.sensor_width
    sy = data.sensor_width if data.sensor_fit == 'AUTO' else data.sensor_height
    side = data.sensor_fit if data.sensor_fit != 'AUTO' else ('HORIZONTAL' if aspect >= 1.0 else 'VERTICAL')
    return (fw, fw * sy / sx) if side == 'HORIZONTAL' else (fh * sx / sy, fh)


def _close(a, b, tol=1e-3):
    return all(abs(x - y) <= tol for x, y in zip(a, b))


def render_aspect(scene):
    r = scene.render
    return (r.resolution_x * r.pixel_aspect_x) / (r.resolution_y * r.pixel_aspect_y)


def maya_gates(hfa, vfa, fit, aspect):
    """Maya's rule: ((resolution gate w, h), (film gate w, h)) on the film back."""
    film = hfa / vfa
    if fit == 'FILL':
        fit = 'HORIZONTAL' if aspect >= film else 'VERTICAL'
    elif fit == 'OVERSCAN':
        fit = 'VERTICAL' if aspect >= film else 'HORIZONTAL'
    return ((hfa, hfa / aspect) if fit == 'HORIZONTAL' else (vfa * aspect, vfa)), (hfa, vfa)


def sync(scene):
    """What the kit runs when the render size or the film back changes (msgbus; background mode has none)."""
    return ff.sync(scene) if ff is not None else []


def film_fit(data):
    return getattr(data, "allset_film_fit", None)


# --- Maya's rule -------------------------------------------------------------------------------------------------

def test_maya_fit_rule():
    assert ff is not None, "the kit has no Fit Resolution Gate"
    film = 36.0 / 24.0
    assert ff.fitted_side('FILL', film, 16 / 9) == 'HORIZONTAL'
    assert ff.fitted_side('FILL', film, 4 / 3) == 'VERTICAL'
    assert ff.fitted_side('FILL', film, 1.5) == 'HORIZONTAL'          # the film back's own shape: both sides touch
    assert ff.fitted_side('OVERSCAN', film, 16 / 9) == 'VERTICAL'
    assert ff.fitted_side('OVERSCAN', film, 4 / 3) == 'HORIZONTAL'
    assert ff.fitted_side('HORIZONTAL', film, 4 / 3) == 'HORIZONTAL'
    assert ff.fitted_side('VERTICAL', film, 16 / 9) == 'VERTICAL'
    # gates on a 36 x 24 film back
    assert _close(maya_gates(36, 24, 'FILL', 16 / 9)[0], (36.0, 20.25))
    assert _close(maya_gates(36, 24, 'FILL', 4 / 3)[0], (32.0, 24.0))
    assert _close(maya_gates(36, 24, 'FILL', 1.0)[0], (24.0, 24.0))
    assert _close(maya_gates(36, 24, 'FILL', 9 / 16)[0], (13.5, 24.0))
    assert _close(maya_gates(36, 24, 'OVERSCAN', 16 / 9)[0], (42.6667, 24.0))
    assert _close(maya_gates(36, 24, 'OVERSCAN', 4 / 3)[0], (36.0, 27.0))
    assert maya_gates(36, 24, 'FILL', 4 / 3)[1] == (36, 24)
    # Fill: the resolution gate is inside the film gate; Overscan: the film gate is inside the resolution gate
    for aspect in (0.5, 9 / 16, 1.0, 4 / 3, 1.5, 16 / 9, 2.39):
        (rw, rh), (gw, gh) = maya_gates(36, 24, 'FILL', aspect)
        assert rw <= gw + 1e-6 and rh <= gh + 1e-6 and (abs(rw - gw) < 1e-6 or abs(rh - gh) < 1e-6), aspect
        (rw, rh), (gw, gh) = maya_gates(36, 24, 'OVERSCAN', aspect)
        assert rw >= gw - 1e-6 and rh >= gh - 1e-6 and (abs(rw - gw) < 1e-6 or abs(rh - gh) < 1e-6), aspect


# --- a new camera ------------------------------------------------------------------------------------------------

def test_new_camera_is_a_maya_camera():
    _clean()
    sc = _scene()
    cam = _new_camera().data
    assert (cam.lens, cam.sensor_width, cam.sensor_height) == (35.0, 36.0, 24.0)
    assert cam.allset_film_fit == 'FILL', cam.allset_film_fit
    assert cam.sensor_fit == 'HORIZONTAL', cam.sensor_fit      # 16:9 is wider than the 3:2 film back
    (fw, fh), _c = frame_mm(cam, sc)
    assert _close((fw, fh), (36.0, 20.25)), (fw, fh)


def test_render_frame_and_film_gate_follow_maya_for_each_shape():
    """The render frame is Maya's resolution gate and the drawn film gate is Maya's film gate on it, for Fill,
    Horizontal, Vertical and Overscan and each render shape (the kit sets Sensor Fit again when the size changes)."""
    _clean()
    sc = _scene()
    cam = _new_camera().data
    bad = []
    for fit in ('FILL', 'HORIZONTAL', 'VERTICAL', 'OVERSCAN'):
        cam.allset_film_fit = fit
        for vfa in (24.0, 20.25, 30.0):
            cam.sensor_height = vfa
            for name, res in RESOLUTIONS.items():
                _scene(res)
                sync(sc)                 # what the kit's msgbus callback runs after a size change
                aspect = res[0] / res[1]
                (rw, rh), (gw, gh) = maya_gates(36.0, vfa, fit, aspect)
                got_frame, centre = frame_mm(cam, sc)
                got_gate = sensor_frame_mm(cam, sc)
                if cam.allset_film_fit != fit or not _close(got_frame, (rw, rh), 0.01) \
                        or not _close(got_gate, (gw, gh), 0.01) or not _close(centre, (0, 0), 1e-4):
                    bad.append((fit, vfa, name, cam.allset_film_fit, cam.sensor_fit, got_frame, (rw, rh), got_gate,
                                (gw, gh)))
    assert not bad, bad[:6]


def test_film_back_with_the_render_shape_gives_one_gate():
    """A film back with the render's width : height: the film gate and the resolution gate are the same rectangle
    (the report: 'film gate and resolution do not match')."""
    _clean()
    sc = _scene((1920, 1080))
    cam = _new_camera().data
    cam.sensor_height = 36.0 * 1080 / 1920
    (fw, fh), _c = frame_mm(cam, sc)
    assert _close(sensor_frame_mm(cam, sc), (fw, fh), 1e-3), (sensor_frame_mm(cam, sc), (fw, fh))


def test_pixel_aspect_and_film_offset():
    _clean()
    sc = _scene((1000, 1080), pixel_aspect=(2.0, 1.0))      # anamorphic pixels: 1.85 : 1 on screen
    cam = _new_camera().data
    sync(sc)
    aspect = 2000 / 1080
    (rw, rh), (gw, gh) = maya_gates(36.0, 24.0, 'FILL', aspect)
    got, _c = frame_mm(cam, sc)
    assert _close(got, (rw, rh), 0.01), (got, (rw, rh))
    # Film Offset (Blender shift) moves both gates together: the film gate keeps its place on the resolution gate
    cam.shift_x, cam.shift_y = 0.1, -0.05
    got2, centre = frame_mm(cam, sc)
    assert _close(got2, got, 1e-3) and abs(centre[0]) > 1.0 and abs(centre[1]) > 0.5, (got2, centre)
    assert _close(sensor_frame_mm(cam, sc), (gw, gh), 0.01)


def test_render_puts_objects_where_the_resolution_gate_does():
    """A marker at a known place of Maya's resolution gate renders there (Workbench, a small image), for 16:9, 4:3
    and 9:16 with a new camera (Fill)."""
    _clean()
    sc = _scene()
    cam_ob = _new_camera()
    cam_ob.location, cam_ob.rotation_euler = (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)     # looks down -Z
    sc.camera = cam_ob
    cam = cam_ob.data
    r = sc.render
    r.engine = 'BLENDER_WORKBENCH'
    sh = sc.display.shading
    sh.light, sh.color_type, sh.single_color = 'FLAT', 'SINGLE', (1.0, 1.0, 1.0)
    if sc.world is None:
        sc.world = bpy.data.worlds.new("World")
    sc.world.color = (0.0, 0.0, 0.0)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.08, segments=12, ring_count=8)
    mark = bpy.context.active_object
    want_uv = (0.75, 0.70)
    out = os.path.join(tempfile.mkdtemp(prefix="t345_"), "r.png")
    for res in ((1920, 1080), (1440, 1080), (1080, 1920)):
        _scene(res)
        sync(sc)
        (rw, rh), _film = maya_gates(36.0, 24.0, 'FILL', res[0] / res[1])
        depth = 6.0
        mark.location = Vector(((want_uv[0] - 0.5) * rw * depth / cam.lens, (want_uv[1] - 0.5) * rh * depth / cam.lens,
                                -depth))
        bpy.context.view_layer.update()
        p = world_to_camera_view(sc, cam_ob, mark.location)
        assert _close((p.x, p.y), want_uv, 1e-3), (res, tuple(p))
        r.resolution_percentage = 10
        bpy.ops.render.render(write_still=False)
        r.resolution_percentage = 100
        bpy.data.images["Render Result"].save_render(out)
        im = bpy.data.images.load(out, check_existing=False)
        w, h = im.size
        pix = np.empty(w * h * 4, dtype=np.float32)
        im.pixels.foreach_get(pix)
        bpy.data.images.remove(im)
        ys, xs = np.nonzero(pix.reshape(h, w, 4)[:, :, 0] > 0.5)
        assert len(xs), res
        got = ((xs.mean() + 0.5) / w, (ys.mean() + 0.5) / h)
        assert _close(got, want_uv, 0.02), (res, got)


# --- keeping the fit ---------------------------------------------------------------------------------------------

def test_size_change_keeps_fill_and_overscan():
    _clean()
    sc = _scene((1920, 1080))
    cam = _new_camera().data
    assert cam.sensor_fit == 'HORIZONTAL'
    _scene((1080, 1920))
    assert sync(sc) == [cam] and cam.sensor_fit == 'VERTICAL' and cam.allset_film_fit == 'FILL'
    cam.allset_film_fit = 'OVERSCAN'
    assert cam.sensor_fit == 'HORIZONTAL' and cam.allset_film_fit == 'OVERSCAN'
    _scene((1920, 1080))
    sync(sc)
    assert cam.sensor_fit == 'VERTICAL' and cam.allset_film_fit == 'OVERSCAN'
    # a film back change can flip the fitted side too (a 2:1 film back is wider than 16:9)
    cam.allset_film_fit = 'FILL'
    cam.sensor_height = 18.0
    sync(sc)
    assert cam.sensor_fit == 'VERTICAL' and cam.allset_film_fit == 'FILL'
    # Horizontal / Vertical don't follow the render's shape
    cam.allset_film_fit = 'HORIZONTAL'
    _scene((1080, 1920))
    assert sync(sc) == [] and cam.sensor_fit == 'HORIZONTAL' and cam.allset_film_fit == 'HORIZONTAL'


def test_blender_sensor_fit_wins_and_other_cameras_stay():
    _clean()
    sc = _scene((1920, 1080))
    cam = _new_camera().data
    cam.sensor_fit = 'VERTICAL'               # changed in Blender's camera properties
    assert cam.allset_film_fit == 'VERTICAL'
    _scene((1080, 1920))
    sync(sc)
    assert cam.sensor_fit == 'VERTICAL' and cam.allset_film_fit == 'VERTICAL'
    cam.sensor_fit = 'HORIZONTAL'             # back to the side Fill had: still Blender's own choice
    _scene((1920, 1080))
    sync(sc)
    assert cam.allset_film_fit == 'HORIZONTAL'
    # a camera the kit didn't make keeps Blender's Auto until a fit is picked for it
    other = bpy.data.cameras.new("blenderCam")
    assert other.sensor_fit == 'AUTO' and other.allset_film_fit == 'AUTO'
    _scene((1440, 1080))
    sync(sc)
    assert other.sensor_fit == 'AUTO'
    other.allset_film_fit = 'FILL'
    assert other.sensor_fit == 'VERTICAL' and other.allset_film_fit == 'FILL'
    other.allset_film_fit = 'AUTO'
    assert other.sensor_fit == 'AUTO' and other.allset_film_fit == 'AUTO'


def test_load_and_kit_render_set_the_fit_again():
    """After a file load (the render size may have changed while the kit was off) and before a kit render."""
    _clean()
    sc = _scene((1920, 1080))
    cam_ob = _new_camera()
    cam = cam_ob.data
    _scene((1440, 1080))                      # no msgbus in background mode: nothing has set the fit yet
    assert cam.sensor_fit == 'HORIZONTAL'
    ff._on_load()
    assert cam.sensor_fit == 'VERTICAL'
    _scene((1920, 1080))
    sc.camera = cam_ob
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.render.resolution_percentage = 5
    assert bpy.ops.allset.render() == {'FINISHED'}
    assert cam.sensor_fit == 'HORIZONTAL'
    sc.render.resolution_percentage = 100


def _ortho_frame(data, scene):
    """Width, height of an orthographic camera's render frame (scene units)."""
    pts = data.view_frame(scene=scene)
    xs, ys = [p.x for p in pts], [p.y for p in pts]
    return max(xs) - min(xs), max(ys) - min(ys)


def test_menu_cameras_start_with_fill():
    """Create > Cameras > Camera / Camera and Aim / Camera, Aim and Up start with Fill, like Maya's menu."""
    _clean()
    _scene((1440, 1080))
    for kind in ('CAMERA', 'CAMERA_AIM', 'CAMERA_AIM_UP'):
        before = set(bpy.data.cameras)
        assert bpy.ops.allset.create(kind=kind) == {'FINISHED'}
        new = [c for c in bpy.data.cameras if c not in before]
        assert len(new) == 1, (kind, new)
        assert new[0].allset_film_fit == 'FILL', (kind, new[0].allset_film_fit)
        assert new[0].sensor_fit == 'VERTICAL', kind                        # 4:3 is narrower than 3:2


def test_new_scene_cameras_start_with_horizontal():
    """The persp / top / front / side cameras of a new scene start with Horizontal, like Maya: the render is as
    wide as the film back (persp) or the orthographic width (top / front / side) whatever its shape."""
    _clean()
    sc = _scene((1440, 1080))
    made = startup_cameras.ensure(sc, bpy.context.view_layer)
    assert [c.name for c in made] == ["persp", "top", "front", "side"]
    unit = startup_cameras.units.maya_unit(sc)
    for res, persp_mm, ortho_wh in (((1440, 1080), (36.0, 27.0), (30.0, 22.5)),
                                    ((1080, 1080), (36.0, 36.0), (30.0, 30.0)),
                                    ((1080, 1920), (36.0, 64.0), (30.0, 160.0 / 3.0)),
                                    ((1920, 1080), (36.0, 20.25), (30.0, 16.875))):
        _scene(res)
        sync(sc)
        for scene_cam in made:
            data = scene_cam.data
            assert data.allset_film_fit == 'HORIZONTAL', (res, scene_cam.name, data.allset_film_fit)
            assert data.sensor_fit == 'HORIZONTAL', (res, scene_cam.name)
            assert (data.sensor_width, data.sensor_height) == (36.0, 24.0)
            if data.type == 'PERSP':
                got, _c = frame_mm(data, sc)
                assert _close(got, persp_mm, 0.01), (res, scene_cam.name, got, persp_mm)
            else:
                w, h = _ortho_frame(data, sc)
                assert _close((w / unit, h / unit), ortho_wh, 0.01), (res, scene_cam.name, (w, h), ortho_wh)


def test_render_persp_command_and_panel_cameras_start_with_horizontal():
    """The persp camera the kit makes for a render, the camera command and Panels > Perspective / Orthographic >
    New start with Horizontal, like a new scene's cameras."""
    _clean()
    sc = _scene((1440, 1080))
    persp = render_persp.persp_camera(create=True)
    assert persp.data.allset_film_fit == 'HORIZONTAL' and persp.data.sensor_fit == 'HORIZONTAL'
    cmds = import_module(kit.MODULE + ".command_line.cmds_shim")
    shape = cmds.camera()[1]
    data = next(o for o in bpy.data.objects if o.type == 'CAMERA' and o.data.name == shape).data
    assert data.allset_film_fit == 'HORIZONTAL', data.allset_film_fit
    assert _close(frame_mm(data, sc)[0], (36.0, 27.0), 0.01)
    win = bpy.context.window_manager.windows[0]
    area = next(a for a in win.screen.areas if a.type == 'VIEW_3D')
    region = next(r for r in area.regions if r.type == 'WINDOW')
    with bpy.context.temp_override(window=win, area=area, region=region):
        assert bpy.ops.allset.panel_new_persp() == {'FINISHED'}
        new_persp = bpy.context.view_layer.objects.active
        assert bpy.ops.allset.panel_new_ortho(kind='top') == {'FINISHED'}
        new_top = bpy.context.view_layer.objects.active
    for ob in (new_persp, new_top):
        assert ob.data.allset_film_fit == 'HORIZONTAL', (ob.name, ob.data.allset_film_fit)


def test_older_cameras_keep_auto():
    """A camera from before the kit had Fit Resolution Gate keeps Blender's Auto: loads, undo and kit renders
    don't change it."""
    _clean()
    sc = _scene((1440, 1080))
    old = bpy.data.cameras.new("oldShape")
    old.sensor_width = 36.0
    assert old.allset_film_fit == 'AUTO'
    ff._on_load()
    ff._on_undo()
    sync(sc)
    assert old.sensor_fit == 'AUTO' and old.allset_film_fit == 'AUTO'


def test_attribute_editor_row():
    rows = [row for sec in ae.CAMERA if sec.name == "Film Back" for row in sec.rows]
    assert ("prop", "data", "allset_film_fit", "Fit Resolution Gate") in rows, rows
    assert not any(row[2] == "sensor_fit" for row in rows if row[0] == "prop")
    items = [it.identifier for it in bpy.types.Camera.bl_rna.properties["allset_film_fit"].enum_items]
    assert items[:4] == ['FILL', 'HORIZONTAL', 'VERTICAL', 'OVERSCAN'], items
