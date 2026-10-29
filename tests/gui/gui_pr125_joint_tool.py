"""PR #125 follow-up, Joint Tool branching (Maya 2022-2027):
a joint selected before the tool starts is NOT a parent (joint1 selected, two clicks -> an unparented chain);
the first click on an existing joint with the tool running branches from it. W finishes the placement and switches
to the Move tool (Maya: moveSuperContext)."""

import os
import sys
from importlib import import_module

import bpy
from bpy_extras import view3d_utils

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, setup, step, tap, win  # noqa: E402

C = {}


def mod(name):
    return import_module(MODULE + name)


def main_view():
    toolbox = mod(".ui.toolbox")
    areas = [a for a in win().screen.areas if a.type == 'VIEW_3D' and not toolbox.is_toolbox(a.spaces.active)]
    area = max(areas, key=lambda a: a.width * a.height)
    return area, next(r for r in area.regions if r.type == 'WINDOW')


def start_tool():
    area, region = main_view()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.allset.joint_tool('INVOKE_DEFAULT')


def click_at(x, y):
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('LEFTMOUSE', 'PRESS', x=x, y=y)
    ev('LEFTMOUSE', 'RELEASE', x=x, y=y)


def at(f, g):
    _a, r = main_view()
    return r.x + int(r.width * f), r.y + int(r.height * g)


def running():
    return any(op.bl_idname == "ALLSET_OT_joint_tool" for op in win().modal_operators)


@step
def s_setup():
    setup()
    bpy.ops.allset.make_maya(open_layout=False)
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    joints = mod(".operators.joints")
    area, region = main_view()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        rig = joints.new_skeleton(bpy.context)
        a = joints.add_joint(rig, (0, 0, 0))
        b = joints.add_joint(rig, (0, 0, 2), a)
        joints.finish(bpy.context, rig, [a, b])     # pose mode, the last joint selected
    C["rig"], C["a"], C["b"] = rig.name, a, b
    C["bones"] = {rig.name: len(rig.data.bones)}


@step
def s_preselected():
    rig = bpy.data.objects[C["rig"]]
    check(f"a joint is selected before the tool ({bpy.context.mode})", bpy.context.mode == 'POSE')
    start_tool()


@step
def s_click1():
    click_at(*at(0.25, 0.25))


@step
def s_click2():
    click_at(*at(0.35, 0.25))


@step
def s_enter():
    _a, r = main_view()
    ev('MOUSEMOVE', 'NOTHING', x=r.x + r.width // 2, y=r.y + r.height // 2)
    tap('RET')


@step
def s_new_chain():
    rig = bpy.data.objects[C["rig"]]
    others = [o for o in bpy.data.objects if o.type == 'ARMATURE' and o.name != rig.name]
    check(f"the pre-selected rig got no joints ({len(rig.data.bones)} bones)", len(rig.data.bones) == 2)
    check(f"the two clicks made a new, unparented skeleton ({[o.name for o in others]})",
          len(others) == 1 and len(others[0].data.bones) == 2
          and sum(b.parent is None for b in others[0].data.bones) == 1)
    C["new"] = others[0].name if others else None
    if others:
        new = others[0]
        root = next(b for b in new.data.bones if b.parent is None)
        sel = [pb.name for pb in new.pose.bones if mod(".ui.channel_box").bone_selected(pb)]
        # Maya 2026: Enter selects the new chain's root, Select Tool
        check(f"Enter selected the new chain's root ({sel}, root {root.name})", sel == [root.name]
              and new.data.bones.active == root)
    check("Enter ended the Joint Tool", not running())
    area, region = main_view()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        tool = bpy.context.workspace.tools.from_space_view3d_mode(bpy.context.mode, create=False)
    check(f"Enter switched to the Select tool ({tool and tool.idname})",
          tool is not None and tool.idname == 'builtin.select_box')


@step
def s_branch_start():
    for ob in bpy.context.selected_objects:
        ob.select_set(False)
    if bpy.context.mode != 'OBJECT':
        area, region = main_view()
        with bpy.context.temp_override(window=win(), area=area, region=region):
            bpy.ops.object.mode_set(mode='OBJECT')
    start_tool()


@step
def s_click_joint():
    rig = bpy.data.objects[C["rig"]]
    area, region = main_view()
    head = rig.matrix_world @ rig.pose.bones[C["b"]].head
    p = view3d_utils.location_3d_to_region_2d(region, area.spaces.active.region_3d, head)
    check("the existing joint is on screen", p is not None)
    C["joint_xy"] = (region.x + int(p.x), region.y + int(p.y)) if p is not None else at(0.5, 0.5)
    click_at(*C["joint_xy"])


@step
def s_click_new():
    x, y = C["joint_xy"]
    click_at(x + 120, y + 40)


@step
def s_w():
    _a, r = main_view()
    ev('MOUSEMOVE', 'NOTHING', x=r.x + r.width // 2, y=r.y + r.height // 2)
    tap('W')


@step
def s_branched():
    rig = bpy.data.objects[C["rig"]]
    bones = rig.data.bones
    new = [b for b in bones if b.name not in (C["a"], C["b"])]
    check(f"the click on {C['b']} branched: one new joint in that rig ({[b.name for b in bones]})", len(new) == 1)
    check("the new joint's parent is the clicked joint",
          len(new) == 1 and new[0].parent is not None and new[0].parent.name == C["b"])
    check("W ended the Joint Tool", not running())
    area, region = main_view()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        tool = bpy.context.workspace.tools.from_space_view3d_mode(bpy.context.mode, create=False)
    check(f"W switched to the Move tool ({tool and tool.idname})", tool is not None and tool.idname == 'builtin.move')
    sel = [pb.name for pb in rig.pose.bones if mod(".ui.channel_box").bone_selected(pb)]
    check(f"W selected the joint the branch grew from ({sel})", sel == [C["b"]])


run()
