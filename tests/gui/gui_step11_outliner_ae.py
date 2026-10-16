"""Step 11 in a real UI: Ctrl+A switches the dock to the Attribute Editor (sidebar opens),
node tabs (transform / shape / history / material), the Maya Outliner tab; screenshots."""

import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, ev, run, step, setup, screenshot, view3d, win  # noqa: E402

SHOTS = os.environ.get("MAYA_KIT_GUI_SHOTS", "")
C = {"tries": 0}


def ui_region():
    return next(r for r in view3d()[0].regions if r.type == 'UI')


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


def shot(name):
    if SHOTS:
        screenshot(os.path.join(SHOTS, name))


def goto_tab(category, then):
    """Ctrl+wheel over the sidebar tab strip until ``category`` shows (retried per tick)."""
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


@step
def s_setup():
    C["x"], C["y"] = setup()
    cube = bpy.data.objects["Cube"]
    grp = bpy.data.objects.new("group1", None)
    bpy.context.scene.collection.objects.link(grp)
    cube.parent = grp
    cube.modifiers.new("polySmooth1", 'SUBSURF')
    mat = bpy.data.materials.new("standardSurface1")
    mat.use_nodes = True
    cube.data.materials.append(mat)
    for o in bpy.context.view_layer.objects:
        o.select_set(o is cube)
    bpy.context.view_layer.objects.active = cube
    check("sidebar starts hidden", not view3d()[0].spaces.active.show_region_ui)
    ev('MOUSEMOVE', 'NOTHING', x=C["x"], y=C["y"])
    ev('A', 'PRESS', ctrl=True)
    ev('A', 'RELEASE', ctrl=True)


@step
def s_toggled():
    wm = bpy.context.window_manager
    check("Ctrl+A -> dock shows the Attribute Editor", wm.maya_kit_dock == 'ATTRIBUTE_EDITOR')
    check("Ctrl+A opens the sidebar", view3d()[0].spaces.active.show_region_ui)


def _after_cb_tab():
    redraw()


step(goto_tab("Channel Box", _after_cb_tab))


@step
def s_shape_shot():
    shot("gui_step11_ae_shape.png")      # default tab: shape
    bpy.ops.maya_kit.ae_tab(key="T")
    redraw()


@step
def s_wait_t():
    pass


@step
def s_transform_shot():
    shot("gui_step11_ae_transform.png")
    bpy.ops.maya_kit.ae_tab(key="M:polySmooth1")
    redraw()


@step
def s_wait_m():
    pass


@step
def s_history_shot():
    shot("gui_step11_ae_history.png")
    bpy.ops.maya_kit.ae_tab(key="MAT:0")
    redraw()


@step
def s_wait_mat():
    pass


@step
def s_material_shot():
    shot("gui_step11_ae_material.png")
    ev('MOUSEMOVE', 'NOTHING', x=C["x"], y=C["y"])
    ev('A', 'PRESS', ctrl=True)
    ev('A', 'RELEASE', ctrl=True)


@step
def s_back():
    check("Ctrl+A again -> Channel Box", bpy.context.window_manager.maya_kit_dock == 'CHANNEL_BOX')
    wm = bpy.context.window_manager
    wm.maya_kit_outliner_shapes = True
    bpy.data.objects["group1"].maya_kit_expanded = True
    bpy.data.objects["Cube"].maya_kit_expanded = True
    redraw()


def _after_outliner_tab():
    rows = [(r.kind, r.object, r.depth) for r in bpy.context.window_manager.maya_kit_outliner_rows]
    i = rows.index(('OBJECT', "Cube", 1)) if ('OBJECT', "Cube", 1) in rows else -1
    check(f"Outliner: Cube under group1, its shape row next ({rows})",
          i > 0 and rows[i - 1][1] == "group1" and rows[i + 1] == ('SHAPE', "Cube", 2))
    redraw()


step(goto_tab("Outliner", _after_outliner_tab))


@step
def s_outliner_wait():
    redraw()


@step
def s_outliner_shot():
    shot("gui_step11_outliner.png")


run()
