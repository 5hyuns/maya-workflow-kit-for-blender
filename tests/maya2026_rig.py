"""Maya joints -> kit skeleton, for the 0.6.0 rig upgrade tests (step 242, Issue #159).

Axis map (research/maya/re/joint_rig_2026_joint_math.md 「Blender」 table; kit ``joints.MAYA_WORLD`` / ``JOINT_AXES``):
- Maya world point (x, y, z) -> Blender (x, -z, y) (Maya Y-up -> Blender Z-up), times the scene's Maya unit;
- a joint's axes: bone Y = Maya X, bone Z = Maya Y (so bone X = Maya Z).

Maya joint matrix (row vectors, joint_math.md:33-41): L = S · RA · R(xyz) · JO · IS · T, W = L · W_parent, IS = the
inverse of the parent joint's scale while segmentScaleCompensate is on (Maya default; record key "ssc" = 0 turns it
off). In mathutils' column form that is W_parent @ T @ IS @ JO @ R @ RA @ S, and a
Maya xyz rotation in row form is exactly ``Euler(radians, 'XYZ').to_matrix()`` in column form.

Joint records are the fixture's ``{"t", "r", "jo", "ra", "s", "w", "parent"}`` dicts (tests/maya2026_rig_data.py);
missing keys default to Maya's factory values.
"""
import math

import bpy
from mathutils import Euler, Matrix, Vector

# Maya world axes in Blender world (columns = Maya X, Y, Z): the same matrix as joints.MAYA_WORLD
MAYA_TO_BLENDER = Matrix(((1.0, 0.0, 0.0), (0.0, 0.0, -1.0), (0.0, 1.0, 0.0)))
BLENDER_TO_MAYA = MAYA_TO_BLENDER.transposed()
# bone axes (X, Y, Z) in joint axes = Maya (Z, X, Y): the same matrix as joints.JOINT_AXES (bone frame @ it = joint axes)
JOINT_AXES = Matrix(((0.0, 0.0, 1.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)))


def to_blender_xyz(p, unit=1.0):
    """Maya world point / vector -> Blender world (x, -z, y) times ``unit`` — plain Python floats (double precision;
    mathutils keeps single precision)."""
    x, y, z = (float(c) for c in p)
    return (x * unit, -z * unit, y * unit)


def to_maya_xyz(p, unit=1.0):
    """Blender world point / vector -> Maya world (x, z, -y) divided by ``unit`` (inverse of ``to_blender_xyz``)."""
    x, y, z = (float(c) for c in p)
    return (x / unit, z / unit, -y / unit)


def frame_to_blender_rows(axes):
    """Maya world rotation (rows of a 3x3, columns = joint axes) -> Blender world, plain floats: rows (r0, -r2, r1)."""
    r0, r1, r2 = ([float(c) for c in row] for row in axes)
    return [r0, [-c for c in r2], r1]


def frame_to_maya_rows(axes):
    r0, r1, r2 = ([float(c) for c in row] for row in axes)
    return [r0, r2, [-c for c in r1]]


def to_blender(p, unit=1.0):
    return Vector(to_blender_xyz(p, unit))


def to_maya(p, unit=1.0):
    return Vector(to_maya_xyz(p, unit))


def frame_to_blender(axes):
    """Maya world rotation (columns = joint X, Y, Z in Maya world) -> the same axes in Blender world."""
    return MAYA_TO_BLENDER @ Matrix(axes)


def frame_to_maya(axes):
    return BLENDER_TO_MAYA @ Matrix(axes)


def bone_frame(maya_axes):
    """Blender world rotation of a bone whose Y = Maya X and Z = Maya Y (columns = bone X, Y, Z)."""
    return frame_to_blender(maya_axes) @ JOINT_AXES.transposed()


def _rot(deg):
    return Euler([math.radians(a) for a in deg], 'XYZ').to_matrix().to_4x4()


def _scale(s):
    return Matrix.Diagonal(Vector(tuple(s) + (1.0,)))


def local_matrix(rec, parent=None):
    """Maya local matrix of a joint record, column form (T @ IS @ JO @ R @ RA @ S); ``parent`` = the parent joint's
    record (its scale is compensated while this joint's segmentScaleCompensate is on)."""
    t = Matrix.Translation(Vector(rec.get("t", (0.0, 0.0, 0.0))))
    s = _scale(rec.get("s", (1.0, 1.0, 1.0)))
    inv = Matrix.Identity(4)
    if parent is not None and rec.get("ssc", 1):
        inv = _scale([1.0 / c for c in parent.get("s", (1.0, 1.0, 1.0))])
    return t @ inv @ _rot(rec.get("jo", (0, 0, 0))) @ _rot(rec.get("r", (0, 0, 0))) @ _rot(rec.get("ra", (0, 0, 0))) @ s


def _order(joints):
    done, out = set(), []

    def visit(name):
        if name in done:
            return
        parent = joints[name].get("parent")
        if parent in joints:
            visit(parent)
        done.add(name)
        out.append(name)

    for name in joints:
        visit(name)
    return out


def world_matrices(joints):
    """{name: Maya world matrix (4x4, column form)} from the joints' local attributes; every parent must be listed."""
    missing = {r.get("parent") for r in joints.values()} - set(joints) - {None}
    if missing:
        raise ValueError(f"parents not in the skeleton: {sorted(missing)}")
    out = {}
    for name in _order(joints):
        parent = joints[name].get("parent")
        base = out[parent] if parent in out else Matrix.Identity(4)
        out[name] = base @ local_matrix(joints[name], joints.get(parent) if parent else None)
    return out


def children(joints, name):
    return [n for n, rec in joints.items() if rec.get("parent") == name]


def build_skeleton(joints, unit=1.0, name="skeleton1", context=None, oriented=True):
    """An armature object with one bone per Maya joint (same names), left in OBJECT mode.

    Bone head = the joint's world position (``world_matrices``; the record's measured ``"w"`` is only used when the
    record has no ``"t"``). With ``oriented`` the bone's frame is the joint's: Y = Maya X, roll so Z = Maya Y; the
    length is the distance to the first child (half the parent's for an end joint, 1 for a lone joint). Children whose
    head lands on the tail are connected. Returns the object."""
    context = context or bpy.context
    worlds = world_matrices({n: r for n, r in joints.items() if "t" in r})
    pos = {n: (worlds[n].to_translation() if n in worlds else Vector(r["w"])) for n, r in joints.items()}
    arm = bpy.data.armatures.new(name)
    ob = bpy.data.objects.new(name, arm)
    context.scene.collection.objects.link(ob)
    if context.view_layer.objects.active is not None and context.view_layer.objects.active.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT')
    ebs = arm.edit_bones
    lengths = {}
    for jn in _order(joints):
        kids = children(joints, jn)
        parent = joints[jn].get("parent")
        if kids and (pos[kids[0]] - pos[jn]).length > 1e-9:
            length = (pos[kids[0]] - pos[jn]).length
        elif parent and parent in lengths:
            length = lengths[parent] * 0.5
        else:
            length = 1.0
        length = max(length, 1e-3)
        lengths[jn] = length
        eb = ebs.new(jn)
        head = to_blender(pos[jn], unit)
        if oriented and jn in worlds:
            axes = worlds[jn].to_3x3().normalized()
            y = frame_to_blender(axes).col[0]
            z = frame_to_blender(axes).col[1]
        else:
            d = to_blender(pos[kids[0]] - pos[jn]) if kids else Vector()
            y = d.normalized() if d.length > 1e-9 else Vector((0.0, 1.0, 0.0))   # a zero-length child: any way
            z = None
        eb.head = head
        eb.tail = head + y * (length * unit)
        if z is not None:
            eb.align_roll(z)
        if parent and parent in ebs:
            eb.parent = ebs[parent]
            eb.use_connect = (ebs[parent].tail - eb.head).length < 1e-5 * max(1.0, unit)
    bpy.ops.object.mode_set(mode='OBJECT')
    return ob


MAYA_FRAME = "allset_maya_frame"   # joints.MAYA_FRAME: the joint's Maya frame relative to the bone (quaternion)


def joint_world(ob, name, unit=1.0):
    """(Maya world position, Maya world axes) read back from a bone's rest frame (inverse of ``build_skeleton``),
    turned by the bone's stored Maya frame (``allset_maya_frame``) when it has one. Works in edit mode too."""
    from mathutils import Quaternion
    if ob.mode == 'EDIT':
        bone = ob.data.edit_bones[name]
        m = ob.matrix_world @ bone.matrix
    else:
        bone = ob.data.bones[name]
        m = ob.matrix_world @ bone.matrix_local
    axes = m.to_3x3().normalized() @ JOINT_AXES
    q = bone.get(MAYA_FRAME)
    if q is not None and len(q) == 4:
        axes = axes @ Quaternion(q).to_matrix()
    return to_maya(m.to_translation(), unit), frame_to_maya(axes)
