# SPDX-License-Identifier: GPL-3.0-or-later
"""Rigging menu items with Maya meaning.

- Constrain > Parent / Point / Orient / Scale / Aim ...: Maya order (targets, then the constrained node
  last). In pose mode the constraint goes on the active joint (pose bone), the target is the selected
  control object or joint — not on the armature object (-18,-3).
- Modify > Add / Edit / Delete Attribute (Maya Attributes section,
  ): custom properties on the selected objects / joints,
  which the Channel Box shows as channels.
- Deform > Blend Shape: ``object.join_shapes`` (targets selected, base last = Maya's order).
- Skeleton > Quick Rig: Rigify (bundled with Blender), enabled only after the user confirms.
"""

import re

import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, StringProperty

from ..ui import channel_box as cb

CONSTRAINT_TYPES = (
    ('CHILD_OF', "Parent", "Maya parentConstraint (Child Of; the offset is kept like Maya's Maintain Offset)"),
    ('COPY_LOCATION', "Point", "Maya pointConstraint (Copy Location)"),
    ('COPY_ROTATION', "Orient", "Maya orientConstraint (Copy Rotation)"),
    ('COPY_SCALE', "Scale", "Maya scaleConstraint (Copy Scale)"),
    ('TRACK_TO', "Aim", "Maya aimConstraint (Track To)"),
    ('FOLLOW_PATH', "Attach to Motion Path", "Maya motion path (Follow Path)"),
    ('SHRINKWRAP', "Geometry", "Maya geometryConstraint (Shrinkwrap)"),
)
CONSTRAIN_HINT = "Select the control first, then the joint last (joints in pose mode)"


class ALLSET_OT_constrain(bpy.types.Operator):
    """Maya Constrain: select the target(s), then the object or joint to constrain last"""
    bl_idname = "allset.constrain"
    bl_label = "Constrain"
    bl_options = {'REGISTER', 'UNDO'}

    type: EnumProperty(items=CONSTRAINT_TYPES, name="Type")

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.mode in {'OBJECT', 'POSE'}

    def execute(self, context):
        label = next(t[1] for t in CONSTRAINT_TYPES if t[0] == self.type)
        arm = cb.pose_armature(context)
        if arm is not None:
            pb = context.active_pose_bone
            others = [o for o in context.selected_objects if o is not arm]
            bones = [b for b in context.selected_pose_bones or () if b != pb]
            if pb is None or not (others or bones):
                self.report({'WARNING'}, CONSTRAIN_HINT)
                return {'CANCELLED'}
            before = len(pb.constraints)
            bpy.ops.pose.constraint_add_with_targets(type=self.type)
            owner, cons = pb.name, pb.constraints
        else:
            ob = context.active_object
            if not [o for o in context.selected_objects if o is not ob]:
                self.report({'WARNING'}, CONSTRAIN_HINT)
                return {'CANCELLED'}
            before = len(ob.constraints)
            bpy.ops.object.constraint_add_with_targets(type=self.type)
            owner, cons = ob.name, ob.constraints
        if len(cons) == before:
            self.report({'WARNING'}, CONSTRAIN_HINT)
            return {'CANCELLED'}
        con = cons[-1]
        target = getattr(con, "target", None)
        sub = getattr(con, "subtarget", "")
        self.report({'INFO'}, f"{label} constraint on {owner}" +
                    (f" (target {target.name}{'.' + sub if sub else ''})" if target else ""))
        return {'FINISHED'}


# --- Blend Shape ------------------------------------------------------------------------------------

class ALLSET_OT_blend_shape(bpy.types.Operator):
    """Maya Blend Shape: select the target shapes, then the base mesh last (shape keys on the base)"""
    bl_idname = "allset.blend_shape"
    bl_label = "Blend Shape"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        return ob is not None and ob.type == 'MESH' and context.mode == 'OBJECT'

    def execute(self, context):
        base = context.active_object
        targets = [o for o in context.selected_objects if o is not base and o.type == 'MESH']
        if not targets:
            self.report({'WARNING'}, "Select the target shapes, then the base mesh last")
            return {'CANCELLED'}
        n = len(base.data.vertices)
        bad = [o for o in targets if len(o.data.vertices) != n]
        good = [o for o in targets if o not in bad]
        if not good:
            self.report({'ERROR'}, f"Blend Shape: {', '.join(o.name for o in bad)} "
                                   f"has a different vertex count than {base.name} ({n})")
            return {'CANCELLED'}
        for o in bad:
            o.select_set(False)
        bpy.ops.object.join_shapes()
        msg = f"Blend Shape on {base.name}: {', '.join(o.name for o in good)}"
        if bad:
            msg += f" (skipped, different vertex count: {', '.join(o.name for o in bad)})"
        self.report({'WARNING'} if bad else {'INFO'}, msg)
        return {'FINISHED'}


# --- Quick Rig -> Rigify ---------------------------------------------------------------------------

RIGIFY = "rigify"
QUICK_RIG_TEXT = ("Blender has no Quick Rig / HumanIK. Rigify (bundled with Blender) adds a human "
                  "meta-rig: fit its guides to the mesh, then Generate Rig (no automatic fitting).")


class ALLSET_OT_quick_rig(bpy.types.Operator):
    """Maya Quick Rig with Blender's Rigify: add a human meta-rig to fit to the mesh, then Generate Rig"""
    bl_idname = "allset.quick_rig"
    bl_label = "Quick Rig (Rigify)"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        if RIGIFY not in context.preferences.addons:
            return context.window_manager.invoke_confirm(
                self, event, title="Enable Rigify?", confirm_text="Enable Rigify",
                message="Quick Rig uses Rigify, an add-on bundled with Blender. Enable it (your "
                        "add-on list changes) and add a human meta-rig?")
        return self.execute(context)

    def execute(self, context):
        if RIGIFY not in context.preferences.addons:
            import addon_utils
            addon_utils.enable(RIGIFY, default_set=True)
            if RIGIFY not in context.preferences.addons:
                self.report({'ERROR'}, "Rigify could not be enabled")
                return {'CANCELLED'}
        if context.mode != 'OBJECT' and context.active_object is not None:
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.armature_human_metarig_add()
        self.report({'INFO'}, QUICK_RIG_TEXT)
        return {'FINISHED'}


# --- Add / Edit / Delete Attribute ---------------------------------------------------------------

NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
DATA_TYPES = (('FLOAT', "Float", "Maya double / float"), ('INT', "Integer", "Maya long"),
              ('BOOL', "Boolean", "Maya bool"))


def custom_nodes(context):
    return cb.targets(context)


def selected_custom(context, node):
    return [k[len(cb.CUSTOM_PREFIX):] for k in cb.selected_channels(context)
            if k.startswith(cb.CUSTOM_PREFIX) and k[len(cb.CUSTOM_PREFIX):] in node.keys()]


def set_limits(node, name, kind, use_min, minimum, use_max, maximum, default):
    if kind == 'BOOL':
        node.id_properties_ui(name).update(default=bool(default))
        return
    cast = int if kind == 'INT' else float
    big = 2 ** 31 - 1 if kind == 'INT' else 3.4e38
    lo = cast(minimum) if use_min else -big
    hi = cast(maximum) if use_max else big
    node.id_properties_ui(name).update(min=lo, max=hi, soft_min=lo, soft_max=hi, default=cast(default))


def limits(node, name):
    """(kind, use_min, min, use_max, max, default) of a custom property."""
    value = node[name]
    kind = 'BOOL' if isinstance(value, bool) else 'INT' if isinstance(value, int) else 'FLOAT'
    data = node.id_properties_ui(name).as_dict()
    big = 1e30
    lo, hi = data.get("min", -big), data.get("max", big)
    return (kind, lo > -big and abs(lo) < 2 ** 31 - 1, lo, hi < big and abs(hi) < 2 ** 31 - 1, hi,
            data.get("default", value))


class _AttributeLimits:
    data_type: EnumProperty(items=DATA_TYPES, name="Data Type", default='FLOAT')
    use_min: BoolProperty(name="Minimum", description="Limit the value from below")
    minimum: FloatProperty(name="Minimum", default=0.0)
    use_max: BoolProperty(name="Maximum", description="Limit the value from above")
    maximum: FloatProperty(name="Maximum", default=1.0)
    default: FloatProperty(name="Default", default=0.0)

    def draw_limits(self, layout):
        if self.data_type == 'BOOL':
            layout.prop(self, "default", text="Default (0 / 1)")
            return
        for use, value in (("use_min", "minimum"), ("use_max", "maximum")):
            row = layout.row(align=True)
            row.prop(self, use, text="")
            sub = row.row(align=True)
            sub.active = getattr(self, use)
            sub.prop(self, value)
        layout.prop(self, "default")


class ALLSET_OT_add_attribute(_AttributeLimits, bpy.types.Operator):
    """Maya Add Attribute: a new keyable attribute on the selected objects / joints (a Channel Box channel)"""
    bl_idname = "allset.add_attribute"
    bl_label = "Add Attribute"
    bl_options = {'REGISTER', 'UNDO'}

    long_name: StringProperty(name="Long name", description="Letters, digits and _ (Maya attribute name)")

    @classmethod
    def poll(cls, context):
        return cb.lead(context) is not None

    def invoke(self, context, event):
        node = cb.lead(context)
        return context.window_manager.invoke_props_dialog(self, title=f"Add Attribute: {node.name}",
                                                          confirm_text="OK", width=320)

    def draw(self, context):
        lay = self.layout
        lay.prop(self, "long_name")
        lay.row().prop(self, "data_type", expand=True)
        lay.label(text="Numeric Attribute Properties")
        self.draw_limits(lay)

    def execute(self, context):
        name = self.long_name.strip()
        if not NAME_RE.match(name) or name.startswith("allset_"):
            self.report({'ERROR'}, f"Add Attribute: '{name}' is not a valid attribute name "
                                   "(letters, digits and _, not starting with a digit)")
            return {'CANCELLED'}
        nodes = custom_nodes(context)
        added = []
        for node in nodes:
            if name in node.keys():
                self.report({'WARNING'}, f"{node.name} already has an attribute '{name}'")
                continue
            value = self.default
            if self.data_type != 'BOOL':
                if self.use_min:
                    value = max(value, self.minimum)
                if self.use_max:
                    value = min(value, self.maximum)
            node[name] = bool(value) if self.data_type == 'BOOL' else int(value) if self.data_type == 'INT' \
                else float(value)
            set_limits(node, name, self.data_type, self.use_min, self.minimum, self.use_max, self.maximum,
                       value)
            added.append(node.name)
        if not added:
            return {'CANCELLED'}
        cb.rebuild_rows()
        self.report({'INFO'}, f"Added {cb.nice_name(name)} to {', '.join(added)}")
        return {'FINISHED'}


def _rename_paths(ob, old, new, prefix=""):
    """Animation / driver paths of ``prefix["old"]`` on the object -> ``prefix["new"]``."""
    a, b = f'{prefix}["{old}"]', f'{prefix}["{new}"]'
    ad = ob.animation_data
    if ad is None:
        return
    from .. import compat
    fcs = list(ad.drivers) + compat.id_fcurves(ob)
    for fc in fcs:
        if fc.data_path == a:
            fc.data_path = b


def _rename_driver_targets(id_data, old_path, new_path):
    for ob in bpy.data.objects:
        ad = ob.animation_data
        for fc in (ad.drivers if ad else ()):
            for var in fc.driver.variables:
                for t in var.targets:
                    if t.id == id_data and t.data_path == old_path:
                        t.data_path = new_path


class ALLSET_OT_edit_attribute(_AttributeLimits, bpy.types.Operator):
    """Maya Edit Attribute: rename the attribute selected in the Channel Box and change its limits"""
    bl_idname = "allset.edit_attribute"
    bl_label = "Edit Attribute"
    bl_options = {'REGISTER', 'UNDO'}

    attribute: StringProperty(name="Attribute", options={'SKIP_SAVE'})
    long_name: StringProperty(name="Long name")

    @classmethod
    def poll(cls, context):
        node = cb.lead(context)
        return node is not None and bool(selected_custom(context, node))

    def invoke(self, context, event):
        node = cb.lead(context)
        self.attribute = selected_custom(context, node)[0]
        self.long_name = self.attribute
        (self.data_type, self.use_min, lo, self.use_max, hi, default) = limits(node, self.attribute)
        self.minimum, self.maximum = (lo if self.use_min else 0.0), (hi if self.use_max else 1.0)
        self.default = float(default)
        return context.window_manager.invoke_props_dialog(
            self, title=f"Edit Attribute: {node.name}.{self.attribute}", confirm_text="OK", width=320)

    def draw(self, context):
        lay = self.layout
        lay.prop(self, "long_name")
        lay.label(text="Numeric Attribute Properties")
        self.draw_limits(lay)

    def execute(self, context):
        old, new = self.attribute, self.long_name.strip()
        if not old:
            node = cb.lead(context)
            names = selected_custom(context, node) if node else []
            if not names:
                return {'CANCELLED'}
            old = names[0]
            new = new or old
        if not NAME_RE.match(new):
            self.report({'ERROR'}, f"Edit Attribute: '{new}' is not a valid attribute name")
            return {'CANCELLED'}
        for node in custom_nodes(context):
            if old not in node.keys():
                continue
            if new != old:
                if new in node.keys():
                    self.report({'WARNING'}, f"{node.name} already has an attribute '{new}'")
                    continue
                ui = node.id_properties_ui(old).as_dict()
                node[new] = node[old]
                node.id_properties_ui(new).update(**{k: v for k, v in ui.items() if k != "subtype"})
                del node[old]
                ob = node.id_data
                prefix = node.path_from_id() if cb.is_bone(node) else ""
                _rename_paths(ob, old, new, prefix)
                _rename_driver_targets(ob, f'{prefix}["{old}"]', f'{prefix}["{new}"]')
            set_limits(node, new, self.data_type, self.use_min, self.minimum, self.use_max, self.maximum,
                       self.default)
        cb.set_selected_channels([cb.CUSTOM_PREFIX + new if k == cb.CUSTOM_PREFIX + old else k
                                  for k in cb.selected_channels(context)], context)
        return {'FINISHED'}


class ALLSET_OT_delete_attribute(bpy.types.Operator):
    """Maya Delete Attribute: delete the attributes selected in the Channel Box (with their keys and drivers)"""
    bl_idname = "allset.delete_attribute"
    bl_label = "Delete Attribute"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        node = cb.lead(context)
        return node is not None and bool(selected_custom(context, node))

    def execute(self, context):
        names = selected_custom(context, cb.lead(context))
        count = 0
        for node in custom_nodes(context):
            for name in names:
                if name not in node.keys():
                    continue
                key = cb.CUSTOM_PREFIX + name
                ad = node.id_data.animation_data
                fc = cb.driver(node, key)
                if fc is not None:
                    ad.drivers.remove(fc)
                fc = cb.fcurve(node, key)
                if fc is not None:
                    cb._fcurves(node).remove(fc)   # the whole curve, not just this frame's key
                del node[name]
                count += 1
        cb.set_selected_channels([k for k in cb.selected_channels(context)
                                  if k[len(cb.CUSTOM_PREFIX):] not in names], context)
        self.report({'INFO'}, f"Deleted {count} attribute(s)")
        return {'FINISHED'}


classes = (ALLSET_OT_constrain, ALLSET_OT_blend_shape, ALLSET_OT_quick_rig, ALLSET_OT_add_attribute,
           ALLSET_OT_edit_attribute, ALLSET_OT_delete_attribute)
