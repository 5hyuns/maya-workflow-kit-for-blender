"""Graph Editor pan with many keys and the kit's tangents (Maya Alt+MMB): while the drag runs the keys are read once
and the kit's drawing of the drag's first frame is moved with the view; what is on screen during the drag is the same,
pixel for pixel, as a fresh draw at the same view after the release."""

import math
import os
import sys
import tempfile
from importlib import import_module

import bpy
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, step, setup, screenshot, view3d, win, load_maya_layout  # noqa: E402

GUI_TIMEOUT = 300
C = {"shots": {}}
TMP = tempfile.mkdtemp(prefix="allset_drag_draw_")


def mod(name):
    return import_module(MODULE + name)


def region():
    return next(r for r in C["area"].regions if r.type == 'WINDOW')


def shot(tag):
    path = os.path.join(TMP, tag + ".png")
    screenshot(path)
    C["shots"][tag] = path


def crop(tag):
    """RGBA pixels of the Graph Editor's curve view in a window screenshot."""
    img = bpy.data.images.load(C["shots"][tag])
    w, h = img.size
    px = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    bpy.data.images.remove(img)
    r = region()
    return px.reshape(h, w, 4)[r.y:r.y + r.height, r.x:r.x + r.width]


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_scene():
    bpy.ops.allset.keymap_activate()
    area, _reg = view3d()
    ob = bpy.data.objects.new("pCube1", bpy.data.meshes.new("pCubeShape1"))
    bpy.context.scene.collection.objects.link(ob)
    for f in range(24):
        ob.location = (math.sin(f * 0.4), math.cos(f * 0.3) * 2, f * 0.1)
        ob.rotation_euler = (0.1 * f, -0.05 * f, math.sin(f) * 0.5)
        ob.scale = (1.0, 1.0 + 0.02 * f, 1.0)
        for path in ("location", "rotation_euler", "scale"):
            ob.keyframe_insert(path, frame=1 + 3 * f)
    for o in bpy.context.scene.objects:
        o.select_set(o == ob)
    bpy.context.view_layer.objects.active = ob
    p = mod(".preferences").get()
    p.graph_auto_frame = False
    p.graph_auto_frame_time = False
    C["area"] = area
    area.ui_type = 'FCURVES'
    for fc in mod(".compat").id_fcurves(ob):
        for i, kp in enumerate(fc.keyframe_points):
            kp.select_control_point = i % 3 == 0
            kp.select_right_handle = i % 4 == 0


@step
def s_frame():
    a = C["area"]
    a.spaces.active.use_only_selected_keyframe_handles = False
    with bpy.context.temp_override(window=win(), area=a, region=region()):
        bpy.ops.graph.view_all()
    r = region()
    C["xy"] = (r.x + r.width // 2, r.y + r.height // 2)
    ev('MOUSEMOVE', 'NOTHING', x=C["xy"][0], y=C["xy"][1])


for _ in range(3):
    step(lambda: None)


@step
def s_count_reads():
    gk = mod(".ui.graph_keys_draw")
    real = gk.Keys
    C["reads"], C["real_keys"] = [0], real

    class Counted(real):
        def __init__(self, *a, **kw):
            C["reads"][0] += 1
            super().__init__(*a, **kw)
    gk.Keys = Counted
    check("the kit draws this Graph Editor's tangents", mod(".ui.graph_handles").owns(C["area"].spaces.active))
    ev('LEFT_ALT', 'PRESS')
    ev('MIDDLEMOUSE', 'PRESS', alt=True, x=C["xy"][0], y=C["xy"][1])


for _i in range(1, 9):
    @step
    def s_move(i=_i):
        if i == 2:
            C["reads_at_start"] = C["reads"][0]
            C["view0"] = mod(".ui.graph_keys_draw").view_map(region())
        ev('MOUSEMOVE', 'NOTHING', alt=True, x=C["xy"][0] - 7 * i, y=C["xy"][1] + 5 * i)
        C["area"].tag_redraw()


step(lambda: None)


@step
def s_drag_shot():
    modal = [op.bl_idname for op in win().modal_operators]
    C["modal"] = modal
    shot("drag")


@step
def s_release():
    gk = mod(".ui.graph_keys_draw")
    C["reads_drag"] = C["reads"][0] - C["reads_at_start"]
    C["view1"] = gk.view_map(region())
    ev('MIDDLEMOUSE', 'RELEASE', alt=True)
    ev('LEFT_ALT', 'RELEASE')
    gk.Keys = C["real_keys"]


step(lambda: None)


@step
def s_after_shot():
    C["area"].tag_redraw()


step(lambda: None)


@step
def s_after():
    shot("after")
    v0, v1 = C["view0"], C["view1"]
    check(f"the drag panned the view ({v0[0]:.2f} -> {v1[0]:.2f}) at the same zoom",
          abs(v0[0] - v1[0]) > 1e-3 and abs(v0[2] - v1[2]) <= 1e-6 * abs(v0[2]))
    check(f"a view drag ran ({C['modal']})", any(m in mod(".ui.graph_keys_draw").NAV_OPS for m in C["modal"]))
    check(f"the keys were not read again while the drag ran ({C['reads_drag']} reads over 6 moves)",
          C["reads_drag"] <= 1)
    a, b = crop("drag"), crop("after")
    differ = int((np.abs(a - b).max(axis=2) > 0).sum())
    check(f"the drawing moved with the drag is the fresh drawing, pixel for pixel ({differ} px differ)", differ == 0)


run()
