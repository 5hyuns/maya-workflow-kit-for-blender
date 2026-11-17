# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya Skeleton > Enable IK/FK Control and Enable IK Handle Snap on kit IK handles.

In Maya the IK solver writes its result into the chain joints' rotate values (joints without keys): the Channel Box
shows the solved rotation, and with Ik Blend going from 1 to 0 the joints stay in the IK pose. Blender's IK constraint
leaves the bone channels alone (they stay the FK values), so a handler here writes the solved pose into the channels
of every kit IK chain at Ik Blend 1 whose joints have no rotation keys — the same values Maya keeps.

Rotating a joint of an IK chain, Maya 2026:

- Enable IK/FK Control off (the default) and the handle keyed: the joint does not turn.
- Enable IK/FK Control off and Enable IK Handle Snap on (the default), handle not keyed: the joint turns and the handle
  follows the end joint; at Ik Blend 0 the handle stays on the end joint.
- otherwise the joint turns and the handle stays where it is (Blender's IK takes the chain back to the handle at once;
  Maya shows the turned joint until the handle moves).

Enable IK Handle Snap is greyed out while Enable IK/FK Control is on (it has no effect then). Both are global checks
(kit session state, like Enable IK Solver).
"""

import bpy
from bpy.app.handlers import persistent

from .. import update_summary
from . import ik_fk

_STATE = {"control": False, "snap": True}
_seen = {}                 # constraint pointer -> {bone name: channel values} last seen or written
_found = [None, []]        # (objects_version, object count) of the last look, [(armature, bone, IK constraint)]
_busy = []
ROT_EPS = 1e-4             # channel change that counts (radians / quaternion units)
POS_EPS = 1e-6

_XFORM_PATHS = ("location", "rotation_euler", "rotation_quaternion", "rotation_axis_angle")


def control_on():
    return _STATE["control"]


def snap_on():
    """Enable IK Handle Snap in effect (Maya ignores it while IK/FK control is on)."""
    return _STATE["snap"] and not _STATE["control"]


# --- chains ---------------------------------------------------------------------------------------------------------

def kit_chains():
    """[(armature, constrained pose bone, IK constraint)] whose target is a kit IK handle (it has Ik Blend)."""
    out = []
    for ob in bpy.data.objects:
        if ob.type != 'ARMATURE' or ob.pose is None:
            continue
        for pb in ob.pose.bones:
            for con in pb.constraints:
                t = con.target if con.type == 'IK' else None
                if t is not None and t.type != 'ARMATURE' and ik_fk.IK_BLEND in t.keys():
                    out.append((ob, pb, con))
    return out


def _chains():
    from ..ui.outliner import objects_version
    key = (objects_version(), len(bpy.data.objects))
    if _found[0] != key:
        _found[0], _found[1] = key, kit_chains()
    return _found[1]


def channels(pb):
    return tuple(getattr(pb, ik_fk.rotation_path(pb)))


def basis_channels(pb, basis):
    """The rotation channel values that give ``basis`` (what ``ik_fk.write_rotation`` would write)."""
    q = basis.to_quaternion()
    if pb.rotation_mode == 'QUATERNION':
        if q.dot(pb.rotation_quaternion) < 0.0:
            q.negate()
        return tuple(q)
    if pb.rotation_mode == 'AXIS_ANGLE':
        axis, angle = q.to_axis_angle()
        return (angle, *axis)
    return tuple(q.to_euler(pb.rotation_mode, pb.rotation_euler))


def _differ(a, b):
    return any(abs(x - y) > ROT_EPS for x, y in zip(a, b))


def _animated_paths(ob):
    from .. import compat
    paths = {fc.data_path for fc in compat.id_fcurves(ob)}
    ad = ob.animation_data
    if ad is not None:
        paths.update(fc.data_path for fc in ad.drivers)
    return paths


def handle_keyed(handle):
    """The handle has transform keys (Maya: the joints of its chain don't turn while IK/FK control is off)."""
    from .. import compat
    return any(fc.data_path in _XFORM_PATHS for fc in compat.id_fcurves(handle))


def _move_handle(handle, where):
    if (handle.matrix_world.translation - where).length <= POS_EPS:
        return False
    update_summary.wrote()
    mw = handle.matrix_world.copy()
    mw.translation = where
    handle.matrix_world = mw
    return True


def _set_channels(pb, values):
    update_summary.wrote()
    setattr(pb, ik_fk.rotation_path(pb), values)


def update_chain(arm, pb, con, animated):
    """Apply Maya's IK / FK rules to one kit chain. Returns True when something was written."""
    handle = con.target
    key = con.as_pointer()
    bones = ik_fk.chain(pb, con)
    if con.mute or any(b.path_from_id(ik_fk.rotation_path(b)) in animated for b in bones):
        _seen.pop(key, None)            # keyed joints: their curves give the FK values (Maya keeps them too)
        return False
    cur = {b.name: channels(b) for b in bones}
    seen = _seen.get(key)
    if seen is not None and seen["ch"].keys() != cur.keys():
        seen = None
    prev = seen["ch"] if seen is not None else None
    blend = ik_fk.blend_of(con)
    full = blend >= 1.0 - 1e-6
    wrote = False
    changed = prev is not None and any(_differ(cur[n], prev[n]) for n in cur)
    if (seen is not None and not full and seen["blend"] >= 1.0 - 1e-6 and not changed and seen["ik"] is not None
            and any(_differ(cur[n], seen["ik"][n]) for n in cur)):
        # Ik Blend left 1: the joints keep the last IK solution (Maya's rotate values)
        for b in bones:
            _set_channels(b, seen["ik"][b.name])
        cur = dict(seen["ik"])
        wrote = True
    snap = snap_on() and not handle_keyed(handle)
    if blend <= 1e-6:                   # FK: the joints turn freely; with snap the handle sits on the end joint
        _seen[key] = {"ch": cur, "ik": None, "blend": blend}
        return (snap and _move_handle(handle, ik_fk.fk_end(arm, pb, con))) or wrote
    bases = ik_fk.visual_bases(arm, bones)
    shown = {b.name: basis_channels(b, bases[b.name]) for b in bones}
    ik = shown if full else None
    if changed and any(_differ(cur[n], shown[n]) for n in cur):
        # a joint of the chain was turned
        if not control_on() and handle_keyed(handle):
            for b in bones:             # Maya: the joint doesn't turn
                if _differ(cur[b.name], prev[b.name]):
                    _set_channels(b, prev[b.name])
            return True
        _seen[key] = {"ch": cur, "ik": None, "blend": blend}
        return (snap and _move_handle(handle, ik_fk.fk_end(arm, pb, con))) or wrote
    if prev is not None and full and any(_differ(cur[n], shown[n]) for n in cur):
        for b in bones:                 # Maya: the solved rotation is the joints' rotate value
            if _differ(cur[b.name], shown[b.name]):
                _set_channels(b, shown[b.name])
        _seen[key] = {"ch": shown, "ik": ik, "blend": blend}
        return True
    _seen[key] = {"ch": cur, "ik": ik, "blend": blend}
    return wrote


def _playing():
    wm = bpy.context.window_manager
    return wm is not None and any(w.screen is not None and w.screen.is_animation_playing for w in wm.windows)


def update():
    if _busy:
        return
    from . import anim_snapshot
    if anim_snapshot._busy or _playing():
        return
    _busy.append(1)
    try:
        wrote = False
        animated = {}
        for arm, pb, con in _chains():
            if arm.mode == 'EDIT':
                continue
            paths = animated.get(arm.name)
            if paths is None:
                paths = animated[arm.name] = _animated_paths(arm)
            wrote |= update_chain(arm, pb, con, paths)
        if wrote:
            for arm in {a for a, _p, _c in _found[1]}:
                arm.update_tag()
    except (ReferenceError, AttributeError, RuntimeError):
        _found[0] = None
        _seen.clear()
    finally:
        _busy.clear()


def forget():
    """Undo, redo and load: start again from the channels as they are."""
    _seen.clear()
    _found[0] = None


@persistent
def _on_update(_scene=None, _depsgraph=None):
    update()


@persistent
def _on_frame(_scene=None, _depsgraph=None):
    update()


@persistent
def _on_reset(*_args):
    forget()


# --- menu check items -----------------------------------------------------------------------------------------------

def _get_control(_self):
    return _STATE["control"]


def _set_control(_self, value):
    _STATE["control"] = bool(value)
    forget()


def _get_snap(_self):
    return _STATE["snap"]


def _set_snap(_self, value):
    if _STATE["control"]:
        return                      # greyed out in Maya while IK/FK control is on
    _STATE["snap"] = bool(value)
    forget()


_HANDLERS = (("depsgraph_update_post", _on_update), ("frame_change_post", _on_frame),
             ("undo_post", _on_reset), ("redo_post", _on_reset), ("load_post", _on_reset))


def register():
    bpy.types.WindowManager.allset_ik_fk_control = bpy.props.BoolProperty(
        name="Enable IK/FK Control", get=_get_control, set=_set_control,
        description="Let the joints of an IK chain turn even when the IK handle has keys; the handle stays where it "
                    "is (Maya Skeleton > Enable IK/FK Control)")
    bpy.types.WindowManager.allset_ik_handle_snap = bpy.props.BoolProperty(
        name="Enable IK Handle Snap", get=_get_snap, set=_set_snap,
        description="The IK handle follows the end joint when a joint of its chain is turned, and stays on it at "
                    "Ik Blend 0 (Maya Skeleton > Enable IK Handle Snap)")
    for name, fn in _HANDLERS:
        hs = getattr(bpy.app.handlers, name)
        if fn not in hs:
            hs.append(fn)


def unregister():
    for name, fn in _HANDLERS:
        hs = getattr(bpy.app.handlers, name)
        if fn in hs:
            hs.remove(fn)
    del bpy.types.WindowManager.allset_ik_handle_snap
    del bpy.types.WindowManager.allset_ik_fk_control
    forget()
