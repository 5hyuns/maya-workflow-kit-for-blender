# SPDX-License-Identifier: GPL-3.0-or-later
"""The viewport panel toolbar's Image Plane button (#398), like Maya.

A view without an image plane: the button opens a file browser (in the project's sourceimages folder) and the picked
image becomes an image plane of that view, a Blender image empty named ``imagePlane1``:
- an orthographic view (top / front / side or an orthographic camera) gets a plane facing it, at the origin for the
  top / front / side views and 5 units in front of any other orthographic camera;
- a perspective camera the view looks through gets a plane attached to it (parented) 100 units in front, filling its
  view, so it follows the camera;
- Blender's own perspective view (no camera object) gets a plane facing the view at the view's centre.
The plane is as wide as the image's pixel width / 100 (Maya length units), its height follows the image.

A view that has an image plane: the button shows / hides it (Maya's image plane display on / off), nothing is made.
"""

import json
import os

import bpy
from bpy.props import BoolProperty, StringProperty
from mathutils import Quaternion, Vector

from . import units

TAG = "allset_image_plane_view"     # the view an image plane belongs to: a startup camera name / a camera's name
PIXELS_PER_UNIT = 100.0             # the plane is the image's pixel width / 100 units wide
CAMERA_DEPTH = 100.0                # a camera's plane, units in front of it
ORTHO_OFFSET = 5.0                  # an orthographic camera's plane (not top / front / side), units in front of it


def _view_target(context):
    """Where this view's image plane goes, as plain data (kept between the button click and the file browser):
    ``kind`` ORTHO / CAMERA / VIEW, ``key`` (the view's camera; "" = none to show / hide), ``rot`` (w, x, y, z),
    ``loc`` and ``camera`` (the camera object's name for CAMERA)."""
    from ..ui import panel_cameras
    from . import startup_cameras
    space = context.space_data if context.space_data is not None and context.space_data.type == 'VIEW_3D' else None
    rv3d = context.region_data or getattr(space, "region_3d", None)
    if rv3d is None:
        return None
    k = units.maya_unit(context.scene)
    cam = panel_cameras.view_camera(context)
    if cam is not None and cam.type == 'CAMERA':
        mark = cam.get(startup_cameras.MARK) if startup_cameras.is_startup(cam) else None
        rot = cam.matrix_world.to_quaternion()
        if cam.data.type != 'ORTHO':
            return {"kind": 'CAMERA', "key": cam.name, "rot": list(rot), "loc": [0.0, 0.0, 0.0], "camera": cam.name}
        if mark:
            loc = Vector()
        else:
            loc = cam.matrix_world.translation + rot @ Vector((0.0, 0.0, -ORTHO_OFFSET * k))
        return {"kind": 'ORTHO', "key": mark or cam.name, "rot": list(rot), "loc": list(loc), "camera": ""}
    rot = rv3d.view_rotation
    if rv3d.view_perspective == 'ORTHO':
        return {"kind": 'ORTHO', "key": panel_cameras._startup_name(context) or "", "rot": list(rot),
                "loc": [0.0, 0.0, 0.0], "camera": ""}
    return {"kind": 'VIEW', "key": "persp", "rot": list(rot), "loc": list(rv3d.view_location), "camera": ""}


def view_plane(context, key):
    """The image plane of the view ``key`` (None: the view has none)."""
    if not key:
        return None
    for ob in context.view_layer.objects:
        if ob.get(TAG) == key and ob.type == 'EMPTY' and ob.empty_display_type == 'IMAGE':
            return ob
    return None


def _plane_size(image, width, height=None):
    """Display size of an image empty showing ``image`` ``width`` wide, or fitting in ``width`` x ``height``
    (Blender draws an image empty's larger side at its display size)."""
    w, h = (image.size[0], image.size[1]) if image is not None and image.size[0] and image.size[1] else (1, 1)
    if height is not None and w * height < h * width:     # taller than the frame: fit the height
        width = height * w / h
    return width if w >= h else width * h / w


def build(context, target, image):
    """The image plane for ``target`` (``_view_target``) showing ``image``; returns the new object."""
    from . import create
    k = units.maya_unit(context.scene)
    ob = create.create(context, 'IMAGE_PLANE', create._maya_naming(context))
    ob.data = image
    ob.rotation_mode = 'XYZ'
    cam = bpy.data.objects.get(target["camera"]) if target["kind"] == 'CAMERA' else None
    if cam is not None:
        depth = min(CAMERA_DEPTH * k, cam.data.clip_end * 0.9)
        frame = [Vector(c) for c in cam.data.view_frame(scene=context.scene)]
        scale = depth / max(-frame[0].z, 1e-9)
        fw = (max(c.x for c in frame) - min(c.x for c in frame)) * scale
        fh = (max(c.y for c in frame) - min(c.y for c in frame)) * scale
        ob.parent = cam
        ob.matrix_parent_inverse.identity()
        ob.location = (0.0, 0.0, -depth)
        ob.rotation_euler = (0.0, 0.0, 0.0)
        ob.empty_display_size = _plane_size(image, fw, fh)
    else:
        w = (image.size[0] if image is not None and image.size[0] else PIXELS_PER_UNIT) / PIXELS_PER_UNIT
        ob.location = target["loc"]
        ob.rotation_euler = Quaternion(target["rot"]).to_euler('XYZ')
        ob.empty_display_size = _plane_size(image, w * k)
    if target["key"]:
        ob[TAG] = target["key"]
    return ob


def toggle(plane):
    plane.hide_set(not plane.hide_get())


class ALLSET_OT_image_plane(bpy.types.Operator):
    """Import an image as an image plane facing this view (attached to the camera it looks through); when the view
    has one, show or hide it, like Maya"""
    bl_idname = "allset.image_plane"
    bl_label = "Image Plane"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(subtype='FILE_PATH', options={'SKIP_SAVE'})
    filter_image: BoolProperty(default=True, options={'HIDDEN', 'SKIP_SAVE'})
    filter_folder: BoolProperty(default=True, options={'HIDDEN', 'SKIP_SAVE'})
    view: StringProperty(options={'HIDDEN', 'SKIP_SAVE'})

    @classmethod
    def poll(cls, context):
        return context.scene is not None and context.view_layer is not None

    def _target(self, context):
        if self.view:
            return json.loads(self.view)
        return _view_target(context)

    def invoke(self, context, _event):
        target = self._target(context)
        if target is None:
            return {'CANCELLED'}
        self.view = json.dumps(target)
        plane = view_plane(context, target["key"])
        if plane is not None and not self.filepath:
            toggle(plane)
            return {'FINISHED'}
        if not self.filepath:
            from . import project
            folder = project.texture_folder(context)     # the project's sourceimages, like Maya's image dialogs
            if folder:
                self.filepath = os.path.join(folder, "")
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        target = self._target(context)
        if target is None:
            return {'CANCELLED'}
        path = bpy.path.abspath(self.filepath) if self.filepath else ""
        if not path:
            plane = view_plane(context, target["key"])
            if plane is None:
                self.report({'WARNING'}, "Image Plane: pick an image file")
                return {'CANCELLED'}
            toggle(plane)
            return {'FINISHED'}
        if not os.path.isfile(path):
            self.report({'WARNING'}, f"Image Plane: no image file '{self.filepath}'")
            return {'CANCELLED'}
        try:
            image = bpy.data.images.load(path, check_existing=True)
        except RuntimeError as ex:       # a file Blender can't read as an image
            self.report({'WARNING'}, f"Image Plane: {ex}")
            return {'CANCELLED'}
        ob = build(context, target, image)
        from .. import results
        results.result(self, f"Created {ob.name}")
        return {'FINISHED'}


classes = (ALLSET_OT_image_plane,)
