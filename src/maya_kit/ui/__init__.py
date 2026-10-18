# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya-style UI: Channel Box, Layer Editor, Attribute Editor, Outliner (3D View
sidebar), menu bar + menu sets, Status Line (top bar), Shelf (strip under it), Time
Slider + Range Slider (Timeline header), viewport panel menus (3D View header), Maya grid, view furniture and selection wire (3D View),
Tool Box (3D View toolbar) and the dock-only sidebar.

See  for what is P/W/C in Blender's Python UI.
"""

from . import (attribute_editor, input_line, graph_editor, hypershade, light_editor, render_view, channel_box, dock_tabs, layer_editor, maya_grid, maya_outliner, menu_sets, notices, outliner,
               in_view, manipulator, mesh_tools, modeling_toolkit, uv_toolkit, paint_weights, panel_menus, set_driven_key, shelf, selection_wire, status_line, time_slider,
               toolbox, view_furniture, view_message, range_bar)

_modules = (notices, input_line, channel_box, layer_editor, attribute_editor, outliner, menu_sets, status_line, shelf,
            time_slider, panel_menus, maya_grid, view_furniture, selection_wire, toolbox, dock_tabs, maya_outliner,
            paint_weights, manipulator, set_driven_key, modeling_toolkit, mesh_tools, in_view, uv_toolkit, hypershade, light_editor, render_view, graph_editor,
            view_message, range_bar)


def register():
    for mod in _modules:
        mod.register()


def unregister():
    for mod in reversed(_modules):
        mod.unregister()
