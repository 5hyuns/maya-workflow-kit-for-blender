# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya Kit: make Blender feel like Maya (keymap, interaction, UI, concepts).

Shipped as one Blender 4.2+ extension (docs/user_decisions.md #3). The same
source also builds a legacy add-on zip, which is why ``bl_info`` is kept;
extensions read ``blender_manifest.toml`` instead and ignore it.

Each feature area is a sub-package with its own ``register()`` /
``unregister()``. Order matters: preferences first (others may read them),
then the Blender-preferences preset, keymap last (keymap items reference
operators registered before it). ``CORE`` stays registered; ``MODE`` is
Maya mode, switched on and off at run time by ``switch`` (step 60).
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

from . import (preferences, switch, prefs_preset, operators, ui, command_line, marking, theme,
               app_template, first_start, keymap)

# Always registered: the preferences and the Maya / Blender switch (docs/steps/step_60.md).
CORE = (preferences, switch)
# "Maya mode": registered while the add-on preference ``maya_mode`` is on; switching to
# Blender unregisters them, which puts back everything they changed.
MODE = (prefs_preset, operators, ui, command_line, marking, theme, app_template, first_start, keymap)


def register():
    for mod in CORE:
        mod.register()
    if switch.is_on():
        if switch.has_snapshot() and not switch.maya_state_saved():
            switch.forget_snapshot()    # stale: kept from before a disable, the user may have changed things
        if not switch.has_snapshot():
            switch.take_snapshot()      # the user's values before Maya mode (complete revert)
        switch.register_mode()
        switch._registered[0] = True
    elif switch.has_snapshot():
        switch.finish_interrupted()     # a switch to Blender was interrupted (crash): finish it


def unregister():
    if switch._registered[0]:
        switch.unregister_mode()
        switch._registered[0] = False
        # Disable / Remove gives the user's settings back. The snapshot file stays: Blender also
        # unregisters add-ons when it quits, and the next start in Maya mode still needs it.
        switch.restore_snapshot(delete=False)
    for mod in reversed(CORE):
        mod.unregister()
