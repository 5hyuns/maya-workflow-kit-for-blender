# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya Channel Box in the 3D View sidebar (category "Channel Box").

; design:  「계획」.
- Translate/Rotate/Scale/Visibility rows are getter/setter proxies on
  ``Scene.maya_kit_cb``: they read the lead (active) object and write every
  selected object, like Maya (channel_box.md:52-55).
- Channel names are buttons that select channels; selected channels drive
  the MMB virtual slider in the viewport (channel_box.md) and the
  Channels menu ().
- Value fields are text (step 38): Maya numbers in display units and relative entry
  (``+=5``, ``*=2``; ui/cb_entry.py), applied to every selected object that has the
  channel and to every selected channel when the edited row is one of them.
- Custom properties, SHAPES (object data) and INPUTS (modifiers = construction history,
 ) are rows in ``Scene.maya_kit_cb.rows`` (rebuilt from handlers), so their edits reach
  the same-named channel of the other selected objects too; stale rows fall back to the
  lead object's real properties.
"""

import math

import bpy
from bpy.app.handlers import persistent
from bpy.props import (BoolProperty, CollectionProperty, EnumProperty, FloatProperty, IntProperty,
                       StringProperty)

from ..operators import display
from . import cb_entry, chrome

CATEGORY = "Channel Box"

# key, label, data path, index, kind
MAIN = (
    ("tx", "Translate X", "location", 0, "LOC"),
    ("ty", "Translate Y", "location", 1, "LOC"),
    ("tz", "Translate Z", "location", 2, "LOC"),
    ("rx", "Rotate X", "rotation_euler", 0, "ROT"),
    ("ry", "Rotate Y", "rotation_euler", 1, "ROT"),
    ("rz", "Rotate Z", "rotation_euler", 2, "ROT"),
    ("sx", "Scale X", "scale", 0, "SCALE"),
    ("sy", "Scale Y", "scale", 1, "SCALE"),
    ("sz", "Scale Z", "scale", 2, "SCALE"),
    ("v", "Visibility", "hide_viewport", -1, "VIS"),
)
MAIN_BY_KEY = {c[0]: c for c in MAIN}
_LOCK_PROP = {"LOC": "lock_location", "ROT": "lock_rotation", "SCALE": "lock_scale"}

# Per-object bookkeeping for Maya attribute flags Blender doesn't have.
HIDDEN_PROP = "maya_kit_cb_hidden"
NONKEYABLE_PROP = "maya_kit_cb_nonkeyable"
CUSTOM_PREFIX = "cp:"

# MMB slider: value change per pixel at speed Medium ( 「계획」 ).
SLIDER_STEP = {"LOC": 0.01, "ROT": math.radians(0.5), "SCALE": 0.01, "CUSTOM": 0.01}
SPEEDS = (("SLOWEST", "Slowest", "x0.01", 0.01), ("SLOW", "Slow", "x0.1", 0.1),
          ("MEDIUM", "Medium", "x1", 1.0), ("FAST", "Fast", "x10", 10.0))
SPEED_FACTOR = {s[0]: s[3] for s in SPEEDS}


# --- nodes: objects or pose bones -------------------------
# A Maya joint is a pose bone (). Pose bones carry the
# same RNA names as objects (location / rotation_euler / scale / lock_* / rotation_mode / ID
# properties); only their animation lives on the armature object (``pose.bones["n"].<path>``).

def is_bone(node):
    return isinstance(node, bpy.types.PoseBone)


def bone_selected(pb):
    sel = getattr(pb, "select", None)   # 4.5: Bone.select; newer versions may keep it on the pose bone
    return pb.bone.select if sel is None else sel


def set_bone_selected(pb, state):
    if hasattr(pb, "select"):
        pb.select = state
    else:
        pb.bone.select = state


def pose_armature(context=None):
    """The active armature when it is in pose mode (= Maya: joints are being picked)."""
    ob = (context or bpy.context).active_object
    return ob if ob is not None and ob.type == 'ARMATURE' and ob.mode == 'POSE' else None


def placing_joints(context=None):
    ob = (context or bpy.context).active_object
    return ob is not None and ob.type == 'ARMATURE' and ob.mode == 'EDIT'


def pose_objects(context=None):
    context = context or bpy.context
    arm = pose_armature(context)
    if arm is None:
        return []
    others = [o for o in context.view_layer.objects
              if o is not arm and o.type == 'ARMATURE' and o.mode == 'POSE']
    return [arm] + others


def selected_bones(context=None):
    return [pb for arm in pose_objects(context) for pb in arm.pose.bones
            if bone_selected(pb) and not pb.bone.hide]


def lead(context=None):
    """The Maya lead: the active object, or in pose mode the active (selected) pose bone."""
    context = context or bpy.context
    arm = pose_armature(context)
    if arm is None:
        return context.active_object
    act = arm.data.bones.active
    pb = arm.pose.bones.get(act.name) if act is not None else None
    if pb is not None and bone_selected(pb) and not pb.bone.hide:
        return pb
    sel = selected_bones(context)
    return sel[0] if sel else None


def targets(context=None):
    """Lead + selected objects / pose bones (lead first), like Maya's selection list."""
    context = context or bpy.context
    nodes = selected_bones(context) if pose_armature(context) else list(context.selected_objects)
    ld = lead(context)
    if ld is not None:
        nodes = [ld] + [n for n in nodes if n != ld]
    return nodes


def full_path(node, path):
    """Animation data path of ``path`` on the node's ID (the armature object for a bone)."""
    if not is_bone(node):
        return path
    return None if path == "hide_viewport" else node.path_from_id(path)   # bone visibility: Bone.hide


def _flag_list(ob, prop):
    raw = ob.get(prop, "")
    return [s for s in raw.split(",") if s] if isinstance(raw, str) else []


def _set_flag_list(ob, prop, keys):
    if keys:
        ob[prop] = ",".join(sorted(set(keys)))
    elif prop in ob:
        del ob[prop]


def is_hidden(ob, key):
    return key in _flag_list(ob, HIDDEN_PROP)


def is_keyable(ob, key):
    if key == "v" and is_bone(ob):
        return False   # Bone.hide lives on the armature data, not in the object's action
    return key not in _flag_list(ob, NONKEYABLE_PROP)


def is_locked(ob, key):
    c = MAIN_BY_KEY.get(key)
    if c is None or c[4] not in _LOCK_PROP:
        return False
    return bool(getattr(ob, _LOCK_PROP[c[4]])[c[3]])


def set_locked(ob, key, locked):
    c = MAIN_BY_KEY.get(key)
    if c is None or c[4] not in _LOCK_PROP:
        return False
    arr = getattr(ob, _LOCK_PROP[c[4]])
    arr[c[3]] = locked
    return True


def custom_keys(ob):
    """Numeric custom properties = Maya extra (user-defined) attributes."""
    out = []
    for k in ob.keys():
        if k.startswith("_") or k.startswith("maya_kit_"):
            continue
        if isinstance(ob[k], (int, float)):  # bool is an int too
            out.append(k)
    return sorted(out)


def channel_path(key):
    """(data path, index, kind) for a channel key."""
    if key.startswith(CUSTOM_PREFIX):
        return f'["{key[len(CUSTOM_PREFIX):]}"]', -1, "CUSTOM"
    c = MAIN_BY_KEY[key]
    return c[2], c[3], c[4]


def channel_label(key):
    if key.startswith(CUSTOM_PREFIX):
        return key[len(CUSTOM_PREFIX):]
    return MAIN_BY_KEY[key][1]


def has_channel(ob, key):
    if key.startswith(CUSTOM_PREFIX):
        return key[len(CUSTOM_PREFIX):] in ob.keys()
    kind = MAIN_BY_KEY[key][4]
    return kind != "ROT" or ob.rotation_mode in {'XYZ', 'XZY', 'YXZ', 'YZX', 'ZXY', 'ZYX'}


def get_value(ob, key):
    path, idx, kind = channel_path(key)
    if kind == "CUSTOM":
        return ob[key[len(CUSTOM_PREFIX):]]
    if kind == "VIS":
        return not (ob.bone.hide if is_bone(ob) else ob.hide_viewport)
    return getattr(ob, path)[idx]


def set_value(ob, key, value):
    path, idx, kind = channel_path(key)
    if kind == "CUSTOM":
        ob[key[len(CUSTOM_PREFIX):]] = type(ob[key[len(CUSTOM_PREFIX):]])(value)
    elif kind == "VIS":
        if is_bone(ob):
            ob.bone.hide = not value
        else:
            ob.hide_viewport = not value
    else:
        getattr(ob, path)[idx] = value


def keyframe(ob, key, keytype='KEYFRAME'):
    path, idx, kind = channel_path(key)
    if kind == "VIS" and is_bone(ob):
        return False
    return ob.keyframe_insert(path, index=idx, keytype=keytype)


# --- animation state ---------------------------------------------------------------------

def _fcurves(ob):
    ad = ob.id_data.animation_data
    if ad is None or ad.action is None:
        return None
    try:
        from bpy_extras.anim_utils import action_get_channelbag_for_slot
        bag = action_get_channelbag_for_slot(ad.action, ad.action_slot)
        return bag.fcurves if bag is not None else None
    except ImportError:  # pre-4.4 actions
        return ad.action.fcurves


def fcurve(ob, key):
    fcs = _fcurves(ob)
    if fcs is None:
        return None
    path, idx, _kind = channel_path(key)
    path = full_path(ob, path)
    return None if path is None else fcs.find(path, index=max(idx, 0))


def driver(ob, key):
    ad = ob.id_data.animation_data
    if ad is None:
        return None
    path, idx, _kind = channel_path(key)
    path = full_path(ob, path)
    return None if path is None else ad.drivers.find(path, index=max(idx, 0))


def channel_state(ob, key, frame=None):
    """'DRIVEN', 'KEYED' (key on this frame), 'ANIMATED' or None (channel_box.md:138-139)."""
    if driver(ob, key) is not None:
        return 'DRIVEN'
    fc = fcurve(ob, key)
    if fc is None:
        return None
    frame = bpy.context.scene.frame_current if frame is None else frame
    if any(abs(kp.co[0] - frame) < 0.5 for kp in fc.keyframe_points):
        return 'KEYED'
    return 'ANIMATED'


# --- channel selection (WindowManager string; not undoable) -----------------------------------

def selected_channels(context=None):
    wm = (context or bpy.context).window_manager
    return [s for s in wm.maya_kit_cb_selected.split(",") if s]


def set_selected_channels(keys, context=None):
    wm = (context or bpy.context).window_manager
    wm.maya_kit_cb_selected = ",".join(dict.fromkeys(keys))


def select_channel(key, mode="SET", context=None):
    """mode: SET (click), TOGGLE (Ctrl), EXTEND (Shift)."""
    sel = selected_channels(context)
    if mode == "SET":
        sel = [key]
    elif mode == "TOGGLE":
        sel = [k for k in sel if k != key] if key in sel else sel + [key]
    else:
        sel = sel + [key]
    set_selected_channels(sel, context)
    return sel


# --- proxies -------------------------------------------------------------------------------------

def _proxy_get(key):
    def get(_self):
        ob = lead()
        if ob is None or not has_channel(ob, key):
            return False if MAIN_BY_KEY[key][4] == "VIS" else 0.0
        return get_value(ob, key)
    return get


def _proxy_set(key):
    def set_(_self, value):
        context = bpy.context
        autokey = context.scene.tool_settings.use_keyframe_insert_auto
        for ob in targets(context):
            if not has_channel(ob, key) or is_locked(ob, key):
                continue
            set_value(ob, key, value)
            if autokey and is_keyable(ob, key):
                keyframe(ob, key)
    return set_


# --- text entry (step 38) ------------------------------------------------------------------

_KIND_ENTRY = {"LOC": "LENGTH", "ROT": "ROTATION", "SCALE": "NONE", "VIS": "BOOL"}


def entry_kind(ob, key):
    if key.startswith(CUSTOM_PREFIX):
        return cb_entry.kind_of_value(ob.get(key[len(CUSTOM_PREFIX):]))
    return _KIND_ENTRY[MAIN_BY_KEY[key][4]]


def entry_keys(key, context=None):
    """The edited channel, or every selected channel when it is one of them (channel_box.md:136)."""
    sel = selected_channels(context)
    return sel if key in sel else [key]


def apply_entry(key, text, context=None):
    """Typed text on channel ``key``: absolute or relative (``+=``...) per object, on every
    selected object that has the channel; returns how many values changed."""
    context = context or bpy.context
    scene = context.scene
    autokey = scene.tool_settings.use_keyframe_insert_auto
    count = 0
    for k in entry_keys(key, context):
        for ob in targets(context):
            if not has_channel(ob, k) or is_locked(ob, k):
                continue
            kind = entry_kind(ob, k)
            if kind is None:
                continue
            try:
                value = cb_entry.parse_entry(text, get_value(ob, k), kind, scene)
            except (ValueError, TypeError, SyntaxError):
                return count
            set_value(ob, k, value)
            count += 1
            if autokey and is_keyable(ob, k):
                keyframe(ob, k)
    return count


def _text_get(key):
    def get(_self):
        ob = lead()
        if ob is None or not has_channel(ob, key):
            return ""
        return cb_entry.format_value(get_value(ob, key), entry_kind(ob, key), bpy.context.scene)
    return get


def _text_set(key):
    def set_(_self, text):
        apply_entry(key, text)
    return set_


# --- rows for custom attributes, SHAPES and INPUTS (step 38) --------------------------------

def _inputs(ob):
    return [m for m in getattr(ob, "modifiers", ()) if not display.is_preview(m)]


# --- constraints = Maya constraint nodes ------------------------
#  (pCube1_parentConstraint1, weight locator1W0), :126.

MAYA_CONSTRAINT = {'CHILD_OF': "parentConstraint", 'COPY_TRANSFORMS': "parentConstraint",
                   'COPY_LOCATION': "pointConstraint", 'COPY_ROTATION': "orientConstraint",
                   'COPY_SCALE': "scaleConstraint", 'TRACK_TO': "aimConstraint",
                   'DAMPED_TRACK': "aimConstraint", 'LOCKED_TRACK': "aimConstraint"}
_AIM = ('TRACK_TO', 'DAMPED_TRACK', 'LOCKED_TRACK')


def constraints(node):
    """Constraints shown as INPUTS nodes (Limit constraints are Maya transform limits: AE only)."""
    return [c for c in getattr(node, "constraints", ()) if not c.type.startswith("LIMIT_")]


def constraint_enabled(con):
    en = getattr(con, "enabled", None)
    return (not con.mute) if en is None else bool(en)


def _nth_constraint(node, con):
    return [c for c in constraints(node) if c.type == con.type].index(con)


def constraint_node_name(node, con):
    """Maya's name for the constraint node: ``<node>_<type><n>`` (pCube1_parentConstraint1)."""
    mtype = MAYA_CONSTRAINT.get(con.type)
    if mtype is None:
        return con.name
    same = [c for c in constraints(node) if MAYA_CONSTRAINT.get(c.type) == mtype]
    return f"{node.name}_{mtype}{same.index(con) + 1}"


def weight_name(con):
    """Maya target weight attribute: ``<target>W0`` (one target per Blender constraint)."""
    target = getattr(con, "target", None)
    if target is None:
        return "W0"
    sub = getattr(con, "subtarget", "")
    return f"{sub if target.type == 'ARMATURE' and sub else target.name}W0"


def _axes(con, pattern):
    return [a for a in "xyz" if getattr(con, pattern.format(a), True)]


def constrained_keys(node):
    """Channel keys an enabled constraint drives (Maya draws them blue, channel_box.md:138-139)."""
    out = set()
    for con in constraints(node):
        if not constraint_enabled(con):
            continue
        t = con.type
        if t == 'CHILD_OF':
            for k, pattern in (("t", "use_location_{}"), ("r", "use_rotation_{}"), ("s", "use_scale_{}")):
                out.update(k + a for a in _axes(con, pattern))
        elif t in ('COPY_TRANSFORMS', 'ARMATURE'):
            out.update(k for k in MAIN_BY_KEY if k != "v")
        elif t == 'COPY_LOCATION':
            out.update("t" + a for a in _axes(con, "use_{}"))
        elif t == 'COPY_ROTATION':
            out.update("r" + a for a in _axes(con, "use_{}"))
        elif t == 'COPY_SCALE':
            out.update("s" + a for a in _axes(con, "use_{}"))
        elif t in _AIM:
            out.update(("rx", "ry", "rz"))
    return out


def _nth_of_type(ob, mod):
    return [m for m in _inputs(ob) if m.type == mod.type].index(mod)


def row_owner(ob, kind, name, mod_type="", nth=0, lead_ob=None):
    """The struct holding row ``name`` on ``ob`` (None: ob has no such channel).

    Same-named channel: custom = same property name,
    SHAPE = same object type and data property, INPUT = same modifier type at the same
    position among that type."""
    if kind == "CUSTOM":
        return ob if name in ob.keys() else None
    if kind == "SHAPE":
        data = getattr(ob, "data", None)
        if data is None or (lead_ob is not None and ob.type != lead_ob.type):
            return None
        return data if name in data.bl_rna.properties else None
    if kind == "INPUT":
        mods = [m for m in _inputs(ob) if m.type == mod_type]
        if nth < len(mods) and name in mods[nth].bl_rna.properties:
            return mods[nth]
    if kind == "CONSTRAINT":
        cons = [c for c in constraints(ob) if c.type == mod_type]
        if nth < len(cons) and name in cons[nth].bl_rna.properties:
            return cons[nth]
    return None


def _row_kind(owner, kind, name):
    if kind == "CUSTOM":
        return cb_entry.kind_of_value(owner.get(name))
    return cb_entry.kind_of_rna(owner.bl_rna.properties[name])


def _row_read(owner, kind, name):
    return owner[name] if kind == "CUSTOM" else getattr(owner, name)


def _row_write(owner, kind, name, value):
    if kind == "CUSTOM":
        owner[name] = type(owner[name])(value)
    else:
        setattr(owner, name, value)


def _row_get(self):
    ob = lead()
    if ob is None:
        return ""
    owner = row_owner(ob, self.kind, self.name, self.mod_type, self.nth)
    if owner is None:
        return ""
    entry = _row_kind(owner, self.kind, self.name)
    return cb_entry.format_value(_row_read(owner, self.kind, self.name), entry, bpy.context.scene)


def apply_row_entry(row, text, context=None):
    """Typed text on a custom / SHAPES / INPUTS row: every selected object with that channel."""
    context = context or bpy.context
    if row.kind == "CUSTOM":
        return apply_entry(CUSTOM_PREFIX + row.name, text, context)
    ld = lead(context)
    count = 0
    for ob in targets(context):
        owner = row_owner(ob, row.kind, row.name, row.mod_type, row.nth, ld)
        if owner is None:
            continue
        entry = _row_kind(owner, row.kind, row.name)
        try:
            value = cb_entry.parse_entry(text, _row_read(owner, row.kind, row.name), entry,
                                         context.scene)
        except (ValueError, TypeError, SyntaxError):
            return count
        try:
            _row_write(owner, row.kind, row.name, value)
        except (TypeError, ValueError, AttributeError):
            continue
        count += 1
    return count


def _row_set(self, text):
    apply_row_entry(self, text)


class MAYAKIT_PG_cb_row(bpy.types.PropertyGroup):
    kind: StringProperty()        # CUSTOM / SHAPE / INPUT / CONSTRAINT
    name: StringProperty()        # property name
    mod_type: StringProperty()    # INPUT: modifier type, CONSTRAINT: constraint type
    nth: IntProperty()            # position among the lead's modifiers / constraints of that type
    text: StringProperty(get=_row_get, set=_row_set)


def _make_proxy_annotations():
    ann = {}
    for key, label, _path, _idx, kind in MAIN:
        if kind == "VIS":
            ann[key] = BoolProperty(name=label, get=_proxy_get(key), set=_proxy_set(key))
        elif kind == "LOC":
            ann[key] = FloatProperty(name=label, get=_proxy_get(key), set=_proxy_set(key),
                                     subtype='DISTANCE', unit='LENGTH', precision=3, step=10)
        elif kind == "ROT":
            ann[key] = FloatProperty(name=label, get=_proxy_get(key), set=_proxy_set(key),
                                     subtype='ANGLE', unit='ROTATION', precision=3)
        else:
            ann[key] = FloatProperty(name=label, get=_proxy_get(key), set=_proxy_set(key),
                                     precision=3, step=10)
        ann[key + "_text"] = StringProperty(name=label, get=_text_get(key), set=_text_set(key))
    ann["rows"] = CollectionProperty(type=MAYAKIT_PG_cb_row)
    ann["rows_sig"] = StringProperty(options={'HIDDEN'})
    return ann


MAYAKIT_PG_channel_box = type("MAYAKIT_PG_channel_box", (bpy.types.PropertyGroup,),
                              {"__annotations__": _make_proxy_annotations()})


# --- MMB virtual slider ---------------------------------------------------------------------------

def slider_delta(dx, kind, speed=1.0, ctrl=False, shift=False, hyperbolic=False):
    d = float(dx)
    if hyperbolic:
        d = d * abs(d) / 50.0
    factor = speed * (0.1 if ctrl else 1.0) * (10.0 if shift else 1.0)
    return d * SLIDER_STEP[kind] * factor


def slider_targets(context):
    """[(object, key)] the slider would change: selected numeric channels on targets."""
    out = []
    for key in selected_channels(context):
        if key in MAIN_BY_KEY and MAIN_BY_KEY[key][4] == "VIS":
            continue
        for ob in targets(context):
            if has_channel(ob, key) and not is_locked(ob, key) and not is_hidden(ob, key):
                if key.startswith(CUSTOM_PREFIX) and isinstance(get_value(ob, key), bool):
                    continue
                out.append((ob, key))
    return out


def slider_apply(starts, dx, speed=1.0, ctrl=False, shift=False, hyperbolic=False):
    """starts: {(ob, key): start value}. Sets each to start + delta."""
    for (ob, key), start in starts.items():
        kind = channel_path(key)[2]
        set_value(ob, key, start + slider_delta(dx, kind, speed, ctrl, shift, hyperbolic))


class MAYAKIT_OT_cb_virtual_slider(bpy.types.Operator):
    """MMB-drag in the viewport changes the channels selected in the Channel Box"""
    bl_idname = "maya_kit.cb_virtual_slider"
    bl_label = "Channel Box Virtual Slider"
    bl_options = {'REGISTER', 'UNDO', 'GRAB_CURSOR_X', 'BLOCKING'}

    def invoke(self, context, event):
        if context.mode not in {'OBJECT', 'POSE'}:
            return {'PASS_THROUGH'}
        pairs = slider_targets(context)
        if not pairs:
            return {'PASS_THROUGH'}  # let the tool's MMB drag run
        self._starts = {(ob, key): get_value(ob, key) for ob, key in pairs}
        self._dx = 0
        self._last_x = event.mouse_x
        from .. import preferences
        prefs = preferences.get(context)
        self._speed = SPEED_FACTOR[prefs.cb_speed]
        self._hyper = prefs.cb_hyperbolic
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def _header(self, context, text):
        if context.area:
            context.area.header_text_set(text)

    def modal(self, context, event):
        if event.type == 'MOUSEMOVE':
            step = event.mouse_x - self._last_x
            self._last_x = event.mouse_x
            if context.region and abs(step) > context.region.width // 2:
                step = 0  # cursor wrapped by GRAB_CURSOR_X: not a real move
            self._dx += step
            slider_apply(self._starts, self._dx, self._speed, event.ctrl, event.shift, self._hyper)
            ob, key = next(iter(self._starts))
            self._header(context, f"{channel_label(key)}: {get_value(ob, key):.3f}  "
                                  "(Ctrl slower, Shift faster, Esc cancel)")
            return {'RUNNING_MODAL'}
        if event.type == 'MIDDLEMOUSE' and event.value == 'RELEASE':
            self._header(context, None)
            return {'FINISHED'}
        if event.type in {'ESC', 'RIGHTMOUSE'} and event.value == 'PRESS':
            for (ob, key), start in self._starts.items():
                set_value(ob, key, start)
            self._header(context, None)
            return {'CANCELLED'}
        return {'RUNNING_MODAL'}


# --- operators: selection, Channels menu ----------------------------------------------------------

class MAYAKIT_OT_cb_select_channel(bpy.types.Operator):
    """Select this channel (Ctrl: toggle, Shift: add). Selected channels follow MMB-drag in the viewport"""
    bl_idname = "maya_kit.cb_select_channel"
    bl_label = "Select Channel"
    bl_options = {'INTERNAL'}

    key: StringProperty()
    mode: EnumProperty(items=(("SET", "Set", ""), ("TOGGLE", "Toggle", ""), ("EXTEND", "Extend", "")))

    def invoke(self, context, event):
        self.mode = "TOGGLE" if event.ctrl else "EXTEND" if event.shift else "SET"
        return self.execute(context)

    def execute(self, context):
        select_channel(self.key, self.mode, context)
        for area in context.screen.areas if context.screen else ():
            area.tag_redraw()
        return {'FINISHED'}


class MAYAKIT_OT_cb_deselect_channels(bpy.types.Operator):
    """Clear the Channel Box channel selection"""
    bl_idname = "maya_kit.cb_deselect_channels"
    bl_label = "Deselect Channels"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        set_selected_channels([], context)
        return {'FINISHED'}


def _visible_channels(ob):
    keys = [c[0] for c in MAIN if has_channel(ob, c[0])] + \
           [CUSTOM_PREFIX + k for k in custom_keys(ob)]
    return [k for k in keys if not is_hidden(ob, k)]


class _ChannelAction:
    """Base: acts on selected channels of all target objects."""
    bl_options = {'REGISTER', 'UNDO'}
    use_all = False  # True: every visible channel when nothing is selected

    @classmethod
    def poll(cls, context):
        return lead(context) is not None

    def channel_keys(self, context, ob):
        sel = selected_channels(context)
        if not sel and self.use_all:
            return _visible_channels(ob)
        return [k for k in sel if has_channel(ob, k)]

    def execute(self, context):
        count = 0
        for ob in targets(context):
            for key in self.channel_keys(context, ob):
                count += bool(self.act(context, ob, key))
        self.report({'INFO'}, f"{self.bl_label}: {count} channel(s)")
        return {'FINISHED'}


def _op(idname, label, doc, act, use_all=False, **props):
    cls = type(f"MAYAKIT_OT_{idname}", (_ChannelAction, bpy.types.Operator), {
        "bl_idname": f"maya_kit.{idname}", "bl_label": label, "__doc__": doc,
        "act": act, "use_all": use_all, "__annotations__": props})
    return cls


def _act_key(self, context, ob, key):
    return is_keyable(ob, key) and keyframe(ob, key)


def _act_breakdown(self, context, ob, key):
    return is_keyable(ob, key) and keyframe(ob, key, 'BREAKDOWN')


def _act_mute(self, context, ob, key):
    fc = fcurve(ob, key)
    if fc is not None:
        fc.mute = self.mute
    return fc is not None


def _act_delete(self, context, ob, key):
    fc = fcurve(ob, key)
    if fc is not None:
        _fcurves(ob).remove(fc)
    return fc is not None


def _act_break(self, context, ob, key):
    done = _act_delete(self, context, ob, key)
    dr = driver(ob, key)
    if dr is not None:
        ob.id_data.animation_data.drivers.remove(dr)
        done = True
    return done


def _act_lock(self, context, ob, key):
    return set_locked(ob, key, self.lock)


def _act_hide(self, context, ob, key):
    if self.lock:
        set_locked(ob, key, True)
    _set_flag_list(ob, HIDDEN_PROP, _flag_list(ob, HIDDEN_PROP) + [key])
    return True


def _act_keyable(self, context, ob, key):
    keys = [k for k in _flag_list(ob, NONKEYABLE_PROP) if k != key]
    if not self.keyable:
        keys.append(key)
    _set_flag_list(ob, NONKEYABLE_PROP, keys)
    return True


def _act_duplicate(self, context, ob, key):
    ld = lead(context)
    if ob == ld or not has_channel(ld, key) or is_locked(ob, key):
        return False
    set_value(ob, key, get_value(ld, key))
    return True


CHANNEL_OPS = (
    _op("cb_key_selected", "Key Selected", "Set a key on the selected channels", _act_key),
    _op("cb_key_all", "Key All Keyable", "Set a key on every keyable channel", _act_key, use_all=True),
    _op("cb_breakdown_selected", "Breakdown Selected", "Set a breakdown key on the selected channels",
        _act_breakdown),
    _op("cb_mute", "Mute Selected", "Mute or unmute the animation of the selected channels", _act_mute,
        mute=BoolProperty(default=True)),
    _op("cb_delete_keys", "Delete Selected", "Delete the animation curves of the selected channels",
        _act_delete),
    _op("cb_break_connections", "Break Connections",
        "Remove the animation curve or driver feeding the selected channels", _act_break),
    _op("cb_lock", "Lock Selected", "Lock or unlock the selected channels", _act_lock,
        lock=BoolProperty(default=True)),
    _op("cb_hide", "Hide Selected", "Hide the selected channels from the Channel Box", _act_hide,
        lock=BoolProperty(default=False)),
    _op("cb_keyable", "Make Selected Keyable", "Make the selected channels keyable or nonkeyable",
        _act_keyable, keyable=BoolProperty(default=True)),
    _op("cb_duplicate_values", "Duplicate Values",
        "Copy the lead object's values of the selected channels to the other selected objects",
        _act_duplicate),
)


class MAYAKIT_OT_cb_show_all(bpy.types.Operator):
    """Show every hidden channel again"""
    bl_idname = "maya_kit.cb_show_all"
    bl_label = "Show All Channels"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for ob in targets(context):
            _set_flag_list(ob, HIDDEN_PROP, [])
        return {'FINISHED'}


# --- menus -------------------------------------------------------------------------------------------

class MAYAKIT_MT_cb_channels(bpy.types.Menu):
    bl_label = "Channels"

    def draw(self, context):
        lay = self.layout
        lay.operator("maya_kit.cb_key_selected")
        lay.operator("maya_kit.cb_key_all")
        lay.operator("maya_kit.cb_breakdown_selected")
        lay.operator("maya_kit.cb_mute", text="Mute Selected").mute = True
        lay.operator("maya_kit.cb_mute", text="Unmute Selected").mute = False
        lay.separator()
        lay.operator("maya_kit.cb_delete_keys")
        lay.operator("maya_kit.cb_break_connections")
        lay.separator()
        lay.operator("maya_kit.cb_duplicate_values")
        lay.separator()
        lay.operator("maya_kit.cb_lock", text="Lock Selected").lock = True
        lay.operator("maya_kit.cb_lock", text="Unlock Selected").lock = False
        lay.operator("maya_kit.cb_hide", text="Hide Selected").lock = False
        lay.operator("maya_kit.cb_hide", text="Lock and Hide Selected").lock = True
        lay.operator("maya_kit.cb_show_all")
        lay.operator("maya_kit.cb_keyable", text="Make Selected Nonkeyable").keyable = False
        lay.operator("maya_kit.cb_keyable", text="Make Selected Keyable").keyable = True
        lay.separator()
        lay.operator("maya_kit.cb_deselect_channels")


def is_cb_button(context):
    """The button under the mouse is a Channel Box channel name or value (for its RMB menu)."""
    op = getattr(context, "button_operator", None)
    if op is not None and op.bl_rna.identifier == MAYAKIT_OT_cb_select_channel.__name__:
        return True
    ptr = getattr(context, "button_pointer", None)
    return isinstance(ptr, (MAYAKIT_PG_channel_box, MAYAKIT_PG_cb_row))


# Maya's Channel Box RMB menu = the Channels menu (). RMB on a UI button
# opens Blender's button context menu from C (not a keymap item), so the Channels items go on top of it.
RMB_ITEMS = (("maya_kit.cb_key_selected", "Key Selected", {}),
             ("maya_kit.cb_breakdown_selected", "Breakdown Selected", {}),
             ("maya_kit.cb_mute", "Mute Selected", {"mute": True}),
             ("maya_kit.cb_mute", "Unmute Selected", {"mute": False}),
             ("maya_kit.cb_delete_keys", "Delete Selected", {}),
             ("maya_kit.cb_break_connections", "Break Connections", {}),
             ("maya_kit.cb_lock", "Lock Selected", {"lock": True}),
             ("maya_kit.cb_lock", "Unlock Selected", {"lock": False}),
             ("maya_kit.cb_hide", "Hide Selected", {"lock": False}),
             ("maya_kit.cb_keyable", "Make Selected Nonkeyable", {"keyable": False}))


def draw_button_menu(self, context):
    if not is_cb_button(context):
        return
    lay = self.layout
    for idname, text, props in RMB_ITEMS:
        op = lay.operator(idname, text=text)
        for k, v in props.items():
            setattr(op, k, v)
    lay.separator()


class MAYAKIT_MT_cb_settings(bpy.types.Menu):
    bl_label = "Settings"

    def draw(self, context):
        from .. import preferences
        prefs = preferences.get(context)
        lay = self.layout
        lay.label(text="Virtual slider speed")
        lay.prop(prefs, "cb_speed", expand=True)
        lay.prop(prefs, "cb_hyperbolic")


class MAYAKIT_MT_cb_edit(bpy.types.Menu):
    """Maya Channel Box Edit menu (Maya-174, )"""
    bl_label = "Edit"

    def draw(self, context):
        lay = self.layout
        chrome.grey(lay, "Expressions...")
        chrome.grey(lay, "Set Driven Key...")
        lay.operator("maya_kit.open_editor", text="Graph Editor").ui_type = 'FCURVES'
        chrome.grey(lay, "Channel Control...")
        chrome.grey(lay, "Connection Editor")
        lay.operator("maya_kit.dock_show", text="Attribute Editor").dock = 'ATTRIBUTE_EDITOR'
        lay.operator("maya_kit.material_attributes", text="Material Attributes...")
        lay.separator()
        for label in ("Add Attribute...", "Edit Attribute...", "Duplicate Attribute", "Delete Attributes"):
            chrome.grey(lay, label)
        lay.separator()
        lay.operator(MAYAKIT_OT_cb_make_lead.bl_idname, text="Select Node").only = True
        lay.operator("object.delete", text="Delete Node").use_global = False
        lay.operator("maya_kit.delete_history", text="Delete History")
        lay.separator()
        lay.menu("MAYAKIT_MT_cb_settings", text="Settings")
        chrome.grey(lay, "Channel Names")


class MAYAKIT_OT_cb_make_lead(bpy.types.Operator):
    """Make this object the lead (Maya Channel Box Object menu: select -add)"""
    bl_idname = "maya_kit.cb_make_lead"
    bl_label = "Lead Object"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    name: StringProperty(options={'SKIP_SAVE'})
    only: BoolProperty(name="Only", description="Select only this object", options={'SKIP_SAVE'})

    def execute(self, context):
        if pose_armature(context):
            return self._bone(context)
        ob = context.scene.objects.get(self.name) if self.name else context.active_object
        if ob is None:
            return {'CANCELLED'}
        if self.only:
            for other in context.selected_objects:
                other.select_set(False)
        ob.select_set(True)
        context.view_layer.objects.active = ob
        return {'FINISHED'}

    def _bone(self, context):
        bones = [pb for arm in pose_objects(context) for pb in arm.pose.bones]
        pb = next((b for b in bones if b.name == self.name), None) if self.name else lead(context)
        if pb is None:
            return {'CANCELLED'}
        if self.only:
            for other in bones:
                set_bone_selected(other, False)
        set_bone_selected(pb, True)
        pb.id_data.data.bones.active = pb.bone
        return {'FINISHED'}


class MAYAKIT_OT_cb_rotate_order(bpy.types.Operator):
    """Set the rotate order (Blender converts the rotation, the pose stays): Maya channels need Euler"""
    bl_idname = "maya_kit.cb_rotate_order"
    bl_label = "Rotate Order"
    bl_options = {'REGISTER', 'UNDO'}

    order: EnumProperty(name="Rotate Order", items=[(m, m, "") for m in
                                                    ('XYZ', 'XZY', 'YXZ', 'YZX', 'ZXY', 'ZYX')])

    @classmethod
    def poll(cls, context):
        return lead(context) is not None

    def execute(self, context):
        for node in targets(context):
            node.rotation_mode = self.order
        return {'FINISHED'}


class MAYAKIT_MT_cb_object(bpy.types.Menu):
    """Maya Channel Box Object menu: the selected objects (joints in pose mode), picking one makes it
    the lead ()"""
    bl_label = "Object"

    def draw(self, context):
        lay = self.layout
        obs = targets(context)
        if not obs:
            chrome.grey(lay, "Nothing selected")
        ld = lead(context)
        for ob in obs[:10]:
            lay.operator(MAYAKIT_OT_cb_make_lead.bl_idname, text=ob.name,
                         icon='LAYER_ACTIVE' if ob == ld else 'BLANK1').name = ob.name


class MAYAKIT_MT_cb_show(bpy.types.Menu):
    """Maya Channel Box Show menu (generateChannelShowMenu, )"""
    bl_label = "Show"

    def draw(self, context):
        lay = self.layout
        lay.operator("maya_kit.cb_show_all", text="All")
        lay.separator()
        for label in ("Assets", "Attribute Type Filters"):
            chrome.grey(lay, label)


# Maya Channel Box menu bar, left to right (Maya-474, channel_box.md:27-30).
MENU_BAR = (("Channels", "MAYAKIT_MT_cb_channels"), ("Edit", "MAYAKIT_MT_cb_edit"),
            ("Object", "MAYAKIT_MT_cb_object"), ("Show", "MAYAKIT_MT_cb_show"))
# Maya's empty Channel Box text (compare/01_layout_empty, three centred lines).
EMPTY_TEXT = ("Select objects in the scene to view,", "edit and set keyframes on channels", "(attributes)")


PLACING_TEXT = ("Placing joints:", "channels are in pose mode")
POSE_HINT = "Joint channels: Ctrl+Tab (pose mode)"


def draw_empty(layout):
    layout.separator(factor=6)
    chrome.wrapped(layout, EMPTY_TEXT)   # empty state, channel_box.md:22-24
    layout.separator(factor=6)


# --- panel ---------------------------------------------------------------------------------------------

_STATE_ICON = {'KEYED': 'DECORATE_KEYFRAME', 'ANIMATED': 'DECORATE_ANIMATE', 'DRIVEN': 'DECORATE_DRIVER'}


def _row_label(row, key, selected):
    sub = row.row(align=True)
    op = sub.operator("maya_kit.cb_select_channel", text=channel_label(key), depress=selected,
                      emboss=selected)
    op.key = key


ROW_SCALE = 0.8


def draw_channel_row(layout, ob, key, value_owner, value_prop, selected, constrained=False):
    row = layout.row(align=True)
    split = row.split(factor=0.5, align=True)
    _row_label(split, key, selected)
    right = split.row(align=True)
    state = channel_state(ob, key)
    right.enabled = not is_locked(ob, key)
    if constrained:
        # Maya draws constrained channels blue (channel_box.md:138-139): a pressed button is the
        # theme's selection blue (wcol_tool inner_sel #5285a6); UILayout has no other colour.
        text = cb_entry.format_value(get_value(ob, key), entry_kind(ob, key), bpy.context.scene)
        right.operator("maya_kit.cb_select_channel", text=text, depress=True).key = key
        row.label(text="", icon='CONSTRAINT')
        return row
    right.alert = state is not None
    right.prop(value_owner, value_prop, text="")
    # Proxy fields get no automatic keyframe colouring: show the lead object's state.
    row.label(text="", icon=_STATE_ICON.get(state, 'BLANK1'))
    return row


def _modifier_props(mod, limit=10):
    """Editable scalar properties of a modifier, Maya INPUTS-style (channel_box.md:46)."""
    skip = {"name", "show_expanded", "show_on_cage", "show_in_editmode", "show_render",
            "use_apply_on_spline", "use_pin_to_last", "is_override_data_editable",
            "persistent_uid", "execution_time", "show_viewport"}
    out = []
    for p in mod.bl_rna.properties:
        ident = p.identifier
        if (ident in skip or p.is_readonly or ident.startswith(("show_", "open_", "is_"))
                or ident.endswith("_panel")):
            continue
        if p.type in {'INT', 'FLOAT', 'BOOLEAN'} and getattr(p, "array_length", 0) == 0:
            out.append(p.identifier)
        if len(out) >= limit:
            break
    return out


SHAPE_PROPS = {
    'CAMERA': ("lens", "clip_start", "clip_end"),
    'LIGHT': ("energy", "color", "shadow_soft_size"),
}


def wanted_rows(ob):
    """(kind, name, mod_type, nth) for every text row of the lead object."""
    out = [("CUSTOM", name, "", 0) for name in custom_keys(ob)]
    data = getattr(ob, "data", None)
    if data is not None:
        for prop in SHAPE_PROPS.get(ob.type, ()):
            rna = data.bl_rna.properties.get(prop)
            if rna is not None and cb_entry.kind_of_rna(rna):
                out.append(("SHAPE", prop, "", 0))
    for mod in _inputs(ob):
        if mod.show_expanded:
            for prop in _modifier_props(mod):
                out.append(("INPUT", prop, mod.type, _nth_of_type(ob, mod)))
    for con in constraints(ob):
        out.append(("CONSTRAINT", "influence", con.type, _nth_constraint(ob, con)))
    return out


def rows_signature(ob):
    if ob is None:
        return ""
    cons = [(c.name, c.type, weight_name(c)) for c in constraints(ob)]
    if is_bone(ob):
        return repr(("BONE", ob.id_data.name, ob.name, custom_keys(ob), cons))
    mods = [(m.name, m.type, m.show_expanded) for m in _inputs(ob)]
    return repr((ob.name, ob.type, custom_keys(ob), mods, cons))


_rows_state = {"busy": False}


def rebuild_rows(context=None):
    """Make ``Scene.maya_kit_cb.rows`` match the lead object (only when it changed)."""
    context = context or bpy.context
    scene = getattr(context, "scene", None)
    cb = getattr(scene, "maya_kit_cb", None) if scene is not None else None
    view_layer = getattr(context, "view_layer", None)
    if cb is None or view_layer is None or _rows_state["busy"]:
        return False
    ob = lead(context)
    sig = rows_signature(ob)
    if cb.rows_sig == sig:
        return False
    _rows_state["busy"] = True
    try:
        cb.rows.clear()
        if ob is not None:
            for kind, name, mod_type, nth in wanted_rows(ob):
                r = cb.rows.add()
                r.kind, r.name, r.mod_type, r.nth = kind, name, mod_type, nth
        cb.rows_sig = sig
    finally:
        _rows_state["busy"] = False
    return True


def row_for(context, ob, kind, name, mod_type="", nth=0):
    """The text row to draw, or None when the rows are stale (then draw the real property)."""
    cb = context.scene.maya_kit_cb
    if cb.rows_sig != rows_signature(ob):
        return None
    for r in cb.rows:
        if r.kind == kind and r.name == name and r.mod_type == mod_type and r.nth == nth:
            return r
    return None


@persistent
def _on_depsgraph(_scene, _depsgraph):
    rebuild_rows()


@persistent
def _on_load(_dummy):
    rebuild_rows()


def _first_rebuild():
    rebuild_rows()
    return None


def _draw_text_row(layout, context, ob, owner, prop, kind, mod_type="", nth=0, label=None):
    """A SHAPES / INPUTS row: label + text field applied to all selected (else the real prop)."""
    label = owner.bl_rna.properties[prop].name if label is None else label
    row = row_for(context, ob, kind, prop, mod_type, nth)
    if row is None:
        layout.prop(owner, prop, text=label)
        return
    split = layout.row(align=True).split(factor=0.5, align=True)
    split.label(text=label)
    split.prop(row, "text", text="")


class MAYAKIT_PT_channel_box(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = CATEGORY
    bl_label = "Channel Box"
    bl_order = 0
    bl_options = {'HIDE_HEADER'}   # Maya: a menu bar, no collapsible panel title (step 50)

    @classmethod
    def poll(cls, context):
        # Hidden while the dock shows the Attribute Editor.
        return getattr(context.window_manager, "maya_kit_dock", 'CHANNEL_BOX') == 'CHANNEL_BOX'

    def draw(self, context):
        layout = self.layout
        from .attribute_editor import draw_dock_switch
        draw_dock_switch(layout, context)
        chrome.menu_bar(layout, MENU_BAR)
        if placing_joints(context):
            layout.separator(factor=2)
            chrome.wrapped(layout, PLACING_TEXT)   # armature edit mode = joint placement (step 55)
            return
        ob = lead(context)
        if ob is None:
            draw_empty(layout)
            return
        cb = context.scene.maya_kit_cb
        sel = set(selected_channels(context))
        head = layout.row(align=True)
        head.prop(ob, "name", text="", emboss=False)   # Maya: the lead's name as plain text
        n = len(targets(context))
        if n > 1:
            head.label(text=f"+{n - 1}")
        if not is_bone(ob) and ob.type == 'ARMATURE' and ob.mode == 'OBJECT':
            hint = layout.row()
            hint.active = False
            hint.label(text=POSE_HINT)
        blue = constrained_keys(ob)

        col = layout.column(align=True)
        # Maya channel rows are 16 px with 11 px text ( metrics,
        # screens/11b_channel_box_crop.png); Blender rows are 20 px at scale 1.0 (step 44).
        col.scale_y = ROW_SCALE
        for key, _label, _path, _idx, kind in MAIN:
            if is_hidden(ob, key):
                continue
            if kind == "ROT" and not has_channel(ob, key):
                continue
            draw_channel_row(col, ob, key, cb, key + "_text", key in sel, key in blue)
        if not has_channel(ob, "rx"):
            col.label(text=f"Rotation mode {ob.rotation_mode}")
            col.prop(ob, "rotation_quaternion" if ob.rotation_mode == 'QUATERNION' else "rotation_axis_angle",
                     text="")
            col.operator(MAYAKIT_OT_cb_rotate_order.bl_idname, text="Rotate Order XYZ").order = 'XYZ'

        for name in custom_keys(ob):
            key = CUSTOM_PREFIX + name
            if not is_hidden(ob, key):
                row = row_for(context, ob, "CUSTOM", name)
                if row is not None:
                    draw_channel_row(col, ob, key, row, "text", key in sel)
                else:
                    draw_channel_row(col, ob, key, ob, f'["{name}"]', key in sel)

        # SHAPES / INPUTS: a section title and indented node names, no boxes (11b_channel_box_crop).
        data = getattr(ob, "data", None)
        if data is not None:
            box = layout.column(align=True)
            box.label(text="SHAPES")
            name = box.row()
            name.separator(factor=1.5)
            name.prop(data, "name", text="", emboss=False)
            for prop in SHAPE_PROPS.get(ob.type, ()):
                if hasattr(data, prop):
                    _draw_text_row(box, context, ob, data, prop, "SHAPE")

        # Smooth Mesh Preview is a shape display attribute in Maya, not an input node (step 15).
        inputs = _inputs(ob)
        cons = constraints(ob)
        if inputs or cons:
            box = layout.column(align=True)
            box.label(text="INPUTS")
            for mod in inputs:
                row = box.row(align=True)
                row.prop(mod, "show_expanded", text="", emboss=False,
                         icon='DISCLOSURE_TRI_DOWN' if mod.show_expanded else 'DISCLOSURE_TRI_RIGHT')
                row.prop(mod, "name", text="", emboss=False)
                row.prop(mod, "show_viewport", text="")
                if mod.show_expanded:
                    sub = box.column(align=True)
                    for prop in _modifier_props(mod):
                        _draw_text_row(sub, context, ob, mod, prop, "INPUT", mod.type,
                                       _nth_of_type(ob, mod))
            for con in cons:
                # Maya constraint node + its target weight (animation.md:42, :126)
                row = box.row(align=True)
                name = row.row()
                name.active = constraint_enabled(con)
                name.separator(factor=1.5)
                name.label(text=constraint_node_name(ob, con))
                if hasattr(con, "enabled"):
                    row.prop(con, "enabled", text="")
                sub = box.column(align=True)
                _draw_text_row(sub, context, ob, con, "influence", "CONSTRAINT", con.type,
                               _nth_constraint(ob, con), label=weight_name(con))


classes = (MAYAKIT_PG_cb_row, MAYAKIT_PG_channel_box, MAYAKIT_OT_cb_virtual_slider, MAYAKIT_OT_cb_select_channel,
           MAYAKIT_OT_cb_deselect_channels, *CHANNEL_OPS, MAYAKIT_OT_cb_show_all,
           MAYAKIT_MT_cb_channels, MAYAKIT_MT_cb_settings, MAYAKIT_OT_cb_make_lead,
           MAYAKIT_OT_cb_rotate_order, MAYAKIT_MT_cb_edit,
           MAYAKIT_MT_cb_object, MAYAKIT_MT_cb_show, MAYAKIT_PT_channel_box)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.maya_kit_cb = bpy.props.PointerProperty(type=MAYAKIT_PG_channel_box)
    bpy.types.WindowManager.maya_kit_cb_selected = StringProperty(
        name="Selected Channels", options={'SKIP_SAVE'})
    bpy.app.handlers.depsgraph_update_post.append(_on_depsgraph)
    bpy.app.handlers.load_post.append(_on_load)
    bpy.app.timers.register(_first_rebuild, first_interval=0.0)
    bpy.types.UI_MT_button_context_menu.prepend(draw_button_menu)


def unregister():
    bpy.types.UI_MT_button_context_menu.remove(draw_button_menu)
    if bpy.app.timers.is_registered(_first_rebuild):
        bpy.app.timers.unregister(_first_rebuild)
    bpy.app.handlers.load_post.remove(_on_load)
    bpy.app.handlers.depsgraph_update_post.remove(_on_depsgraph)
    del bpy.types.WindowManager.maya_kit_cb_selected
    del bpy.types.Scene.maya_kit_cb
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
