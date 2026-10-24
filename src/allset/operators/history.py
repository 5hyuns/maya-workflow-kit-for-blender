# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya Delete History, Delete Non-Deformer History, Edit > Delete (All) by Type.

 Maya history = upstream DG nodes; the closest
Blender equivalent is the modifier stack plus shape keys (blendShape). Delete
History (``delete -ch``, Alt+Shift+D) bakes them; Non-Deformer History
(``BakeNonDefHistory``) bakes the modelling operations and keeps the deformers.
 「계획」 8.
"""

import bpy
from bpy.props import BoolProperty, EnumProperty

from .. import results
from .. import undo_steps
from .display import is_preview

# Modifiers that play the part of Maya deformers (skinCluster, ffd, cluster, wrap,
# nonlinear, deltaMush, shrinkWrap, textureDeformer, wire, ...): kept by
# Delete Non-Deformer History.
DEFORMERS = {'ARMATURE', 'LATTICE', 'HOOK', 'MESH_DEFORM', 'SURFACE_DEFORM', 'CORRECTIVE_SMOOTH',
             'SIMPLE_DEFORM', 'WAVE', 'CAST', 'CURVE', 'SHRINKWRAP', 'DISPLACE', 'SMOOTH',
             'LAPLACIANSMOOTH', 'LAPLACIANDEFORM', 'WARP', 'MESH_CACHE', 'MESH_SEQUENCE_CACHE'}
CLUSTERS = {'HOOK'}
NONLINEARS = {'SIMPLE_DEFORM', 'WAVE', 'CAST'}


def _bake(context, ob, keep):
    """Replace ``ob``'s mesh with its evaluated result, with the modifiers in ``keep``
    (names) switched off for the evaluation and kept afterwards."""
    saved = {}
    for md in ob.modifiers:
        if md.name in keep:
            saved[md.name] = md.show_viewport
            md.show_viewport = False
    dg = context.evaluated_depsgraph_get()
    try:
        mesh = bpy.data.meshes.new_from_object(ob.evaluated_get(dg), preserve_all_data_layers=True,
                                               depsgraph=dg)
    finally:
        for name, show in saved.items():
            ob.modifiers[name].show_viewport = show
    old = ob.data
    for md in [m for m in ob.modifiers if m.name not in keep]:
        ob.modifiers.remove(md)
    ob.data = mesh  # the evaluated copy has no shape keys: the mix is baked in
    name = old.name
    if old.users == 0:
        bpy.data.meshes.remove(old)
    mesh.name = name


def delete_history(context, objects, non_deformer=False):
    """Bake history on mesh ``objects``. Returns (baked, notes)."""
    from . import prim_history
    baked, notes = 0, []
    for ob in objects:
        # The primitive's creation node (polyCube1, makeNurbCircle1) is history too: both kinds drop it, the shape
        # stays as it is (step 129)
        if prim_history.drop(ob) and not ob.modifiers and not (ob.type == 'MESH' and ob.data.shape_keys):
            baked += 1
            continue
        # Smooth Mesh Preview (1/2/3) is a display attribute in Maya, not history
        # (): never baked, always kept (step 15).
        preview = {md.name for md in ob.modifiers if is_preview(md)}
        history = [md for md in ob.modifiers if md.name not in preview]
        if not history and not (ob.type == 'MESH' and ob.data.shape_keys):
            continue
        if ob.type != 'MESH':
            notes.append(f"{ob.name}: not a mesh, modifiers kept")
            continue
        if not non_deformer:
            _bake(context, ob, keep=preview)
            baked += 1
            continue
        prefix = []
        for md in history:
            if md.type in DEFORMERS:
                break
            prefix.append(md.name)
        if not prefix:
            continue
        if ob.data.shape_keys:
            notes.append(f"{ob.name}: has shape keys, modelling modifiers kept")
            continue
        rest = [md.name for md in history if md.name not in prefix]
        if any(ob.modifiers[n].type not in DEFORMERS for n in rest):
            notes.append(f"{ob.name}: modifiers after a deformer kept")
        _bake(context, ob, keep=set(rest) | preview)
        baked += 1
    return baked, notes


def _static(fcurve):
    pts = fcurve.keyframe_points
    return len(pts) > 0 and all(abs(k.co[1] - pts[0].co[1]) < 1e-6 for k in pts)


def _fcurve_owners(action):
    """Collections holding the action's F-curves (layered actions in 4.4+, legacy fallback)."""
    from .. import compat
    return compat.fcurve_owners(action)


def delete_static_channels(ob):
    ad = ob.animation_data
    if ad is None or ad.action is None:
        return 0
    n = 0
    for owner in _fcurve_owners(ad.action):
        for fc in [f for f in owner.fcurves if _static(f)]:
            owner.fcurves.remove(fc)
            n += 1
    return n


TYPES = (
    ('HISTORY', "History", "Bake modifiers and shape keys (Delete History)"),
    ('NON_DEFORMER_HISTORY', "Non-Deformer History", "Bake modelling modifiers, keep deformers"),
    ('CHANNELS', "Channels", "Remove animation"),
    ('STATIC_CHANNELS', "Static Channels", "Remove animation curves whose value never changes"),
    ('CONSTRAINTS', "Constraints", "Remove constraints"),
    ('MOTION_PATHS', "Motion Paths", "Remove motion paths"),
    ('RIGID_BODIES', "Rigid Bodies", "Remove rigid bodies"),
    ('JOINTS', "Joints", "Delete armatures"),
    ('LATTICES', "Lattices", "Delete lattices"),
    ('CAMERAS', "Cameras", "Delete cameras"),
    ('LIGHTS', "Lights", "Delete lights"),
    ('IMAGE_PLANES', "Image Planes", "Delete image empties"),
    ('CLUSTERS', "Clusters", "Remove Hook modifiers"),
    ('NONLINEARS', "Nonlinears", "Remove Simple Deform / Wave / Cast modifiers"),
    ('PARTICLES', "Particles", "Remove particle systems"),
)
_DELETE_OBJECTS = {'JOINTS': lambda o: o.type == 'ARMATURE', 'LATTICES': lambda o: o.type == 'LATTICE',
                   'CAMERAS': lambda o: o.type == 'CAMERA', 'LIGHTS': lambda o: o.type == 'LIGHT',
                   'IMAGE_PLANES': lambda o: o.type == 'EMPTY' and o.empty_display_type == 'IMAGE'}
_REMOVE_MODIFIERS = {'CLUSTERS': CLUSTERS, 'NONLINEARS': NONLINEARS, 'PARTICLES': {'PARTICLE_SYSTEM'}}


def delete_by_type(context, kind, objects):
    """Delete ``kind`` from ``objects``. Returns (count, notes)."""
    objects = list(objects)
    if kind in ('HISTORY', 'NON_DEFORMER_HISTORY'):
        return delete_history(context, objects, kind == 'NON_DEFORMER_HISTORY')
    n = 0
    if kind in _DELETE_OBJECTS:
        for ob in [o for o in objects if _DELETE_OBJECTS[kind](o)]:
            bpy.data.objects.remove(ob)
            n += 1
    elif kind in _REMOVE_MODIFIERS:
        for ob in objects:
            for md in [m for m in ob.modifiers if m.type in _REMOVE_MODIFIERS[kind]]:
                ob.modifiers.remove(md)
                n += 1
    elif kind == 'CHANNELS':
        for ob in objects:
            if ob.animation_data is not None:
                ob.animation_data_clear()
                n += 1
    elif kind == 'STATIC_CHANNELS':
        n = sum(delete_static_channels(ob) for ob in objects)
    elif kind == 'CONSTRAINTS':
        for ob in objects:
            n += len(ob.constraints)
            ob.constraints.clear()
    elif kind == 'MOTION_PATHS':
        targets = [ob for ob in objects if ob.motion_path is not None]
        if targets:
            with context.temp_override(selected_objects=targets, selected_editable_objects=targets):
                bpy.ops.object.paths_clear(only_selected=True)
        n = len(targets)
    elif kind == 'RIGID_BODIES':
        targets = [ob for ob in objects if ob.rigid_body is not None]
        if targets:
            with context.temp_override(selected_objects=targets, object=targets[0],
                                       active_object=targets[0]):
                bpy.ops.rigidbody.objects_remove()
        n = len(targets)
    return n, []


@undo_steps.no_redo_panel      # step 147: no Adjust Last Operation (Maya has none)
class ALLSET_OT_delete_history(bpy.types.Operator):
    """Bake the modifier stack and shape keys into the mesh (Maya Edit > Delete by
    Type > History, Alt+Shift+D)"""
    bl_idname = "allset.delete_history"
    bl_label = "Delete History"
    bl_options = {'REGISTER', 'UNDO'}

    non_deformer: BoolProperty(name="Non-Deformer Only",
                               description="Keep deformers (Armature, Lattice, ...) and shape keys")

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def execute(self, context):
        baked, notes = delete_history(context, context.selected_objects, self.non_deformer)
        for note in notes:
            self.report({'WARNING'}, note)
        results.result(self, f"Deleted history on {baked} object(s)")
        return {'FINISHED'}


class ALLSET_OT_delete_by_type(bpy.types.Operator):
    """Delete one kind of node from the selection or the whole scene
    (Maya Edit > Delete by Type / Delete All by Type)"""
    bl_idname = "allset.delete_by_type"
    bl_label = "Delete by Type"
    bl_options = {'REGISTER', 'UNDO'}

    type: EnumProperty(name="Type", items=TYPES)
    all: BoolProperty(name="All", description="Whole scene instead of the selection")

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def execute(self, context):
        objects = context.scene.objects if self.all else context.selected_objects
        n, notes = delete_by_type(context, self.type, objects)
        for note in notes:
            self.report({'WARNING'}, note)
        results.result(self, f"{self.type.replace('_', ' ').title()}: {n}")
        return {'FINISHED'}


classes = (ALLSET_OT_delete_history, ALLSET_OT_delete_by_type)
