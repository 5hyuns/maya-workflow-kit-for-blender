"""Issue #355 in a real UI: a display layer made from a picked joint holds that joint only (like Maya).

Maya Workflow Kit layout, front view, joint1 > joint2 > joint3 of a kit skeleton. A click picks joint2, the Layer
Editor's Create Layer from Selected button makes layer1 with it. V off: joint2 and joint3 are no longer drawn while
joint1 and its bone to joint2 stay, joint1 is still picked by a click and a click on joint3's place picks nothing; the
skeleton object stays shown and no joint's own Visibility changes. V on, the type box to Template: joint2 / joint3 draw
grey and a click on joint3 picks nothing; Reference: black, still not picked; joint1 is picked in both.
Shots ``gui_issue355_<name>.png`` with ``--shots``."""

import os
import sys
from importlib import import_module

import bpy
import numpy as np
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import (MODULE, check, dock_area, dock_region, ev, find_button,  # noqa: E402
                 load_maya_layout, px, run, screenshot, setup, step, view3d, win)

GUI_TIMEOUT = 300
SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
VIOLET = np.array([0x26, 0x00, 0x43]) / 255.0
GREY = np.array([0x78, 0x78, 0x78]) / 255.0
BLACK = np.array([0.0, 0.0, 0.0])
C = {}


def mod(name):
    return import_module(MODULE + name)


def dock():
    return dock_area(), dock_region()


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


def shot(name):
    path = os.path.join(SHOTS or bpy.app.tempdir, f"gui_issue355_{name}.png")
    screenshot(path)
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    px = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(px)
    bpy.data.images.remove(img)
    return px.reshape(h, w, 4)[..., :3]


def to_window(world):
    from bpy_extras.view3d_utils import location_3d_to_region_2d
    area, region = view3d()
    p = location_3d_to_region_2d(region, area.spaces.active.region_3d, world)
    return None if p is None else Vector((p.x + region.x, p.y + region.y))


def heads():
    arm = bpy.data.objects[C["arm"]]
    return [arm.matrix_world @ arm.data.bones[n].head_local for n in C["names"]]


def r_px():
    """Drawn joint radius in window px (front ortho)."""
    k = mod(".operators.units").maya_unit()
    a, b = to_window(heads()[1]), to_window(heads()[1] + Vector((2.0 * k, 0, 0)))
    return (b - a).length


def count(px, world, colour, half=None):
    half = int(half if half is not None else 0.5 * r_px())
    p = to_window(world)
    x, y = int(round(p.x)), int(round(p.y))
    patch = px[y - half:y + half, x - half:x + half]
    return int((np.abs(patch - colour).max(axis=-1) < 0.06).sum())


def picked():
    arm = bpy.data.objects[C["arm"]]
    if arm.mode == 'POSE':
        cb = mod(".ui.channel_box")
        return [pb.name for pb in arm.pose.bones if cb.bone_selected(pb)]
    if arm.mode == 'EDIT':
        js = mod(".operators.joint_selection")
        return [eb.name for eb in js._edit_picked(arm)]
    return []


def layer():
    return bpy.data.collections.get(C.get("layer", ""))


def click(name, world_fn):
    def press():
        p = world_fn()
        ev('MOUSEMOVE', 'NOTHING', x=int(p.x), y=int(p.y))
        ev('LEFTMOUSE', 'PRESS', x=int(p.x), y=int(p.y))

    def release():
        p = world_fn()
        ev('LEFTMOUSE', 'RELEASE', x=int(p.x), y=int(p.y))
    press.__name__, release.__name__ = f"s_{name}_press", f"s_{name}_release"
    step(press)
    step(release)


def press_found(key):
    def hover():
        if C.get(key):
            ev('MOUSEMOVE', 'NOTHING', x=C[key][0], y=C[key][1])

    def press():
        if C.get(key):
            ev('LEFTMOUSE', 'PRESS', x=C[key][0], y=C[key][1])

    def release():
        if C.get(key):
            ev('LEFTMOUSE', 'RELEASE', x=C[key][0], y=C[key][1])
        redraw()
    hover.__name__, press.__name__, release.__name__ = f"s_{key}_hover", f"s_{key}_press", f"s_{key}_release"
    step(hover)
    step(press)
    step(release)


def head(i):
    return lambda: to_window(heads()[i])


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_scene():
    bpy.ops.allset.keymap_activate()
    joints = mod(".operators.joints")
    k = mod(".operators.units").maya_unit()
    arm = joints.new_skeleton(bpy.context)
    names, parent = [], None
    for x in (-8.0, 0.0, 8.0):
        parent = joints.add_joint(arm, Vector((x, 0.0, 4.0)) * k, parent, length=1.0 * k)
        names.append(parent)
    joints.finish(bpy.context, arm, names)
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for n in names:
        arm.data.bones[n][joints.RADIUS] = 4.0          # drawn radius 2 units: big enough to sample
    for ob in bpy.context.scene.objects:
        ob.select_set(False)
    C["arm"], C["names"] = arm.name, names
    from mathutils import Euler
    area, region = view3d()
    rv3d = area.spaces.active.region_3d
    rv3d.view_perspective = 'ORTHO'
    rv3d.view_rotation = Euler((1.5707963, 0.0, 0.0)).to_quaternion()
    rv3d.view_location = (0.0, 0.0, 4.0 * k)
    rv3d.view_distance = 30.0 * k
    bpy.context.window_manager.allset_le_tab = 'DISPLAY'
    redraw()


@step
def s_wait():
    redraw()


click("pick_joint2", head(1))


@step
def s_picked():
    check(f"a click picks joint2 ({picked()})", picked() == [C["names"][1]])
    redraw()


@step
def s_find_new():
    """Sweep down the column of the toolbar's last button (Create Layer from Selected, right-aligned)."""
    _area, region = dock()
    frac = (region.width - px(52)) / region.width
    look = find_button(dock, lambda _p, c: "layer_new(selected=True)" in c, C, "new", x_frac=frac, step_px=3,
                       start_frac=0.3)
    look()                                     # it runs on at the front of the steps until it found the button
press_found("new")


@step
def s_layer_made():
    arm = bpy.data.objects[C["arm"]]
    lj = mod(".ui.layer_joints")
    le = mod(".ui.layer_editor")
    made = le.layers(bpy.context.scene)
    check(f"Create Layer from Selected button found ({C.get('new')})", C.get("new") is not None)
    coll = made[0] if made else None
    members = lj.members(coll, bpy.context.scene) if coll is not None else {}
    check(f"layer1 holds joint2 only, not the skeleton ({members}, objects "
          f"{[o.name for o in coll.objects] if coll else None})",
          coll is not None and members == {arm: [C["names"][1]]} and arm.name not in coll.objects)
    C["layer"] = coll.name if coll is not None else ""
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    mod(".operators.joint_selection").clear(bpy.context)     # nothing selected: the joints draw their own colours
    for o in bpy.context.scene.objects:
        o.select_set(False)
    redraw()


step(find_button(dock, lambda _p, c: "layer_toggle" in c and "visible" in c, C, "vbox", x_frac=0.1, step_px=4,
                 start_frac=0.3))
press_found("vbox")


@step
def s_hidden_shot():
    arm = bpy.data.objects[C["arm"]]
    coll = layer()
    check(f"V box found and turned off ({C.get('vbox')})", coll is not None and not coll.allset_layer.visible)
    px = shot("hidden")
    h = heads()
    n = [count(px, p, VIOLET) for p in h]
    check(f"joint1 draws, joint2 / joint3 don't ({n} px)", n[0] > 20 and n[1] == 0 and n[2] == 0)
    mid = (h[0] + h[1]) / 2
    bone = count(px, mid, VIOLET, half=0.8 * r_px())
    check(f"the bone from joint1 to joint2 stays ({bone} px)", bone > 0)
    check("the skeleton object is not hidden", arm.visible_get())
    check("no joint's own Visibility changed", not any(pb.hide for pb in arm.pose.bones))
    for o in bpy.context.scene.objects:
        o.select_set(False)
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    redraw()


click("hidden_joint3", head(2))


@step
def s_hidden_joint3():
    check(f"a click on hidden joint3's place picks nothing ({picked()})", picked() == [])


click("hidden_joint1", head(0))


@step
def s_hidden_joint1():
    check(f"joint1 is still picked ({picked()})", picked() == [C["names"][0]])
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    mod(".operators.joint_selection").clear(bpy.context)
    for o in bpy.context.scene.objects:
        o.select_set(False)
    layer().allset_layer.visible = True
    redraw()


step(find_button(dock, lambda _p, c: "layer_cycle_type" in c, C, "tbox", y_from="vbox", step_px=4))
press_found("tbox")


def type_checks(kind, colour):
    @step
    def shot_step():
        coll = layer()
        check(f"type box found and set to {kind} ({C.get('tbox')}, {coll.allset_layer.display_type if coll else None})",
              coll is not None and coll.allset_layer.display_type == kind)
        px = shot(kind.lower())
        h = heads()
        n = [count(px, p, colour) for p in h[1:]]
        check(f"{kind}: joint2 / joint3 draw in the layer colour ({n} px), not violet",
              all(c > 20 for c in n) and all(count(px, p, VIOLET) == 0 for p in h[1:]))
        check(f"{kind}: joint1 stays violet", count(px, h[0], VIOLET) > 20)
        for o in bpy.context.scene.objects:
            o.select_set(False)
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        redraw()
    shot_step.__name__ = f"s_{kind.lower()}_shot"

    click(f"{kind.lower()}_joint3", head(2))

    @step
    def joint3():
        check(f"{kind}: a click on joint3 picks nothing ({picked()})", picked() == [])
    joint3.__name__ = f"s_{kind.lower()}_joint3"

    click(f"{kind.lower()}_joint1", head(0))

    @step
    def joint1():
        check(f"{kind}: joint1 is picked ({picked()})", picked() == [C["names"][0]])
        for o in bpy.context.scene.objects:
            o.select_set(False)
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        redraw()
    joint1.__name__ = f"s_{kind.lower()}_joint1"


type_checks('TEMPLATE', GREY)
press_found("tbox")
type_checks('REFERENCE', BLACK)


run()
