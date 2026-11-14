# SPDX-License-Identifier: GPL-3.0-or-later
"""The nodes the kit's key commands act on and their keys: the Channel Box's targets (``nodes``: selected objects, or
pose bones in pose mode), a node's F-curves (``node_fcurves``; a bone: its own ``pose.bones["n"]`` curves), the Time
Slider range (``time_range``), the keys in it (``keys_in``) and ``_move`` (a key and its handles in time).
Used by key_scope and time_keys (which re-exports these names for key_insert, graph_key_menu and ui/time_slider).
"""

import bpy


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


def _move(kp, dx):
    kp.co.x += dx
    kp.handle_left.x += dx
    kp.handle_right.x += dx
