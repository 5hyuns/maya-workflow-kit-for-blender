"""#435 in a real view: Modeling Toolkit Selection Constraint Angle. A strip whose faces 0-2 are flat and 3-5 flat
again after a 60 degree fold: with Angle 10 a click on face 0 picks faces 0-2, Shift+click on face 4 adds 3-5,
Ctrl+click on face 1 takes 0-2 away; a marquee over face 0 picks 0-2; Off or Angle 0 picks one face."""

import math
import os
import sys

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, ev, run, setup, step, screenshot, load_maya_layout, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
S = {}


def ob():
    return bpy.data.objects["strip"]


def sel():
    return {f.index for f in bmesh.from_edit_mesh(ob().data).faces if f.select}


def ctx():
    area, r = view3d()
    return bpy.context.temp_override(window=win(), area=area, region=r)


def face_px(i):
    from bpy_extras.view3d_utils import location_3d_to_region_2d
    area, r = view3d()
    bm = bmesh.from_edit_mesh(ob().data)
    bm.faces.ensure_lookup_table()
    p = location_3d_to_region_2d(r, area.spaces.active.region_3d, ob().matrix_world @ bm.faces[i].calc_center_median())
    return r.x + int(p[0]), r.y + int(p[1])


def add(fn, name):
    fn.__name__ = name
    step(fn)


def click(tag, face, then, shift=False, ctrl=False):
    add(lambda: ev('MOUSEMOVE', 'NOTHING', x=face_px(face)[0], y=face_px(face)[1]), tag + "_hover")
    add(lambda: ev('LEFTMOUSE', 'PRESS', shift=shift, ctrl=ctrl), tag + "_press")
    add(lambda: ev('LEFTMOUSE', 'RELEASE', shift=shift, ctrl=ctrl), tag + "_release")
    add(lambda: None, tag + "_settle")
    add(lambda: None, tag + "_settle2")
    add(then, tag + "_check")


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_strip():
    # polyline in the XY plane, width along Z: faces 0-2 flat, a 60 degree turn, faces 3-5 flat; seen from +Z...
    pts, d, p = [(0.0, 0.0)], 0.0, (0.0, 0.0)
    for turn in (0, 0, 0, 60, 0, 0):
        d += math.radians(turn)
        p = (p[0] + math.cos(d), p[1] + math.sin(d))
        pts.append(p)
    verts = [(x, z, y) for x, y in pts for z in (0.0, 1.0)]       # ... rotated so the strip faces the top view
    faces = [(2 * c, 2 * c + 2, 2 * c + 3, 2 * c + 1) for c in range(len(pts) - 1)]
    me = bpy.data.meshes.new("strip")
    me.from_pydata(verts, [], faces)
    o = bpy.data.objects.new("strip", me)
    bpy.context.scene.collection.objects.link(o)
    with ctx():
        for x in bpy.context.view_layer.objects.selected:
            x.select_set(False)
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.context.scene.tool_settings.mesh_select_mode = (False, False, True)
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.view3d.view_axis(type='TOP')
        bpy.ops.view3d.view_selected()
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")      # Maya's Select Tool
    wm = bpy.context.window_manager
    wm.allset_sel_constraint = 'ANGLE'
    wm.allset_sel_constraint_angle = 10.0
    check("strip in face mode, Angle 10", bpy.context.mode == 'EDIT_MESH')


step(lambda: None)
click("plain", 0, lambda: check(f"click on face 0 picks the flat run 0-2 ({sorted(sel())})", sel() == {0, 1, 2}))
click("add", 4, lambda: check(f"Shift+click on face 4 adds 3-5 ({sorted(sel())})", sel() == set(range(6))),
      shift=True)
click("remove", 1, lambda: check(f"Ctrl+click on face 1 takes 0-2 away ({sorted(sel())})", sel() == {3, 4, 5}),
      ctrl=True)


def box_over(face):
    def run_box():
        x, y = face_px(face)
        area, r = view3d()
        with ctx():
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.allset.uv_shell_box('INVOKE_DEFAULT')       # the first-place drag item, then Blender's box
            bpy.ops.view3d.select_box(xmin=x - r.x - 6, xmax=x - r.x + 6, ymin=y - r.y - 6, ymax=y - r.y + 6,
                                      mode='SET')
        S["box_blender"] = sorted(sel())
    return run_box


add(box_over(0), "box")
add(lambda: None, "box_settle")
add(lambda: None, "box_settle2")
add(lambda: check(f"a marquee over face 0 (Blender picked {S.get('box_blender')}) grows to 0-2 ({sorted(sel())})",
                  sel() == {0, 1, 2}), "box_check")


def set_off():
    bpy.context.window_manager.allset_sel_constraint = 'OFF'


add(set_off, "off")
click("off_click", 0, lambda: check(f"with Off a click picks one face ({sorted(sel())})", sel() == {0}))


def zero():
    wm = bpy.context.window_manager
    wm.allset_sel_constraint = 'ANGLE'
    wm.allset_sel_constraint_angle = 0.0


def mtk():
    wm = bpy.context.window_manager
    wm.allset_sel_constraint = 'ANGLE'
    wm.allset_sel_constraint_angle = 25.0
    with ctx():
        bpy.ops.allset.dock_show(dock='MODELING_TOOLKIT')


def mtk_shot():
    if SHOTS:
        screenshot(os.path.join(SHOTS, "gui_issue435_mtk.png"))
    check("the Modeling Toolkit shows Selection Constraint Angle 25", True)


add(mtk, "mtk")
add(lambda: None, "mtk_settle")
add(lambda: None, "mtk_settle2")
add(mtk_shot, "mtk_shot")
add(zero, "zero")
click("zero_click", 1, lambda: check(f"Angle 0 picks one face ({sorted(sel())})", sel() == {1}))


run()
