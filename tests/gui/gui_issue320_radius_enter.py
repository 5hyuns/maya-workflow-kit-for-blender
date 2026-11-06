"""Issue #320 (3): a joint's Radius typed in the Channel Box and confirmed with Enter redraws the joint at once — no
click in the viewport needed. A three-joint chain in the Maya layout (front view), the middle joint the lead; the
Radius field gets a doubled value; the drawn circle doubles in the next screenshot without any viewport event.
Screenshots with ALLSET_GUI_SHOTS (or --shots)."""

import os
import sys
from importlib import import_module

import bpy
import numpy as np
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import (MODULE, check, dock_area, dock_region, ev, find_button, load_maya_layout, run, screenshot,  # noqa: E402
                 setup, step, tap, view3d, win)

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
LEAD = np.array([0x43, 0xff, 0xa3]) / 255.0
C = {}
GUI_TIMEOUT = 240


def mod(name):
    return import_module(MODULE + name)


def shot(name):
    path = os.path.join(SHOTS or bpy.app.tempdir, f"gui_issue320_{name}.png")
    screenshot(path)
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    px = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(px)
    bpy.data.images.remove(img)
    return px.reshape(h, w, 4)[..., :3]


def dock():
    return dock_area(), dock_region()


def type_text(text):
    ev('A', 'PRESS', ctrl=True)     # select the whole text, then type over it
    ev('A', 'RELEASE', ctrl=True)
    for ch in text:
        ev('TEXTINPUT', 'PRESS', unicode=ch)


def arm():
    return bpy.data.objects[C["arm"]]


def to_window(world):
    from bpy_extras.view3d_utils import location_3d_to_region_2d
    area, region = view3d()
    p = location_3d_to_region_2d(region, area.spaces.active.region_3d, world)
    return None if p is None else Vector((p.x + region.x, p.y + region.y))


def green_px(px, half=90):
    """Lead-coloured pixels around the middle joint's head (its circle and the bones to its neighbours)."""
    p = to_window(arm().matrix_world @ arm().data.bones[C["mid"]].head_local)
    x, y = int(round(p.x)), int(round(p.y))
    patch = px[y - half:y + half, x - half:x + half]
    return int((np.abs(patch - LEAD).max(axis=-1) < 0.08).sum())


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_scene():
    bpy.ops.allset.keymap_activate()
    joints = mod(".operators.joints")
    k = mod(".operators.units").maya_unit()
    a = joints.new_skeleton(bpy.context)
    names, parent = [], None
    for x in (-8.0, 0.0, 8.0):
        parent = joints.add_joint(a, Vector((x, 0.0, 4.0)) * k, parent, length=1.0 * k)
        names.append(parent)
    joints.finish(bpy.context, a, names)
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for n in names:
        a.data.bones[n][joints.RADIUS] = 4.0          # drawn radius 2 units
    C["arm"], C["mid"] = a.name, names[1]
    for ob in bpy.context.scene.objects:
        ob.select_set(False)
    a.select_set(True)
    bpy.context.view_layer.objects.active = a
    area, region = view3d()
    rv3d = area.spaces.active.region_3d
    rv3d.view_perspective = 'ORTHO'
    rv3d.view_rotation = (0.7071068, 0.7071068, 0.0, 0.0)      # front
    rv3d.view_location = (0.0, 0.0, 4.0 * k)
    rv3d.view_distance = 40.0 * k
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.object.mode_set(mode='POSE')
    cb = mod(".ui.channel_box")
    for pb in a.pose.bones:
        cb.set_bone_selected(pb, pb.name == C["mid"])
    a.data.bones.active = a.data.bones[C["mid"]]
    dock_area('CHANNEL_BOX')
    for ar in win().screen.areas:
        ar.tag_redraw()


@step
def s_before():
    C["before"] = green_px(shot("before"))
    check(f"the lead joint draws green at Radius 4 ({C['before']} px)", C["before"] > 40)


step(find_button(dock, lambda path, _cmd: path.endswith("allset_joint_radius"), C, "radius", x_frac=0.7, step_px=6))


@step
def s_found():
    check(f"the Channel Box has the Radius field ({C.get('radius')})", C.get("radius") is not None)
    if not C.get("radius"):
        raise RuntimeError("Radius field not found")
    x, y = C["radius"]
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)


@step
def s_click():
    x, y = C["radius"]
    ev('LEFTMOUSE', 'PRESS', x=x, y=y)
    ev('LEFTMOUSE', 'RELEASE', x=x, y=y)


@step
def s_type():
    type_text("8")


@step
def s_enter():
    tap('RET')      # the mouse stays on the Channel Box: no viewport click, no redraw request from the test


@step
def s_after():
    joints = mod(".operators.joints")
    r = float(arm().data.bones[C["mid"]].get(joints.RADIUS, 1.0))
    check(f"Enter set the joint's Radius ({r})", abs(r - 8.0) < 1e-6)
    C["after"] = green_px(shot("after"))
    check(f"the joint redrew larger right after Enter, no viewport click ({C['before']} -> {C['after']} px)",
          C["after"] > C["before"] * 1.4)
    mj = mod(".ui.maya_joints")
    area, _region = view3d()
    hit = mj._CACHE.get(area.spaces.active.as_pointer())
    check(f"the view's joint lines were rebuilt after the change (cache generation {hit[0][0] if hit else None} "
          f"vs {mj._GEN[0]})", hit is not None and hit[0][0] == mj._GEN[0])


run()
