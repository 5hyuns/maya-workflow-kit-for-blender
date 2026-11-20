"""#398: the viewport panel toolbar's Image Plane button, like Maya.

- A view without an image plane: the button picks an image file and makes an image plane showing it (Maya's
  Import Image). An orthographic view's plane faces that view at the origin (top: facing up), a camera's plane is
  attached to the camera in front of it and fills its view, Blender's own perspective view gets one facing the view
  at its centre. The plane is as wide as the image's pixel width / 100 (Maya length units).
- A camera view whose camera has one: the button shows / hides that image plane, no new object. The top / front /
  side planes (and those of Blender's own views) aren't tied to the view: every click imports another image.
- Create > Free Image Plane stays a plane with no image facing the front, like Maya.
"""

import math
import os
import tempfile
from importlib import import_module

import bpy
from mathutils import Euler, Vector

import kit

pmd = import_module(kit.MODULE + ".ui.panel_menu_data")
units = import_module(kit.MODULE + ".operators.units")
sc = import_module(kit.MODULE + ".operators.startup_cameras")
ip = import_module(kit.MODULE + ".operators.image_plane")

EPS = 1e-4


def _row():
    return next(item for group in pmd.TOOLBAR for item in group if item[3] == "Image Plane")


def _png(w, h, name):
    path = os.path.join(tempfile.mkdtemp(prefix="mk398_"), name)
    img = bpy.data.images.new(name, w, h)
    img.filepath_raw = path
    img.file_format = 'PNG'
    img.save()
    bpy.data.images.remove(img)
    return path


def _view(persp='ORTHO', rot=(0.0, 0.0, 0.0)):
    """The largest 3D View of the window, set to ``persp`` looking with Euler ``rot`` (degrees)."""
    window = bpy.context.window_manager.windows[0]
    area = max((a for a in window.screen.areas if a.type == 'VIEW_3D'), key=lambda a: a.width * a.height)
    region = next(r for r in area.regions if r.type == 'WINDOW')
    rv3d = area.spaces.active.region_3d
    rv3d.view_perspective = persp
    rv3d.view_rotation = Euler([math.radians(a) for a in rot]).to_quaternion()
    return window, area, region, rv3d


def _click(view, **extra):
    """The toolbar button's operator run in ``view`` (``filepath`` = the file picked in its file browser)."""
    window, area, region, _rv3d = view
    _glyph, _kind, (op_id, props), _label = _row()
    mod, name = op_id.split(".")
    with bpy.context.temp_override(window=window, area=area, region=region):
        return getattr(getattr(bpy.ops, mod), name)('EXEC_DEFAULT', **props, **extra)


def _new_objects(before):
    return [ob for ob in bpy.data.objects if ob.name not in before]


def _fresh():
    bpy.ops.wm.read_homefile()
    return {ob.name for ob in bpy.data.objects}


def _normal(ob):
    return (ob.matrix_world.to_3x3() @ Vector((0.0, 0.0, 1.0))).normalized()


def _up(ob):
    return (ob.matrix_world.to_3x3() @ Vector((0.0, 1.0, 0.0))).normalized()


def _close(a, b):
    return (Vector(a) - Vector(b)).length < EPS


def test_ortho_views_import_an_image_facing_the_view():
    for rot, normal, up in (((0, 0, 0), (0, 0, 1), (0, 1, 0)),        # top: faces up
                            ((90, 0, 0), (0, -1, 0), (0, 0, 1)),      # front
                            ((90, 0, 90), (1, 0, 0), (0, 0, 1))):     # side
        before = _fresh()
        k = units.maya_unit(bpy.context.scene)
        path = _png(400, 200, "ref398.png")
        assert _click(_view('ORTHO', rot), filepath=path) == {'FINISHED'}
        new = _new_objects(before)
        assert len(new) == 1, [o.name for o in new]
        ob = new[0]
        assert ob.type == 'EMPTY' and ob.empty_display_type == 'IMAGE', (ob.type, ob.empty_display_type)
        assert ob.data is not None, "the plane shows the picked image"
        assert os.path.normcase(bpy.path.abspath(ob.data.filepath)) == os.path.normcase(path), ob.data.filepath
        assert _close(_normal(ob), normal), (rot, tuple(_normal(ob)))
        assert _close(_up(ob), up), (rot, tuple(_up(ob)))
        assert _close(ob.matrix_world.translation, (0, 0, 0)), tuple(ob.matrix_world.translation)
        # as wide as the image's pixel width / 100 (the larger side of a Blender image empty = its display size)
        assert abs(ob.empty_display_size * max(ob.scale) - 4.0 * k) < EPS * k, (ob.empty_display_size, k)
        assert ob.name.startswith("imagePlane"), ob.name


def test_the_button_shows_and_hides_the_cameras_image_plane():
    """A camera the view looks through keeps its image plane: the next click shows / hides it, no new object."""
    before = _fresh()
    bpy.context.scene.camera = bpy.data.objects["Camera"]
    view = _view('CAMERA')
    assert _click(view, filepath=_png(64, 64, "toggle398.png")) == {'FINISHED'}
    plane = _new_objects(before)[0]
    names = {ob.name for ob in bpy.data.objects}
    assert _click(view) == {'FINISHED'}
    assert not ip.shown(plane), "a second click hides the camera's image plane"
    assert _click(view) == {'FINISHED'}
    assert ip.shown(plane), "the next click shows it again"
    assert {ob.name for ob in bpy.data.objects} == names, "no new object"


def test_top_front_side_import_again_on_every_click():
    """The top / front / side planes aren't the view's own: every click imports one more image, nothing is hidden."""
    before = _fresh()
    view = _view('ORTHO')
    assert _click(view, filepath=_png(64, 64, "first398.png")) == {'FINISHED'}
    first = _new_objects(before)[0]
    names = {ob.name for ob in bpy.data.objects}
    assert _click(view) == {'CANCELLED'}, "no image picked: nothing to show / hide"
    assert ip.shown(first)
    assert {ob.name for ob in bpy.data.objects} == names
    assert _click(view, filepath=_png(32, 32, "second398.png")) == {'FINISHED'}
    new = _new_objects(names)
    assert len(new) == 1 and new[0].data is not None and new[0] != first, [o.name for o in new]
    assert ip.shown(first)


def test_blenders_persp_view_and_a_persp_camera_keep_their_own_planes():
    """A plane attached to the persp camera is not the plane of Blender's own perspective view (and the other way
    round)."""
    _fresh()
    persp = next(ob for ob in sc.ensure(bpy.context.scene, bpy.context.view_layer) if ob.get(sc.MARK) == "persp")
    before = {ob.name for ob in bpy.data.objects}
    bpy.context.scene.camera = persp
    assert _click(_view('CAMERA'), filepath=_png(64, 64, "cam398b.png")) == {'FINISHED'}
    cam_plane = _new_objects(before)[0]
    assert cam_plane.parent == persp
    names = {ob.name for ob in bpy.data.objects}
    view = _view('PERSP', (60, 0, 30))
    assert _click(view) == {'CANCELLED'}
    assert ip.shown(cam_plane), "the camera's plane stays shown"
    assert _click(view, filepath=_png(64, 64, "view398b.png")) == {'FINISHED'}
    assert len(_new_objects(names)) == 1
    assert ip.shown(cam_plane)


def test_a_camera_view_attaches_the_plane_in_front_of_the_camera():
    before = _fresh()
    cam = bpy.data.objects["Camera"]
    bpy.context.scene.camera = cam
    view = _view('CAMERA')
    path = _png(800, 400, "cam398.png")
    assert _click(view, filepath=path) == {'FINISHED'}
    ob = _new_objects(before)[0]
    assert ob.parent == cam, ob.parent
    # faces the camera: the plane's normal is the camera's backward axis, its up the camera's up
    assert _close(_normal(ob), (cam.matrix_world.to_3x3() @ Vector((0, 0, 1))).normalized())
    assert _close(_up(ob), (cam.matrix_world.to_3x3() @ Vector((0, 1, 0))).normalized())
    local = cam.matrix_world.inverted() @ ob.matrix_world.translation
    assert abs(local.x) < EPS and abs(local.y) < EPS and local.z < 0, tuple(local)
    assert -local.z < cam.data.clip_end, (local.z, cam.data.clip_end)
    # fills the camera's frame width at that distance (a wide image)
    frame = [Vector(c) for c in cam.data.view_frame(scene=bpy.context.scene)]
    scale = -local.z / -frame[0].z
    width = (max(c.x for c in frame) - min(c.x for c in frame)) * scale
    assert abs(ob.empty_display_size - width) < 1e-3 * width, (ob.empty_display_size, width)
    # the camera moves: the plane stays in front of it
    cam.location.x += 3.0
    bpy.context.view_layer.update()
    assert _close(cam.matrix_world.inverted() @ ob.matrix_world.translation, local)


def test_blenders_perspective_view_faces_the_view_at_its_centre():
    before = _fresh()
    view = _view('PERSP', (60, 0, 30))
    rv3d = view[3]
    rv3d.view_location = (1.0, 2.0, 0.5)
    assert _click(view, filepath=_png(100, 300, "persp398.png")) == {'FINISHED'}
    ob = _new_objects(before)[0]
    assert ob.parent is None
    toward_viewer = (rv3d.view_rotation @ Vector((0, 0, 1))).normalized()
    assert _close(_normal(ob), toward_viewer), (tuple(_normal(ob)), tuple(toward_viewer))
    assert _close(ob.matrix_world.translation, rv3d.view_location)
    k = units.maya_unit(bpy.context.scene)
    assert abs(ob.empty_display_size - 3.0 * k) < EPS * k, "a tall image: its height is 300 px / 100"


def test_free_image_plane_still_faces_the_front_with_no_image():
    before = _fresh()
    _view('ORTHO')
    bpy.ops.allset.create(kind='IMAGE_PLANE')
    ob = _new_objects(before)[0]
    assert ob.data is None
    assert _close(_normal(ob), (0, -1, 0)), tuple(_normal(ob))
