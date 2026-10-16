# SPDX-License-Identifier: GPL-3.0-or-later
"""Optional "Maya Units": 1 BU = 1 cm (docs/user_decisions.md #1).

Default (decision 1): metres kept, lengths shown in cm (the app template sets
that, tools/make_startup.py). With the add-on preference on, the scenes of the
current file get ``scale_length = 0.01`` + cm and the 3D views Maya's camera
clip 0.1 / 10000 (research/maya/defaults.json camera, PREF:569-570; units =
cm = BU). Side effects (physics, light falloff and importers assume
1 BU = 1 m): research/blender/api_limits.md:76-78.

The values before are kept per scene in the custom property
``maya_kit_units_backup`` and come back when the option is turned off. New
files (no file path: the home file) get the units on load; saved files are
never changed behind the user's back. Plan: docs/steps/step_10.md 「계획」 7.
"""

import json

import bpy
from bpy.app.handlers import persistent

BACKUP = "maya_kit_units_backup"
UNITS = {"system": 'METRIC', "length_unit": 'CENTIMETERS', "scale_length": 0.01}
VIEW = {"clip_start": 0.1, "clip_end": 10000.0}


def _views():
    for screen in bpy.data.screens:
        for area in screen.areas:
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    yield space


def is_applied(scene):
    return BACKUP in scene


def apply_file():
    """Maya units on every scene and 3D view of the current file (backup kept once)."""
    views = list(_views())
    view_before = {k: getattr(views[0], k) for k in VIEW} if views else dict(VIEW)
    for scene in bpy.data.scenes:
        us = scene.unit_settings
        if BACKUP not in scene:
            scene[BACKUP] = json.dumps({"units": {k: getattr(us, k) for k in UNITS},
                                        "view": view_before})
        for key, value in UNITS.items():
            setattr(us, key, value)
    for space in views:
        for key, value in VIEW.items():
            setattr(space, key, value)


def restore_file():
    """Values from before ``apply_file`` (scenes without a backup are left alone)."""
    view = None
    for scene in bpy.data.scenes:
        if BACKUP not in scene:
            continue
        data = json.loads(scene[BACKUP])
        us = scene.unit_settings
        for key in ("system", "length_unit", "scale_length"):  # length_unit depends on system
            setattr(us, key, data["units"][key])
        view = view or data["view"]
        del scene[BACKUP]
    if view:
        for space in _views():
            for key, value in view.items():
                setattr(space, key, value)


def _enabled():
    from .. import preferences
    try:
        return preferences.get().maya_units
    except KeyError:
        return False


@persistent
def _on_load_post(_dummy):
    if _enabled() and not bpy.data.filepath:
        apply_file()


def register_handler():
    bpy.app.handlers.load_post.append(_on_load_post)


def unregister_handler():
    if _on_load_post in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_on_load_post)
