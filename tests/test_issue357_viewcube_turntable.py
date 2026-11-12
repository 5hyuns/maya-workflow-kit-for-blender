"""#357: the ViewCube drag's turntable — around the world Z axis for a sideways drag, around the view's own X axis for
an up / down drag, sideways reversed while the view is upside down (like Alt+LMB), at Blender's turntable speed x
CUBE_TUMBLE_RATIO (Maya: a 60 px drag on the cube turns the view about 35 degrees, Alt+LMB 24)."""

import math
from importlib import import_module

import bpy
from mathutils import Quaternion, Vector

import kit

vf = import_module(kit.MODULE + ".ui.view_furniture")


def _close(a, b, eps=1e-5):
    return (Vector(a) - Vector(b)).length < eps


def test_rate():
    prefs = bpy.context.preferences
    want = prefs.inputs.view_rotate_sensitivity_turntable / (prefs.system.ui_scale or 1.0) * vf.CUBE_TUMBLE_RATIO
    assert abs(vf.tumble_rate(bpy.context) - want) < 1e-9
    assert 1.4 < vf.CUBE_TUMBLE_RATIO < 1.55


def test_sideways_turns_around_world_z():
    q = Quaternion((1.0, 0.0, 0.0), math.radians(60))           # a view looking down at 30 degrees
    rate = math.radians(1.0)
    turned = vf.turntable(q, 30, 0, rate)
    up_before, up_after = q @ Vector((0, 0, -1)), turned @ Vector((0, 0, -1))
    assert abs(up_before.z - up_after.z) < 1e-6                 # the tilt stays
    a0 = math.atan2(up_before.y, up_before.x)
    a1 = math.atan2(up_after.y, up_after.x)
    assert abs(((a1 - a0 + math.pi) % (2 * math.pi) - math.pi) + math.radians(30)) < 1e-5


def test_up_down_turns_around_the_view_x_axis():
    q = Quaternion((1.0, 0.0, 0.0), math.radians(60))
    turned = vf.turntable(q, 0, 10, math.radians(1.0))
    assert _close(q @ Vector((1, 0, 0)), turned @ Vector((1, 0, 0)))      # the view's X axis stays
    tilt0 = (q @ Vector((0, 0, -1))).z
    tilt1 = (turned @ Vector((0, 0, -1))).z
    assert abs(tilt0 - tilt1) > 0.1


def test_upside_down_reverses_sideways():
    upright = Quaternion((1.0, 0.0, 0.0), math.radians(60))
    flipped = Quaternion((1.0, 0.0, 0.0), math.radians(240))  # past the top: the view's up points down
    assert (flipped @ Vector((0, 1, 0))).z < 0
    r = math.radians(1.0)

    def yaw_change(q):
        d0, d1 = q @ Vector((0, 0, -1)), vf.turntable(q, 20, 0, r) @ Vector((0, 0, -1))
        return (math.atan2(d1.y, d1.x) - math.atan2(d0.y, d0.x) + math.pi) % (2 * math.pi) - math.pi
    assert yaw_change(upright) * yaw_change(flipped) < 0


def test_face_operator_drags():
    cls = vf.ALLSET_OT_view_cube_face
    assert hasattr(cls, "invoke") and hasattr(cls, "modal")
