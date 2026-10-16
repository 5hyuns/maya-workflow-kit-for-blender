# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya arrow-key pick-walk (object mode).

research/maya/interaction.md §2 "Arrow keys": Up = parent, Down = child,
Left/Right = sibling (``pickWalk -d up``, HK:364-369). Siblings are ordered
by name (Blender Outliner default sort) and wrap around [K]. Component
pick-walk is not covered yet (docs/steps/step_3.md).
"""

import bpy

DIRECTIONS = (
    ("UP", "Up", "Select the parent"),
    ("DOWN", "Down", "Select the first child"),
    ("LEFT", "Left", "Select the previous sibling"),
    ("RIGHT", "Right", "Select the next sibling"),
)


def _in_layer(view_layer, objs):
    names = view_layer.objects
    return sorted((o for o in objs if o.name in names), key=lambda o: o.name)


def siblings(view_layer, ob):
    if ob.parent is not None:
        return _in_layer(view_layer, ob.parent.children)
    return _in_layer(view_layer, (o for o in view_layer.objects if o.parent is None))


def walk(view_layer, ob, direction):
    """Object reached from ``ob`` (``ob`` itself when there is nowhere to go)."""
    if direction == "UP":
        return ob.parent if ob.parent is not None and ob.parent.name in view_layer.objects else ob
    if direction == "DOWN":
        kids = _in_layer(view_layer, ob.children)
        return kids[0] if kids else ob
    sibs = siblings(view_layer, ob)
    if len(sibs) < 2:
        return ob
    i = sibs.index(ob)
    return sibs[(i + (1 if direction == "RIGHT" else -1)) % len(sibs)]


class MAYAKIT_OT_pick_walk(bpy.types.Operator):
    """Walk the selection through the hierarchy (Maya arrow keys)"""
    bl_idname = "maya_kit.pick_walk"
    bl_label = "Pick Walk"
    bl_options = {'REGISTER', 'UNDO'}

    direction: bpy.props.EnumProperty(items=DIRECTIONS, name="Direction")

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and bool(context.selected_objects)

    def execute(self, context):
        vl = context.view_layer
        active = vl.objects.active
        targets = []
        for ob in context.selected_objects:
            t = walk(vl, ob, self.direction)
            if t not in targets:
                targets.append(t)
        for ob in context.selected_objects:
            ob.select_set(False)
        for t in targets:
            t.select_set(True)
        if active is not None:
            vl.objects.active = walk(vl, active, self.direction)
        return {'FINISHED'}


classes = (MAYAKIT_OT_pick_walk,)
