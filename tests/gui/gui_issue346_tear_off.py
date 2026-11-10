"""#346: a viewport torn off the Maya Workflow Kit layout keeps its Maya panel menu bar and panel toolbar.

Panels > Tear Off Copy... and Panels > Tear Off... open the view in a window of its own. Like a torn-off Maya model
panel, that window's 3D View shows the panel menu bar (View Shading Lighting Show Renderer Panels) and the panel
toolbar under it — not Blender's 3D View header and not a second Status Line. The main window stays as it was;
closing the windows and turning the kit off leave nothing of it behind. Shots with ``--shots``."""

import os
import sys
from importlib import import_module

import addon_utils
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, load_maya_layout, run, setup, step, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {"bar": {}, "toolbar": set(), "status": set(), "windows": []}


def mod(name):
    return import_module(f"{MODULE}.{name}")


def main_view():
    return max((a for a in win().screen.areas if a.type == 'VIEW_3D'), key=lambda a: a.width * a.height)


def new_windows():
    return [w for w in bpy.context.window_manager.windows if w.as_pointer() not in C["before"]]


def redraw_all():
    for w in bpy.context.window_manager.windows:
        for a in w.screen.areas:
            a.tag_redraw()


def record_draws():
    """Record what the 3D View headers draw: the header / tool header branch (Maya bar or Blender's), the Maya
    panel toolbar and the kit's Status Line, by area."""
    pt, sl = mod("ui.panel_toolbar"), mod("ui.status_line")
    maya_layout, draw_toolbar, draw_status_line = pt.maya_layout, pt.draw_toolbar, sl.draw_status_line

    def rec_layout(context):
        got = maya_layout(context)
        region = getattr(context, "region", None)
        if context.area is not None and region is not None:
            C["bar"][(context.area.as_pointer(), region.type)] = got
        return got

    def rec_toolbar(layout, context):
        if context.area is not None:
            C["toolbar"].add(context.area.as_pointer())
        return draw_toolbar(layout, context)

    def rec_status(layout, context, *a, **kw):
        if context.area is not None and context.area.type == 'VIEW_3D':
            C["status"].add(context.area.as_pointer())
        return draw_status_line(layout, context, *a, **kw)

    pt.maya_layout, pt.draw_toolbar, sl.draw_status_line = rec_layout, rec_toolbar, rec_status


def forget():
    C["bar"].clear()
    C["toolbar"].clear()
    C["status"].clear()
    redraw_all()


def tear_off(copy):
    def run_it():
        C["before"] = {w.as_pointer() for w in bpy.context.window_manager.windows}
        area = main_view()
        header = next(r for r in area.regions if r.type == 'HEADER')
        with bpy.context.temp_override(window=win(), area=area, region=header):
            res = bpy.ops.allset.panel_run(op="allset.panel_tear_off", props='{"copy": %s}' % str(copy).lower())
        C["res"] = res
        forget()
    return run_it


def check_window(label):
    def look():
        new = new_windows()
        check(f"{label}: opened one window ({C['res']})", len(new) == 1)
        if not new:
            return
        window = new[0]
        C["windows"].append(window.as_pointer())
        area = window.screen.areas[0]
        ptr = area.as_pointer()
        check(f"{label}: the window holds one 3D View ({[a.type for a in window.screen.areas]})",
              len(window.screen.areas) == 1 and area.type == 'VIEW_3D')
        check(f"{label}: its header is the Maya panel menu bar ({C['bar'].get((ptr, 'HEADER'))})",
              C["bar"].get((ptr, 'HEADER')) is True)
        check(f"{label}: its tool header is the Maya panel toolbar ({C['bar'].get((ptr, 'TOOL_HEADER'))})",
              C["bar"].get((ptr, 'TOOL_HEADER')) is True and ptr in C["toolbar"])
        check(f"{label}: no Status Line in the torn-off view", ptr not in C["status"])
        check(f"{label}: the tool header row is shown", area.spaces.active.show_region_tool_header)
        main = main_view().as_pointer()
        check(f"{label}: the main viewport keeps its Maya bar and toolbar",
              C["bar"].get((main, 'HEADER')) is True and main in C["toolbar"] and main not in C["status"])
        check(f"{label}: the main window keeps the Maya strip",
              mod("ui.shelf").strip_area(win().screen) is not None)
        if SHOTS:
            with bpy.context.temp_override(window=window):
                bpy.ops.screen.screenshot(filepath=os.path.join(SHOTS, f"gui_issue346_{label.replace(' ', '_')}.png"))
    return look


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_hooks():
    record_draws()
    C["main_areas"] = len(win().screen.areas)
    forget()


@step
def s_main_before():
    main = main_view().as_pointer()
    check("before: the main viewport draws the Maya bar and toolbar, no Status Line in its tool header",
          C["bar"].get((main, 'HEADER')) is True and main in C["toolbar"] and main not in C["status"])


step(tear_off(True))
step(lambda: forget())
step(lambda: None)
step(check_window("Tear Off Copy"))
step(tear_off(False))
step(lambda: forget())
step(lambda: None)
step(check_window("Tear Off"))


@step
def s_undo():
    # the windows are UI, not scene data: an undo keeps them and their bars
    area = main_view()
    with bpy.context.temp_override(window=win(), area=area):
        try:
            bpy.ops.ed.undo()
        except RuntimeError:
            pass
    forget()


@step
def s_after_undo():
    torn = [w for w in bpy.context.window_manager.windows if w.as_pointer() in C["windows"]]
    ptrs = [w.screen.areas[0].as_pointer() for w in torn]
    check(f"after an undo the torn-off views keep the Maya bar ({len(torn)} windows)",
          len(torn) == 2 and all(C["bar"].get((p, 'HEADER')) is True for p in ptrs))


@step
def s_close():
    for w in list(bpy.context.window_manager.windows):
        if w.as_pointer() in C["windows"]:
            with bpy.context.temp_override(window=w):
                bpy.ops.wm.window_close()
    forget()


@step
def s_after_close():
    check(f"closing the windows leaves the main window as it was ({len(win().screen.areas)} areas)",
          len(bpy.context.window_manager.windows) == 1 and len(win().screen.areas) == C["main_areas"])
    main = main_view().as_pointer()
    check("the main viewport still draws the Maya bar and toolbar",
          C["bar"].get((main, 'HEADER')) is True and main in C["toolbar"])


@step
def s_disable():
    # a torn-off window open while the kit is turned off: Blender's own header draws come back
    C["before"] = {w.as_pointer() for w in bpy.context.window_manager.windows}
    area = main_view()
    header = next(r for r in area.regions if r.type == 'HEADER')
    with bpy.context.temp_override(window=win(), area=area, region=header):
        bpy.ops.allset.panel_tear_off()
    pt, sl = mod("ui.panel_toolbar"), mod("ui.status_line")
    C["kit_draws"] = (pt._header, pt._tool_header, sl.draw_tool_header)
    addon_utils.disable(MODULE, default_set=True)


@step
def s_after_disable():
    funcs = (list(bpy.types.VIEW3D_HT_header._dyn_ui_initialize())
             + list(bpy.types.VIEW3D_HT_tool_header._dyn_ui_initialize()))
    left = [f for f in funcs if f in C["kit_draws"]]
    check(f"kit off: no kit draw left in the 3D View headers ({left})", not left)
    check("kit off: the torn-off window is still there with its 3D View",
          any(w.screen.areas[0].type == 'VIEW_3D' for w in new_windows()))


run()
