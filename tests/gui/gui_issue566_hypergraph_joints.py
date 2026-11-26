"""Hypergraph: Hierarchy with a skeleton in a real UI (#566): joint1 > joint2 > joint3 are nodes -> a click on the
joint2 node picks joint2 (Pose Mode, lead) -> Shift+click on joint3 adds it -> a middle-mouse drag of pCube1 onto the
joint3 node parents pCube1 under joint3; shots with ``--shots``."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, load_maya_layout, run, setup, step, win  # noqa: E402

GUI_TIMEOUT = 200
SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def mod(name):
    return import_module(MODULE + name)


def shot(name):
    if SHOTS:
        with bpy.context.temp_override(window=C["w"]):
            bpy.ops.screen.screenshot(filepath=os.path.join(SHOTS, name))


def v3d():
    area = max((a for a in win().screen.areas if a.type == 'VIEW_3D'), key=lambda a: a.width * a.height)
    return area, next(r for r in area.regions if r.type == 'WINDOW')


def redraw():
    for w in bpy.context.window_manager.windows:
        for a in w.screen.areas:
            a.tag_redraw()


def again(fn, cond, limit=40):
    C.setdefault(fn.__name__, 0)
    if not cond() and C[fn.__name__] < limit:
        C[fn.__name__] += 1
        import sim
        sim._steps.insert(0, fn)
        redraw()
        return True
    return False


def hg_area():
    mw = mod(".ui.marked_window")
    w = mw.find_window(bpy.context, "HYPERGRAPH")
    if w is None:
        return None, None, None
    area = next(a for a in w.screen.areas if mw.kind_of(a) == "HYPERGRAPH")
    return w, area, next(r for r in area.regions if r.type == 'WINDOW')


def arm():
    return bpy.data.objects[C["arm"]]


def node_point(key):
    hg = mod(".ui.hypergraph")
    _w, area, region = hg_area()
    view = hg.VIEWS[area.as_pointer()]
    cents, _n, _b = hg.centres(bpy.context.scene)
    rx, ry = view.to_region(*cents[key])
    return int(region.x + rx), int(region.y + ry)


def joint(name):
    return ('B', arm().session_uid, name)


def hev(type, value, x, y, **kw):
    C["w"].event_simulate(type=type, value=value, x=int(x), y=int(y), **kw)


def picked():
    cb = mod(".ui.channel_box")
    a = arm()
    return sorted(pb.name for pb in a.pose.bones if cb.bone_selected(pb)) if a.mode == 'POSE' else []


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_scene():
    bpy.ops.allset.keymap_activate()
    for ob in list(bpy.data.objects):
        if ob.type in {'MESH', 'ARMATURE'}:
            bpy.data.objects.remove(ob)
    cmds = mod(".command_line.cmds_shim")
    cmds.joint(p=(0, 0, 0))
    cmds.joint(p=(0, 3, 0))
    cmds.joint(p=(0, 6, 0))
    a = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    area, region = v3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.allset.create(kind='CUBE')
    cube = bpy.context.active_object
    cube.location = (4.0, 0.0, 0.0)
    for o in bpy.context.scene.objects:
        o.select_set(False)
    bpy.context.view_layer.update()
    C.update(arm=a.name, cube=cube.name, world=tuple(cube.matrix_world.translation))
    with bpy.context.temp_override(window=win(), area=area, region=region):
        C["open"] = bpy.ops.allset.menu_item(item="Windows/General Editors/Hypergraph: Hierarchy")


@step
def s_open():
    if again(s_open, lambda: hg_area()[0] is not None):
        return
    C["w"] = hg_area()[0]
    check(f"Hypergraph: Hierarchy opens ({C['open']})", C["w"] is not None)
    redraw()


@step
def s_drawn():
    hg = mod(".ui.hypergraph")
    if again(s_drawn, lambda: hg_area()[1].as_pointer() in hg.VIEWS):
        return
    cents, nodes, _by = hg.centres(bpy.context.scene)
    parent = dict(nodes)
    check("joint1 > joint2 > joint3 are nodes under each other",
          parent.get(joint("joint2")) == joint("joint1") and parent.get(joint("joint3")) == joint("joint2")
          and all(joint(n) in cents for n in ("joint1", "joint2", "joint3")))
    check("the kit skeleton object has no node of its own", arm().session_uid not in parent)
    redraw()


@step
def s_shot_open():
    shot("gui_issue566_open.png")
    hev('MOUSEMOVE', 'NOTHING', *node_point(joint("joint2")))


@step
def s_click():
    x, y = node_point(joint("joint2"))
    hev('LEFTMOUSE', 'PRESS', x, y)
    hev('LEFTMOUSE', 'RELEASE', x, y)


@step
def s_click_check():
    check(f"a click on the joint2 node picks joint2 ({picked()})", picked() == ["joint2"]
          and arm().data.bones.active.name == "joint2")
    hev('MOUSEMOVE', 'NOTHING', *node_point(joint("joint3")))


@step
def s_shift_click():
    x, y = node_point(joint("joint3"))
    hev('LEFTMOUSE', 'PRESS', x, y, shift=True)
    hev('LEFTMOUSE', 'RELEASE', x, y, shift=True)


@step
def s_shift_check():
    check(f"Shift+click on joint3 adds it ({picked()})", picked() == ["joint2", "joint3"])
    redraw()


@step
def s_shot_picked():
    shot("gui_issue566_picked.png")
    hev('MOUSEMOVE', 'NOTHING', *node_point(bpy.data.objects[C["cube"]].session_uid))


@step
def s_mmb_press():
    x, y = node_point(bpy.data.objects[C["cube"]].session_uid)
    C["to"] = node_point(joint("joint3"))
    hev('MIDDLEMOUSE', 'PRESS', x, y)


@step
def s_mmb_move():
    x, y = C["to"]
    hev('MOUSEMOVE', 'NOTHING', x - 10, y)


@step
def s_mmb_move2():
    hev('MOUSEMOVE', 'NOTHING', *C["to"])


@step
def s_mmb_release():
    hev('MIDDLEMOUSE', 'RELEASE', *C["to"])


@step
def s_parent_check():
    from mathutils import Vector
    cube = bpy.data.objects[C["cube"]]
    bpy.context.view_layer.update()
    moved = (cube.matrix_world.translation - Vector(C["world"])).length
    check(f"MMB drag of pCube1 onto joint3 parents it under joint3 ({cube.parent}, {cube.parent_bone})",
          cube.parent == arm() and cube.parent_type == 'BONE' and cube.parent_bone == "joint3")
    check(f"world position kept ({moved:.6f})", moved < 1e-4)
    redraw()


@step
def s_final_shot():
    shot("gui_issue566_final.png")


run()
