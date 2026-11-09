"""Issue #345: the gates of a view that looks through a camera match the render, like Maya.

The Resolution Gate is Blender's camera frame and is what renders; the Film Gate is the camera's film back
(Horizontal x Vertical Film Aperture), placed on the resolution gate by Fit Resolution Gate. A new camera
(Create > Cameras > Camera) has Maya's 36 x 24 mm film back and Fit Resolution Gate Fill. For each case the test reads
the drawn film gate from the screen (a screenshot with the Film Gate on minus one with it off), projects Blender's
camera frame into the view, and renders a small bright marker: the marker sits at the same place of the resolution
gate in the view and in the render, and the film gate has Maya's size on the resolution gate."""

import os
import sys
import tempfile
from importlib import import_module

import bpy
import numpy as np
from bpy_extras.view3d_utils import location_3d_to_region_2d
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, run, screenshot, setup, step, view3d, win, load_maya_layout  # noqa: E402

C = {}
SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
TMP = tempfile.mkdtemp(prefix="gui345_")
MARK_UV = (0.75, 0.70)          # where the marker is put on Maya's resolution gate
DEPTH = 10.0
PX_TOL = 4.0                    # drawn line positions are whole pixels; the gate's lines are dashed


def maya_gates(hfa, vfa, fit, aspect):
    """Maya: (resolution gate w, h), film gate (w, h) in mm on the film back."""
    film = hfa / vfa
    if fit == 'FILL':
        fit = 'HORIZONTAL' if aspect >= film else 'VERTICAL'
    elif fit == 'OVERSCAN':
        fit = 'VERTICAL' if aspect >= film else 'HORIZONTAL'
    res = (hfa, hfa / aspect) if fit == 'HORIZONTAL' else (vfa * aspect, vfa)
    return res, (hfa, vfa)


# (name, resolution, vertical film aperture, Fit Resolution Gate or None = the new camera's)
CASES = [
    ("HD 1920x1080", (1920, 1080), 24.0, None),
    ("4:3 1440x1080", (1440, 1080), 24.0, None),
    ("portrait 1080x1920", (1080, 1920), 24.0, None),
    ("film back with the render's aspect (36 x 20.25 mm, 1920x1080)", (1920, 1080), 20.25, None),
    ("Fit Resolution Gate Overscan, 1920x1080", (1920, 1080), 24.0, 'OVERSCAN'),
]


def ctx():
    area, region = view3d()
    return dict(window=win(), area=area, region=region, space_data=area.spaces.active)


def frame_rect():
    """Blender's camera frame (the render) in the big view, region pixels: (x0, y0, x1, y1)."""
    area, region = view3d()
    rv3d = area.spaces.active.region_3d
    cam = C["cam"]
    pts = [location_3d_to_region_2d(region, rv3d, cam.matrix_world @ v)
           for v in cam.data.view_frame(scene=bpy.context.scene)]
    return min(p.x for p in pts), min(p.y for p in pts), max(p.x for p in pts), max(p.y for p in pts)


def frame_mm():
    """Size of the render frame on the film back (mm): from Blender's camera frame."""
    cam = C["cam"].data
    pts = cam.view_frame(scene=bpy.context.scene)
    k = cam.lens / abs(pts[0].z)
    return (max(p.x for p in pts) - min(p.x for p in pts)) * k, (max(p.y for p in pts) - min(p.y for p in pts)) * k


def load(path):
    """RGB pixels of an image file as an (h, w, 3) array, bottom row first (window coordinates)."""
    im = bpy.data.images.load(path, check_existing=False)
    w, h = im.size
    pix = np.empty(w * h * 4, dtype=np.float32)
    im.pixels.foreach_get(pix)
    bpy.data.images.remove(im)
    return pix.reshape(h, w, 4)[:, :, :3]


def drawn_film_gate(on_path, off_path):
    """The film gate lines in the big view: pixels that change when the Film Gate is turned on, as a region rect.
    Rows / columns with at least 20 changed pixels are the gate's edges (not a stray pixel); an edge that lies on the
    camera frame's own edge changes few pixels, so the extent along an edge also counts: a horizontal edge row spans
    the gate's width, a vertical edge column its height."""
    _area, region = view3d()
    a, b = load(on_path), load(off_path)
    ys, xs = slice(region.y, region.y + region.height), slice(region.x, region.x + region.width)
    changed = np.abs(a[ys, xs] - b[ys, xs]).sum(axis=2) > 0.45
    edge_rows = np.nonzero(changed.sum(axis=1) >= 20)[0]
    edge_cols = np.nonzero(changed.sum(axis=0) >= 20)[0]
    if not len(edge_rows) and not len(edge_cols):
        return None
    xs_, ys_ = list(edge_cols), list(edge_rows)
    for y in edge_rows:
        on = np.nonzero(changed[y])[0]
        xs_ += [on.min(), on.max()]
    for x in edge_cols:
        on = np.nonzero(changed[:, x])[0]
        ys_ += [on.min(), on.max()]
    return float(min(xs_)), float(min(ys_)), float(max(xs_)), float(max(ys_))


def render_mark():
    """(u, v) of the marker in a small render of the camera (0..1 across the image, from the bottom left)."""
    sc = bpy.context.scene
    r = sc.render
    r.resolution_percentage = 10
    try:
        bpy.ops.render.render(write_still=False)
    finally:
        r.resolution_percentage = 100
    path = os.path.join(TMP, "render.png")
    bpy.data.images["Render Result"].save_render(path)
    pix = load(path)
    h, w = pix.shape[:2]
    ys, xs = np.nonzero(pix[:, :, 0] > 0.5)
    return (float(xs.mean() + 0.5) / w, float(ys.mean() + 0.5) / h) if len(xs) else None


def place_mark(res_mm):
    """Put the marker at MARK_UV of Maya's resolution gate (``res_mm`` on the film back), DEPTH ahead."""
    cam = C["cam"]
    lens = cam.data.lens
    x = (MARK_UV[0] - 0.5) * res_mm[0] * DEPTH / lens
    y = (MARK_UV[1] - 0.5) * res_mm[1] * DEPTH / lens
    C["mark"].location = cam.matrix_world @ Vector((x, y, -DEPTH))


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_scene():
    sc = bpy.context.scene
    r = sc.render
    r.resolution_x, r.resolution_y, r.resolution_percentage = 1920, 1080, 100
    r.pixel_aspect_x = r.pixel_aspect_y = 1.0
    r.engine = 'BLENDER_WORKBENCH'
    sh = sc.display.shading
    sh.light, sh.color_type, sh.single_color = 'FLAT', 'SINGLE', (1.0, 1.0, 1.0)
    sc.world.color = (0.0, 0.0, 0.0)
    for ob in list(sc.objects):
        if ob.type == 'MESH':
            bpy.data.objects.remove(ob)
    with bpy.context.temp_override(**ctx()):
        bpy.ops.allset.create(kind='CAMERA')
    cam = bpy.context.view_layer.objects.active
    C["cam"] = cam
    check(f"Create > Camera: Maya's 36 x 24 mm film back ({cam.data.sensor_width:g} x {cam.data.sensor_height:g})",
          abs(cam.data.sensor_width - 36.0) < 1e-3 and abs(cam.data.sensor_height - 24.0) < 1e-3)
    fit = getattr(cam.data, "allset_film_fit", None)
    check(f"Create > Camera: Fit Resolution Gate Fill like a new Maya camera ({fit})", fit == 'FILL')
    me = bpy.data.meshes.new("mark345")
    mark = bpy.data.objects.new("mark345", me)
    sc.collection.objects.link(mark)
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=0.12)
    bm.to_mesh(me)
    bm.free()
    C["mark"] = mark
    for ob in sc.objects:
        ob.select_set(ob == cam)
    bpy.context.view_layer.objects.active = cam
    with bpy.context.temp_override(**ctx()):
        bpy.ops.allset.panel_look_through()
    cam.data.show_passepartout = False
    cam.data.show_sensor = False
    cam.data.allset_overscan = 2.2          # room around the frame: the whole film gate is in the view
    sc.camera = cam
    C["case"] = 0


def _case():
    return CASES[C["case"]]


@step
def s_case_set():
    name, (rx, ry), vfa, fit = _case()
    sc = bpy.context.scene
    cam = C["cam"]
    sc.render.resolution_x, sc.render.resolution_y = rx, ry
    cam.data.sensor_height = vfa
    if fit is not None:
        if hasattr(cam.data, "allset_film_fit"):
            cam.data.allset_film_fit = fit
        else:
            check(f"{name}: the camera has Fit Resolution Gate (Maya's Fill / Horizontal / Vertical / Overscan)",
                  False)
    cam.data.show_sensor = False
    bpy.context.view_layer.update()
    for a in win().screen.areas:
        a.tag_redraw()


@step
def s_case_off():
    screenshot(os.path.join(TMP, "off.png"))
    with bpy.context.temp_override(**ctx()):
        bpy.ops.allset.panel_set(key='FILM_GATE')          # the panel toolbar's Film Gate button
    for a in win().screen.areas:
        a.tag_redraw()


@step
def s_case_check():
    name, (rx, ry), vfa, fit = _case()
    cam = C["cam"]
    on = os.path.join(TMP, "on.png")
    screenshot(on)
    if SHOTS:
        screenshot(os.path.join(SHOTS, f"gui_issue345_case{C['case']}.png"))
    check(f"{name}: the Film Gate button shows the film gate", cam.data.show_sensor)
    aspect = rx / ry
    res_mm, film_mm = maya_gates(36.0, vfa, fit or 'FILL', aspect)
    got_mm = frame_mm()
    check(f"{name}: the render frame is Maya's resolution gate ({got_mm[0]:.2f} x {got_mm[1]:.2f} mm, Maya "
          f"{res_mm[0]:.2f} x {res_mm[1]:.2f})", abs(got_mm[0] - res_mm[0]) < 0.02 and abs(got_mm[1] - res_mm[1]) < 0.02)
    fx0, fy0, fx1, fy1 = frame_rect()
    fw, fh = fx1 - fx0, fy1 - fy0
    gate = drawn_film_gate(on, os.path.join(TMP, "off.png"))
    want = (film_mm[0] / res_mm[0], film_mm[1] / res_mm[1])
    if gate is None:
        check(f"{name}: a film gate is drawn", False)
    else:
        gx0, gy0, gx1, gy1 = gate
        got = ((gx1 - gx0) / fw, (gy1 - gy0) / fh)
        tol = (PX_TOL * 2 / fw, PX_TOL * 2 / fh)
        check(f"{name}: the drawn film gate is Maya's film gate on the resolution gate ({got[0]:.3f} x {got[1]:.3f} "
              f"resolution gates, Maya {want[0]:.3f} x {want[1]:.3f})",
              abs(got[0] - want[0]) <= tol[0] and abs(got[1] - want[1]) <= tol[1])
        gcx, gcy, fcx, fcy = (gx0 + gx1) / 2, (gy0 + gy1) / 2, (fx0 + fx1) / 2, (fy0 + fy1) / 2
        check(f"{name}: the film gate and the resolution gate share their centre ({gcx - fcx:+.1f}, {gcy - fcy:+.1f} px)",
              abs(gcx - fcx) <= PX_TOL and abs(gcy - fcy) <= PX_TOL)
    place_mark(res_mm)
    C["frame"] = (fx0, fy0, fw, fh)


@step
def s_case_render():
    name = _case()[0]
    area, region = view3d()
    rv3d = area.spaces.active.region_3d
    fx0, fy0, fw, fh = frame_rect()[0], frame_rect()[1], C["frame"][2], C["frame"][3]
    p = location_3d_to_region_2d(region, rv3d, C["mark"].location)
    view_uv = ((p.x - fx0) / fw, (p.y - fy0) / fh)
    got = render_mark()
    check(f"{name}: the marker renders where Maya's resolution gate puts it ({got and tuple(round(v, 3) for v in got)}, "
          f"Maya {MARK_UV})", got is not None and abs(got[0] - MARK_UV[0]) < 0.02 and abs(got[1] - MARK_UV[1]) < 0.02)
    check(f"{name}: the marker sits at the same place of the resolution gate in the view and in the render (view "
          f"{view_uv[0]:.3f}, {view_uv[1]:.3f})",
          got is not None and abs(view_uv[0] - got[0]) < 0.02 and abs(view_uv[1] - got[1]) < 0.02)
    C["case"] += 1
    if C["case"] < len(CASES):
        _steps_again()


def _steps_again():
    """Queue the case steps again for the next case."""
    sim = sys.modules["sim"]
    sim._steps[0:0] = [s_case_set, s_case_off, s_case_check, s_case_render]


@step
def s_ae_row():
    ae = import_module(MODULE + ".ui.ae_layout")
    rows = [row for sec in ae.CAMERA if sec.name == "Film Back" for row in sec.rows]
    check(f"Attribute Editor > Film Back: Fit Resolution Gate is Maya's (Fill / Horizontal / Vertical / Overscan) "
          f"({[r for r in rows if r[-1] == 'Fit Resolution Gate']})",
          ("prop", "data", "allset_film_fit", "Fit Resolution Gate") in rows)


run()
