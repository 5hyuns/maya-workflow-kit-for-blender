# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya Kit app template ("MayaKit"): Maya General layout in startup.blend.

Installed by the Maya Kit extension (Preferences > Add-ons > Maya Kit >
Install Maya Layout). The template only holds the layout; all behaviour is in
the extension, which is enabled here if it is installed but turned off.
"""

import addon_utils


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


def unregister():
    pass
