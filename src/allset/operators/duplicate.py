# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya Duplicate (Ctrl+D), Duplicate Special (Ctrl+Shift+D) and Duplicate with
Transform (Shift+D).

Maya ``duplicateSpecial`` default options (copy,
count 1, group under Parent, T/R = 0, S = 1) and ``shiftD``
(``cmds.duplicate(smartTransform=True)``). Edit > Duplicate Special runs with
the saved options (DuplicateSpecial), no dialog; Blender's Adjust Last Operation
edits them afterwards. Maya duplicates the whole subtree; names count up (``pCube1`` -> ``pCube2``).

What a copy takes from the original's inputs (#347), like Maya:

- Duplicate (Ctrl+D, Shift+D, Smart Duplicate, ``cmds.duplicate``): only the node itself. The copy's geometry is
  what the original shows now (shape-key mix, skin pose, deformers and modelling modifiers baked in); it has no
  history, deformers, shape keys, animation, drivers or constraints, and its channels keep their current values, so
  nothing the original's inputs do moves it. Materials, display settings (the smooth mesh preview) and children stay.
- Duplicate Special > Duplicate input graph: the copy gets its own copies of the inputs (modifiers, shape keys,
  drivers, constraints, its creation node and copies of the animation, so it animates on its own).
- Duplicate Special > Duplicate input connections: the copy shares the original's inputs (the same animation drives
  both).
"""

import bpy
from bpy.props import BoolProperty, EnumProperty, FloatVectorProperty, IntProperty
from mathutils import Euler, Quaternion, Vector

from .. import undo_steps
from . import naming, prim_history
from .freeze import hierarchy
from .group import make_group

# Last duplicates made by this module: {copy name: source name} (smart transform).
PAIRS = {}

# What a copy takes from the original's inputs (see the module docstring)
PLAIN, INPUT_GRAPH, INPUT_CONNECTIONS = 'PLAIN', 'INPUT_GRAPH', 'INPUT_CONNECTIONS'
# Object types whose points take a shape-key mix and deforming modifiers in place (meshes get a baked mesh)
_POINT_TYPES = {'CURVE', 'SURFACE', 'LATTICE'}


def selected_roots(objects):
    chosen = set(objects)
    out = []
    for ob in objects:
        p = ob.parent
        while p is not None and p not in chosen:
            p = p.parent
        if p is None:
            out.append(ob)
    return out


def copy_subtree(root, instance=False, inputs=PLAIN):
    """Copy ``root`` and its descendants (data copied, or shared for an instance). ``inputs``: what the copies take
    from the originals' inputs (``PLAIN``, ``INPUT_GRAPH``, ``INPUT_CONNECTIONS``; an instance shares its data)."""
    new_of = {}
    for ob in hierarchy([root]):
        new = ob.copy()
        if ob.data is not None and not instance:
            new.data = ob.data.copy()
        if not instance and inputs != INPUT_GRAPH:   # no polyCube1 on pCube2: the creation node is an input
            _drop_creation_node(new)
        for coll in ob.users_collection:
            coll.objects.link(new)
        if ob is not root:
            new.parent = new_of[ob.parent]   # matrix_parent_inverse copied with the object
        naming.apply_maya_name(new, naming.base_name(ob.name), rename_data=not instance)
        new_of[ob] = new
    if not instance:
        copies = list(new_of.values())          # parents first
        if inputs == INPUT_GRAPH:
            _own_inputs(copies)
        elif inputs == PLAIN:
            _plain(bpy.context, copies)
    return new_of[root]


def _drop_creation_node(new):
    for idb in (new, new.data):
        for key in (prim_history.KEY, prim_history.PART):
            if idb is not None and key in idb:
                del idb[key]


# --- Duplicate input graph: the copy's own inputs ------------------------------------------------------------

def _anim_ids(ob):
    """The copy's own IDs that can carry animation: the object, its data and the data's shape keys."""
    out = [ob]
    if ob.data is not None:
        out.append(ob.data)
        keys = getattr(ob.data, "shape_keys", None)
        if keys is not None:
            out.append(keys)
    return out


def _own_action(action, made):
    """One copy of ``action`` per duplicate (IDs that shared it share the copy, each with its own slot)."""
    if action not in made:
        made[action] = action.copy()
    return made[action]


def _set_action(holder, action, made):
    """Give ``holder`` (animation data or an NLA strip) a copy of ``action`` on the slot of the same name."""
    slot = getattr(holder, "action_slot", None)
    ident = slot.identifier if slot is not None else None
    holder.action = _own_action(action, made)
    if ident is not None and hasattr(holder, "action_slot"):
        new_slot = next((s for s in holder.action.slots if s.identifier == ident), None)
        if new_slot is not None and holder.action_slot != new_slot:
            holder.action_slot = new_slot


def _own_inputs(copies):
    """Duplicate input graph: the copies keep their modifiers, shape keys, drivers and constraints (Blender copies
    them with the object and data) and get copies of the animation, so they animate on their own; a creation node
    (polyCube1) becomes the copy's own (polyCube2)."""
    made = {}
    for new in copies:
        for idb in _anim_ids(new):
            ad = idb.animation_data
            if ad is None:
                continue
            if ad.action is not None:
                _set_action(ad, ad.action, made)
            for track in ad.nla_tracks:
                for strip in track.strips:
                    if strip.action is not None:
                        _set_action(strip, strip.action, made)
        owner = prim_history.owner_of(new)
        if owner is not None and prim_history.KEY in owner and owner in (new, new.data):
            node = owner[prim_history.KEY]
            node["name"] = prim_history._next_name(node["type"])


# --- Duplicate: the node itself ----------------------------------------------------------------------------

def _history_records(new):
    """Kit records that rebuild a shape from its inputs (modelling history, a loft's curves): not on a plain copy."""
    from . import model_history, surfaces_maya
    if surfaces_maya.LOFT_KEY in new:
        del new[surfaces_maya.LOFT_KEY]
    if new.type == 'MESH':
        for key in (model_history.KEY, model_history.BASE):
            if key in new.data:
                del new.data[key]


def _bakes(new):
    """Modifiers baked into a plain copy's points (everything but the kit's display modifiers)."""
    from .display import is_preview
    return [md for md in new.modifiers if not is_preview(md)]


def _needs_evaluation(new):
    if new.constraints:
        return True
    if new.type == 'MESH' or new.type in _POINT_TYPES:
        return bool(_bakes(new)) or getattr(new.data, "shape_keys", None) is not None
    if new.type == 'ARMATURE' and new.pose is not None:
        return any(pb.constraints for pb in new.pose.bones)
    return False


def _bake_mesh(context, new):
    """The copy's mesh = what it shows now without the display modifiers; the follow of its skin goes into the
    points (its channels stay), like Delete History."""
    from . import history, skin_follow
    from .display import is_preview
    if not _bakes(new) and new.data.shape_keys is None:
        return
    history._bake(context, new, keep={md.name for md in new.modifiers if is_preview(md)})
    skin_follow.detach(new, keep_shape=True)


def _bake_points(context, new):
    """Curves, surfaces and lattices: the shape-key mix and the deforming modifiers go into the points (a modifier
    that builds new geometry can't be applied to them and stays)."""
    with context.temp_override(object=new, active_object=new, selected_objects=[new],
                               selected_editable_objects=[new]):
        if getattr(new.data, "shape_keys", None) is not None:
            bpy.ops.object.shape_key_remove(all=True, apply_mix=True)
        for md in _bakes(new):
            try:
                bpy.ops.object.modifier_apply(modifier=md.name)
            except RuntimeError:
                pass


def _hold_pose(context, arm):
    """An armature copy holds the pose its bone constraints give now in the bones' own channels (Maya's joints keep
    their values; IK handles and constraints are separate nodes), then loses the constraints."""
    pbs = [pb for pb in arm.pose.bones if pb.constraints]
    if not pbs:
        return
    ev = arm.evaluated_get(context.evaluated_depsgraph_get())
    basis = {pb.name: ev.convert_space(pose_bone=pb, matrix=pb.matrix, from_space='POSE', to_space='LOCAL')
             for pb in ev.pose.bones}
    for pb in arm.pose.bones:
        for con in list(pb.constraints):
            pb.constraints.remove(con)
        pb.matrix_basis = basis[pb.name]


def _hold_place(context, new):
    """The copy stays where its constraints put it now, without them."""
    if not new.constraints:
        return
    mw = new.evaluated_get(context.evaluated_depsgraph_get()).matrix_world.copy()
    new.constraints.clear()
    new.matrix_world = mw


def _plain(context, copies):
    """Maya Duplicate: each copy is the node itself, as the original shows now, with nothing that drives it."""
    if any(_needs_evaluation(new) for new in copies):
        context.view_layer.update()            # the copies evaluate like their originals (same inputs still)
    for new in copies:                          # parents first
        if new.type == 'MESH':
            _bake_mesh(context, new)
        elif new.type in _POINT_TYPES:
            _bake_points(context, new)
        elif new.type == 'ARMATURE' and new.pose is not None:
            _hold_pose(context, new)
        _hold_place(context, new)
        for idb in _anim_ids(new):             # the channels keep the values they have now
            if idb.animation_data is not None:
                idb.animation_data_clear()
        _drop_creation_node(new)               # also on a baked mesh
        _history_records(new)


def offset_channels(ob, k, translate, rotate, scale):
    """k-th copy: channels t + k*T, r + k*R, s * S^k (Maya cumulative offsets)."""
    ob.location = Vector(ob.location) + k * Vector(translate)
    q = Euler(tuple(k * a for a in rotate)).to_quaternion()
    if ob.rotation_mode == 'QUATERNION':
        ob.rotation_quaternion = q @ ob.rotation_quaternion
    elif ob.rotation_mode == 'AXIS_ANGLE':
        angle, *axis = ob.rotation_axis_angle
        axis, angle = (q @ Quaternion(axis, angle)).to_axis_angle()
        ob.rotation_axis_angle = (angle, *axis)
    else:
        ob.rotation_euler = tuple(a + k * b for a, b in zip(ob.rotation_euler, rotate))
    ob.scale = tuple(a * b ** k for a, b in zip(ob.scale, scale))


def _select(context, objects):
    for ob in context.selected_objects:
        ob.select_set(False)
    for ob in objects:
        ob.select_set(True)
    if objects:
        context.view_layer.objects.active = objects[-1]


def duplicate(context, instance=False):
    """Copy every selected root with its subtree in place, Maya names; returns the copies (Maya Duplicate: the
    geometry as it shows now, no inputs). Records source pairs so a following Shift+D repeats the move between them."""
    roots = selected_roots(context.selected_objects)
    made, pairs = [], {}
    for root in roots:
        new = copy_subtree(root, instance)
        made.append(new)
        pairs[new.name] = root.name
    PAIRS.clear()
    PAIRS.update(pairs)
    _select(context, made)
    return made


class ALLSET_OT_duplicate(bpy.types.Operator):
    """Duplicate the selection in place with its children: the geometry as it shows now, without history,
    deformers, shape keys or animation; copies are named the Maya way (pCube1 -> pCube2, pCubeShape2) and
    selected (Maya Edit > Duplicate, Ctrl+D)"""
    bl_idname = "allset.duplicate"
    bl_label = "Duplicate"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def execute(self, context):
        if not duplicate(context):
            self.report({'WARNING'}, "Nothing selected")
            return {'CANCELLED'}
        return {'FINISHED'}


@undo_steps.no_redo_panel      # no Adjust Last Operation (Maya has none)
class ALLSET_OT_duplicate_special(bpy.types.Operator):
    """Duplicate with options: copies or instances, number of copies, offsets per
    copy, where to put them, the copies' own or shared inputs (Maya Edit > Duplicate Special)"""
    bl_idname = "allset.duplicate_special"
    bl_label = "Duplicate Special"
    bl_options = {'REGISTER', 'UNDO'}

    geometry_type: EnumProperty(
        name="Geometry Type",
        items=(('COPY', "Copy", "Copy the geometry"),
               ('INSTANCE', "Instance", "Share the geometry (Blender linked duplicate)")))
    group_under: EnumProperty(
        name="Group Under",
        items=(('PARENT', "Parent", "Same parent as the original"),
               ('WORLD', "World", "At the top of the hierarchy"),
               ('NEW_GROUP', "New Group", "Under a new group")))
    translate: FloatVectorProperty(name="Translate", subtype='TRANSLATION', unit='LENGTH')
    rotate: FloatVectorProperty(name="Rotate", subtype='EULER', unit='ROTATION')
    scale: FloatVectorProperty(name="Scale", default=(1.0, 1.0, 1.0), subtype='XYZ')
    copies: IntProperty(name="Number of Copies", default=1, min=1, soft_max=100, max=10000)
    input_graph: BoolProperty(
        name="Duplicate Input Graph",
        description="Each copy gets its own copies of the inputs: modifiers, shape keys, drivers, constraints and "
                    "its own animation. Offsets apply to plain copies only")
    input_connections: BoolProperty(
        name="Duplicate Input Connections",
        description="Each copy shares the original's inputs: the same animation drives both. Offsets apply to "
                    "plain copies only")

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def execute(self, context):
        roots = selected_roots(context.selected_objects)
        if not roots:
            self.report({'WARNING'}, "Nothing selected")
            return {'CANCELLED'}
        instance = self.geometry_type == 'INSTANCE'
        inputs = (PLAIN if instance else INPUT_GRAPH if self.input_graph
                  else INPUT_CONNECTIONS if self.input_connections else PLAIN)
        made, pairs = [], {}
        for root in roots:
            for k in range(1, self.copies + 1):
                new = copy_subtree(root, instance, inputs)
                if inputs == PLAIN:       # Maya: no offsets for copies with their inputs
                    offset_channels(new, k, self.translate, self.rotate, self.scale)
                made.append(new)
                if self.copies == 1:
                    pairs[new.name] = root.name
        context.view_layer.update()
        if self.group_under == 'WORLD':
            from .parenting import unparent
            unparent(made)
        elif self.group_under == 'NEW_GROUP':
            grp = make_group(context, made)
            made = [grp]
        PAIRS.clear()
        PAIRS.update(pairs)
        _select(context, made)
        return {'FINISHED'}


class ALLSET_OT_duplicate_with_transform(bpy.types.Operator):
    """Duplicate and repeat the transform between the last duplicate and its source,
    so repeated use builds an array (Maya Edit > Duplicate with Transform, Shift+D)"""
    bl_idname = "allset.duplicate_with_transform"
    bl_label = "Duplicate with Transform"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def execute(self, context):
        roots = selected_roots(context.selected_objects)
        if not roots:
            self.report({'WARNING'}, "Nothing selected")
            return {'CANCELLED'}
        context.view_layer.update()
        made, pairs = [], {}
        for ob in roots:
            src = bpy.data.objects.get(PAIRS.get(ob.name, ""))
            new = copy_subtree(ob)
            if src is not None and src is not ob:
                delta = ob.matrix_world @ src.matrix_world.inverted_safe()
                new.matrix_world = delta @ ob.matrix_world
            made.append(new)
            pairs[new.name] = ob.name
        PAIRS.clear()
        PAIRS.update(pairs)
        _select(context, made)
        return {'FINISHED'}


classes = (ALLSET_OT_duplicate, ALLSET_OT_duplicate_special, ALLSET_OT_duplicate_with_transform)
