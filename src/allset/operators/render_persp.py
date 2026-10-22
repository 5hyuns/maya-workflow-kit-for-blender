# SPDX-License-Identifier: GPL-3.0-or-later
"""Render > Render Current Frame / Render Sequence through Maya's persp camera (step 137, #67).

Maya renders the active panel's camera; a new Maya scene's renderable camera is ``perspShape``
(Maya, tmp/audit133_work/out/m04_scene.json:33-34; :105 X1). Blender's user
views aren't cameras and the Maya Workflow Kit startup file has none, so ``render.render`` stopped with
"Cannot render, no camera". The kit renders:

- through the camera the view looks through (camera view: the view's local camera, else ``scene.camera``);
- otherwise through ``persp`` (object ``persp`` / data ``perspShape``, ID property ``allset_persp``), made on
  the first render and kept, placed at the view's current view matrix and lens (Blender's viewport lens is on a
  72 mm sensor: ``key_batch.VIEW_SENSOR``, step 78 / 81), Maya clip planes (``units.clip``), made
  ``scene.camera``, then Blender's render (INVOKE: the Render Result window = Maya's Render View; Keep Image of
  ``ui/render_view.py`` works on its slots).

The view is the 3D View the operator runs in, else the main window's largest 3D View (not the Tool Box column).

The persp camera is linked to no collection (delegated, step 137): the kit Outliner already draws Maya's
default ``persp`` row (``ui/outliner_sets.default_entries``, step 99), which stands for it; unlinked, it isn't a
second row in Blender's Outliner, isn't selectable in the viewport, doesn't render as an object and isn't
exported. ``scene.camera`` doesn't count as a user (checked: renders, follows its matrix, survives
save / reload with ``use_fake_user``), so the object keeps a fake user like Maya's startup cameras, which every
scene has. checked (tmp/probe137): an unlinked ``scene.camera`` renders and follows its transform.
"""

import bpy
from bpy.props import BoolProperty

from . import framing, units
from .key_batch import VIEW_SENSOR, camera_matrix

PROP = "allset_persp"
NAME, SHAPE = "persp", "perspShape"
MAYA_FILM_MM = 36.0          # 35 mm camera film back (create.MAYA_FILM_MM, )


def persp_camera(create=True):
    """The kit's persp camera object (made on demand when ``create``)."""
    ob = next((o for o in bpy.data.objects if o.get(PROP) and o.type == 'CAMERA'), None)
    if ob is None and create:
        data = bpy.data.cameras.new(SHAPE)
        data.sensor_width = MAYA_FILM_MM
        ob = bpy.data.objects.new(NAME, data)
        ob[PROP] = True
        ob.use_fake_user = True
    return ob


def match_view(ob, space, rv3d, scene=None):
    """Put camera ``ob`` where the view (``space``, ``rv3d``) looks from, with the same lens."""
    cam = ob.data
    # From view_location / rotation / distance, not rv3d.view_matrix: that is only recomputed when the view draws
    # (stale after a scripted view change, checked in -b; step 17).
    ob.matrix_world = camera_matrix(framing.view_matrix(rv3d.view_location, rv3d.view_rotation, rv3d.view_distance))
    if rv3d.view_perspective != 'ORTHO':        # (is_perspective is updated on draw too)
        cam.type = 'PERSP'
        cam.lens = space.lens * cam.sensor_width / VIEW_SENSOR
    else:
        cam.type = 'ORTHO'
        cam.ortho_scale = rv3d.view_distance * VIEW_SENSOR / space.lens
    clip = units.clip(scene)
    cam.clip_start, cam.clip_end = clip["clip_start"], clip["clip_end"]


def _is_toolbox(space):
    from ..ui import toolbox
    return toolbox.is_toolbox(space)


def find_view(context):
    """(space, region_3d) of the view the render follows, or (None, None)."""
    area = context.area
    if area is not None and area.type == 'VIEW_3D' and not _is_toolbox(area.spaces.active):
        space = area.spaces.active
        return space, space.region_3d
    from ..ui import maya_dock, status_line
    windows = [maya_dock.main_window(context.window_manager)] if context.window_manager.windows else []
    windows += [w for w in context.window_manager.windows if w not in windows]
    for window in windows:
        if window is None:
            continue
        area, _region = status_line.main_view3d(window.screen)
        if area is not None and not _is_toolbox(area.spaces.active):
            space = area.spaces.active
            return space, space.region_3d
    return None, None


def view_camera(space, rv3d, scene):
    """The camera the view looks through, or None for a user view."""
    if space is None or rv3d is None or rv3d.view_perspective != 'CAMERA':
        return None
    if space.use_local_camera and space.camera is not None:
        return space.camera
    return scene.camera


def render_camera(context):
    """Make the camera Maya would render the active panel with ``scene.camera``; returns it."""
    scene = context.scene
    space, rv3d = find_view(context)
    ob = view_camera(space, rv3d, scene)
    if ob is None:
        ob = persp_camera()
        if rv3d is not None:        # no 3D View at all (background): persp stays where it was
            match_view(ob, space, rv3d, scene)
    scene.camera = ob
    return ob


class _Render:
    """Shared by the two render operators (a registered operator class can't be subclassed into another one)."""
    ANIMATION = False
    bl_options = {'REGISTER'}

    write_still: BoolProperty(name="Write Image", default=False, options={'SKIP_SAVE', 'HIDDEN'})

    @classmethod
    def poll(cls, context):
        return context.scene is not None

    def _render(self, context, how):
        ob = render_camera(context)
        props = {"animation": self.ANIMATION}
        if self.write_still and not self.ANIMATION:
            props["write_still"] = True
        try:
            res = bpy.ops.render.render(how, **props)
        except RuntimeError as ex:
            self.report({'ERROR'}, str(ex))
            return {'CANCELLED'}
        if 'CANCELLED' in res:
            return {'CANCELLED'}
        self.report({'INFO'}, f"Rendering through {ob.name}")
        return {'FINISHED'}

    def invoke(self, context, event):
        if context.window is None or bpy.app.background:
            return self.execute(context)
        return self._render(context, 'INVOKE_DEFAULT')

    def execute(self, context):
        return self._render(context, 'EXEC_DEFAULT')


class ALLSET_OT_render_current_frame(_Render, bpy.types.Operator):
    """Render the current frame through the active view's camera (Maya Render > Render Current Frame:
    persp when the view isn't looking through a camera)"""
    bl_idname = "allset.render_current_frame"
    bl_label = "Render Current Frame"


class ALLSET_OT_render_sequence(_Render, bpy.types.Operator):
    """Render the animation range through the active view's camera (Maya Render > Render Sequence)"""
    bl_idname = "allset.render_sequence"
    bl_label = "Render Sequence"
    ANIMATION = True


classes = (ALLSET_OT_render_current_frame, ALLSET_OT_render_sequence)
