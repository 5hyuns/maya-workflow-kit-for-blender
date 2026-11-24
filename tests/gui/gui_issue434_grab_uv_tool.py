"""#434 in a real UI: UV > 3D Grab UV Tool picked from the main menu over the 3D View raises no Python error and
sets the UV Editor's Grab tool: in the open UV Editor, or in a UV Editor window it opens when there is none."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, run, step, setup, win, view3d, load_maya_layout  # noqa: E402

C = {}
uv_components = import_module(MODULE + ".operators.uv_components")
GRAB = "allset.uv_brush_grab"        # the kit's UV Grab brush tool (#517)
ITEM = "UV/3D Grab UV Tool"


def windows():
    return list(bpy.context.window_manager.windows)


def uv_tool(area):
    for w in windows():
        if any(x == area for x in w.screen.areas):
            with bpy.context.temp_override(window=w, area=area):
                tool = bpy.context.workspace.tools.from_space_image_mode(area.spaces.active.mode)
            return tool.idname if tool else None
    return None


def close_extra_windows():
    for w in windows()[1:]:
        with bpy.context.temp_override(window=w):
            bpy.ops.wm.window_close()


def run_item():
    area, region = view3d()
    errors = []
    with bpy.context.temp_override(window=win(), area=area, region=region):
        try:
            res = bpy.ops.allset.menu_item(item=ITEM)
        except Exception as ex:  # a Python error in the tool lookup comes back as RuntimeError
            res, errors = None, [repr(ex)]
    return res, errors


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_scene():
    bpy.ops.allset.keymap_activate()
    bpy.ops.allset.make_maya(open_layout=False)
    bpy.ops.allset.create(kind='CUBE')
    close_extra_windows()
    C["n0"] = len(windows())
    check("no UV Editor is open", uv_components.find_uv_editor(bpy.context)[1] is None)
    C["res"], C["err"] = run_item()


for _k in range(6):         # the window opens on a later tick
    step(lambda: None)


@step
def s_opened():
    check(f"the menu item ran without a Python error ({C['res']}, {C['err']})",
          C["res"] == {'FINISHED'} and not C["err"])
    w, a = uv_components.find_uv_editor(bpy.context)
    check(f"a UV Editor window opened ({C['n0']} -> {len(windows())})", a is not None and len(windows()) > C["n0"])
    check(f"the UV Editor's tool is Grab ({uv_tool(a) if a else None})", a is not None and uv_tool(a) == GRAB)
    w, a = uv_components.find_uv_editor(bpy.context)
    with bpy.context.temp_override(window=w, area=a):
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box", space_type='IMAGE_EDITOR')
    C["n1"] = len(windows())
    C["res"], C["err"] = run_item()


for _k in range(3):
    step(lambda: None)


@step
def s_existing():
    w, a = uv_components.find_uv_editor(bpy.context)
    check(f"with a UV Editor open, it runs without an error ({C['res']}, {C['err']})",
          C["res"] == {'FINISHED'} and not C["err"])
    check(f"no second window opens ({C['n1']} -> {len(windows())})", len(windows()) == C["n1"])
    check(f"the open UV Editor's tool is Grab again ({uv_tool(a) if a else None})", a is not None and uv_tool(a) == GRAB)
    close_extra_windows()


run()
