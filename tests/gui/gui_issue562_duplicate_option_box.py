"""#562: Edit Mesh > Duplicate ❒ opens the Duplicate Face Options window also when the option box is clicked in a
menu outside the 3D View (the main menu bar): nothing is duplicated until the window's Duplicate, which then runs with
the window's values (Separate duplicated faces off: the copy stays in the mesh). Screenshot with ALLSET_GUI_SHOTS."""

import os
import sys
from importlib import import_module

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, screenshot, setup, step, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def ow():
    return import_module(MODULE + ".operators.option_windows")


def faces():
    ob = bpy.data.objects["Cube"]
    return len(bmesh.from_edit_mesh(ob.data).faces) if ob.mode == 'EDIT' else len(ob.data.polygons)


@step
def s_setup():
    setup()
    C["old"] = ow().saved("duplicate_face")
    ow().store("duplicate_face", {"separate": False, "offset": 0.0})
    bpy.context.view_layer.objects.active = bpy.data.objects["Cube"]
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.scene.tool_settings.mesh_select_mode = (False, False, True)
    bm = bmesh.from_edit_mesh(bpy.data.objects["Cube"].data)
    top = max(bm.faces, key=lambda f: f.calc_center_median().z)
    for f in bm.faces:
        f.select_set(f is top)
    bm.select_flush_mode()
    bmesh.update_edit_mesh(bpy.data.objects["Cube"].data)
    C["objects"] = len(bpy.data.objects)


@step
def s_option_box_from_top_bar():
    area = next((a for a in win().screen.areas if a.type == 'TOPBAR'), None) or next(
        a for a in win().screen.areas if a.type != 'VIEW_3D')
    region = next(r for r in area.regions if r.type in ('HEADER', 'WINDOW'))
    _a, r = view3d()
    ev('MOUSEMOVE', 'NOTHING', x=r.x + r.width // 2, y=r.y + r.height // 2)
    with bpy.context.temp_override(window=win(), area=area, region=region):
        C["res"] = bpy.ops.allset.menu_option_box('INVOKE_DEFAULT', item="Edit Mesh/Duplicate")


step(lambda: None)
step(lambda: None)


@step
def s_window_open():
    check(f"the option box ran ({C['res']}) and duplicated nothing yet (faces {faces()})",
          C["res"] == {'FINISHED'} and faces() == 6 and len(bpy.data.objects) == C["objects"])
    if SHOTS:
        screenshot(os.path.join(SHOTS, "gui_issue562_duplicate_options.png"))
    _a, r = view3d()
    ev('RET', 'PRESS', x=r.x + r.width // 2, y=r.y + r.height // 2)
    ev('RET', 'RELEASE', x=r.x + r.width // 2, y=r.y + r.height // 2)


step(lambda: None)
step(lambda: None)


@step
def s_duplicated():
    check(f"the window's Duplicate ran with Separate off: the copy stays in the mesh (faces {faces()}, "
          f"objects {len(bpy.data.objects)}, mode {bpy.context.mode})",
          faces() == 7 and len(bpy.data.objects) == C["objects"] and bpy.context.mode == 'EDIT_MESH')
    ow().store("duplicate_face", C["old"])


run()
