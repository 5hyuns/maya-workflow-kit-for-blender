"""In a real UI: cube -> UV > UV Editor with an 8 x 8 image -> UV Editor > Image > Dim darkens the image while the
UV lines keep their colour; Dim again brings the image back; the image is drawn unfiltered (each pixel one flat
colour when zoomed in), which the greyed Image > Unfiltered item says (screenshots)."""

import os
import random
import sys
from importlib import import_module

import bmesh
import bpy
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, run, setup, step, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
TMP = os.path.join(bpy.app.tempdir, "gui_uv_image_dim")
C = {}
PATH = "UV Editor/Image/Dim"


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


def grab(name):
    """Screenshot of the UV window -> (h, w, 4) float array, row 0 at the bottom."""
    w, _a, _r = uv_window()
    os.makedirs(TMP, exist_ok=True)
    path = os.path.join(TMP, name + ".png")
    with bpy.context.temp_override(window=w):
        bpy.ops.screen.screenshot(filepath=path)
    if SHOTS:
        with bpy.context.temp_override(window=w):
            bpy.ops.screen.screenshot(filepath=os.path.join(SHOTS, f"gui_uv_image_dim_{name}.png"))
    img = bpy.data.images.load(path)
    px = np.empty(img.size[0] * img.size[1] * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    out = px.reshape(img.size[1], img.size[0], 4)
    bpy.data.images.remove(img)
    return out


def at(u, v):
    """Window pixel (x, y) of UV (u, v) in the UV Editor."""
    _w, _a, r = uv_window()
    x, y = r.view2d.view_to_region(u, v, clip=False)
    return r.x + int(x), r.y + int(y)


def lum(p):
    return float(p[0] + p[1] + p[2])


@step
def s_setup():
    C["x"], C["y"] = setup()
    bpy.context.view_layer.objects.active = cube()
    cube().select_set(True)
    area, region = view3d()
    menu_map = mod(".ui.menu_map")
    modal = mod(".marking.modal")
    with bpy.context.temp_override(window=win(), area=area, region=region):
        modal.run_action(bpy.context, menu_map.MAP["UV/UV Editor"])


@step
def s_wait_uv_window():
    import sim
    C.setdefault("wait_uv", 0)
    if uv_window()[1] is None and C["wait_uv"] < 15:
        C["wait_uv"] += 1
        sim._steps.insert(0, s_wait_uv_window)


@step
def s_image():
    w, a, r = uv_window()
    check("a UV Editor window opens", a is not None)
    if a is None:
        return
    b = bmesh.from_edit_mesh(cube().data)
    for el in (*b.verts, *b.edges, *b.faces):
        el.select = True
    bmesh.update_edit_mesh(cube().data)
    img = bpy.data.images.new("dim_probe", 8, 8)
    random.seed(3)
    px = []
    for _ in range(64):
        px += [0.2 + 0.8 * random.random(), 0.2 + 0.8 * random.random(), 0.2 + 0.8 * random.random(), 1.0]
    img.pixels = px
    a.spaces.active.image = img
    with bpy.context.temp_override(window=w, area=a, region=r):
        bpy.ops.image.view_all(fit_view=True)
    a.tag_redraw()


@step
def s_plain():
    C["plain"] = grab("plain")
    w, a, r = uv_window()
    menu_map = mod(".ui.menu_map")
    modal = mod(".marking.modal")
    with bpy.context.temp_override(window=w, area=a, region=r):
        C["run"] = modal.run_action(bpy.context, menu_map.MAP[PATH])
    a.tag_redraw()


@step
def s_wait():
    pass


@step
def s_dimmed():
    C["dim"] = grab("dimmed")
    w, a, r = uv_window()
    menu_map = mod(".ui.menu_map")
    modal = mod(".marking.modal")
    with bpy.context.temp_override(window=w, area=a, region=r):
        modal.run_action(bpy.context, menu_map.MAP[PATH])
    a.tag_redraw()


@step
def s_wait2():
    pass


@step
def s_check():
    back = grab("back")
    plain, dimmed = C["plain"], C["dim"]
    wm = bpy.context.window_manager
    check(f"the menu item turned Dim on, then off ({C.get('run')})", wm.allset_uv_image_dim is False)
    # image texels outside the cube's UV layout (top-left, bottom-right corners)
    ratios = []
    for u, v in ((0.0625, 0.9375), (0.9375, 0.0625), (0.0625, 0.0625)):
        x, y = at(u, v)
        ratios.append(lum(dimmed[y, x]) / max(1e-6, lum(plain[y, x])))
    check(f"Dim darkens the image ({[round(q, 3) for q in ratios]})", all(0.4 < q < 0.85 for q in ratios))
    x, y = at(0.0625, 0.9375)
    check("Dim again brings the image back", float(np.abs(back[y, x, :3] - plain[y, x, :3]).max()) < 0.02)
    # a UV line: the cube layout's left border (u 0.375) - some pixel near it is the line colour, unchanged
    x, y = at(0.375, 0.5)
    win_ = plain[y - 3:y + 4, x - 3:x + 4, :3]
    dwin = dimmed[y - 3:y + 4, x - 3:x + 4, :3]
    line = [(i, j) for i in range(win_.shape[0]) for j in range(win_.shape[1])
            if win_[i, j, 0] > 0.8 and win_[i, j, 2] < 0.35]
    same = [ij for ij in line if float(np.abs(dwin[ij][:3] - win_[ij][:3]).max()) < 0.03]
    check(f"the UV lines keep their colour ({len(same)} of {len(line)} line pixels)", line and same)
    # unfiltered: across one texel (zoomed in) the colour stays flat
    xa, ya = at(0.0625 - 0.04, 0.9375)
    xb, yb = at(0.0625 + 0.04, 0.9375)
    flat = float(np.abs(plain[ya, xa, :3] - plain[yb, xb, :3]).max())
    check(f"the image is drawn unfiltered ({flat:.4f}, texel {at(0.125, 0)[0] - at(0, 0)[0]} px wide)", flat < 0.01)
    notices = mod(".ui.notices")
    check("Image > Unfiltered says so", notices.greyed_notice("UV Editor/Image/Unfiltered") is not None)


run()
