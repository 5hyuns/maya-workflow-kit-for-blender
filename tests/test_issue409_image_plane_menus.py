"""#409: the panel toolbar's Image Plane button has a right-click menu and the panel View menu an Image Plane
submenu, like Maya.

- View > Image Plane: Import Image..., Import Movie..., Image Plane Attributes (the image planes attached to the
  camera the view looks through: picking one selects it and shows it in the Attribute Editor; greyed when there is
  none).
- Right-click on the toolbar's Image Plane button: Import Image..., Display Mode (None / Outline / RGB / RGBA /
  Luminance / Alpha for the camera's first image plane: None hides it, RGBA shows it, the others have no Blender
  equivalent), Delete: <image plane>.
- Import Image... always adds an image (also when the camera already has one: the button itself shows / hides it).
"""

import math
import os
import tempfile
from importlib import import_module

import bpy
from mathutils import Euler

import kit

pmd = import_module(kit.MODULE + ".ui.panel_menu_data")
pt = import_module(kit.MODULE + ".ui.panel_toolbar")
notices = import_module(kit.MODULE + ".ui.notices")
ip = import_module(kit.MODULE + ".operators.image_plane")


def _png(w, h, name):
    path = os.path.join(tempfile.mkdtemp(prefix="mk409_"), name)
    img = bpy.data.images.new(name, w, h)
    img.filepath_raw = path
    img.file_format = 'PNG'
    img.save()
    bpy.data.images.remove(img)
    return path


def _view(persp='CAMERA', rot=(0.0, 0.0, 0.0)):
    window = bpy.context.window_manager.windows[0]
    area = max((a for a in window.screen.areas if a.type == 'VIEW_3D'), key=lambda a: a.width * a.height)
    region = next(r for r in area.regions if r.type == 'WINDOW')
    rv3d = area.spaces.active.region_3d
    rv3d.view_perspective = persp
    rv3d.view_rotation = Euler([math.radians(a) for a in rot]).to_quaternion()
    return window, area, region


def _run(view, op, how='EXEC_DEFAULT', **props):
    window, area, region = view
    mod, name = op.split(".")
    with bpy.context.temp_override(window=window, area=area, region=region):
        return getattr(getattr(bpy.ops, mod), name)(how, **props)


def _camera_with_plane():
    bpy.ops.wm.read_homefile()
    cam = bpy.data.objects["Camera"]
    bpy.context.scene.camera = cam
    view = _view('CAMERA')
    before = {ob.name for ob in bpy.data.objects}
    assert _run(view, "allset.image_plane", filepath=_png(64, 32, "a409.png")) == {'FINISHED'}
    plane = next(ob for ob in bpy.data.objects if ob.name not in before)
    return cam, view, plane


def test_view_menu_has_the_image_plane_submenu():
    labels = [r[1] for r in pmd.VIEW if r[0] != "sep" or r[1]]
    i = labels.index("Camera Tools")
    menu = next(r for r in pmd.VIEW if r[0] == "menu" and r[1] == "Image Plane")
    assert labels[i + 1] == "Image Plane", labels
    rows = pmd.MENUS[menu[2]][1]
    assert [r[1] for r in rows] == ["Import Image...", "Import Movie...", "Image Plane Attributes"], rows
    assert rows[0][0] == "run" and rows[0][2] == "allset.image_plane" and rows[0][3].get("import_image")
    assert rows[1][3].get("movie") and rows[1][3].get("import_image")
    assert hasattr(bpy.types, menu[2]) and hasattr(bpy.types, rows[2][2])


def test_the_toolbar_button_has_a_right_click_menu():
    menu = pt.RMB_MENUS.get("image_plane")
    assert menu and hasattr(bpy.types, menu), pt.RMB_MENUS
    display = pmd.MENUS["ALLSET_MT_pt_image_plane_display"][1]
    assert [r[1] for r in display] == ["None", "Outline", "RGB", "RGBA", "Luminance", "Alpha"], display
    greyed = [r[1] for r in display if r[0] == "grey"]
    assert greyed == ["Outline", "RGB", "Luminance", "Alpha"], greyed
    for label in greyed:
        assert notices.greyed_notice(pmd.item_path("ALLSET_MT_pt_image_plane_display", label)), label


def test_import_image_adds_one_more_plane_to_the_camera():
    cam, view, plane = _camera_with_plane()
    names = {ob.name for ob in bpy.data.objects}
    res = _run(view, "allset.image_plane", how='INVOKE_DEFAULT', import_image=True)
    assert not plane.hide_get(), "Import Image never hides the camera's plane"
    assert res != {'FINISHED'} or {ob.name for ob in bpy.data.objects} != names, res
    assert _run(view, "allset.image_plane", import_image=True, filepath=_png(32, 32, "b409.png")) == {'FINISHED'}
    new = [ob for ob in bpy.data.objects if ob.name not in names]
    assert len(new) == 1 and new[0].parent == cam, [o.name for o in new]
    assert [p.name for p in ip.view_planes(bpy.context, cam.name)] == [plane.name, new[0].name]


def test_display_mode_none_hides_and_rgba_shows_the_first_plane():
    _cam, view, plane = _camera_with_plane()
    assert _run(view, "allset.image_plane_display", mode='NONE') == {'FINISHED'}
    assert plane.hide_get()
    assert _run(view, "allset.image_plane_display", mode='RGBA') == {'FINISHED'}
    assert not plane.hide_get()


def test_delete_removes_the_first_plane():
    cam, view, plane = _camera_with_plane()
    name = plane.name
    assert _run(view, "allset.image_plane_delete") == {'FINISHED'}
    assert name not in bpy.data.objects and not ip.view_planes(bpy.context, cam.name)
    assert _run(view, "allset.image_plane_display", mode='NONE') == {'CANCELLED'}, "no plane left"


def test_image_plane_attributes_selects_the_plane():
    cam, view, plane = _camera_with_plane()
    bpy.ops.object.select_all(action='DESELECT')
    cam.select_set(True)
    window, area, region = view
    with bpy.context.temp_override(window=window, area=area, region=region):
        res = bpy.ops.allset.image_plane_attributes(name=plane.name)
    assert res == {'FINISHED'}, res
    assert plane.select_get() and not cam.select_get()
    assert bpy.context.view_layer.objects.active == plane


def test_import_movie_plays_a_movie_on_the_plane():
    """Import Movie...: a movie file becomes an image plane whose picture follows the frame."""
    _camera_with_plane()
    scene = bpy.context.scene
    out = os.path.join(tempfile.mkdtemp(prefix="mk409m_"), "clip409.mp4")
    r = scene.render
    r.resolution_x, r.resolution_y, r.resolution_percentage = 64, 32, 100
    scene.frame_start, scene.frame_end = 1, 3
    if hasattr(r.image_settings, "media_type"):
        r.image_settings.media_type = 'VIDEO'
    r.image_settings.file_format = 'FFMPEG'
    r.ffmpeg.format = 'MPEG4'
    r.ffmpeg.codec = 'H264'
    r.filepath = out
    scene.render.engine = 'BLENDER_WORKBENCH'
    bpy.ops.render.render(animation=True)
    movie = next((os.path.join(os.path.dirname(out), f) for f in os.listdir(os.path.dirname(out))), None)
    if movie is None:
        raise kit.Skip("this Blender wrote no movie file")
    view = _view('CAMERA')
    names = {ob.name for ob in bpy.data.objects}
    assert _run(view, "allset.image_plane", import_image=True, movie=True, filepath=movie) == {'FINISHED'}
    new = [ob for ob in bpy.data.objects if ob.name not in names]
    assert len(new) == 1 and new[0].data is not None and new[0].data.source == 'MOVIE', new
    iu = new[0].image_user
    assert iu.use_auto_refresh and iu.frame_duration >= 3, (iu.use_auto_refresh, iu.frame_duration)
