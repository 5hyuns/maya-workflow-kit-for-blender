# SPDX-License-Identifier: GPL-3.0-or-later
"""The scene-structure version the kit's Outliner tree (``ui/outliner_tree.py``) and other structure caches key on.

``structure_version`` goes up whenever names, parents, membership or bones may have changed: every depsgraph update
the row check doesn't skip (``depsgraph_filter.outliner_skip``: motion only, or the Scene alone — a selection; also a
joint selection and the steps of a move in Object / Pose Mode), a file load, undo and redo. Code that derives something from the scene's structure keeps it until this changes.
"""

import bpy
from bpy.app.handlers import persistent

from .. import depsgraph_filter

_state = {"version": 0}


def _bump():
    _state["version"] += 1


def structure_version():
    """Goes up whenever names, parents, membership or bones may have changed (any update the row check doesn't skip,
    load, undo, redo): code that derives something from the scene's structure keeps it until this changes."""
    return _state["version"]


_SKELETONS = {}     # skeleton object pointer -> ``_skeleton_rows`` when last seen


def _skeleton_rows(ob):
    """What of skeleton ``ob`` the structure holds outside Edit Mode (bones are re-parented only there): its name,
    parent and Outliner flag, and its joints' names in order."""
    p = ob.parent
    return (ob.name, p.as_pointer() if p is not None else 0, ob.parent_type, ob.parent_bone,
            bool(ob.get("allset_hidden_in_outliner")), tuple(ob.pose.bones.keys()) if ob.pose is not None else ())


def _joint_selection_only(scene, depsgraph):
    """The update can't change the structure: a joint selection (it updates the skeleton and its data, Blender
    re-evaluates the meshes it deforms) — every skeleton it touched holds the same names, parent and joints as when
    last seen; anything else it touched only moved or was re-evaluated."""
    if depsgraph is None or scene is None:
        return False
    touched = set()
    for u in depsgraph.updates:
        id_ = u.id
        if isinstance(id_, bpy.types.Scene):
            continue
        if isinstance(id_, bpy.types.Armature):
            if id_.is_editmode:
                return False
            touched.add(id_.original.as_pointer())
            continue
        if not isinstance(id_, bpy.types.Object):
            return False
        if id_.type == 'ARMATURE':
            touched.add(id_.original.data.as_pointer() if id_.original.data is not None else 0)
        elif not (u.is_updated_transform or u.is_updated_geometry):
            return False                # renamed, re-parented, a custom property: not a motion
    if not touched:
        return False
    same = True
    for ob in scene.objects:
        if ob.type != 'ARMATURE' or ob.data is None or ob.data.as_pointer() not in touched:
            continue
        sig = _skeleton_rows(ob)
        if _SKELETONS.get(ob.as_pointer()) != sig:
            same = False
            if len(_SKELETONS) > 256:
                _SKELETONS.clear()
            _SKELETONS[ob.as_pointer()] = sig
    return same


def _posing():
    """A move / rotate / scale runs in Object or Pose Mode: until it ends only poses and transforms change (every
    step of a pose drag updates the skeleton's data)."""
    from . import maya_joints
    return getattr(bpy.context, "mode", None) in {'OBJECT', 'POSE'} and maya_joints.transforming()


@persistent
def _on_depsgraph(scene, depsgraph):
    # #191: the rows are names / parents / membership / bones — a move, a mesh edit or a selection change can't
    # change them
    if depsgraph_filter.outliner_skip(depsgraph):
        return
    try:
        if _posing():
            return
        if _joint_selection_only(scene, depsgraph):
            return
    except (ReferenceError, AttributeError):
        pass
    _bump()


@persistent
def _on_undo(_dummy):
    _SKELETONS.clear()
    _bump()


@persistent
def _on_load(_dummy):
    _SKELETONS.clear()
    _bump()


_HANDLERS = ((bpy.app.handlers.depsgraph_update_post, _on_depsgraph), (bpy.app.handlers.load_post, _on_load),
             (bpy.app.handlers.undo_post, _on_undo), (bpy.app.handlers.redo_post, _on_undo))


def register():
    for handlers, fn in _HANDLERS:
        if fn not in handlers:
            handlers.append(fn)
    _bump()


def unregister():
    for handlers, fn in _HANDLERS:
        while fn in handlers:
            handlers.remove(fn)
    _SKELETONS.clear()
