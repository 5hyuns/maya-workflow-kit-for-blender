# SPDX-License-Identifier: GPL-3.0-or-later
"""Joints in Maya display layers.

Maya: a joint picked in a view is a node of its own, so a display layer made from a picked joint holds that joint
only (one node, one layer: adding it to another layer moves it). The layer's state reaches everything below a member:
a hidden layer hides the member joint, every joint below it and the objects under them; Template draws them grey,
Reference black, and neither can be picked. The bone from the member's parent joint stays (a bone belongs to its
parent joint). A parent's Template or Reference wins over a child's Normal layer, and a hidden parent hides a child
whose own layer is visible. Skinned surfaces are not members and keep deforming.

Here a joint's layer is ``PoseBone.allset_display_layer`` (the layer collection: a renamed joint or layer keeps it, a
duplicated skeleton copies it, undo takes it back, a deleted layer leaves None). A layer never writes the joint's own
flags (``PoseBone.hide`` is its Visibility channel): ``state(ob)`` = {joint name: HIDDEN / TEMPLATE / REFERENCE} of
every joint a layer reaches, kept per skeleton until a layer, a membership, the skeleton, playback or undo changes it.
The kit's joint drawing, joint picking, Outliner rows and parent rule (``operators/dag.py``) read it; Blender's own
bone drawing (a view with the Bones overlay on) and Blender's bone operators don't know it.
"""

import types

import bpy
from bpy.app.handlers import persistent
from bpy.props import PointerProperty

from .. import depsgraph_filter

PROP = "allset_display_layer"
HIDDEN, TEMPLATE, REFERENCE = "HIDDEN", "TEMPLATE", "REFERENCE"
# drawn colour of a joint in a Template / Reference layer: grey and black lines, like Maya
COLOURS = {TEMPLATE: (0x78 / 255, 0x78 / 255, 0x78 / 255), REFERENCE: (0.0, 0.0, 0.0)}
_EMPTY = types.MappingProxyType({})
_REV = [0]          # bumped by every change that can change a skeleton's layer state
_STATES = {}        # skeleton object pointer -> (key, state)
_ROOTS = {}         # kit skeleton object pointer -> (key, first root joint name)
_PLAYING = [False]  # animation playback runs: a layer with Playback off hides its joints


# --- membership -----------------------------------------------------------------------------------------------------

def _on_set(_self, _context):
    bump()


def layer_of(pb):
    """The display layer (collection) joint ``pb`` belongs to, or None."""
    coll = getattr(pb, PROP, None)
    if coll is None:
        return None
    try:
        return coll if coll.allset_layer.is_layer else None
    except (ReferenceError, AttributeError):
        return None


def set_layer(pb, coll):
    """Put joint ``pb`` in layer ``coll`` (None: in no layer). A joint is in one layer at most, like Maya."""
    if getattr(pb, PROP, None) != coll:
        setattr(pb, PROP, coll)


def members(coll, scene):
    """{skeleton object: [joint names]} of layer ``coll`` among ``scene``'s objects, in bone order."""
    out = {}
    if not hasattr(bpy.types.PoseBone, PROP):
        return out
    for ob in scene.objects:
        if ob is None or ob.type != 'ARMATURE' or ob.pose is None:
            continue
        names = [pb.name for pb in ob.pose.bones if getattr(pb, PROP) == coll]
        if names:
            out[ob] = names
    return out


def has_members(scene):
    """Some joint of ``scene`` is in a display layer."""
    if not hasattr(bpy.types.PoseBone, PROP):
        return False
    return any(ob is not None and ob.type == 'ARMATURE' and ob.pose is not None
               and any(getattr(pb, PROP) is not None for pb in ob.pose.bones) for ob in scene.objects)


# --- state ----------------------------------------------------------------------------------------------------------

def bump(redraw=True):
    """A layer, a membership or a skeleton changed: every skeleton's state is read again at its next use."""
    _REV[0] += 1
    _STATES.clear()
    _ROOTS.clear()
    try:
        from . import maya_joints
        maya_joints.changed()
    except (ImportError, AttributeError):
        pass
    if redraw:
        _redraw()


def _redraw():
    try:
        for w in bpy.context.window_manager.windows:
            for a in w.screen.areas:
                if a.type in {'VIEW_3D', 'OUTLINER'}:
                    a.tag_redraw()
    except (AttributeError, ReferenceError, RuntimeError):
        pass


def set_playing(on):
    if _PLAYING[0] != bool(on):
        _PLAYING[0] = bool(on)
        bump()


def _compute(ob):
    pose = ob.pose
    if pose is None or not hasattr(bpy.types.PoseBone, PROP):
        return _EMPTY
    found = [(pb.name, coll) for pb in pose.bones if (coll := getattr(pb, PROP)) is not None]
    if not found:
        return _EMPTY
    data = ob.data
    bones = data.edit_bones if data.is_editmode else data.bones
    playing = _PLAYING[0]
    ranked = []
    for name, coll in found:
        st = getattr(coll, "allset_layer", None)
        b = bones.get(name)
        if st is None or not st.is_layer or b is None:
            continue
        hidden = not st.visible or (playing and not st.playback)
        kind = st.display_type if st.display_type in COLOURS else None
        if not hidden and kind is None:
            continue
        depth, p = 0, b.parent
        while p is not None:
            depth, p = depth + 1, p.parent
        ranked.append((depth, name, b, hidden, kind))
    if not ranked:
        return _EMPTY
    ranked.sort(key=lambda r: (r[0], r[1]))     # members nearer the root first: their Template / Reference wins
    out = {}
    for _depth, name, b, hidden, kind in ranked:
        names = (name, *(c.name for c in b.children_recursive))
        if hidden:
            for n in names:
                out[n] = HIDDEN
        else:
            for n in names:
                out.setdefault(n, kind)
    return out


def _key(ob):
    pose = ob.pose
    return (_REV[0], ob.data.as_pointer(), ob.mode, len(pose.bones) if pose is not None else 0), ob.as_pointer()


def _cached(store, ob, fn):
    try:
        key, ptr = _key(ob)
    except (ReferenceError, AttributeError):
        return None
    got = store.get(ptr)
    if got is not None and got[0] == key:
        return got[1]
    out = fn(ob)
    if len(store) > 64:
        store.clear()
    store[ptr] = (key, out)
    return out


def state(ob):
    """{joint name: HIDDEN / TEMPLATE / REFERENCE} of skeleton ``ob``: the joints its display layers reach (members
    and every joint below them). Empty for other objects and skeletons without such joints. Read only."""
    if ob is None or ob.type != 'ARMATURE':
        return _EMPTY
    out = _cached(_STATES, ob, _compute)
    return _EMPTY if out is None else out


def hidden(ob, name):
    """Joint ``name`` of skeleton ``ob`` is hidden by a display layer (its own or one above it)."""
    return state(ob).get(name) == HIDDEN


def pickable(ob, name):
    """No display layer keeps joint ``name`` of skeleton ``ob`` from being picked in a view (hidden, Template or
    Reference)."""
    return name not in state(ob)


def parent_joint(ob):
    """The joint whose layer state object ``ob`` follows: its parent bone, or for an object parented to a kit
    skeleton itself the skeleton's first root joint (where the kit Outliner lists it). None otherwise."""
    p = ob.parent
    if p is None or p.type != 'ARMATURE':
        return None
    if ob.parent_type == 'BONE':
        return ob.parent_bone or None
    if ob.parent_type != 'OBJECT' or not state(p):
        return None
    return _cached(_ROOTS, p, _first_root)


def _first_root(ob):
    from . import outliner_tree
    bones = outliner_tree._Bones(ob)
    return bones.roots[0] if outliner_tree.is_kit_skeleton(ob, bones) else None


def hidden_under(ob):
    """Object ``ob`` hangs from a joint a display layer hides."""
    name = parent_joint(ob)
    return name is not None and hidden(ob.parent, name)


# --- handlers -------------------------------------------------------------------------------------------------------

@persistent
def _on_depsgraph(_scene, depsgraph=None):
    """Skeleton changes other than motion: renamed, re-parented, added or removed joints / objects, a membership
    written; in Edit Mode every bone edit (a re-parented edit bone is a geometry update)."""
    if not _STATES:
        return
    try:
        if depsgraph_filter.only_scene(depsgraph):
            return
        if depsgraph_filter.only_motion(depsgraph) and not any(
                isinstance(u.id, bpy.types.Armature) and u.id.is_editmode for u in depsgraph.updates):
            return
    except (ReferenceError, AttributeError):
        pass
    bump(redraw=False)


@persistent
def _on_reload(*_args):
    bump()


def _handlers():
    h = bpy.app.handlers     # playback start / end: layer_editor.on_playback_pre / _post call set_playing
    return ((h.undo_post, _on_reload), (h.redo_post, _on_reload), (h.load_post, _on_reload))


def register():
    bpy.types.PoseBone.allset_display_layer = PointerProperty(type=bpy.types.Collection, update=_on_set,
                                                              options={'HIDDEN'})
    lst = bpy.app.handlers.depsgraph_update_post
    if _on_depsgraph not in lst:
        lst.insert(0, _on_depsgraph)       # before the parent rule (operators/dag.py) reads the state
    for lst, fn in _handlers():
        if fn not in lst:
            lst.append(fn)


def unregister():
    for lst, fn in ((bpy.app.handlers.depsgraph_update_post, _on_depsgraph), *_handlers()):
        if fn in lst:
            lst.remove(fn)
    _STATES.clear()
    _ROOTS.clear()
    _PLAYING[0] = False
    del bpy.types.PoseBone.allset_display_layer
