# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya main menu bar and menu sets (Modeling/Rigging/Animation/FX/Rendering).

 (:170-192): the common menus are always shown,
the menu set dropdown swaps the menus after them. Structure from
``menu_data`` (generated from ), Blender actions from
``menu_map``; unmapped items are drawn greyed out. Design: 
「계획」 2.

One ``Menu`` class per Maya menu and submenu is built from the data at import
time. ``menu_idname(maya_name)`` is the public name for other UI (hotbox).
"""

import json

import bpy
from bpy.props import BoolProperty, StringProperty

from . import menu_data, menu_map

COMMON_SET = "commonMenuSet"
ALWAYS = "(always visible)"
DEFAULT_SET = "modelingMenuSet"

# Menu set dropdown items (Maya setting currentMenuBarTab, ui_layout.md:182-183).
SET_ITEMS = tuple((sid, label, f"Maya {label} menu set")
                  for sid, label, _menus in menu_data.MENU_SETS if sid != COMMON_SET)
# Plugin menus (MASH, Bifrost, Boss) are listed in the sets but have no data: skipped.
_SET_MENUS = {sid: tuple(m for m in menus if m in menu_data.MENUS)
              for sid, _label, menus in menu_data.MENU_SETS}
_ALWAYS_MENUS = tuple(n for n, m in menu_data.MENUS.items() if m[1] == ALWAYS)


def menu_idname(maya_name):
    return f"MAYAKIT_MT_{maya_name}"


def menus_for_set(set_id):
    """Maya menu names shown in the menu bar for ``set_id``, left to right."""
    return _SET_MENUS[COMMON_SET] + _SET_MENUS.get(set_id, ()) + _ALWAYS_MENUS


def iter_items(items=None, prefix=""):
    """Yield (label path, item) for every entry below ``items`` (all menus if None)."""
    if items is None:
        for label, _set, _src, its in menu_data.MENUS.values():
            yield from iter_items(its, label)
        return
    for path, it in children(items, prefix):
        if path is None:
            continue
        yield path, it
        kids = sub_items(path, it)
        if kids:
            yield from iter_items(kids, path)


def sub_items(path, it):
    """Children of a menu entry: Maya's run-time ones (``menu_map.CHILDREN``), else the data's."""
    return menu_map.CHILDREN.get(path) or (it[1] if len(it) > 1 else None)


def children(items, prefix):
    """(path, item) per direct entry; path None for dividers. A label repeated
    among siblings gets "#2", "#3" (Select > Components for polygons, curves,
    surfaces). ``menu_map.EXTRA`` items follow the entry they are attached to."""
    seen = {}
    for it in items:
        if it[0] == "-":
            yield None, it
            continue
        n = seen[it[0]] = seen.get(it[0], 0) + 1
        path = f"{prefix}/{it[0]}" + (f"#{n}" if n > 1 else "")
        yield path, it
        for extra in menu_map.EXTRA.get(path, ()):
            yield (None if extra[0] == "-" else f"{prefix}/{extra[0]}"), extra


def current_set(context=None):
    from .. import preferences
    try:
        return preferences.get(context).menu_set
    except KeyError:  # add-on preferences not registered (disable in progress)
        return DEFAULT_SET


# --- items ---------------------------------------------------------------------

def draw_item(layout, path, label):
    """Draw one Maya menu item: its Blender action, or greyed out."""
    draw_spec(layout, label, menu_map.spec(path), path)


def draw_spec(layout, label, s, path, icon='NONE'):
    """Draw a normalised action (``menu_map.normalize``); None = greyed out with
    ``path`` (the Maya menu path) in the tooltip."""
    if s is None:
        layout.operator(MAYAKIT_OT_menu_unavailable.bl_idname, text=label, icon=icon).item = path
        return
    kind, target, props = s
    if kind == "menu":
        layout.menu(target, text=label, icon=icon)
    elif kind == "pie":
        layout.operator("wm.call_menu_pie", text=label + " ▸", icon=icon).name = target
    elif kind == "tool":
        op = layout.operator(MAYAKIT_OT_menu_tool.bl_idname, text=label, icon=icon)
        op.tool = target
        op.edit = props["edit"]
    elif kind == "v3d":
        op = layout.operator(MAYAKIT_OT_menu_run.bl_idname, text=label, icon=icon)
        op.op = target
        op.props = json.dumps(props)
    else:
        op = layout.operator(target, text=label, icon=icon)
        for key, value in props.items():
            setattr(op, key, value)


def _draw_items(layout, items, prefix, submenus):
    for path, it in children(items, prefix):
        if path is None:
            layout.separator()
            if it[1]:
                layout.label(text=it[1])
            continue
        if sub_items(path, it) and path not in menu_map.MAP:
            layout.menu(submenus[path], text=it[0])
        else:
            draw_item(layout, path, it[0])


def _make_menu(idname, label, prefix, items, top_label=None):
    submenus = {}
    classes = []
    for path, it in iter_items(items, prefix):
        if sub_items(path, it) and path not in submenus and path not in menu_map.MAP:
            submenus[path] = f"{idname}_{len(submenus)}"
    # Build the submenu classes (each draws its own children).
    for path, sub_id in submenus.items():
        node = _find(items, prefix, path)
        classes.append(_menu_class(sub_id, node[0], path, sub_items(path, node), submenus))
    classes.insert(0, _menu_class(idname, label, prefix, items, submenus, top_label))
    return classes


def _find(items, prefix, path):
    for p, it in iter_items(items, prefix):
        if p == path:
            return it
    raise KeyError(path)


def _menu_class(idname, label, prefix, items, submenus, top_label=None):
    blender = menu_map.BLENDER_MENU.get(top_label) if top_label else None

    def draw(self, context):
        layout = self.layout
        _draw_items(layout, items, prefix, submenus)
        if blender:
            layout.separator()
            layout.menu(blender[0], text=blender[1], icon='BLENDER')

    return type(idname, (bpy.types.Menu,), {
        "bl_idname": idname, "bl_label": label, "draw": draw,
        "__doc__": f"Maya menu: {prefix}"})


# --- operators -----------------------------------------------------------------

class MAYAKIT_OT_menu_unavailable(bpy.types.Operator):
    """Maya menu item without a Blender equivalent in Maya Kit (always greyed out)"""
    bl_idname = "maya_kit.menu_unavailable"
    bl_label = "Not Available"
    bl_options = {'INTERNAL'}

    item: StringProperty(options={'SKIP_SAVE'})

    @classmethod
    def poll(cls, context):
        return False

    @classmethod
    def description(cls, context, props):
        return f"Maya: {props.item}\nNo Blender equivalent in Maya Kit yet"

    def execute(self, context):
        return {'CANCELLED'}


def _call(op_id, props):
    mod, name = op_id.split(".")
    return getattr(getattr(bpy.ops, mod), name)('INVOKE_DEFAULT', **props)


class MAYAKIT_OT_menu_run(bpy.types.Operator):
    """Run a Blender operator in the largest 3D View (for Maya menu items)"""
    bl_idname = "maya_kit.menu_run"
    bl_label = "Run in 3D View"
    bl_options = {'INTERNAL'}

    op: StringProperty(options={'SKIP_SAVE'})
    props: StringProperty(default="{}", options={'SKIP_SAVE'})

    @classmethod
    def description(cls, context, props):
        try:
            mod, name = props.op.split(".")
            return getattr(getattr(bpy.ops, mod), name).get_rna_type().description
        except (ValueError, AttributeError, KeyError):
            return ""

    def execute(self, context):
        from .status_line import main_view3d
        area, region = main_view3d(context.window.screen if context.window else None)
        if area is None:
            self.report({'ERROR'}, "No 3D View to run this in")
            return {'CANCELLED'}
        try:
            with context.temp_override(window=context.window, area=area, region=region):
                _call(self.op, json.loads(self.props))
        except RuntimeError as ex:  # poll failed etc.
            self.report({'ERROR'}, str(ex).strip())
            return {'CANCELLED'}
        return {'FINISHED'}


class MAYAKIT_OT_menu_tool(bpy.types.Operator):
    """Switch the 3D View tool (for Maya menu items that pick a tool)"""
    bl_idname = "maya_kit.menu_tool"
    bl_label = "Set Tool"
    bl_options = {'INTERNAL'}

    tool: StringProperty(options={'SKIP_SAVE'})
    edit: BoolProperty(description="Enter mesh edit (component) mode first", options={'SKIP_SAVE'})

    def execute(self, context):
        ob = context.active_object
        if self.edit:
            if ob is None or ob.type != 'MESH':
                self.report({'ERROR'}, "Select a mesh first")
                return {'CANCELLED'}
            if context.mode != 'EDIT_MESH':
                bpy.ops.object.mode_set(mode='EDIT')
        try:
            bpy.ops.wm.tool_set_by_id(name=self.tool, space_type='VIEW_3D')
        except RuntimeError as ex:
            self.report({'ERROR'}, str(ex).strip())
            return {'CANCELLED'}
        return {'FINISHED'}


class MAYAKIT_MT_ui_elements(bpy.types.Menu):
    """Maya Windows > UI Elements (startup/Maya-83, ui_layout.md:190-191)"""
    bl_idname = "MAYAKIT_MT_ui_elements"
    bl_label = "UI Elements"

    def draw(self, context):
        from .. import preferences
        prefs = preferences.get(context)
        layout = self.layout
        layout.prop(prefs, "maya_top_bar")
        layout.prop(prefs, "show_status_line")
        from .shelf import strip_area
        layout.operator("maya_kit.shelf_strip_toggle", text="Shelf",
                        icon='CHECKBOX_HLT' if strip_area(context.screen) else 'CHECKBOX_DEHLT')
        layout.prop(prefs, "show_command_line")
        layout.prop(prefs, "show_help_line")


class MAYAKIT_MT_menu_bar(bpy.types.Menu):
    """The Maya menu bar folded into one menu (header menus collapsed)"""
    bl_idname = "MAYAKIT_MT_menu_bar"
    bl_label = "Menus"

    def draw(self, context):
        draw_menu_bar(self.layout, context, collapsed=True)


def draw_menu_bar(layout, context, collapsed=False):
    """Blender logo menu, Maya common menus, menu set dropdown, set menus, Cache, Help."""
    from .. import preferences
    prefs = preferences.get(context)
    if collapsed:
        layout.menu("TOPBAR_MT_blender", text="Blender")
    else:
        layout.menu("TOPBAR_MT_blender", text="", icon='BLENDER')
    set_id = prefs.menu_set
    for name in _SET_MENUS[COMMON_SET]:
        layout.menu(menu_idname(name))
    if collapsed:
        layout.separator()
        layout.prop(prefs, "menu_set", text="")
    else:
        sub = layout.row()
        sub.ui_units_x = 5.5
        sub.prop(prefs, "menu_set", text="")
    for name in _SET_MENUS.get(set_id, ()) + _ALWAYS_MENUS:
        layout.menu(menu_idname(name))


_menu_classes = []
for _name, (_label, _set, _src, _items) in menu_data.MENUS.items():
    _menu_classes.extend(_make_menu(menu_idname(_name), _label, _label, _items, top_label=_label))

classes = (MAYAKIT_OT_menu_unavailable, MAYAKIT_OT_menu_run, MAYAKIT_OT_menu_tool,
           MAYAKIT_MT_ui_elements, MAYAKIT_MT_menu_bar, *_menu_classes)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
