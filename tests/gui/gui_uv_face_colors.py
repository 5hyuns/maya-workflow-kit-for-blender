"""UV Editor Shaded in a real UI (#246): a plane split into two faces, one with its UVs mirrored (clockwise) -> 5 in
the UV Editor: the flipped face is drawn red, the other blue; 4 = Wireframe: no colour."""

import os
import sys

import bmesh
import bpy
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, ev, run, screenshot, setup, step, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def area():
    return C["area"]


def region():
    return next(r for r in area().regions if r.type == 'WINDOW')


def shot(name):
    path = os.path.join(SHOTS or bpy.app.tempdir, f"gui_uv_face_colors_{name}.png")
    screenshot(path)
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    px = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(px)
    bpy.data.images.remove(img)
    return px.reshape(h, w, 4)[..., :3]


def colour_at(px, uv):
    r = region()
    x, y = r.view2d.view_to_region(*uv, clip=False)
    x, y = int(r.x + x), int(r.y + y)
    return px[y - 2:y + 3, x - 2:x + 3].reshape(-1, 3).mean(axis=0)


@step
def s_setup():
    setup()
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    me = bpy.data.meshes.new("uvplane")
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new()
    vs = [bm.verts.new(co) for co in ((0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0), (2, 0, 0), (2, 1, 0))]
    a = bm.faces.new((vs[0], vs[1], vs[2], vs[3]))
    b = bm.faces.new((vs[1], vs[4], vs[5], vs[2]))
    for f, corners in ((a, ((0.1, 0.1), (0.45, 0.1), (0.45, 0.9), (0.1, 0.9))),       # counter-clockwise
                       (b, ((0.55, 0.1), (0.55, 0.9), (0.9, 0.9), (0.9, 0.1)))):     # clockwise = flipped
        for loop, co in zip(f.loops, corners):
            loop[uv].uv = co
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("uvplane", me)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    big = max(win().screen.areas, key=lambda a: a.width * a.height)
    C["area"] = big
    with bpy.context.temp_override(window=win(), area=big):
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
    big.ui_type = 'UV'
    bpy.context.scene.tool_settings.use_uv_select_sync = True


@step
def s_frame():
    with bpy.context.temp_override(window=win(), area=area(), region=region()):
        bpy.ops.image.view_all(fit_view=True)
    area().tag_redraw()


@step
def s_shaded():
    r = region()
    ev('MOUSEMOVE', 'NOTHING', x=r.x + r.width // 2, y=r.y + r.height // 2)
    ev('FIVE', 'PRESS')
    ev('FIVE', 'RELEASE')


@step
def s_wait():
    area().tag_redraw()


@step
def s_check_shaded():
    px = shot("shaded")
    front, flipped = colour_at(px, (0.28, 0.5)), colour_at(px, (0.72, 0.5))
    check(f"5 = Shaded: colours on ({bpy.context.window_manager.allset_uv_face_colors})",
          bpy.context.window_manager.allset_uv_face_colors)
    check(f"the flipped face is red ({flipped.round(2)})", flipped[0] > flipped[2] + 0.15)
    check(f"the front-facing face is blue ({front.round(2)})", front[2] > front[0] + 0.15)
    ev('FOUR', 'PRESS')
    ev('FOUR', 'RELEASE')


@step
def s_wait2():
    area().tag_redraw()


@step
def s_check_wire():
    px = shot("wire")
    flipped = colour_at(px, (0.72, 0.5))
    check(f"4 = Wireframe: no colour on the flipped face ({flipped.round(2)})", abs(flipped[0] - flipped[2]) < 0.1)


run()
