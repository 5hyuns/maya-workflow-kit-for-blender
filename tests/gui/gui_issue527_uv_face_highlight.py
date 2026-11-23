"""#527: a face clicked in the 3D View (face mode, UV Sync Selection on) shows in the UV Editor with only its own
UV edges in the selection colour, like Maya; the edges of other shells that share its mesh edges keep the border
colour. Also the same with the thick texture borders off (Blender's own thin UV edges). Shots: ALLSET_GUI_SHOTS."""

import os
import sys
import tempfile
from importlib import import_module

import bmesh
import bpy
from bpy_extras import view3d_utils

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, ev, run, setup, step, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def mod(name):
    return import_module(sys.modules["sim"].MODULE + name)


def cube():
    return bpy.data.objects["Cube"]


def uv_window():
    for w in bpy.context.window_manager.windows:
        for a in w.screen.areas:
            if a.ui_type == 'UV':
                return w, a, next(r for r in a.regions if r.type == 'WINDOW')
    return None, None, None


def redraw_all():
    for w in bpy.context.window_manager.windows:
        for a in w.screen.areas:
            a.tag_redraw()


def uv_px(u, v):
    _w, _a, r = uv_window()
    x, y = r.view2d.view_to_region(u, v, clip=False)
    return r.x + int(round(x)), r.y + int(round(y))


def block(path, x, y):
    """sRGB colours of the 3 x 3 window pixels around (x, y) (bottom-left origin) in a screenshot."""
    img = bpy.data.images.load(path, check_existing=False)
    try:
        w, _h = img.size
        px = img.pixels[:]
        return [tuple(px[((y + dy) * w + x + dx) * 4 + k] for k in range(3)) for dx in (-1, 0, 1) for dy in (-1, 0, 1)]
    finally:
        bpy.data.images.remove(img)


def near(c, rgb, tol=0.1):
    return all(abs(a - b) <= tol for a, b in zip(c, rgb))


def mid(seg):
    (u0, v0), (u1, v1) = seg
    return (u0 + u1) / 2, (v0 + v1) / 2


def top_face(bm):
    return max(bm.faces, key=lambda f: f.calc_center_median().z)


@step
def s_setup():
    setup()
    bpy.context.view_layer.objects.active = cube()
    cube().select_set(True)
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        C["open"] = mod(".marking.modal").run_action(bpy.context, mod(".ui.menu_map").MAP["UV/UV Editor"])


@step
def s_wait_uv_window():
    import sim
    C.setdefault("wait_uv", 0)
    if uv_window()[1] is None and C["wait_uv"] < 15:
        C["wait_uv"] += 1
        sim._steps.insert(0, s_wait_uv_window)


@step
def s_split_top_face():
    w, a, r = uv_window()
    check(f"UV Editor window open ({C['open']})", a is not None and cube().mode == 'EDIT')
    if a is None:
        return
    ts = bpy.context.scene.tool_settings
    ts.use_uv_select_sync = True
    ts.mesh_select_mode = (False, False, True)
    bm = bmesh.from_edit_mesh(cube().data)
    uv = bm.loops.layers.uv.active
    top = top_face(bm)
    for loop in top.loops:          # the top face its own shell, away from the side faces
        loop[uv].uv = (loop[uv].uv.x * 0.25 + 0.7, loop[uv].uv.y * 0.25 + 0.05)
    for el in (*bm.verts, *bm.edges, *bm.faces):
        el.select = False
    bmesh.update_edit_mesh(cube().data)

    def side(l):
        return (tuple(l[uv].uv), tuple(l.link_loop_next[uv].uv))
    C["own"] = [side(l) for l in top.loops]
    C["others"] = [side(o) for l in top.loops for o in l.edge.link_loops if o.face is not top]
    with bpy.context.temp_override(window=w, area=a, region=r):
        bpy.ops.image.view_all(fit_view=True)
    redraw_all()


@step
def s_click_top_face():
    area, region = view3d()
    bm = bmesh.from_edit_mesh(cube().data)
    p = view3d_utils.location_3d_to_region_2d(region, region.data,
                                              cube().matrix_world @ top_face(bm).calc_center_median())
    check(f"top face centre on screen ({p})", p is not None)
    if p is None:
        return
    x, y = region.x + int(p.x), region.y + int(p.y)
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('LEFTMOUSE', 'PRESS', x=x, y=y)
    ev('LEFTMOUSE', 'RELEASE', x=x, y=y)


@step
def s_after_click():
    bm = bmesh.from_edit_mesh(cube().data)
    sel = [f.index for f in bm.faces if f.select]
    check(f"only the top face selected by the click ({sel})", sel == [top_face(bm).index])
    redraw_all()


@step
def s_wait1():
    pass


def shot(name):
    w, _a, _r = uv_window()
    path = os.path.join(C.setdefault("dir", SHOTS or tempfile.mkdtemp()), name)
    with bpy.context.temp_override(window=w):
        bpy.ops.screen.screenshot(filepath=path)
    return path


@step
def s_shot_borders():
    C["shot"] = shot("gui_issue527_uv_face_highlight.png")
    bpy.context.window_manager.allset_uv_texture_borders = False
    bpy.context.window_manager.allset_uv_shell_borders = False
    redraw_all()


@step
def s_wait2():
    pass


@step
def s_shot_thin():
    C["thin"] = shot("gui_issue527_uv_face_highlight_thin.png")
    bpy.context.window_manager.allset_uv_texture_borders = True


def _check(path, label):
    theme = bpy.context.preferences.themes[0].image_editor
    sel_rgb = tuple(theme.edge_select)[:3]
    for seg in C["own"]:
        cs = block(path, *uv_px(*mid(seg)))
        check(f"{label}: clicked face's edge in the selection colour {sel_rgb}: "
              f"{[tuple(round(v, 2) for v in c) for c in cs]}", any(near(c, sel_rgb) for c in cs))
    for seg in C["others"]:
        cs = block(path, *uv_px(*mid(seg)))
        check(f"{label}: other shell's edge on the same mesh edge not in the selection colour: "
              f"{[tuple(round(v, 2) for v in c) for c in cs]}", not any(near(c, sel_rgb) for c in cs))


@step
def s_check():
    if "shot" in C:
        _check(C["shot"], "texture borders")
    if "thin" in C:
        _check(C["thin"], "thin UV edges")


run()
