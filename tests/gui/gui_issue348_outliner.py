"""#348 in a real UI: the Maya Outliner lists a skeleton's joints as rows under their parent joint (joint1 is the top
row, no skeleton1 row), Display > Shapes keeps the Maya header (Display / Show / Help, dock handle, search) and adds
the shape rows (pCube1 > pCubeShape1; joints have none), a joint picked in the viewport leaves the tree closed and
marks the row holding it (Maya), F opens the rows down to it, and Shapes off takes the shape rows away again.

Rows are read from what the kit tree drew last (``outliner_tree.SEEN``)."""

import json
import os
import sys
from importlib import import_module

import bpy
import numpy as np
from bpy_extras import view3d_utils

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, screenshot, setup, step, tap, win, load_maya_layout  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
POINTS = ((3.0, -1.0, 2.0), (3.0, -1.0, 6.0), (5.0, -1.0, 9.0))
C = {}


def mod(name):
    return import_module(MODULE + name)


def tree():
    return mod(".ui.outliner_tree")


def main_view():
    toolbox = mod(".ui.toolbox")
    areas = [a for a in win().screen.areas if a.type == 'VIEW_3D' and not toolbox.is_toolbox(a.spaces.active)]
    area = max(areas, key=lambda a: a.width * a.height)
    return area, next(r for r in area.regions if r.type == 'WINDOW')


def outliner():
    area = next(a for a in win().screen.areas if a.type == 'OUTLINER')
    return area, next(r for r in area.regions if r.type == 'WINDOW'), \
        next(r for r in area.regions if r.type == 'HEADER')


def redraw_all():
    for area in win().screen.areas:
        area.tag_redraw()


def park_mouse():
    """Mouse in the viewport: no hover highlight in the Outliner header."""
    _a, r = main_view()
    ev('MOUSEMOVE', 'NOTHING', x=r.x + 20, y=r.y + 20)


def shot(name):
    path = os.path.join(SHOTS or bpy.app.tempdir, f"gui_issue348_{name}.png")
    screenshot(path)
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    px = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(px)
    bpy.data.images.remove(img)
    return px.reshape(h, w, 4)          # bottom line first, like a framebuffer read


def crop(px, region):
    return px[region.y:region.y + region.height, region.x:region.x + region.width, :3]


def drawn():
    _a, region, _h = outliner()
    return [(k, lab, d) for k, lab, _j, d in tree().SEEN.get(region.as_pointer(), [])]


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_joints():
    bpy.ops.allset.keymap_activate()
    k = mod(".operators.units").maya_unit(bpy.context.scene)
    pts = [[c * k for c in p] for p in POINTS]
    area, region = main_view()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        for ob in list(bpy.context.selected_objects):
            ob.select_set(False)
        bpy.ops.allset.joint_tool(points=json.dumps(pts))
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.allset.create(kind='CUBE')
        for ob in list(bpy.context.selected_objects):
            ob.select_set(False)
    park_mouse()
    redraw_all()


@step
def s_wait():
    redraw_all()


@step
def s_shapes_off():
    px = shot("1_shapes_off")
    mo = mod(".ui.maya_outliner")
    area, region, header = outliner()
    sp = area.spaces.active
    got = drawn()
    check("a Maya Outliner with the kit's rows, Shapes off",
          mo.is_maya_outliner(sp) and tree().is_tree(sp) and not sp.use_filter_object_content)
    check(f"the skeleton is its root joint's row, no skeleton1 row ({got})",
          ('JOINT', "joint1", 0) in got and not any(lab == "skeleton1" for _k, lab, _d in got))
    C["header"] = crop(px, header).copy()
    C["header_size"] = (header.width, header.height)
    sp.use_filter_object_content = True          # Display > Shapes (the menu item is this property)
    cube = bpy.data.objects["pCube1"]
    tree().set_expanded([('O', cube.session_uid)], True)
    redraw_all()


@step
def s_wait_on():
    redraw_all()


@step
def s_shapes_on():
    px = shot("2_shapes_on")
    mo = mod(".ui.maya_outliner")
    area, region, header = outliner()
    sp = area.spaces.active
    check("Shapes on: still a Maya Outliner with the kit's rows", mo.is_maya_outliner(sp) and tree().is_tree(sp))
    same_size = (header.width, header.height) == C["header_size"]
    diff = np.abs(crop(px, header) - C["header"]).max(axis=-1) if same_size else None
    changed = float((diff > 0.06).mean()) if diff is not None else 1.0
    check(f"Shapes on: the header is the same Maya header (Display / Show / Help, handle, search; "
          f"{changed:.1%} of its pixels changed)", changed < 0.02)
    got = drawn()
    i = next((n for n, r in enumerate(got) if r[1] == "pCube1"), None)
    check(f"Shapes on: pCubeShape1 is the row under pCube1 ({got})",
          i is not None and got[i + 1] == ('SHAPE', "pCubeShape1", 1))
    check(f"joints have no shape rows ({got})", not any(k == 'SHAPE' and "joint" in lab for k, lab, _d in got))
    # pick joint3 in the viewport
    rig = bpy.data.objects["skeleton1"]
    area3, r3 = main_view()
    head = rig.matrix_world @ rig.data.bones["joint3"].head_local
    p = view3d_utils.location_3d_to_region_2d(r3, area3.spaces.active.region_3d, head)
    x, y = int(r3.x + p.x), int(r3.y + p.y)
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('LEFTMOUSE', 'PRESS', x=x, y=y)
    ev('LEFTMOUSE', 'RELEASE', x=x, y=y)


@step
def s_wait_pick():
    park_mouse()
    redraw_all()


@step
def s_wait_pick2():
    redraw_all()


@step
def s_picked():
    shot("3_joint3_picked")
    rig = bpy.data.objects["skeleton1"]
    mode = rig.mode
    act = (rig.data.edit_bones.active if mode == 'EDIT' else rig.data.bones.active)
    check(f"joint3 picked in the viewport (active {act.name if act else None}, mode {mode})",
          act is not None and act.name == "joint3" and mode in ('POSE', 'EDIT'))
    got = drawn()
    above = tree().selected_ancestors(bpy.context)
    check(f"the tree stays closed (Maya opens nothing on a viewport pick) ({got})",
          not any(lab == "joint3" for _k, lab, _d in got))
    check(f"the joint1 row is marked as holding the pick ({above})", ('B', rig.session_uid, "joint1") in above)
    _a, region, _h = outliner()
    ev('MOUSEMOVE', 'NOTHING', x=region.x + region.width // 2, y=region.y + region.height // 2)
    tap('F')                                     # Maya's Reveal Selected


@step
def s_wait_f():
    redraw_all()


@step
def s_revealed():
    shot("4_reveal")
    got = drawn()
    names = [lab for _k, lab, _d in got if lab.startswith("joint")]
    check(f"F opens joint1 > joint2 > joint3 ({got})", names[:3] == ["joint1", "joint2", "joint3"]
          and [d for k, lab, d in got if lab in ("joint1", "joint2", "joint3")] == [0, 1, 2])
    area, _r, _h = outliner()
    area.spaces.active.use_filter_object_content = False
    park_mouse()
    redraw_all()


@step
def s_wait_off():
    redraw_all()


@step
def s_off():
    shot("5_shapes_off_again")
    got = drawn()
    check(f"Shapes off again: no shape rows ({got})", not any(k == 'SHAPE' for k, _l, _d in got))


run()
