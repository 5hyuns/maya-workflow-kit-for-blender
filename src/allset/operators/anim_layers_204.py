# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya animation layer commands, part 4.

Maya 2022 Layer Editor Anim tab (Maya, layerEditorBuildAnimLayerMenu / createAnimLayerEditor; labels
from Maya m_layerEditor.*), re-implemented on the kit's NLA layers (operators/anim_layers.py):

- Extract Selected Objects (layerEditorExtractObjectsSingleAnimLayer): per selected layer L a new layer
  ``L_extract`` with L's settings, right above L, takes the selected objects' membership and curves out of L
  (``animLayer -extractAnimation``); with BaseAnimation selected (and Extract Non-Layered Animation for Selected / All
  Objects) a new Override layer ``BaseAnimation_extract`` right above BaseAnimation takes the objects' base curves.
  The result doesn't change.
- Duplicate Layer / Duplicate Layer (No Animation) (layerEditorCopyAnimLayer: ``animLayer -copy L L_copy`` +
  ``-moveLayerAfter L``): a copy right above L with the same members, settings and (or without) curves.
- Empty (``animLayer -removeAllAttributes``) / Delete Empty Layers (deleteEmptyAnimLayers: every layer but
  BaseAnimation without attributes; the others are named in a warning).
- Zero Weight and Key Layer / Set Weight to 1.0 and Key Layer (layerEditorZero/FullWeightKeyAnimLayer): weight 0 / 1
  on the selected layers, then ``setKeyframe <layer>.weight`` at the current time. The kit's weight is each member's
  strip influence, so the key goes on every member's influence curve.
- Layer Editor Ctrl / Shift click (Qt tree view): several selected layers (``picked`` flags); the last picked one stays
  ``allset_anim_layer_index`` (keys and the Graph Editor's editable curves, step 194), ui/graph_layers.py draws the
  other selected layers' curves.

 = documented / MEL-read behaviour not checked in Maya yet ( will confirm).
"""

import bpy
from bpy.props import BoolProperty

from . import anim_layers as al

EXTRACT = "_extract"
COPY = "_copy"
NOT_EMPTY = "Layer was not deleted because it was not empty: {}"     # m_layerEditor.kLayersNotDeletedBecauseHaveObjects


# --- selection (Layer Editor Ctrl / Shift click) --------------------------------------------------------------

def pick(scene, index, toggle=False, extend=False):
    """Maya's tree view click on layer ``index``: plain = only it, Ctrl = add / remove it, Shift = the range from the
    last picked one (list order = Maya's stack order). The last picked layer becomes ``allset_anim_layer_index``; a
    Ctrl click on the last selected layer keeps it (the kit always has one selected layer, delegated)."""
    ls = al.layers(scene)
    n = len(ls)
    if not 0 <= index < n:
        return
    cur = scene.allset_anim_layer_index
    have = {i for i, e in enumerate(ls) if e.picked} if 0 <= cur < n and ls[cur].picked else \
        ({cur} if 0 <= cur < n else set())
    new = index
    if toggle:
        if index in have:
            if len(have) > 1:
                have.discard(index)
                new = cur if cur in have else max(have)
        else:
            have.add(index)
    elif extend and 0 <= cur < n:
        lo, hi = sorted((cur, index))
        have = set(range(lo, hi + 1))
    else:
        have = {index}
    for i, e in enumerate(ls):
        if e.picked != (i in have):
            e.picked = i in have
    if scene.allset_anim_layer_index != new:
        scene.allset_anim_layer_index = new       # its update shows the layer (anim_layers.show)
    else:
        al.show(scene)


def activate(scene, name):
    """Make the selected layer ``name`` the last picked one (Graph Editor row / curve pick), keeping the selection."""
    ls = al.layers(scene)
    i = next((k for k, e in enumerate(ls) if e.name == name), None)
    if i is None:
        return False
    keep = {e.name for e in al.selected_layers(scene)}
    if name not in keep:
        return False
    for e in ls:
        e.picked = e.name in keep
    if scene.allset_anim_layer_index != i:
        scene.allset_anim_layer_index = i
    return True


def redraw(context):
    wm = getattr(context, "window_manager", None)
    for win in (wm.windows if wm is not None else ()):
        for area in win.screen.areas:
            if area.type in {'GRAPH_EDITOR', 'DOPESHEET_EDITOR', 'VIEW_3D', 'PROPERTIES'}:
                area.tag_redraw()


# --- helpers ------------------------------------------------------------------------------------------------

def maya_name(scene, base):
    """Maya node naming: ``base`` when free, else ``base`` + 1, 2, ... ( the clash suffix)."""
    names = {e.name for e in al.layers(scene)}
    if base not in names:
        return base
    n = 1
    while f"{base}{n}" in names:
        n += 1
    return f"{base}{n}"


def _index_of(scene, name):
    return next((i for i, e in enumerate(al.layers(scene)) if e.name == name), None)


def _keep_selection(scene, name, picked):
    """Point the selected index at ``name`` again after list edits (the ``picked`` flags move with their entries)."""
    i = _index_of(scene, name)
    if i is None:
        i = 0
        for e in al.layers(scene):
            e.picked = False
    if scene.allset_anim_layer_index != i:
        scene.allset_anim_layer_index = i
    for e in al.layers(scene):
        if e.name in picked and not e.picked:
            e.picked = True


SETTINGS = ("weight", "mute", "solo", "lock", "override")


def insert_layer(scene, name, above, like=None):
    """A new list entry ``name`` right above entry ``above`` (Maya ``-moveLayerAfter``), settings copied from
    ``like`` (Maya ``-copy`` / ``-copyNoAnimation`` keep the layer attributes, )."""
    ls = al.ensure_list(scene)
    cur = al.selected(scene)
    keep, picked = (cur.name if cur is not None else al.BASE), {e.name for e in ls if e.picked}
    e = ls.add()
    e.name = name
    ls.move(len(ls) - 1, above + 1)
    e = ls[above + 1]
    if like is not None:
        for attr in SETTINGS:
            v = getattr(like, attr)
            if getattr(e, attr) != v:
                setattr(e, attr, v)
    _keep_selection(scene, keep, picked)
    return e


def _rename_action(act, layer, ob):
    act[al.MARK] = layer
    act.name = f"{layer}_{ob.name}"


def move_track(scene, ob, src, dst):
    """``ob``'s curves on ``src`` go to a new ``dst`` track (Maya -extractAnimation): the action is re-marked, the
    weight keys go along, the attribute list too; BaseAnimation gets a new empty action."""
    tr = al.tracks(ob)[src]
    st = al._strip(tr)
    act, state = st.action, al.strip_state(st)
    ad = ob.animation_data
    if ad.action is not None and ad.action == act:
        ad.action = None
    ad.nla_tracks.remove(tr)
    _rename_action(act, dst, ob)
    ntr = al._add_track(ob, dst, act)
    if src != al.BASE:
        al.restore_strip_state(al._strip(ntr), state)
    else:
        al._add_track(ob, al.BASE, al._new_action(ob, al.BASE))
    rec = al._attr_record(ob).get(src)
    if rec is not None:
        al._set_attr_record(ob, src, None)
        al._set_attr_record(ob, dst, rec)


def copy_track(scene, ob, src, dst, with_curves=True):
    tr = al.tracks(ob)[src]
    st = al._strip(tr)
    if with_curves:
        act = st.action.copy()
        _rename_action(act, dst, ob)
    else:
        act = al._new_action(ob, dst)
    ntr = al._add_track(ob, dst, act)
    al.restore_strip_state(al._strip(ntr), al.strip_state(st))
    rec = al._attr_record(ob).get(src)
    if rec is not None:
        al._set_attr_record(ob, dst, rec)


def _finish(scene, obs):
    names = [e.name for e in al.layers(scene)]
    for ob in obs:
        al.order_tracks(ob, names)
        ob.update_tag(refresh={'TIME'})
    al.sync(scene)


# --- commands ------------------------------------------------------------------------------------------------

def extract(scene, objects, layer):
    """Maya Extract Selected Objects from ``layer`` (BaseAnimation: Extract Non-Layered Animation). Returns the new
    layer's name. Maya makes the layer even when no object is a member ( MEL: copyNoAnimation first)."""
    if layer == al.BASE:
        new = insert_layer(scene, maya_name(scene, al.BASE + EXTRACT), 0)
        new.override = True              # layerEditorCreateAnimLayer(true, true): an Override layer from the selection
        obs = list(objects)
        for ob in obs:
            al.ensure_base(ob)
            move_track(scene, ob, al.BASE, new.name)
    else:
        src = al.layers(scene)[_index_of(scene, layer)]
        new = insert_layer(scene, maya_name(scene, layer + EXTRACT), _index_of(scene, layer), like=src)
        obs = [ob for ob in objects if layer in al.tracks(ob)]
        for ob in obs:
            move_track(scene, ob, layer, new.name)
    _finish(scene, obs)
    return new.name


def duplicate(scene, layer, with_curves=True):
    """Maya Duplicate Layer (``animLayer -copy``) / Duplicate Layer (No Animation) (``-copyNoAnimation``)."""
    src = al.layers(scene)[_index_of(scene, layer)]
    new = insert_layer(scene, maya_name(scene, layer + COPY), _index_of(scene, layer), like=src)
    obs = al.members(scene, layer)
    for ob in obs:
        copy_track(scene, ob, layer, new.name, with_curves)
    _finish(scene, obs)
    return new.name


def empty(scene, layer):
    """Maya Layers > Empty (``animLayer -removeAllAttributes``): no members, no curves; the layer stays."""
    for ob in al.members(scene, layer):
        al._set_attr_record(ob, layer, None)
        al.remove_object(scene, ob, layer)
        ob.update_tag(refresh={'TIME'})
    al.sync(scene)


def delete_empty(scene):
    """Maya Delete Empty Layers: every layer but BaseAnimation without attributes (kit: without member objects).
    Returns (deleted, kept) names."""
    ls = al.layers(scene)
    cur = al.selected(scene)
    keep, picked = (cur.name if cur is not None else al.BASE), {e.name for e in ls if e.picked}
    gone = [e.name for e in ls if e.name != al.BASE and not al.members(scene, e.name)]
    kept = [e.name for e in ls if e.name != al.BASE and e.name not in gone]
    for name in gone:
        ls.remove(_index_of(scene, name))
    _keep_selection(scene, keep, picked)
    al.sync(scene)
    return gone, kept


def key_weight(scene, names, weight, frame=None):
    """Maya Zero Weight and Key Layer / Set Weight to 1.0 and Key Layer: the weight of each layer (not
    BaseAnimation) set, then keyed at ``frame`` on every member strip's influence. Returns the keyed layers."""
    frame = scene.frame_current if frame is None else frame
    done = []
    for name in names:
        if name == al.BASE:
            continue
        i = _index_of(scene, name)
        if i is None:
            continue
        e = al.layers(scene)[i]
        if abs(e.weight - weight) > 1e-9:
            e.weight = weight                    # its update writes the strips (anim_layers.sync)
        for ob in al.members(scene, name):
            st = al._strip(al.tracks(ob)[name])
            fc = al.weight_curve(st)
            if fc is None:
                continue
            fc.keyframe_points.insert(frame, weight)
            fc.update()
            ob.update_tag(refresh={'TIME'})
        done.append(name)
    return done


# --- operators -------------------------------------------------------------------------------------------------

def _names(scene):
    return [e.name for e in al.selected_layers(scene)]


class ALLSET_OT_anim_layer_extract(bpy.types.Operator):
    """Move the selected objects' animation out of the selected layers into new layers (Maya Extract Selected
    Objects; from BaseAnimation: Extract Non-Layered Animation)"""
    bl_idname = "allset.anim_layer_extract"
    bl_label = "Extract Selected Objects"
    bl_options = {'UNDO'}

    base: BoolProperty(options={'SKIP_SAVE'}, description="Extract the non-layered (BaseAnimation) animation")
    all_objects: BoolProperty(options={'SKIP_SAVE'}, description="Every animated object, not the selection")

    def execute(self, context):
        scene = context.scene
        al.ensure_list(scene)
        if self.all_objects:
            obs = [ob for ob in scene.objects if ob.animation_data is not None and
                   (ob.animation_data.action is not None or al.has_layers(ob))]
        else:
            obs = al._layer_objects(context)
        if not obs and (self.base or self.all_objects):
            self.report({'WARNING'}, "Select objects to extract")
            return {'CANCELLED'}
        for name in ([al.BASE] if self.base or self.all_objects else _names(scene)):
            extract(scene, obs, name)
        return {'FINISHED'}


class ALLSET_OT_anim_layer_duplicate(bpy.types.Operator):
    """Copy the selected layers with their members and keys, right above them (Maya Duplicate Layer)"""
    bl_idname = "allset.anim_layer_duplicate"
    bl_label = "Duplicate Layer"
    bl_options = {'UNDO'}

    no_animation: BoolProperty(options={'SKIP_SAVE'}, description="Copy members and settings, not the keys")

    def execute(self, context):
        scene = context.scene
        names = [n for n in _names(scene) if n != al.BASE]
        if not names:
            self.report({'WARNING'}, "Select an animation layer")     #  Maya's message for BaseAnimation
            return {'CANCELLED'}
        for name in names:
            duplicate(scene, name, with_curves=not self.no_animation)
        return {'FINISHED'}


class ALLSET_OT_anim_layer_empty(bpy.types.Operator):
    """Remove every attribute (member) and its keys from the selected layers (Maya Layers > Empty)"""
    bl_idname = "allset.anim_layer_empty"
    bl_label = "Empty"
    bl_options = {'UNDO'}

    def execute(self, context):
        names = [n for n in _names(context.scene) if n != al.BASE]
        if not names:
            self.report({'WARNING'}, "Select an animation layer")
            return {'CANCELLED'}
        for name in names:
            empty(context.scene, name)
        return {'FINISHED'}


class ALLSET_OT_anim_layer_delete_empty(bpy.types.Operator):
    """Delete every animation layer without members (Maya Delete Empty Layers)"""
    bl_idname = "allset.anim_layer_delete_empty"
    bl_label = "Delete Empty Layers"
    bl_options = {'UNDO'}

    def execute(self, context):
        gone, kept = delete_empty(context.scene)
        if kept and gone:          # Maya prints the kept ones when some layer was deleted
            self.report({'WARNING'}, "; ".join(NOT_EMPTY.format(n) for n in kept))
        return {'FINISHED'}


class ALLSET_OT_anim_layer_key_weight(bpy.types.Operator):
    """Set the selected layers' weight and key it at the current time (Maya Zero Weight and Key Layer / Set Weight
    to 1.0 and Key Layer)"""
    bl_idname = "allset.anim_layer_key_weight"
    bl_label = "Key Layer Weight"
    bl_options = {'UNDO'}

    weight: bpy.props.FloatProperty(default=0.0, min=0.0, max=1.0, options={'SKIP_SAVE'})

    @classmethod
    def description(cls, context, props):
        return "Set Weight to 1.0 and Key Layer" if props.weight >= 1.0 else "Zero Weight and Key Layer"

    def execute(self, context):
        if not key_weight(context.scene, _names(context.scene), self.weight):
            self.report({'WARNING'}, "Select an animation layer")
            return {'CANCELLED'}
        return {'FINISHED'}


classes = (ALLSET_OT_anim_layer_extract, ALLSET_OT_anim_layer_duplicate, ALLSET_OT_anim_layer_empty,
           ALLSET_OT_anim_layer_delete_empty, ALLSET_OT_anim_layer_key_weight)
