# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya Ctrl+G group.

research/maya/concepts.md:89-91: ``doGroup(world=0, preserve=1, zeroPivot=1)``
creates the group under the common parent with its pivot at the origin; with
nothing selected it makes an empty group. Names are ``group1``, ``group2``, ...

Blender form: an Empty is the group transform. Children are parented the Maya
way (docs/user_decisions.md #2): world transform kept, ``matrix_parent_inverse``
left at identity so the child's local values are relative to the group.
"""

import re

import bpy
from mathutils import Matrix

from . import units

_GROUP_RE = re.compile(r"^group(\d+)$")


def next_group_name(names):
    """Lowest unused ``groupN`` (N >= 1) given existing object names."""
    used = {int(m.group(1)) for n in names if (m := _GROUP_RE.match(n))}
    n = 1
    while n in used:
        n += 1
    return f"group{n}"


def common_parent(objects):
    parents = {ob.parent for ob in objects}
    return parents.pop() if len(parents) == 1 else None


def set_parent_keep_world(child, parent):
    """Parent with identity parent-inverse while keeping the world matrix."""
    world = child.matrix_world.copy()
    child.parent = parent
    child.matrix_parent_inverse = Matrix.Identity(4)
    child.matrix_world = world


def make_group(context, objects):
    """Create a Maya-style group over ``objects``. Returns the new Empty."""
    objects = list(objects)
    parent = common_parent(objects) if objects else None
    if objects and objects[0].users_collection:
        collection = objects[0].users_collection[0]
    else:
        collection = context.collection

    grp = bpy.data.objects.new(next_group_name(o.name for o in bpy.data.objects), None)
    grp.empty_display_type = 'PLAIN_AXES'
    # 1 Maya unit, like a Create locator (decision 8, docs/steps/step_21.md)
    grp.empty_display_size = units.maya_unit(context.scene)
    collection.objects.link(grp)
    if parent is not None:
        # Under the common parent with an identity local transform, so the
        # group pivot sits at the parent's origin (Maya zeroPivot).
        grp.parent = parent
        grp.matrix_parent_inverse = Matrix.Identity(4)
    grp.matrix_basis = Matrix.Identity(4)
    context.view_layer.update()

    for ob in objects:
        set_parent_keep_world(ob, grp)
    return grp


class MAYAKIT_OT_group(bpy.types.Operator):
    """Group the selected objects under a new transform (Maya Ctrl+G)"""
    bl_idname = "maya_kit.group"
    bl_label = "Group"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and context.view_layer is not None

    def execute(self, context):
        objects = [ob for ob in context.selected_objects]
        grp = make_group(context, objects)
        for ob in objects:
            ob.select_set(False)
        grp.select_set(True)
        context.view_layer.objects.active = grp
        self.report({'INFO'}, f"Grouped {len(objects)} object(s) into {grp.name}")
        return {'FINISHED'}


classes = (MAYAKIT_OT_group,)
