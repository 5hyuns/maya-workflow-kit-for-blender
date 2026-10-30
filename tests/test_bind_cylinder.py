"""Bind Skin on a 20-row cylinder (#257): a 2- and a 3-joint chain made with the Joint Tool get the expected
closest-distance weights, and turning joint2 by 90 degrees bends the cylinder accordingly (a 2-joint chain's top
gets half the turn: its top row is shared 0.5 / 0.5 between the two joints)."""

import json
import math
from importlib import import_module

import bpy
from mathutils import Matrix, Vector

import kit

create = import_module(kit.MODULE + ".operators.create")

# Expected result for a cylinder r 1 h 2 with 20 rows bound to joints at y = -1 (0) 1, Bind Skin defaults.
# Rows: (rest position, Y-up, weights per joint, position with joint2 rotated 90 degrees about the up-facing Z).
EXPECTED = {
    2: [((0.9511, -1.0, -0.309), (0.9615, 0.0385), (0.9914, -0.8865, -0.309)),
        ((0.9511, 0.0, -0.309), (0.8, 0.2), (0.9608, 0.3902, -0.309)),
        ((0.9511, 0.5, -0.309), (0.6098, 0.3902), (0.775, 1.0663, -0.309)),
        ((0.9511, 1.0, -0.309), (0.5, 0.5), (0.4755, 1.4755, -0.309))],
    3: [((0.9511, -1.0, -0.309), (0.7752, 0.1938, 0.031), (0.9621, -0.5614, -0.309)),
        ((0.9511, 0.0, -0.309), (0.4444, 0.4444, 0.1111), (0.4227, 0.5284, -0.309)),
        ((0.9511, 0.5, -0.309), (0.2807, 0.4386, 0.2807), (-0.0927, 0.8244, -0.309)),
        ((0.9511, 1.0, -0.309), (0.1111, 0.4444, 0.4444), (-0.7832, 0.9565, -0.309))],
}


def _blender(p):
    """Y-up -> Blender Z-up."""
    x, y, z = p
    return Vector((x, -z, y))


def _clean():
    if bpy.context.object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)


def _bound(njoints):
    _clean()
    cyl = create.create(bpy.context, 'CYLINDER', overrides={"subdivisionsHeight": 20})
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    zs = (-1.0, 1.0) if njoints == 2 else (-1.0, 0.0, 1.0)
    assert bpy.ops.allset.joint_tool(points=json.dumps([(0, 0, z) for z in zs])) == {'FINISHED'}
    arm = bpy.context.active_object
    assert arm.type == 'ARMATURE', arm
    bpy.ops.object.mode_set(mode='OBJECT')
    for ob in bpy.context.selected_objects:
        ob.select_set(False)
    arm.select_set(True)
    cyl.select_set(True)
    bpy.context.view_layer.objects.active = arm
    assert bpy.ops.allset.bind_skin() == {'FINISHED'}
    names = [b.name for b in sorted(arm.data.bones, key=lambda b: b.head_local.z)]
    return cyl, arm, names


def _vertex(cyl, p):
    return min(cyl.data.vertices, key=lambda v: (cyl.matrix_world @ v.co - p).length)


def _weights(cyl, v, names):
    by_index = {g.index: g.name for g in cyl.vertex_groups}
    got = {by_index[e.group]: e.weight for e in v.groups}
    return [got.get(n, 0.0) for n in names]


def test_weights():
    for n, rows in EXPECTED.items():
        cyl, _arm, names = _bound(n)
        assert len(names) == n, names
        for rest, want, _bent in rows:
            v = _vertex(cyl, _blender(rest))
            assert (cyl.matrix_world @ v.co - _blender(rest)).length < 1e-3, (n, rest, v.co)
            got = _weights(cyl, v, names)
            assert all(abs(a - b) < 1e-3 for a, b in zip(got, want)), (n, rest, got, want)


def test_bend():
    for n, rows in EXPECTED.items():
        cyl, arm, names = _bound(n)
        ids = [_vertex(cyl, _blender(rest)).index for rest, _w, _b in rows]
        pb = arm.pose.bones[names[1]]
        head = arm.matrix_world @ pb.bone.head_local
        # Y-up world Z = Blender -Y
        turn = Matrix.Rotation(math.radians(90.0), 4, Vector((0.0, -1.0, 0.0)))
        world = Matrix.Translation(head) @ turn @ Matrix.Translation(-head) @ arm.matrix_world @ pb.bone.matrix_local
        pb.matrix = arm.matrix_world.inverted() @ world
        bpy.context.view_layer.update()
        ev = cyl.evaluated_get(bpy.context.evaluated_depsgraph_get())
        me = ev.to_mesh()
        try:
            for i, (_rest, _w, bent) in zip(ids, rows):
                got = ev.matrix_world @ me.vertices[i].co
                assert (got - _blender(bent)).length < 2e-3, (n, i, tuple(got), bent)
        finally:
            ev.to_mesh_clear()
