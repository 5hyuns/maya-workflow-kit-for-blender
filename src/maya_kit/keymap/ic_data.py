# SPDX-License-Identifier: GPL-3.0-or-later
"""Industry Compatible keymap data, generated fresh from the installed Blender.

Same loading as Blender's own preset loader
(``$S\\presets\\keyconfig\\Industry_Compatible.py:21-34``): exec
``keymap_data/industry_compatible_data.py`` and call ``generate_keymaps``.
No copy of the IC data is kept in this repository, so a Blender update is
picked up automatically; ``patch.KeyconfigData.remove`` raises when an item we
patch has disappeared.
"""

import os

import bpy


def _module_path():
    from bpy.utils import system_resource
    return os.path.join(system_resource('SCRIPTS'), "presets", "keyconfig",
                        "keymap_data", "industry_compatible_data.py")


def generate():
    """Return a new list of IC keyconfig data (safe to mutate)."""
    ic = bpy.utils.execfile(_module_path())
    params = ic.Params(
        use_mouse_emulate_3_button=bpy.context.preferences.inputs.use_mouse_emulate_3_button)
    data = ic.generate_keymaps(params)

    import sys
    if sys.platform == "darwin":
        from bl_keymap_utils.platform_helpers import keyconfig_data_oskey_from_ctrl_for_macos
        data = keyconfig_data_oskey_from_ctrl_for_macos(data)
    return data
