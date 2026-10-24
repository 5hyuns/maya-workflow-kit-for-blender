# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya Set Driven Key (Key > Set Driven Key > Set... / Go to Previous / Go to Next).

Maya's result is an animCurveUU from the driver attribute to the driven one
(research/maya/workflows/rigging.md §1.5, §4-4). Blender equivalent: a driver on the driven
channel (one variable ``sdk`` reading the driver channel, type AVERAGE = the variable) whose
F-curve has keys (driver value, driven value) — the same curve shape (docs/steps/step_62.md 「계획」 1).
Values are raw RNA values (radians, metres), so the mapping is the one the user posed.

Blender writes a driver's result back over a typed value at the next update (measured, step 62),
so while the Set Driven Key window is open, a Channel Box edit of a channel driven by a kit SDK
driver mutes that driver until Key (which records the pose) or Close (which drops it).
The window state lives on the WindowManager like a Maya window (not undoable, not saved).
"""

import bpy
from bpy.props import BoolProperty, CollectionProperty, EnumProperty, IntProperty, PointerProperty, StringProperty

from .. import results
from ..ui import channel_box as cb

VAR = "sdk"          # the kit's driver variable name: marks a Set Driven Key driver


# --- nodes ---------------------------------------------------------------------------------------

def node_of(ob, bone):
    if ob is None:
        return None
    if bone:
        return ob.pose.bones.get(bone) if ob.pose else None
    return ob


def node_ref(node):
    """(object, bone name) of an object or pose bone."""
    return (node.id_data, node.name) if cb.is_bone(node) else (node, "")


def node_label(node):
    return node.name


def channels(node):
    """The node's Channel Box channels (Maya SDK lists the keyable attributes)."""
    keys = cb._visible_channels(node)
    return [k for k in keys if not (k == "v" and cb.is_bone(node))]


def _rna_path(key):
    """(data path, index) of the raw RNA value of a channel (Visibility = hide_viewport)."""
    path, idx, _kind = cb.channel_path(key)
    return path, idx


def raw_value(node, key):
    path, idx = _rna_path(key)
    if path.startswith('["'):
        return float(node[path[2:-2]])
    value = getattr(node, path)
    return float(value[idx] if idx >= 0 else value)


def set_raw_value(node, key, value):
    path, idx = _rna_path(key)
    if path.startswith('["'):
        name = path[2:-2]
        node[name] = type(node[name])(value)
        node.id_data.update_tag()
    elif idx >= 0:
        getattr(node, path)[idx] = value
    else:
        setattr(node, path, type(getattr(node, path))(value))


def _var_path(node, key):
    """Driver variable path of a channel on the node's ID (pose bones: on the armature object)."""
    path, idx = _rna_path(key)
    full = node.path_from_id(path) if cb.is_bone(node) else path
    return full + (f"[{idx}]" if idx >= 0 else "")


def sdk_fcurve(node, key):
    """The kit SDK driver F-curve of a driven channel, or None."""
    fc = cb.driver(node, key)
    if fc is None or not any(v.name == VAR for v in fc.driver.variables):
        return None
    return fc


LENGTH_KEYS = ("tx", "ty", "tz")


def curve_scale(driver_key):
    """Curve x per raw driver value. Blender merges F-curve keys less than 0.01 apart in x (measured, step 97),
    and a length driver in the cm template moves 0.01 BU per cm: those curves keep x in display units."""
    from . import units
    k = units.maya_unit()
    return 1.0 / k if driver_key in LENGTH_KEYS and k < 1.0 else 1.0


def fcurve_scale(fc):
    """The x scale a kit SDK curve was made with (``sdk*<s>`` expression; plain average = 1)."""
    d = fc.driver
    if d.type == 'SCRIPTED' and d.expression.startswith(VAR + "*"):
        try:
            return float(d.expression[len(VAR) + 1:])
        except ValueError:
            return 1.0
    return 1.0


def ensure_driver(driven, key, driver_node, driver_key):
    """The kit SDK driver of ``driven``.``key`` reading ``driver_node``.``driver_key``."""
    fc = sdk_fcurve(driven, key)
    if fc is None:
        path, idx = _rna_path(key)
        full = cb.full_path(driven, path)
        ob = driven.id_data
        old = cb.driver(driven, key)
        if old is not None:   # another driver on this channel: Maya replaces the connection
            ob.animation_data.drivers.remove(old)
        fc = ob.driver_add(full, idx) if idx >= 0 else ob.driver_add(full)
        # A new driver curve maps 1:1 — a Generator modifier in 4.5, two keys (0, 0) (1, 1) in 5.x (measured,
        # step 118): SDK curves start empty either way.
        for mod in list(fc.modifiers):
            fc.modifiers.remove(mod)
        while len(fc.keyframe_points):
            fc.keyframe_points.remove(fc.keyframe_points[0], fast=True)
        fc.extrapolation = 'CONSTANT'   # Maya infinity Constant (5.x driver curves start LINEAR)
        scale = curve_scale(driver_key)
        if scale != 1.0:   # a simple expression: no Python auto-run needed
            fc.driver.type = 'SCRIPTED'
            fc.driver.expression = f"{VAR}*{scale:g}"
        else:
            fc.driver.type = 'AVERAGE'
        var = fc.driver.variables.new()
        var.name = VAR
        var.type = 'SINGLE_PROP'
    var = next(v for v in fc.driver.variables if v.name == VAR)
    target = var.targets[0]
    target.id_type = 'OBJECT'
    target.id = driver_node.id_data
    target.data_path = _var_path(driver_node, driver_key)
    return fc


def set_key(driven, key, driver_node, driver_key):
    """One Set Driven Key key: (driver value, driven value) on the driven channel's curve."""
    y = raw_value(driven, key)          # held by a muted driver while posing, else the driven value
    fc = ensure_driver(driven, key, driver_node, driver_key)
    x = raw_value(driver_node, driver_key) * fcurve_scale(fc)
    for kp in fc.keyframe_points:
        if abs(kp.co[0] - x) < 1e-6:
            kp.co[1] = y
            break
    else:
        kp = fc.keyframe_points.insert(x, y, options={'FAST'})
    for kp in fc.keyframe_points:
        kp.interpolation = 'BEZIER'
        kp.handle_left_type = kp.handle_right_type = 'AUTO_CLAMPED'
    fc.update()
    fc.mute = False
    fc.driver.is_valid = True
    return fc


def key_xs(fcs):
    return sorted({round(kp.co[0], 6) for fc in fcs for kp in fc.keyframe_points})


def step_to(xs, current, direction):
    """The key x after (NEXT) or before (PREVIOUS) ``current``, or None."""
    if direction == 'NEXT':
        return next((x for x in xs if x > current + 1e-6), None)
    return next((x for x in reversed(xs) if x < current - 1e-6), None)


def all_sdk_curves():
    for ob in bpy.data.objects:
        ad = ob.animation_data
        if ad is None:
            continue
        for fc in ad.drivers:
            if any(v.name == VAR for v in fc.driver.variables):
                yield fc


def release_all():
    """Unmute every kit SDK driver muted for posing; returns how many."""
    n = 0
    for fc in all_sdk_curves():
        if fc.mute:
            fc.mute = False
            n += 1
    return n


# --- window state ----------------------------------------------------------------------------------

class ALLSET_PG_sdk_node(bpy.types.PropertyGroup):
    object: PointerProperty(type=bpy.types.Object)
    bone: StringProperty()


class ALLSET_PG_sdk_item(bpy.types.PropertyGroup):
    key: StringProperty()      # channel key (channel_box)
    label: StringProperty()


class ALLSET_PG_sdk(bpy.types.PropertyGroup):
    open: BoolProperty(name="Set Driven Key")
    driver: PointerProperty(type=ALLSET_PG_sdk_node)
    driver_attr: StringProperty()
    driven: CollectionProperty(type=ALLSET_PG_sdk_node)
    driven_index: IntProperty()
    driven_attrs: StringProperty()          # comma-separated channel keys
    # rows of the scrolling attribute lists (UIList needs collections); rebuilt by refresh_items()
    driver_items: CollectionProperty(type=ALLSET_PG_sdk_item)
    driver_items_index: IntProperty()
    driven_items: CollectionProperty(type=ALLSET_PG_sdk_item)
    driven_items_index: IntProperty()


def state(context=None):
    return (context or bpy.context).window_manager.allset_sdk


def driver_node(st):
    return node_of(st.driver.object, st.driver.bone)


def driven_nodes(st):
    return [n for n in (node_of(i.object, i.bone) for i in st.driven) if n is not None]


def driven_keys(st):
    return [k for k in st.driven_attrs.split(",") if k]


def _fill(items, node, selected):
    items.clear()
    first = -1
    for i, key in enumerate(channels(node) if node is not None else ()):
        item = items.add()
        item.key, item.label = key, cb.channel_label(key)
        if first < 0 and key in selected:
            first = i
    return max(first, 0)


def refresh_items(st):
    """Rebuild the attribute rows; the lists scroll to the first selected attribute."""
    st.driver_items_index = _fill(st.driver_items, driver_node(st), {st.driver_attr})
    nodes = driven_nodes(st)
    node = nodes[min(st.driven_index, len(nodes) - 1)] if nodes else None
    st.driven_items_index = _fill(st.driven_items, node, set(driven_keys(st)))


def hold_driven(node, key):
    """channel_box.set_value hook: keep a typed value on a channel the SDK window drives."""
    try:
        st = state()
    except AttributeError:
        return
    if not st.open:
        return
    fc = sdk_fcurve(node, key)
    if fc is not None:
        fc.mute = True


def _redraw(context):
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()


# --- operators -----------------------------------------------------------------------------------

class ALLSET_OT_sdk_window(bpy.types.Operator):
    """Maya Set Driven Key window: load a driver and driven channels, pose, Key (Key > Set Driven Key > Set...)"""
    bl_idname = "allset.sdk_window"
    bl_label = "Set Driven Key"

    def execute(self, context):
        st = state(context)
        st.open = True
        if hasattr(bpy.ops.allset, "dock_show"):
            try:   # the window is drawn under the Channel Box in the sidebar dock
                bpy.ops.allset.dock_show(dock='CHANNEL_BOX')
            except RuntimeError:
                context.window_manager.allset_dock = 'CHANNEL_BOX'
        _redraw(context)
        return {'FINISHED'}


class ALLSET_OT_sdk_load(bpy.types.Operator):
    """Load the lead (Driver) or every selected object / joint (Driven); the channels selected in the
    Channel Box become the selected attributes"""
    bl_idname = "allset.sdk_load"
    bl_label = "Load"

    which: EnumProperty(items=(('DRIVER', "Driver", ""), ('DRIVEN', "Driven", "")), options={'SKIP_SAVE'})

    def execute(self, context):
        st = state(context)
        sel = cb.selected_channels(context)
        if self.which == 'DRIVER':
            node = cb.lead(context)
            if node is None:
                self.report({'WARNING'}, "Select the driver object (or joint) first")
                return {'CANCELLED'}
            st.driver.object, st.driver.bone = node_ref(node)
            avail = channels(node)
            st.driver_attr = next((k for k in sel if k in avail), "")
        else:
            nodes = cb.targets(context)
            if not nodes:
                self.report({'WARNING'}, "Select the driven objects (or joints) first")
                return {'CANCELLED'}
            st.driven.clear()
            for node in nodes:
                item = st.driven.add()
                item.object, item.bone = node_ref(node)
            st.driven_index = 0
            avail = set(channels(nodes[0]))
            st.driven_attrs = ",".join(k for k in sel if k in avail)
        refresh_items(st)
        _redraw(context)
        return {'FINISHED'}


class ALLSET_OT_sdk_pick(bpy.types.Operator):
    """Pick an attribute (Driven: Ctrl adds / removes) or a driven node in the Set Driven Key lists"""
    bl_idname = "allset.sdk_pick"
    bl_label = "Pick"
    bl_options = {'INTERNAL'}

    which: EnumProperty(items=(('DRIVER', "Driver", ""), ('DRIVEN', "Driven", ""), ('NODE', "Node", "")),
                        options={'SKIP_SAVE'})
    key: StringProperty(options={'SKIP_SAVE'})
    index: IntProperty(options={'SKIP_SAVE'})
    toggle: BoolProperty(options={'SKIP_SAVE'})

    def invoke(self, context, event):
        self.toggle = self.toggle or event.ctrl or event.shift
        return self.execute(context)

    def execute(self, context):
        st = state(context)
        if self.which == 'DRIVER':
            st.driver_attr = self.key
        elif self.which == 'NODE':
            st.driven_index = self.index
            refresh_items(st)
        else:
            keys = driven_keys(st)
            if self.toggle:
                keys = [k for k in keys if k != self.key] if self.key in keys else keys + [self.key]
            else:
                keys = [self.key]
            st.driven_attrs = ",".join(keys)
        _redraw(context)
        return {'FINISHED'}


class ALLSET_OT_sdk_key(bpy.types.Operator):
    """Key: record (driver value, driven value) for every loaded driven attribute"""
    bl_idname = "allset.sdk_key"
    bl_label = "Key"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        st = state(context)
        return driver_node(st) is not None and st.driver_attr and driven_nodes(st) and driven_keys(st)

    def execute(self, context):
        st = state(context)
        drv = driver_node(st)
        count = 0
        for node in driven_nodes(st):
            if node == drv:
                continue
            avail = set(channels(node))
            for key in driven_keys(st):
                if key in avail:
                    set_key(node, key, drv, st.driver_attr)
                    count += 1
        context.view_layer.update()
        results.result(self, f"Set Driven Key: {count} key(s) at {cb.channel_label(st.driver_attr)} = "
                              f"{raw_value(drv, st.driver_attr):g}")
        return {'FINISHED'}


class ALLSET_OT_sdk_go(bpy.types.Operator):
    """Set the driver to the previous / next driven key (Key > Set Driven Key > Go to Previous / Next)"""
    bl_idname = "allset.sdk_go"
    bl_label = "Go to Driven Key"
    bl_options = {'REGISTER', 'UNDO'}

    direction: EnumProperty(items=(('PREVIOUS', "Previous", ""), ('NEXT', "Next", "")), options={'SKIP_SAVE'})

    def execute(self, context):
        st = state(context)
        drv = driver_node(st)
        fcs = [fc for node in driven_nodes(st) for key in driven_keys(st)
               if (fc := sdk_fcurve(node, key)) is not None] if drv is not None else []
        if not fcs:
            self.report({'WARNING'}, "Load a driver and driven attributes with keys (Set Driven Key window)")
            return {'CANCELLED'}
        scale = fcurve_scale(fcs[0])
        x = step_to(key_xs(fcs), raw_value(drv, st.driver_attr) * scale, self.direction)
        if x is None:
            results.result(self, "No more driven keys")
            return {'CANCELLED'}
        release_all()
        set_raw_value(drv, st.driver_attr, x / scale)
        context.view_layer.update()
        return {'FINISHED'}


class ALLSET_OT_sdk_close(bpy.types.Operator):
    """Close the Set Driven Key window (driven values posed but not keyed go back to the curve)"""
    bl_idname = "allset.sdk_close"
    bl_label = "Close"

    def execute(self, context):
        state(context).open = False
        release_all()
        context.view_layer.update()
        _redraw(context)
        return {'FINISHED'}


@bpy.app.handlers.persistent
def _on_load(_dummy):
    release_all()


classes = (ALLSET_PG_sdk_node, ALLSET_PG_sdk_item, ALLSET_PG_sdk, ALLSET_OT_sdk_window, ALLSET_OT_sdk_load, ALLSET_OT_sdk_pick,
           ALLSET_OT_sdk_key, ALLSET_OT_sdk_go, ALLSET_OT_sdk_close)


def register_props():
    bpy.types.WindowManager.allset_sdk = PointerProperty(type=ALLSET_PG_sdk, options={'SKIP_SAVE'})
    cb.WRITE_HOOKS.append(hold_driven)
    bpy.app.handlers.load_post.append(_on_load)


def unregister_props():
    bpy.app.handlers.load_post.remove(_on_load)
    if hold_driven in cb.WRITE_HOOKS:
        cb.WRITE_HOOKS.remove(hold_driven)
    del bpy.types.WindowManager.allset_sdk
