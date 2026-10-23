# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya Skeleton / Skin / Deform commands with Maya-measured results (step 110, docs/steps/step_110.md 「계획」 5-7).

research/maya/re/modeling_rigging_110.md §6 (Reroot, Preferred Angle, IK Spline Handle), §7 (Hammer, Add / Remove
Influence, Remove Unused Influences), §8 (Cluster, Soft Mod; Nonlinear lives in ``menu_items``). A Maya joint is a
bone head (or a chain end's tail), research/maya/workflows/rigging.md §4; skin = Armature modifier + vertex groups
named after the joints.
"""

import math

import bmesh
import bpy
from mathutils import Matrix, Vector

from . import naming, units
from .joints import _InEditMode

PREFERRED_PROP = "allset_preferred_angle"
PREFERRED_NOTE = ("Blender's IK bends from the rest pose: the preferred angle is stored and restored by Assume "
                  "Preferred Angle, the solver doesn't read it.")
SOFT_MOD_RADIUS = 5.0          # Maya softMod falloffRadius default (Maya units)
SPLINE_SAMPLES = 200           # polyline samples for the IK Spline curve fit


def _cb():
    from ..ui import channel_box
    return channel_box


def _selected_bones(arm):
    cb = _cb()
    return [pb for pb in arm.pose.bones if cb.bone_selected(pb)]


def _armature(context):
    ob = context.active_object
    return ob if ob is not None and ob.type == 'ARMATURE' else None


# --- Reroot Skeleton ---------------------------------------------------------------------------

def reroot(arm, name):
    """Make the joint at the head of bone ``name`` the root: the bones on the way to the old root are reversed and
    re-parented (joint positions unchanged, Maya ``reroot``). Bone names stay. Returns False if already a root."""
    with _InEditMode(arm) as ebs:
        b = ebs[name]
        path, p = [], b.parent
        while p is not None:
            path.append(p)
            p = p.parent
        if not path:
            return False
        on_path = {eb.name for eb in path} | {b.name}
        others = {eb.name: [c.name for c in eb.children if c.name not in on_path] for eb in path}
        old_tail = {eb.name: eb.tail.copy() for eb in path}
        b.use_connect = False
        b.parent = None
        for eb in path:
            eb.use_connect = False
            eb.parent = None
        for eb in path:
            head, tail = eb.head.copy(), eb.tail.copy()
            eb.head, eb.tail = tail, head
        for i, eb in enumerate(path):
            if i > 0:
                eb.parent = path[i - 1]
                eb.use_connect = True
        # the other children of a path bone hang at its old tail = the previous reversed bone's tail
        for i, eb in enumerate(path):
            for cname in others[eb.name]:
                c = ebs[cname]
                at_tail = (c.head - old_tail[eb.name]).length < 1e-5
                if at_tail:
                    c.use_connect = False
                    c.parent = path[i - 1] if i > 0 else None
    return True


class ALLSET_OT_reroot_skeleton(bpy.types.Operator):
    """Make the selected joint the root of its skeleton (Maya Skeleton > Reroot Skeleton)"""
    bl_idname = "allset.reroot_skeleton"
    bl_label = "Reroot Skeleton"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _armature(context) is not None

    def execute(self, context):
        arm = _armature(context)
        act = arm.data.bones.active
        if act is None:
            self.report({'WARNING'}, "Select a joint")
            return {'CANCELLED'}
        if not reroot(arm, act.name):
            self.report({'INFO'}, f"{act.name} is already a root")
        return {'FINISHED'}


# --- Set / Assume Preferred Angle -----------------------------------------------------------------

def _euler(pb):
    if pb.rotation_mode == 'QUATERNION':
        return pb.rotation_quaternion.to_euler()
    if pb.rotation_mode == 'AXIS_ANGLE':
        w, x, y, z = pb.rotation_axis_angle
        return Matrix.Rotation(w, 3, Vector((x, y, z))).to_euler()
    return pb.rotation_euler.copy()


def _set_euler(pb, e):
    if pb.rotation_mode == 'QUATERNION':
        pb.rotation_quaternion = e.to_quaternion()
    elif pb.rotation_mode == 'AXIS_ANGLE':
        axis, angle = e.to_quaternion().to_axis_angle()
        pb.rotation_axis_angle = (angle, *axis)
    else:
        pb.rotation_euler = e


def _with_children(bones):
    out = []
    for pb in bones:
        for b in (pb, *pb.children_recursive):
            if b not in out:
                out.append(b)
    return out


def set_preferred(bones):
    """Maya ``joint -e -spa -ch``: preferredAngle = the current rotation, on the joints and their children."""
    for pb in _with_children(bones):
        pb[PREFERRED_PROP] = [math.degrees(a) for a in _euler(pb)]


def assume_preferred(bones):
    """Maya ``joint -e -apa -ch``: rotation = preferredAngle (joints without one keep their rotation)."""
    from mathutils import Euler
    for pb in _with_children(bones):
        if PREFERRED_PROP in pb:
            d = pb[PREFERRED_PROP]
            _set_euler(pb, Euler([math.radians(a) for a in d], _euler(pb).order))


class _PoseBones:
    @classmethod
    def poll(cls, context):
        return _cb().pose_armature(context) is not None

    def bones(self, context):
        arm = _cb().pose_armature(context)
        bones = _selected_bones(arm) if arm else []
        if not bones and arm is not None:
            bones = [pb for pb in arm.pose.bones if pb.parent is None]   # Maya: the skeleton when no joint picked
        return bones


class ALLSET_OT_set_preferred_angle(_PoseBones, bpy.types.Operator):
    """Remember the selected joints' current rotation as their preferred angle (Maya Skeleton > Set Preferred
    Angle)"""
    bl_idname = "allset.set_preferred_angle"
    bl_label = "Set Preferred Angle"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        set_preferred(self.bones(context))
        self.report({'INFO'}, PREFERRED_NOTE)
        return {'FINISHED'}


class ALLSET_OT_assume_preferred_angle(_PoseBones, bpy.types.Operator):
    """Turn the selected joints back to their preferred angle (Maya Skeleton > Assume Preferred Angle)"""
    bl_idname = "allset.assume_preferred_angle"
    bl_label = "Assume Preferred Angle"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        assume_preferred(self.bones(context))
        return {'FINISHED'}


# --- IK Spline Handle ----------------------------------------------------------------------------

def _resample(points, n):
    seg = [(points[i + 1] - points[i]).length for i in range(len(points) - 1)]
    total = sum(seg) or 1.0
    out, i, acc = [], 0, 0.0
    for k in range(n + 1):
        d = total * k / n
        while i < len(seg) - 1 and acc + seg[i] < d:
            acc += seg[i]
            i += 1
        t = 0.0 if seg[i] == 0 else min(1.0, (d - acc) / seg[i])
        out.append((points[i].lerp(points[i + 1], t), k / n))
    return out


def fit_cubic(points):
    """One-span cubic (4 control points) with its ends on the first / last point and the middle two a least-squares
    fit of the polyline (Maya's IK Spline curve: spans 1, degree 3, modeling_rigging_110.md §6)."""
    p0, p3 = points[0], points[-1]
    a11 = a12 = a22 = 0.0
    r1, r2 = Vector(), Vector()
    for p, t in _resample(points, SPLINE_SAMPLES):
        b0, b1, b2, b3 = (1 - t) ** 3, 3 * t * (1 - t) ** 2, 3 * t * t * (1 - t), t ** 3
        rest = p - p0 * b0 - p3 * b3
        a11 += b1 * b1
        a12 += b1 * b2
        a22 += b2 * b2
        r1 += rest * b1
        r2 += rest * b2
    det = a11 * a22 - a12 * a12
    if abs(det) < 1e-12:
        return [p0, p0.lerp(p3, 1 / 3), p0.lerp(p3, 2 / 3), p3]
    return [p0, (r1 * a22 - r2 * a12) / det, (r2 * a11 - r1 * a12) / det, p3]


def create_spline_ik(context, arm, start, end):
    """``curve1`` through the chain + a Spline IK constraint ``ikHandleN`` on the bone ending at the end joint."""
    from .skin import ik_chain
    chain = ik_chain(arm, start, end)
    if chain is None:
        return None
    ik_bone, count = chain
    bones, b = [], ik_bone
    for _ in range(count):
        bones.append(b)
        b = b.parent
    bones.reverse()
    mw = arm.matrix_world
    pts = [mw @ pb.head for pb in bones] + [mw @ ik_bone.tail]
    cvs = fit_cubic(pts)
    data = bpy.data.curves.new("curveShape", 'CURVE')
    data.dimensions = '3D'
    sp = data.splines.new('NURBS')
    sp.points.add(3)
    for p, c in zip(sp.points, cvs):
        p.co = (c.x, c.y, c.z, 1.0)
    sp.order_u = 4
    sp.use_endpoint_u = True
    curve = bpy.data.objects.new("curve", data)
    context.view_layer.active_layer_collection.collection.objects.link(curve)
    naming.apply_maya_name(curve, "curve")
    taken = {c.name for o in bpy.data.objects if o.pose for p in o.pose.bones for c in p.constraints}
    taken |= {o.name for o in bpy.data.objects}
    con = ik_bone.constraints.new('SPLINE_IK')
    con.name = f"ikHandle{naming.next_number('ikHandle', taken)}"
    con.target = curve
    con.chain_count = count
    con.y_scale_mode = 'BONE_ORIGINAL'      # Maya: no stretch by default
    con.xz_scale_mode = 'NONE'
    con.use_curve_radius = False
    return con, curve


class ALLSET_OT_ik_spline_handle(bpy.types.Operator):
    """Create a spline IK from the start joint to the end joint with a curve through the chain (select both
    joints; Maya Skeleton > Create IK Spline Handle)"""
    bl_idname = "allset.ik_spline_handle"
    bl_label = "Create IK Spline Handle"
    bl_options = {'REGISTER', 'UNDO'}

    # Maya IK Spline Handle Tool "Root on curve" (factory on, research/maya/re/option_boxes_140.md:213-218): off lets
    # the root joint keep its place off the curve = Blender's Chain Offset
    root_on_curve: bpy.props.BoolProperty(name="Root on curve", default=True)

    def execute(self, context):
        from .skin import selected_pair
        pair = selected_pair(context)
        if pair is None:
            self.report({'WARNING'}, "Select the start joint, then the end joint (pose mode)")
            return {'CANCELLED'}
        res = create_spline_ik(context, *pair)
        if res is None:
            self.report({'WARNING'}, "The end joint must be below the start joint in the same skeleton")
            return {'CANCELLED'}
        con, curve = res
        con.use_chain_offset = not self.root_on_curve
        self.report({'INFO'}, f"Created {con.name} with {curve.name} (Spline IK constraint; Blender has no "
                              "effector node)")
        return {'FINISHED'}


# --- Skin: influences, Hammer ----------------------------------------------------------------------

def _skin_armature(mesh):
    md = next((m for m in mesh.modifiers if m.type == 'ARMATURE' and m.object is not None), None)
    return md.object if md else None


def _skinned(context):
    return [o for o in context.selected_objects if o.type == 'MESH' and _skin_armature(o) is not None]


def _influence_groups(mesh):
    arm = _skin_armature(mesh)
    bones = set(arm.data.bones.keys()) if arm else set()
    return [g for g in mesh.vertex_groups if g.name in bones]


def normalize(mesh, groups=None):
    """Weights of each vertex over the influence groups sum to 1 (Maya normalizeWeights Interactive)."""
    idx = {g.index for g in (groups if groups is not None else _influence_groups(mesh))}
    for v in mesh.data.vertices:
        ws = [g for g in v.groups if g.group in idx]
        total = sum(g.weight for g in ws)
        if total > 1e-12:
            for g in ws:
                g.weight /= total


def add_influence(mesh, bone_names):
    """Each joint becomes an influence with weight 0 on every vertex (Maya Add Influence default)."""
    added = []
    all_verts = [v.index for v in mesh.data.vertices]
    for name in bone_names:
        if name in mesh.vertex_groups:
            continue
        g = mesh.vertex_groups.new(name=name)
        g.add(all_verts, 0.0, 'REPLACE')
        added.append(name)
    return added


def remove_influence(mesh, bone_names):
    removed = []
    for name in bone_names:
        g = mesh.vertex_groups.get(name)
        if g is not None:
            mesh.vertex_groups.remove(g)
            removed.append(name)
    if removed:
        normalize(mesh)
    return removed


def unused_influences(mesh):
    groups = _influence_groups(mesh)
    used = {g.index: False for g in groups}
    for v in mesh.data.vertices:
        for g in v.groups:
            if g.group in used and g.weight > 1e-9:
                used[g.group] = True
    return [g.name for g in groups if not used[g.index]]


def _selected_bone_names(context):
    arm = None
    for o in context.selected_objects:
        if o.type == 'ARMATURE':
            arm = o
    if context.active_object is not None and context.active_object.type == 'ARMATURE':
        arm = context.active_object
    if arm is None:
        return []
    return [b.name for b in arm.data.bones if b.select]


class ALLSET_OT_add_influence(bpy.types.Operator):
    """Add the selected joints to the selected skinned mesh with weight 0 (Maya Skin > Edit Influences > Add
    Influence)"""
    bl_idname = "allset.add_influence"
    bl_label = "Add Influence"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        meshes, names = _skinned(context), _selected_bone_names(context)
        if not meshes or not names:
            self.report({'WARNING'}, "Select the skinned mesh and the joints to add")
            return {'CANCELLED'}
        added = [n for m in meshes for n in add_influence(m, names)]
        self.report({'INFO'}, f"Added {', '.join(added) or 'nothing (already influences)'}")
        return {'FINISHED'}


class ALLSET_OT_remove_influence(bpy.types.Operator):
    """Remove the selected joints from the selected skinned mesh; the weights are renormalised (Maya Skin > Edit
    Influences > Remove Influence)"""
    bl_idname = "allset.remove_influence"
    bl_label = "Remove Influence"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        meshes, names = _skinned(context), _selected_bone_names(context)
        if not meshes or not names:
            self.report({'WARNING'}, "Select the skinned mesh and the joints to remove")
            return {'CANCELLED'}
        for m in meshes:
            remove_influence(m, names)
        return {'FINISHED'}


class ALLSET_OT_remove_unused_influences(bpy.types.Operator):
    """Remove influences that weigh nothing on any vertex (Maya Skin > Edit Influences > Remove Unused
    Influences)"""
    bl_idname = "allset.remove_unused_influences"
    bl_label = "Remove Unused Influences"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        meshes = _skinned(context) or [o for o in context.selected_objects if o.type == 'MESH']
        n = 0
        for m in meshes:
            names = unused_influences(m)
            for name in names:
                m.vertex_groups.remove(m.vertex_groups[name])
            n += len(names)
        self.report({'INFO'}, f"Removed {n} unused influence(s)")
        return {'FINISHED'}


def hammer(bm, deform, groups):
    """Selected vertices take the plain average of their edge neighbours' weights over ``groups`` (Maya Hammer Skin
    Weights, modeling_rigging_110.md §7). Returns the number of changed vertices."""
    new = {}
    for v in (v for v in bm.verts if v.select):
        nbrs = [e.other_vert(v) for e in v.link_edges]
        if not nbrs:
            continue
        avg = {g: sum(n[deform].get(g, 0.0) for n in nbrs) / len(nbrs) for g in groups}
        total = sum(avg.values())
        if total > 1e-12:
            avg = {g: w / total for g, w in avg.items()}
        new[v] = avg
    for v, avg in new.items():
        dv = v[deform]
        for g, w in avg.items():
            if w > 0.0 or g in dv:
                dv[g] = w
    return len(new)


class ALLSET_OT_hammer_weights(bpy.types.Operator):
    """Give the selected vertices the average skin weights of their neighbours (Maya Skin > Hammer Skin Weights)"""
    bl_idname = "allset.hammer_weights"
    bl_label = "Hammer Skin Weights"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        ob = context.edit_object
        return ob is not None and ob.type == 'MESH'

    def execute(self, context):
        ob = context.edit_object
        groups = [g.index for g in (_influence_groups(ob) or ob.vertex_groups)]
        bm = bmesh.from_edit_mesh(ob.data)
        deform = bm.verts.layers.deform.verify()
        n = hammer(bm, deform, groups)
        bmesh.update_edit_mesh(ob.data)
        if not n:
            self.report({'WARNING'}, "Select vertices to hammer")
            return {'CANCELLED'}
        return {'FINISHED'}


# --- Cluster / Soft Mod (Hook modifiers + handle empties) ------------------------------------------

def _hook(context, ob, base, centre_world, vertex_indices=None):
    """Hook modifier ``<base>N`` driven by the empty ``<base>NHandle`` at ``centre_world`` (rest = no change)."""
    taken = {m.name for o in bpy.data.objects for m in o.modifiers} | {o.name for o in bpy.data.objects}
    name = f"{base}{naming.next_number(base, taken)}"
    handle = bpy.data.objects.new(f"{name}Handle", None)
    context.view_layer.active_layer_collection.collection.objects.link(handle)
    handle.empty_display_type = 'PLAIN_AXES'
    handle.empty_display_size = 0.5 * units.maya_unit(context.scene)
    handle.location = centre_world
    context.view_layer.update()
    md = ob.modifiers.new(name, 'HOOK')
    md.object = handle
    md.center = ob.matrix_world.inverted() @ centre_world
    md.matrix_inverse = handle.matrix_world.inverted() @ ob.matrix_world
    if vertex_indices is not None:
        md.vertex_indices_set(vertex_indices)
    return md, handle


def _selection(ob):
    """World centroid of the selected vertices and their indices (object mode: all vertices, the object's centre)."""
    if ob.mode == 'EDIT':
        bm = bmesh.from_edit_mesh(ob.data)
        idx = [v.index for v in bm.verts if v.select]
        cos = [v.co for v in bm.verts if v.select]
    else:
        idx = None
        vs = [v.co for v in ob.data.vertices]          # undeformed points (bound_box follows the modifiers)
        cos = []
        if vs:   # the bounding-box corners: their mean is the box centre
            cos = [Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs))),
                   Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))]
    if not cos:
        return None, None
    c = sum(cos, Vector()) / len(cos)
    return ob.matrix_world @ c, idx


def _select_handle(context, handle):
    if context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for o in context.selected_objects:
        o.select_set(False)
    handle.select_set(True)
    context.view_layer.objects.active = handle


class ALLSET_OT_cluster(bpy.types.Operator):
    """Make a cluster of the selected components (or the whole object): a Hook modifier ``clusterN`` driven by the
    handle ``clusterNHandle`` at their centre (Maya Deform > Cluster)"""
    bl_idname = "allset.cluster"
    bl_label = "Cluster"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        return ob is not None and ob.type in {'MESH', 'LATTICE', 'CURVE', 'SURFACE'}

    def execute(self, context):
        ob = context.active_object
        if ob.type == 'MESH':
            centre, idx = _selection(ob)
        else:
            centre, idx = ob.matrix_world @ (sum((Vector(c) for c in ob.bound_box), Vector()) / 8), None
        if centre is None:
            self.report({'WARNING'}, "Select components or an object")
            return {'CANCELLED'}
        mode = ob.mode
        if mode == 'EDIT':
            bpy.ops.object.mode_set(mode='OBJECT')
        _md, handle = _hook(context, ob, "cluster", centre, idx)
        handle.empty_display_type = 'SPHERE'
        _select_handle(context, handle)       # Maya: the new handle is selected
        return {'FINISHED'}


def cosine_falloff(curve_mapping, steps=10):
    """Hook falloff curve = Maya softMod's smooth curve: weight = (1 + cos(pi d / r)) / 2, input x = 1 - d / r."""
    curve = curve_mapping.curves[0]
    while len(curve.points) > 2:
        curve.points.remove(curve.points[1])
    curve.points[0].location = (0.0, 0.0)
    curve.points[-1].location = (1.0, 1.0)
    for k in range(1, steps):
        x = k / steps
        curve.points.new(x, (1 - math.cos(math.pi * x)) / 2)
    curve_mapping.update()


class ALLSET_OT_soft_mod(bpy.types.Operator):
    """Soft modification at the selection: a Hook modifier ``softModN`` on the whole mesh with Maya's falloff
    (radius 5, smooth) driven by ``softModNHandle`` (Maya Deform > Soft Modification)"""
    bl_idname = "allset.soft_mod"
    bl_label = "Soft Modification"
    bl_options = {'REGISTER', 'UNDO'}

    radius: bpy.props.FloatProperty(name="Falloff Radius", default=SOFT_MOD_RADIUS, min=0.0,
                                    description="Maya units (softMod falloffRadius)")

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        return ob is not None and ob.type == 'MESH'

    def execute(self, context):
        ob = context.active_object
        if ob.mode == 'EDIT':
            centre, _idx = _selection(ob)
            bpy.ops.object.mode_set(mode='OBJECT')
        else:
            centre = ob.matrix_world.translation.copy()
        if centre is None:
            self.report({'WARNING'}, "Select components or an object")
            return {'CANCELLED'}
        # a Hook with neither a vertex group nor indices moves nothing (measured): every vertex, weighted by falloff
        md, handle = _hook(context, ob, "softMod", centre, list(range(len(ob.data.vertices))))
        md.falloff_type = 'CURVE'
        md.falloff_radius = self.radius * units.maya_unit(context.scene)
        cosine_falloff(md.falloff_curve)
        handle.empty_display_type = 'CUBE'
        _select_handle(context, handle)
        return {'FINISHED'}


classes = (ALLSET_OT_reroot_skeleton, ALLSET_OT_set_preferred_angle, ALLSET_OT_assume_preferred_angle,
           ALLSET_OT_ik_spline_handle, ALLSET_OT_add_influence, ALLSET_OT_remove_influence,
           ALLSET_OT_remove_unused_influences, ALLSET_OT_hammer_weights, ALLSET_OT_cluster, ALLSET_OT_soft_mod)
