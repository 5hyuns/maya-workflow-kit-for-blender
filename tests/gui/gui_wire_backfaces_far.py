"""Selected wire seen from far away (#243, #229): in the Maya layout (cm scene) a selected cube's hidden back edges
stay hidden behind its faces whatever the zoom — near, medium and far views of cubes of size 1, 20 and 200, in
perspective. A hidden edge counts as shown when the lead green is drawn at its middle (away from any visible edge)."""

import os
import sys

import bpy
import numpy as np
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, load_maya_layout, run, screenshot, setup, step, view3d, win  # noqa: E402
from importlib import import_module  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
LEAD = np.array([0x43, 0xff, 0xa3]) / 255.0
C = {"cases": [], "i": 0, "bad": []}
# (cube size in Maya units, cube size on screen in px)
CASES = [(s, px) for s in (1.0, 20.0, 200.0) for px in (400, 120, 40)]


def shot(name):
    path = os.path.join(SHOTS or bpy.app.tempdir, f"gui_wire_far_{name}.png")
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


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


def seg_dist(p, a, b):
    ab = b - a
    t = max(0.0, min(1.0, (p - a).dot(ab) / max(ab.length_squared, 1e-9)))
    return (a + ab * t - p).length


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_scene():
    bpy.ops.allset.keymap_activate()
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.allset.create(kind='CUBE')
    ob = bpy.context.view_layer.objects.active
    for o in bpy.context.scene.objects:
        o.select_set(o == ob)
    C["ob"] = ob.name
    rv3d = area.spaces.active.region_3d
    rv3d.view_perspective = 'PERSP'
    redraw()


def _place(size, on_screen):
    unit = import_module(MODULE + ".operators.units").maya_unit()
    ob = bpy.data.objects[C["ob"]]
    ob.scale = (size,) * 3
    ob.location = (0.0, 0.0, 0.0)
    area, region = view3d()
    space = area.spaces.active
    rv3d = space.region_3d
    rv3d.view_location = (0.0, 0.0, 0.0)
    # the cube's diagonal on screen ~ on_screen px: f_px = width * lens / 72 (Blender viewport lens)
    f_px = region.width * space.lens / 72.0
    rv3d.view_distance = f_px * size * unit * 1.7 / on_screen
    redraw()


def _check(tag):
    ob = bpy.data.objects[C["ob"]]
    area, _region = view3d()
    rv3d = area.spaces.active.region_3d
    eye = rv3d.view_matrix.inverted().translation
    mw = ob.matrix_world
    verts = [mw @ v.co for v in ob.data.vertices]
    faces = ob.data.polygons
    front = {i for i, f in enumerate(faces) if (mw.to_3x3() @ f.normal).dot(eye - mw @ f.center) > 0}
    edges = list(ob.data.edges)
    face_of = {}
    for i, f in enumerate(faces):
        for k in f.edge_keys:
            face_of.setdefault(k, []).append(i)
    hidden = [e for e in edges if not any(fi in front for fi in face_of[e.key])]
    shown = [e for e in edges if e not in hidden]
    px = shot(tag)
    bad = 0
    tested = 0
    for e in hidden:
        a, b = (to_window(verts[i]) for i in e.vertices)
        if a is None or b is None:
            continue
        mid = (a + b) / 2
        segs = [(to_window(verts[s.vertices[0]]), to_window(verts[s.vertices[1]])) for s in shown]
        if any(seg_dist(mid, p, q) < 6 for p, q in segs):
            continue
        tested += 1
        x, y = int(round(mid.x)), int(round(mid.y))
        patch = px[y - 1:y + 2, x - 1:x + 2]
        if (np.abs(patch - LEAD).max(axis=-1) < 0.12).any():
            bad += 1
    return tested, bad


for _i, (_size, _px) in enumerate(CASES):
    def _pl(size=_size, on=_px):
        _place(size, on)

    def _ck(size=_size, on=_px):
        tested, bad = _check(f"{size:g}_{on}")
        C["cases"].append((size, on, tested, bad))
        print("CASE", size, on, tested, bad)
    _pl.__name__, _ck.__name__ = f"s_place_{_i}", f"s_check_{_i}"
    step(_pl)
    step(_ck)


@step
def s_report():
    for size, on, tested, bad in C["cases"]:
        check(f"cube {size:g} units, ~{on} px on screen: hidden back edges stay hidden ({bad} / {tested} shown)",
              tested > 0 and bad == 0)


run()
