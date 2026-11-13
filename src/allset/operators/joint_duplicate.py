# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya Edit > Duplicate (Ctrl+D) on picked joints.

Maya: duplicating a picked joint copies it with every joint below it, in place, under the same parent (a root joint's
copy is a new top joint); the top copy takes the next joint number, the copies keep their joint attributes and
display layers but no animation, and the copies of the picked joints are picked after. A joint picked below another
picked joint is copied with its parent's subtree, not twice.

``allset.duplicate`` (Ctrl+D, Edit > Duplicate) runs this in Pose Mode and joint Edit Mode. Here a picked joint is a
bone picked in Pose Mode, or in Edit Mode with the Move tool (``joint_selection``: the bone
and its subtree are selected there, the head of a connected bone without its parent's tail, so Blender's own Duplicate
dropped the picked bone and copied its children only). Blender's Duplicate does the copying (bone settings,
bone collections, pose channels with their constraints, custom shapes and display layer) once the selection is the
subtrees of the topmost picked joints; the copies take their joints' current pose (Blender copies the rest only),
then get Maya joint names (Blender bone names are unique in a
skeleton, so the copies below the top one take the next numbers too) and the top copies sort last among their
siblings, like a new node.
"""

import bpy

from .. import compat

SOURCE = "allset_duplicate_of"      # temporary edit bone property: the source of a copy


def _picked(context):
    """{skeleton object: [picked joint names]} of the armatures in Pose / Edit Mode."""
    from . import joint_selection
    from ..ui.channel_box import bone_selected
    out = {}
    for ob in context.objects_in_mode_unique_data if context.mode in {'POSE', 'EDIT_ARMATURE'} else ():
        if ob.type != 'ARMATURE':
            continue
        if ob.mode == 'EDIT':
            names = [eb.name for eb in joint_selection._edit_picked(ob)]
        else:
            names = [pb.name for pb in ob.pose.bones if bone_selected(pb) and not compat.bone_hidden(pb)]
        if names:
            out[ob] = names
    return out


def _tops(bones, names):
    """The picked joints with no picked joint above them, in bone order."""
    picked = set(names)
    out = []
    for n in names:
        b = bones.get(n)
        if b is None:
            continue
        p = b.parent
        while p is not None and p.name not in picked:
            p = p.parent
        if p is None:
            out.append(n)
    return out


def _depth(bone):
    n, p = 0, bone.parent
    while p is not None:
        n, p = n + 1, p.parent
    return n


def _select_subtrees(ob, tops):
    """Edit Mode selection Blender's Duplicate copies exactly: the subtrees of ``tops``; a connected top also needs
    its parent's tail (that end point is the top's head), its parent itself stays unselected."""
    ebs = ob.data.edit_bones
    for eb in ebs:
        eb.select = eb.select_head = eb.select_tail = False
    for n in tops:
        top = ebs[n]
        for b in (top, *top.children_recursive):
            b.select = b.select_head = b.select_tail = True
        if top.use_connect and top.parent is not None:
            top.parent.select_tail = True


POSE_CHANNELS = ("rotation_mode", "location", "rotation_quaternion", "rotation_euler", "rotation_axis_angle", "scale")


def _copy_pose(sources):
    """The copies stand where their joints stand now: their channels take the sources' current values (the keys
    stay with the sources, like Maya)."""
    for ob, pairs in sources.items():
        pbs = ob.pose.bones
        for copy, src in pairs.items():
            a, b = pbs.get(src), pbs.get(copy)
            if a is None or b is None:
                continue
            for prop in POSE_CHANNELS:
                setattr(b, prop, getattr(a, prop))


def duplicate(context):
    """Maya Duplicate of the picked joints. Returns the names of the copies of the picked joints (empty: nothing
    picked)."""
    from . import joint_selection, joints
    picked = _picked(context)
    if not picked:
        return []
    start = context.mode
    active = context.view_layer.objects.active
    if start != 'EDIT_ARMATURE':
        bpy.ops.object.mode_set(mode='EDIT')         # every armature in Pose Mode goes with the active one
    made = {}
    for ob, names in picked.items():
        ebs = ob.data.edit_bones
        tops = _tops(ebs, names)
        _select_subtrees(ob, tops)
        for eb in ebs:
            eb[SOURCE] = eb.name
    before = {ob: {eb.name for eb in ob.data.edit_bones} for ob in picked}
    with context.temp_override(active_object=active, edit_object=active):
        bpy.ops.armature.duplicate()
    taken = set()
    sources = {}                                   # skeleton -> {copy: source}
    for ob, names in picked.items():
        ebs = ob.data.edit_bones
        new = [eb for eb in ebs if eb.name not in before[ob]]
        copy_of = {eb.get(SOURCE): eb for eb in new}
        tops = set(_tops(ebs, names))
        # Maya names in creation order: each top copy, then the copies below it, parents first
        order = sorted(new, key=lambda eb: (_depth(eb), ebs.find(eb.name)))
        for eb in order:
            name = joints.next_joint_name(extra=taken)
            taken.add(name)
            src = eb.get(SOURCE)
            eb.name = name
            sources.setdefault(ob, {})[name] = src
            if src in tops:
                joints.stamp_last(eb)              # a new node: last among its siblings
        for eb in ebs:
            if SOURCE in eb:
                del eb[SOURCE]
        made[ob] = [copy_of[n].name for n in names if n in copy_of]
    bpy.ops.object.mode_set(mode='POSE')
    _copy_pose(sources)
    if start == 'EDIT_ARMATURE':
        bpy.ops.object.mode_set(mode='EDIT')
        for ob, copies in made.items():
            ebs = ob.data.edit_bones
            for eb in ebs:
                eb.select = eb.select_head = eb.select_tail = False
            for n in copies:
                joint_selection._pick_shape(ebs[n], True, False)
            if copies:
                ebs.active = ebs[copies[-1]]
        joint_selection.sync_joint_pivot(context)
    else:
        from ..ui.channel_box import set_bone_selected
        for ob, copies in made.items():
            for pb in ob.pose.bones:
                set_bone_selected(pb, pb.name in copies)
            if copies:
                ob.data.bones.active = ob.data.bones[copies[-1]]
    from ..ui import layer_joints
    layer_joints.bump()
    return [n for copies in made.values() for n in copies]
