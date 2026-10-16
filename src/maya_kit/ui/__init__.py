# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya-style UI: Channel Box, Layer Editor (3D View sidebar), menu bar + menu sets,
Status Line (top bar).

See  for what is P/W/C in Blender's Python UI.
"""

from . import channel_box, layer_editor, menu_sets, status_line

_modules = (channel_box, layer_editor, menu_sets, status_line)


def register():
    for mod in _modules:
        mod.register()


def unregister():
    for mod in reversed(_modules):
        mod.unregister()
