# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya Shelf: factory shelves as Blender operator buttons, user shelves of Python
scripts, drawn under the Status Line in a thin "Maya strip" area.

 ( behaviour, tab order, buttons);
 #11. Design:  「계획」.

- The strip is an Image Editor area marked by the hidden Mask ``.MayaKitStrip``
  (``space.mask``): its header row draws the Status Line, its tool header row the
  shelf. ``IMAGE_HT_header.draw`` / ``IMAGE_HT_tool_header.draw`` are swapped while
  the add-on is enabled and restored on unregister; unmarked Image Editors draw as
  usual.
- Factory buttons: ``shelf_data`` (generated) + ``shelf_map`` (Blender action, icon),
  run with ``marking.modal.run_action``. Click = command, double-click (or Ctrl+click)
  = options (Adjust Last Operation of that run), like Maya's doubleClickCommand.
- User shelves: ``shelves.json`` in the extension's user directory; a button runs
  its Python script (Maya ``-sourceType python``).
"""

import json
import os
import traceback

import bpy
from bpy.props import BoolProperty, IntProperty, StringProperty

from . import shelf_data, shelf_map

MARKER = ".MayaKitStrip"
USER_PREFIX = "USER:"
DEFAULT_USER = {"shelves": [{"name": "Custom", "buttons": []}]}
STRIP_PX = 68          # header + tool header rows at UI scale 1 (checked,  「계획」 1)
_user = {}             # cached shelves.json content


# --- storage -------------------------------------------------------------------------------------

def _package():
    return __package__.rsplit(".", 1)[0]   # the add-on package (``...maya_kit``)


def store_path():
    """``shelves.json`` in the extension's user directory (legacy add-on: user config)."""
    try:
        base = bpy.utils.extension_path_user(_package(), create=True)
    except (ValueError, AttributeError):
        base = bpy.utils.user_resource('CONFIG', path="maya_kit", create=True)
    return os.path.join(base, "shelves.json")


def user_data():
    if not _user:
        data = None
        path = store_path()
        if os.path.isfile(path):
            try:
                with open(path, encoding="utf-8") as fh:
                    data = json.load(fh)
            except (OSError, ValueError):
                traceback.print_exc()
        if not isinstance(data, dict) or not isinstance(data.get("shelves"), list):
            data = json.loads(json.dumps(DEFAULT_USER))
        _user.update(data)
    return _user


def save_user():
    with open(store_path(), "w", encoding="utf-8") as fh:
        json.dump(user_data(), fh, indent=1)


def reload_user():
    _user.clear()
    return user_data()


def user_shelf(name):
    return next((s for s in user_data()["shelves"] if s["name"] == name), None)


# --- shelves and buttons -------------------------------------------------------------------------

def shelves():
    """[(id, tab label)] in Maya order: factory tabs, then the user shelves ("Custom" first)."""
    out = [(name, label) for name, label, _b in shelf_data.SHELVES]
    out += [(USER_PREFIX + s["name"], s["name"]) for s in user_data()["shelves"]]
    return out


def factory_buttons(name):
    """[(index, label, action, icon)] of the mapped buttons of a factory shelf."""
    for shelf, _label, buttons in shelf_data.SHELVES:
        if shelf == name:
            out = []
            for i, (label, command) in enumerate(buttons):
                hit = shelf_map.lookup(shelf, label, command)
                if hit is not None:
                    out.append((i, label, hit[0], hit[1]))
            return out
    return []


def current(context=None):
    from .. import preferences
    try:
        cur = preferences.get(context).shelf_current
    except KeyError:
        cur = ""
    ids = [s[0] for s in shelves()]
    return cur if cur in ids else shelf_data.DEFAULT


def set_current(context, shelf_id):
    from .. import preferences
    preferences.get(context).shelf_current = shelf_id


def run_script(context, label, script):
    """Run a user shelf button's Python script; returns (ok, message)."""
    from ..command_line import runner
    ns = dict(runner.namespace(), C=context, __name__="__maya_kit_shelf__")
    try:
        exec(compile(script, f"<shelf button {label}>", "exec"), ns)
    except Exception as ex:  # a user script: report, don't break the UI
        traceback.print_exc()
        return False, f"{label}: {type(ex).__name__}: {ex}"
    return True, ""


# --- operators -------------------------------------------------------------------------------------

class MAYAKIT_OT_shelf_button(bpy.types.Operator):
    """Run this shelf button (double-click or Ctrl+click: its options)"""
    bl_idname = "maya_kit.shelf_button"
    bl_label = "Shelf Button"
    bl_options = {'INTERNAL'}

    shelf: StringProperty()
    index: IntProperty()
    option: BoolProperty(options={'SKIP_SAVE'})

    @classmethod
    def description(cls, context, props):
        for i, label, _a, _icon in factory_buttons(props.shelf):
            if i == props.index:
                return f"{label} (Maya shelf). Double-click: options"
        if props.shelf.startswith(USER_PREFIX):
            s = user_shelf(props.shelf[len(USER_PREFIX):])
            if s and 0 <= props.index < len(s["buttons"]):
                b = s["buttons"][props.index]
                return f"{b['label']}\n{b['script'][:200]}"
        return "Shelf button"

    def invoke(self, context, event):
        if event.value == 'DOUBLE_CLICK' or event.ctrl:
            # The first click already ran the command: open its options (Maya
            # doubleClickCommand = "...Options", shelves.md:14-16).
            if event.value == 'DOUBLE_CLICK':
                try:
                    return bpy.ops.screen.redo_last('INVOKE_DEFAULT')
                except RuntimeError:
                    return {'CANCELLED'}
            self.option = True
        return self.execute(context)

    def execute(self, context):
        if self.shelf.startswith(USER_PREFIX):
            s = user_shelf(self.shelf[len(USER_PREFIX):])
            if s is None or not 0 <= self.index < len(s["buttons"]):
                return {'CANCELLED'}
            b = s["buttons"][self.index]
            ok, msg = run_script(context, b["label"], b["script"])
            if not ok:
                self.report({'ERROR'}, msg)
                return {'CANCELLED'}
            return {'FINISHED'}
        for i, _label, action, _icon in factory_buttons(self.shelf):
            if i == self.index:
                from ..marking.modal import run_action
                try:
                    run_action(context, action, self.option)
                except RuntimeError as ex:
                    self.report({'WARNING'}, str(ex).strip().splitlines()[-1])
                    return {'CANCELLED'}
                return {'FINISHED'}
        return {'CANCELLED'}


class MAYAKIT_OT_shelf_select(bpy.types.Operator):
    """Show this shelf"""
    bl_idname = "maya_kit.shelf_select"
    bl_label = "Select Shelf"
    bl_options = {'INTERNAL'}

    shelf: StringProperty()

    def execute(self, context):
        set_current(context, self.shelf)
        _redraw(context)
        return {'FINISHED'}


class MAYAKIT_OT_shelf_step(bpy.types.Operator):
    """Previous / next shelf tab"""
    bl_idname = "maya_kit.shelf_step"
    bl_label = "Next Shelf"
    bl_options = {'INTERNAL'}

    forward: BoolProperty(default=True)

    def execute(self, context):
        ids = [s[0] for s in shelves()]
        i = ids.index(current(context)) + (1 if self.forward else -1)
        set_current(context, ids[i % len(ids)])
        _redraw(context)
        return {'FINISHED'}


class MAYAKIT_OT_shelf_new(bpy.types.Operator):
    """Add an empty shelf (Maya shelf menu > New Shelf)"""
    bl_idname = "maya_kit.shelf_new"
    bl_label = "New Shelf"

    name: StringProperty(name="Name", default="Shelf1")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        name = self.name.strip() or "Shelf"
        base, n = name, 1
        while user_shelf(name) is not None:
            n += 1
            name = f"{base}{n}"
        user_data()["shelves"].append({"name": name, "buttons": []})
        save_user()
        set_current(context, USER_PREFIX + name)
        _redraw(context)
        return {'FINISHED'}


def _current_user_shelf(context):
    cur = current(context)
    return user_shelf(cur[len(USER_PREFIX):]) if cur.startswith(USER_PREFIX) else None


class MAYAKIT_OT_shelf_delete(bpy.types.Operator):
    """Delete the current user shelf (factory shelves stay)"""
    bl_idname = "maya_kit.shelf_delete"
    bl_label = "Delete Shelf"

    @classmethod
    def poll(cls, context):
        return _current_user_shelf(context) is not None and len(user_data()["shelves"]) > 1

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        s = _current_user_shelf(context)
        user_data()["shelves"].remove(s)
        save_user()
        set_current(context, shelf_data.DEFAULT)
        _redraw(context)
        return {'FINISHED'}


class _ButtonProps:
    label: StringProperty(name="Label", default="Script")
    icon: StringProperty(name="Icon", default="SCRIPT",
                         description="Blender icon name (e.g. SCRIPT, MESH_CUBE)")
    script: StringProperty(name="Python", default="print('hello')")
    from_text: BoolProperty(name="From Text Editor",
                            description="Use the text open in a Text Editor instead of the line above")

    def _source(self, context):
        if self.from_text:
            text = next((a.spaces.active.text for a in context.screen.areas
                         if a.type == 'TEXT_EDITOR' and a.spaces.active.text), None)
            if text is None:
                text = bpy.data.texts[0] if bpy.data.texts else None
            return text.as_string() if text is not None else None
        return self.script


def _valid_icon(name):
    items = bpy.types.UILayout.bl_rna.functions["label"].parameters["icon"].enum_items
    return name if name in items else 'SCRIPT'


class MAYAKIT_OT_shelf_add_button(_ButtonProps, bpy.types.Operator):
    """Add a Python script button to the current user shelf"""
    bl_idname = "maya_kit.shelf_add_button"
    bl_label = "Add Button"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return _current_user_shelf(context) is not None

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=420)

    def execute(self, context):
        source = self._source(context)
        if not source:
            self.report({'WARNING'}, "No script")
            return {'CANCELLED'}
        _current_user_shelf(context)["buttons"].append(
            {"label": self.label, "icon": _valid_icon(self.icon), "script": source})
        save_user()
        _redraw(context)
        return {'FINISHED'}


class MAYAKIT_OT_shelf_edit_button(_ButtonProps, bpy.types.Operator):
    """Change a button of the current user shelf"""
    bl_idname = "maya_kit.shelf_edit_button"
    bl_label = "Edit Button"
    bl_options = {'REGISTER'}

    index: IntProperty()

    def invoke(self, context, event):
        s = _current_user_shelf(context)
        if s is None or not 0 <= self.index < len(s["buttons"]):
            return {'CANCELLED'}
        b = s["buttons"][self.index]
        self.label, self.icon, self.script = b["label"], b["icon"], b["script"]
        return context.window_manager.invoke_props_dialog(self, width=420)

    def execute(self, context):
        s = _current_user_shelf(context)
        if s is None or not 0 <= self.index < len(s["buttons"]):
            return {'CANCELLED'}
        source = self._source(context)
        s["buttons"][self.index] = {"label": self.label, "icon": _valid_icon(self.icon),
                                    "script": source or s["buttons"][self.index]["script"]}
        save_user()
        _redraw(context)
        return {'FINISHED'}


class MAYAKIT_OT_shelf_remove_button(bpy.types.Operator):
    """Delete a button from the current user shelf"""
    bl_idname = "maya_kit.shelf_remove_button"
    bl_label = "Delete Button"
    bl_options = {'REGISTER'}

    index: IntProperty()

    def execute(self, context):
        s = _current_user_shelf(context)
        if s is None or not 0 <= self.index < len(s["buttons"]):
            return {'CANCELLED'}
        del s["buttons"][self.index]
        save_user()
        _redraw(context)
        return {'FINISHED'}


class MAYAKIT_OT_shelf_add_last_command(bpy.types.Operator):
    """Add the last command-line command as a button (Maya: drag a script to the shelf)"""
    bl_idname = "maya_kit.shelf_add_last_command"
    bl_label = "Add Last Command"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        from ..command_line import runner
        return _current_user_shelf(context) is not None and bool(runner.history)

    def execute(self, context):
        from ..command_line import runner
        cmd = runner.history[-1]
        _current_user_shelf(context)["buttons"].append(
            {"label": cmd.split("(")[0][-24:] or "Command", "icon": 'CONSOLE', "script": cmd})
        save_user()
        _redraw(context)
        return {'FINISHED'}


# Material buttons run maya_kit.shelf_material (operators/material.py, ).


# --- the strip area ----------------------------------------------------------------------------------

def is_strip(space):
    mask = getattr(space, "mask", None)
    return space is not None and space.type == 'IMAGE_EDITOR' and mask is not None and mask.name == MARKER


def strip_area(screen):
    for area in (screen.areas if screen else ()):
        if area.type == 'IMAGE_EDITOR' and is_strip(area.spaces.active):
            return area
    return None


def marker_mask():
    mask = bpy.data.masks.get(MARKER)
    if mask is None:
        mask = bpy.data.masks.new(MARKER)
        mask.use_fake_user = True
    return mask


def make_strip(space):
    """Turn an Image Editor space into the Maya strip."""
    space.mask = marker_mask()
    space.mode = 'VIEW'
    space.show_region_tool_header = True
    space.show_region_ui = False
    space.show_region_toolbar = False


class MAYAKIT_OT_shelf_strip_toggle(bpy.types.Operator):
    """Show or hide the Status Line + Shelf strip above the largest 3D View"""
    bl_idname = "maya_kit.shelf_strip_toggle"
    bl_label = "Shelf"

    def execute(self, context):
        from .status_line import main_view3d
        screen = context.screen
        win = context.window
        area = strip_area(screen)
        if area is not None:
            region = next(r for r in area.regions if r.type == 'WINDOW')
            with context.temp_override(window=win, screen=screen, area=area, region=region):
                bpy.ops.screen.area_close()
            return {'FINISHED'}
        view3d, region = main_view3d(screen)
        if view3d is None:
            self.report({'WARNING'}, "No 3D View to put the shelf over")
            return {'CANCELLED'}
        before = {a.as_pointer() for a in screen.areas}
        px = STRIP_PX * context.preferences.system.ui_scale
        factor = max(0.5, 1.0 - px / max(view3d.height, 1))
        with context.temp_override(window=win, screen=screen, area=view3d, region=region):
            bpy.ops.screen.area_split(direction='HORIZONTAL', factor=factor)
        new = next((a for a in screen.areas if a.as_pointer() not in before), None)
        if new is None:
            return {'CANCELLED'}
        new.type = 'IMAGE_EDITOR'
        make_strip(new.spaces.active)
        return {'FINISHED'}


def _redraw(context):
    screen = context.screen
    for area in (screen.areas if screen else ()):
        area.tag_redraw()


# --- drawing --------------------------------------------------------------------------------------------

class MAYAKIT_MT_shelf_tabs(bpy.types.Menu):
    """Choose the shelf (Maya shelf tabs)"""
    bl_idname = "MAYAKIT_MT_shelf_tabs"
    bl_label = "Shelves"

    def draw(self, context):
        cur = current(context)
        for shelf_id, label in shelves():
            if shelf_id.startswith(USER_PREFIX) and shelf_id == USER_PREFIX + user_data()["shelves"][0]["name"]:
                self.layout.separator()
            op = self.layout.operator(MAYAKIT_OT_shelf_select.bl_idname, text=label,
                                      icon='RADIOBUT_ON' if shelf_id == cur else 'RADIOBUT_OFF')
            op.shelf = shelf_id


class MAYAKIT_MT_shelf_settings(bpy.types.Menu):
    """Maya shelf menu: new/delete shelf, add/edit/delete buttons"""
    bl_idname = "MAYAKIT_MT_shelf_settings"
    bl_label = "Shelf"

    def draw(self, context):
        layout = self.layout
        layout.operator(MAYAKIT_OT_shelf_new.bl_idname, icon='ADD')
        layout.operator(MAYAKIT_OT_shelf_delete.bl_idname, icon='TRASH')
        layout.separator()
        layout.operator(MAYAKIT_OT_shelf_add_button.bl_idname, icon='SCRIPT')
        layout.operator(MAYAKIT_OT_shelf_add_last_command.bl_idname, icon='CONSOLE')
        s = _current_user_shelf(context)
        if s and s["buttons"]:
            layout.separator()
            for i, b in enumerate(s["buttons"]):
                row = layout.row()
                row.operator(MAYAKIT_OT_shelf_edit_button.bl_idname, text=f"Edit {b['label']}",
                             icon='GREASEPENCIL').index = i
            layout.separator()
            for i, b in enumerate(s["buttons"]):
                layout.operator(MAYAKIT_OT_shelf_remove_button.bl_idname, text=f"Delete {b['label']}",
                                icon='X').index = i


def draw_shelf(layout, context):
    """Shelf row: settings menu, tab dropdown with < >, then the current shelf's buttons."""
    cur = current(context)
    label = dict(shelves()).get(cur, cur)
    row = layout.row(align=True)
    row.menu(MAYAKIT_MT_shelf_settings.bl_idname, text="", icon='PREFERENCES')
    row = layout.row(align=True)
    row.operator(MAYAKIT_OT_shelf_step.bl_idname, text="", icon='TRIA_LEFT').forward = False
    row.menu(MAYAKIT_MT_shelf_tabs.bl_idname, text=label)
    row.operator(MAYAKIT_OT_shelf_step.bl_idname, text="", icon='TRIA_RIGHT').forward = True
    layout.separator(type='LINE')
    row = layout.row(align=True)
    if cur.startswith(USER_PREFIX):
        s = user_shelf(cur[len(USER_PREFIX):]) or {"buttons": []}
        if not s["buttons"]:
            row.operator(MAYAKIT_OT_shelf_add_button.bl_idname, text="Add Button", icon='ADD')
        for i, b in enumerate(s["buttons"]):
            op = row.operator(MAYAKIT_OT_shelf_button.bl_idname, text=b["label"] if b["icon"] == 'SCRIPT' else "",
                              icon=_valid_icon(b["icon"]))
            op.shelf, op.index = cur, i
        return
    for i, _label, _action, icon in factory_buttons(cur):
        op = row.operator(MAYAKIT_OT_shelf_button.bl_idname, text="", icon=icon)
        op.shelf, op.index = cur, i


_orig = {}


def _draw_image_header(self, context):
    if is_strip(context.space_data):
        from .status_line import draw_status_line
        return draw_status_line(self.layout, context)
    return _orig["header"](self, context)


def _draw_image_tool_header(self, context):
    if is_strip(context.space_data):
        return draw_shelf(self.layout, context)
    return _orig["tool_header"](self, context)


def patch_image_headers():
    if not _orig:
        _orig["header"] = bpy.types.IMAGE_HT_header.draw
        _orig["tool_header"] = bpy.types.IMAGE_HT_tool_header.draw
    bpy.types.IMAGE_HT_header.draw = _draw_image_header
    bpy.types.IMAGE_HT_tool_header.draw = _draw_image_tool_header


def unpatch_image_headers():
    if _orig:
        bpy.types.IMAGE_HT_header.draw = _orig.pop("header")
        bpy.types.IMAGE_HT_tool_header.draw = _orig.pop("tool_header")


classes = (MAYAKIT_OT_shelf_button, MAYAKIT_OT_shelf_select, MAYAKIT_OT_shelf_step,
           MAYAKIT_OT_shelf_new, MAYAKIT_OT_shelf_delete, MAYAKIT_OT_shelf_add_button,
           MAYAKIT_OT_shelf_edit_button, MAYAKIT_OT_shelf_remove_button,
           MAYAKIT_OT_shelf_add_last_command,
           MAYAKIT_OT_shelf_strip_toggle, MAYAKIT_MT_shelf_tabs, MAYAKIT_MT_shelf_settings)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    patch_image_headers()


def unregister():
    unpatch_image_headers()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    _user.clear()
