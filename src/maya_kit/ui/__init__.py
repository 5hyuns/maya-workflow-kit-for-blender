# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya-style UI: Channel Box, Layer Editor, Attribute Editor, Outliner (3D View
sidebar), menu bar + menu sets, Status Line (top bar), Shelf (strip under it).

See  for what is P/W/C in Blender's Python UI.
"""

from . import attribute_editor, channel_box, layer_editor, menu_sets, outliner, shelf, status_line

_modules = (channel_box, layer_editor, attribute_editor, outliner, menu_sets, status_line, shelf)


def register():
    for mod in _modules:
        mod.register()


def unregister():
    for mod in reversed(_modules):
        mod.unregister()
