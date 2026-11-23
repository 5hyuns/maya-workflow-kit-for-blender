"""Switching Maya mode off and on again in a real UI takes the kit's UV Editor tools (UV brushes, Lattice) out of the
UV Editor toolbar and puts them back each time: no "Unable to remove" on the way out, each tool once in the toolbar on
the way back, and the tools can be made active again. Also when the UV manipulator preference is switched while
Blender mode is on: Blender's UV Move / Rotate / Scale tools keep Blender's own gizmos then."""

import io
import os
import sys
from contextlib import redirect_stderr, redirect_stdout
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, run, setup, step, view3d, win  # noqa: E402

C = {}
ROUNDS = 3
LAYOUT = True       # the Maya layout on the way in, Blender's on the way out, like the Maya / Blender buttons


def mod(name):
    return import_module(sys.modules["sim"].MODULE + name)


def kit_ids():
    return [t.bl_idname for t in mod(".ui.uv_brush_tools").TOOLS]


def toolbar_ids():
    """bl_idname of every tool in the UV Editor's UV toolbar (groups flattened)."""
    from bl_ui.space_toolsystem_common import ToolDef, ToolSelectPanelHelper
    cls = ToolSelectPanelHelper._tool_class_from_space_type('IMAGE_EDITOR')
    out = []
    for item in cls._tools['UV']:
        group = (item,) if isinstance(item, ToolDef) or not isinstance(item, tuple) else item
        out += [t.idname for t in group if isinstance(t, ToolDef)]
    return out


def blender_widgets():
    """True when the UV toolbar's Move / Rotate / Scale tools use Blender's own gizmos."""
    from bl_ui.space_toolsystem_common import ToolDef, ToolSelectPanelHelper
    cls = ToolSelectPanelHelper._tool_class_from_space_type('IMAGE_EDITOR')
    defs = []
    for item in cls._tools['UV']:
        group = (item,) if isinstance(item, ToolDef) or not isinstance(item, tuple) else item
        defs += [t for t in group if isinstance(t, ToolDef)]
    um = mod(".ui.uv_manipulator")
    return all(t.widget in um.BLENDER_WIDGETS for t in defs if t.idname in um.TOOLS)


def uv_window():
    for w in bpy.context.window_manager.windows:
        for a in w.screen.areas:
            if a.ui_type == 'UV':
                return w, a, next(r for r in a.regions if r.type == 'WINDOW')
    return None, None, None


@step
def s_setup():
    setup()
    cube = bpy.data.objects["Cube"]
    bpy.context.view_layer.objects.active = cube
    cube.select_set(True)
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        C["open"] = mod(".marking.modal").run_action(bpy.context, mod(".ui.menu_map").MAP["UV/UV Editor"])


@step
def s_wait_uv_window():
    import sim
    C.setdefault("wait_uv", 0)
    if uv_window()[1] is None and C["wait_uv"] < 15:
        C["wait_uv"] += 1
        sim._steps.insert(0, s_wait_uv_window)


@step
def s_use_tools():
    w, a, r = uv_window()
    check(f"UV Editor open ({C['open']})", a is not None)
    ids = toolbar_ids()
    check("every kit UV tool once in the UV toolbar at the start", all(ids.count(i) == 1 for i in kit_ids()))
    if a is None:
        return
    with bpy.context.temp_override(window=w, area=a, region=r):     # each tool made active once, Lattice last
        for i in kit_ids():
            bpy.ops.wm.tool_set_by_id(name=i, space_type='IMAGE_EDITOR')


def _switch(on, round_no):
    out = io.StringIO()
    with redirect_stdout(out), redirect_stderr(out):
        mod(".switch").set_mode(on, layout=LAYOUT)
    text = out.getvalue()
    sys.stdout.write(text)
    word = "on" if on else "off"
    check(f"round {round_no}: Maya mode {word} without an unregister error",
          "Unable to remove" not in text and "failed" not in text)
    ids = toolbar_ids()
    if on:
        check(f"round {round_no}: every kit UV tool back once ({[ids.count(i) for i in kit_ids()]})",
              all(ids.count(i) == 1 for i in kit_ids()))
    else:
        check(f"round {round_no}: no kit UV tool left in the toolbar ({[i for i in kit_ids() if i in ids]})",
              not any(i in ids for i in kit_ids()))


def _round(k):
    def off():
        _switch(False, k)

    def on():
        _switch(True, k)
        w, a, r = uv_window()
        if a is None:
            return
        with bpy.context.temp_override(window=w, area=a, region=r):
            for i in kit_ids():
                bpy.ops.wm.tool_set_by_id(name=i, space_type='IMAGE_EDITOR')
            active = bpy.context.workspace.tools.from_space_image_mode('UV').idname
        check(f"round {k}: the last kit tool is active again ({active})", active == kit_ids()[-1])
    def again():        # the Maya button while Maya mode is already on: keys and layout put back
        mod(".switch").set_mode(True, layout=LAYOUT)
    step(again)
    step(lambda: None)
    def prefs_toggle():     # the UV manipulator preference switched off and on while Blender mode is on
        prefs = mod(".preferences").get()
        prefs.maya_uv_manipulator = False
        prefs.maya_uv_manipulator = True
        check(f"round {k}: Blender mode keeps Blender's UV gizmos after the preference switch", blender_widgets())
    step(off)
    step(lambda: None)
    step(prefs_toggle)
    step(on)
    step(lambda: None)


for _k in range(1, ROUNDS + 1):
    _round(_k)

run()
