# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya navigation and undo values for Blender's user preferences, with backup/restore.

Values and reasons: docs/steps/step_4.md 「계획」 1 (research/maya/interaction.md
§1). The user's original values are kept as JSON in the add-on preferences
(``prefs_backup``) so they survive restarts and come back when the option
or the add-on is turned off. Applied once: a later restart does not
override values the user changed afterwards.
"""

import json
import os
import sys

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


# Maya's undo queue is infinite (undoIsInfinite true, research/maya/defaults.json:130-134,
# interaction.md:222); Blender keeps at most 256 steps (hard max of edit.undo_steps, default 32).
# undo_memory_limit stays 0 (= no limit). docs/steps/step_30.md 「계획」 3.
UNDO_PRESET = (
    ("edit.undo_steps", 256),
)

# Maya Auto Key keys only attributes that already have keys (research/maya/workflows/animation.md:17, §3 row 9);
# Blender's auto keying keys every changed channel unless "Only Insert Available" is on (docs/steps/step_70.md).
AUTOKEY_PRESET = (
    ("edit.use_keyframe_insert_available", True),
)

# Maya starts without a splash popup (docs/steps/step_42.md); option off by default.
SPLASH_PRESET = (
    ("view.show_splash", False),
)


# Maya density (docs/steps/step_44.md): Maya 2022 draws its Qt UI at device pixel ratio 1.0 even on a
# 125 % Windows display (research/maya/colors.json metrics: Segoe UI 11 px, menu items 20 px, menu bar
# 27 px), while Blender multiplies its UI by the OS scale (system.ui_scale 1.25 at view.ui_scale 1.0,
# measured). Blender at an effective scale of 1.0 gives 11 px text, 20 px rows and a 26 px top bar,
# so the Maya value is 1 / (OS scale): 0.8 at 125 %, 1.0 at 100 %.
def os_scale(prefs=None):
    prefs = prefs or bpy.context.preferences
    if prefs.system.ui_scale <= 0.0:   # background: no window, system.ui_scale is 0
        return 1.0
    return prefs.system.ui_scale / max(prefs.view.ui_scale, 0.01)


def maya_ui_scale(prefs=None):
    return round(min(max(1.0 / os_scale(prefs), 0.5), 2.0), 3)


def _density_preset():
    return (("view.ui_scale", maya_ui_scale()),)


# Maya's UI font is Segoe UI (metrics.font). Used from the installed Windows font, never shipped
# (step_40.md D3); nothing to apply on other systems or when the file is missing.
SEGOE_UI = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", "segoeui.ttf")


def font_available():
    return sys.platform == "win32" and os.path.isfile(SEGOE_UI)


def _font_preset():
    return (("view.font_path_ui", SEGOE_UI),) if font_available() else ()


# Maya's viewport wires are aliased 1 px lines (step 43 viewport.md: dormant wire #000460 vs Blender's
# smoothed #151d5e).
WIRE_PRESET = (
    ("system.use_overlay_smooth_wire", False),
    ("system.use_edit_mode_smooth_wire", False),
)

# group -> (preset or function returning one, backup property, option property) on the add-on preferences.
GROUPS = {
    "navigation": (PRESET, "prefs_backup", "use_maya_navigation"),
    "undo": (UNDO_PRESET, "undo_backup", "use_maya_undo"),
    "autokey": (AUTOKEY_PRESET, "autokey_backup", "use_maya_auto_key"),
    "splash": (SPLASH_PRESET, "splash_backup", "maya_hide_splash"),
    "density": (_density_preset, "density_backup", "maya_density"),
    "font": (_font_preset, "font_backup", "maya_font"),
    "wire": (WIRE_PRESET, "wire_backup", "maya_wire"),
}


def preset_of(group):
    preset = GROUPS[group][0]
    return preset() if callable(preset) else preset


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
    preset, backup = preset_of(group), GROUPS[group][1]
    if not preset:
        return
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
    (JSON) and comes back when the add-on is turned off (docs/steps/step_27.md).
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


# Applied from a timer: while add-ons register at start-up the window (and so the OS scale in
# system.ui_scale) may not exist yet.
LATE = ("density",)


def _apply_late():
    from . import preferences
    try:
        addon_prefs = preferences.get()
    except KeyError:
        return None
    for group in LATE:
        _preset, backup, option = GROUPS[group]
        if getattr(addon_prefs, option) and not getattr(addon_prefs, backup):
            apply(bpy.context.preferences, addon_prefs, group)
    return None


def register():
    from . import preferences
    addon_prefs = preferences.get()
    # First enable (no backup yet): apply. Later starts: values already stored.
    for group, (_preset, backup, option) in GROUPS.items():
        if group in LATE:
            continue
        if getattr(addon_prefs, option) and not getattr(addon_prefs, backup):
            apply(bpy.context.preferences, addon_prefs, group)
    bpy.app.timers.register(_apply_late, first_interval=0.0)


def unregister():
    from . import preferences
    try:
        addon_prefs = preferences.get()
    except KeyError:
        return
    if bpy.app.timers.is_registered(_apply_late):
        bpy.app.timers.unregister(_apply_late)
    for group in GROUPS:
        restore(bpy.context.preferences, addon_prefs, group)
    restore_runtime(bpy.context.preferences, addon_prefs)
