# SPDX-License-Identifier: GPL-3.0-or-later
"""The scene-structure version the kit's Outliner tree (``ui/outliner_tree.py``) and other structure caches key on.

``structure_version`` goes up whenever names, parents, membership or bones may have changed: every depsgraph update
the row check doesn't skip (``depsgraph_filter.outliner_skip``: motion only, or the Scene alone — a selection), a
file load, undo and redo. Code that derives something from the scene's structure keeps it until this changes.
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


@persistent
def _on_depsgraph(scene, depsgraph):
    # #191: the rows are names / parents / membership / bones — a move, a mesh edit or a selection change can't
    # change them
    if depsgraph_filter.outliner_skip(depsgraph):
        return
    _bump()


@persistent
def _on_undo(_dummy):
    _bump()


@persistent
def _on_load(_dummy):
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
