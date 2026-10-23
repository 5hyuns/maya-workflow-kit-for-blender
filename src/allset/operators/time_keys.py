# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya keys: S = Set Key on every keyable channel, Set Breakdown Key, and the Time Slider key edits
(Cut / Copy / Paste / Delete / Snap / Keys / Tangents / Set Range to).

research/maya/workflows/animation.md §1.1 (S keys every keyable attribute), §3 rows 5, 8, 11-13; Maya
``others/TimeSliderMenu.mel:300-770`` (the time slider edits act on ``timeControl -q -range``: the
Shift-dragged range, else the current frame), design docs/steps/step_56.md 「계획」 2, 4.

Nodes are the Channel Box's (``ui/channel_box.targets``): selected objects, or the selected pose bones
in pose mode (a bone's curves are the armature action's ``pose.bones["n"]...`` curves).
"""

import bpy
from bpy.props import BoolProperty, EnumProperty

# Maya tangent -> (interpolation, handle type or None); FLAT also levels the handles.
# (animation.md:14 table; reused by the Graph Editor tangent buttons, step 67)
TANGENTS = {
    "SPLINE": ("BEZIER", 'AUTO'),
    "LINEAR": ("LINEAR", None),
    "CLAMPED": ("BEZIER", 'AUTO_CLAMPED'),
    "STEPPED": ("CONSTANT", None),
    "FLAT": ("BEZIER", 'ALIGNED'),
    "PLATEAU": ("BEZIER", 'AUTO_CLAMPED'),
    "AUTO": ("BEZIER", 'AUTO_CLAMPED'),
    # step 70 (docs/steps/step_70.md 「계획」 table): Fixed keeps the handles where they are; Blender has no
    # Stepped Next (animation.md §4): Stepped. BREAK / UNIFY only change the handle type (free / aligned).
    "FIXED": ("BEZIER", 'ALIGNED'),
    "STEPPED_NEXT": ("CONSTANT", None),
    "BREAK": (None, 'FREE'),
    "UNIFY": (None, 'ALIGNED'),
}
# Maya names for the menus / buttons
TANGENT_LABELS = {"AUTO": "Auto", "SPLINE": "Spline", "CLAMPED": "Clamped", "LINEAR": "Linear", "FLAT": "Flat",
                  "STEPPED": "Stepped", "STEPPED_NEXT": "Stepped Next", "PLATEAU": "Plateau", "FIXED": "Fixed",
                  "BREAK": "Break Tangents", "UNIFY": "Unify Tangents"}


def apply_tangent(kp, kind):
    """One key's Maya tangent (in and out)."""
    interp, handle = TANGENTS[kind]
    if interp is not None:
        kp.interpolation = interp
    if handle is not None:
        kp.handle_left_type = kp.handle_right_type = handle
    if kind == "FLAT":
        kp.handle_left.y = kp.handle_right.y = kp.co.y
TANGENT_ITEMS = [(k, TANGENT_LABELS.get(k, k.title()), "") for k in TANGENTS]

_CLIPBOARD = {"nodes": [], "span": 0}


def _cb():
    from ..ui import channel_box
    return channel_box


# --- nodes and their curves ---------------------------------------------------------------

def nodes(context=None):
    return _cb().targets(context)


def prefix(node):
    """Animation path prefix of a node: ``pose.bones["n"]`` for a bone, "" for an object."""
    return node.path_from_id() if _cb().is_bone(node) else ""


def node_fcurves(node):
    """The node's F-curves (a bone: only its own ``pose.bones["n"]`` curves)."""
    fcs = _cb()._fcurves(node)
    if fcs is None:
        return []
    pre = prefix(node)
    if not pre:
        return list(fcs)
    return [fc for fc in fcs if fc.data_path.startswith(pre + ".") or fc.data_path.startswith(pre + "[")]


def time_range(context=None):
    """(start, end) the time slider edits act on: the Shift range, else the current frame."""
    context = context or bpy.context
    wm = context.window_manager
    if getattr(wm, "allset_time_range_on", False):
        a, b = wm.allset_time_range
        return min(a, b), max(a, b)
    f = context.scene.frame_current
    return f, f


def _in(kp, a, b):
    return a - 0.5 <= kp.co.x < b + 0.5


def keys_in(node, a, b):
    """[(fcurve, [keyframe points in a..b])] of a node."""
    out = []
    for fc in node_fcurves(node):
        pts = [kp for kp in fc.keyframe_points if _in(kp, a, b)]
        if pts:
            out.append((fc, pts))
    return out


# --- Set Key ----------------------------------------------------------------------------------

def keyable_channels(node):
    """Maya keyable attributes of a node: the Channel Box's shown channels that are keyable."""
    cb = _cb()
    return [k for k in cb._visible_channels(node) if cb.is_keyable(node, k)]


def set_key(context, breakdown=False):
    """S: key every keyable channel of every node (or the active keying set); count of channels."""
    scene = context.scene
    keytype = 'BREAKDOWN' if breakdown else 'KEYFRAME'
    if scene.keying_sets.active is not None and not breakdown and bpy.ops.anim.keyframe_insert.poll():
        bpy.ops.anim.keyframe_insert()
        return len(scene.keying_sets.active.paths)
    count = 0
    for node in nodes(context):
        for key in keyable_channels(node):
            count += bool(_cb().keyframe(node, key, keytype))
    return count


# --- Time Slider edits ------------------------------------------------------------------------

def delete_keys(context, a, b):
    n = 0
    for node in nodes(context):
        fcs = _cb()._fcurves(node)
        for fc, pts in keys_in(node, a, b):
            for kp in sorted(pts, key=lambda p: -p.co.x):
                fc.keyframe_points.remove(kp, fast=True)
                n += 1
            if len(fc.keyframe_points) == 0 and fcs is not None:
                fcs.remove(fc)
            else:
                fc.update()
    return n


def copy_keys(context, a, b):
    """Time Slider copy: the nodes' keys in a..b onto the animation clipboard (see ``copy_scope``)."""
    return copy_scope(context, KeyScope(time_range="Start/End", start=a, end=b))


def paste_keys(context, frame):
    """Time Slider paste at ``frame`` (Maya's factory Merge): one copied node goes to every node, several in order."""
    return paste_scope(context, frame=frame)


def _find_curve(node, path, index):
    fcs = _cb()._fcurves(node)
    return fcs.find(path, index=index) if fcs is not None else None


def _move(kp, dx):
    kp.co.x += dx
    kp.handle_left.x += dx
    kp.handle_right.x += dx


def snap_keys(context, a, b):
    n = 0
    for node in nodes(context):
        for fc, pts in keys_in(node, a, b):
            for kp in pts:
                dx = round(kp.co.x) - kp.co.x
                if dx:
                    _move(kp, dx)
                    n += 1
            fc.update()
    return n


def set_key_type(context, a, b, ktype):
    n = 0
    for node in nodes(context):
        for _fc, pts in keys_in(node, a, b):
            for kp in pts:
                kp.type = ktype
                n += 1
    return n


def inbetween(context, frame, delta):
    """Add (+1) / Remove (-1) an inbetween at ``frame``: the keys after it move by ``delta``
    (Remove only where the next key is more than one frame away, so keys never collide)."""
    n = 0
    for node in nodes(context):
        for fc in node_fcurves(node):
            later = [kp for kp in fc.keyframe_points if kp.co.x > frame + 0.5]
            if not later:
                continue
            if delta < 0 and min(kp.co.x for kp in later) < frame + 1.5:
                continue
            for kp in later:
                _move(kp, delta)
                n += 1
            fc.update()
    return n


def set_tangent(context, a, b, kind):
    n = 0
    for node in nodes(context):
        for fc, pts in keys_in(node, a, b):
            for kp in pts:
                apply_tangent(kp, kind)
                n += 1
            fc.update()
    return n


def key_span(context):
    """(first, last) key frame of the nodes, or None."""
    frames = [kp.co.x for node in nodes(context) for fc in node_fcurves(node) for kp in fc.keyframe_points]
    return (int(round(min(frames))), int(round(max(frames)))) if frames else None


# --- Maya Key menu commands with their options (step 140, issue #35) ------------------------------
# Maya's Key > Delete / Cut / Copy / Paste / Scale / Snap Keys run cutKey / copyKey / pasteKey / scaleKey / snapKey with
# the option window's values (research/maya/re/option_boxes_140.md; doCutKeyArgList: Time range All = no -time, Time
# Slider = the playback range, Start/End = the fields). Results measured with mayapy:
# research/maya/re/option_boxes_140_edit.md. Values (pivots, offsets, multiples) are Maya values: display units for
# translations, degrees for rotations.

class KeyScope:
    """The keySetOptionBoxCommon fields: which nodes, channels and times a key command acts on."""

    NAMES = ("objects", "hierarchy", "channels", "driven", "shapes", "time_range", "start", "end")

    def __init__(self, objects="Selected", hierarchy="Selected", channels="All keyable", driven=False, shapes=True,
                 time_range="All", start=0.0, end=10.0):
        self.objects, self.hierarchy, self.channels = objects, hierarchy, channels
        self.driven, self.shapes = driven, shapes
        self.time_range, self.start, self.end = time_range, start, end

    @classmethod
    def of(cls, values):
        return cls(**{k: values[k] for k in cls.NAMES if k in values})


class CurveRef:
    """One F-curve in scope: ``part`` "node" (the node's own), "driver" (a set-driven-key curve), "data" / "shape"
    (Maya Shapes: the object data's and its shape keys' curves)."""

    def __init__(self, node, part, coll, fc, rel):
        self.node, self.part, self.coll, self.fc, self.rel = node, part, coll, fc, rel

    @property
    def key(self):
        return (self.part, self.rel, self.fc.array_index)


def scope_nodes(context, scope):
    if scope.objects == "All":
        return [ob for ob in context.scene.objects if ob is not None]
    ns = nodes(context)
    if scope.hierarchy != "Below":
        return ns
    from .freeze import hierarchy
    out = []
    for n in ns:
        if _cb().is_bone(n):
            pose = n.id_data.pose
            chain = [n] + [pose.bones[b.name] for b in n.bone.children_recursive if b.name in pose.bones]
        else:
            chain = hierarchy([n])
        out.extend(x for x in chain if x not in out)
    return out


def _channel_filter(context, node):
    """{(data path, index)} of the Channel Box's selected channels on ``node`` (From Channel Box), None = all."""
    cb = _cb()
    allowed = set()
    for k in cb.selected_channels(context):
        try:
            path, idx, _kind = cb.channel_path(k)
        except KeyError:
            continue
        full = cb.full_path(node, path)
        if full:
            allowed.add((full, max(idx, 0)))
    return allowed or None      # nothing selected in the Channel Box: every channel


def scope_curves(context, scope):
    from .. import compat
    out, seen = [], set()

    def add(node, part, coll, fc, rel):
        if fc.as_pointer() not in seen:
            seen.add(fc.as_pointer())
            out.append(CurveRef(node, part, coll, fc, rel))

    for node in scope_nodes(context, scope):
        pre = prefix(node)
        allowed = _channel_filter(context, node) if scope.channels == "From Channel Box" else None
        coll = _cb()._fcurves(node)
        for fc in node_fcurves(node):
            if allowed is None or (fc.data_path, fc.array_index) in allowed:
                add(node, "node", coll, fc, fc.data_path[len(pre):])
        ad = node.id_data.animation_data
        if scope.driven and ad is not None:
            for fc in ad.drivers:
                if len(fc.keyframe_points) and (not pre or fc.data_path.startswith(pre)) and (
                        allowed is None or (fc.data_path, fc.array_index) in allowed):
                    add(node, "driver", None, fc, fc.data_path[len(pre):])
        if scope.shapes and allowed is None and not _cb().is_bone(node):
            data = getattr(node, "data", None)
            for part, idb in (("data", data), ("shape", getattr(data, "shape_keys", None))):
                if idb is None:
                    continue
                for fc in compat.id_fcurves(idb):
                    add(node, part, compat.id_fcurve_collection(idb), fc, fc.data_path)
    return out


def scope_range(context, scope):
    """(a, b) of a key command, or None = every key (Maya Time range All)."""
    if scope.time_range == "Start/End":
        return min(scope.start, scope.end), max(scope.start, scope.end)
    if scope.time_range == "Time Slider":     # doCutKeyArgList: playbackOptions -min / -max
        sc = context.scene
        if sc.use_preview_range:
            return float(sc.frame_preview_start), float(sc.frame_preview_end)
        return float(sc.frame_start), float(sc.frame_end)
    return None


EPS = 1e-4


def _within(x, rng):
    return rng is None or rng[0] - EPS <= x <= rng[1] + EPS


def value_unit(fc):
    """Blender value per Maya value of a curve: the display length unit for translations, radians per degree."""
    import math
    from . import units
    path = fc.data_path.rsplit(".", 1)[-1]
    if path in ("location", "delta_location"):
        return units.maya_unit()
    if path in ("rotation_euler", "delta_rotation_euler"):
        return math.radians(1.0)
    return 1.0


def _remove_points(fc, pts):
    for kp in sorted(pts, key=lambda p: -p.co.x):
        fc.keyframe_points.remove(kp, fast=True)


def _drop_empty(ref):
    if ref.part != "driver" and ref.coll is not None and len(ref.fc.keyframe_points) == 0:
        ref.coll.remove(ref.fc)
        return
    if len(ref.fc.keyframe_points):
        ref.fc.update()


def _offset_value(kp, dv):
    kp.co.y += dv
    kp.handle_left.y += dv
    kp.handle_right.y += dv


# --- operators ----------------------------------------------------------------------------------

def _redraw(context):
    for area in context.screen.areas if context.screen else ():
        area.tag_redraw()


class ALLSET_OT_set_key(bpy.types.Operator):
    """Set a key on every keyable channel of the selection (Maya S); the active keying set if there is one"""
    bl_idname = "allset.set_key"
    bl_label = "Set Key"
    bl_options = {'REGISTER', 'UNDO'}

    breakdown: BoolProperty(name="Breakdown", description="Set a breakdown key (Maya Set Breakdown Key)",
                            options={'SKIP_SAVE'})

    @classmethod
    def poll(cls, context):
        return context.scene.keying_sets.active is not None or _cb().lead(context) is not None

    def execute(self, context):
        n = set_key(context, self.breakdown)
        if n == 0:
            self.report({'WARNING'}, "Nothing keyable selected")
            return {'CANCELLED'}
        self.report({'INFO'}, f"{'Breakdown' if self.breakdown else 'Key'}: {n} channel(s)")
        _redraw(context)
        return {'FINISHED'}


ACTIONS = (("CUT", "Cut", "Remove keys and place on the animation clipboard"),
           ("COPY", "Copy", "Copy keys and place on the animation clipboard"),
           ("PASTE", "Paste", "Paste keys from the animation clipboard at the current time"),
           ("DELETE", "Delete", "Delete keys but do not place on the animation clipboard"),
           ("SNAP", "Snap", "Snap keys to whole frames"),
           ("TO_KEY", "Convert to Key", "Change existing breakdowns into keys"),
           ("TO_BREAKDOWN", "Convert to Breakdown", "Change existing keys into breakdowns"),
           ("ADD_INBETWEEN", "Add Inbetween", "Insert an inbetween at the current time (later keys move one frame)"),
           ("REMOVE_INBETWEEN", "Remove Inbetween", "Remove an inbetween at the current time"),
           ("TANGENT", "Tangent", "Set in and out tangents"))


class ALLSET_OT_time_keys(bpy.types.Operator):
    """Edit the selection's keys in the Time Slider range (Shift-drag), else at the current frame (Maya Time Slider menu)"""
    bl_idname = "allset.time_keys"
    bl_label = "Time Slider Keys"
    bl_options = {'REGISTER', 'UNDO'}

    action: EnumProperty(name="Action", items=ACTIONS, options={'SKIP_SAVE'})
    tangent: EnumProperty(name="Tangent", items=TANGENT_ITEMS, options={'SKIP_SAVE'})

    @classmethod
    def description(cls, context, props):
        return next(d for k, _l, d in ACTIONS if k == props.action)

    @classmethod
    def poll(cls, context):
        return _cb().lead(context) is not None

    def execute(self, context):
        a, b = time_range(context)
        frame = context.scene.frame_current
        act = self.action
        if act == "COPY":
            n = copy_keys(context, a, b)
        elif act == "CUT":
            n = copy_keys(context, a, b)
            delete_keys(context, a, b)
        elif act == "PASTE":
            n = paste_keys(context, frame)
        elif act == "DELETE":
            n = delete_keys(context, a, b)
        elif act == "SNAP":
            n = snap_keys(context, a, b)
        elif act in ("TO_KEY", "TO_BREAKDOWN"):
            n = set_key_type(context, a, b, 'KEYFRAME' if act == "TO_KEY" else 'BREAKDOWN')
        elif act in ("ADD_INBETWEEN", "REMOVE_INBETWEEN"):
            n = inbetween(context, frame, 1 if act == "ADD_INBETWEEN" else -1)
        else:
            n = set_tangent(context, a, b, self.tangent)
        self.report({'INFO'}, f"{dict((k, l) for k, l, _d in ACTIONS)[act]}: {n} key(s)")
        _redraw(context)
        return {'FINISHED'}


class ALLSET_OT_time_set_range(bpy.types.Operator):
    """Set the playback range (Maya Time Slider > Set Range to)"""
    bl_idname = "allset.time_set_range"
    bl_label = "Set Range to"
    bl_options = {'REGISTER', 'UNDO'}

    mode: EnumProperty(items=(("START_END", "Start/End", "Playback range = animation range"),
                              ("MIN_MAX", "Min/Max", "Playback range = first and last keys of the selection"),
                              ("SELECTED", "Selected", "Playback range = the Shift-dragged Time Slider range")),
                       options={'SKIP_SAVE'})

    def execute(self, context):
        scene, wm = context.scene, context.window_manager
        if self.mode == "START_END":
            a, b = scene.frame_start, scene.frame_end
        elif self.mode == "MIN_MAX":
            span = key_span(context)
            if span is None:
                self.report({'WARNING'}, "No keys found. Cannot determine min/max of animation range.")
                return {'CANCELLED'}
            a, b = span
        else:
            if not getattr(wm, "allset_time_range_on", False):
                self.report({'WARNING'}, "No range selected. Use Shift-LMB to select a range.")
                return {'CANCELLED'}
            a, b = time_range(context)
        scene.use_preview_range = True
        a, b = int(a), int(max(a, b))
        if a > scene.frame_preview_end:   # the setters keep start <= end: move the far side first
            scene.frame_preview_end, scene.frame_preview_start = b, a
        else:
            scene.frame_preview_start, scene.frame_preview_end = a, b
        return {'FINISHED'}


classes = (ALLSET_OT_set_key, ALLSET_OT_time_keys, ALLSET_OT_time_set_range)
