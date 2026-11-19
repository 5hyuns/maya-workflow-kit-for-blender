"""#389 in a real UI: Quad Draw on a live sphere, the retopology mesh wraps the whole sphere. A Shift+drag relax
stroke on the side facing the camera leaves the far side alone (its vertices were pulled through to the front), and
the relaxed vertices stay on the live surface where they were, also near the sphere's outline seen from the camera.
Screenshots with ALLSET_GUI_SHOTS (or --shots)."""

import math
import os
import sys
from importlib import import_module

import bmesh
import bpy
import numpy as np
from bpy_extras import view3d_utils
from mathutils import Euler, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, screenshot, setup, step, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}
R = 3.0


def shot(name):
    if SHOTS:
        screenshot(os.path.join(SHOTS, name))


def mod(name):
    return import_module(MODULE + ".operators." + name)


def override():
    a, r = view3d()
    return bpy.context.temp_override(window=win(), area=a, region=r)


def co():
    ob = bpy.context.edit_object
    return np.asarray([v.co[:] for v in bmesh.from_edit_mesh(ob.data).verts])


def screen(p):
    a, r = view3d()
    v = view3d_utils.location_3d_to_region_2d(r, a.spaces.active.region_3d, Vector(p))
    return r.x + round(v.x), r.y + round(v.y)


def stroke(at, dx=30, steps=6):
    """Shift+LMB press at ``at`` (world), drag ``dx`` px right in ``steps`` moves, release."""
    x, y = screen(at)
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y, shift=True)
    ev('LEFTMOUSE', 'PRESS', x=x, y=y, shift=True)
    for i in range(1, steps + 1):
        ev('MOUSEMOVE', 'NOTHING', x=x + round(dx * i / steps), y=y, shift=True)
    ev('LEFTMOUSE', 'RELEASE', x=x + dx, y=y, shift=True)


def restore():
    ob = bpy.context.edit_object
    bm = bmesh.from_edit_mesh(ob.data)
    for v, p in zip(bm.verts, C["original"]):
        v.co = p
    bmesh.update_edit_mesh(ob.data)
    mod('preselect').invalidate()


@step
def prepare():
    setup()
    with override():
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=R, segments=96, ring_count=48)
        mod('live').set_objects(bpy.context.scene, [bpy.context.object])
        bpy.ops.mesh.primitive_uv_sphere_add(radius=R, segments=32, ring_count=16)
        ob = bpy.context.object
        bpy.ops.allset.quad_draw_start()
        state = bpy.context.scene.allset_symmetry
        state.on = False
        mod('symmetry').apply(state, [ob])
        bpy.context.scene.allset_soft_select = False
        bm = bmesh.from_edit_mesh(ob.data)
        for seq in (bm.verts, bm.edges, bm.faces):
            for el in seq:
                el.select = False
        bmesh.update_edit_mesh(ob.data)
        a, _r = view3d()
        rv = a.spaces.active.region_3d
        rv.view_perspective = 'PERSP'
        rv.view_rotation = Euler((math.radians(90), 0, 0)).to_quaternion()     # look along +Y
        rv.view_location = (0, 0, 0)
        rv.view_distance = 14.0
        C["original"] = co()
        C["spacing"] = 2 * math.pi * R / 32
        bpy.ops.ed.undo_push(message='Relax far side fixture')


@step
def front_stroke():
    shot("gui_issue389_before.png")
    stroke((0.0, -R, 0.0))                 # the middle of the side facing the camera


step(lambda: None)


@step
def front_result():
    now, before = co(), C["original"]
    moved = np.linalg.norm(now - before, axis=1)
    far = before[:, 1] > 0.5
    check(f"the stroke relaxed vertices on the side facing the camera ({int(np.count_nonzero(moved > 1e-6))})",
          np.count_nonzero(moved[~far] > 1e-6) > 0)
    check(f"the far side's vertices stay where they were (max move {moved[far].max():.4f}, "
          f"{int(np.count_nonzero(moved[far] > 1e-6))} moved)", moved[far].max() < 1e-6)
    radius = np.linalg.norm(now, axis=1)
    check(f"every vertex is still on the live surface (radius {radius.min():.4f} .. {radius.max():.4f})",
          np.abs(radius - R).max() < 0.02)
    shot("gui_issue389_front.png")
    restore()


@step
def outline_stroke():
    a = math.radians(70.0)                 # 70 degrees round from the camera: near the sphere's outline
    C["outline_at"] = (R * math.sin(a), -R * math.cos(a), 0.0)
    stroke(C["outline_at"], dx=6, steps=3)


step(lambda: None)


@step
def outline_result():
    now, before = co(), C["original"]
    moved = np.linalg.norm(now - before, axis=1)
    worst = float(moved.max())
    toward = float(np.max(-(now - before)[:, 1]))            # how far vertices came toward the camera (-Y)
    check(f"near the outline the relaxed vertices stay where they were on the surface (largest move "
          f"{worst:.3f}, {worst / C['spacing']:.2f} of the edge length; toward the camera {toward:.3f})",
          worst < 0.25 * C["spacing"])
    radius = np.linalg.norm(now, axis=1)
    check(f"... and on the live surface (radius {radius.min():.4f} .. {radius.max():.4f})",
          np.abs(radius - R).max() < 0.02)
    shot("gui_issue389_outline.png")
    with override():
        bpy.ops.allset.quad_draw_exit()


run()
