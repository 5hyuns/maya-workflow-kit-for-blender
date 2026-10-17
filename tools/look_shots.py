"""In-Blender part of tools/look_compare.py: Blender shots of the states research/maya/screens/ shows.

Runs in a GUI Blender (1600x900, --enable-event-simulate) on a clean sandbox config with the
extension installed and enabled. Shot names match the Maya shots (tmp/maya_shots/shots.py,
research/maya/screens/) so look_compare.py can pair them. ``00_first_start`` is the layout
before the Maya theme is applied (what a new user sees); every later shot has the theme on.
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

SHOTS = os.environ["MAYA_KIT_LOOK_SHOTS"]
C = {}


def shot(name):
    sim.screenshot(os.path.join(SHOTS, name + ".png"))


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


def v3d_override():
    area, region = view3d()
    return bpy.context.temp_override(window=win(), screen=win().screen, area=area, region=region)


def centre():
    area, region = view3d()
    return region.x + region.width // 2, region.y + region.height // 2


@step
def s_start():
    setup()
    check("install the Maya layout template", bpy.ops.maya_kit.layout_install() == {'FINISHED'})
    bpy.ops.wm.read_homefile(app_template="MayaKit")


@step
def s_wait():
    redraw()


@step
def s_first_start():
    shot("00_first_start")
    bpy.ops.maya_kit.theme_apply()
    redraw()


@step
def s_wait2():
    redraw()


@step
def s_layout():
    shot("01_layout_empty")
    k = import_module(MODULE + ".operators.units").maya_unit()
    C["k"] = k
    with v3d_override():
        bpy.ops.maya_kit.create(kind='CUBE')
        bpy.ops.wm.tool_set_by_id(name="builtin.move")
        bpy.ops.view3d.view_selected()
    redraw()


@step
def s_wait3():
    redraw()


@step
def s_cube_sel():
    shot("02_cube_selected_move")
    bpy.ops.object.select_all(action='DESELECT')
    redraw()


@step
def s_cube_unsel():
    shot("03_cube_unselected")
    k = C["k"]
    with v3d_override():
        for x in (2, -2):
            bpy.ops.maya_kit.create(kind='CUBE')
            bpy.context.active_object.location.x = x * k
        bpy.ops.object.select_all(action='DESELECT')
        bpy.data.objects["pCube2"].select_set(True)
        cube = bpy.data.objects["pCube1"]
        cube.select_set(True)
        bpy.context.view_layer.objects.active = cube
        bpy.ops.view3d.view_all(center=False)
    view3d()[0].spaces.active.shading.type = 'WIREFRAME'
    redraw()


@step
def s_wait4():
    redraw()


@step
def s_wire():
    shot("04_wire_selected_lead")
    view3d()[0].spaces.active.shading.type = 'SOLID'
    bpy.ops.object.select_all(action='DESELECT')
    cube = bpy.data.objects["pCube1"]
    cube.select_set(True)
    bpy.context.view_layer.objects.active = cube
    bpy.ops.wm.tool_set_by_id(name="builtin.rotate")
    redraw()


@step
def s_wait5():
    redraw()


@step
def s_rotate():
    shot("05_rotate_manip")
    bpy.ops.wm.tool_set_by_id(name="builtin.scale")
    redraw()


@step
def s_wait6():
    redraw()


@step
def s_scale():
    shot("06_scale_manip")
    bpy.ops.wm.tool_set_by_id(name="builtin.move")
    with v3d_override():
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='FACE')
        bpy.ops.mesh.select_all(action='DESELECT')
    me = bpy.data.objects["pCube1"].data
    bpy.ops.object.mode_set(mode='OBJECT')
    for i in (1, 4):
        me.polygons[i].select = True
    bpy.ops.object.mode_set(mode='EDIT')
    redraw()


@step
def s_wait7():
    redraw()


@step
def s_faces():
    shot("07_faces_selected")
    bpy.ops.object.mode_set(mode='OBJECT')
    me = bpy.data.objects["pCube1"].data
    for p in me.polygons:
        p.select = False
    for e in me.edges:
        e.select = False
    for v in me.vertices:
        v.select = v.index in (0, 1, 2)
    bpy.ops.object.mode_set(mode='EDIT')
    with v3d_override():
        bpy.ops.mesh.select_mode(type='VERT')
    redraw()


@step
def s_wait8():
    redraw()


@step
def s_verts():
    shot("08_verts_selected")
    bpy.ops.object.mode_set(mode='OBJECT')
    me = bpy.data.objects["pCube1"].data
    for v in me.vertices:
        v.select = False
    for e in me.edges:
        e.select = e.index in (0, 5)
    bpy.ops.object.mode_set(mode='EDIT')
    with v3d_override():
        bpy.ops.mesh.select_mode(type='EDGE')
    redraw()


@step
def s_wait9():
    redraw()


@step
def s_edges():
    shot("09_edges_selected")
    bpy.ops.object.mode_set(mode='OBJECT')
    redraw()


@step
def s_wait10():
    redraw()


@step
def s_cb():
    shot("11_channel_box")
    with bpy.context.temp_override(window=win()):
        bpy.ops.wm.call_menu(name="MAYAKIT_MT_mainCreateMenu")


@step
def s_wait11():
    pass


@step
def s_menu():
    shot("12_create_menu")
    ev('ESC', 'PRESS')
    ev('ESC', 'RELEASE')
    x, y = centre()
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('SPACE', 'PRESS')


@step
def s_wait12():
    redraw()


@step
def s_hotbox():
    shot("13_hotbox")
    ev('SPACE', 'RELEASE')
    x, y = centre()
    cube = bpy.data.objects["pCube1"]
    # RMB over the selected cube (screen position of its origin)
    from bpy_extras.view3d_utils import location_3d_to_region_2d
    area, region = view3d()
    p = location_3d_to_region_2d(region, area.spaces.active.region_3d, cube.matrix_world.translation)
    if p is not None:
        x, y = region.x + int(p.x), region.y + int(p.y)
    C["rmb"] = (x, y)
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('RIGHTMOUSE', 'PRESS', x=x, y=y)


@step
def s_wait13():
    redraw()


@step
def s_mm():
    shot("14_marking_menu_object")
    x, y = C["rmb"]
    ev('RIGHTMOUSE', 'RELEASE', x=x, y=y)
    ev('ESC', 'PRESS')
    ev('ESC', 'RELEASE')
    with v3d_override():
        bpy.ops.screen.region_quadview()
    redraw()


@step
def s_wait14():
    redraw()


@step
def s_four():
    shot("16_four_view")
    with v3d_override():
        bpy.ops.screen.region_quadview()


run(interval=0.6, first=3.0)
