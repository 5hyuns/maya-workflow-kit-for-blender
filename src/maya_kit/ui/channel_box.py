# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya Channel Box in the 3D View sidebar (category "Channel Box").

research/maya/channel_box.md; design: docs/steps/step_6.md 「계획」.
- Translate/Rotate/Scale/Visibility rows are getter/setter proxies on
  ``Scene.maya_kit_cb``: they read the lead (active) object and write every
  selected object, like Maya (channel_box.md:52-55).
- Channel names are buttons that select channels; selected channels drive
  the MMB virtual slider in the viewport (channel_box.md §2.3) and the
  Channels menu (§2.4).
- Custom properties, SHAPES (object data) and INPUTS (modifiers =
  construction history, §4) draw the lead object's real properties.
"""

import math

import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, StringProperty

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

# MMB slider: value change per pixel at speed Medium (step_6.md 「계획」 [I]).
SLIDER_STEP = {"LOC": 0.01, "ROT": math.radians(0.5), "SCALE": 0.01, "CUSTOM": 0.01}
SPEEDS = (("SLOWEST", "Slowest", "x0.01", 0.01), ("SLOW", "Slow", "x0.1", 0.1),
          ("MEDIUM", "Medium", "x1", 1.0), ("FAST", "Fast", "x10", 10.0))
SPEED_FACTOR = {s[0]: s[3] for s in SPEEDS}


# --- objects, channels --------------------------------------------------------------

def lead(context=None):
    return (context or bpy.context).active_object


def targets(context=None):
    """Lead + selected objects (lead first), like Maya's selection list."""
    context = context or bpy.context
    obs = list(context.selected_objects)
    ld = lead(context)
    if ld is not None:
        obs = [ld] + [o for o in obs if o != ld]
    return obs


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
        return not ob.hide_viewport
    return getattr(ob, path)[idx]


def set_value(ob, key, value):
    path, idx, kind = channel_path(key)
    if kind == "CUSTOM":
        ob[key[len(CUSTOM_PREFIX):]] = type(ob[key[len(CUSTOM_PREFIX):]])(value)
    elif kind == "VIS":
        ob.hide_viewport = not value
    else:
        getattr(ob, path)[idx] = value


def keyframe(ob, key, keytype='KEYFRAME'):
    path, idx, kind = channel_path(key)
    return ob.keyframe_insert(path, index=idx, keytype=keytype)


# --- animation state ---------------------------------------------------------------------

def _fcurves(ob):
    ad = ob.animation_data
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
    return fcs.find(path, index=max(idx, 0))


def driver(ob, key):
    ad = ob.animation_data
    if ad is None:
        return None
    path, idx, _kind = channel_path(key)
    return ad.drivers.find(path, index=max(idx, 0))


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
        if context.mode != 'OBJECT':
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
        ob.animation_data.drivers.remove(dr)
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


class MAYAKIT_MT_cb_settings(bpy.types.Menu):
    bl_label = "Settings"

    def draw(self, context):
        from .. import preferences
        prefs = preferences.get(context)
        lay = self.layout
        lay.label(text="Virtual slider speed")
        lay.prop(prefs, "cb_speed", expand=True)
        lay.prop(prefs, "cb_hyperbolic")


# --- panel ---------------------------------------------------------------------------------------------

_STATE_ICON = {'KEYED': 'DECORATE_KEYFRAME', 'ANIMATED': 'DECORATE_ANIMATE', 'DRIVEN': 'DECORATE_DRIVER'}


def _row_label(row, key, selected):
    sub = row.row(align=True)
    op = sub.operator("maya_kit.cb_select_channel", text=channel_label(key), depress=selected,
                      emboss=selected)
    op.key = key


def draw_channel_row(layout, ob, key, value_owner, value_prop, selected):
    row = layout.row(align=True)
    split = row.split(factor=0.5, align=True)
    _row_label(split, key, selected)
    right = split.row(align=True)
    state = channel_state(ob, key)
    right.alert = state is not None
    right.enabled = not is_locked(ob, key)
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


class MAYAKIT_PT_channel_box(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = CATEGORY
    bl_label = "Channel Box"
    bl_order = 0

    @classmethod
    def poll(cls, context):
        # Hidden while the dock shows the Attribute Editor (docs/steps/step_11.md 「계획」 1).
        return getattr(context.window_manager, "maya_kit_dock", 'CHANNEL_BOX') == 'CHANNEL_BOX'

    def draw_header_preset(self, context):
        row = self.layout.row(align=True)
        row.menu("MAYAKIT_MT_cb_channels", text="Channels")
        row.menu("MAYAKIT_MT_cb_settings", text="", icon='PREFERENCES')

    def draw(self, context):
        layout = self.layout
        ob = lead(context)
        if ob is None:
            layout.label(text="make a selection")  # empty state, channel_box.md:22-24
            return
        cb = context.scene.maya_kit_cb
        sel = set(selected_channels(context))
        head = layout.row(align=True)
        head.prop(ob, "name", text="")
        n = len(context.selected_objects)
        if n > 1:
            head.label(text=f"+{n - 1}")

        col = layout.column(align=True)
        for key, _label, _path, _idx, kind in MAIN:
            if is_hidden(ob, key):
                continue
            if kind == "ROT" and not has_channel(ob, key):
                continue
            draw_channel_row(col, ob, key, cb, key, key in sel)
        if not has_channel(ob, "rx"):
            col.label(text=f"Rotation mode {ob.rotation_mode}")
            col.prop(ob, "rotation_quaternion" if ob.rotation_mode == 'QUATERNION' else "rotation_axis_angle",
                     text="")
        for name in custom_keys(ob):
            key = CUSTOM_PREFIX + name
            if not is_hidden(ob, key):
                draw_channel_row(col, ob, key, ob, f'["{name}"]', key in sel)

        data = ob.data
        if data is not None:
            box = layout.box()
            box.label(text="SHAPES")
            box.prop(data, "name", text="", icon='OBJECT_DATA')
            for prop in SHAPE_PROPS.get(ob.type, ()):
                if hasattr(data, prop):
                    box.prop(data, prop)

        if len(ob.modifiers):
            box = layout.box()
            box.label(text="INPUTS")
            for mod in ob.modifiers:
                row = box.row(align=True)
                row.prop(mod, "show_expanded", text="", emboss=False,
                         icon='DISCLOSURE_TRI_DOWN' if mod.show_expanded else 'DISCLOSURE_TRI_RIGHT')
                row.prop(mod, "name", text="")
                row.prop(mod, "show_viewport", text="")
                if mod.show_expanded:
                    sub = box.column(align=True)
                    for prop in _modifier_props(mod):
                        sub.prop(mod, prop)


classes = (MAYAKIT_PG_channel_box, MAYAKIT_OT_cb_virtual_slider, MAYAKIT_OT_cb_select_channel,
           MAYAKIT_OT_cb_deselect_channels, *CHANNEL_OPS, MAYAKIT_OT_cb_show_all,
           MAYAKIT_MT_cb_channels, MAYAKIT_MT_cb_settings, MAYAKIT_PT_channel_box)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.maya_kit_cb = bpy.props.PointerProperty(type=MAYAKIT_PG_channel_box)
    bpy.types.WindowManager.maya_kit_cb_selected = StringProperty(
        name="Selected Channels", options={'SKIP_SAVE'})


def unregister():
    del bpy.types.WindowManager.maya_kit_cb_selected
    del bpy.types.Scene.maya_kit_cb
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
