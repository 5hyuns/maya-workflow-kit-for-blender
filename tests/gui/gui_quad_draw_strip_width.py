"""Quad Draw Tab + middle-drag in empty space: the strip width follows the drag (right = wider, left = narrower), a
preview strip of that width shows while dragging, and the next Tab + LMB strip uses the new width (the Tool Settings
Quad Strip Width)."""
import os, sys
from importlib import import_module
import bpy, bmesh
import numpy as np
from mathutils import Quaternion
from bpy_extras import view3d_utils
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, setup, step, run, view3d, win, ev, check, screenshot  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS")
C = {"n": 0}


def mod(n):
    return import_module(MODULE + '.operators.' + n)


def settings():
    return mod('poly_draw').settings()


def scale():
    return bpy.context.preferences.system.ui_scale


def override():
    a, r = view3d()
    return bpy.context.temp_override(window=win(), area=a, region=r)


def bm():
    return bmesh.from_edit_mesh(bpy.context.edit_object.data)


def centre():
    a, r = view3d()
    return r.x + r.width // 2, r.y + r.height // 3


def grab(tag):
    C["n"] += 1
    path = os.path.join(SHOTS or bpy.app.tempdir, f"gui_quad_draw_strip_width_{C['n']}_{tag}.png")
    screenshot(path)
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    a = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(a)
    bpy.data.images.remove(img)
    return a.reshape(h, w, 4)[:, :, :3]


def green_span(img):
    """x extent (pixels) of the preview strip's green lines in a box above the press point."""
    x, y = centre()
    sub = img[y - 4:y + 260, x - 160:x + 160]
    mask = (sub[:, :, 1] > 0.8) & (sub[:, :, 0] < 0.5) & (sub[:, :, 2] > 0.4) & (sub[:, :, 2] < 0.85)
    cols = np.nonzero(mask.any(axis=0))[0]
    if not len(cols):
        return 0, 0
    return int(cols.max() - cols.min()), int(mask.sum())


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


@step
def prepare():
    setup()
    with override():
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)
        bpy.ops.mesh.primitive_plane_add(size=20)
        mod('live').set_objects(bpy.context.scene, [bpy.context.object])
        bpy.ops.allset.quad_draw_start()
        a, r = view3d()
        rv = a.spaces.active.region_3d
        rv.view_rotation = Quaternion((1, 0, 0, 0))
        rv.view_perspective = 'ORTHO'
        rv.view_location = (0, 0, 0)
        rv.view_distance = 12
    settings().qd_strip_width = 20
    C['verts'] = len(bm().verts)


@step
def hover():
    x, y = centre()
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)


@step
def baseline():
    C['green0'] = green_span(grab("before"))[1]
    ev('TAB', 'PRESS')


@step
def mmb_press():
    ev('MIDDLEMOUSE', 'PRESS')


@step
def drag_right():
    pv = mod('quad_draw').STATE['preview']
    check('Tab + MMB in empty space starts the strip width drag with a preview strip',
          pv is not None and pv[0] == 'WIDTH')
    x, y = centre()
    ev('MOUSEMOVE', 'NOTHING', x=x + 40, y=y)
    redraw()


@step
def wait_right():
    redraw()


@step
def wider():
    C['wide'] = settings().qd_strip_width
    check('dragging right widens the strip', C['wide'] == round(20 + 40 / scale()))
    span, count = green_span(grab("wide"))
    C['span_wide'] = span
    check('the preview strip is drawn at the new width',
          count > C['green0'] + 50 and abs(span - C['wide'] * scale()) <= 6)
    x, y = centre()
    ev('MOUSEMOVE', 'NOTHING', x=x + 10, y=y)
    redraw()


@step
def wait_left():
    redraw()


@step
def narrower():
    C['narrow'] = settings().qd_strip_width
    check('dragging left narrows the strip', C['narrow'] < C['wide'] and C['narrow'] == round(20 + 10 / scale()))
    span, _count = green_span(grab("narrow"))
    check('the preview strip follows the narrower width', span < C['span_wide'] - 10)
    ev('MIDDLEMOUSE', 'RELEASE')


@step
def released():
    check('releasing keeps the width, ends the preview and makes no geometry',
          settings().qd_strip_width == C['narrow'] and mod('quad_draw').STATE['preview'] is None
          and len(bm().verts) == C['verts'])
    ev('TAB', 'RELEASE')


@step
def strip_tab():
    settings().qd_auto_weld = False
    x, y = centre()
    C['strip'] = (x - 120, y)
    ev('MOUSEMOVE', 'NOTHING', x=x - 120, y=y)
    ev('TAB', 'PRESS')


@step
def strip_press():
    ev('LEFTMOUSE', 'PRESS')


for d in (30, 60, 90, 120):
    @step
    def strip_move(d=d):
        x, y = C['strip']
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y + d)


@step
def strip_release():
    ev('LEFTMOUSE', 'RELEASE')
    ev('TAB', 'RELEASE')


@step
def strip_result():
    ob = bpy.context.edit_object
    a, r = view3d()
    rv = a.spaces.active.region_3d
    pts = [view3d_utils.location_3d_to_region_2d(r, rv, ob.matrix_world @ v.co) for v in bm().verts]
    xs = [p.x for p in pts if p is not None]
    width = (max(xs) - min(xs)) if xs else 0
    check('the next Tab + LMB strip uses the new width',
          len(bm().faces) >= 2 and abs(width - C['narrow'] * scale()) <= 1.5)


run()
