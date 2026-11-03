# SPDX-License-Identifier: GPL-3.0-or-later
"""Persistent settings used by the official Maya In-View HUD.

This module owns HUD preferences and normalized viewport placement. It is
kept separate from drawing and modal interaction so other In-View components
can reuse the settings without importing the HUD implementation.
"""

DEFAULT_SENSITIVITY = 0.30
DEFAULT_POSITION_X = 0.65
DEFAULT_POSITION_Y = 0.35
_LAYOUT_VERSION = 1


def _preferences():
    try:
        from .. import preferences
        return preferences.get()
    except Exception:
        return None


def get_sensitivity():
    prefs = _preferences()
    try:
        return max(0.0, min(1.0, float(prefs.hud_drag_sensitivity)))
    except Exception:
        return DEFAULT_SENSITIVITY


def set_sensitivity(value):
    value = max(0.0, min(1.0, float(value)))
    prefs = _preferences()
    if prefs is not None:
        try:
            prefs.hud_drag_sensitivity = value
        except Exception:
            pass
    return value


def _migrate_default_layout(prefs):
    """Apply the new bottom-right default once, preserving later user moves."""
    try:
        if int(getattr(prefs, "hud_layout_version", 0)) < _LAYOUT_VERSION:
            for key in ("tool_hud", "maya_inview_hud"):
                setattr(prefs, key + "_x", -1.0)
                setattr(prefs, key + "_y", -1.0)
            prefs.hud_layout_version = _LAYOUT_VERSION
    except Exception:
        pass


def default_position(region):
    """Default HUD anchor: x=65%, y=35% from the viewport bottom-left.

    These are POSITION coordinates, not panel width/height ratios. The HUD's
    existing fixed footprint is preserved; each HUD layout clamps this anchor
    so the complete panel remains inside the View3D WINDOW region.
    """
    if region is None:
        return None
    return (region.width * DEFAULT_POSITION_X,
            region.height * DEFAULT_POSITION_Y)


def get_position(key, region):
    """Return saved (left, top) pixels, or the default lower-right position, nudged 5% left and 10% up."""
    prefs = _preferences()
    if region is None:
        return None
    if prefs is not None:
        _migrate_default_layout(prefs)
        try:
            x = float(getattr(prefs, key + "_x"))
            y = float(getattr(prefs, key + "_y"))
            if x >= 0.0 and y >= 0.0:
                return (x * region.width, y * region.height)
        except Exception:
            pass
    return default_position(region)


def set_position(key, x, top, region):
    """Persist HUD top-left in normalized View3D WINDOW-region coordinates."""
    prefs = _preferences()
    if prefs is None or region is None or not region.width or not region.height:
        return
    nx = max(0.0, min(1.0, float(x) / region.width))
    ny = max(0.0, min(1.0, float(top) / region.height))
    try:
        setattr(prefs, key + "_x", nx)
        setattr(prefs, key + "_y", ny)
    except Exception:
        pass
