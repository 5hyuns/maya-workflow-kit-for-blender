# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya IK handles and skinning: IK Handle Tool, Pole Vector, Bind / Unbind Skin, Paint Skin Weights, Copy /
Mirror Skin Weights, Copy / Paste Vertex Weights.

-1.3 (7, 8, 11-14), concept 8 (skin = Armature modifier + vertex
groups named after the joints), design  「계획」. A Maya joint is a bone's head (or the
tail of a chain end, step 57); Blender's IK pulls a bone's tail, so a Maya IK handle on end joint J is an IK
constraint on the bone whose tail is J.
"""

import math

import bmesh
import bpy
from bpy.props import BoolProperty, EnumProperty, IntProperty
from bpy_extras import view3d_utils
from mathutils import Vector, kdtree

from . import naming, units

PICK_RADIUS = 25          # px at UI scale 1.0
IK_STATUS = "IK Handle Tool: click the start joint, then the end joint (Esc: cancel)"
EFFECTOR_NOTE = "Blender has no effector node: the IK constraint sits on the bone that ends at the end joint."


def _cb():
    from ..ui import channel_box
    return channel_box


# --- joints (Maya points) on bones -----------------------------------------------------------

def joints_of(arm):
    """[(bone name, 'HEAD' | 'TAIL', world position)]: every bone head, plus the tails of chain ends."""
    mw = arm.matrix_world
    out = []
    for pb in arm.pose.bones:
        out.append((pb.name, 'HEAD', mw @ pb.head))
        if not pb.children:
            out.append((pb.name, 'TAIL', mw @ pb.tail))
    return out


def pick_joint(region, rv3d, armatures, coord, radius):
    """(armature, (bone, 'HEAD'|'TAIL')) of the joint nearest ``coord`` on screen within ``radius`` px."""
    best, best_d = None, radius
    for arm in armatures:
        for name, end, pos in joints_of(arm):
            p = view3d_utils.location_3d_to_region_2d(region, rv3d, pos)
            if p is None:
                continue
            d = (Vector(coord) - p).length
            if d < best_d:
                best, best_d = (arm, (name, end)), d
    return best


def _incoming(arm, joint):
    """The bone whose tail is the joint (None for a root joint)."""
    name, end = joint
    pb = arm.pose.bones[name]
    if end == 'TAIL':
        return pb
    parent = pb.parent
    if parent is not None and (parent.tail - pb.head).length < 1e-5:
        return parent
    return None


def ik_chain(arm, start, end):
    """(IK bone, chain_count) for a Maya IK from joint ``start`` to joint ``end``, or None."""
    if start[1] == 'TAIL':
        return None
    first = arm.pose.bones[start[0]]
    ik_bone = _incoming(arm, end)
    if ik_bone is None:
        return None
    count, b = 1, ik_bone
    while b is not None and b != first:
        b = b.parent
        count += 1
    return (ik_bone, count) if b == first else None


def joint_position(arm, joint):
    pb = arm.pose.bones[joint[0]]
    return arm.matrix_world @ (pb.tail if joint[1] == 'TAIL' else pb.head)


def create_ik(context, arm, start, end):
    """IK constraint + ``ikHandleN`` empty at the end joint; returns the handle (None = not a chain)."""
    chain = ik_chain(arm, start, end)
    if chain is None:
        return None
    ik_bone, count = chain
    handle = bpy.data.objects.new("ikHandle", None)
    context.view_layer.active_layer_collection.collection.objects.link(handle)
    naming.apply_maya_name(handle, "ikHandle", rename_data=False)
    handle.empty_display_type = 'PLAIN_AXES'
    handle.empty_display_size = units.maya_unit(context.scene)
    handle.location = joint_position(arm, end)
    con = ik_bone.constraints.new('IK')
    con.name = handle.name
    con.target = handle
    con.chain_count = count
    con.use_tail = True
    if context.active_object is not None and context.active_object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in context.selected_objects:
        ob.select_set(False)
    handle.select_set(True)
    context.view_layer.objects.active = handle       # Maya: the new handle is selected, W moves it
    return handle


def selected_pair(context):
    """(start, end) joints from two selected pose bones (the ancestor starts, the active ends), or None."""
    cb = _cb()
    arm = cb.pose_armature(context)
    if arm is None:
        return None
    sel = [pb for pb in arm.pose.bones if cb.bone_selected(pb)]
    act = arm.data.bones.active
    if len(sel) != 2 or act is None:
        return None
    end = arm.pose.bones[act.name]
    start = sel[0] if sel[1] == end else sel[1]
    return arm, (start.name, 'HEAD'), (end.name, 'HEAD')


class ALLSET_OT_ik_handle(bpy.types.Operator):
    """Maya IK Handle Tool: click the start joint, then the end joint (or select both joints first)"""
    bl_idname = "allset.ik_handle"
    bl_label = "IK Handle Tool"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        """Without clicks: the two selected joints (scripts, and invoke when two are selected)."""
        pair = selected_pair(context)
        if pair is None:
            self.report({'WARNING'}, "Select the start joint, then the end joint (pose mode)")
            return {'CANCELLED'}
        return self._make(context, *pair)

    def invoke(self, context, event):
        if selected_pair(context) is not None or context.window is None:
            return self.execute(context)
        self._start = None
        self._swallow = False
        context.workspace.status_text_set(IK_STATUS)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def _make(self, context, arm, start, end):
        handle = create_ik(context, arm, start, end)
        if handle is None:
            self.report({'WARNING'}, "The end joint must be below the start joint in the same skeleton")
            return {'CANCELLED'}
        self.report({'INFO'}, f"Created {handle.name}. {EFFECTOR_NOTE}")
        return {'FINISHED'}

    def _pick(self, context, event):
        from .joints import view_under
        hit = view_under(context.window, event.mouse_x, event.mouse_y)
        if hit is None:
            return None
        area, region = hit
        arms = [o for o in context.view_layer.objects if o.type == 'ARMATURE' and o.visible_get()]
        radius = PICK_RADIUS * context.preferences.system.ui_scale
        return pick_joint(region, region.data, arms, (event.mouse_x - region.x, event.mouse_y - region.y),
                          radius)

    def modal(self, context, event):
        if event.type == 'ESC' and event.value == 'PRESS':
            context.workspace.status_text_set(None)
            return {'CANCELLED'}
        if event.type == 'LEFTMOUSE':
            if event.value == 'PRESS' and not (event.alt or event.ctrl or event.shift):
                hit = self._pick(context, event)
                if hit is None:
                    return {'PASS_THROUGH'} if not self._swallow else {'RUNNING_MODAL'}
                self._swallow = True
                arm, joint = hit
                if self._start is None or self._start[0] != arm:
                    self._start = (arm, joint)
                    return {'RUNNING_MODAL'}
                context.workspace.status_text_set(None)
                with context.temp_override(window=context.window):
                    return self._make(context, arm, self._start[1], joint)
            if event.value == 'RELEASE' and self._swallow:
                self._swallow = False
                return {'RUNNING_MODAL'}
        return {'PASS_THROUGH'}


# --- Pole Vector ------------------------------------------------------------------------------

def _signed_angle(v1, v2, normal):
    a = v1.angle(v2)
    return -a if normal.dot(v1.cross(v2)) < 0 else a


def pole_angle(arm, con_bone, count, pole_location):
    """IK pole angle that keeps the chain where it is (first chain bone's X axis to the pole plane)."""
    mw = arm.matrix_world
    base = con_bone
    for _ in range(count - 1):
        base = base.parent
    m = mw @ base.matrix
    head, tail = m.translation, mw @ base.tail
    x_axis = m.to_3x3().col[0]
    ik_tail = mw @ con_bone.tail
    pole_normal = (ik_tail - head).cross(pole_location - head)
    projected = pole_normal.cross(tail - head)
    return _signed_angle(x_axis, projected, tail - head)


def _chain_heads(arm, con_bone, count):
    out, b = [], con_bone
    for _ in range(count):
        if b is None:
            break
        out.append(arm.matrix_world @ b.head)
        out.append(arm.matrix_world @ b.tail)
        b = b.parent
    return out


def set_pole(context, arm, pb, con, pole):
    """Pole target + the pole angle that keeps the chain where it is: the analytic angle's sign and
    half-turn depend on the bone roll, so the candidates are tried and the one that moves the chain
    least is kept (Maya: adding a pole vector doesn't flip the knee)."""
    count = max(con.chain_count, 1)
    context.view_layer.update()
    before = _chain_heads(arm, pb, count)
    a = pole_angle(arm, pb, count, pole.matrix_world.translation)
    con.pole_target = pole
    best = None
    for cand in (a, -a, a + math.pi, -a + math.pi):
        con.pole_angle = math.atan2(math.sin(cand), math.cos(cand))
        context.view_layer.update()
        moved = sum((p - q).length for p, q in zip(before, _chain_heads(arm, pb, count)))
        if best is None or moved < best[0]:
            best = (moved, con.pole_angle)
    con.pole_angle = best[1]
    context.view_layer.update()
    return best[0]


def ik_constraints_on(target):
    """[(armature, pose bone, IK constraint)] whose IK target is ``target``."""
    out = []
    for ob in bpy.data.objects:
        if ob.type != 'ARMATURE' or ob.pose is None:
            continue
        for pb in ob.pose.bones:
            for con in pb.constraints:
                if con.type == 'IK' and con.target == target:
                    out.append((ob, pb, con))
    return out


class ALLSET_OT_pole_vector(bpy.types.Operator):
    """Maya Pole Vector constraint: select the pole object, then the IK handle"""
    bl_idname = "allset.pole_vector"
    bl_label = "Pole Vector"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and context.active_object is not None

    def execute(self, context):
        handle = context.active_object
        poles = [o for o in context.selected_objects if o is not handle]
        found = ik_constraints_on(handle)
        if not poles or not found:
            self.report({'WARNING'}, "Select the pole object, then the IK handle")
            return {'CANCELLED'}
        pole = poles[0]
        for arm, pb, con in found:
            set_pole(context, arm, pb, con, pole)
        self.report({'INFO'}, f"{pole.name} is the pole vector of {handle.name}")
        return {'FINISHED'}


# --- Bind / Unbind Skin -------------------------------------------------------------------------

def armature_modifier(mesh):
    return next((m for m in mesh.modifiers if m.type == 'ARMATURE' and m.object is not None), None)


def bind_skin(context, arm, meshes, max_influences=5, only_bones=None):
    """Smooth bind: automatic weights, the meshes stay where they are in the hierarchy (Maya skinCluster)."""
    if context.active_object is not None and context.active_object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in context.selected_objects:
        ob.select_set(False)
    for ob in (*meshes, arm):
        ob.select_set(True)
    context.view_layer.objects.active = arm
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')
    arm.select_set(False)
    context.view_layer.objects.active = meshes[-1]
    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')   # Maya doesn't parent the skin to the joints
    bones = {b.name for b in arm.data.bones}
    for mesh in meshes:
        if only_bones:
            for vg in list(mesh.vertex_groups):
                if vg.name in bones and vg.name not in only_bones:
                    mesh.vertex_groups.remove(vg)
        context.view_layer.objects.active = mesh
        if mesh.vertex_groups:
            bpy.ops.object.vertex_group_limit_total(group_select_mode='ALL', limit=max_influences)
            bpy.ops.object.vertex_group_normalize_all(group_select_mode='ALL', lock_active=False)
    arm.select_set(True)
    return meshes


class ALLSET_OT_bind_skin(bpy.types.Operator):
    """Maya Bind Skin: the selected skeleton and meshes, in any order (automatic weights, no parenting)"""
    bl_idname = "allset.bind_skin"
    bl_label = "Bind Skin"
    bl_options = {'REGISTER', 'UNDO'}

    bind_to: EnumProperty(name="Bind To", items=(("HIERARCHY", "Joint Hierarchy", "Every joint of the skeleton"),
                                                 ("SELECTED", "Selected Joints", "Only the joints selected in "
                                                  "pose mode")), default="HIERARCHY")
    max_influences: IntProperty(name="Max Influences", default=5, min=1, max=30)

    def execute(self, context):
        cb = _cb()
        arm = cb.pose_armature(context)
        picked = [pb.name for pb in arm.pose.bones if cb.bone_selected(pb)] if arm is not None else []
        sel = list(context.selected_objects)
        if arm is None:
            arm = next((o for o in sel if o.type == 'ARMATURE'), None)
        meshes = [o for o in sel if o.type == 'MESH']
        if arm is None or not meshes:
            self.report({'WARNING'}, "Select a skeleton and the meshes to bind")
            return {'CANCELLED'}
        only = set(picked) if self.bind_to == "SELECTED" and picked else None
        bind_skin(context, arm, meshes, self.max_influences, only)
        self.report({'INFO'}, f"Bound {len(meshes)} mesh(es) to {arm.name}")
        return {'FINISHED'}


class ALLSET_OT_unbind_skin(bpy.types.Operator):
    """Maya Unbind Skin: remove the Armature modifier and the joint weight groups"""
    bl_idname = "allset.unbind_skin"
    bl_label = "Unbind Skin"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        n = 0
        for mesh in [o for o in context.selected_objects if o.type == 'MESH']:
            for mod in [m for m in mesh.modifiers if m.type == 'ARMATURE']:
                bones = {b.name for b in mod.object.data.bones} if mod.object else set()
                for vg in [g for g in mesh.vertex_groups if g.name in bones]:
                    mesh.vertex_groups.remove(vg)
                mesh.modifiers.remove(mod)
                n += 1
        self.report({'INFO'}, f"Unbound {n} skin(s)")
        return {'FINISHED'} if n else {'CANCELLED'}


# --- Paint Skin Weights --------------------------------------------------------------------------

def skinned_mesh(context):
    ob = context.active_object
    if ob is not None and ob.type == 'MESH' and armature_modifier(ob):
        return ob
    return next((o for o in context.selected_objects if o.type == 'MESH' and armature_modifier(o)), None)


def influences(mesh):
    """Vertex groups that are joints of the mesh's skeleton (Maya: the skinCluster influences)."""
    mod = armature_modifier(mesh)
    if mod is None:
        return []
    bones = {b.name for b in mod.object.data.bones}
    return [vg for vg in mesh.vertex_groups if vg.name in bones]


class ALLSET_OT_paint_skin_weights(bpy.types.Operator):
    """Maya Paint Skin Weights: weight paint the skinned mesh with its skeleton posable (Ctrl+click picks a joint)"""
    bl_idname = "allset.paint_skin_weights"
    bl_label = "Paint Skin Weights"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.mode == 'PAINT_WEIGHT':
            bpy.ops.paint.weight_paint_toggle()          # Maya: leaving the paint tool
            return {'FINISHED'}
        mesh = skinned_mesh(context)
        if mesh is None:
            self.report({'WARNING'}, "Select a skinned mesh (Skin > Bind Skin first)")
            return {'CANCELLED'}
        arm = armature_modifier(mesh).object
        if context.active_object is not None and context.active_object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        for ob in context.selected_objects:
            ob.select_set(False)
        arm.select_set(True)
        mesh.select_set(True)
        context.view_layer.objects.active = mesh
        bpy.ops.paint.weight_paint_toggle()              # the skeleton goes to pose mode with it
        if mesh.vertex_groups.active is None and influences(mesh):
            mesh.vertex_groups.active_index = influences(mesh)[0].index
        # Maya Bind Skin makes the skinCluster with Normalize Weights = Interactive (normalizeWeights 1): painting a
        # joint takes weight from the others so every vertex keeps a total of 1 (#20, step 129). Blender's factory
        # Auto Normalize is off; Skin > Normalize Weights > Disable still turns it off while painting.
        context.tool_settings.use_auto_normalize = True
        return {'FINISHED'}


class ALLSET_OT_flood_weights(bpy.types.Operator):
    """Maya Paint Skin Weights Flood: the Value on every vertex for the selected joint; with weight normalization on
    (Maya Interactive) the other joints make room so every vertex keeps a total weight of 1"""
    bl_idname = "allset.flood_weights"
    bl_label = "Flood"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        return context.mode == 'PAINT_WEIGHT' and ob is not None and ob.vertex_groups.active is not None

    def execute(self, context):
        res = bpy.ops.paint.weight_set()                 # Blender's fill ignores Auto Normalize (checked, step 129)
        if res != {'FINISHED'}:
            return res
        if context.tool_settings.use_auto_normalize:
            bpy.ops.object.vertex_group_normalize_all(group_select_mode='BONE_DEFORM', lock_active=True)
        return {'FINISHED'}


# --- Copy / Mirror Skin Weights, Copy / Paste Vertex Weights -----------------------------------------

class ALLSET_OT_copy_skin_weights(bpy.types.Operator):
    """Maya Copy Skin Weights: select the source mesh, then the destination"""
    bl_idname = "allset.copy_skin_weights"
    bl_label = "Copy Skin Weights"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def execute(self, context):
        dst = context.active_object
        srcs = [o for o in context.selected_objects if o is not dst and o.type == 'MESH' and armature_modifier(o)]
        if dst is None or dst.type != 'MESH' or not srcs:
            self.report({'WARNING'}, "Select the skinned source mesh, then the destination mesh")
            return {'CANCELLED'}
        if armature_modifier(dst) is None:
            mod = dst.modifiers.new("Armature", 'ARMATURE')
            mod.object = armature_modifier(srcs[0]).object
        bpy.ops.object.data_transfer(use_reverse_transfer=True, data_type='VGROUP_WEIGHTS', use_create=True,
                                     vert_mapping='POLYINTERP_NEAREST',
                                     # reverse transfer swaps the two layer enums (checked, tmp/probe58/dt.py)
                                     layers_select_src='NAME', layers_select_dst='ALL')
        self.report({'INFO'}, f"Copied skin weights to {dst.name}")
        return {'FINISHED'}


# Maya mirror plane (Y-up) -> Blender axis index (Z-up): YZ = x, XY = Maya z = Blender y, XZ = Maya y = Blender z
PLANE_AXIS = {"YZ": 0, "XY": 1, "XZ": 2}


def _reflect(v, axis):
    v = Vector(v)
    v[axis] = -v[axis]
    return v


def mirror_group_names(arm, axis, tol=1e-3):
    """Joint name -> the joint at the mirrored place (itself for joints on the plane)."""
    mw = arm.matrix_world
    bones = [(b.name, mw @ b.head_local, mw @ b.tail_local) for b in arm.data.bones]
    scale = max(max((h - t).length for _n, h, t in bones), 1e-6) if bones else 1.0
    out = {}
    for name, h, t in bones:
        rh, rt = _reflect(h, axis), _reflect(t, axis)
        out[name] = next((n for n, h2, t2 in bones if (h2 - rh).length < tol * scale and (t2 - rt).length < tol * scale),
                         name)
    return out


def mirror_weights(mesh, axis=0, positive_to_negative=True):
    """Copy the weights of one side onto the other (Maya Mirror Skin Weights); count of vertices written."""
    mod = armature_modifier(mesh)
    pair = mirror_group_names(mod.object, axis) if mod else {}
    mw = mesh.matrix_world
    verts = mesh.data.vertices
    world = [mw @ v.co for v in verts]
    tree = kdtree.KDTree(len(world))
    for i, p in enumerate(world):
        tree.insert(p, i)
    tree.balance()
    groups = mesh.vertex_groups
    names = {vg.index: vg.name for vg in groups}
    eps = 1e-6
    n = 0
    for v in verts:
        side = world[v.index][axis]
        if (side <= eps) if positive_to_negative else (side >= -eps):
            continue
        _co, j, _d = tree.find(_reflect(world[v.index], axis))
        if j is None or j == v.index:
            continue
        weights = [(names[g.group], g.weight) for g in v.groups]
        for vg in groups:
            vg.remove([j])
        for name, w in weights:
            target = groups.get(pair.get(name, name))
            if target is not None:
                target.add([j], w, 'REPLACE')
        n += 1
    return n


class ALLSET_OT_mirror_skin_weights(bpy.types.Operator):
    """Maya Mirror Skin Weights: copy one side's weights onto the other, joints paired by position"""
    bl_idname = "allset.mirror_skin_weights"
    bl_label = "Mirror Skin Weights"
    bl_options = {'REGISTER', 'UNDO'}

    plane: EnumProperty(name="Mirror Across", items=[(k, k, "") for k in ("XY", "YZ", "XZ")], default="YZ")
    positive_to_negative: BoolProperty(name="Direction: Positive to Negative", default=True)

    @classmethod
    def poll(cls, context):
        return context.mode in {'OBJECT', 'PAINT_WEIGHT'}

    def execute(self, context):
        mesh = skinned_mesh(context)
        if mesh is None:
            self.report({'WARNING'}, "Select a skinned mesh")
            return {'CANCELLED'}
        n = mirror_weights(mesh, PLANE_AXIS[self.plane], self.positive_to_negative)
        mesh.data.update()
        self.report({'INFO'}, f"Mirrored the weights of {n} vertices")
        return {'FINISHED'}


_VERTEX_CLIPBOARD = {}


def _edit_bmesh(context):
    ob = context.edit_object
    if ob is None or ob.type != 'MESH':
        return None, None, None
    bm = bmesh.from_edit_mesh(ob.data)
    return ob, bm, bm.verts.layers.deform.verify()


class ALLSET_OT_copy_vertex_weights(bpy.types.Operator):
    """Maya Copy Vertex Weights: remember the active vertex's joint weights"""
    bl_idname = "allset.copy_vertex_weights"
    bl_label = "Copy Vertex Weights"

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def execute(self, context):
        ob, bm, layer = _edit_bmesh(context)
        act = bm.select_history.active
        if not isinstance(act, bmesh.types.BMVert):
            act = next((v for v in bm.verts if v.select), None)
        if act is None:
            self.report({'WARNING'}, "Select a vertex")
            return {'CANCELLED'}
        names = {vg.index: vg.name for vg in ob.vertex_groups}
        _VERTEX_CLIPBOARD.clear()
        _VERTEX_CLIPBOARD.update({names[i]: w for i, w in act[layer].items() if i in names})
        self.report({'INFO'}, f"Copied {len(_VERTEX_CLIPBOARD)} weight(s)")
        return {'FINISHED'}


class ALLSET_OT_paste_vertex_weights(bpy.types.Operator):
    """Maya Paste Vertex Weights: give the selected vertices the copied joint weights"""
    bl_idname = "allset.paste_vertex_weights"
    bl_label = "Paste Vertex Weights"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH' and bool(_VERTEX_CLIPBOARD)

    def execute(self, context):
        ob, bm, layer = _edit_bmesh(context)
        idx = {}
        for name in _VERTEX_CLIPBOARD:
            vg = ob.vertex_groups.get(name) or ob.vertex_groups.new(name=name)
            idx[name] = vg.index
        n = 0
        for v in bm.verts:
            if v.select:
                dv = v[layer]
                dv.clear()
                for name, w in _VERTEX_CLIPBOARD.items():
                    dv[idx[name]] = w
                n += 1
        bmesh.update_edit_mesh(ob.data)
        self.report({'INFO'}, f"Pasted weights on {n} vertices")
        return {'FINISHED'}


classes = (ALLSET_OT_ik_handle, ALLSET_OT_pole_vector, ALLSET_OT_bind_skin, ALLSET_OT_unbind_skin,
           ALLSET_OT_paint_skin_weights, ALLSET_OT_flood_weights, ALLSET_OT_copy_skin_weights, ALLSET_OT_mirror_skin_weights,
           ALLSET_OT_copy_vertex_weights, ALLSET_OT_paste_vertex_weights)
