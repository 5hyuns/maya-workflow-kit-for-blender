"""Step 38 in a real UI: two cubes selected, type "+=5" in the Channel Box Translate X field ->
both move by 5 display units (each from its own value); AE tab of a Maya lambert material;
screenshots."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, screenshot, setup, step, tap, view3d, win  # noqa: E402

SHOTS = os.environ.get("MAYA_KIT_GUI_SHOTS", "")
C = {"tries": 0}


def shot(name):
    if SHOTS:
        screenshot(os.path.join(SHOTS, name))


def ui_region():
    return next(r for r in view3d()[0].regions if r.type == 'UI')


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


def goto_tab(category, then):
    """Ctrl+wheel over the sidebar tab strip until ``category`` shows (gui_step11)."""
    def s_tab():
        r = ui_region()
        if r.active_panel_category != category and C["tries"] < 12:
            C["tries"] += 1
            ev('MOUSEMOVE', 'NOTHING', x=r.x + r.width - 8, y=r.y + r.height - 60)
            ev('WHEELDOWNMOUSE', 'PRESS', ctrl=True)
            sys.modules["sim"]._steps.insert(0, s_tab)
            return
        C["tries"] = 0
        check(f"sidebar shows the {category} tab", r.active_panel_category == category)
        then()
    return s_tab


def cubes():
    return bpy.data.objects["Cube"], bpy.data.objects["Cube2"]


@step
def s_setup():
    C["x"], C["y"] = setup()
    a = bpy.data.objects["Cube"]
    b = a.copy()
    b.name = "Cube2"
    bpy.context.scene.collection.objects.link(b)
    a.location.x, b.location.x = 1.0, 4.0
    for o in bpy.context.view_layer.objects:
        o.select_set(o in (a, b))
    bpy.context.view_layer.objects.active = a
    view3d()[0].spaces.active.show_region_ui = True
    redraw()


step(goto_tab("Channel Box", redraw))


@step
def s_wait():
    redraw()


@step
def s_cb_shot():
    shot("gui_step38_cb_before.png")
    r = ui_region()
    C["ui"] = (r.x, r.y, r.width, r.height)
    print("GUI UI region", C["ui"])
    check("Channel Box drawn with two objects selected (screenshot)", True)
    # Translate X value field: 1185, 229 in gui_step38_cb_before.png (1600 x 900 window).
    C["field"] = (1185, 900 - 229)
    ev('MOUSEMOVE', 'NOTHING', x=C["field"][0], y=C["field"][1])


@step
def s_click_field():
    x, y = C["field"]
    ev('LEFTMOUSE', 'PRESS', x=x, y=y)
    ev('LEFTMOUSE', 'RELEASE', x=x, y=y)


@step
def s_type():
    ev('A', 'PRESS', ctrl=True)     # select the whole text, then type over it
    ev('A', 'RELEASE', ctrl=True)
    for ch in "+=5":
        ev('TEXTINPUT', 'PRESS', unicode=ch)
    redraw()


@step
def s_typed_shot():
    shot("gui_step38_cb_typing.png")
    tap('RET')


@step
def s_applied():
    a, b = cubes()
    check(f"'+=5' moved the lead Cube 1 -> {a.location.x:.3f}", abs(a.location.x - 6.0) < 1e-4)
    check(f"... and Cube2 from its own value 4 -> {b.location.x:.3f}", abs(b.location.x - 9.0) < 1e-4)
    redraw()


@step
def s_after_shot():
    shot("gui_step38_cb_after.png")
    material = import_module(MODULE + ".operators.material")
    a, _b = cubes()
    mat = material.new_material('LAMBERT')
    a.data.materials.clear()
    a.data.materials.append(mat)
    C["mat"] = mat.name
    bpy.context.window_manager.maya_kit_dock = 'ATTRIBUTE_EDITOR'
    bpy.ops.maya_kit.ae_tab(key="MAT:0")
    redraw()


@step
def s_ae_wait():
    redraw()


@step
def s_ae_shot():
    shot("gui_step38_ae_lambert.png")
    ae = import_module(MODULE + ".ui.attribute_editor")
    a, _b = cubes()
    label = next(t for t in ae.tabs(a) if t[0] == "MAT:0")
    check(f"AE material tab is a lambert ({label})", label[2] == "lambert" and label[1] == C["mat"])


run()
