"""Real-UI flows for #184 and #193.

#184: face mode, top face, Ctrl+E, the extrusion edited (what a manipulator drag does), another face selected, G key
= a second extrusion on that face (polyExtrudeFace2), the first one stays where it was dragged.
#193: Panels > Perspective lists New; New makes persp1 and the view looks through it; Ctrl+Z takes it back."""

import os
import sys
from importlib import import_module

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, screenshot, setup, step, tap, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def shot(name):
    if SHOTS:
        screenshot(os.path.join(SHOTS, name))


def override():
    area, region = view3d()
    return bpy.context.temp_override(window=win(), area=area, region=region)


def counts():
    b = bmesh.from_edit_mesh(bpy.data.objects["Cube"].data)
    return len(b.verts), len(b.faces), round(max(v.co.z for v in b.verts), 3)


def select_faces(keep):
    ob = bpy.data.objects["Cube"]
    b = bmesh.from_edit_mesh(ob.data)
    for f in b.faces:
        f.select_set(False)
    for f in b.faces:
        if keep(f):
            f.select_set(True)
    b.select_flush_mode()
    bmesh.update_edit_mesh(ob.data)


def key(k, **mods):
    ev(k, 'PRESS', **mods)
    ev(k, 'RELEASE', **mods)


@step
def s_setup():
    C["x"], C["y"] = setup()
    cube = bpy.data.objects["Cube"]
    for o in bpy.context.view_layer.objects:
        o.select_set(o is cube)
    bpy.context.view_layer.objects.active = cube
    ev('MOUSEMOVE', 'NOTHING', x=C["x"], y=C["y"])
    tap('F11')                                   # Maya face mode


@step
def s_top():
    select_faces(lambda f: f.normal.z > 0.9)
    C["n0"] = counts()
    key('E', ctrl=True)                          # Ctrl+E


@step
def s_drag():
    ex = import_module(MODULE + ".operators.extrude")
    C["n1"] = counts()
    with override():
        ex.set_params(bpy.context, local_translate_z=0.5)       # what dragging the extrude manipulator runs
    C["n2"] = counts()
    select_faces(lambda f: f.normal.x > 0.9 and f.calc_center_median().z < 0.9)
    key('G')


@step
def s_g_done():
    ex = import_module(MODULE + ".operators.extrude")
    n0, n1, n2, n3 = C["n0"], C["n1"], C["n2"], counts()
    check(f"Ctrl+E then a drag: one extrusion moved up ({n0} -> {n1} -> {n2})", n1[:2] == (12, 10) and n2[2] > n1[2])
    check(f"G on the new face = a second extrusion, the first stays ({n2} -> {n3})",
          n3[:2] == (16, 14) and n3[2] == n2[2])
    rec = ex.active(bpy.context)[1]
    check(f"G made a new node ({rec and rec.name})", rec is not None and rec.name == "polyExtrudeFace2")
    shot("184_after_g.png")
    tap('F8')                                    # object mode


@step
def s_menu():
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.wm.call_menu(name="ALLSET_MT_panel_perspective")


@step
def s_menu_shot():
    shot("193_menu.png")
    tap('ESC')


@step
def s_new():
    area, region = view3d()
    C["mouse"] = (region.x + region.width // 2, region.y + region.height // 2)
    ev('MOUSEMOVE', 'NOTHING', x=C["mouse"][0], y=C["mouse"][1])
    with bpy.context.temp_override(window=win(), area=area, region=region):
        C["res"] = bpy.ops.allset.panel_new_persp('INVOKE_DEFAULT', True)


@step
def s_new_done():
    area, _r = view3d()
    ob = bpy.data.objects.get("persp1")
    space = area.spaces.active
    check(f"New made persp1 ({C['res']}, {[o.name for o in bpy.data.objects]})", ob is not None)
    check("the view looks through persp1", ob is not None and space.camera == ob
          and space.region_3d.view_perspective == 'CAMERA')
    check("persp1 is selected", ob is not None and ob.select_get() and bpy.context.view_layer.objects.active == ob)
    shot("193_through_persp1.png")
    key('Z', ctrl=True)


@step
def s_undone():
    check(f"Ctrl+Z takes persp1 back ({[o.name for o in bpy.data.objects]})", "persp1" not in bpy.data.objects)


run()
