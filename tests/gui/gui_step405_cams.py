"""In a real UI: Ctrl+Shift+C and View > Create Camera From View copy the view's camera (persp1, the view looks
through it, the selection stays, one Ctrl+Z takes it back and the view is the persp view again); Panels >
Orthographic > New > Back makes back1 and looks through it."""

import os
import sys
from importlib import import_module

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, load_maya_layout, run, screenshot, setup, step, tap, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def shot(name):
    if SHOTS:
        screenshot(os.path.join(SHOTS, name))


def mod(name):
    return import_module(f"{MODULE}.{name}")


def override():
    area, region = view3d()
    return bpy.context.temp_override(window=win(), screen=win().screen, area=area, region=region)


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


def centre():
    ev('MOUSEMOVE', 'NOTHING', x=C["mid"][0], y=C["mid"][1])


def undo():
    centre()
    ev('Z', 'PRESS', ctrl=True)
    ev('Z', 'RELEASE', ctrl=True)


def persp_view():
    """Back to Blender's persp view (the startup persp camera of the Maya layout)."""
    rv3d = view3d()[0].spaces.active.region_3d
    rv3d.view_perspective = 'PERSP'
    redraw()


def selection_kept():
    vl = bpy.context.view_layer
    cube = bpy.data.objects.get(C["cube"])
    return (cube is not None and [o.name for o in bpy.context.selected_objects] == [C["cube"]]
            and vl.objects.active == cube)


def through(name):
    space = view3d()[0].spaces.active
    return space.camera is not None and space.camera.name == name and space.region_3d.view_perspective == 'CAMERA'


@step
def s_setup():
    setup()
    bpy.ops.allset.make_maya(open_layout=False)
    load_maya_layout()


@step
def s_scene():
    bpy.ops.allset.keymap_activate()
    _area, region = view3d()
    C["mid"] = (region.x + region.width // 2, region.y + region.height // 2)
    with override():
        bpy.ops.allset.create(kind='CUBE')
    C["cube"] = bpy.context.view_layer.objects.active.name
    persp_view()
    space = view3d()[0].spaces.active
    rv3d = space.region_3d
    C["eye"] = rv3d.view_location + rv3d.view_rotation @ Vector((0.0, 0.0, rv3d.view_distance))
    C["rot"] = rv3d.view_rotation.copy()
    C["lens"] = space.lens
    bpy.ops.ed.undo_push(message="cube")          # Ctrl+Z later comes back here
    centre()


@step
def s_hotkey():
    ev('C', 'PRESS', shift=True, ctrl=True)
    ev('C', 'RELEASE', shift=True, ctrl=True)


@step
def s_hotkey_check():
    ob = bpy.data.objects.get("persp1")
    check(f"Ctrl+Shift+C makes persp1 ({[o.name for o in bpy.data.objects if o.type == 'CAMERA']})",
          ob is not None and ob.type == 'CAMERA' and ob.data.name == "persp1Shape")
    if ob is not None:
        err = (ob.matrix_world.translation - C["eye"]).length
        turn = ob.matrix_world.to_quaternion().rotation_difference(C["rot"]).angle
        check(f"persp1 sits where the view looks from (eye {err:.1e}, turn {turn:.1e})", err < 1e-3 and turn < 1e-4)
        check(f"persp1 keeps the view's focal length ({ob.data.lens:.2f} mm, view lens {C['lens']:.1f})",
              abs(ob.data.lens - C["lens"] * ob.data.sensor_width / 72.0) < 1e-3)
        check("persp1 is not selected", not ob.select_get())
    check("the view looks through persp1", through("persp1"))
    check("the selection stays (the cube, still the lead)", selection_kept())
    shot("gui_step405_hotkey.png")
    undo()


@step
def s_hotkey_undo():
    redraw()
    names = [o.name for o in bpy.data.objects]
    check(f"one Ctrl+Z takes persp1 back ({names})", "persp1" not in names and C["cube"] in names)
    check("after Ctrl+Z the cube is selected as before", selection_kept())
    space = view3d()[0].spaces.active
    rv3d = space.region_3d
    eye = rv3d.view_location + rv3d.view_rotation @ Vector((0.0, 0.0, rv3d.view_distance))
    check(f"after Ctrl+Z the view is the persp view again ({rv3d.view_perspective}, {space.camera}, "
          f"eye moved {(eye - C['eye']).length:.1e})",
          rv3d.view_perspective == 'PERSP' and space.camera is None and (eye - C["eye"]).length < 1e-4)
    shot("gui_step405_hotkey_undone.png")


@step
def s_menu_open():
    persp_view()
    centre()
    with override():
        bpy.ops.wm.call_menu(name="ALLSET_MT_panel_view")


@step
def s_menu_pick():
    shot("gui_step405_view_menu.png")
    tap('C')            # the row's underlined letter: Create Camera From View


@step
def s_menu_check():
    check(f"View > Create Camera From View makes persp1 ({[o.name for o in bpy.data.objects]})",
          "persp1" in bpy.data.objects)
    check("the view looks through it", through("persp1"))
    check("the selection stays", selection_kept())
    undo()


@step
def s_menu_undo():
    names = [o.name for o in bpy.data.objects]
    check(f"one Ctrl+Z takes the menu's persp1 back ({names})", "persp1" not in names and C["cube"] in names)
    persp_view()
    centre()
    with override():
        bpy.ops.wm.call_menu(name="ALLSET_MT_panel_orthographic")


@step
def s_ortho_menu():
    shot("gui_step405_ortho_menu.png")
    tap('N')            # New: its submenu opens


@step
def s_ortho_new_pick():
    shot("gui_step405_ortho_new.png")
    tap('B')            # Back


@step
def s_ortho_new_check():
    unit = mod("operators.units").maya_unit(bpy.context.scene)
    ob = bpy.data.objects.get("back1")
    check(f"Orthographic > New > Back makes back1 ({[o.name for o in bpy.data.objects]})",
          ob is not None and ob.data.type == 'ORTHO')
    if ob is not None:
        check(f"back1 is 30 units wide ({ob.data.ortho_scale / unit:.3f})", abs(ob.data.ortho_scale - 30.0 * unit) < 1e-5)
        loc = ob.matrix_world.translation / unit
        look = ob.matrix_world.to_quaternion() @ Vector((0.0, 0.0, -1.0))
        check(f"back1 sits 1000.1 units out behind, looking at the origin ({tuple(round(v, 2) for v in loc)})",
              (loc - Vector((0.0, 1000.1, 0.0))).length < 1e-2 and (look - Vector((0.0, -1.0, 0.0))).length < 1e-5)
        check("back1 is selected and doesn't render", ob.select_get() and not ob.data.allset_renderable)
    check("the view looks through back1", through("back1"))
    shot("gui_step405_back1.png")      # the view's label reads back1
    undo()


@step
def s_ortho_new_undo():
    names = [o.name for o in bpy.data.objects]
    check(f"one Ctrl+Z takes back1 back ({names})", "back1" not in names and C["cube"] in names)
    check("and the view is the persp view again", view3d()[0].spaces.active.region_3d.view_perspective == 'PERSP')


run()
