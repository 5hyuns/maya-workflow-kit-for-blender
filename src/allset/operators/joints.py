# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya joints: Joint Tool, Orient Joint, Mirror Joints, joint pick-walk and P / Shift+P.

 (1-6), concept 1 (a Maya joint = a bone of one armature per
skeleton, ``skeleton1`` / ``joint1``, rotate order XYZ, Blender's bone Y points at the child), design
 「계획」. A Maya joint is a point and a Blender bone a segment, so N clicks make N
bones: bone K runs from click K to click K+1, the last (Maya's end joint) gets a short tail along the
previous segment.
"""

import json

import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, StringProperty
from bpy_extras import view3d_utils
from mathutils import Matrix, Vector

from .. import results
from .. import undo_steps
from . import naming, units

JOINT_BASE = "joint"
SKELETON_BASE = "skeleton"
STATUS = "Joint Tool: click to place joints, Enter to finish (Esc: stop)"
AXIS_NOTE = ("Blender joints point their Y axis at the child joint (Maya Primary Axis X): "
             "only the secondary axis can be set.")


def _cb():
    from ..ui import channel_box
    return channel_box


# --- placing joints ---------------------------------------------------------------------------

def click_point(region, rv3d, coord):
    """World point for a click (Maya Joint Tool depth): an orthographic view places on the view plane
    through the origin, a perspective view on the ground (z = 0), else at the origin's depth."""
    origin = Vector((0.0, 0.0, 0.0))
    if rv3d.is_perspective:
        start = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)
        ray = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
        if abs(ray.z) > 1e-6:
            t = -start.z / ray.z
            if t > 0:
                return start + ray * t
    return view3d_utils.region_2d_to_location_3d(region, rv3d, coord, origin)


def taken_joint_names():
    """Joint names of the skeletons that still exist. Maya names are unique among existing nodes: a deleted
    skeleton frees ``joint1`` again (#73) — its armature data stays in ``bpy.data`` with no users until a purge,
    so only armatures an object still uses count."""
    names = set()
    for ob in bpy.data.objects:
        if ob.type != 'ARMATURE' or ob.users == 0:
            continue
        names.update(b.name for b in ob.data.bones)
        if ob.mode == 'EDIT':
            names.update(eb.name for eb in ob.data.edit_bones)
    return names


def next_joint_name(base=JOINT_BASE, extra=()):
    """Lowest free ``jointN`` over every armature (Maya numbers joints scene-wide)."""
    return f"{base}{naming.next_number(base, taken_joint_names() | set(extra))}"


def new_skeleton(context):
    """``skeleton1``: an armature at the origin, selected, active, in edit mode."""
    arm = bpy.data.armatures.new(SKELETON_BASE)
    ob = bpy.data.objects.new(SKELETON_BASE, arm)
    context.view_layer.active_layer_collection.collection.objects.link(ob)
    naming.apply_maya_name(ob, SKELETON_BASE, rename_data=False)
    arm.name = ob.name
    if context.active_object is not None and context.active_object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for other in context.selected_objects:
        other.select_set(False)
    ob.select_set(True)
    context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT')
    return ob


def add_joint(ob, point, parent_name=None, up=Vector((0.0, 0.0, 1.0)), length=1.0):
    """Add a joint (edit bone) at world ``point`` under ``parent_name``; returns its name (the parent's
    name when the click repeats the parent's position). An end joint parent gets its tail moved here."""
    ebs = ob.data.edit_bones
    p = ob.matrix_world.inverted() @ Vector(point)
    parent = ebs.get(parent_name) if parent_name else None
    if parent is not None and (p - parent.head).length < 1e-6:
        return parent.name
    eb = ebs.new(next_joint_name())
    eb.head = p
    if parent is None:
        eb.tail = p + Vector(up).normalized() * length
        return eb.name
    seg = p - parent.head
    if len(parent.children) == 0:
        parent.tail = p                      # the parent was an end joint: it now reaches this one
    eb.parent = parent
    eb.use_connect = (parent.tail - p).length < 1e-6
    eb.tail = p + seg.normalized() * seg.length * 0.5
    return eb.name


def finish(context, ob, names):
    """Pose mode, new joints rotate XYZ (rigging.md:134), the last joint is the only selection."""
    if ob.mode != 'POSE':
        bpy.ops.object.mode_set(mode='POSE')
    cb = _cb()
    for pb in ob.pose.bones:
        if pb.name in names:
            pb.rotation_mode = 'XYZ'
        cb.set_bone_selected(pb, False)
    if names:
        last = ob.pose.bones.get(names[-1])
        if last is not None:
            cb.set_bone_selected(last, True)
            ob.data.bones.active = last.bone


def view_under(window, x, y):
    """(area, WINDOW region) of the 3D View under window position x, y (not the Tool Box column)."""
    from ..ui import toolbox
    for area in window.screen.areas:
        if area.type != 'VIEW_3D' or toolbox.is_toolbox(area.spaces.active):
            continue
        for region in area.regions:
            if region.type == 'WINDOW' and region.x <= x < region.x + region.width \
                    and region.y <= y < region.y + region.height:
                return area, region
    return None


# Maya Joint Tool settings the kit honours (): Secondary Axis Y with
# Secondary Axis World Orientation +Y (jointCtx secondaryAxisOrient "yup"), Create IK handle off. Blender bones point
# their Y at the child (= Maya Primary Axis X); a joint's Maya Y / Z = the bone's Z / X (rig_tools.local_axis).
SECONDARY_AXES = (("X", "X", "Maya X is the primary axis: not allowed"), ("Y", "Y", "The bone's Z axis"),
                  ("Z", "Z", "The bone's X axis"), ("NONE", "None", "Leave the bone roll as placed"))
# Maya world axis (Y-up) -> Blender world vector (Z-up: X -> X, Y -> Z, Z -> -Y)
WORLD_AXES = {"X": Vector((1.0, 0.0, 0.0)), "Y": Vector((0.0, 0.0, 1.0)), "Z": Vector((0.0, -1.0, 0.0))}


def orient_new(ob, names, secondary="Y", world="Y", sign="+"):
    """Roll the new joints so their Maya secondary axis faces the Maya world direction (Joint Tool orientation)."""
    if secondary == "NONE":
        return 0
    if secondary == "X":
        raise RuntimeError("Secondary axis must differ from the primary axis (X)")
    d = WORLD_AXES[world] * (1.0 if sign == "+" else -1.0)
    d = ob.matrix_world.inverted().to_3x3() @ d
    n = 0
    with _InEditMode(ob) as ebs:
        for name in names:
            eb = ebs.get(name)
            if eb is None or eb.length < 1e-9:
                continue
            y = (eb.tail - eb.head).normalized()
            # secondary Y = bone Z -> d; secondary Z = bone X -> d, so bone Z = X x Y = d x y
            z = d if secondary == "Y" else d.cross(y)
            if z.cross(y).length < 1e-6:
                continue                    # the bone runs along the world direction: Maya leaves it too
            eb.align_roll(z)
            n += 1
    return n


BRANCH_RADIUS_PX = 10      # a Joint Tool click this close to an existing joint branches from it


class ALLSET_OT_joint_tool(bpy.types.Operator):
    """Maya Joint Tool: click in a view to place joints (each one a child of the last), Enter to finish"""
    bl_idname = "allset.joint_tool"
    bl_label = "Joint Tool"
    bl_options = {'UNDO'}

    secondary_axis: EnumProperty(name="Secondary Axis", items=SECONDARY_AXES, default="Y")
    secondary_world: EnumProperty(name="Secondary Axis World Orientation",
                                  items=[(a, a, "") for a in ("X", "Y", "Z")], default="Y")
    secondary_sign: EnumProperty(name="Sign", items=(("+", "+", ""), ("-", "-", "")), default="+")
    create_ik: BoolProperty(name="Create IK handle", default=False)
    ik_solver: EnumProperty(name="Current solver",
                            items=(("RP", "Rotate-Plane Solver", ""), ("SC", "Single-Chain Solver", "")), default="RP")
    ik_solver_enable: BoolProperty(name="Solver enable", default=True)
    ik_weight: FloatProperty(name="Weight", default=1.0, min=0.01, max=1.0)
    points: StringProperty(options={'SKIP_SAVE', 'HIDDEN'},
                           description="JSON list of world points: place these joints without clicks (scripts)")

    def execute(self, context):
        """Without clicks: a new skeleton with a joint at each of ``points``."""
        try:
            pts = [Vector(p) for p in json.loads(self.points)] if self.points else []
        except (ValueError, TypeError):
            pts = []
        if not pts:
            self.report({'WARNING'}, "Joint Tool: click in a view to place joints")
            return {'CANCELLED'}
        ob = new_skeleton(context)
        names, parent = [], None
        for p in pts:
            name = add_joint(ob, p, parent, length=units.maya_unit(context.scene))
            if name != parent:
                names.append(name)
            parent = name
        self._names, self._ob = names, ob
        return self._finish(context)

    def invoke(self, context, event):
        if context.window is None:
            return {'CANCELLED'}
        # Maya 2022-2027 never branch from a joint selected before the tool starts (checked: joint1 selected, two
        # clicks -> an unparented chain, PR125_MAYA_CHECK.md 8b); clicking an existing joint with the tool does
        # (``_branch_from``).
        self._names, self._ob, self._parent = [], None, None
        self._swallow = False
        context.workspace.status_text_set(STATUS)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def _end(self, context):
        context.workspace.status_text_set(None)

    def _place(self, context, event):
        hit = view_under(context.window, event.mouse_x, event.mouse_y)
        if hit is None:
            return False
        area, region = hit
        rv3d = region.data
        coord = (event.mouse_x - region.x, event.mouse_y - region.y)
        if self._ob is None and self._branch_from(context, area, region, coord):
            return True
        point = click_point(region, rv3d, coord)
        if self._ob is None:
            with context.temp_override(window=context.window, area=area, region=region):
                self._ob = new_skeleton(context)
        if self._ob.mode != 'EDIT':
            with context.temp_override(window=context.window, area=area, region=region):
                bpy.ops.object.mode_set(mode='EDIT')
        up = rv3d.view_rotation @ Vector((0.0, 1.0, 0.0))
        name = add_joint(self._ob, point, self._parent, up=up, length=units.maya_unit(context.scene))
        if name != self._parent:
            self._names.append(name)
        self._parent = name
        area.tag_redraw()
        return True

    def _branch_from(self, context, area, region, coord):
        """The first click on an existing joint: the new joints go under it (Maya Joint Tool). True when hit."""
        from .skin import pick_joint
        arms = [o for o in context.view_layer.objects if o.type == 'ARMATURE' and o.visible_get()]
        scale = context.preferences.system.ui_scale or 1.0
        hit = pick_joint(region, region.data, arms, coord, BRANCH_RADIUS_PX * scale) if arms else None
        if hit is None or hit[1][1] != 'HEAD':
            return False
        arm, (name, _end) = hit
        with context.temp_override(window=context.window, area=area, region=region):
            if context.mode != 'OBJECT' and context.active_object is not None:
                bpy.ops.object.mode_set(mode='OBJECT')
            for o in context.selected_objects:
                o.select_set(False)
            arm.select_set(True)
            context.view_layer.objects.active = arm
            bpy.ops.object.mode_set(mode='EDIT')
        self._ob, self._parent = arm, name
        area.tag_redraw()
        return True

    def modal(self, context, event):
        if (event.type in {'Q', 'W', 'E', 'R'} and event.value == 'PRESS'
                and not (event.alt or event.ctrl or event.shift or event.oskey)):
            result = self._done(context)
            tool = {'Q': 'builtin.select_box', 'W': 'builtin.move',
                    'E': 'builtin.rotate', 'R': 'builtin.scale'}[event.type]
            hit = view_under(context.window, event.mouse_x, event.mouse_y)
            if hit is not None:
                with context.temp_override(area=hit[0], region=hit[1]):
                    bpy.ops.wm.tool_set_by_id(name=tool)
            return {'FINISHED'} if self._ob is not None else {'CANCELLED'}
        if event.type in {'RET', 'NUMPAD_ENTER'} and event.value == 'PRESS':
            return self._done(context)
        if event.type == 'ESC' and event.value == 'PRESS':
            if not self._names:
                self._end(context)
                return {'CANCELLED'}
            return self._done(context)
        if event.type == 'LEFTMOUSE':
            if event.value == 'PRESS' and not (event.alt or event.ctrl or event.shift or event.oskey):
                if self._place(context, event):
                    self._swallow = True
                    return {'RUNNING_MODAL'}
            elif event.value == 'RELEASE' and self._swallow:
                self._swallow = False
                return {'RUNNING_MODAL'}
        return {'PASS_THROUGH'}

    def _done(self, context):
        self._end(context)
        if self._ob is None or not self._names:
            return {'CANCELLED'}
        hit = next(((a, r) for a in context.window.screen.areas if a.type == 'VIEW_3D'
                    for r in a.regions if r.type == 'WINDOW'), None)
        override = dict(window=context.window, area=hit[0], region=hit[1]) if hit else dict(window=context.window)
        with context.temp_override(**override):
            return self._finish(context)

    def _finish(self, context):
        ob, names = self._ob, self._names
        try:
            orient_new(ob, names, self.secondary_axis, self.secondary_world, self.secondary_sign)
        except RuntimeError as ex:
            self.report({'WARNING'}, str(ex))
        finish(context, ob, names)
        msg = f"Created {len(names)} joint(s) in {ob.name}"
        if self.create_ik and len(names) >= 2:
            from .skin import create_ik
            handle = create_ik(context, ob, (names[0], 'HEAD'), (names[-1], 'HEAD'), self.ik_solver,
                               self.ik_solver_enable, self.ik_weight)
            if handle is not None:
                msg += f" and {handle.name}"
        results.result(self, msg)
        return {'FINISHED'}


# --- edit-mode helpers ------------------------------------------------------------------------

def _armature(context):
    ob = context.active_object
    return ob if ob is not None and ob.type == 'ARMATURE' and ob.mode in {'POSE', 'EDIT'} else None


def selected_joint_names(ob):
    if ob.mode == 'EDIT':
        return [eb.name for eb in ob.data.edit_bones if eb.select]
    cb = _cb()
    return [pb.name for pb in ob.pose.bones if cb.bone_selected(pb)]


def active_joint_name(ob):
    if ob.mode == 'EDIT':
        act = ob.data.edit_bones.active
    else:
        act = ob.data.bones.active
    return act.name if act is not None else None


class _InEditMode:
    """Run a block in armature edit mode and come back to the mode it started in."""

    def __init__(self, ob):
        self.ob, self.mode = ob, ob.mode

    def __enter__(self):
        if self.mode != 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')
        return self.ob.data.edit_bones

    def __exit__(self, *exc):
        if self.mode != 'EDIT':
            bpy.ops.object.mode_set(mode=self.mode)


def with_descendants(ebs, names):
    out = []
    for name in names:
        eb = ebs.get(name)
        if eb is None:
            continue
        for b in [eb, *eb.children_recursive]:
            if b.name not in out:
                out.append(b.name)
    return out


# --- Orient Joint ---------------------------------------------------------------------------

# Maya secondary world orientation (Y-up) -> Blender calculate_roll type (Z-up: Maya X->X, Y->Z, Z->-Y)
SAO_ROLL = {"X+": 'GLOBAL_POS_X', "X-": 'GLOBAL_NEG_X', "Y+": 'GLOBAL_POS_Z', "Y-": 'GLOBAL_NEG_Z',
            "Z+": 'GLOBAL_NEG_Y', "Z-": 'GLOBAL_POS_Y'}
_AXES = [(a, a, "") for a in ("X", "Y", "Z")]


def orient(ob, names, sao, children=True):
    """Roll the joints so their secondary axis faces the world direction (Maya Orient Joint)."""
    if sao not in SAO_ROLL:
        return 0
    with _InEditMode(ob) as ebs:
        targets = with_descendants(ebs, names) if children else [n for n in names if n in ebs]
        keep = {eb.name: eb.select for eb in ebs}
        for eb in ebs:
            eb.select = eb.select_head = eb.select_tail = eb.name in targets
        if targets:
            bpy.ops.armature.calculate_roll(type=SAO_ROLL[sao])
        for eb in ebs:
            eb.select = keep.get(eb.name, False)
    return len(targets)


class ALLSET_OT_orient_joint(bpy.types.Operator):
    """Maya Orient Joint: aim the joints' secondary axis at a world direction (the bone always points at its child)"""
    bl_idname = "allset.orient_joint"
    bl_label = "Orient Joint Options"
    bl_options = {'REGISTER', 'UNDO'}

    primary: EnumProperty(name="Primary Axis", items=_AXES, default="X")
    secondary: EnumProperty(name="Secondary Axis", items=_AXES, default="Y")
    world: EnumProperty(name="Secondary World Orientation",
                        items=[(k, k, "") for k in SAO_ROLL] + [("NONE", "None", "Leave the roll")],
                        default="Y+")
    children: BoolProperty(name="Orient Children of Joint", default=True)

    @classmethod
    def poll(cls, context):
        return _armature(context) is not None

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=360, confirm_text="Orient")

    def draw(self, context):
        lay = self.layout
        note = lay.column(align=True)
        note.active = False
        for line in ("Blender joints point their Y axis at the child joint", "(Maya Primary Axis X):",
                     "only the secondary axis can be set."):
            note.label(text=line)
        lay.prop(self, "primary")
        lay.prop(self, "secondary")
        lay.prop(self, "world")
        lay.prop(self, "children")

    def execute(self, context):
        ob = _armature(context)
        names = selected_joint_names(ob)
        if not names:
            self.report({'WARNING'}, "Select joints to orient")
            return {'CANCELLED'}
        n = orient(ob, names, self.world, self.children)
        results.result(self, f"Oriented {n} joint(s). {AXIS_NOTE}")
        return {'FINISHED'}


# --- Mirror Joints ----------------------------------------------------------------------------

# Maya mirror plane (Y-up) -> Blender reflection (Z-up): YZ = x, XY = Maya z = Blender -y, XZ = Maya y = z
PLANES = {"XY": (1.0, -1.0, 1.0), "YZ": (-1.0, 1.0, 1.0), "XZ": (1.0, 1.0, -1.0)}


def mirrored_name(name, search, replace, taken):
    new = name.replace(search, replace) if search and search in name else name
    if new == name or new in taken:
        base = naming.base_name(new)
        new = f"{base}{naming.next_number(base, taken)}"
    return new


def mirror(ob, names, plane="YZ", behavior=True, search="", replace=""):
    """Mirror the joints and their hierarchies across a plane through the world origin; returns the new names."""
    r = Matrix.Diagonal(PLANES[plane])
    mw = ob.matrix_world
    refl = mw.inverted().to_3x3() @ r @ mw.to_3x3()        # the world reflection in armature space
    origin = mw.inverted() @ (r @ (mw @ Vector((0.0, 0.0, 0.0))))
    new_names = []
    with _InEditMode(ob) as ebs:
        chain = with_descendants(ebs, names)
        taken = taken_joint_names() | {eb.name for eb in ebs}
        made = {}
        for name in chain:                                     # parents come before children
            src = ebs[name]
            rot = refl @ src.matrix.to_3x3()
            rot.col[0 if behavior else 2] *= -1.0              # right-handed again (Behavior = symmetrize)
            dst = ebs.new(mirrored_name(name, search, replace, taken))
            taken.add(dst.name)
            dst.head = refl @ src.head + origin
            dst.tail = refl @ src.tail + origin
            m = rot.to_4x4()
            m.translation = dst.head
            dst.matrix = m
            parent = src.parent
            if parent is not None and parent.name in made:
                dst.parent = ebs[made[parent.name]]
                dst.use_connect = src.use_connect
            else:
                dst.parent = parent
            made[name] = dst.name
            new_names.append(dst.name)
    return new_names


class ALLSET_OT_mirror_joints(bpy.types.Operator):
    """Maya Mirror Joints: copy the selected joints and their children across a plane through the origin"""
    bl_idname = "allset.mirror_joints"
    bl_label = "Mirror Joints Options"
    bl_options = {'REGISTER', 'UNDO'}

    plane: EnumProperty(name="Mirror Across", items=[(k, k, "") for k in ("XY", "YZ", "XZ")], default="YZ")
    function: EnumProperty(name="Mirror Function", items=(("BEHAVIOR", "Behavior", "Mirrored joints rotate "
                                                           "the opposite way (Blender symmetrize)"),
                                                          ("ORIENTATION", "Orientation", "Mirrored joints keep the "
                                                           "same axes")), default="BEHAVIOR")
    search: StringProperty(name="Search For")
    replace: StringProperty(name="Replace With")

    @classmethod
    def poll(cls, context):
        return _armature(context) is not None

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=360, confirm_text="Mirror")

    def draw(self, context):
        lay = self.layout
        lay.prop(self, "plane", expand=True)
        lay.prop(self, "function", expand=True)
        lay.label(text="Replacement names for duplicated joints")
        lay.prop(self, "search")
        lay.prop(self, "replace")

    def execute(self, context):
        ob = _armature(context)
        names = selected_joint_names(ob)
        if not names:
            self.report({'WARNING'}, "Select the joints to mirror")
            return {'CANCELLED'}
        new = mirror(ob, names, self.plane, self.function == "BEHAVIOR", self.search, self.replace)
        if ob.mode == 'POSE':
            for name in new:
                pb = ob.pose.bones.get(name)
                if pb is not None:
                    pb.rotation_mode = 'XYZ'
        results.result(self, f"Mirrored {len(new)} joint(s)")
        return {'FINISHED'}


# --- joint pick-walk and parenting --------------------------------------------------------------

def walk_bone(bone, direction):
    """Bone reached from ``bone`` (data Bone): Up parent, Down first child, Left/Right sibling (wraps)."""
    if direction == "UP":
        return bone.parent or bone
    if direction == "DOWN":
        kids = sorted(bone.children, key=lambda b: b.name)
        return kids[0] if kids else bone
    sibs = bone.parent.children if bone.parent else [b for b in bone.id_data.bones if b.parent is None]
    sibs = sorted(sibs, key=lambda b: b.name)
    if len(sibs) < 2:
        return bone
    i = [b.name for b in sibs].index(bone.name)
    return sibs[(i + (1 if direction == "RIGHT" else -1)) % len(sibs)]


@undo_steps.no_redo_panel      # step 147: no Adjust Last Operation (Maya has none)
class ALLSET_OT_pick_walk_joint(bpy.types.Operator):
    """Walk the joint selection through the skeleton (Maya arrow keys)"""
    bl_idname = "allset.pick_walk_joint"
    bl_label = "Pick Walk Joint"
    bl_options = {'REGISTER', 'UNDO'}

    direction: EnumProperty(items=(("UP", "Up", ""), ("DOWN", "Down", ""), ("LEFT", "Left", ""),
                                   ("RIGHT", "Right", "")), name="Direction")

    @classmethod
    def poll(cls, context):
        return context.mode == 'POSE' and _cb().lead(context) is not None

    def execute(self, context):
        cb = _cb()
        lead = cb.lead(context)
        picked = []
        for pb in cb.targets(context):
            to = walk_bone(pb.bone, self.direction)
            key = (pb.id_data.name, to.name)
            if key not in picked:
                picked.append(key)
        for arm in cb.pose_objects(context):
            for pb in arm.pose.bones:
                cb.set_bone_selected(pb, False)
        for arm_name, bone_name in picked:
            cb.set_bone_selected(bpy.data.objects[arm_name].pose.bones[bone_name], True)
        if lead is not None:
            lead.id_data.data.bones.active = walk_bone(lead.bone, self.direction)
        return {'FINISHED'}


def parent_joints(ob, names, parent_name):
    """Parent the joints to ``parent_name`` keeping where they are (Maya P); None = unparent."""
    n = 0
    with _InEditMode(ob) as ebs:
        parent = ebs.get(parent_name) if parent_name else None
        for name in names:
            eb = ebs.get(name)
            if eb is None or eb is parent:
                continue
            if parent is not None and (parent == eb or eb in parent.parent_recursive):
                continue                                       # would make a loop
            eb.use_connect = False
            eb.parent = parent
            n += 1
    return n


class ALLSET_OT_parent_joint(bpy.types.Operator):
    """Parent the selected joints to the last selected one, keeping their place (Maya P)"""
    bl_idname = "allset.parent_joint"
    bl_label = "Parent Joints"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _armature(context) is not None

    def execute(self, context):
        ob = _armature(context)
        active = active_joint_name(ob)
        names = [n for n in selected_joint_names(ob) if n != active]
        if active is None or not names:
            self.report({'WARNING'}, "Select the child joints, then the parent joint last")
            return {'CANCELLED'}
        results.result(self, f"Parented {parent_joints(ob, names, active)} joint(s) to {active}")
        return {'FINISHED'}


class ALLSET_OT_unparent_joint(bpy.types.Operator):
    """Unparent the selected joints, keeping their place (Maya Shift+P)"""
    bl_idname = "allset.unparent_joint"
    bl_label = "Unparent Joints"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _armature(context) is not None

    def execute(self, context):
        ob = _armature(context)
        n = parent_joints(ob, selected_joint_names(ob), None)
        results.result(self, f"Unparented {n} joint(s)")
        return {'FINISHED'}


classes = (ALLSET_OT_joint_tool, ALLSET_OT_orient_joint, ALLSET_OT_mirror_joints, ALLSET_OT_pick_walk_joint,
           ALLSET_OT_parent_joint, ALLSET_OT_unparent_joint)
