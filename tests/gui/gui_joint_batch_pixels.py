"""Maya joints drawn from a points buffer and a colours buffer kept across redraws look exactly like the same lines
drawn from one interleaved buffer: every pixel of the view is the same, with spheres, bones, control shapes, selected
joints (their local axes, the lead colour) and X-Ray Joints. A new pose draws the same pixels as drawing it from
scratch."""

import math
import os
import sys
from importlib import import_module

import bpy
import numpy as np
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, load_maya_layout, run, screenshot, setup, step, view3d, win  # noqa: E402

C = {}


def mod(name):
    return import_module(MODULE + name)


def grab(name):
    """The main 3D View's pixels (RGBA float, rows bottom up)."""
    path = os.path.join(bpy.app.tempdir, f"gui_joint_batch_pixels_{name}.png")
    screenshot(path)
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    px = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(px)
    bpy.data.images.remove(img)
    _area, region = view3d()
    px = px.reshape(h, w, 4)
    return px[region.y + 2:region.y + region.height - 2, region.x + 2:region.x + region.width - 2].copy()


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


def interleaved(hit):
    """The lines as one buffer of points and colours."""
    import gpu
    from gpu_extras.batch import batch_for_shader
    sh = gpu.shader.from_builtin('POLYLINE_SMOOTH_COLOR')
    return batch_for_shader(sh, 'LINES', {"pos": hit[0], "color": hit[1]})


def use(batcher):
    mj = mod(".ui.maya_joints")
    mj._new_batch = batcher
    for hit in mj._JOINED.values():
        hit[2] = None                       # every view makes its batch again
    redraw()


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
    made, parent = [], None
    for i in range(9):
        p = made[(i - 1) // 2] if i and i % 4 == 0 else parent
        parent = joints.add_joint(arm, Vector((-8.0 + 2.0 * i, 0.8 * math.sin(i), 2.0 + 0.6 * i)) * k, p,
                                  length=1.0 * k)
        made.append(parent)
    joints.finish(bpy.context, arm, made)
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.mesh.primitive_circle_add(vertices=12, radius=1.5 * k, location=(0.0, 0.0, -20.0 * k))
    ctrl = bpy.context.object
    arm.pose.bones[made[3]].custom_shape = ctrl
    for b in arm.data.bones:
        b[joints.RADIUS] = 2.0
    for ob in bpy.context.scene.objects:
        ob.select_set(False)
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    bpy.ops.object.mode_set(mode='POSE')
    for i, pb in enumerate(arm.pose.bones):
        pb.select = i in (1, 5, 6)
    arm.data.bones.active = arm.data.bones[made[5]]
    C["arm"], C["made"] = arm.name, made
    area, _region = view3d()
    rv3d = area.spaces.active.region_3d
    rv3d.view_perspective = 'PERSP'
    rv3d.view_location = Vector((0.0, 0.0, 4.0)) * k
    rv3d.view_distance = 30.0 * k
    C["real"] = mod(".ui.maya_joints")._new_batch
    redraw()


@step
def s_kit():
    C["kit"] = grab("kit")
    use(interleaved)


@step
def s_one_buffer():
    one = grab("one_buffer")
    kit = C["kit"]
    lit = int((np.abs(kit[..., :3] - kit[0, 0, :3]).max(axis=-1) > 0.05).sum())
    diff = int((np.abs(kit - one).max(axis=-1) > 0).sum())
    check(f"two buffers draw the pixels of one buffer ({diff} pixels differ, {lit} pixels away from the background)",
          diff == 0 and lit > 2000)
    use(C["real"])
    area, _region = view3d()
    area.spaces.active.overlay.show_xray_bone = True
    redraw()


@step
def s_xray_kit():
    C["kit_x"] = grab("kit_xray")
    use(interleaved)


@step
def s_xray_one():
    diff = int((np.abs(C["kit_x"] - grab("one_xray")).max(axis=-1) > 0).sum())
    check(f"X-Ray Joints: the same pixels ({diff} differ)", diff == 0)
    use(C["real"])
    arm = bpy.data.objects[C["arm"]]
    pb = arm.pose.bones[C["made"][0]]
    pb.rotation_mode = 'XYZ'
    pb.rotation_euler = (0.3, 0.2, -0.4)
    bpy.context.view_layer.update()
    redraw()


@step
def s_posed():
    C["posed"] = grab("posed")
    mj = mod(".ui.maya_joints")
    mj._forget()                            # drawn from scratch: no kept colours, lines or buffers
    redraw()


@step
def s_posed_fresh():
    diff = int((np.abs(C["posed"] - grab("posed_fresh")).max(axis=-1) > 0).sum())
    check(f"a new pose draws what a build from scratch draws ({diff} pixels differ)", diff == 0)


run()
