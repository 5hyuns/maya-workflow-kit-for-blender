"""In-Blender part of tools/release_check.py: first-start checks and docs/screenshots/.

Runs in a GUI Blender started on a clean sandbox config with the extension already
installed and enabled from the command line, with --enable-event-simulate (helpers
from tests/gui/sim.py). Each screenshot is taken one tick after the UI change
(``screen.screenshot`` shows the previous frame).
"""

import os
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tests" / "gui"))
import sim  # noqa: E402
from sim import MODULE, check, ev, run, setup, step, view3d, win  # noqa: E402

SHOTS = os.environ.get("MAYA_KIT_SHOTS", str(ROOT / "docs" / "screenshots"))
C = {"tries": 0}


def shot(name):
    sim.screenshot(os.path.join(SHOTS, name))


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


def v3d_override():
    area, region = view3d()
    return bpy.context.temp_override(window=win(), screen=win().screen, area=area, region=region)


def ui_region():
    return next(r for r in view3d()[0].regions if r.type == 'UI')


def goto_tab(category, then):
    def s_tab():
        r = ui_region()
        if r.active_panel_category != category and C["tries"] < 12:
            C["tries"] += 1
            ev('MOUSEMOVE', 'NOTHING', x=r.x + r.width - 8, y=r.y + r.height - 60)
            ev('WHEELDOWNMOUSE', 'PRESS', ctrl=True)
            sim._steps.insert(0, s_tab)
            return
        C["tries"] = 0
        check(f"sidebar shows the {category} tab", r.active_panel_category == category)
        then()
    return s_tab


@step
def s_first_start():
    prefs = bpy.context.preferences
    check("extension enabled by the command-line install", MODULE in prefs.addons)
    kc = bpy.context.window_manager.keyconfigs.active
    check(f"Maya keymap active on first start (got {kc.name if kc else None})",
          kc is not None and kc.name == "Maya")
    setup()   # closes the splash; the add-on is already enabled
    check("install the Maya layout template", bpy.ops.maya_kit.layout_install() == {'FINISHED'})
    bpy.ops.wm.read_homefile(app_template="MayaKit")


@step
def s_scene():
    kc = bpy.context.window_manager.keyconfigs.active
    check("Maya keymap still active after loading the layout", kc is not None and kc.name == "Maya")
    check("layout has the Maya strip (Status Line + Shelf)",
          bpy.data.masks.get(".MayaKitStrip") is not None)
    with v3d_override():
        bpy.ops.maya_kit.create(kind='SPHERE')
        bpy.context.active_object.location = (3.5, 0, 1)
        bpy.ops.maya_kit.create(kind='CYLINDER')
        bpy.context.active_object.location = (-3.5, 0, 1)
        bpy.data.objects["pSphere1"].select_set(True)
        bpy.ops.maya_kit.group()
        bpy.ops.maya_kit.create(kind='CUBE')
        cube = bpy.context.active_object
        cube.scale = (1.5, 1.5, 1.5)
        cube.modifiers.new("polySmooth1", 'SUBSURF')
        bpy.ops.maya_kit.shelf_material(kind='LAMBERT')
        bpy.ops.view3d.view_all(center=False)
    check("Maya names (pCube1, pSphere1, group1)",
          all(n in bpy.data.objects for n in ("pCube1", "pSphere1", "pCylinder1", "group1")))
    area, region = view3d()
    C["x"], C["y"] = region.x + region.width // 2, region.y + region.height // 2
    ev('MOUSEMOVE', 'NOTHING', x=C["x"], y=C["y"])
    redraw()


@step
def s_wait_layout():
    redraw()


@step
def s_layout():
    shot("01_layout.png")
    with bpy.context.temp_override(window=win()):
        bpy.ops.wm.call_menu(name="MAYAKIT_MT_mainCreateMenu")


@step
def s_menu():
    pass


@step
def s_menu_shot():
    shot("02_create_menu.png")
    ev('ESC', 'PRESS')
    ev('ESC', 'RELEASE')
    ev('MOUSEMOVE', 'NOTHING', x=C["x"], y=C["y"])
    ev('RIGHTMOUSE', 'PRESS', x=C["x"], y=C["y"])


@step
def s_mm_wait():
    redraw()


@step
def s_mm_shot():
    shot("03_marking_menu.png")
    ev('RIGHTMOUSE', 'RELEASE', x=C["x"], y=C["y"])   # released in the centre: nothing runs
    ev('ESC', 'PRESS')
    ev('ESC', 'RELEASE')


@step
def s_hotbox_press():
    ev('MOUSEMOVE', 'NOTHING', x=C["x"], y=C["y"])
    ev('SPACE', 'PRESS')


@step
def s_hotbox_wait():
    redraw()


@step
def s_hotbox_shot():
    shot("04_hotbox.png")
    ev('SPACE', 'RELEASE')


@step
def s_ae():
    with v3d_override():
        bpy.ops.maya_kit.ae_toggle()
        bpy.ops.maya_kit.ae_tab(key="T")
    redraw()


def _after_cb():
    redraw()


step(goto_tab("Channel Box", _after_cb))


@step
def s_ae_wait():
    redraw()


@step
def s_ae_shot():
    shot("05_attribute_editor.png")
    with v3d_override():
        bpy.ops.maya_kit.ae_tab(key="M:polySmooth1")
    redraw()


@step
def s_ae_hist_wait():
    redraw()


@step
def s_ae_hist_shot():
    shot("06_attribute_editor_history.png")
    with v3d_override():
        bpy.ops.maya_kit.ae_toggle()
    wm = bpy.context.window_manager
    wm.maya_kit_outliner_shapes = True
    bpy.data.objects["group1"].maya_kit_expanded = True
    bpy.data.objects["pCube1"].maya_kit_expanded = True
    bpy.ops.maya_kit.shelf_select(shelf="Rigging")
    redraw()


def _after_outliner():
    redraw()


step(goto_tab("Outliner", _after_outliner))


@step
def s_outliner_wait():
    redraw()


@step
def s_outliner_shot():
    shot("07_outliner_rigging_shelf.png")
    bpy.ops.maya_kit.shelf_select(shelf="Polygons")


run(interval=0.5, first=3.0)
