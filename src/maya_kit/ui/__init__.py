# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya-style UI: Channel Box, Layer Editor, Attribute Editor, Outliner (3D View
sidebar), menu bar + menu sets, Status Line (top bar), Shelf (strip under it), Time
Slider + Range Slider (Timeline header), viewport panel menus (3D View header), Maya grid and view furniture (3D View).

See research/blender/api_limits.md for what is P/W/C in Blender's Python UI.
"""

from . import (attribute_editor, channel_box, layer_editor, maya_grid, menu_sets, outliner, panel_menus, shelf,
               status_line, time_slider, view_furniture)

_modules = (channel_box, layer_editor, attribute_editor, outliner, menu_sets, status_line, shelf,
            time_slider, panel_menus, maya_grid, view_furniture)


def register():
    for mod in _modules:
        mod.register()


def unregister():
    for mod in reversed(_modules):
        mod.unregister()
