# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya-style UI: Channel Box, Layer Editor, Attribute Editor, Outliner (3D View
sidebar), menu bar + menu sets, Status Line (top bar), Shelf (strip under it), Time
Slider + Range Slider (Timeline header), viewport panel menus (3D View header), Maya grid, view furniture and selection wire (3D View),
Tool Box (3D View toolbar) and the dock-only sidebar.

See research/blender/api_limits.md for what is P/W/C in Blender's Python UI.
"""

from . import (attribute_editor, editor_chrome, file_project, render_settings, script_editor, input_line, graph_editor, hypershade, light_editor, render_view, channel_box, dock_tabs, layer_editor, maya_grid, maya_outliner, menu_sets, outliner_sets, notices, outliner,
               in_view, manipulator, mesh_tools, modeling_toolkit, uv_toolkit, paint_weights, panel_menus, set_driven_key, shelf, selection_wire, status_line, time_slider,
               tool_settings, toolbox, view_furniture, view_message, range_bar, status_icons, panel_toolbar)

_modules = (status_icons, notices, input_line, channel_box, layer_editor, attribute_editor, outliner, menu_sets, file_project, status_line, shelf,
            time_slider, panel_menus, panel_toolbar, maya_grid, view_furniture, selection_wire, toolbox, dock_tabs, maya_outliner, outliner_sets,
            paint_weights, manipulator, set_driven_key, modeling_toolkit, mesh_tools, in_view, uv_toolkit, hypershade, light_editor, render_view, graph_editor, editor_chrome, render_settings, script_editor,
            view_message, range_bar, tool_settings)


def register():
    for mod in _modules:
        mod.register()


def unregister():
    for mod in reversed(_modules):
        mod.unregister()
