"""Issue #320: in a scene with Unit Scale 0.01 a Rigify metarig comes in 2 cm tall; scaled up 100 times in Object Mode
to fit a 2 m character (scale not applied), its joints draw at their Radius size in the Maya layout, like Maya, where
a joint's own scale leaves its sphere alone: in a front view framing the character every lead-coloured joint pixel
sits on the character, not across the whole view. Screenshots with ALLSET_GUI_SHOTS (or --shots)."""

import os
import sys
from importlib import import_module

import addon_utils
import bpy
import numpy as np
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, load_maya_layout, run, screenshot, setup, step, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
LEAD = np.array([0x43, 0xff, 0xa3]) / 255.0
C = {}


def shot(name):
    path = os.path.join(SHOTS or bpy.app.tempdir, f"gui_issue320_{name}.png")
    screenshot(path)
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    px = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(px)
    bpy.data.images.remove(img)
    return px.reshape(h, w, 4)[..., :3]


def to_window(world):
    from bpy_extras.view3d_utils import location_3d_to_region_2d
    area, region = view3d()
    p = location_3d_to_region_2d(region, area.spaces.active.region_3d, world)
    return None if p is None else Vector((p.x + region.x, p.y + region.y))


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_scene():
    scene = bpy.context.scene
    us = scene.unit_settings
    us.system, us.length_unit, us.scale_length = 'METRIC', 'METERS', 0.01
    if scene.is_property_set("allset_joint_size"):
        scene.property_unset("allset_joint_size")
    for ob in list(bpy.data.objects):
        if ob.type != 'CAMERA':
            bpy.data.objects.remove(ob)
    addon_utils.enable("rigify", default_set=True)
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.object.armature_human_metarig_add()
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
    meta = bpy.context.view_layer.objects.active
    meta.scale = (100.0, 100.0, 100.0)          # 2 m on screen, scale not applied
    for ob in bpy.context.scene.objects:
        ob.select_set(ob is meta)
    bpy.context.view_layer.update()
    C["arm"] = meta.name
    space = area.spaces.active
    space.clip_start, space.clip_end = 1.0, 100000.0     # the view was set up for the scene's earlier unit
    rv3d = space.region_3d
    rv3d.view_perspective = 'ORTHO'
    rv3d.view_rotation = (0.7071068, 0.7071068, 0.0, 0.0)      # front
    rv3d.view_location = (0.0, 0.0, 100.0)
    rv3d.view_distance = 500.0
    for ar in win().screen.areas:
        ar.tag_redraw()


@step
def s_wait():
    pass


@step
def s_check():
    meta = bpy.data.objects[C["arm"]]
    mw = meta.matrix_world
    pts = [to_window(mw @ v) for b in meta.data.bones for v in (b.head_local, b.tail_local)]
    pts = [p for p in pts if p is not None]
    xs, ys = [p.x for p in pts], [p.y for p in pts]
    pad = 0.1 * (max(ys) - min(ys))
    box = (min(xs) - pad, max(xs) + pad, min(ys) - pad, max(ys) + pad)
    px = shot("scaled_metarig")
    _area, region = view3d()
    ys_, xs_ = np.nonzero(np.abs(px - LEAD).max(axis=-1) < 0.08)
    inside = (xs_ >= region.x) & (xs_ < region.x + region.width) & (ys_ >= region.y) & (ys_ < region.y + region.height)
    xs_, ys_ = xs_[inside], ys_[inside]
    check(f"the metarig's joints draw in the lead colour ({len(xs_)} px)", len(xs_) > 200)
    out = ((xs_ < box[0]) | (xs_ > box[1]) | (ys_ < box[2]) | (ys_ > box[3])).sum()
    check(f"the joints stay on the 2 m character, none spread over the view ({int(out)} of {len(xs_)} px outside "
          f"its outline)", len(xs_) and out < 0.01 * len(xs_))


run()
