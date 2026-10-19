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
from bpy.app.handlers import persistent

from .. import compat

KEYCONFIG_NAME = "Maya-style"   # descriptive, not a brand ()

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


TARGET_VERSION = compat.TARGET   #  


def generate_data():
    """IC data with the Maya patches applied (fresh list each call). Strict on Blender 4.5 ();
    elsewhere IC differences are collected in ``patch.DRIFT``."""
    from . import ic_data, maya_patches, patch
    patch.STRICT = compat.IS_TARGET
    patch.DRIFT.clear()
    data = maya_patches.apply(ic_data.generate())
    if patch.DRIFT:
        print(f"Allset: {len(patch.DRIFT)} keymap patches don't apply to Blender {bpy.app.version_string} "
              "(made for 4.5):", *patch.DRIFT[:20], sep="\n  ")
    return data


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


# A GUI template switch (File > New > Allset, Start in Maya Layout) sets the active keyconfig back to "Blender"
# (stored name too), after load_post, while the preferences and the add-on stay; load_pre doesn't run for it (checked,
# ). Before step 115 the template's own __init__.py re-activated Maya; the template now carries
# no code, so the keymap module does the same: in the Allset template, Blender's default keyconfig -> Maya (a keymap
# the user picked other than Blender's default is left alone).
def wants_maya(app_template, active_name):
    from ..app_template import TEMPLATE_ID
    return app_template == TEMPLATE_ID and active_name in (None, "Blender")


def _reactivate():
    kcs = bpy.context.window_manager.keyconfigs
    if wants_maya(bpy.context.preferences.app_template, kcs.active.name if kcs.active else None):
        activate()
    return None


@persistent
def _keep_keyconfig(*_args):
    _reactivate()
    if not bpy.app.timers.is_registered(_reactivate):
        bpy.app.timers.register(_reactivate, first_interval=0.0, persistent=True)


class ALLSET_OT_keymap_activate(bpy.types.Operator):
    """Use the Maya keymap (it is not listed in the keymap preset menu)"""
    bl_idname = "allset.keymap_activate"
    bl_label = "Activate Maya Keymap"
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        activate()
        return {'FINISHED'}


classes = (ALLSET_OT_keymap_activate,)


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
        # Not in background sessions: `blender --command extension install-file --enable`
        # saves this flag but not the active keyconfig, so the first GUI start stayed on
        # the Blender keymap (found by tools/release_check.py, ).
        if not bpy.app.background:
            prefs.keymap_auto_activated = True
    bpy.app.handlers.load_post.append(_keep_keyconfig)


def unregister():
    global _previous_active
    if _keep_keyconfig in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_keep_keyconfig)
    if bpy.app.timers.is_registered(_reactivate):
        bpy.app.timers.unregister(_reactivate)
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
