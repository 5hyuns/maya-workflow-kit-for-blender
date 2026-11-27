"""#583 in a real UI: a cube in component mode (face) -> click the Polygon Sphere / Polygon Cube shelf buttons -> each
click makes the primitive and goes back to object mode, like Maya; with Interactive Creation on the click leaves
component mode and the creation tool is current."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, load_maya_layout, run, scale, screenshot, setup, step, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}
shelf = import_module(MODULE + ".ui.shelf")


def redraw():
    for w in bpy.context.window_manager.windows:
        for a in w.screen.areas:
            a.tag_redraw()


def icon_centre(slot):
    area = shelf.shelf_row_area(win().screen)
    r = next(r for r in area.regions if r.type == 'WINDOW')
    x, y, size = shelf.icon_rect(r, slot, scale())
    return round(r.x + x + size / 2), round(r.y + y + size / 2)


def prefs():
    return import_module(MODULE + ".preferences").get(bpy.context)


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_scene():
    bpy.ops.allset.keymap_activate()
    bpy.ops.allset.make_maya(open_layout=False)
    bpy.ops.allset.shelf_select(shelf="Polygons")
    redraw()


def component_mode():
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        for ob in list(bpy.data.objects):
            bpy.data.objects.remove(ob)
        bpy.ops.allset.create(kind='CUBE')
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='FACE')
    C["first"] = bpy.context.view_layer.objects.active.name
    C["n0"] = len(bpy.data.objects)
    redraw()


def click_case(label, interactive):
    @step
    def s_prepare():
        prefs().interactive_creation = False
        component_mode()
        prefs().interactive_creation = interactive
        _cur, buttons = shelf.icon_buttons(bpy.context)
        slot = next(k for k, b in enumerate(buttons) if b[1] == label)
        x, y = icon_centre(slot)
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
        redraw()

    @step
    def s_click():
        check(f"{label}: the cube is in component mode before the click ({bpy.context.mode})",
              bpy.context.mode == 'EDIT_MESH')
        ev('LEFTMOUSE', 'PRESS')
        ev('LEFTMOUSE', 'RELEASE')

    step(lambda: None)

    @step
    def s_check():
        names = [ob.name for ob in bpy.data.objects]
        mode = bpy.context.mode
        if SHOTS:
            screenshot(os.path.join(SHOTS, f"gui_issue583_{label.split()[-1].lower()}_{int(interactive)}.png"))
        check(f"{label} (Interactive Creation {interactive}): back in object mode ({mode})", mode == 'OBJECT')
        if interactive:
            tool = bpy.context.workspace.tools.from_space_view3d_mode('OBJECT', create=False)
            check(f"the creation tool is current ({tool.idname if tool else None})",
                  tool is not None and tool.idname == import_module(MODULE + ".operators.interactive_create").TOOL)
        else:
            check(f"{label} made one new object ({names})", len(names) == C["n0"] + 1)
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")


click_case("Polygon Sphere", False)
click_case("Polygon Cube", False)
click_case("Polygon Cube", True)


@step
def s_restore():
    prefs().interactive_creation = False


run()
