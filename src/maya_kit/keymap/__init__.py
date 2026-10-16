# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya keymap.

Plan (, M1): generate a "Maya" keyconfig from Blender's Industry
Compatible data () and keep
small per-feature overlays in the add-on keyconfig. Everything added to the
add-on keyconfig goes through ``add_item`` so ``unregister`` removes it.
"""

import bpy

# (KeyMap, KeyMapItem) pairs this add-on created in wm.keyconfigs.addon.
_addon_keymaps = []


def add_item(km_name, idname, type, value, space_type="EMPTY", region_type="WINDOW", **kwargs):
    """Add one item to the add-on keyconfig and remember it for cleanup.

    Returns the KeyMapItem, or None when there is no add-on keyconfig
    (it can be missing in some background sessions).
    """
    kc = bpy.context.window_manager.keyconfigs.addon
    if kc is None:
        return None
    km = kc.keymaps.new(name=km_name, space_type=space_type, region_type=region_type)
    kmi = km.keymap_items.new(idname, type, value, **kwargs)
    _addon_keymaps.append((km, kmi))
    return kmi


def register():
    pass


def unregister():
    for km, kmi in reversed(_addon_keymaps):
        try:
            km.keymap_items.remove(kmi)
        except (ReferenceError, RuntimeError):
            pass  # Keyconfig already freed (Blender quitting).
    _addon_keymaps.clear()
