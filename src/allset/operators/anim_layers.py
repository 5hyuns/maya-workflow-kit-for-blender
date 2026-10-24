# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya animation layers on Blender NLA tracks (docs/steps/step_180.md 「계획」).

Maya 2022 (mayapy, research/maya/re/anim_layers_180.md / .json): BaseAnimation = the plain anim curves; an Additive
layer adds weight x its curve (rotations Euler component-wise, scale multiplies: below x layer^weight), an Override
layer replaces ((1 - w) below + w layer); mute drops a layer, solo keeps BaseAnimation + the soloed layers; a key set
on the selected layer is the curve value that makes the result the displayed value.

Blender 4.5 NLA gives the same numbers (probe, step_180.md): BaseAnimation = a REPLACE strip on the bottom track,
Additive = COMBINE (location / Euler add, scale multiplies with influence as exponent), Override = REPLACE, weight =
the strip influence, mute = track mute; strips span a fixed wide range with 1:1 time so every key is evaluated.
Blender's tweak mode evaluates only the tracks below the tweaked one (no Python switch for the upper stack), so keys
are not set through tweak mode: ``key()`` solves the layer value from the composition rule itself.

Layers are scene-wide (``Scene.allset_anim_layers``, first entry BaseAnimation) like Maya's animLayer nodes; every
member object has one NLA track per layer, named like the layer, playing an action ``<layer>_<object>`` marked with
the ID property ``allset_anim_layer``.
"""

import bpy
from bpy.props import BoolProperty, CollectionProperty, FloatProperty, IntProperty, StringProperty

from .. import compat

BASE = "BaseAnimation"
MARK = "allset_anim_layer"
WIDE = (-1000.0, 1000.0)          # strip / action range: keys outside it are not evaluated (delegated)
SCALE_PATHS = {"scale", "delta_scale"}


# --- scene model -----------------------------------------------------------------------------------

def layers(scene):
    return scene.allset_anim_layers


def ensure_list(scene):
    """The layer list with BaseAnimation as first entry."""
    ls = layers(scene)
    if not len(ls) or ls[0].name != BASE:
        e = ls.add()
        e.name = BASE
        ls.move(len(ls) - 1, 0)
    return ls


def selected(scene):
    ls = layers(scene)
    i = scene.allset_anim_layer_index
    return ls[i] if 0 <= i < len(ls) else (ls[0] if len(ls) else None)


def unique_name(scene, base="AnimLayer"):
    names = {e.name for e in layers(scene)}
    n = 1
    while f"{base}{n}" in names:
        n += 1
    return f"{base}{n}"


# --- per object tracks -------------------------------------------------------------------------------

def tracks(ob):
    ad = ob.animation_data
    if ad is None:
        return {}
    return {tr.name: tr for tr in ad.nla_tracks if tr.strips and tr.strips[0].action is not None
            and tr.strips[0].action.get(MARK) == tr.name}


def has_layers(ob):
    return bool(tracks(ob))


def _new_action(ob, layer):
    """An empty action with a slot for ``ob`` (Blender 4.4+ makes the slot when the action is assigned)."""
    act = bpy.data.actions.new(f"{layer}_{ob.name}")
    act[MARK] = layer
    ob.animation_data_create()
    slots = getattr(act, "slots", None)
    if slots is not None:       # 4.4+: an empty action gets no slot by being assigned; make it (the strip needs it)
        slot = slots.new(id_type='OBJECT', name=ob.name)
        act["allset_slot"] = slot.identifier
    return act


def _slot(act):
    ident = act.get("allset_slot")
    slots = getattr(act, "slots", None)
    if slots is None:
        return None
    if ident and ident in slots:
        return slots[ident]
    return slots[0] if len(slots) else None


def _strip(tr):
    return tr.strips[0]


def _add_track(ob, layer, act):
    ad = ob.animation_data_create()
    tr = ad.nla_tracks.new()
    tr.name = layer
    st = tr.strips.new(layer, int(WIDE[0]), act)
    sl = _slot(act)
    if sl is not None and hasattr(st, "action_slot"):
        st.action_slot = sl
    st.action_frame_start, st.action_frame_end = WIDE
    st.frame_start, st.frame_end = WIDE
    st.use_auto_blend = False
    st.blend_in = st.blend_out = 0.0
    st.extrapolation = 'HOLD' if layer == BASE else 'HOLD_FORWARD'
    return tr


def ensure_base(ob):
    """Move the object's own animation (its active action) onto the BaseAnimation track."""
    if BASE in tracks(ob):
        return tracks(ob)[BASE]
    ad = ob.animation_data_create()
    act = ad.action
    if act is not None:
        slot = getattr(ad, "action_slot", None)
        act[MARK] = BASE
        if slot is not None:
            act["allset_slot"] = slot.identifier
        ad.action = None
    else:
        act = _new_action(ob, BASE)
    tr = _add_track(ob, BASE, act)
    order_tracks(ob, [e.name for e in layers(bpy.context.scene)] or [BASE])
    return tr


def add_object(scene, ob, layer):
    """Make ``ob`` a member of ``layer`` (Maya Add Selected Objects / Create Layer from Selected)."""
    ensure_list(scene)
    ensure_base(ob)
    if layer != BASE and layer not in tracks(ob):
        _add_track(ob, layer, _new_action(ob, layer))
    order_tracks(ob, [e.name for e in layers(scene)])
    sync(scene)


def remove_object(scene, ob, layer):
    tr = tracks(ob).get(layer)
    if tr is None or layer == BASE:
        return
    act = _strip(tr).action
    ob.animation_data.nla_tracks.remove(tr)
    if act is not None and act.users == 0:
        bpy.data.actions.remove(act)


def order_tracks(ob, names):
    """NLA tracks in the layer list order, bottom first (Blender can only move tracks by recreating them, so only the
    kit tracks' strip settings are swapped into place: track i gets layer names[i])."""
    have = tracks(ob)
    want = [n for n in names if n in have]
    ad = ob.animation_data
    kit = [tr for tr in ad.nla_tracks if tr.name in have]
    if [tr.name for tr in kit] == want:
        return
    data = {n: (_strip(have[n]).action, have[n].mute) for n in want}
    for tr in kit:
        ad.nla_tracks.remove(tr)
    for n in want:
        tr = _add_track(ob, n, data[n][0])
        tr.mute = data[n][1]


def members(scene, layer):
    return [ob for ob in scene.objects if layer in tracks(ob)]


def sync(scene):
    """Write the layer list onto every member object's tracks (Maya weight / mute / solo / mode)."""
    ls = layers(scene)
    if not len(ls):
        return
    solo = {e.name for e in ls if e.solo and e.name != BASE}
    info = {e.name: e for e in ls}
    for ob in scene.objects:
        have = tracks(ob)
        if not have:
            continue
        for name, tr in have.items():
            e = info.get(name)
            if e is None:
                continue
            st = _strip(tr)
            tr.mute = e.mute or (bool(solo) and name != BASE and name not in solo)
            st.blend_type = 'REPLACE' if name == BASE or e.override else 'COMBINE'
            st.extrapolation = 'HOLD' if name == BASE else 'HOLD_FORWARD'
            _set_influence(st, 1.0 if name == BASE else e.weight)
            tr.lock = e.lock
        ob.update_tag(refresh={'TIME'})


def _set_influence(st, w):
    if abs(w - 1.0) < 1e-9 and not st.use_animated_influence:
        return
    if not st.use_animated_influence:
        st.use_animated_influence = True      # Blender keys influence when it turns this on: drop that key
        fc = st.fcurves.find("influence")
        if fc is not None:
            while fc.keyframe_points:
                fc.keyframe_points.remove(fc.keyframe_points[0])
    st.influence = w


# --- evaluation and keys -------------------------------------------------------------------------------

def _fcurve(act, path, index):
    for fc in compat.action_fcurves(act, _slot(act)):
        if fc.data_path == path and fc.array_index == index:
            return fc
    return None


def compose(steps, start):
    """Fold the layer steps over ``start``: steps = [(mode, weight, value)] bottom first, mode REPLACE / ADD /
    MUL (scale COMBINE). Returns the result."""
    acc = start
    for mode, w, x in steps:
        if mode == 'REPLACE':
            acc = (1.0 - w) * acc + w * x
        elif mode == 'MUL':
            acc = acc * (x ** w if x > 0 else 0.0)
        else:
            acc = acc + w * x
    return acc


def _steps(ob, path, index, frame, scene):
    """[(layer name, mode, weight, value or None)] of the object's evaluated layers for one channel, bottom first."""
    info = {e.name: e for e in layers(scene)}
    out = []
    ad = ob.animation_data
    for tr in ad.nla_tracks:
        if tr.name not in info or tr.mute:
            continue
        st = _strip(tr)
        fc = _fcurve(st.action, path, index)
        w = st.influence if st.use_animated_influence else 1.0
        if st.blend_type == 'REPLACE':
            mode = 'REPLACE'
        elif st.blend_type == 'COMBINE' and path in SCALE_PATHS:
            mode = 'MUL'
        else:
            mode = 'ADD'
        out.append((tr.name, mode, w, fc.evaluate(frame) if fc is not None else None))
    return out


def solve(steps, target, layer, start=0.0):
    """The value ``layer``'s curve needs so the folded result is ``target`` (Maya: a key on the selected layer makes
    the displayed value the result). ``steps`` as from ``_steps``; missing values = no curve yet (identity)."""
    def ident(mode):
        return 1.0 if mode == 'MUL' else 0.0
    k = next(i for i, s in enumerate(steps) if s[0] == layer)
    below = compose([(m, w, x) for _n, m, w, x in steps[:k] if x is not None], start)
    upper = [(m, w, x) for _n, m, w, x in steps[k + 1:] if x is not None]
    # the upper layers are affine in their input: result = a * acc + b (or a * acc for MUL steps)
    a, b = 1.0, 0.0
    for m, w, x in upper:
        if m == 'REPLACE':
            a, b = a * (1.0 - w), b * (1.0 - w) + w * x
        elif m == 'MUL':
            f = x ** w if x > 0 else 0.0
            a, b = a * f, b * f
        else:
            b = b + w * x
    _n, mode, w, cur = steps[k]
    if abs(a) < 1e-12 or w < 1e-12:
        return cur if cur is not None else ident(mode)        # an upper Override hides this layer: keep it
    acc = (target - b) / a
    if mode == 'REPLACE':
        return (acc - (1.0 - w) * below) / w
    if mode == 'MUL':
        return (acc / below) ** (1.0 / w) if below and acc / below > 0 else 1.0
    return (acc - below) / w


def target_layer(scene, ob):
    """The layer a key on ``ob`` goes to: the selected layer when ``ob`` is in it, else BaseAnimation."""
    e = selected(scene)
    name = e.name if e is not None else BASE
    return name if name in tracks(ob) else BASE


def key(ob, path, index, frame=None, value=None, scene=None):
    """Key channel (``path``, ``index``) of ``ob`` on the selected layer so the result is ``value`` (default: the
    displayed value). False when the layer is locked."""
    scene = scene or bpy.context.scene
    frame = scene.frame_current if frame is None else frame
    if value is None:
        v = ob.path_resolve(path)
        value = float(v[index] if index >= 0 else v)
    index = max(index, 0)
    layer = target_layer(scene, ob)
    info = {e.name: e for e in layers(scene)}
    if layer in info and info[layer].lock:
        return False
    steps = _steps(ob, path, index, frame, scene)
    if not any(s[0] == layer for s in steps):          # the target layer is muted: Maya keys it anyway
        tr = tracks(ob)[layer]
        steps = [s for s in steps if s[0] != layer]
        st = _strip(tr)
        steps.append((layer, 'REPLACE' if st.blend_type == 'REPLACE' else
                      ('MUL' if path in SCALE_PATHS else 'ADD'), 1.0, None))
    # NLA starts a channel no lower strip animates from the property's default (scale 1, else 0)
    start = value if layer == BASE else (1.0 if path in SCALE_PATHS else 0.0)
    x = solve(steps, value, layer, start)
    act = _strip(tracks(ob)[layer]).action
    fc = _fcurve(act, path, index)
    if fc is None:
        fc = _new_fcurve(ob, act, path, index)
    if fc is None:
        return False
    fc.keyframe_points.insert(frame, x)
    fc.update()
    ob.update_tag(refresh={'TIME'})
    return True


def _new_fcurve(ob, act, path, index):
    ad = ob.animation_data
    keep, keep_slot = ad.action, getattr(ad, "action_slot", None)
    try:
        ad.action = act
        sl = _slot(act)
        if sl is not None and hasattr(ad, "action_slot"):
            ad.action_slot = sl
        if hasattr(act, "fcurve_ensure_for_datablock"):
            return act.fcurve_ensure_for_datablock(ob, path, index=index)
        return act.fcurves.new(path, index=index)
    finally:
        ad.action = keep
        if keep is not None and keep_slot is not None:
            ad.action_slot = keep_slot


# --- operators -------------------------------------------------------------------------------------

def _sync_update(self, context):
    sync(context.scene)


class ALLSET_PG_anim_layer(bpy.types.PropertyGroup):
    weight: FloatProperty(name="Weight", default=1.0, min=0.0, max=1.0, update=_sync_update,
                          description="Maya layer weight (NLA strip influence)")
    mute: BoolProperty(name="Mute", update=_sync_update, description="Mute layer")
    solo: BoolProperty(name="Solo", update=_sync_update, description="Solo layer (BaseAnimation stays)")
    lock: BoolProperty(name="Lock", update=_sync_update, description="Lock layer: no keys")
    override: BoolProperty(name="Override", update=_sync_update,
                           description="Override the layers below (else Additive)")


def _layer_objects(context):
    return [ob for ob in context.selected_objects if ob.type in {'MESH', 'CURVE', 'SURFACE', 'EMPTY', 'ARMATURE',
                                                               'LIGHT', 'CAMERA', 'LATTICE', 'META', 'FONT'}]


class ALLSET_OT_anim_layer_create(bpy.types.Operator):
    """Create an animation layer, empty or with the selected objects (Maya Create Empty Layer / Create Layer from
    Selected)"""
    bl_idname = "allset.anim_layer_create"
    bl_label = "Create Animation Layer"
    bl_options = {'UNDO'}

    from_selected: BoolProperty(default=False, options={'SKIP_SAVE'})

    def execute(self, context):
        scene = context.scene
        ls = ensure_list(scene)
        e = ls.add()
        e.name = unique_name(scene)
        scene.allset_anim_layer_index = len(ls) - 1
        if self.from_selected:
            for ob in _layer_objects(context):
                add_object(scene, ob, e.name)
        sync(scene)
        return {'FINISHED'}


class ALLSET_OT_anim_layer_members(bpy.types.Operator):
    """Add the selected objects to the selected layer, or remove them (Maya Add / Remove Selected Objects)"""
    bl_idname = "allset.anim_layer_members"
    bl_label = "Layer Members"
    bl_options = {'UNDO'}

    add: BoolProperty(default=True, options={'SKIP_SAVE'})

    def execute(self, context):
        e = selected(context.scene)
        if e is None or e.name == BASE:
            self.report({'WARNING'}, "Select an animation layer")
            return {'CANCELLED'}
        for ob in _layer_objects(context):
            (add_object if self.add else remove_object)(context.scene, ob, e.name)
        sync(context.scene)
        return {'FINISHED'}


class ALLSET_OT_anim_layer_delete(bpy.types.Operator):
    """Delete the selected animation layer and its keys (Maya Delete Layer)"""
    bl_idname = "allset.anim_layer_delete"
    bl_label = "Delete Animation Layer"
    bl_options = {'UNDO'}

    def execute(self, context):
        scene = context.scene
        e = selected(scene)
        if e is None or e.name == BASE:
            self.report({'WARNING'}, "BaseAnimation can't be deleted")
            return {'CANCELLED'}
        name = e.name
        for ob in members(scene, name):
            remove_object(scene, ob, name)
        ls = layers(scene)
        ls.remove(next(i for i, x in enumerate(ls) if x.name == name))
        scene.allset_anim_layer_index = max(0, min(scene.allset_anim_layer_index, len(ls) - 1))
        sync(scene)
        return {'FINISHED'}


class ALLSET_OT_anim_layer_select(bpy.types.Operator):
    """Make this the selected layer: keys go to it (Maya click on a layer)"""
    bl_idname = "allset.anim_layer_select"
    bl_label = "Select Animation Layer"
    bl_options = {'INTERNAL'}

    index: IntProperty(options={'SKIP_SAVE'})

    def execute(self, context):
        context.scene.allset_anim_layer_index = self.index
        return {'FINISHED'}


classes = (ALLSET_PG_anim_layer, ALLSET_OT_anim_layer_create, ALLSET_OT_anim_layer_members,
           ALLSET_OT_anim_layer_delete, ALLSET_OT_anim_layer_select)


def register_props():
    bpy.types.Scene.allset_anim_layers = CollectionProperty(type=ALLSET_PG_anim_layer)
    bpy.types.Scene.allset_anim_layer_index = IntProperty(name="Selected Layer", default=0, min=0)


def unregister_props():
    del bpy.types.Scene.allset_anim_layer_index
    del bpy.types.Scene.allset_anim_layers
