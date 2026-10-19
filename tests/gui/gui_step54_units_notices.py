"""Step 54 in a real UI (Allset template = cm scene, maya_unit 0.01), Maya hand order:
Create > Lights > Point Light -> power 10 W x maya_unit^2; Fields/Solvers > Gravity -> field 1 Maya unit;
Windows > Animation Editors > Trax Editor under the mouse -> tooltip + Help Line 「NLA」 notice.
Menus are the kit's Maya menus, opened as menus and picked with the keyboard (accelerator / arrows).
Screenshot: gui_step54_trax_notice.png."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, setup, screenshot, step, tap, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def shot(name):
    if SHOTS:
        screenshot(os.path.join(SHOTS, name))


def maya_menu(path):
    """bl_idname of the kit menu drawing Maya's ``path``."""
    for cls in import_module(MODULE + ".ui.menu_sets")._menu_classes:
        if (cls.__doc__ or "").strip() == f"Maya menu: {path}":
            return cls.bl_idname
    raise LookupError(path)


def open_menu(path):
    area, region = view3d()
    x, y = region.x + region.width // 2, region.y + region.height // 2
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.wm.call_menu(name=maya_menu(path))


@step
def s_setup():
    setup()
    check("install layout", bpy.ops.allset.layout_install() == {'FINISHED'})
    bpy.ops.wm.read_homefile(app_template="Allset")


@step
def s_scene():
    bpy.ops.allset.keymap_activate()
    C["k"] = import_module(MODULE + ".operators.units").maya_unit()
    check(f"Allset template: a Maya unit is {C['k']} BU (cm)", abs(C["k"] - 0.01) < 1e-9)
    open_menu("Create/Lights")


@step
def s_point():
    tap('P')   # Point Light


@step
def s_point_check():
    ob = bpy.context.view_layer.objects.active
    want = 10.0 * C["k"] ** 2
    check(f"Create > Lights > Point Light: {ob and ob.name}, power {ob and ob.data.energy:.6f} W "
          f"(10 W x maya_unit^2 = {want:.6f})",
          ob is not None and ob.type == 'LIGHT' and abs(ob.data.energy - want) < 1e-6 * 10)
    open_menu("Fields/Solvers")


@step
def s_gravity():
    tap('G')   # Gravity


@step
def s_gravity_check():
    ob = bpy.context.view_layer.objects.active
    check(f"Fields/Solvers > Gravity: {ob and ob.name}, size {ob and ob.empty_display_size:.4f} BU = 1 Maya unit",
          ob is not None and ob.field and ob.field.type == 'WIND' and abs(ob.empty_display_size - C["k"]) < 1e-6)
    open_menu("Windows/Animation Editors")


@step
def s_trax_walk():
    # The menu opens with its first row under the mouse — Maya's tear-off line since step 116 — rows are 20 px at
    # scale 1: Graph Editor is one row down, Trax Editor three.
    area, region = view3d()
    x, y = region.x + region.width // 2, region.y + region.height // 2
    pitch = round(20 * bpy.context.preferences.system.ui_scale)
    for n in (1, 2, 3):
        ev('MOUSEMOVE', 'NOTHING', x=x + 4, y=y - n * pitch)


@step
def s_trax_wait():
    pass


@step
def s_trax_wait2():
    # rest on the row (a small move restarts Blender's tooltip timer once the menu has settled)
    area, region = view3d()
    x, y = region.x + region.width // 2, region.y + region.height // 2
    pitch = round(20 * bpy.context.preferences.system.ui_scale)
    ev('MOUSEMOVE', 'NOTHING', x=x + 6, y=y - 3 * pitch)


@step
def s_trax_wait3():
    pass


@step
def s_trax_wait4():
    for a in win().screen.areas:
        a.tag_redraw()


@step
def s_trax_check():
    notices = import_module(MODULE + ".ui.notices")
    text = notices.current()
    check(f"Trax Editor under the mouse: Help Line notice ({text!r})", "NLA" in text and "Trax" in text)
    shot("gui_step54_trax_notice.png")
    tap('ESC')
    tap('ESC')


run(interval=0.6)
