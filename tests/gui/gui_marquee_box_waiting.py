"""A replace marquee over two posed skeletons whose joint rules run before Blender's own box result is evaluated (the
rules run in the same main-loop pass as the end of Blender's box): the joints are picked as always (each skeleton's
boxed joint closest to the root, the last skeleton active, both in Pose mode), the joint selection is evaluated
together with Blender's result, the evaluation after the mode switches updates only the skeleton objects, and one
Ctrl+Z takes the marquee back."""

import os
import sys
from importlib import import_module

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, load_maya_layout, run, setup, step, view3d, win  # noqa: E402

C = {"rounds": [], "applied": []}
KINDS = ('SCENE', 'OBJECT', 'ARMATURE', 'MESH')


def mod(name):
    return import_module(MODULE + name)


def to_window(world):
    from bpy_extras.view3d_utils import location_3d_to_region_2d
    area, region = view3d()
    p = location_3d_to_region_2d(region, area.spaces.active.region_3d, world)
    return Vector((p.x + region.x, p.y + region.y))


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


def picked():
    cb = mod(".ui.channel_box")
    return {name: sorted(pb.name for pb in bpy.data.objects[name].pose.bones if cb.bone_selected(pb))
            for name in C["rigs"]}


def state():
    layer = bpy.context.view_layer
    return (picked(), [bpy.data.objects[n].mode for n in C["rigs"]],
            layer.objects.active.name if layer.objects.active else None)


def mark_undo(frame):
    """A known undo step: the scene at ``frame`` (an undo past it shows another frame)."""
    bpy.context.scene.frame_set(frame)
    bpy.ops.ed.undo_push(message=f"frame {frame}")


def _note(_scene, depsgraph):
    C["rounds"].append({k for k in KINDS if depsgraph.id_type_updated(k)})


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_scene():
    bpy.ops.allset.keymap_activate()
    joints = mod(".operators.joints")
    k = mod(".operators.units").maya_unit()
    rigs = []
    for x0 in (-10.0, 2.0):
        a = joints.new_skeleton(bpy.context)
        names, parent = [], None
        for x in (x0, x0 + 4.0, x0 + 8.0):
            parent = joints.add_joint(a, Vector((x, 0.0, 4.0)) * k, parent, length=1.0 * k)
            names.append(parent)
        joints.finish(bpy.context, a, names)
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        for n in names:
            a.data.bones[n][joints.RADIUS] = 2.0
        rigs.append((a.name, names))
    order = [o.name for o in bpy.context.scene.objects if o.type == 'ARMATURE']
    rigs.sort(key=lambda r: order.index(r[0]))      # the marquee goes skeleton by skeleton in the scene's order
    C["rigs"] = [r[0] for r in rigs]
    C["names"] = dict(rigs)
    area, region = view3d()
    rv3d = area.spaces.active.region_3d
    rv3d.view_perspective = 'PERSP'
    rv3d.view_location = (0.0, 0.0, 4.0 * k)
    rv3d.view_distance = 40.0 * k
    # both skeletons in Pose mode, the last one active, each with its middle joint picked
    for ob in bpy.context.scene.objects:
        ob.select_set(False)
    for name in C["rigs"]:
        bpy.data.objects[name].select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects[C["rigs"][-1]]
    bpy.ops.object.mode_set(mode='POSE')
    cb = mod(".ui.channel_box")
    for name in C["rigs"]:
        ob = bpy.data.objects[name]
        for pb in ob.pose.bones:
            cb.set_bone_selected(pb, pb.name == C["names"][name][1])
        ob.data.bones.active = ob.data.bones[C["names"][name][1]]
    redraw()


@step
def s_scene_undo():
    mark_undo(1)
    mark_undo(7)
    C["start"] = state()
    want = ({n: [C["names"][n][1]] for n in C["rigs"]}, ['POSE', 'POSE'], C["rigs"][-1])
    check(f"two skeletons in Pose mode, the last active, a joint each ({C['start']})", C["start"] == want)


def corners():
    first = bpy.data.objects[C["rigs"][0]]
    last = bpy.data.objects[C["rigs"][-1]]
    p0 = to_window(first.matrix_world @ first.data.bones[C["names"][first.name][0]].head_local)
    p1 = to_window(last.matrix_world @ last.data.bones[C["names"][last.name][-1]].head_local)
    return p0 + Vector((-60, 60)), p1 + Vector((60, -60))


@step
def s_box_press():
    jm = mod(".operators.joint_marquee")
    # the joint rules' check runs on every main-loop pass: it runs in the pass that ends Blender's box, before the
    # scene is evaluated and drawn
    C["tick"] = jm._TICK
    jm._TICK = 0.0
    real = jm.apply

    def apply(*args):
        C["applied"].append({"waiting": args[4] if len(args) > 4 else None, "first": len(C["rounds"])})
        try:
            return real(*args)
        finally:
            C["applied"][-1]["last"] = len(C["rounds"])
    jm.apply = apply
    C["real_apply"] = real
    p0, _p1 = corners()
    ev('MOUSEMOVE', 'NOTHING', x=int(p0.x), y=int(p0.y))
    ev('LEFTMOUSE', 'PRESS', x=int(p0.x), y=int(p0.y))


@step
def s_box_move():
    p0, p1 = corners()
    p = (p0 + p1) / 2
    ev('MOUSEMOVE', 'NOTHING', x=int(p.x), y=int(p.y))


@step
def s_box_move2():
    _p0, p1 = corners()
    ev('MOUSEMOVE', 'NOTHING', x=int(p1.x), y=int(p1.y))


@step
def s_box_release():
    _p0, p1 = corners()
    C["rounds"].clear()
    bpy.app.handlers.depsgraph_update_post.append(_note)
    ev('LEFTMOUSE', 'RELEASE', x=int(p1.x), y=int(p1.y))


@step
def s_settle():
    pass


@step
def s_box_done():
    jm = mod(".operators.joint_marquee")
    bpy.app.handlers.depsgraph_update_post.remove(_note)
    jm.apply = C["real_apply"]
    jm._TICK = C["tick"]
    got = state()
    want = ({n: [C["names"][n][0]] for n in C["rigs"]}, ['POSE', 'POSE'], C["rigs"][-1])
    check(f"the marquee picks each skeleton's top joint, the last skeleton active ({got})", got == want)
    applied = C["applied"]
    check(f"the joint rules ran once, before Blender's result was evaluated ({applied})",
          len(applied) == 1 and applied[0]["waiting"] is True and applied[0]["first"] == 0)
    inside = C["rounds"][applied[0]["first"]:applied[0]["last"]] if applied else []
    check(f"the selection is evaluated with Blender's result, then only the mode switches ({inside})",
          len(inside) == 2 and 'SCENE' in inside[0] and not inside[1] & {'SCENE', 'ARMATURE', 'MESH'})
    check("the evaluation count is off once the marquee has ended",
          jm._count not in bpy.app.handlers.depsgraph_update_post)


@step
def s_undo():
    _p0, p1 = corners()
    ev('MOUSEMOVE', 'NOTHING', x=int(p1.x), y=int(p1.y) + 80)
    ev('LEFT_CTRL', 'PRESS', ctrl=True)
    ev('Z', 'PRESS', ctrl=True)
    ev('Z', 'RELEASE', ctrl=True)
    ev('LEFT_CTRL', 'RELEASE')


@step
def s_undo_settle():
    pass


@step
def s_undo_done():
    got = state()
    check(f"one Ctrl+Z takes the marquee back ({got})", got == C["start"])
    check(f"and nothing before it (frame {bpy.context.scene.frame_current})", bpy.context.scene.frame_current == 7)


run()
