"""#361: in the UV Editor a selected edge on a UV shell border shows in the selection colour, like a selected edge
inside a shell; the unselected border edges keep the thick texture border colour. Cube -> UV > UV Editor, UV Sync
Selection on, edge mode, one border edge selected. Shots: ALLSET_GUI_SHOTS."""

import os
import sys
import tempfile
from importlib import import_module

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, run, setup, step, view3d, win  # noqa: E402

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
def s_select_border_edge():
    w, a, r = uv_window()
    check(f"UV Editor window open ({C['open']})", a is not None and cube().mode == 'EDIT')
    if a is None:
        return
    ts = bpy.context.scene.tool_settings
    ts.use_uv_select_sync = True
    ts.mesh_select_mode = (False, True, False)
    with bpy.context.temp_override(window=w, area=a, region=r):
        bpy.ops.image.view_all(fit_view=True)
    bm = bmesh.from_edit_mesh(cube().data)
    C["bm"] = bm
    uv = bm.loops.layers.uv.active

    def side(l):
        return (tuple(l[uv].uv), tuple(l.link_loop_next[uv].uv))

    def cut(e):     # the two faces' UVs differ along the edge: both sides are shell borders
        a, b = e.link_loops
        return side(a) != side(b)[::-1]
    borders = [e for e in bm.edges if len(e.link_loops) == 2 and cut(e)]
    edge = borders[0]
    near_edges = {edge, *edge.verts[0].link_edges, *edge.verts[1].link_edges}
    other = next(e for e in borders if e not in near_edges)
    C["sel"] = [side(l) for l in edge.link_loops]
    C["other"] = [side(l) for l in other.link_loops]
    for el in (*bm.verts, *bm.edges, *bm.faces):
        el.select = False
    edge.select_set(True)
    bm.select_flush_mode()
    mod(".compat").uv_sync_from_mesh(bm)
    bmesh.update_edit_mesh(cube().data)
    check(f"a border edge with border sides picked ({len(C['sel'])} sides, {len(C['other'])} others)",
          C["sel"] and C["other"])
    redraw_all()


@step
def s_wait1():
    pass


@step
def s_wait2():
    pass


@step
def s_shot():
    w, _a, _r = uv_window()
    C["shot"] = os.path.join(SHOTS or tempfile.mkdtemp(), "gui_issue361_uv_border_selection.png")
    with bpy.context.temp_override(window=w):
        bpy.ops.screen.screenshot(filepath=C["shot"])


@step
def s_check():
    if "shot" not in C:
        return
    theme = bpy.context.preferences.themes[0].image_editor
    sel_rgb, wire_rgb = tuple(theme.edge_select)[:3], tuple(theme.wire_edit)[:3]
    check("Texture Borders on (the thick border lines are drawn)", bpy.context.window_manager.allset_uv_texture_borders)
    for seg in C["sel"]:
        cs = block(C["shot"], *uv_px(*mid(seg)))
        check(f"selected border edge drawn in the selection colour {sel_rgb}: {[tuple(round(v, 2) for v in c) for c in cs]}",
              any(near(c, sel_rgb) for c in cs))
    for seg in C["other"]:
        cs = block(C["shot"], *uv_px(*mid(seg)))
        check(f"unselected border edge keeps the border colour {wire_rgb}: {[tuple(round(v, 2) for v in c) for c in cs]}",
              not any(near(c, sel_rgb) for c in cs) and any(near(c, wire_rgb, 0.15) for c in cs))


run()
