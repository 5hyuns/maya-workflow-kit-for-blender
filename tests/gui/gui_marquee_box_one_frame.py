"""A marquee over kit-drawn joints shows its final selection in the first frame after the release, like Maya: the
joint rules run in the main-loop pass that ends Blender's own box, before the scene is evaluated and drawn, so
Blender's own result (the meshes in an Object Mode box, the joints taken off by a Pose mode box) is never drawn.
Checked frame by frame (the view's pixels and the selection each frame draws) for boxes from Object Mode over many
meshes and from Pose mode over two skeletons, each three times, let go at different moments."""

import os
import sys
from importlib import import_module

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, load_maya_layout, run, setup, step, view3d, win  # noqa: E402

C = {"frames": [], "armed": False}


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


def state():
    """(selected meshes, each skeleton's picked joints, each skeleton's mode, active object)."""
    cb = mod(".ui.channel_box")
    layer = bpy.context.view_layer
    picks = {}
    for name in C["rigs"]:
        ob = bpy.data.objects[name]
        picks[name] = sorted(pb.name for pb in ob.pose.bones if cb.bone_selected(pb)) if ob.mode == 'POSE' else []
    return (sum(1 for o in bpy.context.selected_objects if o.type == 'MESH'), picks,
            [bpy.data.objects[n].mode for n in C["rigs"]], layer.objects.active.name if layer.objects.active else None)


def _released():
    """Blender has ended this drag's box with a result (it registered a new box select)."""
    ops = bpy.context.window_manager.operators
    return (len(ops) and ops[-1].as_pointer() != C["last_op"] and ops[-1].bl_idname == "VIEW3D_OT_select_box")


def _shot():
    """Every draw of the main view after the release: its pixels and the selection it shows."""
    if not C["armed"] or bpy.context.area is None or bpy.context.area.as_pointer() != C["area"]:
        return
    if not _released():
        return
    import gpu
    import numpy as np
    region = bpy.context.region
    buf = gpu.state.active_framebuffer_get().read_color(0, 0, region.width, region.height, 4, 0, 'UBYTE')
    C["frames"].append((np.frombuffer(buf, dtype=np.uint8).reshape(region.height, region.width, 4)[:, :, :3].copy(),
                        state()))


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
    rigs.sort(key=lambda r: order.index(r[0]))
    C["rigs"] = [r[0] for r in rigs]
    C["names"] = dict(rigs)
    # many small meshes in the box, below the joints: Blender's Object Mode box selects them, the joint rules drop them
    mesh = None
    for i in range(12):
        for j in range(5):
            bpy.ops.mesh.primitive_cube_add(size=0.5 * k, location=((-10.0 + 1.8 * i) * k, 0.0, (-1.0 - 1.2 * j) * k))
            if mesh is None:
                mesh = bpy.context.object.data
    area, region = view3d()
    rv3d = area.spaces.active.region_3d
    rv3d.view_perspective = 'PERSP'
    rv3d.view_location = (0.0, 0.0, 0.0)
    rv3d.view_distance = 55.0 * k
    C["area"] = area.as_pointer()
    C["handle"] = bpy.types.SpaceView3D.draw_handler_add(_shot, (), 'WINDOW', 'POST_PIXEL')
    for ob in bpy.context.scene.objects:
        ob.select_set(False)
    bpy.context.view_layer.objects.active = None
    redraw()


def corners():
    first = bpy.data.objects[C["rigs"][0]]
    last = bpy.data.objects[C["rigs"][-1]]
    k = mod(".operators.units").maya_unit()
    p0 = to_window(first.matrix_world @ first.data.bones[C["names"][first.name][0]].head_local)
    p1 = to_window(last.matrix_world @ last.data.bones[C["names"][last.name][-1]].head_local)
    low = to_window(Vector((0.0, 0.0, -8.0 * k)))
    return p0 + Vector((-60, 60)), Vector((p1.x + 60, low.y))


def object_start():
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in bpy.context.scene.objects:
        ob.select_set(False)
    bpy.context.view_layer.objects.active = None
    redraw()


def pose_start():
    """Both skeletons in Pose mode, the last active, each with its middle joint picked."""
    object_start()
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


def box(name, start, offset):
    def prepare():
        start()

    def press():
        ops = bpy.context.window_manager.operators
        C["last_op"] = ops[-1].as_pointer() if len(ops) else 0
        C["frames"], C["armed"] = [], True
        p0, _p1 = corners()
        ev('MOUSEMOVE', 'NOTHING', x=int(p0.x), y=int(p0.y))
        ev('LEFTMOUSE', 'PRESS', x=int(p0.x), y=int(p0.y))

    def move():
        p0, p1 = corners()
        p = (p0 + p1) / 2
        ev('MOUSEMOVE', 'NOTHING', x=int(p.x), y=int(p.y))

    def move2():
        _p0, p1 = corners()
        ev('MOUSEMOVE', 'NOTHING', x=int(p1.x), y=int(p1.y))

    def release():
        _p0, p1 = corners()

        def send():
            ev('LEFTMOUSE', 'RELEASE', x=int(p1.x), y=int(p1.y))
        # a hand lets go at any moment: off the steps' own timer beat, at another moment each box
        bpy.app.timers.register(send, first_interval=offset)

    def settle():
        redraw()                    # one more frame of the settled view

    def look():
        import numpy as np
        C["armed"] = False
        final = state()
        frames = C["frames"]
        want = (0, {n: [C["names"][n][0]] for n in C["rigs"]}, ['POSE', 'POSE'], C["rigs"][-1])
        check(f"{name}: the marquee picks each skeleton's top joint and no mesh ({final})", final == want)
        shown = [s for _px, s in frames]
        check(f"{name}: every frame after the release shows the final selection ({len(frames)} frames, {shown})",
              len(frames) >= 2 and all(s == final for s in shown))
        last = frames[-1][0] if frames else None
        diff = [int(np.count_nonzero((np.abs(px.astype(np.int16) - last).max(axis=2)) > 64)) for px, _s in frames]
        check(f"{name}: and the same picture ({diff} pixels differ from the last frame)",
              bool(frames) and not any(diff))
    for i, fn in enumerate((prepare, press, move, move2, release, settle, settle, look)):
        f = (lambda fn: lambda: fn())(fn)
        f.__name__ = f"s_{name}_{i}"
        step(f)


for _k in range(3):
    box(f"object_box_{_k}", object_start, 0.013 + 0.016 * _k)
    box(f"pose_box_{_k}", pose_start, 0.021 + 0.016 * _k)


@step
def s_done():
    bpy.types.SpaceView3D.draw_handler_remove(C["handle"], 'WINDOW')


run()
