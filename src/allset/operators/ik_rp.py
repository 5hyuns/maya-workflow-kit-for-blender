# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya ikRPsolver on a kit IK handle (step 245, Issue #162).

Maya 2026 (–3,; checked , private notes –1.5):
- a new RP handle gets a **default pole vector**: with the chain at its preferred angles, the joint whose offset from
  the start joint has the largest |p × d| (d = start -> end; ties keep the first), pv = d × (p × d) normalised (= that
  joint's offset perpendicular to the chain), length 2 × jointDisplayScale, stored in the handle's parent space
  (world); a straight chain falls back to a perpendicular [U: the checked straight pv bends toward Maya +Z for a chain
  along X: d × Maya Y here];
- the solve plane: v = pv perpendicular to u = root -> goal, turned about u by +twist (right-handed); Pole Vector
  constraint = pv follows (target − start joint).

Blender (4.5 checked, ik.md): the IK constraint's pole target at root + R(u, twist)·pv with
pole_angle = −signed_angle(base bone X -> rest bend direction about the rest chain axis) reproduces Maya's elbow to
2.2e-4 for reachable goals (0.011 when the goal is out of reach: Blender's IK keeps a sliver of bend). A straight chain
needs a starting bend (Blender's IK starts from the pose): the in-between joints get their preferred angle, else 1°
toward the pole (step 245 checked: 0.01 rad is enough, less is not).

Kit pieces: the handle's custom properties ``poleVectorX/Y/Z`` (Maya units, Maya axes) and ``twist`` (degrees) are
its Channel Box channels; a hidden empty ``<handle>Pole`` (at the chain's start joint + the turned pv, world, like
the skeleton) is the IK pole target, parented to the start joint's parent so it moves with the skeleton; ``update``
(depsgraph / frame handlers) keeps it at start joint + R(u, twist)·pv and, after Constrain > Pole Vector, pv = target −
start joint.
"""

import math

import bpy
from bpy.app.handlers import persistent
from mathutils import Matrix, Quaternion, Vector

from . import units

PV = ("poleVectorX", "poleVectorY", "poleVectorZ")
TWIST = "twist"
HELPER = "allset_pole_helper"          # handle -> its pole helper empty
OWNER = "allset_pole_of"               # helper -> its handle
POLE_OBJECT = "allset_pole_object"     # handle -> the Pole Vector constraint's target
PREBEND = math.radians(1.0)
# Maya world axes in Blender world (joints.MAYA_WORLD): Maya X -> X, Y -> Z, Z -> -Y
_M2B = ((1.0, 0.0, 0.0), (0.0, 0.0, -1.0), (0.0, 1.0, 0.0))


def to_blender(m):
    return Vector((m[0], -m[2], m[1]))


def to_maya(b):
    return Vector((b[0], b[2], -b[1]))


def _signed(a, b, axis):
    ang = a.angle(b)
    return ang if axis.dot(a.cross(b)) >= 0.0 else -ang


def chain_points(arm, bones, preferred=True):
    """World positions of the chain joints (start, in-between, end) with the in-between joints at their preferred
    angles (Maya computes the default pole vector that way, principles.md) — FK from the start joint's pose."""
    from .rig_maya import PREFERRED_PROP
    root = bones[0]
    m = arm.matrix_world @ root.matrix
    pts = [m.translation.copy()]
    for prev, b in zip(bones, bones[1:]):
        local = prev.bone.matrix_local.inverted() @ b.bone.matrix_local
        # Maya sets every DOF to its preferred angle (factory 0 = the rest)
        rot = Matrix.Identity(4) if preferred else b.matrix_basis.to_3x3().to_4x4()
        if preferred and PREFERRED_PROP in b:
            from mathutils import Euler
            rot = Euler([math.radians(a) for a in b[PREFERRED_PROP]], 'XYZ').to_matrix().to_4x4()
        m = m @ local @ rot
        pts.append(m.translation.copy())
    end = bones[-1]
    pts.append((m @ Vector((0.0, end.bone.length, 0.0))).copy())
    return pts


def default_pole_vector(points, length):
    """Maya's default pole vector (world) for the chain ``points`` (start .. end): the in-between joint with the
    largest |p × d|, its offset perpendicular to d; a straight chain: d × Maya up (then d × Maya X)."""
    p0 = points[0]
    d = points[-1] - p0
    best, best_n2 = None, 0.0
    for p in points[1:-1]:
        n = (p - p0).cross(d)
        if best is None or n.length_squared > best_n2 + 1e-10:
            best, best_n2 = n, n.length_squared
    if best is None or best_n2 < 1e-12 * max(d.length_squared, 1e-12) ** 2:
        v = d.cross(Vector((0.0, 0.0, 1.0)))            # Maya up (+Y) in Blender
        if v.length < 1e-9 * max(d.length, 1e-9):
            v = d.cross(Vector((1.0, 0.0, 0.0)))
    else:
        v = d.cross(best)
    return v.normalized() * length


def pole_angle(arm, bones, bend):
    """Blender pole_angle reproducing Maya's plane: −signed angle (about the rest chain axis) from the base bone's X
    to ``bend`` (armature-space rest direction of the elbow side), both made perpendicular to the axis."""
    root, end = bones[0].bone, bones[-1].bone
    u = (end.tail_local - root.head_local).normalized()
    x = root.matrix_local.to_3x3().col[0]
    x = (x - u * x.dot(u)).normalized()
    e = (bend - u * bend.dot(u)).normalized()
    return -_signed(x, e, u)


def _rest_bend(bones, fallback):
    """The rest chain's bend direction (armature space): the farthest in-between joint's perpendicular offset, else
    ``fallback`` (a straight rest chain)."""
    root, end = bones[0].bone, bones[-1].bone
    p0 = root.head_local
    d = end.tail_local - p0
    best, best_n2 = None, 0.0
    for b in bones[1:]:
        n = (b.bone.head_local - p0).cross(d)
        if best is None or n.length_squared > best_n2 + 1e-10:
            best, best_n2 = n, n.length_squared
    if best is None or best_n2 < 1e-10 * max(d.length_squared, 1e-12) ** 2:
        return fallback, True
    return d.cross(best), False


def _prebend(arm, bones, bend):
    """Give a straight chain's in-between joints a starting bend toward ``bend`` (armature space): their preferred
    angle when they have one (Maya bends a straight chain that way, ik.md), else 1°. Only joints at rest."""
    from .rig_maya import PREFERRED_PROP
    from mathutils import Euler
    u = (bones[-1].bone.tail_local - bones[0].bone.head_local).normalized()
    axis = u.cross(bend - u * bend.dot(u))
    for b in bones[1:]:
        if b.matrix_basis.to_quaternion().angle > 1e-9:
            continue
        if PREFERRED_PROP in b and any(abs(a) > 1e-9 for a in b[PREFERRED_PROP]):
            q = Euler([math.radians(a) for a in b[PREFERRED_PROP]], 'XYZ').to_quaternion()
        else:
            local = b.bone.matrix_local.to_3x3().inverted() @ axis
            q = Quaternion(local.normalized(), -PREBEND)
        if b.rotation_mode == 'QUATERNION':
            b.rotation_quaternion = q
        elif b.rotation_mode == 'AXIS_ANGLE':
            ax, ang = q.to_axis_angle()
            b.rotation_axis_angle = (ang, *ax)
        else:
            b.rotation_euler = q.to_euler(b.rotation_mode)


def _maya_unit(context=None):
    scene = getattr(context or bpy.context, "scene", None)
    return units.maya_unit(scene) if scene is not None else 1.0


def setup(context, arm, ik_bone, con, handle, display_scale=1.0):
    """Maya RP handle: default pole vector + Twist channels on ``handle``, the hidden pole helper, pole_angle, and a
    starting bend for a straight chain. Returns the helper."""
    from .ik_fk import chain
    bones = chain(ik_bone, con)
    k = _maya_unit(context)
    context.view_layer.update()
    pts = chain_points(arm, bones)
    pv = default_pole_vector(pts, 2.0 * display_scale * k)
    for i, name in enumerate(PV):
        handle[name] = float(to_maya(pv)[i] / k)
        handle.id_properties_ui(name).update(default=0.0)
    handle[TWIST] = 0.0
    handle.id_properties_ui(TWIST).update(default=0.0, subtype='NONE')
    helper = bpy.data.objects.new(f"{handle.name}Pole", None)
    for col in handle.users_collection or (context.scene.collection,):
        col.objects.link(helper)
        break
    helper.empty_display_type = 'SPHERE'
    helper.empty_display_size = 0.2 * k
    helper.hide_viewport = True
    helper.hide_select = True
    helper.hide_render = True
    helper[OWNER] = handle.name
    # parented to the start joint's parent (bone, or the skeleton object): the helper follows the skeleton without a
    # dependency on the IK chain itself (a Copy Location of the start joint made a cycle — the IK reads the helper —
    # and the GUI evaluated the pole stale, step 245)
    helper.parent = arm
    if bones[0].parent is not None:
        helper.parent_type = 'BONE'
        helper.parent_bone = bones[0].parent.name
    helper.matrix_world = Matrix.Translation(arm.matrix_world @ bones[0].head + pv)
    handle[HELPER] = helper
    # Blender's pole angle for Maya's plane (the rest bend; a straight rest chain: the pole direction)
    inv = (arm.matrix_world @ bones[0].matrix @ bones[0].bone.matrix_local.inverted()).to_3x3().inverted()
    bend, straight = _rest_bend(bones, inv @ pv)
    con.pole_target = helper
    con.pole_angle = pole_angle(arm, bones, bend)
    if straight:
        _prebend(arm, bones, bend)
    update_handle(handle)
    return helper


def handle_root(handle):
    """(armature, start pose bone) of the RP handle's chain (None when the chain is gone)."""
    from .skin import ik_constraints_on
    from .ik_fk import chain
    for arm, pb, con in ik_constraints_on(handle):
        return arm, chain(pb, con)[0]
    return None


def pole_vector(handle):
    return to_blender([float(handle.get(n, 0.0)) for n in PV]) * _maya_unit()


def update_handle(handle, depsgraph=None):
    """Put the handle's pole helper at root + R(u, twist)·pv (and pv = Pole Vector target − start joint)."""
    helper = handle.get(HELPER)
    if helper is None or not isinstance(helper, bpy.types.Object):
        return False
    found = handle_root(handle)
    if found is None:
        return False
    arm, root = found
    k = _maya_unit()
    root_w = arm.matrix_world @ root.head
    target = handle.get(POLE_OBJECT)
    if isinstance(target, bpy.types.Object):
        pv_m = to_maya(target.matrix_world.translation - root_w) / k
        for i, name in enumerate(PV):
            if abs(float(handle.get(name, 0.0)) - pv_m[i]) > 1e-7:
                handle[name] = float(pv_m[i])
    pv = pole_vector(handle)
    goal = handle.matrix_world.translation
    u = goal - root_w
    tw = math.radians(float(handle.get(TWIST, 0.0)))
    off = Quaternion(u.normalized(), tw) @ pv if (abs(tw) > 1e-12 and u.length > 1e-9) else pv
    want = root_w + off
    if (helper.matrix_world.translation - want).length > 1e-7 * max(k, 1e-6):
        helper.matrix_world = Matrix.Translation(want)
        return True
    return False


def rp_handles():
    return [ob for ob in bpy.data.objects if HELPER in ob]


_busy = []


@persistent
def _on_update(*_args):
    if _busy:
        return
    _busy.append(1)
    try:
        for handle in rp_handles():
            update_handle(handle)
    except (ReferenceError, AttributeError, RuntimeError):
        pass
    finally:
        _busy.clear()


def set_pole_object(handle, target):
    """Constrain > Pole Vector on a kit RP handle: Maya pv = target − start joint, kept by ``update``."""
    handle[POLE_OBJECT] = target
    update_handle(handle)


def helpers_of(objs):
    """Pole helpers of the handles in ``objs`` (they go with their handle on Delete)."""
    out = []
    for ob in objs:
        try:
            h = ob.get(HELPER)
        except ReferenceError:
            continue
        if isinstance(h, bpy.types.Object) and h not in objs:
            out.append(h)
    return out


def register_handlers():
    for hs in (bpy.app.handlers.depsgraph_update_post, bpy.app.handlers.frame_change_post):
        if _on_update not in hs:
            hs.append(_on_update)


def unregister_handlers():
    for hs in (bpy.app.handlers.depsgraph_update_post, bpy.app.handlers.frame_change_post):
        if _on_update in hs:
            hs.remove(_on_update)
