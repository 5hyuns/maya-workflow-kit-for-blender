"""In a real UI: Shift+drag on the manipulator with a joint picked = Maya Smart Duplicate. joint1 > joint2 > joint3,
joint2 picked with the Move tool (joint Edit Mode): Shift+drag on the X arrow -> joint4 (under joint1, with joint5
below it) moved by the drag, joint2 stays, joint4 picked, still Edit Mode. A Shift+click without a drag leaves no copy
(the click then goes on to selection). Pose Mode with the Rotate tool: Shift+drag on a ring -> a turned copy of the
picked joint (the copy is made through Edit Mode while the drag waits), the joint itself stays."""

import os
import sys
from importlib import import_module

import bpy
from bpy_extras.view3d_utils import location_3d_to_region_2d
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, screenshot, setup, step, view3d, win  # noqa: E402

GUI_TIMEOUT = 200
SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}
STEPS = 8


def mod(name):
    return import_module(MODULE + name)


def arm():
    return bpy.data.objects[C["arm"]]


def shot(name):
    if SHOTS:
        screenshot(os.path.join(SHOTS, name))


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


def bones():
    ob = arm()
    return ob.data.edit_bones if ob.mode == 'EDIT' else ob.data.bones


def head(name):
    b = bones()[name]
    return arm().matrix_world @ (b.head if arm().mode == 'EDIT' else b.head_local)


def arrow_point(origin, axis=Vector((1, 0, 0)), frac=0.5):
    """Window position on the manipulator at ``origin``: ``frac`` of the gizmo size along ``axis``."""
    _area, region = view3d()
    o = location_3d_to_region_2d(region, region.data, origin)
    a = location_3d_to_region_2d(region, region.data, origin + axis * 0.1)
    d = (a - o).normalized()
    size = bpy.context.preferences.view.gizmo_size * bpy.context.preferences.system.ui_scale
    p = o + d * size * frac
    return int(region.x + p.x), int(region.y + p.y), d


def hover(x, y, d, dist):
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('MOUSEMOVE', 'NOTHING', x=x + 1, y=y)
    C["drag"] = (x, y, d, dist)


def press_drag():
    x, y, d, dist = C["drag"]
    ev('LEFT_SHIFT', 'PRESS', shift=True)        # only a keyboard event's modifiers reach the window event state
    ev('LEFTMOUSE', 'PRESS', x=x, y=y, shift=True)
    for i in range(1, STEPS + 1):
        f = dist * i / STEPS
        ev('MOUSEMOVE', 'NOTHING', x=int(x + d.x * f), y=int(y + d.y * f), shift=True)


def release():
    x, y, d, dist = C["drag"]
    ev('LEFTMOUSE', 'RELEASE', x=int(x + d.x * dist), y=int(y + d.y * dist), shift=True)
    ev('LEFT_SHIFT', 'RELEASE')


def tool(idname):
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.wm.tool_set_by_id(name=idname)
    redraw()


@step
def s_setup():
    setup()
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    joints = mod(".operators.joints")
    ob = joints.new_skeleton(bpy.context)
    names, parent = [], None
    for z in (0.0, 2.0, 4.0):
        parent = joints.add_joint(ob, Vector((0.0, 0.0, z)), parent, length=0.5)
        names.append(parent)
    joints.finish(bpy.context, ob, names)
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    C.update(arm=ob.name, names=names)
    mod(".operators.joint_selection").select_edit(bpy.context, ob, names[1])     # the Move tool's pick
    tool("builtin.move")
    mod(".operators.joint_selection").sync_joint_pivot(bpy.context)


@step
def s_hover_edit():
    ob = arm()
    check(f"joint Edit Mode with joint2 picked ({ob.mode})", ob.mode == 'EDIT')
    C["start"] = head(C["names"][1]).copy()
    C["count"] = len(bones())
    x, y, d = arrow_point(C["start"])
    hover(x, y, d, 80)


@step
def s_press_edit():
    press_drag()


@step
def s_shot_edit():
    shot("gui_joint_smart_duplicate_edit.png")
    release()


@step
def s_edit_done():
    ob = arm()
    j1, j2, _j3 = C["names"]
    b = bones()
    check(f"Shift+drag copies joint2 with the joint below ({len(b)} bones: {[x.name for x in b]})",
          len(b) == C["count"] + 2 and "joint4" in b and "joint5" in b)
    if "joint4" in b:
        check(f"the copy is under joint1 ({b['joint4'].parent.name if b['joint4'].parent else None})",
              b["joint4"].parent is not None and b["joint4"].parent.name == j1 and b["joint5"].parent.name == "joint4")
        moved = head("joint4") - C["start"]
        # in joint modes the manipulator is Blender's transform gizmo: Shift on an arrow moves across it
        check(f"the drag moved the copy ({tuple(round(v, 3) for v in moved)})", moved.length > 0.1)
    check(f"joint2 stays ({tuple(round(v, 3) for v in head(j2) - C['start'])})", (head(j2) - C["start"]).length < 1e-4)
    js = mod(".operators.joint_selection")
    picked = [eb.name for eb in js._edit_picked(ob)] if ob.mode == 'EDIT' else []
    check(f"still Edit Mode with the copy picked ({ob.mode}, {picked})", ob.mode == 'EDIT' and picked == ["joint4"])
    C["count"] = len(b)
    js.sync_joint_pivot(bpy.context)
    x, y, d = arrow_point(head("joint4"))
    hover(x, y, d, 0)


@step
def s_shift_click():
    x, y, _d, _dist = C["drag"]
    ev('LEFT_SHIFT', 'PRESS', shift=True)
    ev('LEFTMOUSE', 'PRESS', x=x, y=y, shift=True)
    ev('LEFTMOUSE', 'RELEASE', x=x, y=y, shift=True)
    ev('LEFT_SHIFT', 'RELEASE')


@step
def s_wait_click():
    pass                      # the manipulator's watch takes an unmoved copy back on its next ticks


@step
def s_click_done():
    ob = arm()
    b = bones()
    check(f"a Shift+click leaves no copy ({len(b)} bones, was {C['count']}, {ob.mode})",
          len(b) == C["count"] and {x.name for x in b} == {"joint1", "joint2", "joint3", "joint4", "joint5"})
    # Pose Mode, Rotate tool (another tool than Move: the skeleton stays in Pose Mode)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode='POSE')
    cb = mod(".ui.channel_box")
    for pb in ob.pose.bones:
        cb.set_bone_selected(pb, pb.name == "joint4")
    ob.data.bones.active = ob.data.bones["joint4"]
    bpy.context.scene.tool_settings.transform_pivot_point = 'INDIVIDUAL_ORIGINS'
    tool("builtin.rotate")


@step
def s_hover_pose():
    ob = arm()
    check(f"Pose Mode with the Rotate tool ({ob.mode})", ob.mode == 'POSE')
    bpy.context.view_layer.update()
    C["count"] = len(ob.data.bones)
    C["before"] = {b.name for b in ob.data.bones}
    C["rot"] = tuple(ob.pose.bones["joint4"].matrix_basis.to_quaternion())
    origin = head("joint4")
    x, y, d = arrow_point(origin, frac=0.9)          # on the Z ring (in the XY plane), along +X
    hover(x, y, Vector((-d.y, d.x)), 60)


@step
def s_press_pose():
    press_drag()


@step
def s_shot_pose():
    shot("gui_joint_smart_duplicate_pose.png")
    release()


@step
def s_pose_done():
    ob = arm()
    new = [b.name for b in ob.data.bones if b.name not in C["before"]]
    check(f"Shift+drag in Pose Mode copies joint4 with the joint below ({C['count']} -> {len(ob.data.bones)}: {new})",
          len(ob.data.bones) == C["count"] + 2)
    check("joint4 keeps its rotation",
          tuple(ob.pose.bones["joint4"].matrix_basis.to_quaternion()) == C["rot"])
    tops = [n for n in new if ob.data.bones[n].parent is not None and ob.data.bones[n].parent.name == "joint1"]
    if tops:
        angle = ob.pose.bones[tops[0]].matrix_basis.to_quaternion().angle
        check(f"the copy {tops[0]} is turned ({angle:.3f} rad), Pose Mode ({ob.mode})",
              angle > 1e-3 and ob.mode == 'POSE')


run()
