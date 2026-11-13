"""In a real UI: about 600 highlighted objects (500 copies of one cube standing on a ground plane, meshes of their own,
thin plates and cards, subdivided cubes, a lead with 30 unselected children among white wires, lattices and curves)
draw the same picture with the instanced selection wire as drawing each object by itself: perspective views from
above and grazing the ground, top and front orthographic views, wireframe shading with and without X-ray. The copies
of the cube share one batch, and 3,000 selected objects draw the wire in a fraction of the one-by-one time without
setting off Python's garbage collector."""

import gc
import math
import os
import random
import sys
import time
from importlib import import_module

import bpy
import numpy as np
from mathutils import Euler

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, load_maya_layout, run, screenshot, setup, step, view3d, win  # noqa: E402

GUI_TIMEOUT = 600
SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
LEAD = np.array([0x43, 0xff, 0xa3]) / 255.0
C = {"views": [], "many": 0}
BOX = [(x, y, z) for x in (-.5, .5) for y in (-.5, .5) for z in (-.5, .5)]
FACES = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]


def sw():
    return import_module(MODULE + ".ui.selection_wire")


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


def shot(name):
    path = os.path.join(SHOTS or bpy.app.tempdir, f"gui_wire_instanced_{name}.png")
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=2)
    screenshot(path)
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    px = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(px)
    bpy.data.images.remove(img)
    _area, region = view3d()
    return px.reshape(h, w, 4)[region.y:region.y + region.height, region.x:region.x + region.width, :3].copy()


def _mesh(name, verts, faces):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    return me


def _link(ob):
    bpy.context.scene.collection.objects.link(ob)
    return ob


@step
def s_setup():
    setup()
    load_maya_layout()
    # a still picture: no viewport anti-aliasing passes adding up between redraws, no display dither noise
    bpy.context.preferences.system.viewport_aa = 'OFF'
    bpy.context.scene.render.dither_intensity = 0.0


@step
def s_scene():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    rng = random.Random(3)
    box = _mesh("box", BOX, FACES)
    # No two solid faces meet or overlap (Blender itself may draw coinciding faces in either order from one redraw to
    # the next): the ground lies below the cubes, the cubes stand apart at heights of their own. Every wire still lies
    # on its own object's faces, where the depth offset decides each pixel.
    ground = _link(bpy.data.objects.new("ground", _mesh("ground", [(-1, -1, 0), (1, -1, 0), (1, 1, 0), (-1, 1, 0)],
                                                       [(0, 1, 2, 3)])))
    ground.scale = (40, 40, 1)
    ground.location.z = -0.25
    picked = []
    for i in range(500):
        if i == 250:      # the lead in the middle of the drawing order, its children among white wires
            lead = _link(bpy.data.objects.new("lead", box))
            lead.location = (26.0, -6.0, 0.5)
            picked.append(lead)
            for j in range(30):
                kid = _link(bpy.data.objects.new(f"kid{j:02d}", box))
                kid.parent = lead
                kid.location = (1.6 * (j % 6 - 2.5), 1.6 * (j // 6 + 1), 0.011 * j)
                kid.rotation_euler = (0, 0, j * 0.3)
        ob = _link(bpy.data.objects.new(f"c{i:03d}", box))
        ob.location = ((i % 25) * 1.6 - 20, (i // 25) * 1.6 - 16, 0.5 + 0.013 * (i % 9))
        if i % 3 == 0:
            ob.rotation_euler = Euler((0, 0, rng.uniform(0, 3)))
        if i % 17 == 0:
            ob.rotation_euler = Euler((rng.uniform(-0.5, 0.5), rng.uniform(-0.5, 0.5), rng.uniform(0, 3)))
            ob.location.z += 0.2
        picked.append(ob)
    for i in range(60):           # meshes of their own: grids, thin plates, flat cards
        n = 2 + i % 4
        verts = [(x / n - .5, y / n - .5, 0.0) for y in range(n + 1) for x in range(n + 1)]
        faces = [(y * (n + 1) + x, y * (n + 1) + x + 1, (y + 1) * (n + 1) + x + 1, (y + 1) * (n + 1) + x)
                 for y in range(n) for x in range(n)]
        ob = _link(bpy.data.objects.new(f"g{i:02d}", _mesh(f"g{i:02d}", verts, faces)))
        ob.location = ((i % 15) * 2.6 - 19, 18 + (i // 15) * 2.6, 1.2)
        ob.rotation_euler = Euler((rng.uniform(-1.2, 1.2), rng.uniform(-1.2, 1.2), rng.uniform(0, 3)))
        ob.scale = (rng.uniform(0.5, 1.8), rng.uniform(0.5, 1.8), rng.choice((1.0, 0.0)))
        picked.append(ob)
    for i in range(10):           # their own evaluated mesh each
        ob = _link(bpy.data.objects.new(f"s{i}", _mesh(f"s{i}", BOX, FACES)))
        ob.modifiers.new("sub", 'SUBSURF').levels = 1
        ob.location = (i * 1.6 - 7, -19, 0.5)
        picked.append(ob)
    for i in range(2):
        lat = _link(bpy.data.objects.new(f"lat{i}", bpy.data.lattices.new(f"lat{i}")))
        lat.location = (-17 + i * 3, 15, 1.0)
        picked.append(lat)
    for i in range(3):
        crv = bpy.data.curves.new(f"crv{i}", 'CURVE')
        spline = crv.splines.new('POLY')
        spline.points.add(3)
        for k, p in enumerate(spline.points):
            p.co = (k, (k % 2) * 0.7, 0.2, 1)
        ob = _link(bpy.data.objects.new(f"crv{i}", crv))
        ob.location = (10 + i * 2, -17, 0.0)
        picked.append(ob)
    bpy.context.view_layer.update()
    for ob in bpy.context.view_layer.objects:
        ob.select_set(ob in picked)
    bpy.context.view_layer.objects.active = bpy.data.objects["lead"]
    C["cubes"] = [ob.name for ob in picked if ob.data == box]
    area, region = view3d()
    space = area.spaces.active
    space.overlay.show_overlays = True
    real = sw()._draw_many

    def counted(*args, **kw):
        C["many"] += 1
        return real(*args, **kw)
    sw()._draw_many = counted
    C["real_many"] = real
    redraw()


# (name, perspective, view rotation (euler), distance, shading, x-ray)
VIEWS = [("persp_above", 'PERSP', (0.9, 0, 0.6), 60.0, 'SOLID', False),
         ("persp_grazing", 'PERSP', (1.45, 0, -0.4), 26.0, 'SOLID', False),
         ("ortho_top", 'ORTHO', (0, 0, 0), 40.0, 'SOLID', False),
         ("ortho_front", 'ORTHO', (math.pi / 2, 0, 0), 30.0, 'SOLID', False),
         ("wire_xray", 'PERSP', (1.0, 0, 2.2), 55.0, 'WIREFRAME', True),
         ("wire_solid", 'PERSP', (1.1, 0, -2.4), 50.0, 'WIREFRAME', False)]


def _set_view(persp, rot, dist, shading, xray):
    area, _region = view3d()
    space = area.spaces.active
    rv3d = space.region_3d
    rv3d.view_perspective = persp
    rv3d.view_rotation = Euler(rot).to_quaternion()
    rv3d.view_location = (4.0, 0.0, 0.5)
    rv3d.view_distance = dist
    space.shading.type = shading
    space.shading.show_xray_wireframe = xray


for _name, _persp, _rot, _dist, _shading, _xray in VIEWS:
    def _old(name=_name, persp=_persp, rot=_rot, dist=_dist, shading=_shading, xray=_xray):
        _set_view(persp, rot, dist, shading, xray)
        C["default_from"] = C.get("default_from", sw().INSTANCE_FROM)
        sw().INSTANCE_FROM = 10 ** 9          # each object by itself
        redraw()

    def _shot_old(name=_name):
        C["many"] = 0
        C["old"] = shot(name + "_one_by_one")
        C["still"] = int((np.abs(shot(name + "_one_by_one_again") - C["old"]).max(axis=-1) > 0).sum())
        C["old_many"] = C["many"]
        sw().INSTANCE_FROM = C["default_from"]
        redraw()

    def _shot_new(name=_name):
        C["many"] = 0
        new = shot(name + "_instanced")
        old = C["old"]
        diff = int((np.abs(new - old).max(axis=-1) > 0).sum())
        lead = int((np.abs(new - LEAD).max(axis=-1) < 0.02).sum())
        white = int((new.min(axis=-1) > 0.98).sum())
        C["views"].append((name, diff, lead, white, C["old_many"], C["many"], C["still"]))
        print("VIEW", name, "diff", diff, "lead px", lead, "white px", white, "many", C["old_many"], C["many"],
              "still", C["still"])
    _old.__name__, _shot_old.__name__, _shot_new.__name__ = f"s_{_name}", f"s_{_name}_old", f"s_{_name}_new"
    step(_old)
    step(_shot_old)
    step(_shot_new)


@step
def s_nudged():
    """Control: the same view with every matrix one unit in the last place larger shows up in the picture, so a
    picture equal to one by one means equal positions, not a blind comparison."""
    _set_view('PERSP', (1.45, 0, -0.4), 22.0, 'SOLID', False)
    redraw()
    base = shot("control_instanced")
    s = sw()
    real = s.projected_matrices
    s.projected_matrices = lambda *a: np.nextafter(real(*a), np.float32(np.inf))
    try:
        s._last_many.clear()                # computed again, not the matrices kept from the last redraw
        nudged = shot("control_nudged")
    finally:
        s.projected_matrices = real
    s._last_many.clear()
    again = shot("control_instanced_again")
    moved = int((np.abs(nudged - base).max(axis=-1) > 0).sum())
    same = int((np.abs(again - base).max(axis=-1) > 0).sum())
    print("CONTROL nudged", moved, "again", same)
    check(f"control: matrices one float step off change {moved} pixels; drawing again changes {same}",
          moved > 0 and same == 0)


@step
def s_moved():
    """Some objects move in a still view (a playback frame): only their rows are computed again, and the picture is
    still the one drawing each object by itself gives."""
    shot("moved_before")                       # keeps this view's matrices and offsets
    s = sw()
    real, rows = s._biases_rows, []
    s._biases_rows = lambda worlds, *a: rows.append(len(worlds)) or real(worlds, *a)
    C["rows"], C["real_rows"] = rows, real
    for k, name in enumerate(C["cubes"][::40]):
        ob = bpy.data.objects[name]
        ob.location.z += 0.3 + 0.01 * k
        ob.rotation_euler.z += 0.2
    bpy.context.view_layer.update()
    redraw()


@step
def s_moved_shots():
    s = sw()
    try:
        new = shot("moved_instanced")
    finally:
        s._biases_rows = C["real_rows"]
    rows = C["rows"]
    s.INSTANCE_FROM = 10 ** 9
    try:
        old = shot("moved_one_by_one")
    finally:
        s.INSTANCE_FROM = C["default_from"]
    diff = int((np.abs(new - old).max(axis=-1) > 0).sum())
    moved = len(C["cubes"][::40])
    check(f"{moved} objects moved: {rows} rows computed again, the same pixels as one by one ({diff} differ)",
          moved in rows and len(bpy.context.selected_objects) not in rows and diff == 0)


@step
def s_report_views():
    import gpu
    print("GPU", gpu.platform.backend_type_get(), gpu.platform.renderer_get(), gpu.platform.version_get())
    for name, diff, lead, white, old_many, many, still in C["views"]:
        check(f"{name}: the instanced wire draws the same pixels as one by one ({diff} differ, {still} between two "
              f"pictures one by one; {lead} lead, {white} white pixels)", diff == 0 and still == 0 and white > 300)
        check(f"{name}: one by one, then instanced ({old_many} / {many} instanced draws)", old_many == 0 and many >= 1)
    leads = [lead for _name, _diff, lead, *_rest in C["views"]]
    check(f"the lead wire is in the pictures ({leads} lead pixels)", sum(lead > 100 for lead in leads) >= 4)
    batches = {id(sw()._batches[bpy.data.objects[n].session_uid][0]) for n in C["cubes"]
               if bpy.data.objects[n].session_uid in sw()._batches}
    check(f"{len(C['cubes'])} copies of one cube share one batch ({len(batches)})", len(batches) == 1)
    sw()._draw_many = C["real_many"]


def wire_ms(n=12, turn=0.0):
    """The selection wire's own ms a redraw of the view, over ``n`` redraws (``turn``: the view turns by this many
    radians before each, an orbit)."""
    area, region = view3d()
    s = sw()
    rv3d = area.spaces.active.region_3d
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.wm.redraw_timer(type='DRAW', iterations=2)
        s._times.clear()
        if turn:
            for _ in range(n):
                rv3d.view_rotation = Euler((0.0, 0.0, turn)).to_quaternion() @ rv3d.view_rotation
                bpy.ops.wm.redraw_timer(type='DRAW', iterations=1)
        else:
            bpy.ops.wm.redraw_timer(type='DRAW', iterations=n)
    return s.frame_ms()


@step
def s_many():
    box = bpy.data.meshes["box"]
    for i in range(2400):
        ob = _link(bpy.data.objects.new(f"m{i:04d}", box))
        ob.location = ((i % 60) * 0.6 - 18, (i // 60) * 0.6 - 30, 0.5)
    bpy.context.view_layer.update()
    for ob in bpy.context.view_layer.objects:
        ob.select_set(ob.name != "ground")
    _set_view('PERSP', (0.9, 0, 0.6), 60.0, 'SOLID', False)
    redraw()


@step
def s_many_time():
    s = sw()
    n = len(bpy.context.selected_objects)
    s.INSTANCE_FROM = 10 ** 9
    one = wire_ms(turn=0.01)
    s.INSTANCE_FROM = C["default_from"]
    inst = wire_ms(turn=0.01)
    stats = gc.get_stats()
    before = [g["collections"] for g in stats]
    t = time.perf_counter()
    inst2 = wire_ms(20)
    after = [g["collections"] for g in gc.get_stats()]
    runs = [a - b for a, b in zip(after, before)]
    print("GUI wire instanced", n, "one by one", one, "instanced", inst, inst2, "gc runs", runs,
          f"{time.perf_counter() - t:.2f}s")
    check(f"{n} selected objects, the view turning: the wire takes {inst:.1f} ms a redraw instanced, {one:.1f} ms one "
          f"by one; {inst2:.1f} ms in a still view", inst <= one * 0.75 and inst2 <= one * 0.4)
    check(f"22 redraws with {n} selected objects run the garbage collector {runs[0]} times (gen 0), "
          f"{runs[2]} full", runs[0] <= 6 and runs[2] == 0)


run()
