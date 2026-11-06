"""Editable motion trail with the Move tool: a plain pick deselects the object, the kit draws a move manipulator on
the picked key; its X arrow moves the key along world X only, a middle drag anywhere uses the last used handle, the
XZ plane square moves in that plane, one undo takes one move back; an object's own gizmo over a key marker wins; and
a bone's trail in Pose Mode moves the bone's location key."""

import math
import os
import sys
from importlib import import_module

import bpy
import numpy as np
from mathutils import Euler, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, load_maya_layout, run, screenshot, setup, step, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def mod(name):
    return import_module(MODULE + name)


def mte():
    return mod(".operators.motion_trail_edit")


def region_xy(world):
    from bpy_extras.view3d_utils import location_3d_to_region_2d
    area, region = view3d()
    return location_3d_to_region_2d(region, area.spaces.active.region_3d, world)


def to_window(world):
    _area, region = view3d()
    p = region_xy(world)
    return None if p is None else (int(round(p.x + region.x)), int(round(p.y + region.y)))


def shot(name):
    path = os.path.join(SHOTS or bpy.app.tempdir, f"gui_motion_trail_manip_{name}.png")
    screenshot(path)
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    px = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(px)
    bpy.data.images.remove(img)
    return px.reshape(h, w, 4)[..., :3]


def fcurve_value(id_, path, index, frame):
    for fc in mod(".compat").id_fcurves(id_):
        if fc.data_path == path and fc.array_index == index:
            for kp in fc.keyframe_points:
                if abs(kp.co.x - frame) < 1e-4:
                    return kp.co.y
    return None


def kx(frame=10):
    return fcurve_value(bpy.data.objects["Ball"], "location", 0, frame)


def kz(frame=10):
    return fcurve_value(bpy.data.objects["Ball"], "location", 2, frame)


def path_point(holder, frame):
    mp = holder.motion_path
    return Vector(mp.points[frame - mp.frame_start].co)


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


def override():
    area, region = view3d()
    return bpy.context.temp_override(window=win(), area=area, region=region)


def btn(kind, p, value):
    ev(kind, value, x=p[0], y=p[1])


def move(p):
    ev('MOUSEMOVE', 'NOTHING', x=p[0], y=p[1])


def drag_steps(kind, start, delta, n=4, release=True):
    """Steps: hover, press, n moves, release."""
    step(lambda: move(C[start]))
    step(lambda: btn(kind, C[start], 'PRESS'))
    for i in range(1, n + 1):
        step(lambda i=i: move((C[start][0] + delta[0] * i // n, C[start][1] + delta[1] * i // n)))
    if release:
        step(lambda: btn(kind, (C[start][0] + delta[0], C[start][1] + delta[1]), 'RELEASE'))


def undo():
    ev('LEFT_CTRL', 'PRESS', ctrl=True)
    ev('Z', 'PRESS', ctrl=True)
    ev('Z', 'RELEASE', ctrl=True)
    ev('LEFT_CTRL', 'RELEASE')


def manip():
    """Window points of the manipulator centre, the X arrow (70 %) and the XZ plane square."""
    centre = mte().anchor(_ctx())
    c, axes = mte().manip_layout(_ctx(), centre)
    _area, region = view3d()
    off = Vector((region.x, region.y))
    ux, lx = axes[0]
    sq = mte().plane_square(c, axes, 1)
    return {"c": tuple(int(round(v)) for v in c + off), "x": tuple(int(round(v)) for v in c + ux * (lx * 0.7) + off),
            "xz": tuple(int(round(v)) for v in sq[0] + off), "axes": axes}


class _Ctx:
    """The bits of a 3D View context the kit's manipulator layout reads."""

    def __init__(self):
        area, region = view3d()
        self.region = region
        self.region_data = area.spaces.active.region_3d
        self.preferences = bpy.context.preferences
        self.scene = bpy.context.scene
        self.active_object = bpy.context.view_layer.objects.active
        self.mode = bpy.context.mode
        self.view_layer = bpy.context.view_layer
        self.space_data = area.spaces.active


def _ctx():
    return _Ctx()


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_scene():
    bpy.ops.allset.keymap_activate()
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    scene = bpy.context.scene
    k = mod(".operators.units").maya_unit()
    C["k"] = k
    scene.frame_start, scene.frame_end = 1, 20
    ball = bpy.data.objects.new("Ball", None)
    ball.empty_display_size = 0.3 * k
    scene.collection.objects.link(ball)
    for f, p in ((1, (0, 0, 0)), (10, (5, 0, 0)), (20, (10, 0, 5))):
        ball.location = Vector(p) * k
        ball.keyframe_insert("location", frame=f)
    scene.frame_set(1)
    for ob in scene.objects:
        ob.select_set(ob == ball)
    bpy.context.view_layer.objects.active = ball
    with override():
        bpy.ops.allset.motion_trail(action='CREATE')
        bpy.ops.wm.tool_set_by_id(name='builtin.move')
    area, region = view3d()
    space = area.spaces.active
    space.overlay.show_motion_paths = True
    rv3d = space.region_3d
    rv3d.view_perspective = 'ORTHO'
    rv3d.view_rotation = Euler((math.radians(90), 0, 0)).to_quaternion()     # front: X right, Z up
    rv3d.view_location = Vector((5, 0, 2)) * k
    rv3d.view_distance = 18 * k
    redraw()


@step
def s_ready():
    ball = bpy.data.objects["Ball"]
    check(f"the Move tool is active ({mod('.operators.preselect').tool_id(bpy.context)})",
          mod('.operators.preselect').tool_id(bpy.context) == 'builtin.move')
    with override():
        bpy.ops.ed.undo_push(message="trail ready")
    C["m10"] = to_window(path_point(ball, 10))
    C["x0"], C["z0"] = kx(), kz()
    move(C["m10"])


step(lambda: btn('LEFTMOUSE', C["m10"], 'PRESS'))
step(lambda: btn('LEFTMOUSE', C["m10"], 'RELEASE'))


@step
def s_picked():
    ball = bpy.data.objects["Ball"]
    check(f"a click picks the key ({mte().picked()})", mte().picked() == [("Ball", "", 10)])
    check(f"and replaces the selection: Ball deselected ({ball.select_get()})", not ball.select_get())
    check(f"nothing moved ({kx():.4f})", abs(kx() - C["x0"]) < 1e-6)
    m = manip()
    C.update(m)
    check(f"the manipulator sits on the key ({m['c']} ~ {C['m10']})",
          abs(m["c"][0] - C["m10"][0]) <= 1 and abs(m["c"][1] - C["m10"][1]) <= 1)
    check(f"front view: X points right, Y (into the view) is hidden ({m['axes'][0][0]}, {m['axes'][1]})",
          m["axes"][0][0].x > 0.99 and m["axes"][1] is None)
    redraw()


@step
def s_drawn():
    px = shot("manip")
    x, y = C["x"]
    patch = px[y - 2:y + 3, x - 2:x + 3]
    red = (patch[..., 0] > 0.6) & (patch[..., 1] < 0.35) & (patch[..., 2] < 0.35)
    check(f"the X arrow is drawn red ({int(red.sum())}/25)", red.sum() >= 3)


# the X arrow: a diagonal drag moves the key along world X only
drag_steps('LEFTMOUSE', "x", (40, 40))


@step
def s_x_moved():
    C["x1"] = kx()
    check(f"the X arrow moves X ({C['x0']:.4f} -> {kx():.4f})", kx() > C["x0"] + 0.5 * C["k"])
    check(f"and not Z ({kz():.5f})", abs(kz() - C["z0"]) < 1e-6)
    check(f"the X arrow is the active handle ({mte()._last_handle[0]})", mte()._last_handle[0] == ('AXIS', 0))
    area, region = view3d()
    C["far"] = (region.x + region.width // 5, region.y + region.height // 5)


# a middle drag anywhere uses the last handle (X): a diagonal drag still moves X only
drag_steps('MIDDLEMOUSE', "far", (40, 40))


@step
def s_mmb_moved():
    check(f"a middle drag anywhere moves along the last handle ({C['x1']:.4f} -> {kx():.4f})",
          kx() > C["x1"] + 0.5 * C["k"])
    check(f"Z still stays ({kz():.5f})", abs(kz() - C["z0"]) < 1e-6)
    C["x2"] = kx()
    C.update(manip())


# the XZ plane square: both X and Z follow
drag_steps('LEFTMOUSE', "xz", (30, 30))


@step
def s_plane_moved():
    check(f"the XZ plane square moves X and Z ({kx():.4f}, {kz():.4f})",
          kx() > C["x2"] + 0.3 * C["k"] and kz() > C["z0"] + 0.3 * C["k"])
    undo()


step(lambda: None)


@step
def s_undone_plane():
    check(f"one undo takes the plane move back ({kx():.4f} ~ {C['x2']:.4f}, {kz():.5f})",
          abs(kx() - C["x2"]) < 1e-5 and abs(kz() - C["z0"]) < 1e-5)
    # the object's own gizmo over a key marker: frame 10, the Ball selected sits on its key 10 marker
    scene = bpy.context.scene
    ball = bpy.data.objects["Ball"]
    mte().clear()
    scene.frame_set(10)
    ball.select_set(True)
    bpy.context.view_layer.objects.active = ball
    C["xg"] = kx()
    C["g"] = to_window(ball.matrix_world.translation)
    redraw()


step(lambda: None)
drag_steps('LEFTMOUSE', "g", (30, 0))


@step
def s_gizmo_won():
    ball = bpy.data.objects["Ball"]
    check(f"the gizmo over a key marker wins: no trail key picked ({mte().picked()})", mte().picked() == [])
    check(f"the key stays ({kx():.4f})", abs(kx() - C["xg"]) < 1e-6)
    check(f"the object moved ({ball.location.x:.4f} vs key {C['xg']:.4f})", ball.location.x > C["xg"] + 0.3 * C["k"])
    undo()


step(lambda: None)


# --- Pose Mode: a bone's head trail ------------------------------------------------------------------------------

@step
def s_rig():
    scene = bpy.context.scene
    k = C["k"]
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    scene.frame_set(1)
    arm = bpy.data.armatures.new("Rig")
    rig = bpy.data.objects.new("Rig", arm)
    scene.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    with override():
        bpy.ops.object.mode_set(mode='EDIT')
        root = arm.edit_bones.new("root")
        root.head, root.tail = (0, 0, 0), (0, 0, 1 * k)
        hand = arm.edit_bones.new("hand")
        hand.head, hand.tail = (0, 0, 2 * k), (0, 0, 3 * k)
        hand.parent = root
        bpy.ops.object.mode_set(mode='POSE')
    pr = rig.pose.bones["root"]
    pr.rotation_mode = 'XYZ'
    pr.rotation_euler = Euler((math.radians(30), 0, 0))      # the parent turned: the hand's channels aren't world
    pb = rig.pose.bones["hand"]
    for f, p in ((1, (0, 0, 0)), (10, (2, 0, 0)), (20, (0, 0, 0))):
        pb.location = Vector(p) * k
        pb.keyframe_insert("location", frame=f)
    scene.frame_set(1)
    with override():
        bpy.ops.pose.select_all(action='DESELECT')
    for owner in (pb, rig.data.bones["hand"]):
        try:
            owner.select = True
        except AttributeError:
            pass
    with override():
        bpy.ops.allset.motion_trail(action='CREATE')
        bpy.ops.wm.tool_set_by_id(name='builtin.select_box')
    with override():
        bpy.ops.pose.select_all(action='DESELECT')
    rv3d = view3d()[0].spaces.active.region_3d
    rv3d.view_location = Vector((1, 0, 2)) * k
    rv3d.view_distance = 10 * k
    redraw()


@step
def s_rig_ready():
    pb = bpy.data.objects["Rig"].pose.bones["hand"]
    check(f"the bone has a motion path ({pb.motion_path is not None})", pb.motion_path is not None)
    with override():
        bpy.ops.ed.undo_push(message="rig ready")
    C["b10"] = to_window(path_point(pb, 10))
    C["w0"] = path_point(pb, 10)
    C["loc0"] = [fcurve_value(bpy.data.objects["Rig"], 'pose.bones["hand"].location', i, 10) for i in range(3)]


drag_steps('LEFTMOUSE', "b10", (0, 40))


@step
def s_bone_moved():
    rig = bpy.data.objects["Rig"]
    pb = rig.pose.bones["hand"]
    w1 = path_point(pb, 10)
    d = w1 - C["w0"]
    check(f"the bone's trail key moved up in the view ({d.x:.4f}, {d.y:.4f}, {d.z:.4f})",
          d.z > 0.3 * C["k"] and abs(d.x) < 1e-3 * C["k"] and abs(d.y) < 1e-3 * C["k"])
    loc = [fcurve_value(rig, 'pose.bones["hand"].location', i, 10) for i in range(3)]
    changed = [i for i in range(3) if abs(loc[i] - C["loc0"][i]) > 1e-6]
    check(f"the bone's location keys took the move in its own space ({C['loc0']} -> {loc})", len(changed) >= 2)
    undo()


step(lambda: None)


@step
def s_bone_undone():
    rig = bpy.data.objects["Rig"]
    loc = [fcurve_value(rig, 'pose.bones["hand"].location', i, 10) for i in range(3)]
    check(f"one undo takes the bone move back ({loc})", all(abs(a - b) < 1e-6 for a, b in zip(loc, C["loc0"])))


run()
