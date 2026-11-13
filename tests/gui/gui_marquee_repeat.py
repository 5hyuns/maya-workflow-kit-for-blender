"""The same marquee over a kit-drawn joint picks the same joint every time, also when marquees follow each other
faster than the joint rules (they run once Blender's box has ended) — each drag's joint rules are applied before the
next drag starts. Like Maya, a box around a joint in Object Mode picks that joint."""

import os
import sys
from importlib import import_module

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, load_maya_layout, run, setup, step, view3d, win  # noqa: E402

C = {}


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


def arm():
    return bpy.data.objects[C["arm"]]


def tip():
    a = arm()
    return to_window(a.matrix_world @ a.data.bones[C["names"][2]].head_local)


def selected_joints():
    a = arm()
    if a.mode != 'POSE':
        return []
    cb = mod(".ui.channel_box")
    return [pb.name for pb in a.pose.bones if cb.bone_selected(pb)]


def mark_undo(frame):
    """A known undo step: the scene at ``frame`` (an undo past it shows another frame)."""
    bpy.context.scene.frame_set(frame)
    bpy.ops.ed.undo_push(message=f"frame {frame}")


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
        a.data.bones[n][joints.RADIUS] = 4.0
    C["arm"], C["names"] = a.name, names
    area, _region = view3d()
    rv3d = area.spaces.active.region_3d
    rv3d.view_perspective = 'PERSP'
    rv3d.view_location = (0.0, 0.0, 4.0 * k)
    rv3d.view_distance = 40.0 * k
    # a small mesh inside the marquee: Blender's box selects it, Maya's rules drop it for the joint
    bpy.ops.mesh.primitive_cube_add(size=0.6 * k, location=(8.0 * k, 0.0, 4.0 * k + 0.9 * k))
    C["cube"] = bpy.context.object.name
    for ob in bpy.context.scene.objects:
        ob.select_set(False)
    redraw()


def picked():
    """(selected joints, selected meshes)."""
    return selected_joints(), sorted(o.name for o in bpy.context.selected_objects if o.type == 'MESH')


def deselect():
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    a = arm()
    cb = mod(".ui.channel_box")
    for pb in a.pose.bones:
        cb.set_bone_selected(pb, False)
    for ob in bpy.context.scene.objects:
        ob.select_set(False)
    redraw()


def drag_events(half, gap=0.02):
    """One marquee around the tip joint as a pointer drag, an event every ``gap`` s (a quick hand)."""
    p0, p1 = tip() - Vector((half, half)), tip() + Vector((half, half))
    yield ('MOUSEMOVE', 'NOTHING', p0)
    yield ('LEFTMOUSE', 'PRESS', p0)
    for i in range(1, 9):
        yield ('MOUSEMOVE', 'NOTHING', p0 + (p1 - p0) * (i / 8))
    yield ('LEFTMOUSE', 'RELEASE', p1)


def play(drags, gap=0.02):
    """Feed the drags' events from a timer, ``gap`` s apart; a drag's release and the next drag's press go out
    together (the next marquee starts before the joint rules' own timer can run)."""
    ticks = []
    for d in drags:
        events = list(d)
        if ticks:
            ticks[-1] += events[:2]          # release of the drag before + move / press of this one
            events = events[2:]
        ticks += [[e] for e in events]

    def tick():
        if not ticks:
            return None
        for t, v, p in ticks.pop(0):
            ev(t, v, x=int(p.x), y=int(p.y))
        return gap
    bpy.app.timers.register(tick, first_interval=0.0)


def settle():
    pass


@step
def s_one():
    deselect()
    play([drag_events(40)])


for _i in range(5):
    step(settle)


@step
def s_one_check():
    C["want"] = picked()
    check(f"one marquee picks the tip joint, not the mesh beside it ({C['want']})",
          C["want"] == ([C["names"][2]], []))


def rapid(k):
    def go():
        deselect()
        play([drag_events(40) for _ in range(3)])   # three marquees, the next press 20 ms after a release
    go.__name__ = f"s_rapid_{k}"

    def look():
        got = picked()
        check(f"three quick marquees, round {k}: the same pick as one ({got})", got == C["want"])
    look.__name__ = f"s_rapid_{k}_check"
    step(go)
    for _ in range(6):
        step(settle)
    step(look)


for _k in range(3):
    rapid(_k)


run()
