# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya keymap.

A full "Maya" keyconfig is generated from Blender's Industry Compatible data
(``ic_data``) patched by ``maya_patches`` and loaded with
``keyconfig_init_from_data`` (
). Small feature-owned overlays can still go into the add-on keyconfig via
``add_item`` so ``unregister`` removes them. Activation rules:
.
"""

import bpy

KEYCONFIG_NAME = "Maya"

# (KeyMap, KeyMapItem) pairs this add-on created in wm.keyconfigs.addon.
_addon_keymaps = []
# Name of the keyconfig that was active before we activated "Maya".
_previous_active = None


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


def generate_data():
    """IC data with the Maya patches applied (fresh list each call)."""
    from . import ic_data, maya_patches
    return maya_patches.apply(ic_data.generate())


def build_keyconfig():
    """Create (or rebuild) the "Maya" keyconfig and return it."""
    from bl_keymap_utils.io import keyconfig_init_from_data
    kcs = bpy.context.window_manager.keyconfigs
    old = kcs.get(KEYCONFIG_NAME)
    if old is not None:
        kcs.remove(old)
    kc = kcs.new(KEYCONFIG_NAME)
    keyconfig_init_from_data(kc, generate_data())
    return kc


def activate():
    """Make "Maya" the active keyconfig, remembering the previous one."""
    global _previous_active
    kcs = bpy.context.window_manager.keyconfigs
    kc = kcs.get(KEYCONFIG_NAME) or build_keyconfig()
    if kcs.active != kc:
        _previous_active = kcs.active.name if kcs.active else None
        kcs.active = kc  # also stores the name in the preferences


class MAYAKIT_OT_keymap_activate(bpy.types.Operator):
    """Use the Maya keymap (it is not listed in the keymap preset menu)"""
    bl_idname = "maya_kit.keymap_activate"
    bl_label = "Activate Maya Keymap"
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        activate()
        return {'FINISHED'}


classes = (MAYAKIT_OT_keymap_activate,)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    from .. import preferences
    prefs = preferences.get()
    # Read before build_keyconfig(): the stored name is what the user picked last.
    last_choice = bpy.context.preferences.keymap.active_keyconfig
    build_keyconfig()
    if not prefs.keymap_auto_activated or last_choice == KEYCONFIG_NAME:
        activate()
        prefs.keymap_auto_activated = True


def unregister():
    global _previous_active
    for km, kmi in reversed(_addon_keymaps):
        try:
            km.keymap_items.remove(kmi)
        except (ReferenceError, RuntimeError):
            pass  # Keyconfig already freed (Blender quitting).
    _addon_keymaps.clear()

    kcs = bpy.context.window_manager.keyconfigs
    kc = kcs.get(KEYCONFIG_NAME)
    if kc is not None:
        if kcs.active == kc:
            kcs.active = kcs.get(_previous_active or "") or kcs.default
        kcs.remove(kc)
    _previous_active = None

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
