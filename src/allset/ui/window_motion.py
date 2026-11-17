# SPDX-License-Identifier: GPL-3.0-or-later
"""Whether a window moved or changed size since a draw callback last drew (``moved``).

While a window is dragged or resized, Blender redraws every region of every window at each step. A region whose own
size stayed the same shows what it showed before, so a draw that finds something in its drawn pixels (a
framebuffer read waits for the GPU to finish) can use what it found at its previous draw instead.
"""

import bpy

_seen = {}      # caller key -> the windows' rects at that caller's previous draw
SEEN_MAX = 256  # keys are region pointers: closed regions' entries go when there are this many


def rects():
    """(x, y, width, height) of every open window."""
    try:
        return tuple((w.x, w.y, w.width, w.height) for w in bpy.context.window_manager.windows)
    except (AttributeError, ReferenceError):
        return None


def moved(key):
    """True when a window moved, changed size, opened or closed since the previous call with ``key``."""
    now = rects()
    last = _seen.get(key)
    if len(_seen) >= SEEN_MAX and last is None:
        _seen.clear()
    _seen[key] = now
    return now is not None and last is not None and last != now


def forget():
    _seen.clear()
