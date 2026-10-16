"""Step 7 in a real UI: Maya top bar (menus, menu sets, Status Line), command line typing,
undo, Help Line, Script Editor window, tool switch from a menu; screenshots."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, step, setup, screenshot, tap, view3d, win  # noqa: E402

SHOTS = os.environ.get("MAYA_KIT_GUI_SHOTS", "")
C = {}


def shot(name):
    if SHOTS:
        screenshot(os.path.join(SHOTS, name))


def prefs():
    return bpy.context.preferences.addons[MODULE].preferences


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


@step
def s_setup():
    setup()
    check("install layout", bpy.ops.maya_kit.layout_install() == {'FINISHED'})
    bpy.ops.wm.read_homefile(app_template="MayaKit")


@step
def s_wait():
    # --factory-startup: switching app template reloads factory preferences, so the
    # "Maya" keyconfig is not active any more (a user's saved prefs keep it).
    bpy.ops.maya_kit.keymap_activate()
    C["cl"] = import_module(MODULE + ".command_line")
    C["sl"] = import_module(MODULE + ".ui.status_line")
    area, r = view3d()
    C["mid"] = (r.x + r.width // 2, r.y + r.height // 2)
    ev('MOUSEMOVE', 'NOTHING', x=C["mid"][0], y=C["mid"][1])
    redraw()


@step
def s_topbar():
    cls = bpy.types.TOPBAR_HT_upper_bar
    check("top bar draws the Maya menu bar", cls.draw_left is C["sl"].draw_left)
    area, _r = view3d()
    check("main 3D View shows the tool header row (Status Line)", area.spaces.active.show_region_tool_header)
    shot("gui_step7_topbar_modeling.png")
    prefs().menu_set = 'riggingMenuSet'
    # The top bar is a global area (not in screen.areas): hovering it redraws it.
    ev('MOUSEMOVE', 'NOTHING', x=800, y=win().height - 12)


@step
def s_rigging_redraw():
    ev('MOUSEMOVE', 'NOTHING', x=820, y=win().height - 12)


@step
def s_rigging():
    shot("gui_step7_topbar_rigging.png")
    prefs().menu_set = 'modelingMenuSet'
    # Open a Maya menu as Blender would (same Menu class the menu bar uses).
    with bpy.context.temp_override(window=win()):
        bpy.ops.wm.call_menu(name="MAYAKIT_MT_mainMeshMenu")


@step
def s_menu_open():
    shot("gui_step7_mesh_menu.png")
    tap('ESC')
    # Type into the command line: click the field in the status bar (bottom row).
    C["n0"] = len(bpy.data.objects)
    ev('MOUSEMOVE', 'NOTHING', x=200, y=12)  # hover first, so the field is the active button
    ev('LEFTMOUSE', 'PRESS', x=200, y=12)
    ev('LEFTMOUSE', 'RELEASE', x=200, y=12)


@step
def s_type():
    for ch in "cmds.polyCube(w=200, h=200, d=200)":
        ev('TEXTINPUT', 'PRESS', unicode=ch)
    ev('RET', 'PRESS')
    ev('RET', 'RELEASE')


@step
def s_typed():
    res = C["cl"]._result
    check(f"typed command ran: result {res['text']!r}", res["text"].startswith("# Result: ['pCube1'"))
    check("cube created by cmds.polyCube", "pCube1" in bpy.data.objects)
    check("command field cleared", bpy.context.window_manager.maya_kit_cmd == "")
    redraw()


@step
def s_cmd_shot():
    shot("gui_step7_command_line.png")
    ev('MOUSEMOVE', 'NOTHING', x=C["mid"][0], y=C["mid"][1])
    ev('Z', 'PRESS', ctrl=True)
    ev('Z', 'RELEASE', ctrl=True)


@step
def s_undo():
    check("Ctrl+Z undoes the whole command (one step)", "pCube1" not in bpy.data.objects)
    # Error result: red field.
    bpy.context.window_manager.maya_kit_cmd = "polyCube -w 2;"
    redraw()


@step
def s_error_shot():
    res = C["cl"]._result
    check("MEL input -> error with Python hint", res["error"] and "cmds.polyCube(w=2)" in res["text"])
    shot("gui_step7_mel_error.png")
    # Holding X lights the grid snap button in the Status Line.
    bpy.ops.mesh.primitive_cube_add()
    with bpy.context.temp_override(window=win()):
        bpy.ops.wm.tool_set_by_id(name="builtin.move", space_type='VIEW_3D')
    ev('X', 'PRESS')


@step
def s_hold():
    ts = bpy.context.scene.tool_settings
    check("X held: grid snap on (Status Line button lit)", C["sl"].snap_on(ts, "GRID"))
    redraw()


@step
def s_hold_shot():
    shot("gui_step7_hold_x.png")
    ev('X', 'RELEASE')


@step
def s_release():
    ts = bpy.context.scene.tool_settings
    check("X released: grid snap off again", not C["sl"].snap_on(ts, "GRID"))
    check("Help Line text for the Move tool", "Move Tool" in C["cl"].help_text(bpy.context))
    # Tool switch from a Maya menu item (fails headless: no tool keymaps in -b).
    with bpy.context.temp_override(window=win()):
        bpy.ops.maya_kit.menu_tool(tool="builtin.knife", edit=True)
    tool = bpy.context.workspace.tools.from_space_view3d_mode('EDIT_MESH', create=False)
    check("Mesh Tools > Multi-Cut: edit mode + knife tool",
          bpy.context.mode == 'EDIT_MESH' and tool is not None and tool.idname == "builtin.knife")
    bpy.ops.object.mode_set(mode='OBJECT')
    # A "v3d" item: runs in the 3D View (Display > Grid).
    v3d = view3d()[0].spaces.active
    C["floor"] = v3d.overlay.show_floor
    with bpy.context.temp_override(window=win()):
        bpy.ops.maya_kit.menu_run(op="wm.context_toggle",
                                  props='{"data_path": "space_data.overlay.show_floor"}')
    check("Display > Grid toggles the viewport grid", v3d.overlay.show_floor != C["floor"])
    v3d.overlay.show_floor = C["floor"]
    C["windows"] = len(bpy.context.window_manager.windows)
    with bpy.context.temp_override(window=win()):
        bpy.ops.maya_kit.script_editor()


@step
def s_script_editor():
    wins = bpy.context.window_manager.windows
    check("Script Editor opens a new window", len(wins) == C["windows"] + 1)
    if len(wins) > C["windows"]:
        new = wins[len(wins) - 1]
        check("new window is a Python Console", new.screen.areas[0].type == 'CONSOLE')
        if SHOTS:
            with bpy.context.temp_override(window=new):
                bpy.ops.screen.screenshot(filepath=os.path.join(SHOTS, "gui_step7_script_editor.png"))
        with bpy.context.temp_override(window=new):
            bpy.ops.wm.window_close()
    # Tool Settings button: the active tool's settings as a popup.
    with bpy.context.temp_override(window=win()):
        bpy.ops.maya_kit.editor_toggle(editor="TOOL_SETTINGS")


@step
def s_tool_settings():
    shot("gui_step7_tool_settings.png")
    tap('ESC')
    bpy.ops.maya_kit.layout_remove()


run()
