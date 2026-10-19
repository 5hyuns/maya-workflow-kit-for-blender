# SPDX-License-Identifier: GPL-3.0-or-later
"""Set Driven Key window drawn in the dock under the Channel Box.

Layout of Maya's window (): a "Driver" bar, node list |
attribute list; a "Driven" bar, node list | attribute list; buttons Key · Load Driver · Load Driven · Close.
Drawn by the Layer Editor panel while the window is open (its place in the dock), so the Channel Box stays
above it for posing. The lists are fixed-height scrolling UILists like Maya's (all ten channels in plain
rows pushed the buttons out of the sidebar, GUI shot step 62).
"""

import bpy

from ..operators import driven_key as sdk

ROWS = 4
BAR = "Driver", "Driven"
HELP = ("Pose in the Channel Box, then Key",)


class ALLSET_UL_sdk_attrs(bpy.types.UIList):
    """Attribute rows: a click picks (Driven: Ctrl adds); selected rows are drawn pressed."""

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index=0):
        driver = active_propname == "driver_items_index"
        selected = item.key == data.driver_attr if driver else item.key in sdk.driven_keys(data)
        op = layout.operator("allset.sdk_pick", text=item.label, emboss=selected, depress=selected)
        op.which, op.key = ('DRIVER' if driver else 'DRIVEN'), item.key

    def draw_filter(self, context, layout):
        pass


class ALLSET_UL_sdk_nodes(bpy.types.UIList):
    """Driven node rows (the node whose attributes the right list shows is pressed)."""

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index=0):
        node = sdk.node_of(item.object, item.bone)
        selected = index == data.driven_index
        op = layout.operator("allset.sdk_pick", text=node.name if node else "?", emboss=selected,
                             depress=selected)
        op.which, op.index = 'NODE', index

    def draw_filter(self, context, layout):
        pass


def _bar(layout, text):
    box = layout.box()
    box.scale_y = 0.6
    box.label(text=text)


def draw(layout, context):
    st = sdk.state(context)
    layout.separator(type='LINE')
    _bar(layout, BAR[0])
    split = layout.split(factor=0.5, align=True)
    left = split.box().column(align=True)
    drv = sdk.driver_node(st)
    if drv is not None:
        left.label(text=drv.name)
    split.template_list("ALLSET_UL_sdk_attrs", "driver", st, "driver_items", st, "driver_items_index",
                        rows=ROWS, maxrows=ROWS)

    _bar(layout, BAR[1])
    split = layout.split(factor=0.5, align=True)
    split.template_list("ALLSET_UL_sdk_nodes", "driven_nodes", st, "driven", st, "driven_index",
                        rows=ROWS, maxrows=ROWS)
    split.template_list("ALLSET_UL_sdk_attrs", "driven", st, "driven_items", st, "driven_items_index",
                        rows=ROWS, maxrows=ROWS)

    # Maya's one button row (Key · Load Driver · Load Driven · Close) as a 2 x 2 grid in the same reading
    # order: four buttons in one sidebar row cut "Load Driver" to "Load Dr..." (GUI shot, step 62).
    grid = layout.grid_flow(row_major=True, columns=2, even_columns=True, align=True)
    grid.operator("allset.sdk_key", text="Key")
    grid.operator("allset.sdk_load", text="Load Driver").which = 'DRIVER'
    grid.operator("allset.sdk_load", text="Load Driven").which = 'DRIVEN'
    grid.operator("allset.sdk_close", text="Close")
    from . import chrome
    chrome.wrapped(layout, HELP, alignment='LEFT')


classes = (ALLSET_UL_sdk_attrs, ALLSET_UL_sdk_nodes)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
