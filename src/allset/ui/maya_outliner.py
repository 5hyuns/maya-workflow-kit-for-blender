# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya Outliner chrome on Blender's Outliner.

Maya's Outliner has a menu bar Display / Show / Help and a search field.
Outliners set up the Maya way (the Maya Workflow Kit layout and Windows > Outliner:
View Layer mode, no collection rows; ``is_maya_outliner``) get that header: ``OUTLINER_HT_header.draw`` is swapped
while the kit is enabled and restored on unregister; other Outliners draw as usual. The rows of an Outliner the kit
set up are the kit's own (``ui/outliner_tree.py``: joints as rows under their parent joint, Maya's startup cameras
and default sets); Display > Shapes adds the shape rows, Show filters the object types.
"""

import bpy

from . import chrome, own_draw

HELP_URL = "https://docs.blender.org/manual/en/5.2/editors/outliner/index.html"
MENU_BAR = (("Display", "ALLSET_MT_outliner_display"), ("Show", "ALLSET_MT_outliner_show"),
            ("Help", "ALLSET_MT_outliner_help"))


def is_maya_outliner(space):
    """The Maya header goes on this Outliner: View Layer mode, no collection rows, and either no object contents (how
    the kit sets it up) or Display > Shapes on in an Outliner the kit set up — no mode column, and no render or
    exclude column (``mark``: the kit turns the exclude column off), which a plain Blender Outliner shows."""
    if (space is None or space.type != 'OUTLINER' or space.display_mode != 'VIEW_LAYER'
            or space.use_filter_collection):
        return False
    return not space.use_filter_object_content or not (
        space.show_mode_column or (space.show_restrict_column_render and space.show_restrict_column_enable))


def mark(space):
    """The first time the kit claims a Maya Outliner: the exclude column (unused: no collection rows) goes off to
    mark it as the kit's, and Blender's select / eye / render columns go on once; the Display menu keeps later
    choices."""
    if space.show_restrict_column_enable:
        space.show_restrict_column_enable = False
        space.show_restrict_column_select = True
        space.show_restrict_column_hide = True
        space.show_restrict_column_render = True


def setup(space):
    """Maya Outliner filters (DAG only, from the world; no mode column) with Blender's select / eye / render columns."""
    space.display_mode = 'VIEW_LAYER'
    space.use_filter_object_content = False
    space.use_filter_collection = False
    space.use_filter_children = True
    space.show_restrict_column_enable = True
    mark(space)
    space.show_mode_column = False      # Maya has no mode column (Blender shows it in edit mode)
    space.use_sort_alpha = False        # Maya lists the DAG in creation order, startup cameras first
    from . import outliner_tree         # the kit draws the rows (joints under their skeleton, #348)
    outliner_tree.hide_rows(space)


class ALLSET_MT_outliner_display(bpy.types.Menu):
    """Maya Outliner Display menu"""
    bl_label = "Display"

    def draw(self, context):
        sp, lay = context.space_data, self.layout
        lay.prop(sp, "use_filter_children", text="Children (DAG Hierarchy)")
        lay.prop(sp, "use_sort_alpha", text="Sort Alphabetically")
        lay.prop(sp, "show_restrict_column_select", text="Selectable Column")
        lay.prop(sp, "show_restrict_column_hide", text="Visibility Column")
        lay.prop(sp, "show_restrict_column_render", text="Render Column")
        lay.separator()
        # Maya Display > Shapes: a shape row (pCubeShape1) under each transform
        lay.prop(sp, "use_filter_object_content", text="Shapes")


class ALLSET_MT_outliner_show(bpy.types.Menu):
    """Maya Outliner Show menu: object type filters"""
    bl_label = "Show"

    def draw(self, context):
        sp, lay = context.space_data, self.layout
        from . import outliner_tree
        if outliner_tree.is_tree(sp):
            # the kit tree hides Blender's rows with Objects off: Maya's Show All turns every type back on
            lay.operator("allset.outliner_tree_show_all", text="Show All")
            col = lay.column()
        else:
            lay.prop(sp, "use_filter_object", text="Objects")
            col = lay.column()
            col.active = sp.use_filter_object
        for prop, label in (("use_filter_object_mesh", "Geometry"), ("use_filter_object_armature", "Joints"),
                            ("use_filter_object_empty", "Groups / Locators"), ("use_filter_object_light", "Lights"),
                            ("use_filter_object_camera", "Cameras"), ("use_filter_object_others", "Others")):
            col.prop(sp, prop, text=label)


class ALLSET_MT_outliner_help(bpy.types.Menu):
    bl_label = "Help"

    def draw(self, context):
        self.layout.operator("wm.url_open", text="Help on Outliner").url = HELP_URL


def _draw(self, context):
    space = context.space_data
    if not is_maya_outliner(space):
        return own_draw.original("OUTLINER_HT_header", _draw)(self, context)
    layout = self.layout
    from . import maya_dock      # Maya's dotted handle: tear the Outliner off / dock it back
    layout.operator("allset.dock_handle", text=maya_dock.HANDLE[:8], emboss=False)
    chrome.menu_bar(layout, MENU_BAR)
    layout.prop(space, "filter_text", text="", icon='VIEWZOOM', placeholder="Search...")


classes = (ALLSET_MT_outliner_display, ALLSET_MT_outliner_show, ALLSET_MT_outliner_help)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    own_draw.swap("OUTLINER_HT_header", _draw)   # Blender's own draw only


def unregister():
    own_draw.restore("OUTLINER_HT_header", _draw)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
