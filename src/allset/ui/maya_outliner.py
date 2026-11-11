# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya Outliner chrome on Blender's Outliner.

Maya's Outliner has a menu bar Display / Show / Help and a search field.
Outliners set up the Maya way (the Maya Workflow Kit layout and Windows > Outliner:
View Layer mode, no collection rows, no object contents; ``is_maya_outliner``) get that header:
``OUTLINER_HT_header.draw`` is swapped while the kit is enabled and restored on unregister; other
Outliners draw as usual. The rows themselves are Blender's (the C list): Maya's grey camera rows
(persp/top/front/side) and default sets have no Blender objects behind them.

Display > Shapes shows Blender's object contents (a skeleton's joints, mesh data, materials ...) and the Outliner
keeps the Maya header, so Shapes is switched off in the same menu. While Shapes is on, picking a joint opens the
tree down to it, like Maya's Outliner shows the picked joint (Blender's Outliner > Show Active, once per pick).
"""

import time

import bpy
from bpy.app.handlers import persistent

from . import chrome, own_draw

HELP_URL = "https://docs.blender.org/manual/en/5.2/editors/outliner/index.html"
MENU_BAR = (("Display", "ALLSET_MT_outliner_display"), ("Show", "ALLSET_MT_outliner_show"),
            ("Help", "ALLSET_MT_outliner_help"))


def is_maya_outliner(space):
    """The Maya header goes on this Outliner: View Layer mode, no collection rows, and either no object contents (how
    the kit sets it up) or Display > Shapes on in an Outliner the kit set up — no mode column and no render toggle,
    which the Maya menus can't change and a plain Blender Outliner shows."""
    if (space is None or space.type != 'OUTLINER' or space.display_mode != 'VIEW_LAYER'
            or space.use_filter_collection):
        return False
    return not space.use_filter_object_content or not (space.show_mode_column or space.show_restrict_column_render)


def _kit_tree(space):
    from . import outliner_tree
    return outliner_tree.is_tree(space)


def shows_dag_only(space):
    """A Maya Outliner with Blender's rows, Shapes off: one row per object, the rows the kit draws names and sets
    over."""
    return is_maya_outliner(space) and not space.use_filter_object_content and not _kit_tree(space)


def shapes_shown(space):
    """A Maya Outliner with Blender's rows and Display > Shapes on: Blender's rows list the joints under their
    skeleton."""
    return is_maya_outliner(space) and space.use_filter_object_content and not _kit_tree(space)


def setup(space):
    """Maya Outliner filters (DAG only, from the world; no eye / mode column: Maya hides with H)."""
    space.display_mode = 'VIEW_LAYER'
    space.use_filter_object_content = False
    space.use_filter_collection = False
    space.use_filter_children = True
    space.show_restrict_column_render = False
    space.show_restrict_column_hide = False
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
        lay.prop(sp, "show_restrict_column_hide", text="Visibility Column")
        lay.separator()
        # Maya Display > Shapes: Blender's object contents (joints, mesh data ...); the Maya menus stay
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


# --- a picked joint is shown in the tree (Shapes on) ----------------------------------------------------------

OUTLINER_GRACE = 1.0      # s: a selection change this soon after an Outliner click / walk / box came from the Outliner
_last = {"key": None, "op": (0, 0.0, False)}   # last picked joint; newest registered operator (pointer, seen, Outliner)
STATS = {"revealed": 0}  # Outliners opened down to a picked joint (GUI tests read it)


def picked_joint(view_layer):
    """(skeleton name, mode, joint name) of the joint picked last — the active bone while it is selected, in Pose or
    Edit Mode — else None (Object Mode picks the object)."""
    ob = getattr(getattr(view_layer, "objects", None), "active", None)
    if ob is None or ob.type != 'ARMATURE':
        return None
    if ob.mode == 'POSE':
        bone = ob.data.bones.active
        pb = ob.pose.bones.get(bone.name) if bone is not None and ob.pose is not None else None
        from .channel_box import bone_selected
        return (ob.name, 'POSE', bone.name) if pb is not None and bone_selected(pb) else None
    if ob.mode == 'EDIT':
        eb = ob.data.edit_bones.active
        return (ob.name, 'EDIT', eb.name) if eb is not None and (eb.select or eb.select_head) else None
    return None


def _from_outliner(wm, now):
    """The newest registered operator is an Outliner one (click, walk, box) seen less than OUTLINER_GRACE ago: the
    selection was made in the Outliner, where the row already shows. The kit's switch to Pose Mode after a
    skeleton row click registers nothing, so it counts too."""
    ops = wm.operators
    newest = ops[-1] if len(ops) else None
    ptr = newest.as_pointer() if newest is not None else 0
    if ptr != _last["op"][0]:
        _last["op"] = (ptr, now, newest is not None and newest.bl_idname.startswith("OUTLINER_OT_"))
    _ptr, seen, outliner_op = _last["op"]
    return outliner_op and now - seen < OUTLINER_GRACE


def _playing(wm):
    return any(w.screen is not None and w.screen.is_animation_playing for w in wm.windows)


@persistent
def _on_depsgraph(scene=None, depsgraph=None):
    """A new joint picked (not in the Outliner, not during playback): open the Shapes Outliners down to it once, from
    a timer (no operators in a depsgraph handler; the Outliner has redrawn the new mode's rows by then)."""
    context = bpy.context
    wm = getattr(context, "window_manager", None)
    if wm is None:
        return
    from_outliner = _from_outliner(wm, time.monotonic())
    view_layer = getattr(depsgraph, "view_layer", None) or getattr(context, "view_layer", None)
    key = picked_joint(view_layer)
    if key == _last["key"]:
        return
    _last["key"] = key
    if key is None or from_outliner or _playing(wm):
        return
    if not bpy.app.timers.is_registered(_reveal):
        bpy.app.timers.register(_reveal, first_interval=0.0)


def reveal(context):
    """Every Maya Outliner with Shapes on: Blender's Show Active (opens the rows above the active joint, scrolls to
    it). Returns how many Outliners did."""
    done = 0
    for window in context.window_manager.windows:
        screen = window.screen
        for area in screen.areas if screen is not None else ():
            if area.type != 'OUTLINER' or not shapes_shown(area.spaces.active):
                continue
            region = next((r for r in area.regions if r.type == 'WINDOW'), None)
            if region is None:
                continue
            try:
                with context.temp_override(window=window, screen=screen, area=area, region=region):
                    if 'FINISHED' in bpy.ops.outliner.show_active():
                        done += 1
            except RuntimeError:
                pass
    return done


def _reveal():
    try:
        STATS["revealed"] += reveal(bpy.context)
    except (AttributeError, ReferenceError, RuntimeError):
        pass
    return None


classes = (ALLSET_MT_outliner_display, ALLSET_MT_outliner_show, ALLSET_MT_outliner_help)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    own_draw.swap("OUTLINER_HT_header", _draw)   # Blender's own draw only
    _last.update(key=None, op=(0, 0.0, False))
    bpy.app.handlers.depsgraph_update_post.append(_on_depsgraph)


def unregister():
    while _on_depsgraph in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(_on_depsgraph)
    if bpy.app.timers.is_registered(_reveal):
        bpy.app.timers.unregister(_reveal)
    _last.update(key=None, op=(0, 0.0, False))
    STATS["revealed"] = 0
    own_draw.restore("OUTLINER_HT_header", _draw)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
