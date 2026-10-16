# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya navigation values for Blender's user preferences, with backup/restore.

Values and reasons: docs/steps/step_4.md 「계획」 1 (research/maya/interaction.md
§1). The user's original values are kept as JSON in the add-on preferences
(``prefs_backup``) so they survive restarts and come back when the option
or the add-on is turned off. Applied once: a later restart does not
override values the user changed afterwards.
"""

import json

import bpy

# (data path under bpy.context.preferences, Maya value)
PRESET = (
    ("inputs.view_rotate_method", 'TURNTABLE'),
    ("inputs.use_rotate_around_active", False),
    ("inputs.use_mouse_depth_navigate", False),
    ("inputs.use_zoom_to_mouse", False),
    ("inputs.use_auto_perspective", True),
    ("inputs.view_zoom_method", 'DOLLY'),
    ("inputs.view_zoom_axis", 'HORIZONTAL'),
    # With HORIZONTAL axis, False = drag right dollies in (Maya); measured by
    # tests/gui/gui_step4_view.py (True made drag right dolly out).
    ("inputs.invert_mouse_zoom", False),
    ("inputs.invert_zoom_wheel", False),
)


def _resolve(prefs, path):
    owner_name, attr = path.split(".")
    return getattr(prefs, owner_name), attr


def read(prefs, preset=PRESET):
    out = {}
    for path, _value in preset:
        owner, attr = _resolve(prefs, path)
        out[path] = getattr(owner, attr)
    return out


def write(prefs, values):
    for path, value in values.items():
        owner, attr = _resolve(prefs, path)
        setattr(owner, attr, value)


def apply(prefs, addon_prefs):
    """Back up the current values (once) and apply the Maya preset."""
    if not addon_prefs.prefs_backup:
        addon_prefs.prefs_backup = json.dumps(read(prefs))
    write(prefs, dict(PRESET))


def restore(prefs, addon_prefs):
    """Put the user's backed-up values back and forget the backup."""
    if addon_prefs.prefs_backup:
        write(prefs, json.loads(addon_prefs.prefs_backup))
        addon_prefs.prefs_backup = ""


def register():
    from . import preferences
    addon_prefs = preferences.get()
    # First enable (no backup yet): apply. Later starts: values already stored.
    if addon_prefs.use_maya_navigation and not addon_prefs.prefs_backup:
        apply(bpy.context.preferences, addon_prefs)


def unregister():
    from . import preferences
    try:
        addon_prefs = preferences.get()
    except KeyError:
        return
    restore(bpy.context.preferences, addon_prefs)
