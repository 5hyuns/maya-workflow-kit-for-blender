"""Step 31 in a real UI: Maya Workflow Kit layout Outliner (width, DAG rows), leaving four views keeps the
picked view's name, W hold menu toggles show their state (engine and pie fallback), timeline;
screenshots."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, step, setup, screenshot, view3d, win, load_maya_layout  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def shot(name):
    if SHOTS:
        screenshot(os.path.join(SHOTS, name))


def prefs():
    return bpy.context.preferences.addons[MODULE].preferences


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


def main_view():
    return max((a for a in win().screen.areas if a.type == 'VIEW_3D'), key=lambda a: a.width * a.height)


def left_outliner():
    return min((a for a in win().screen.areas if a.type == 'OUTLINER'), key=lambda a: a.x)


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_scene():
    bpy.ops.allset.keymap_activate()
    for kind in ('CUBE', 'SPHERE', 'CYLINDER'):
        bpy.ops.allset.create(kind=kind)
    bpy.ops.object.select_all(action='DESELECT')
    bpy.data.objects["pCube1"].select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects["pCube1"]
    bpy.ops.allset.group()   # group1 > pCube1, like the step-23 audit scene
    area = main_view()
    ev('MOUSEMOVE', 'NOTHING', x=area.x + area.width // 2, y=area.y + area.height // 2)
    redraw()


@step
def s_layout():
    so = left_outliner()
    sp = so.spaces.active
    C["outliner_w"] = so.width
    check(f"left Outliner ~20% of the window ({so.width} px)", so.width >= 250)
    check("Outliner = Maya DAG: objects only, no collection rows, no render column",
          not sp.use_filter_collection and not sp.show_restrict_column_render
          and not sp.use_filter_object_content)
    redraw()


@step
def s_layout_shot():
    shot("gui_step31_layout.png")
    area = main_view()
    region = next(r for r in area.regions if r.type == 'WINDOW')
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.allset.toggle_quad_view()
    C["area"] = area


@step
def s_quad():
    area = C["area"]
    quads = [r for r in area.regions if r.type == 'WINDOW']
    print("STATE quads", len(area.spaces.active.region_quadviews), len(quads))
    check("four views on", len(quads) == 4)
    # Top-left quad = Top (Blender's quad order: left column front/top, ...): hover it.
    tl = max((r for r in quads), key=lambda r: (r.y, -r.x))
    C["tl"] = tl
    ev('MOUSEMOVE', 'NOTHING', x=tl.x + tl.width // 2, y=tl.y + tl.height // 2)


@step
def s_quad_shot():
    shot("gui_step31_quad.png")
    tl = C["tl"]
    rv = tl.data
    C["picked"] = (rv.view_perspective, rv.is_orthographic_side_view)
    with bpy.context.temp_override(window=win(), area=C["area"], region=tl):
        bpy.ops.allset.toggle_quad_view()


@step
def s_single():
    rv = C["area"].spaces.active.region_3d
    print("STATE picked", C["picked"], "single", rv.view_perspective, rv.is_orthographic_side_view)
    check("back to one view", not C["area"].spaces.active.region_quadviews)
    check("the kept view is still a named axis view (header 'Top Orthographic', not 'User')",
          rv.view_perspective == 'ORTHO' and rv.is_orthographic_side_view == C["picked"][1] is True)
    redraw()


@step
def s_single_shot():
    shot("gui_step31_quad_back.png")
    area = C["area"]
    region = next(r for r in area.regions if r.type == 'WINDOW')
    region.data.view_perspective = 'PERSP'
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.allset.view_home()   # Maya persp again for the menu shots
    bpy.context.scene.frame_set(8)
    redraw()


@step
def s_timeline_shot():
    shot("gui_step31_timeline_f8.png")
    area = C["area"]
    x, y = area.x + area.width // 3, area.y + area.height // 2
    C["w"] = (x, y)
    bpy.ops.object.select_all(action='DESELECT')
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('W', 'PRESS', x=x, y=y)
    ev('LEFTMOUSE', 'PRESS', x=x, y=y)


@step
def s_w_wait():
    redraw()


@step
def s_w_shot():
    draw = import_module(MODULE + ".marking.draw")
    s = draw.ACTIVE.get("session")
    labels = [i.label for i in s.layout.items] if s else []
    check("W + LMB opens the Move tool options with Smart Duplicate", "Smart Duplicate" in labels)
    shot("gui_step31_w_menu.png")
    x, y = C["w"]
    tap_esc(x, y)


def tap_esc(x, y):
    ev('ESC', 'PRESS', x=x, y=y)
    ev('ESC', 'RELEASE', x=x, y=y)
    ev('LEFTMOUSE', 'RELEASE', x=x, y=y)
    ev('W', 'RELEASE', x=x, y=y)


@step
def s_pie():
    marking = import_module(MODULE + ".marking")
    prefs().marking_menu_style = 'PIE'
    x, y = C["w"]
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    with bpy.context.temp_override(window=win(), area=C["area"]):
        bpy.ops.wm.call_menu_pie(name=marking.idname("translateMarkingMenuImpl"))


@step
def s_pie_wait():
    redraw()


@step
def s_pie_shot():
    shot("gui_step31_w_pie.png")
    x, y = C["w"]
    ev('ESC', 'PRESS', x=x, y=y)
    ev('ESC', 'RELEASE', x=x, y=y)
    prefs().marking_menu_style = 'ENGINE'


run()
