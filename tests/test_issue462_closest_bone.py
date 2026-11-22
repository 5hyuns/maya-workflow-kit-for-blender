"""Issue #462: Copy Skin Weights Influence Association "Closest bone" pairs bones (a joint to its child joint), not
joints: a source joint goes to the destination joint whose bone lies nearest the middle of the source joint's bone
(an end joint: the joint itself); a tie goes to the joint first in the hierarchy."""

from importlib import import_module

import bpy

import kit

scm = import_module(kit.MODULE + ".operators.skin_copy_mirror")


def _chain(name, heights, x=0.0):
    """Skeleton ``name``: one joint per (x, z) or height, each the child of the one before."""
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    arm = bpy.data.armatures.new(name)
    ob = bpy.data.objects.new(name, arm)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT')
    prev = None
    pts = [p if isinstance(p, tuple) else (x, p) for p in heights]
    for i, (px, pz) in enumerate(pts):
        eb = arm.edit_bones.new(f"{name}{i}")
        eb.head = (px, 0.0, pz)
        nxt = pts[i + 1] if i + 1 < len(pts) else None
        eb.tail = (nxt[0], 0.0, nxt[1]) if nxt and (nxt[0], nxt[1]) != (px, pz) else (px, 0.0, pz + 0.5)
        if prev is not None:
            eb.parent = prev
        prev = eb
    bpy.ops.object.mode_set(mode='OBJECT')
    return ob


def _pairs(src_pts, dst_pts):
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    s, d = _chain("s", src_pts), _chain("d", dst_pts)
    return {b.name: scm.associate(s, d, b.name, ("CLOSEST_BONE",)) for b in s.data.bones}


def test_chain_going_the_other_way():
    assert _pairs([0, 4, 8], [8, 4, 0]) == {"s0": "d1", "s1": "d0", "s2": "d0"}


def test_same_chain_beside():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    s, d = _chain("s", [0, 4, 8]), _chain("d", [0, 4, 8], x=1.0)
    got = {b.name: scm.associate(s, d, b.name, ("CLOSEST_BONE",)) for b in s.data.bones}
    assert got == {"s0": "d0", "s1": "d1", "s2": "d1"}, got


def test_bone_lengths_decide():
    assert _pairs([0, 4, 8], [0, 1, 8]) == {"s0": "d1", "s1": "d1", "s2": "d1"}
    assert _pairs([0, 4, 8], [0, 7, 8]) == {"s0": "d0", "s1": "d0", "s2": "d1"}


def test_tie_goes_to_the_first_joint():
    assert _pairs([0, 4, 8], [2, 6, 10]) == {"s0": "d0", "s1": "d0", "s2": "d1"}
    assert _pairs([0, 3, 6, 9], [0, 4.5, 9]) == {"s0": "d0", "s1": "d0", "s2": "d1", "s3": "d1"}
    assert _pairs([0, 4, 8], [9, 6, 3, 0]) == {"s0": "d2", "s1": "d0", "s2": "d0"}


def test_bent_destination():
    assert _pairs([0, 4, 8], [(3.0, 0.0), (0.0, 4.0), (3.0, 8.0)]) == {"s0": "d0", "s1": "d1", "s2": "d1"}


def test_closest_joint_unchanged():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    s, d = _chain("s", [0, 4, 8]), _chain("d", [8, 4, 0])
    got = {b.name: scm.associate(s, d, b.name, ("CLOSEST_JOINT",)) for b in s.data.bones}
    assert got == {"s0": "d2", "s1": "d1", "s2": "d0"}, got
