"""#409: an image plane whose Display Mode is None (or hidden with the Image Plane button) is not drawn but stays a
selectable object, like Maya: View > Image Plane > Image Plane Attributes selects it, and Show > Image Planes off and
on again keeps it undrawn.
"""

from importlib import import_module

import bpy

import kit
from test_issue409_image_plane_menus import _camera_with_plane, _run

gk4 = import_module(kit.MODULE + ".operators.global_keys4")


def _drawn(plane):
    """The viewport draws the plane's image (visible object, image shown in perspective and orthographic views)."""
    return (plane.visible_get() and plane.show_empty_image_perspective
            and plane.show_empty_image_orthographic)


def _attributes(view, plane):
    window, area, region = view
    with bpy.context.temp_override(window=window, area=area, region=region):
        return bpy.ops.allset.image_plane_attributes(name=plane.name)


def test_image_plane_attributes_selects_a_display_mode_none_plane():
    cam, view, plane = _camera_with_plane()
    assert _run(view, "allset.image_plane_display", mode='NONE') == {'FINISHED'}
    assert not _drawn(plane), "Display Mode None: the image is not drawn"
    bpy.ops.object.select_all(action='DESELECT')
    cam.select_set(True)
    assert _attributes(view, plane) == {'FINISHED'}
    assert plane.select_get(), "Image Plane Attributes selects the plane, also with Display Mode None"
    assert not cam.select_get()
    assert bpy.context.view_layer.objects.active == plane
    assert not _drawn(plane), "selecting it keeps Display Mode None"


def test_the_button_hides_a_plane_that_stays_selectable():
    _cam, view, plane = _camera_with_plane()
    assert _run(view, "allset.image_plane") == {'FINISHED'}
    assert not _drawn(plane), "the button's click hides the camera's plane"
    assert _attributes(view, plane) == {'FINISHED'}
    assert plane.select_get()
    assert _run(view, "allset.image_plane") == {'FINISHED'}
    assert _drawn(plane), "the next click shows it again"


def test_show_image_planes_off_and_on_keeps_display_mode_none():
    _cam, view, plane = _camera_with_plane()
    other = bpy.data.objects.new("imagePlaneOther", None)
    other.empty_display_type = 'IMAGE'
    bpy.context.scene.collection.objects.link(other)
    assert _run(view, "allset.image_plane_display", mode='NONE') == {'FINISHED'}
    scene = bpy.context.scene
    assert gk4.toggle_show(None, scene, 'IMAGE_PLANES') is False, "Show > Image Planes off"
    assert gk4.toggle_show(None, scene, 'IMAGE_PLANES') is True, "Show > Image Planes on"
    assert not _drawn(plane), "a Display Mode None plane stays undrawn"
    assert _drawn(other), "the other image plane is drawn again"
    assert _run(view, "allset.image_plane_display", mode='RGBA') == {'FINISHED'}
    assert _drawn(plane), "RGBA draws it again"


def test_display_mode_never_draws_a_plane_while_show_image_planes_is_off():
    """Show > Image Planes is a view filter: with it off, Display Mode RGBA (or the button) doesn't draw the plane,
    also when it is the scene's only image plane; turning Show on again draws it."""
    _cam, view, plane = _camera_with_plane()
    scene = bpy.context.scene
    assert gk4.toggle_show(None, scene, 'IMAGE_PLANES') is False, "Show > Image Planes off"
    assert _run(view, "allset.image_plane_display", mode='NONE') == {'FINISHED'}
    assert not gk4.image_planes_drawn(scene), "Show > Image Planes stays off"
    assert _run(view, "allset.image_plane_display", mode='RGBA') == {'FINISHED'}
    assert not _drawn(plane), "RGBA doesn't draw it while Show > Image Planes is off"
    assert _run(view, "allset.image_plane") == {'FINISHED'}
    assert _run(view, "allset.image_plane") == {'FINISHED'}
    assert not _drawn(plane), "nor does the button's hide / show"
    assert gk4.toggle_show(None, scene, 'IMAGE_PLANES') is True, "Show > Image Planes on"
    assert _drawn(plane), "Show on draws the RGBA plane again"
