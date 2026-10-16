# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya Kit: make Blender feel like Maya (keymap, interaction, UI, concepts).

Shipped as one Blender 4.2+ extension (). The same
source also builds a legacy add-on zip, which is why ``bl_info`` is kept;
extensions read ``blender_manifest.toml`` instead and ignore it.

Each feature area is a sub-package with its own ``register()`` /
``unregister()``. Order matters: preferences first (others may read them),
then the Blender-preferences preset, keymap last (keymap items reference
operators registered before it).
"""

bl_info = {
    "name": "Maya Kit",
    "author": "ohnsk",
    "version": (0, 1, 0),
    "blender": (4, 2, 0),
    "location": "Preferences > Add-ons > Maya Kit",
    "description": "Maya-style keymap, interaction, UI and concepts for Maya users",
    "category": "Interface",
}

from . import preferences, prefs_preset, operators, ui, command_line, theme, app_template, keymap

_modules = (preferences, prefs_preset, operators, ui, command_line, theme, app_template, keymap)


def register():
    for mod in _modules:
        mod.register()


def unregister():
    for mod in reversed(_modules):
        mod.unregister()
