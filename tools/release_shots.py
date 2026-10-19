"""In-Blender part of tools/release_check.py: first-start checks and docs/screenshots/.

Runs in a GUI Blender started on a clean sandbox config with the extension already
installed and enabled from the command line, with --enable-event-simulate (helpers
from tests/gui/sim.py). Each screenshot is taken one tick after the UI change
(``screen.screenshot`` shows the previous frame).
"""

import os
import sys
from importlib import import_module
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tests" / "gui"))
import sim  # noqa: E402
from sim import MODULE, check, ev, run, setup, step, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_SHOTS", str(ROOT / "docs" / "screenshots"))
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
        check(f"sidebar shows the {category} tab (got {r.active_panel_category!r})", r.active_panel_category == category)
        then()
    return s_tab


@step
def s_first_start():
    prefs = bpy.context.preferences
    check("extension enabled by the command-line install", MODULE in prefs.addons)
    kc = bpy.context.window_manager.keyconfigs.active
    check(f"Maya keymap active on first start (got {kc.name if kc else None})",
          kc is not None and kc.name == "Maya-style")
    setup()   # closes the splash; the add-on is already enabled
    check("install the Maya layout template", bpy.ops.allset.layout_install() == {'FINISHED'})
    bpy.ops.wm.read_homefile(app_template="Allset")


@step
def s_scene():
    kc = bpy.context.window_manager.keyconfigs.active
    check("Maya keymap still active after loading the layout", kc is not None and kc.name == "Maya-style")
    check("layout has the Maya strip (Status Line + Shelf)",
          bpy.data.masks.get(".AllsetStrip") is not None)
    k = import_module(MODULE + ".operators.units").maya_unit()  # Maya lengths ()
    with v3d_override():
        bpy.ops.allset.create(kind='SPHERE')
        bpy.context.active_object.location = (3.5 * k, 0, k)
        bpy.ops.allset.create(kind='CYLINDER')
        bpy.context.active_object.location = (-3.5 * k, 0, k)
        bpy.data.objects["pSphere1"].select_set(True)
        bpy.ops.allset.group()
        bpy.ops.allset.create(kind='CUBE')
        cube = bpy.context.active_object
        cube.scale = (1.5, 1.5, 1.5)
        cube.modifiers.new("polySmooth1", 'SUBSURF')
        bpy.ops.allset.shelf_material(kind='LAMBERT')
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
        bpy.ops.wm.call_menu(name="ALLSET_MT_mainCreateMenu")


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
        bpy.ops.allset.ae_toggle()
        bpy.ops.allset.ae_tab(key="T")
    redraw()


def _after_cb():
    redraw()


step(goto_tab("Channel Box / Layer Editor", _after_cb))


@step
def s_ae_wait():
    redraw()


@step
def s_ae_shot():
    shot("05_attribute_editor.png")
    with v3d_override():
        bpy.ops.allset.ae_tab(key="M:polySmooth1")
    redraw()


@step
def s_ae_hist_wait():
    redraw()


@step
def s_ae_hist_shot():
    shot("06_attribute_editor_history.png")
    with v3d_override():
        bpy.ops.allset.ae_toggle()
    wm = bpy.context.window_manager
    wm.allset_outliner_shapes = True
    bpy.data.objects["group1"].allset_expanded = True
    bpy.data.objects["pCube1"].allset_expanded = True
    bpy.ops.allset.shelf_select(shelf="Rigging")
    redraw()


@step
def s_outliner():
    # step 49: the Outliner is the layout's own column left of the view (the sidebar is the dock only)
    outl = [a for a in win().screen.areas if a.type == 'OUTLINER']
    check("layout has the Outliner column", len(outl) == 1)
    if outl:
        with bpy.context.temp_override(window=win(), area=outl[0],
                                       region=next(r for r in outl[0].regions if r.type == 'WINDOW')):
            bpy.ops.outliner.expanded_toggle()
    redraw()


@step
def s_outliner_wait():
    redraw()


@step
def s_outliner_shot():
    shot("07_outliner_rigging_shelf.png")
    bpy.ops.allset.shelf_select(shelf="Polygons")


run(interval=0.5, first=3.0)
