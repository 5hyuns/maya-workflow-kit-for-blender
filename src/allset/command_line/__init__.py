# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya Command Line and Help Line in Blender's status bar.

 (:290-293: language toggle, input/result
field, Script Editor button), (:295-298: Help Line);
 #14 (:93-94). Design: 
「계획」 4. Python only: MEL is not supported (). ``maya.cmds`` is a
small look-alike (``cmds_shim``), importable as ``import maya.cmds as cmds``.
"""

import sys
import types

import bpy
from bpy.props import StringProperty

from . import cmds_shim, runner

# --- state shown in the status bar --------------------------------------------------

_result = {"text": "", "error": False}


def submit(text):
    """Run a command and keep its result for the result field."""
    res = runner.run(text)
    _result["text"], _result["error"] = res.text, res.error
    return res


def _on_command(self, context):
    text = self.allset_cmd
    if not text.strip():
        return
    self.allset_cmd = ""  # re-enters this callback with "" -> returns above
    submit(text)  # an error shows red in the result field
    # An operator called from a property update doesn't push an undo step
    # (checked in the GUI test), so push one: one command = one Ctrl+Z.
    bpy.ops.ed.undo_push(message=f"Command: {text[:40]}")


class ALLSET_OT_command_line_exec(bpy.types.Operator):
    """Run a Python command (one undo step), like Maya's command line"""
    bl_idname = "allset.command_line_exec"
    bl_label = "Run Command"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    command: StringProperty(name="Command", options={'SKIP_SAVE'})

    def execute(self, context):
        res = submit(self.command)
        if res.error:
            self.report({'ERROR'}, res.text)
        elif res.text:
            self.report({'INFO'}, res.text)
        return {'FINISHED'}


class ALLSET_OT_command_line_language(bpy.types.Operator):
    """Command language: Python. MEL is not supported in Blender"""
    bl_idname = "allset.command_line_language"
    bl_label = "Python"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        self.report({'WARNING'}, "MEL is not supported: the command line runs Python "
                                 "(cmds = a small maya.cmds subset; bpy, C, D as in the Python Console)")
        return {'FINISHED'}


class ALLSET_OT_script_editor(bpy.types.Operator):
    """Open the Maya Script Editor: history over input with MEL / Python tabs (ui/script_editor.py, step 105)"""
    bl_idname = "allset.script_editor"
    bl_label = "Script Editor"

    def execute(self, context):
        if context.window is None:
            return {'CANCELLED'}
        from ..ui import script_editor
        if script_editor.open_window(context) is None:
            self.report({'ERROR'}, "Could not open a new window")
            return {'CANCELLED'}
        return {'FINISHED'}


class ALLSET_MT_command_history(bpy.types.Menu):
    """Recent commands: click to run again"""
    bl_idname = "ALLSET_MT_command_history"
    bl_label = "Recent Commands"

    def draw(self, context):
        layout = self.layout
        if not runner.history:
            layout.label(text="No commands yet")
        for cmd in reversed(runner.history):
            text = cmd if len(cmd) <= 60 else cmd[:57] + "..."
            layout.operator(ALLSET_OT_command_line_exec.bl_idname, text=text).command = cmd


# --- Help Line ---------------------------------------------------------------------------

# Maya shows the tool's help in the Help Line when a tool is active (ui_layout.md:295-298).
TOOL_HELP = {
    "builtin.select": "Select Tool: click or drag to select. Shift toggles, Ctrl deselects, Ctrl+Shift adds",
    "builtin.move": "Move Tool: drag the manipulator. Hold X/C/V to snap to grid/curve/point, D to move the pivot",
    "builtin.rotate": "Rotate Tool: drag a ring to rotate. Hold J to snap rotation, D to move the pivot",
    "builtin.scale": "Scale Tool: drag a handle to scale, the centre scales uniformly",
    "builtin.transform": "Universal Manipulator: move, rotate and scale with one manipulator",
    "builtin.knife": "Multi-Cut: click on edges to cut, Enter to complete. Ctrl+click: edge loop, Shift: snap step",
    "builtin.loop_cut": "Insert Edge Loop: click an edge to insert a loop, drag to slide it",
    "builtin.poly_build": "Quad Draw: click to place points, Ctrl+click to delete",
    "allset.target_weld_tool": "Target Weld: drag a vertex or edge onto the target. Selected vertices are merged too",
    "allset.crease_tool": "Crease Tool: select edges or vertices, then middle-drag left to crease less, right for more",
}


def help_for_tool(idname):
    if idname.startswith("builtin.select"):  # select_box, select_lasso, ...
        return TOOL_HELP["builtin.select"]
    return TOOL_HELP.get(idname, "")


def help_text(context):
    try:
        tool = context.workspace.tools.from_space_view3d_mode(context.mode, create=False)
    except (AttributeError, TypeError):
        tool = None
    return help_for_tool(tool.idname) if tool else ""


# --- status bar --------------------------------------------------------------------------

# Maya 2022 puts the Help Line and the Command Line on one row, Help Line left (
# 128-131, :290-298); widths from the factory window (_maya_ui_dump.json HelpLine 675 px, CommandLine 915 px
# at 1600 px) in UI units (20 px at effective scale 1.0).
HELP_UNITS = 33.75
COMMAND_UNITS = 45.75
_blender_draw = []


def draw_help_line(layout, context):
    """Tool help, else Blender's mouse/key hints; reports and job progress after it (Maya's Help Line
    shows progress too)."""
    from ..ui import notices
    notices.remember_status_area(context.area)
    note = notices.current()   # a notice of the menu item under the mouse (step 54)
    text = note or help_text(context)
    if text:
        layout.label(text=text, icon='ERROR' if note else 'INFO')
    else:
        layout.template_input_status()
    layout.template_reports_banner()
    layout.template_running_jobs()


def draw_command_line(layout, context):
    wm = context.window_manager
    row = layout.row(align=True)
    row.operator(ALLSET_OT_command_line_language.bl_idname, text="Python")
    sub = row.row(align=True)
    sub.ui_units_x = 16
    sub.prop(wm, "allset_cmd", text="", placeholder="Python  (cmds.polyCube(), C.object ...)")
    sub = row.box().row()
    sub.alert = _result["error"]
    sub.label(text=_result["text"] or " ")
    row.menu(ALLSET_MT_command_history.bl_idname, text="", icon='RECOVER_LAST')
    row.operator(ALLSET_OT_script_editor.bl_idname, text="", icon='CONSOLE')


def draw_status_bar(self, context):
    """STATUSBAR_HT_header.draw while the kit is on: Help Line | Command Line, then Blender's
    scene statistics if there is room; Blender's own draw when both are off."""
    from .. import preferences
    try:
        prefs = preferences.get(context)
    except KeyError:
        prefs = None
    if prefs is None or not (prefs.show_help_line or prefs.show_command_line):
        return _blender_draw[0](self, context)
    layout = self.layout
    if prefs.show_help_line:
        row = layout.row()
        row.ui_units_x = HELP_UNITS
        draw_help_line(row, context)
    if prefs.show_command_line:
        row = layout.row()
        row.ui_units_x = COMMAND_UNITS
        draw_command_line(row, context)
    for func in getattr(_blender_draw[0], "_draw_funcs", ())[1:]:   # other add-ons' .append()ed items
        func(self, context)
    layout.separator_spacer()
    layout.template_status_info()


# --- `import maya.cmds` --------------------------------------------------------------------

_installed = []


def install_maya_module():
    """Make ``import maya.cmds`` give the shim, unless a real ``maya`` package exists."""
    if "maya" in sys.modules:
        return
    import importlib.util
    if importlib.util.find_spec("maya") is not None:
        return
    pkg = types.ModuleType("maya", "Allset stand-in package: only maya.cmds (cmds_shim)")
    pkg.__path__ = []
    pkg.cmds = cmds_shim
    sys.modules["maya"] = pkg
    sys.modules["maya.cmds"] = cmds_shim
    _installed.extend(("maya", "maya.cmds"))


def uninstall_maya_module():
    while _installed:
        sys.modules.pop(_installed.pop(), None)


classes = (ALLSET_OT_command_line_exec, ALLSET_OT_command_line_language,
           ALLSET_OT_script_editor, ALLSET_MT_command_history)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.WindowManager.allset_cmd = StringProperty(
        name="Command Line", description="Python command (Enter to run). MEL is not supported",
        options={'SKIP_SAVE'}, update=_on_command)
    _blender_draw.append(bpy.types.STATUSBAR_HT_header.draw)
    bpy.types.STATUSBAR_HT_header.draw = draw_status_bar
    install_maya_module()


def unregister():
    uninstall_maya_module()
    bpy.types.STATUSBAR_HT_header.draw = _blender_draw.pop()
    del bpy.types.WindowManager.allset_cmd
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    runner.reset()
    _result.update(text="", error=False)

