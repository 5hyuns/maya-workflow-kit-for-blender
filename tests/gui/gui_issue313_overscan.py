"""Issue #313: camera Overscan like Maya. Looking through a camera (Panels > Look Through Selected) fits its frame to
the view at Overscan 1 (a new camera's value); Overscan 1.3 / 2 make the frame 1 / 1.3 / half of the view. The value
is in the Attribute Editor's Display Options."""

import os
import sys
from importlib import import_module

import bpy
from bpy_extras.view3d_utils import location_3d_to_region_2d

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, run, screenshot, setup, step, view3d, win, load_maya_layout  # noqa: E402

C = {}
SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")


def area3d():
    return max((a for a in win().screen.areas if a.type == 'VIEW_3D'), key=lambda a: a.width * a.height)


def region(area):
    return next(r for r in area.regions if r.type == 'WINDOW')


def frame_fill():
    """(frame width / view width, frame height / view height) of the camera frame in the big view."""
    area = area3d()
    reg, rv3d = region(area), area.spaces.active.region_3d
    cam = C["cam"]
    pts = [location_3d_to_region_2d(reg, rv3d, cam.matrix_world @ v) for v in cam.data.view_frame(scene=bpy.context.scene)]
    xs, ys = [p.x for p in pts], [p.y for p in pts]
    return (max(xs) - min(xs)) / reg.width, (max(ys) - min(ys)) / reg.height


def fits(fill, want, tol=0.03):
    return abs(max(fill) - want) < tol


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_camera():
    sc = bpy.context.scene
    cam = bpy.data.objects.new("camera313", bpy.data.cameras.new("camera313"))
    sc.collection.objects.link(cam)
    cam.location = (0, -10, 2)
    cam.rotation_euler = (1.4, 0, 0)
    C["cam"] = cam
    check(f"a new camera's Overscan is 1 like Maya ({cam.data.allset_overscan})", cam.data.allset_overscan == 1.0)
    for o in sc.objects:
        o.select_set(o == cam)
    bpy.context.view_layer.objects.active = cam
    area = area3d()
    with bpy.context.temp_override(window=win(), area=area, region=region(area)):
        bpy.ops.allset.panel_look_through()


@step
def s_fit():
    fill = frame_fill()
    check(f"looking through it: the frame fills the view at Overscan 1 ({fill[0]:.3f}, {fill[1]:.3f})", fits(fill, 1.0))
    C["cam"].data.allset_overscan = 1.3


@step
def s_13():
    fill = frame_fill()
    check(f"Overscan 1.3: the frame is 1 / 1.3 of the view ({fill[0]:.3f}, {fill[1]:.3f})", fits(fill, 1 / 1.3))
    C["cam"].data.allset_overscan = 2.0


@step
def s_2():
    fill = frame_fill()
    check(f"Overscan 2: half of the view ({fill[0]:.3f}, {fill[1]:.3f})", fits(fill, 0.5))
    C["cam"].data.allset_overscan = 1.1
    if SHOTS:
        bpy.context.view_layer.objects.active = C["cam"]


@step
def s_shot():
    if SHOTS:
        screenshot(os.path.join(SHOTS, "gui_issue313_overscan.png"))
    ae = import_module(MODULE + ".ui.ae_layout")
    rows = [r for sec in ae.CAMERA if sec[0] == "Display Options" for r in sec[2:]] if isinstance(ae.CAMERA[0], tuple) \
        else [r for sec in ae.CAMERA for r in getattr(sec, "rows", ())]
    check(f"Attribute Editor > Display Options has Overscan ({len(rows)} rows)",
          any("allset_overscan" in str(r) for r in rows) or "allset_overscan" in str(ae.CAMERA))


run()
