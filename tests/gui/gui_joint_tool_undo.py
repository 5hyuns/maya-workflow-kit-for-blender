"""Undo while the Joint Tool runs (#256): z / Ctrl+Z take back the last joint and the tool keeps running (no error),
undoing the first joint removes the new skeleton, Shift+Z / Ctrl+Y place an undone joint again, a click after that
goes on from there, and Enter still finishes the chain."""

import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, setup, step, tap, win  # noqa: E402
from importlib import import_module  # noqa: E402

C = {}


def main_view():
    toolbox = import_module(MODULE + ".ui.toolbox")
    areas = [a for a in win().screen.areas if a.type == 'VIEW_3D' and not toolbox.is_toolbox(a.spaces.active)]
    area = max(areas, key=lambda a: a.width * a.height)
    return area, next(r for r in area.regions if r.type == 'WINDOW')


def at(f, g):
    _a, r = main_view()
    return r.x + int(r.width * f), r.y + int(r.height * g)


def running():
    return any(op.bl_idname == "ALLSET_OT_joint_tool" for op in win().modal_operators)


def skeletons():
    return [o for o in bpy.data.objects if o.type == 'ARMATURE']


def joints():
    obs = skeletons()
    if not obs:
        return []
    ob = obs[0]
    bones = ob.data.edit_bones if ob.mode == 'EDIT' else ob.data.bones
    return sorted(b.name for b in bones)


def click(f, g):
    x, y = at(f, g)
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('LEFTMOUSE', 'PRESS', x=x, y=y)
    ev('LEFTMOUSE', 'RELEASE', x=x, y=y)


def key(type, **mods):
    ev(type, 'PRESS', **mods)
    ev(type, 'RELEASE', **mods)


setup()


@step
def s_start():
    for ob in list(bpy.data.objects):
        if ob.type in {'MESH', 'ARMATURE'}:
            bpy.data.objects.remove(ob)
    area, region = main_view()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.allset.joint_tool('INVOKE_DEFAULT')
    click(0.30, 0.30)


@step
def s_second():
    click(0.45, 0.40)


@step
def s_third():
    click(0.60, 0.50)


@step
def s_ctrl_z():
    check(f"three joints placed ({joints()})", len(joints()) == 3)
    C["three"] = joints()
    ev('LEFT_CTRL', 'PRESS', ctrl=True)
    key('Z', ctrl=True)
    ev('LEFT_CTRL', 'RELEASE')


@step
def s_after_ctrl_z():
    check("Ctrl+Z keeps the tool running", running())
    check(f"Ctrl+Z took back the last joint ({joints()})", joints() == C["three"][:2])
    key('Z')


@step
def s_after_z():
    check(f"z took back one more ({joints()})", joints() == C["three"][:1])
    key('Z')


@step
def s_after_first():
    check("undoing the first joint removes the new skeleton", not skeletons())
    check("the tool still runs with no skeleton", running())
    ev('LEFT_SHIFT', 'PRESS', shift=True)
    key('Z', shift=True)
    ev('LEFT_SHIFT', 'RELEASE')


@step
def s_after_redo():
    check(f"Shift+Z placed the first joint again ({joints()})", len(joints()) == 1)
    ev('LEFT_CTRL', 'PRESS', ctrl=True)
    key('Y', ctrl=True)
    ev('LEFT_CTRL', 'RELEASE')


@step
def s_after_ctrl_y():
    check(f"Ctrl+Y placed the second joint again ({joints()})", len(joints()) == 2)
    click(0.70, 0.35)


@step
def s_click_on():
    ob = skeletons()[0] if skeletons() else None
    names = joints()
    check(f"a click goes on from the redone joint ({names})", len(names) == 3)
    if ob is not None and ob.mode == 'EDIT':
        ebs = ob.data.edit_bones
        ends = [b for b in ebs if not b.children]
        check("the chain is one line (one end joint)", len(ends) == 1 and ends[0].parent is not None
              and ends[0].parent.parent is not None)
    x, y = at(0.5, 0.15)
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    tap('RET')


@step
def s_done():
    check("Enter ends the tool", not running())
    ob = skeletons()[0] if skeletons() else None
    check("the chain is finished in Pose mode", ob is not None and ob.mode == 'POSE')
    check(f"one skeleton ({[o.name for o in skeletons()]})", len(skeletons()) == 1)


run()
