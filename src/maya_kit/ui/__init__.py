# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya-style UI: Channel Box, Layer Editor (3D View sidebar), later Status Line etc.

See  for what is P/W/C in Blender's Python UI.
"""

from . import channel_box, layer_editor

_modules = (channel_box, layer_editor)


def register():
    for mod in _modules:
        mod.register()


def unregister():
    for mod in reversed(_modules):
        mod.unregister()
