# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya Kit app template ("MayaKit"): Maya General layout in startup.blend.

Installed by the Maya Kit extension (Preferences > Add-ons > Maya Kit >
Install Maya Layout). The template only holds the layout; all behaviour is in
the extension, which is enabled here if it is installed but turned off.
"""

import importlib

import addon_utils
import bpy


def _maya_kit_module():
    for mod in addon_utils.modules(refresh=False):
        name = mod.__name__
        if name == "maya_kit" or name.endswith(".maya_kit"):
            return name
    return None


def register():
    name = _maya_kit_module()
    if name and not addon_utils.check(name)[1]:
        addon_utils.enable(name, default_set=False)
    # Switching to this template reloads the saved preferences without re-registering
    # add-ons, so an unsaved "Maya" keymap choice falls back to "Blender" (found by
    # tools/release_check.py, docs/steps/step_13.md). Re-activate it unless the user
    # picked a keymap other than Blender's default.
    kcs = bpy.context.window_manager.keyconfigs
    if name and addon_utils.check(name)[1] and (kcs.active is None or kcs.active.name == "Blender"):
        importlib.import_module(name + ".keymap").activate()


def unregister():
    pass
