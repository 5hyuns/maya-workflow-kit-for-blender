# SPDX-License-Identifier: GPL-3.0-or-later
"""Reusable lifecycle interface for one-shot operators using the In-View HUD.

The official :mod:`ui.in_view` module remains the only HUD renderer and event
interaction owner. This module does not draw a second HUD and does not define
a parallel parameter system.

Usage
-----
1. Import :class:`StaticInViewOperator` in the operator module.
2. Inherit from it before ``bpy.types.Operator``::

       class MESH_OT_example(StaticInViewOperator, bpy.types.Operator):
           bl_idname = "mesh.example_in_view"
           bl_label = "Example In-View Operation"

3. Implement the ``in_view_*`` hooks. ``in_view_begin`` must connect the
   operator to the official In-View HUD integration; ``in_view_process_event``
   must forward events to that same integration and return a Blender operator
   result set.
4. Implement ``in_view_execute`` and ``in_view_cancel`` to commit or release
   the operator's own temporary data.

The hook methods are an adapter contract, not an automatic property-to-HUD
binding. The current official In-View HUD is still specialized around its
Extrude/Bevel records. A concrete operator must not invent another HUD
renderer; it must use the generic adapter exposed by the official In-View
implementation when that adapter becomes available.

See ``IN_VIEW_STATIC_USAGE.md`` beside this module for the complete lifecycle
contract, an implementation template, and integration requirements.
"""


def selection_anchor(context):
    """Return the world-space centre of the current mesh selection, if available.

    This helper is intentionally independent of the HUD renderer. Generic
    one-shot operators may use it as their default In-View HUD anchor.
    """
    obj = getattr(context, "active_object", None)
    if obj is None:
        return None
    if getattr(context, "mode", None) == 'EDIT_MESH':
        try:
            import bmesh
            from mathutils import Vector
            bm = bmesh.from_edit_mesh(obj.data)
            coords = []
            faces = [face for face in bm.faces if face.select]
            if faces:
                coords = [face.calc_center_median() for face in faces]
            else:
                edges = [edge for edge in bm.edges if edge.select]
                if edges:
                    coords = [(edge.verts[0].co + edge.verts[1].co) * 0.5
                              for edge in edges]
                else:
                    coords = [vert.co for vert in bm.verts if vert.select]
            if coords:
                center = Vector((0.0, 0.0, 0.0))
                for coordinate in coords:
                    center += coordinate
                center /= len(coords)
                return obj.matrix_world @ center
        except Exception:
            pass
    return obj.matrix_world.translation.copy()


class StaticInViewOperator:
    """Mixin defining the lifecycle of a one-shot In-View HUD operator.

    Required hooks:
        ``in_view_params(context)`` returns the operator's parameter descriptors.
        ``in_view_begin(context, event)`` starts/connects the official HUD session.
        ``in_view_process_event(context, event)`` forwards events to that session.
        ``in_view_execute(context)`` commits the operation after confirmation.
        ``in_view_cancel(context)`` releases temporary resources after cancellation.

    ``in_view_process_event`` returns ``None`` or ``{'RUNNING_MODAL'}`` to
    continue, ``{'FINISHED'}`` to commit, or ``{'CANCELLED'}`` to cancel.

    Example inheritance order::

        class MESH_OT_example(StaticInViewOperator, bpy.types.Operator):
            ...

    This class is a mixin and must not be registered by itself. It intentionally
    does not implement drawing, hit testing, parameter editing, or a second
    modal HUD engine. A concrete subclass must connect its hooks to the generic
    session API owned by :mod:`ui.in_view`.
    """

    def in_view_params(self, context):
        """Return declarative parameter descriptors accepted by the In-View adapter.

        Do not draw UI or handle mouse events in this method.
        """
        raise NotImplementedError

    def in_view_begin(self, context, event):
        """Create operation state and attach it to the official In-View HUD.

        Store any session/token needed by ``in_view_process_event`` on ``self``.
        Do not register a second draw handler or a separate HUD event system.
        """
        raise NotImplementedError

    def in_view_process_event(self, context, event):
        """Forward an event to the official In-View HUD interaction layer.

        Return ``{'RUNNING_MODAL'}`` while the session is active,
        ``{'FINISHED'}`` to confirm, or ``{'CANCELLED'}`` to abort.
        """
        raise NotImplementedError

    def in_view_execute(self, context):
        """Apply the one-shot operation exactly once after HUD confirmation."""
        raise NotImplementedError

    def in_view_cancel(self, context):
        """Release previews, temporary mesh data, and adapter state on cancellation."""
        pass

    def invoke(self, context, event):
        """Start the operator-owned session through the official In-View HUD."""
        if getattr(getattr(context, "space_data", None), "type", None) != 'VIEW_3D':
            return {'CANCELLED'}
        try:
            self.in_view_params(context)
            self.in_view_begin(context, event)
        except Exception:
            try:
                self.in_view_cancel(context)
            except Exception:
                pass
            return {'CANCELLED'}
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        """Route events through the official HUD adapter and commit/cancel once."""
        result = self.in_view_process_event(context, event)
        if result is None or 'RUNNING_MODAL' in result:
            return {'RUNNING_MODAL'}
        if 'FINISHED' in result:
            try:
                self.in_view_execute(context)
            except Exception:
                try:
                    self.in_view_cancel(context)
                except Exception:
                    pass
                return {'CANCELLED'}
            return {'FINISHED'}
        if 'CANCELLED' in result:
            try:
                self.in_view_cancel(context)
            except Exception:
                pass
            return {'CANCELLED'}
        return result
