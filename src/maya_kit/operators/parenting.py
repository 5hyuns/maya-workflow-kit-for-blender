# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya P / Shift+P: parent to the last selected, unparent to the world.

research/maya/concepts.md:98-101 and defaults.json ``parentPreserve 1`` /
``unparentPreserve 1``: the world transform is kept and the child's local
values are recomputed relative to the new parent. docs/user_decisions.md #2:
that is the default ("Maya" Parent Mode, parent inverse = identity); the
"Blender" mode keeps Blender's parent inverse (``object.parent_set``).
Plan: docs/steps/step_10.md 「계획」 4.
"""

import bpy
from mathutils import Matrix

EPS = 1e-6


def is_ancestor(ob, other):
    """True if ``ob`` is ``other`` or one of its ancestors."""
    p = other
    while p is not None:
        if p is ob:
            return True
        p = p.parent
    return False


def set_parent_maya(child, parent):
    """Parent keeping the world matrix with the local values relative to the parent.

    The parent inverse stays identity unless the local matrix has shear (rotated
    child under a non-uniformly scaled parent): Maya stores that in ``shear``,
    Blender channels can't, so the residual goes into the parent inverse and the
    channels hold the closest translate/rotate/scale (delegated, step 10).
    """
    world = child.matrix_world.copy()
    local = parent.matrix_world.inverted_safe() @ world
    t, q, s = local.decompose()
    trs = Matrix.LocRotScale(t, q, s)
    residual = local @ trs.inverted_safe()
    exact = all(abs(residual[i][j] - (1.0 if i == j else 0.0)) < EPS
                for i in range(4) for j in range(4))
    child.parent = parent
    child.matrix_parent_inverse = Matrix.Identity(4) if exact else residual
    child.matrix_world = world


def parent_maya(children, parent):
    """Parent ``children`` under ``parent`` keeping their world matrices. Returns
    (parented, skipped cycles)."""
    done, cycles = [], []
    for ob in children:
        if ob is parent:
            continue
        if is_ancestor(ob, parent):
            cycles.append(ob)
            continue
        set_parent_maya(ob, parent)
        done.append(ob)
    return done, cycles


def unparent(objects):
    done = 0
    for ob in objects:
        if ob.parent is None:
            continue
        world = ob.matrix_world.copy()
        ob.parent = None
        ob.matrix_parent_inverse = Matrix.Identity(4)
        ob.matrix_world = world
        done += 1
    return done


def _mode(context):
    from .. import preferences
    try:
        return preferences.get(context).parent_mode
    except KeyError:
        return 'MAYA'


class MAYAKIT_OT_parent(bpy.types.Operator):
    """Parent the selected objects under the last selected one, keeping them in place
    (Maya Edit > Parent, P)"""
    bl_idname = "maya_kit.parent"
    bl_label = "Parent"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def execute(self, context):
        parent = context.view_layer.objects.active
        children = [ob for ob in context.selected_objects if ob is not parent]
        if parent is None or not parent.select_get() or not children:
            self.report({'WARNING'}, "Select the children, then the parent last")
            return {'CANCELLED'}
        if _mode(context) == 'BLENDER':
            cycles = [ob for ob in children if is_ancestor(ob, parent)]
            if cycles:
                self.report({'WARNING'}, f"Cannot parent {parent.name} under its own child")
                return {'CANCELLED'}
            return bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)
        context.view_layer.update()
        done, cycles = parent_maya(children, parent)
        if cycles:
            self.report({'WARNING'}, "Skipped (parent is their descendant): "
                        + ", ".join(ob.name for ob in cycles))
        return {'FINISHED'} if done else {'CANCELLED'}


class MAYAKIT_OT_unparent(bpy.types.Operator):
    """Move the selected objects to the world, keeping them in place
    (Maya Edit > Unparent, Shift+P)"""
    bl_idname = "maya_kit.unparent"
    bl_label = "Unparent"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def execute(self, context):
        context.view_layer.update()
        unparent(context.selected_objects)
        return {'FINISHED'}


classes = (MAYAKIT_OT_parent, MAYAKIT_OT_unparent)
