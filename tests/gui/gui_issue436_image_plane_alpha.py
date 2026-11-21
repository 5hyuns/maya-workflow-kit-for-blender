"""#436 in a real view: lowering an image plane's Alpha Gain (its Attribute Editor row) draws the image see-through,
and Alpha Gain 1 draws it opaque again."""

import os
import sys

import bpy
from mathutils import Quaternion

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, run, screenshot, setup, step, view3d  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
TMP = os.environ.get("ALLSET_GUI_TMP", "") or bpy.app.tempdir
C = {}


def _wait(n=4):
    for _ in range(n):
        step(lambda: None)


def _red(path, area):
    """How much redder than green the middle of the 3D View is in a window screenshot (0..1)."""
    import numpy as np
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    px = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    bpy.data.images.remove(img)
    px = px.reshape(h, w, 4)
    cx, cy = area.x + area.width // 2, area.y + area.height // 2
    mid = px[cy - 20:cy + 20, cx - 20:cx + 20, :3]
    return float((mid[..., 0] - mid[..., 1]).mean())


def _shot(name):
    path = os.path.join(TMP, f"gui_issue436_{name}.png")
    screenshot(path)
    C[name] = _red(path, C["area"])
    if SHOTS:
        screenshot(os.path.join(SHOTS, f"gui_issue436_{name}.png"))


@step
def s_setup():
    setup()
    scene = bpy.context.scene
    for ob in list(scene.objects):
        bpy.data.objects.remove(ob)
    img = bpy.data.images.new("reference", 16, 16)
    img.pixels = [1.0, 0.0, 0.0, 1.0] * (16 * 16)
    plane = bpy.data.objects.new("imagePlane1", None)
    plane.empty_display_type = 'IMAGE'
    plane.empty_display_size = 20.0
    plane.data = img
    scene.collection.objects.link(plane)
    C["plane"] = plane
    area, _region = view3d()
    C["area"] = area
    space = area.spaces.active
    space.overlay.show_floor = False
    r3d = space.region_3d
    r3d.view_perspective = 'ORTHO'
    r3d.view_rotation = Quaternion((1.0, 0.0, 0.0, 0.0))     # top view, facing the plane
    r3d.view_location = (0.0, 0.0, 0.0)
    r3d.view_distance = 8.0
    area.tag_redraw()


_wait()


@step
def s_opaque():
    _shot("opaque")
    C["plane"].allset_alpha_gain = 0.3
    C["area"].tag_redraw()


_wait()


@step
def s_see_through():
    _shot("see_through")
    C["plane"].allset_alpha_gain = 1.0
    C["area"].tag_redraw()


_wait()


@step
def s_opaque_again():
    _shot("opaque_again")
    check(f"Alpha Gain 1 draws the image opaque (red {C['opaque']:.3f})", C["opaque"] > 0.8)
    check(f"Alpha Gain 0.3 draws it see-through (red {C['opaque']:.3f} -> {C['see_through']:.3f})",
          0.05 < C["see_through"] < C["opaque"] * 0.6)
    check(f"Alpha Gain 1 again draws it opaque (red {C['opaque_again']:.3f})",
          abs(C["opaque_again"] - C["opaque"]) < 0.02)


run()
