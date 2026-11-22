"""Copy Skin Weights onto a skeleton with other joint names: the copied weights replace the destination's own
weights (like Maya); with no joint matched (Name association, other names) the destination keeps its weights."""

from importlib import import_module

import bpy
from mathutils import Vector

import kit



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


def _copy_scene(dst_names):
    _reset()
    src_j = [("s0", (0, 0, 0), None), ("s1", (0, 0, 2), "s0"), ("s2", (0, 0, 4), "s1")]
    # the destination chain points down: its first joint sits at the top
    dst_j = [(dst_names[0], (0, 0, 4.2), None), (dst_names[1], (0, 0, 2.2), dst_names[0]),
             (dst_names[2], (0, 0, 0.2), dst_names[1])]
    sarm, darm = _skeleton(src_j, "skelA"), _skeleton(dst_j, "skelB")
    # a strip: vertices 2 i and 2 i + 1 sit at height 2 i
    pts = [(x, 0, z) for z in (0, 2, 4) for x in (0.0, 0.5)]
    faces = [(0, 1, 3, 2), (2, 3, 5, 4)]
    src, dst = _mesh(pts, "src", faces), _mesh(pts, "dst", faces)
    for mesh, arm, rows in ((src, sarm, ({"s0": 0.9, "s1": 0.1}, {"s1": 1.0}, {"s1": 0.2, "s2": 0.8})),
                            (dst, darm, ({dst_names[1]: 0.5, dst_names[2]: 0.5}, {dst_names[1]: 1.0},
                                         {dst_names[0]: 0.5, dst_names[1]: 0.5}))):
        md = mesh.modifiers.new("skinCluster1", 'ARMATURE')
        md.object = arm
        for b in arm.data.bones:
            mesh.vertex_groups.new(name=b.name)
        for i, r in enumerate(rows):
            for n, w in r.items():
                mesh.vertex_groups[n].add([2 * i, 2 * i + 1], w, 'REPLACE')
    _select(src, dst, active=dst)
    return dst


def test_copy_skin_weights_replaces_weights_on_other_joint_names():
    dst = _copy_scene(("d0", "d1", "d2"))
    assert bpy.ops.allset.copy_skin_weights('EXEC_DEFAULT', influence1='CLOSEST_JOINT') == {'FINISHED'}
    # s0 -> d2 (bottom), s1 -> d1, s2 -> d0 (top); the destination's old weights are gone
    expect = ({"d2": 0.9, "d1": 0.1}, {"d1": 1.0}, {"d1": 0.2, "d0": 0.8})
    for i, e in enumerate(expect):
        got = _w(dst, 2 * i)
        assert set(got) == set(e) and all(abs(got[k] - e[k]) < 1e-5 for k in e), (i, got, e)


def test_copy_skin_weights_no_match_keeps_destination():
    dst = _copy_scene(("d0", "d1", "d2"))
    before = [_w(dst, 2 * i) for i in range(3)]
    assert bpy.ops.allset.copy_skin_weights('EXEC_DEFAULT', influence1='NAME') == {'FINISHED'}
    for i in range(3):
        got = _w(dst, 2 * i)
        assert set(got) == set(before[i]) and all(abs(got[k] - before[i][k]) < 1e-5 for k in got), (i, got)


def test_copy_skin_weights_same_names_still_moves_by_position():
    dst = _copy_scene(("s0", "s1", "s2"))
    assert bpy.ops.allset.copy_skin_weights('EXEC_DEFAULT', influence1='CLOSEST_JOINT') == {'FINISHED'}
    expect = ({"s2": 0.9, "s1": 0.1}, {"s1": 1.0}, {"s1": 0.2, "s0": 0.8})
    for i, e in enumerate(expect):
        got = _w(dst, 2 * i)
        assert set(got) == set(e) and all(abs(got[k] - e[k]) < 1e-5 for k in e), (i, got, e)
