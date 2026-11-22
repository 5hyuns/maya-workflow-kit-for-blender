"""Bind Skin to Selected joints on a branched skeleton: a bound joint's segments run only to its bound children, so
a joint whose other children are not bound weighs by the distance to its bound segments (an unbound branch adds no
reach), like Maya."""

from importlib import import_module

import bpy
from mathutils import Vector

import kit

cb = import_module(kit.MODULE + ".ui.cb_nodes")


def _reset():
    if bpy.context.object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)


def _skeleton(joints, name):
    arm = bpy.data.armatures.new(name)
    ob = bpy.data.objects.new(name, arm)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT')
    for n, p, parent in joints:
        eb = arm.edit_bones.new(n)
        eb.head = Vector(p)
        kids = [q for c, q, par in joints if par == n]
        eb.tail = Vector(kids[0]) if kids else Vector(p) + Vector((0.0, 0.0, 0.5))
        if parent:
            eb.parent = arm.edit_bones[parent]
    bpy.ops.object.mode_set(mode='OBJECT')
    return ob


def _mesh(points, name, faces=()):
    me = bpy.data.meshes.new(name)
    me.from_pydata([Vector(p) for p in points], [], list(faces))
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def _select(*obs, active):
    for o in bpy.data.objects:
        o.select_set(False)
    for o in obs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = active


def _w(mesh, i):
    return {mesh.vertex_groups[g.group].name: g.weight for g in mesh.data.vertices[i].groups if g.weight > 1e-7}


BRANCHED = [("root", (0, 0, 0), None), ("spine", (0, 0, 2), "root"), ("armL", (2, 0, 3), "spine"),
            ("handL", (4, 0, 3), "armL"), ("armR", (-2, 0, 3), "spine"), ("handR", (-4, 0, 3), "armR")]


def test_bind_selected_joints_ignores_unbound_branch():
    _reset()
    arm = _skeleton(BRANCHED, "skeleton1")
    p = Vector((-5.0, 0.0, -1.0))           # left of the unbound right arm
    body = _mesh([p], "body")
    _select(arm, body, active=arm)
    bpy.ops.object.mode_set(mode='POSE')
    for pb in arm.pose.bones:
        cb.set_bone_selected(pb, pb.name in ("spine", "armL", "handL"))
    assert bpy.ops.allset.bind_skin('EXEC_DEFAULT', bind_to='SELECTED') == {'FINISHED'}
    bpy.ops.object.mode_set(mode='OBJECT')
    got = _w(body, 0)
    assert sorted(got) == ["armL", "handL", "spine"], got
    # closest distance, dropoff 4: each bound joint's nearest bound segment is its own head here
    pos = {n: Vector(q) for n, q, _ in BRANCHED}
    raw = {n: 1.0 / (p - pos[n]).length ** 4 for n in got}
    total = sum(raw.values())
    for n, w in got.items():
        assert abs(w - raw[n] / total) < 1e-4, (n, w, raw[n] / total)
