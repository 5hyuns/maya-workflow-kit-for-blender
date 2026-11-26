"""Hide / Show on joints with the Maya keys and menus (#568): a joint picked with a click, Ctrl+H hides it and the
joints below it, Ctrl+Z brings them back, Ctrl+Shift+H and Display > Show > Show Last Hidden / All show them again,
h toggles, and with the Move tool (the skeleton in Edit mode) the hidden joints stay hidden and the same keys work."""

import os
import sys
from importlib import import_module

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, load_maya_layout, run, setup, step, win  # noqa: E402

C = {}


def mod(n):
    return import_module(MODULE + n)


def main_view():
    toolbox = mod(".ui.toolbox")
    areas = [a for a in win().screen.areas if a.type == 'VIEW_3D' and not toolbox.is_toolbox(a.spaces.active)]
    area = max(areas, key=lambda a: a.width * a.height)
    return area, next(r for r in area.regions if r.type == 'WINDOW')


def at(f, g):
    _a, r = main_view()
    return r.x + int(r.width * f), r.y + int(r.height * g)


def to_window(world):
    from bpy_extras.view3d_utils import location_3d_to_region_2d
    area, region = main_view()
    p = location_3d_to_region_2d(region, area.spaces.active.region_3d, world)
    return Vector((p.x + region.x, p.y + region.y))


def arm():
    return next(o for o in bpy.data.objects if o.type == 'ARMATURE')


def click_xy(x, y):
    ev('MOUSEMOVE', 'NOTHING', x=int(x), y=int(y))
    ev('LEFTMOUSE', 'PRESS', x=int(x), y=int(y))
    ev('LEFTMOUSE', 'RELEASE', x=int(x), y=int(y))


def key(t, **m):
    ev(t, 'PRESS', **m)
    ev(t, 'RELEASE', **m)


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_joint_tool():
    """three joints with the Joint Tool in the persp view"""
    bpy.ops.allset.keymap_activate()
    for ob in list(bpy.data.objects):
        if ob.type in {'MESH', 'ARMATURE'}:
            bpy.data.objects.remove(ob)
    area, region = main_view()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.allset.joint_tool('INVOKE_DEFAULT')
    x, y = at(0.35, 0.45)
    click_xy(x, y)


@step
def s_j2():
    click_xy(*at(0.5, 0.5))


@step
def s_j3():
    click_xy(*at(0.65, 0.45))


@step
def s_enter():
    x, y = at(0.5, 0.2)
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    key('RET')


@step
def s_after_tool():
    a = arm()
    C["names"] = [b.name for b in a.data.bones]
    C["heads"] = [a.matrix_world @ b.head_local for b in a.data.bones]
    click_xy(*at(0.9, 0.15))


def hidden():
    a = arm()
    if a.mode == 'EDIT':
        return sorted(b.name for b in a.data.edit_bones if b.hide)
    return sorted(pb.name for pb in a.pose.bones if pb.hide)


def selected():
    a = arm()
    if a.mode == 'EDIT':
        return sorted(b.name for b in a.data.edit_bones if b.select)
    return sorted(pb.name for pb in a.pose.bones if pb.select)


def over_view():
    x, y = at(0.5, 0.25)
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)


def pick(i):
    def f():
        p = to_window(C["heads"][i])
        click_xy(p.x, p.y)
    return f


def keys(k, **m):
    def f():
        over_view()
        key(k, **m)
    return f


def menu(item):
    def f():
        area, region = main_view()
        with bpy.context.temp_override(window=win(), area=area, region=region):
            C["menu"] = bpy.ops.allset.menu_item(item=item)
    return f


def act(label, fn, test):
    def a():
        fn()

    def b():
        test()
    a.__name__, b.__name__ = f"s_{label}", f"s_{label}_check"
    step(a)
    step(b)


def below(i):
    return sorted(C["names"][i:])


act("pick", pick(1), lambda: check(f"a click picks joint2 ({selected()})", selected() == [C["names"][1]]))
act("ctrl_h", keys('H', ctrl=True),
    lambda: check(f"Ctrl+H hides joint2 and the joint below it ({hidden()})", hidden() == below(1)))
act("ctrl_z", keys('Z', ctrl=True),
    lambda: check(f"Ctrl+Z shows them again ({hidden()})", hidden() == []))
act("pick2", pick(1), lambda: None)
act("ctrl_h2", keys('H', ctrl=True), lambda: None)
act("ctrl_shift_h", keys('H', ctrl=True, shift=True),
    lambda: check(f"Ctrl+Shift+H (Show Last Hidden) shows them, joint2 selected ({hidden()}, {selected()})",
                  hidden() == [] and C["names"][1] in selected()))
act("ctrl_h3", keys('H', ctrl=True), lambda: None)
act("menu_last", menu("Display/Show/Show Last Hidden"),
    lambda: check(f"Display > Show > Show Last Hidden in Pose mode ({C['menu']}, {hidden()})",
                  C["menu"] == {'FINISHED'} and hidden() == []))
act("pick3", pick(2), lambda: None)
act("menu_hide", menu("Display/Hide/Hide Selection"),
    lambda: check(f"Display > Hide > Hide Selection hides the picked joint ({hidden()})", hidden() == below(2)))
act("menu_all", menu("Display/Show/All"),
    lambda: check(f"Display > Show > All shows every joint ({hidden()})", hidden() == []))
act("pick4", pick(2), lambda: None)
act("h", keys('H'), lambda: check(f"h hides the picked joint ({hidden()})", hidden() == below(2)))
act("h2", keys('H'), lambda: check(f"h again shows it, still picked ({hidden()}, {selected()})",
                                   hidden() == [] and selected() == [C["names"][2]]))
act("pick5", pick(1), lambda: None)
act("ctrl_h4", keys('H', ctrl=True), lambda: None)
act("pick6", pick(0), lambda: None)
act("w", keys('W'),
    lambda: check(f"the Move tool (Edit mode) keeps the joints hidden ({arm().mode}, {hidden()})",
                  arm().mode == 'EDIT' and hidden() == below(1)))
act("e_last", keys('H', ctrl=True, shift=True),
    lambda: check(f"Ctrl+Shift+H in Edit mode shows them ({hidden()})", hidden() == []))
act("e_pick", pick(2), lambda: None)
act("e_ctrl_h", keys('H', ctrl=True),
    lambda: check(f"Ctrl+H in Edit mode hides the picked joint ({hidden()})", hidden() == below(2)))
act("e_ctrl_z", keys('Z', ctrl=True),
    lambda: check(f"Ctrl+Z in Edit mode shows it again ({hidden()})", hidden() == []))


run()
