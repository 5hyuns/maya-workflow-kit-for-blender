# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya navigation and undo values for Blender's user preferences, with backup/restore.

Values and reasons:  「계획」 1 (
). The user's original values are kept as JSON in the add-on preferences
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
    # With HORIZONTAL axis, False = drag right dollies in (Maya); checked by
    # tests/gui/gui_step4_view.py (True made drag right dolly out).
    ("inputs.invert_mouse_zoom", False),
    ("inputs.invert_zoom_wheel", False),
)


# Maya's undo queue is infinite (undoIsInfinite true, ,
# interaction.md:222); Blender keeps at most 256 steps (hard max of edit.undo_steps, default 32).
# undo_memory_limit stays 0 (= no limit).  「계획」 3.
UNDO_PRESET = (
    ("edit.undo_steps", 256),
)

# group -> (preset, backup property, option property) on the add-on preferences.
GROUPS = {
    "navigation": (PRESET, "prefs_backup", "use_maya_navigation"),
    "undo": (UNDO_PRESET, "undo_backup", "use_maya_undo"),
}


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


def apply(prefs, addon_prefs, group="navigation"):
    """Back up the current values (once) and apply the Maya preset of ``group``."""
    preset, backup, _option = GROUPS[group]
    if not getattr(addon_prefs, backup):
        setattr(addon_prefs, backup, json.dumps(read(prefs, preset)))
    write(prefs, dict(preset))


def restore(prefs, addon_prefs, group="navigation"):
    """Put the user's backed-up values back and forget the backup."""
    _preset, backup, _option = GROUPS[group]
    if getattr(addon_prefs, backup):
        write(prefs, json.loads(getattr(addon_prefs, backup)))
        setattr(addon_prefs, backup, "")


def set_runtime(path, value, prefs=None, addon_prefs=None):
    """Change a Blender preference from a Maya key (e.g. ``view.gizmo_size`` by = / -).

    The user's value from before the first change is kept in ``runtime_backup``
    (JSON) and comes back when the add-on is turned off.
    """
    from . import preferences
    prefs = prefs or bpy.context.preferences
    addon_prefs = addon_prefs or preferences.get()
    backup = json.loads(addon_prefs.runtime_backup or "{}")
    owner, attr = _resolve(prefs, path)
    if path not in backup:
        backup[path] = getattr(owner, attr)
        addon_prefs.runtime_backup = json.dumps(backup)
    setattr(owner, attr, value)
    return getattr(owner, attr)


def restore_runtime(prefs, addon_prefs):
    if addon_prefs.runtime_backup:
        write(prefs, json.loads(addon_prefs.runtime_backup))
        addon_prefs.runtime_backup = ""


def register():
    from . import preferences
    addon_prefs = preferences.get()
    # First enable (no backup yet): apply. Later starts: values already stored.
    for group, (_preset, backup, option) in GROUPS.items():
        if getattr(addon_prefs, option) and not getattr(addon_prefs, backup):
            apply(bpy.context.preferences, addon_prefs, group)


def unregister():
    from . import preferences
    try:
        addon_prefs = preferences.get()
    except KeyError:
        return
    for group in GROUPS:
        restore(bpy.context.preferences, addon_prefs, group)
    restore_runtime(bpy.context.preferences, addon_prefs)
