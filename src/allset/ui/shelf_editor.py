# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya-style Shelf Editor in the kit's floating editor window.

The editor works on a private draft of the existing shelves.json document.
Only Save Changes writes the draft back; Cancel discards it.
"""

import json

import bpy
from bpy.props import BoolProperty, EnumProperty, IntProperty, StringProperty

from . import marked_window, shelf

KIND = "SHELF_EDITOR"
TITLE = "Shelf Editor"

# Shelf Editor layout settings.
# The property list grows with the available window height, within these limits.
PROPERTY_MIN_ROWS = 10
PROPERTY_MAX_ROWS = 40
PROPERTY_ROW_HEIGHT = 22
ADD_MENU_COLUMNS = 2

_draft = None
_loading = False
_OPERATOR_ITEMS = []
_ICON_ITEMS = []


def _copy_document():
    return json.loads(json.dumps(shelf.user_data()))


def _draft_shelves():
    out = [(name, label) for name, label, _buttons in shelf.shelf_data.SHELVES]
    if _draft is not None:
        out.extend((shelf.USER_PREFIX + item["name"], item["name"])
                   for item in _draft.get("shelves", []))
    return out


def _draft_user_shelf(shelf_id):
    if not shelf_id.startswith(shelf.USER_PREFIX) or _draft is None:
        return None
    name = shelf_id[len(shelf.USER_PREFIX):]
    return next((item for item in _draft.get("shelves", []) if item["name"] == name), None)


def _draft_extra(shelf_id, create=False):
    if _draft is None:
        return None
    extra = _draft.get("extra")
    if not isinstance(extra, dict):
        if not create:
            return None
        extra = _draft["extra"] = {}
    if create:
        return extra.setdefault(shelf_id, [])
    return extra.get(shelf_id)


def _draft_buttons(shelf_id, create=False):
    user = _draft_user_shelf(shelf_id)
    if user is not None:
        return user.setdefault("buttons", [])
    if shelf_id.startswith(shelf.USER_PREFIX):
        return None
    if not any(name == shelf_id for name, _label, _buttons in shelf.shelf_data.SHELVES):
        return None
    return _draft_extra(shelf_id, create)


def _factory_rows(shelf_id):
    return shelf.all_buttons(shelf_id) if not shelf_id.startswith(shelf.USER_PREFIX) else []


def _unique_name(base, exclude=None):
    base = (base or "Shelf").strip() or "Shelf"
    names = {item["name"] for item in (_draft or {}).get("shelves", [])
             if item is not exclude}
    if base not in names:
        return base
    index = 2
    while f"{base}{index}" in names:
        index += 1
    return f"{base}{index}"


def _operator_ids():
    global _OPERATOR_ITEMS
    if not _OPERATOR_ITEMS:
        found = set()
        try:
            for module_name in dir(bpy.ops):
                if module_name.startswith("_"):
                    continue
                module = getattr(bpy.ops, module_name)
                for op_name in dir(module):
                    if op_name.startswith("_"):
                        continue
                    identifier = f"{module_name}.{op_name}"
                    try:
                        getattr(module, op_name).get_rna_type()
                    except (AttributeError, RuntimeError, TypeError):
                        continue
                    found.add(identifier)
        except (AttributeError, RuntimeError, TypeError):
            pass
        _OPERATOR_ITEMS[:] = sorted(found)
    return _OPERATOR_ITEMS


def _draw_operator_rna(layout, identifier):
    """Show the selected Operator's RNA schema as guidance without inventing UI properties."""
    if not identifier or "." not in identifier:
        return
    try:
        module, name = identifier.split(".", 1)
        rna = getattr(getattr(bpy.ops, module), name).get_rna_type()
    except (AttributeError, RuntimeError, TypeError):
        layout.label(text="Operator RNA is unavailable", icon="INFO")
        return
    box = layout.box()
    box.label(text=f"{rna.name} — RNA Properties", icon="PROPERTIES")
    shown = 0
    for prop in rna.properties:
        if prop.identifier in {"rna_type", "name"} or prop.is_readonly:
            continue
        description = (prop.description or prop.name or prop.identifier).replace("\n", " ")
        layout_row = box.row(align=True)
        layout_row.label(text=prop.name or prop.identifier)
        layout_row.label(text=prop.type.title())
        shown += 1
        if shown >= 8:
            break
    if shown == 0:
        box.label(text="No configurable properties")
    box.label(text="Overrides are stored as JSON; omitted properties use Operator defaults.", icon="INFO")


def operator_search(self, context, edit_text):
    query = (edit_text or "").lower()
    return [item for item in _operator_ids() if query in item.lower()][:80]


def menu_search(self, context, edit_text):
    from . import menu_map
    query = (edit_text or "").lower()
    return [item for item in sorted(menu_map.MAP) if query in item.lower()][:80]


def icon_search(self, context, edit_text):
    global _ICON_ITEMS
    if not _ICON_ITEMS:
        try:
            enum_items = bpy.types.UILayout.bl_rna.functions["label"].parameters["icon"].enum_items
            _ICON_ITEMS[:] = [item.identifier for item in enum_items if item.identifier != 'NONE']
        except (AttributeError, KeyError, TypeError):
            _ICON_ITEMS[:] = ["SCRIPT", "CONSOLE", "MESH_CUBE", "TOOL_SETTINGS"]
    query = (edit_text or "").lower()
    return [item for item in _ICON_ITEMS if query in item.lower()][:100]


def _wm(context):
    return context.window_manager


def _set_message(context, message):
    _wm(context).allset_se_message = message


def _load_button(context, index):
    global _loading
    wm = _wm(context)
    shelf_id = wm.allset_se_shelf
    buttons = _draft_buttons(shelf_id) or []
    if not 0 <= index < len(buttons):
        _loading = True
        try:
            wm.allset_se_index = -1
            wm.allset_se_label = ""
            wm.allset_se_icon = "SCRIPT"
            wm.allset_se_type = "SCRIPT"
            wm.allset_se_script = ""
            wm.allset_se_menu = ""
            wm.allset_se_operator = ""
            wm.allset_se_props = "{}"
            wm.allset_se_tooltip = ""
            wm.allset_se_action_id = ""
            wm.allset_se_action_code = ""
            wm.allset_se_action_kind = "ui_operator"
            wm.allset_se_tool_space_type = "VIEW_3D"
        finally:
            _loading = False
        return
    button = buttons[index]
    action = button.get("action") or {}
    _loading = True
    try:
        wm.allset_se_index = index
        wm.allset_se_label = button.get("label", "Button")
        wm.allset_se_icon = button.get("icon", "SCRIPT")
        wm.allset_se_tooltip = button.get("tooltip", "")
        if button.get("type") == "separator" or action.get("type") == "separator":
            wm.allset_se_type = "SEPARATOR"
        elif button.get("menu"):
            wm.allset_se_type = "MENU"
            wm.allset_se_menu = button["menu"]
        elif button.get("operator"):
            wm.allset_se_type = "OPERATOR"
            wm.allset_se_operator = button["operator"]
            wm.allset_se_props = json.dumps(button.get("props", {}), ensure_ascii=False)
        elif button.get("type") == "action":
            kind = action.get("type", "operator")
            # This EnumProperty only describes UI subtypes; general Action types
            # such as "operator", "python", and "tool" are not valid enum values.
            if kind in {"blender_menu", "pie_menu", "ui_operator"}:
                wm.allset_se_action_kind = kind
            wm.allset_se_action_id = action.get("id", "")
            wm.allset_se_action_code = action.get("code", "")
            wm.allset_se_props = json.dumps(action.get("properties", {}), ensure_ascii=False)
            if kind == "operator":
                wm.allset_se_type = "OPERATOR"
                wm.allset_se_operator = action.get("id", "")
            elif kind == "maya_menu":
                wm.allset_se_type = "MENU"
                wm.allset_se_menu = action.get("id", "")
            elif kind == "python":
                wm.allset_se_type = "PYTHON"
                wm.allset_se_script = action.get("code", "")
            elif kind == "tool":
                wm.allset_se_type = "TOOL"
                wm.allset_se_tool_space_type = action.get("space_type", "VIEW_3D")
            elif kind in {"blender_menu", "pie_menu", "ui_operator"}:
                wm.allset_se_type = "UI"
            else:
                wm.allset_se_type = "PYTHON"
        else:
            wm.allset_se_type = "SCRIPT"
            wm.allset_se_script = button.get("script", "")
    finally:
        _loading = False


def _start_draft(context):
    global _draft
    if marked_window.find_window(context, KIND) is None or _draft is None:
        _draft = _copy_document()
    wm = _wm(context)
    current = shelf.current(context)
    valid = {identifier for identifier, _label in _draft_shelves()}
    wm.allset_se_shelf = current if current in valid else _draft_shelves()[0][0]
    wm.allset_se_message = ""
    _load_button(context, -1)


def open_editor(context):
    _start_draft(context)
    # Use a compact Maya-style default independent of the source 3D View size.
    # A one-time marker migrates older oversized saved rectangles while preserving
    # any user-resized dimensions on subsequent launches.
    from . import window_places
    if context.window is not None:
        size_marker = f"{KIND}_SIZE_V3"
        if window_places.place(size_marker) is None:
            source = context.window
            width, height = 460, 460
            x = source.x + max(20, (source.width - width) // 2)
            y = source.y + max(20, (source.height - height) // 2)
            window_places.remember(KIND, (x, y, width, height))
            window_places.remember(size_marker, (2, 0, 0, 0))
        elif window_places.place(KIND) is None:
            source = context.window
            width, height = 460, 460
            x = source.x + max(20, (source.width - width) // 2)
            y = source.y + max(20, (source.height - height) // 2)
            window_places.remember(KIND, (x, y, width, height))
    window = marked_window.open_window(context, KIND)
    if window is None:
        return None
    for area in window.screen.areas:
        area.tag_redraw()
    return window


def _redraw(context):
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            area.tag_redraw()


class ALLSET_OT_shelf_editor_open(bpy.types.Operator):
    """Open the Maya-style floating Shelf Editor"""
    bl_idname = "allset.shelf_editor_open"
    bl_label = "Shelf Editor"

    def execute(self, context):
        if open_editor(context) is None:
            # A compact editor area may need to be carved across timer ticks.
            # In that case the opening operator is intentionally re-run later;
            # do not report a failure for this deferred first pass.
            from . import window_places
            if window_places.deferred():
                return {'FINISHED'}
            self.report({'ERROR'}, "Could not open the Shelf Editor window")
            return {'CANCELLED'}
        return {'FINISHED'}


class ALLSET_OT_shelf_editor_select_shelf(bpy.types.Operator):
    bl_idname = "allset.shelf_editor_select_shelf"
    bl_label = "Select Shelf"
    bl_options = {'INTERNAL'}

    shelf_id: StringProperty(options={'SKIP_SAVE'})

    def execute(self, context):
        wm = _wm(context)
        if self.shelf_id not in {identifier for identifier, _label in _draft_shelves()}:
            return {'CANCELLED'}
        wm.allset_se_shelf = self.shelf_id
        wm.allset_se_shelves_index = next(
            (index for index, (shelf_id, _label) in enumerate(_draft_shelves())
             if shelf_id == self.shelf_id),
            wm.allset_se_shelves_index,
        )
        _load_button(context, -1)
        _set_message(context, "")
        _redraw(context)
        return {'FINISHED'}


class ALLSET_OT_shelf_editor_select_button(bpy.types.Operator):
    bl_idname = "allset.shelf_editor_select_button"
    bl_label = "Select Button"
    bl_options = {'INTERNAL'}

    index: IntProperty(options={'SKIP_SAVE'})

    def execute(self, context):
        _load_button(context, self.index)
        _redraw(context)
        return {'FINISHED'}


class ALLSET_OT_shelf_editor_add_shelf(bpy.types.Operator):
    bl_idname = "allset.shelf_editor_add_shelf"
    bl_label = "New Shelf"

    name: StringProperty(name="Shelf Name", default="Custom")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=300)

    def execute(self, context):
        global _draft
        if _draft is None:
            return {'CANCELLED'}
        name = _unique_name(self.name)
        _draft.setdefault("shelves", []).append({"name": name, "buttons": []})
        _wm(context).allset_se_shelf = shelf.USER_PREFIX + name
        _load_button(context, -1)
        _set_message(context, f"Created shelf: {name} (not saved yet)")
        _redraw(context)
        return {'FINISHED'}


class ALLSET_OT_shelf_editor_rename_shelf(bpy.types.Operator):
    bl_idname = "allset.shelf_editor_rename_shelf"
    bl_label = "Rename Shelf"

    name: StringProperty(name="New Name")

    @classmethod
    def poll(cls, context):
        return _draft_user_shelf(_wm(context).allset_se_shelf) is not None

    def invoke(self, context, event):
        self.name = _wm(context).allset_se_shelf[len(shelf.USER_PREFIX):]
        return context.window_manager.invoke_props_dialog(self, width=300)

    def execute(self, context):
        wm = _wm(context)
        item = _draft_user_shelf(wm.allset_se_shelf)
        if item is None:
            return {'CANCELLED'}
        old_id = wm.allset_se_shelf
        name = _unique_name(self.name, exclude=item)
        item["name"] = name
        wm.allset_se_shelf = shelf.USER_PREFIX + name
        _set_message(context, f"Renamed {old_id} to {name} (not saved yet)")
        _redraw(context)
        return {'FINISHED'}


class ALLSET_OT_shelf_editor_duplicate_shelf(bpy.types.Operator):
    bl_idname = "allset.shelf_editor_duplicate_shelf"
    bl_label = "Duplicate Shelf"

    def execute(self, context):
        item = _draft_user_shelf(_wm(context).allset_se_shelf)
        if item is None:
            self.report({'WARNING'}, "Only user shelves can be duplicated")
            return {'CANCELLED'}
        duplicate = json.loads(json.dumps(item))
        duplicate["name"] = _unique_name(item["name"] + " Copy")
        _draft["shelves"].append(duplicate)
        _wm(context).allset_se_shelf = shelf.USER_PREFIX + duplicate["name"]
        _load_button(context, -1)
        _set_message(context, f"Duplicated shelf: {duplicate['name']} (not saved yet)")
        _redraw(context)
        return {'FINISHED'}


class ALLSET_OT_shelf_editor_delete_shelf(bpy.types.Operator):
    bl_idname = "allset.shelf_editor_delete_shelf"
    bl_label = "Delete Shelf"

    @classmethod
    def poll(cls, context):
        return (_draft_user_shelf(_wm(context).allset_se_shelf) is not None
                and len((_draft or {}).get("shelves", [])) > 1)

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        wm = _wm(context)
        item = _draft_user_shelf(wm.allset_se_shelf)
        if item is None:
            return {'CANCELLED'}
        _draft["shelves"].remove(item)
        wm.allset_se_shelf = _draft_shelves()[0][0]
        _load_button(context, -1)
        _set_message(context, "Shelf deleted from the draft (not saved yet)")
        _redraw(context)
        return {'FINISHED'}


class ALLSET_OT_shelf_editor_move_shelf(bpy.types.Operator):
    bl_idname = "allset.shelf_editor_move_shelf"
    bl_label = "Move Shelf"

    direction: EnumProperty(items=(("UP", "Up", ""), ("DOWN", "Down", "")))

    def execute(self, context):
        wm = _wm(context)
        item = _draft_user_shelf(wm.allset_se_shelf)
        if item is None:
            return {'CANCELLED'}
        items = _draft["shelves"]
        index = items.index(item)
        target = index + (-1 if self.direction == "UP" else 1)
        if not 0 <= target < len(items):
            return {'CANCELLED'}
        items[index], items[target] = items[target], items[index]
        _redraw(context)
        return {'FINISHED'}


class ALLSET_OT_shelf_editor_add_button(bpy.types.Operator):
    bl_idname = "allset.shelf_editor_add_button"
    bl_label = "Add Button"

    def execute(self, context):
        wm = _wm(context)
        buttons = _draft_buttons(wm.allset_se_shelf, create=True)
        if buttons is None:
            self.report({'WARNING'}, "This shelf does not accept custom buttons")
            return {'CANCELLED'}
        buttons.append({"label": "New Button", "icon": "SCRIPT", "script": "print('Hello')"})
        _load_button(context, len(buttons) - 1)
        _set_message(context, "New button added to the draft; edit its properties")
        _redraw(context)
        return {'FINISHED'}


class ALLSET_MT_shelf_editor_add_action(bpy.types.Menu):
    bl_idname = "ALLSET_MT_shelf_editor_add_action"
    bl_label = "Add Shelf Button"

    def draw(self, context):
        # Use content-sized flow columns instead of split(), which allocates
        # each column a fraction of the available popup width.
        # ui_units_x is a minimum-width hint, not a maximum-width constraint.
        flow = self.layout.column_flow(columns=ADD_MENU_COLUMNS, align=True)
        choices = (
            ("OPERATOR", "Operator", "CONSOLE", "Blender Operator"),
            ("MENU", "Menu", "LINENUMBERS_ON", "Maya menu item"),
            ("UI", "Popup / UI", "WINDOW", "Blender Menu, Pie Menu or UI Operator"),
            ("TOOL", "Tool", "TOOL_SETTINGS", "Activate a Blender Tool"),
            ("PYTHON", "Python", "CONSOLE", "Python command"),
            ("LEGACY_PYTHON", "Legacy Script", "FILE_SCRIPT", "Legacy script button using the original Shelf script field"),
            ("SEPARATOR", "Separator", "REMOVE", "Visual separator"),
        )
        for index, (kind, label, icon, tip) in enumerate(choices):
            op = flow.operator(
                ALLSET_OT_shelf_editor_create_action.bl_idname,
                text=label,
                icon=icon,
            )
            op.action_type = kind
            op.help_text = tip


class ALLSET_OT_shelf_editor_create_action(bpy.types.Operator):
    """Create a Shelf button using the selected command type."""
    bl_idname = "allset.shelf_editor_create_action"
    bl_label = "Add Shelf Button"
    bl_description = "Create a Shelf button using the selected command type."
    action_type: StringProperty(options={'HIDDEN'})
    help_text: StringProperty(options={'HIDDEN'})
    label: StringProperty(name="Label", default="New Button")
    icon: StringProperty(name="Icon", default="SCRIPT", search=icon_search)
    tooltip: StringProperty(name="Tooltip")
    target: StringProperty(name="Command / ID", search=operator_search)
    code: StringProperty(name="Python", default="print('Hello')")
    properties_json: StringProperty(name="Operator Properties", default="{}")
    ui_kind: EnumProperty(name="UI Type", items=(("blender_menu", "Menu", ""), ("pie_menu", "Pie Menu", ""), ("ui_operator", "UI Operator", "")))

    @classmethod
    def description(cls, context, properties):
        return properties.help_text or "Add a Shelf button using the selected command type."

    def invoke(self, context, event):
        # Selecting a command type creates a draft entry immediately. Detailed
        # values are edited in the persistent Button Properties section.
        return self.execute(context)

    def draw(self, context):
        # Kept for compatibility if this operator is invoked externally with a
        # properties dialog; the Shelf Editor chooser itself never opens it.
        layout = self.layout
        layout.label(text=self.help_text, icon={"OPERATOR":"CONSOLE", "MENU":"LINENUMBERS_ON", "UI":"WINDOW", "TOOL":"TOOL_SETTINGS", "PYTHON":"CONSOLE"}.get(self.action_type, "REMOVE"))
        layout.prop(self, "label")
        layout.prop(self, "icon")
        layout.label(text=self.icon or "SCRIPT", icon=shelf._valid_icon(self.icon))
        layout.prop(self, "tooltip")
        if self.action_type == "OPERATOR":
            layout.prop(self, "target", text="Search Operator")
            layout.prop(self, "properties_json")
            _draw_operator_rna(layout, self.target)
        elif self.action_type == "MENU":
            layout.prop(self, "target", text="Maya Menu Item")
        elif self.action_type == "UI":
            layout.prop(self, "ui_kind")
            layout.prop(self, "target", text="Menu / UI ID")
        elif self.action_type == "TOOL":
            layout.prop(self, "target", text="Tool ID")
        elif self.action_type in {"PYTHON", "LEGACY_PYTHON"}:
            layout.prop(self, "code")
            if self.action_type == "LEGACY_PYTHON":
                layout.label(text="Uses the original Shelf script field for backward compatibility", icon='INFO')

    def execute(self, context):
        buttons = _draft_buttons(_wm(context).allset_se_shelf, create=True)
        if buttons is None:
            self.report({'WARNING'}, "This shelf does not accept custom buttons")
            return {'CANCELLED'}

        record = {
            "label": self.label.strip() or "New Button",
            "icon": shelf._valid_icon(self.icon),
            "tooltip": self.tooltip.strip(),
        }
        kind = self.action_type
        if kind == "SEPARATOR":
            record.update(type="separator", action={"type": "separator"})
        elif kind == "OPERATOR":
            # An empty operator ID is intentional: choose it in Button Properties.
            record.update(type="action", action={"type": "operator", "id": "", "properties": {}})
        elif kind == "MENU":
            record.update(type="action", action={"type": "maya_menu", "id": ""})
        elif kind == "UI":
            record.update(type="action", action={"type": self.ui_kind, "id": ""})
        elif kind == "TOOL":
            record.update(type="action", action={"type": "tool", "id": "", "space_type": "VIEW_3D"})
        elif kind == "PYTHON":
            record.update(type="action", action={"type": "python", "code": self.code.strip() or "print('Hello')"})
        elif kind == "LEGACY_PYTHON":
            record["script"] = self.code.strip() or "print('Hello')"
        else:
            return {'CANCELLED'}

        buttons.append(record)
        _load_button(context, len(buttons) - 1)
        _set_message(context, f"Added {record['label']} to draft; edit its properties below")
        _redraw(context)
        return {'FINISHED'}


class ALLSET_OT_shelf_editor_apply_button(bpy.types.Operator):
    bl_idname = "allset.shelf_editor_apply_button"
    bl_label = "Apply Button Changes"

    def execute(self, context):
        wm = _wm(context)
        buttons = _draft_buttons(wm.allset_se_shelf, create=True)
        index = wm.allset_se_index
        if buttons is None or not 0 <= index < len(buttons):
            self.report({'WARNING'}, "Select a custom button first")
            return {'CANCELLED'}
        label = wm.allset_se_label.strip() or "Button"
        record = {"label": label, "icon": shelf._valid_icon(wm.allset_se_icon),
                  "tooltip": wm.allset_se_tooltip.strip()}
        kind = wm.allset_se_type
        if kind == "SEPARATOR":
            record.update(type="separator", action={"type": "separator"})
        elif kind == "MENU":
            from . import menu_map
            path = wm.allset_se_menu.strip()
            if path not in menu_map.MAP:
                self.report({'WARNING'}, "Choose a valid Maya menu item")
                return {'CANCELLED'}
            record.update(type="action", action={"type": "maya_menu", "id": path})
        elif kind == "OPERATOR":
            op_id = wm.allset_se_operator.strip()
            if op_id not in _operator_ids():
                self.report({'WARNING'}, "Choose a valid Blender Operator")
                return {'CANCELLED'}
            try:
                props = json.loads(wm.allset_se_props or "{}")
            except ValueError as ex:
                self.report({'WARNING'}, f"Operator properties are invalid JSON: {ex}")
                return {'CANCELLED'}
            if not isinstance(props, dict):
                self.report({'WARNING'}, "Operator properties must be a JSON object")
                return {'CANCELLED'}
            record.update(type="action", action={"type": "operator", "id": op_id, "properties": props})
        elif kind == "PYTHON":
            code = wm.allset_se_script
            if not code.strip():
                self.report({'WARNING'}, "Python command cannot be empty")
                return {'CANCELLED'}
            record.update(type="action", action={"type": "python", "code": code})
        elif kind == "TOOL":
            target = wm.allset_se_action_id.strip()
            if not target:
                self.report({'WARNING'}, "Enter a Tool ID")
                return {'CANCELLED'}
            space_type = wm.allset_se_tool_space_type
            record.update(type="action", action={"type": "tool", "id": target,
                                                   "space_type": space_type})
        elif kind == "UI":
            target = wm.allset_se_action_id.strip()
            action_kind = wm.allset_se_action_kind
            if not target or action_kind not in {"blender_menu", "pie_menu", "ui_operator"}:
                self.report({'WARNING'}, "Enter a valid Menu or UI Operator ID")
                return {'CANCELLED'}
            record.update(type="action", action={"type": action_kind, "id": target})
        else:
            code = wm.allset_se_script
            if not code.strip():
                self.report({'WARNING'}, "Python command cannot be empty")
                return {'CANCELLED'}
            record["script"] = code
        buttons[index] = record
        _set_message(context, f"Updated: {label} (not saved yet)")
        _redraw(context)
        return {'FINISHED'}


class ALLSET_OT_shelf_editor_delete_button(bpy.types.Operator):
    bl_idname = "allset.shelf_editor_delete_button"
    bl_label = "Delete Button"

    def execute(self, context):
        wm = _wm(context)
        buttons = _draft_buttons(wm.allset_se_shelf) or []
        index = wm.allset_se_index
        if not 0 <= index < len(buttons):
            return {'CANCELLED'}
        del buttons[index]
        _load_button(context, min(index, len(buttons) - 1))
        _set_message(context, "Button deleted from the draft (not saved yet)")
        _redraw(context)
        return {'FINISHED'}


class ALLSET_OT_shelf_editor_move_button(bpy.types.Operator):
    bl_idname = "allset.shelf_editor_move_button"
    bl_label = "Move Button"

    direction: EnumProperty(items=(("UP", "Up", ""), ("DOWN", "Down", "")))

    def execute(self, context):
        wm = _wm(context)
        buttons = _draft_buttons(wm.allset_se_shelf) or []
        index = wm.allset_se_index
        target = index + (-1 if self.direction == "UP" else 1)
        if not 0 <= index < len(buttons) or not 0 <= target < len(buttons):
            return {'CANCELLED'}
        buttons[index], buttons[target] = buttons[target], buttons[index]
        _load_button(context, target)
        _redraw(context)
        return {'FINISHED'}


class ALLSET_OT_shelf_editor_save(bpy.types.Operator):
    bl_idname = "allset.shelf_editor_save"
    bl_label = "Save Changes"

    def execute(self, context):
        global _draft
        if _draft is None:
            return {'CANCELLED'}
        shelf._user.clear()
        shelf._user.update(json.loads(json.dumps(_draft)))
        shelf.save_user()
        active = _wm(context).allset_se_shelf
        valid = {identifier for identifier, _label in shelf.shelves()}
        if active in valid:
            shelf.set_current(context, active)
        _draft = _copy_document()
        _set_message(context, "Shelf changes saved")
        _redraw(context)
        return {'FINISHED'}


class ALLSET_OT_shelf_editor_cancel(bpy.types.Operator):
    bl_idname = "allset.shelf_editor_cancel"
    bl_label = "Discard Changes"

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        global _draft
        _draft = _copy_document()
        wm = _wm(context)
        valid = {identifier for identifier, _label in _draft_shelves()}
        wm.allset_se_shelf = shelf.current(context) if shelf.current(context) in valid else _draft_shelves()[0][0]
        _load_button(context, -1)
        _set_message(context, "Unsaved changes discarded")
        _redraw(context)
        return {'FINISHED'}


class ALLSET_PG_shelf_editor_list_item(bpy.types.PropertyGroup):
    """Transient row data used by the scrollable Shelf Contents list."""
    label: StringProperty()
    icon: StringProperty(default="NONE")
    button_index: IntProperty(default=-1)
    is_factory: BoolProperty(default=False)
    shelf_id: StringProperty()
    field: StringProperty()
    row_kind: StringProperty(default="FIELD")


class ALLSET_UL_shelf_editor_shelves(bpy.types.UIList):
    """Independent scrollable list of shelves."""
    bl_idname = "ALLSET_UL_shelf_editor_shelves"

    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_property, index=0, flt_flag=0):
        row = layout.row(align=True)
        selected = data.allset_se_shelf == item.shelf_id
        op = row.operator(
            ALLSET_OT_shelf_editor_select_shelf.bl_idname,
            text=item.label,
            icon='RADIOBUT_ON' if selected else 'RADIOBUT_OFF',
            depress=selected,
        )
        op.shelf_id = item.shelf_id


class ALLSET_UL_shelf_editor_properties(bpy.types.UIList):
    """Fixed-height, independently scrollable Button Properties editor."""
    bl_idname = "ALLSET_UL_shelf_editor_properties"

    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_property, index=0, flt_flag=0):
        if item.row_kind == "RNA_HEADER":
            layout.label(text=item.label, icon='PROPERTIES')
            return
        if item.row_kind == "INFO":
            layout.label(text=item.label, icon='DOT')
            return
        if item.row_kind == "RNA_FOOTER":
            layout.label(text=item.label, icon='INFO')
            return
        if item.row_kind == "PREVIEW":
            row = layout.row(align=True)
            row.label(text=item.label or "SCRIPT", icon=shelf._valid_icon(data.allset_se_icon))
            row.label(text="Icon Preview")
            return
        if item.field and hasattr(data, item.field):
            layout.prop(data, item.field, text=item.label)


class ALLSET_UL_shelf_editor_contents(bpy.types.UIList):
    """Keep long Shelf Contents lists scrollable without scrolling the editor footer."""
    bl_idname = "ALLSET_UL_shelf_editor_contents"

    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_property, index=0, flt_flag=0):
        row = layout.row(align=True)
        if item.is_factory:
            row.label(text=item.label, icon=item.icon if item.icon != 'NONE' else 'DOT')
            row.label(text="Factory", icon='LOCKED')
            return

        op = row.operator(
            ALLSET_OT_shelf_editor_select_button.bl_idname,
            text=item.label,
            icon=item.icon if item.icon != 'NONE' else 'DOT',
            depress=data.allset_se_index == item.button_index,
        )
        op.index = item.button_index
        if data.allset_se_index == item.button_index:
            controls = row.row(align=True)
            move_up = controls.operator(ALLSET_OT_shelf_editor_move_button.bl_idname,
                                        text="", icon='TRIA_UP')
            move_up.direction = "UP"
            move_down = controls.operator(ALLSET_OT_shelf_editor_move_button.bl_idname,
                                          text="", icon='TRIA_DOWN')
            move_down.direction = "DOWN"
            controls.operator(ALLSET_OT_shelf_editor_delete_button.bl_idname,
                              text="", icon='TRASH')


def _sync_contents_list(wm, shelf_id):
    """Refresh transient UIList data only when the visible rows actually change."""
    rows = []
    if shelf_id.startswith(shelf.USER_PREFIX):
        for index, button in enumerate(_draft_buttons(shelf_id) or []):
            rows.append((button.get("label", "Button"),
                         shelf._valid_icon(button.get("icon", "SCRIPT")),
                         index, False))
    else:
        for _index, label, _action, icon in _factory_rows(shelf_id):
            rows.append((label, icon, -1, True))
        for index, button in enumerate(_draft_buttons(shelf_id) or []):
            rows.append((button.get("label", "Button"),
                         shelf._valid_icon(button.get("icon", "SCRIPT")),
                         index, False))

    signature = repr((shelf_id, rows))
    if wm.allset_se_items_signature == signature:
        return
    collection = wm.allset_se_items
    collection.clear()
    for label, icon, button_index, is_factory in rows:
        item = collection.add()
        item.label = label
        item.icon = icon
        item.button_index = button_index
        item.is_factory = is_factory
    wm.allset_se_items_signature = signature
    wm.allset_se_list_index = min(wm.allset_se_list_index, max(0, len(rows) - 1))


def _sync_shelves_list(wm):
    """Refresh shelf rows while preserving the independent scroll position."""
    rows = _draft_shelves()
    signature = repr(rows)
    if wm.allset_se_shelves_signature == signature:
        return
    collection = wm.allset_se_shelves
    collection.clear()
    for shelf_id, label in rows:
        item = collection.add()
        item.shelf_id = shelf_id
        item.label = label
        item.icon = 'RADIOBUT_OFF'
    wm.allset_se_shelves_signature = signature
    selected_index = next((index for index, (shelf_id, _label) in enumerate(rows)
                           if shelf_id == wm.allset_se_shelf), 0)
    wm.allset_se_shelves_index = min(selected_index, max(0, len(rows) - 1))


def _sync_properties_list(wm):
    """Build the same Button Properties content as Scroll-Fix in a scrollable UIList."""
    rows = [
        ("FIELD", "allset_se_label", "Label"),
        ("FIELD", "allset_se_icon", "Icon"),
        ("FIELD", "allset_se_type", "Command Type"),
    ]
    kind = wm.allset_se_type
    if kind == "SCRIPT":
        rows.append(("FIELD", "allset_se_script", "Python"))
    elif kind == "MENU":
        rows.append(("FIELD", "allset_se_menu", "Maya Menu Item"))
    elif kind == "OPERATOR":
        rows.extend((
            ("FIELD", "allset_se_operator", "Search Operator"),
            ("FIELD", "allset_se_props", "Properties JSON"),
        ))
        try:
            module, name = wm.allset_se_operator.split(".", 1)
            rna = getattr(getattr(bpy.ops, module), name).get_rna_type()
            rows.append(("RNA_HEADER", "", f"{rna.name} — RNA Properties"))
            shown = 0
            for prop in rna.properties:
                if prop.identifier in {"rna_type", "name"} or prop.is_readonly:
                    continue
                rows.append(("INFO", "", f"{prop.name or prop.identifier} · {prop.type.title()}"))
                shown += 1
                if shown >= 8:
                    break
            if shown == 0:
                rows.append(("INFO", "", "No configurable properties"))
            rows.append((
                "RNA_FOOTER", "",
                "Overrides are stored as JSON; omitted properties use Operator defaults.",
            ))
        except (AttributeError, RuntimeError, TypeError, ValueError):
            rows.append(("INFO", "", "Operator RNA is unavailable"))
    elif kind == "PYTHON":
        rows.append(("FIELD", "allset_se_script", "Python"))
    elif kind == "UI":
        rows.extend((
            ("FIELD", "allset_se_action_kind", "UI Type"),
            ("FIELD", "allset_se_action_id", "Menu / UI ID"),
        ))
    elif kind == "TOOL":
        rows.extend((
            ("FIELD", "allset_se_action_id", "Tool ID"),
            ("FIELD", "allset_se_tool_space_type", "Editor"),
        ))

    rows.extend((
        ("FIELD", "allset_se_tooltip", "Tooltip"),
        ("PREVIEW", "", wm.allset_se_icon or "SCRIPT"),
    ))
    signature = repr((wm.allset_se_index, kind, wm.allset_se_operator, rows))
    if wm.allset_se_properties_signature == signature:
        return
    collection = wm.allset_se_properties
    collection.clear()
    for row_kind, field, label in rows:
        item = collection.add()
        item.row_kind = row_kind
        item.field = field
        item.label = label
    wm.allset_se_properties_signature = signature
    wm.allset_se_properties_index = 0


class ALLSET_PT_shelf_editor(bpy.types.Panel):
    """Maya-style Shelf Editor shown in the kit's dedicated floating editor window"""
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Tool"
    bl_label = TITLE
    bl_options = {'HIDE_HEADER'}
    bl_order = -310

    @classmethod
    def poll(cls, context):
        return marked_window.context_kind(context) == KIND

    def draw(self, context):
        global _draft
        wm = _wm(context)
        layout = self.layout
        layout.use_property_split = False
        layout.use_property_decorate = False
        if _draft is None:
            layout.label(text="Shelf Editor session is not initialized", icon='ERROR')
            layout.operator(ALLSET_OT_shelf_editor_open.bl_idname, text="Reopen Editor")
            return

        header = layout.row(align=True)
        header.label(text="Shelf Editor", icon='TOOL_SETTINGS')

        layout.separator()
        split = layout.split(factor=0.38, align=True)
        left = split.column(align=True)
        left.label(text="Shelves", icon='FILE_FOLDER')
        _sync_shelves_list(wm)
        # A: fixed-height scroll viewport. Match B's framed template_list so
        # both columns have the same visible row count and viewport height.
        shelf_list_box = left.box()
        shelf_list_box.template_list(
            ALLSET_UL_shelf_editor_shelves.bl_idname,
            "shelf_editor_shelves",
            wm,
            "allset_se_shelves",
            wm,
            "allset_se_shelves_index",
            rows=14,
            maxrows=14,
            type='DEFAULT',
        )
        left.separator()
        shelf_tools = left.row(align=True)
        shelf_tools.alignment = 'LEFT'
        shelf_tools.operator(ALLSET_OT_shelf_editor_add_shelf.bl_idname, text="", icon='ADD')
        if _draft_user_shelf(wm.allset_se_shelf) is not None:
            shelf_tools.operator(ALLSET_OT_shelf_editor_rename_shelf.bl_idname, text="", icon='GREASEPENCIL')
            shelf_tools.operator(ALLSET_OT_shelf_editor_duplicate_shelf.bl_idname, text="", icon='DUPLICATE')
            shelf_tools.operator(ALLSET_OT_shelf_editor_delete_shelf.bl_idname, text="", icon='TRASH')
            op = shelf_tools.operator(ALLSET_OT_shelf_editor_move_shelf.bl_idname, text="", icon='TRIA_UP')
            op.direction = "UP"
            op = shelf_tools.operator(ALLSET_OT_shelf_editor_move_shelf.bl_idname, text="", icon='TRIA_DOWN')
            op.direction = "DOWN"

        right = split.column(align=True)
        right.label(text="Shelf Contents", icon='PRESET')
        shelf_id = wm.allset_se_shelf
        _sync_contents_list(wm, shelf_id)
        list_box = right.box()
        list_box.template_list(
            ALLSET_UL_shelf_editor_contents.bl_idname,
            "shelf_contents",
            wm,
            "allset_se_items",
            wm,
            "allset_se_list_index",
            rows=14,
            maxrows=14,
            type='DEFAULT',
        )

        # Native popup menu: selecting a type creates the draft item directly.
        # The popup does not occupy layout space or change A/B/C/D dimensions.
        right.menu(
            ALLSET_MT_shelf_editor_add_action.bl_idname,
            text="Add Button",
            icon='ADD',
        )

        layout.separator()
        help_row = layout.row(align=True)
        help_row.label(text="Quick Add: Ctrl+Shift-click a Maya menu item", icon='INFO')
        help_row.label(text="Add Button opens the visual command chooser")
        # The C viewport fills the remaining editor height, while its own
        # UIList remains independently scrollable. Reserve two UI rows for D:
        # one row of breathing room plus the Save / Discard button row.
        region = context.region
        ui_scale = max(1.0, context.preferences.system.ui_scale)
        has_selection = wm.allset_se_index >= 0
        top_fixed_px = (92 + 16 * 22 + 38) * ui_scale
        help_px = 24 * ui_scale
        message_px = (24 * ui_scale) if wm.allset_se_message else 0.0
        footer_px = 2 * 22 * ui_scale
        property_chrome_px = (28 + 28) * ui_scale if has_selection else 0.0
        bottom_gap_px = 8 * ui_scale
        row_px = PROPERTY_ROW_HEIGHT * ui_scale
        if has_selection:
            property_rows = int((float(region.height) - top_fixed_px - help_px
                                 - message_px - footer_px - property_chrome_px
                                 - bottom_gap_px) / row_px)
            property_rows = max(PROPERTY_MIN_ROWS,
                                min(PROPERTY_MAX_ROWS, property_rows))
            box = layout.box()
            box.label(text="Button Properties", icon='PREFERENCES')
            _sync_properties_list(wm)
            box.template_list(
                ALLSET_UL_shelf_editor_properties.bl_idname,
                "shelf_editor_properties",
                wm,
                "allset_se_properties",
                wm,
                "allset_se_properties_index",
                rows=property_rows,
                maxrows=property_rows,
                type='DEFAULT',
            )
            box.operator(ALLSET_OT_shelf_editor_apply_button.bl_idname,
                         text="Apply to Draft", icon='CHECKMARK')

        if wm.allset_se_message:
            layout.separator()
            layout.label(text=wm.allset_se_message, icon='INFO')

        # Keep D at the bottom with a two-row reserve. C consumes the available
        # height above it instead of remaining a short seven-row panel.
        top_rows = 16
        property_rows_for_footer = property_rows if has_selection else 0
        estimated_content = (92 + top_rows * 22 + 38 + help_px / ui_scale
                             + (56 + property_rows_for_footer * 22 if has_selection else 0)
                             + (message_px / ui_scale) + 2 * 22 + 8) * ui_scale
        available = max(0.0, float(region.height) - estimated_content)
        layout.separator(factor=available / (6.0 * ui_scale))
        footer = layout.row(align=True)
        footer.alignment = 'RIGHT'
        footer.operator(ALLSET_OT_shelf_editor_save.bl_idname, text="Save", icon='FILE_TICK')
        footer.operator(ALLSET_OT_shelf_editor_cancel.bl_idname, text="Discard", icon='LOOP_BACK')


classes = (
    ALLSET_OT_shelf_editor_open,
    ALLSET_OT_shelf_editor_select_shelf,
    ALLSET_OT_shelf_editor_select_button,
    ALLSET_OT_shelf_editor_add_shelf,
    ALLSET_OT_shelf_editor_rename_shelf,
    ALLSET_OT_shelf_editor_duplicate_shelf,
    ALLSET_OT_shelf_editor_delete_shelf,
    ALLSET_OT_shelf_editor_move_shelf,
    ALLSET_OT_shelf_editor_add_button,
    ALLSET_MT_shelf_editor_add_action,
    ALLSET_OT_shelf_editor_create_action,
    ALLSET_OT_shelf_editor_apply_button,
    ALLSET_OT_shelf_editor_delete_button,
    ALLSET_OT_shelf_editor_move_button,
    ALLSET_OT_shelf_editor_save,
    ALLSET_OT_shelf_editor_cancel,
    ALLSET_PG_shelf_editor_list_item,
    ALLSET_UL_shelf_editor_shelves,
    ALLSET_UL_shelf_editor_properties,
    ALLSET_UL_shelf_editor_contents,
    ALLSET_PT_shelf_editor,
)

_WM_PROPS = (
    "allset_se_shelf", "allset_se_index", "allset_se_label", "allset_se_icon",
    "allset_se_type", "allset_se_script", "allset_se_menu", "allset_se_operator",
    "allset_se_props", "allset_se_tooltip", "allset_se_message",
    "allset_se_action_id", "allset_se_action_code", "allset_se_action_kind",
    "allset_se_tool_space_type",
    "allset_se_items", "allset_se_items_signature", "allset_se_list_index",
    "allset_se_shelves", "allset_se_shelves_signature", "allset_se_shelves_index",
    "allset_se_properties", "allset_se_properties_signature", "allset_se_properties_index",
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    wm = bpy.types.WindowManager
    wm.allset_se_shelf = StringProperty(options={'SKIP_SAVE'})
    wm.allset_se_index = IntProperty(default=-1, options={'SKIP_SAVE'})
    wm.allset_se_label = StringProperty(name="Label", options={'SKIP_SAVE'})
    wm.allset_se_icon = StringProperty(name="Icon", search=icon_search, options={'SKIP_SAVE'})
    wm.allset_se_type = EnumProperty(
        name="Command Type",
        items=(("SCRIPT", "Legacy Python", "Legacy Python script"),
               ("MENU", "Maya Menu Item", "Run a Maya Workflow Kit menu command"),
               ("OPERATOR", "Blender Operator", "Run a Blender operator"),
               ("PYTHON", "Python Command", "Run a typed Python command"),
               ("UI", "Popup / UI", "Open a registered menu or UI operator"),
               ("TOOL", "Tool", "Activate a Blender Tool"),
               ("SEPARATOR", "Separator", "Visual separator")),
        options={'SKIP_SAVE'},
    )
    wm.allset_se_script = StringProperty(name="Python", options={'SKIP_SAVE'})
    wm.allset_se_menu = StringProperty(name="Maya Menu Item", search=menu_search, options={'SKIP_SAVE'})
    wm.allset_se_operator = StringProperty(name="Blender Operator", search=operator_search, options={'SKIP_SAVE'})
    wm.allset_se_props = StringProperty(name="Operator Properties", options={'SKIP_SAVE'})
    wm.allset_se_tooltip = StringProperty(name="Tooltip", options={'SKIP_SAVE'})
    wm.allset_se_message = StringProperty(options={'SKIP_SAVE'})
    wm.allset_se_action_id = StringProperty(name="Action ID", options={'SKIP_SAVE'})
    wm.allset_se_action_code = StringProperty(name="Action Code", options={'SKIP_SAVE'})
    wm.allset_se_tool_space_type = EnumProperty(
        name="Editor",
        items=(
            ("VIEW_3D", "3D View", "Activate the tool in the 3D View"),
            ("IMAGE_EDITOR", "UV Editor", "Activate the tool in the UV Editor"),
        ),
        default="VIEW_3D",
        options={'SKIP_SAVE'},
    )
    wm.allset_se_action_kind = EnumProperty(
        name="UI Type",
        items=(
            ("blender_menu", "Menu", ""),
            ("pie_menu", "Pie Menu", ""),
            ("ui_operator", "UI Operator", ""),
        ),
        default="ui_operator",
        options={'SKIP_SAVE'},
    )
    wm.allset_se_items = bpy.props.CollectionProperty(type=ALLSET_PG_shelf_editor_list_item,
                                                       options={'SKIP_SAVE'})
    wm.allset_se_items_signature = StringProperty(options={'SKIP_SAVE'})
    wm.allset_se_list_index = IntProperty(default=0, options={'SKIP_SAVE'})
    wm.allset_se_shelves = bpy.props.CollectionProperty(type=ALLSET_PG_shelf_editor_list_item,
                                                         options={'SKIP_SAVE'})
    wm.allset_se_shelves_signature = StringProperty(options={'SKIP_SAVE'})
    wm.allset_se_shelves_index = IntProperty(default=0, options={'SKIP_SAVE'})
    wm.allset_se_properties = bpy.props.CollectionProperty(type=ALLSET_PG_shelf_editor_list_item,
                                                            options={'SKIP_SAVE'})
    wm.allset_se_properties_signature = StringProperty(options={'SKIP_SAVE'})
    wm.allset_se_properties_index = IntProperty(default=0, options={'SKIP_SAVE'})
    marked_window.KINDS[KIND] = ("show_properties_scene", "show_properties_data")


def unregister():
    global _draft
    _draft = None
    marked_window.KINDS.pop(KIND, None)
    for name in _WM_PROPS:
        if hasattr(bpy.types.WindowManager, name):
            delattr(bpy.types.WindowManager, name)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
