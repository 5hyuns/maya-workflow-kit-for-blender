"""Maya Outliner right-click > Set Active Camera: right-clicking a camera row (with something else selected) targets
that camera; afterwards Blender's camera toggle (Numpad 0 / the navigation gizmo's camera button) looks through it,
also in a kit panel that looked through its own (local) camera."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, load_maya_layout, run, setup, step, tap, view3d, win  # noqa: E402

C = {}


def space():
    return view3d()[0].spaces.active


def outl():
    a = next(a for a in win().screen.areas if a.type == 'OUTLINER')
    return a, next(r for r in a.regions if r.type == 'WINDOW')


def row_xy(i, n):
    tree = import_module(MODULE + ".ui.outliner_tree")
    a, r = outl()
    u = tree.unit()
    y0, y1 = tree.row_rect(a, r, i, u, n)
    return r.x + 3 * u, r.y + (y0 + y1) // 2


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_scene():
    bpy.ops.allset.keymap_activate()
    col = bpy.context.scene.collection.children[0]
    cam = bpy.data.objects.new("cam1", bpy.data.cameras.new("cam1"))
    col.objects.link(cam)
    cam.hide_viewport = True                   # like Maya's startup cameras (Visibility off)
    other = bpy.data.objects.new("other", bpy.data.cameras.new("other"))
    col.objects.link(other)
    mesh = bpy.data.objects.new("M", bpy.data.meshes.new("M"))
    col.objects.link(mesh)
    a, _r = view3d()
    # a kit panel looking through its own camera (Panels > Look Through), then back to a free view
    import_module(MODULE + ".ui.panel_menus").look_through(bpy.context, a, other)
    space().region_3d.view_perspective = 'PERSP'
    check(f"setup: the panel has its own camera ({space().use_local_camera}, {space().camera})",
          space().use_local_camera and space().camera == other)
    # something else (a mesh) is the selection
    for o in bpy.context.scene.objects:
        o.select_set(False)
    bpy.context.view_layer.objects.active = mesh
    mesh.select_set(True)
    for ar in win().screen.areas:
        ar.tag_redraw()


@step
def s_rows():
    tree = import_module(MODULE + ".ui.outliner_tree")
    a, r = outl()
    with bpy.context.temp_override(window=win(), area=a, region=r):
        rows = tree.rows_for(bpy.context, a.spaces.active)
    C["row"] = next(k for k, row in enumerate(rows) if row.kind == 'OBJECT' and row.ob == "cam1")
    C["n"] = len(rows)


@step
def s_right_click():
    x, y = row_xy(C["row"], C["n"])
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('RIGHTMOUSE', 'PRESS')
    ev('RIGHTMOUSE', 'RELEASE')


@step
def s_menu_target():
    tap('ESC')                                 # close the menu
    edit = import_module(MODULE + ".ui.outliner_tree_edit")
    C["cam"] = edit.menu_camera(bpy.context)
    check(f"right-click on the cam1 row with M selected: the menu targets cam1 ({C['cam']!r})", C["cam"] == "cam1")


@step
def s_set_active():
    cam = bpy.data.objects["cam1"]
    a, r = outl()
    with bpy.context.temp_override(window=win(), area=a, region=r):
        bpy.ops.allset.outliner_set_active_camera(camera=C["cam"] or "cam1")
    check(f"scene camera is cam1 ({bpy.context.scene.camera})", bpy.context.scene.camera == cam)
    check("cam1 is enabled in viewports", not cam.hide_viewport)
    check("the selection is untouched (M still active)", bpy.context.view_layer.objects.active.name == "M")


@step
def s_toggle():
    a, r = view3d()
    with bpy.context.temp_override(window=win(), area=a, region=r):
        bpy.ops.view3d.view_camera()
    sp = space()
    cur = sp.camera if sp.use_local_camera else bpy.context.scene.camera
    check(f"camera toggle looks through cam1 ({sp.region_3d.view_perspective}, {cur}, local {sp.use_local_camera})",
          sp.region_3d.view_perspective == 'CAMERA' and cur == bpy.data.objects["cam1"])


run()
