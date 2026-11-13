"""In the Maya layout the top bar, the Status Line strip, the panel toolbar and the dock redraw on every frame change.
They draw the same pixels from what they keep (glyph icon ids, the dock's sampled row) as from scratch; one top bar
redraw builds the workspace list once and sizes each menu once; the dock finds the Layer Editor list in the drawn
pixels exactly where the per-pixel lists found it."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, dock_area, load_maya_layout, run, screenshot, setup, step, win  # noqa: E402

C = {}
sl = import_module(f"{MODULE}.ui.status_line")
md = import_module(f"{MODULE}.ui.maya_dock")
si = import_module(f"{MODULE}.ui.status_icons")
wsm = import_module(f"{MODULE}.ui.workspaces")
ms = import_module(f"{MODULE}.ui.menu_sets")
shelf = import_module(f"{MODULE}.ui.shelf")
cb = import_module(f"{MODULE}.ui.channel_box")


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()
    sl.redraw_top_bars()


def rects():
    """Window rects (x, y, w, h): the top bar (the window's top strip), the Status Line strip header, the main
    view's tool header (panel toolbar) and the dock."""
    w = win()
    out = {"top bar": (0, w.height - 28, w.width, 28)}
    for a in w.screen.areas:
        for r in a.regions:
            if r.width < 2 or r.height < 2:
                continue
            if a.type == 'IMAGE_EDITOR' and r.type == 'HEADER' and shelf.is_strip(a.spaces.active):
                out["status line"] = (r.x, r.y, r.width, r.height)
            elif a.type == 'VIEW_3D' and r.type == 'TOOL_HEADER' and a.width > 300:
                out["panel toolbar"] = (r.x, r.y, r.width, r.height)
            elif a.type == 'PROPERTIES' and r.type == 'WINDOW' and md.role(a) == 'STACK':
                out["dock"] = (r.x, r.y, r.width, r.height)
    return out


def pixels(path):
    im = bpy.data.images.load(path, check_existing=False)
    w, h = im.size
    pix = im.pixels[:]
    bpy.data.images.remove(im)
    return w, h, pix


def crop(shot, rect):
    w, _h, pix = shot
    x, y, rw, rh = rect
    return [pix[(row * w + x) * 4:(row * w + x + rw) * 4] for row in range(y, y + rh)]


def shot(name):
    path = os.path.join(bpy.app.tempdir, f"gui_ui_header_{name}.png")
    screenshot(path)
    return pixels(path)


def old_list_hole(context, region, rows_kept):
    """The dock's Layer Editor list rect found with one Python list per pixel (the reads before)."""
    import gpu
    scale = context.preferences.system.ui_scale or 1.0
    back = max(tuple(context.preferences.themes[0].properties.space.back)[:3])
    limit = back * 255.0 - 4.0
    le_top = int(region.height * (1.0 - cb.cb_share(region, cb._unit(context))))
    fb = gpu.state.active_framebuffer_get()
    key = region.as_pointer()
    first = max(1, round(14 * scale))
    rows = [rows_kept.get(key)] + list(range(first, round(64 * scale), max(1, round(4 * scale))))
    span, ys = None, first
    for ys in rows:
        if ys is None or le_top <= ys + 10:
            continue
        row = fb.read_color(0, ys, region.width, 1, 4, 0, 'UBYTE').to_list()
        span = md.dark_span([px[0] for px in row[0]], limit)
        if span is not None and span[1] - span[0] >= 40 * scale:
            break
        span = None
    if span is None:
        return None
    x0, x1 = span
    col = fb.read_color(x0 + 1, 0, 1, le_top, 4, 0, 'UBYTE').to_list()
    values = [c[0][0] for c in col]
    if values[ys] >= limit:
        return None
    top = md.dark_top(values, ys, limit, round(30 * scale))
    bottom = ys
    while bottom > 0 and values[bottom - 1] < limit:
        bottom -= 1
    return (x0, bottom, x1 + 1, top + 1)


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_scene():
    dock_area('CHANNEL_BOX')
    bpy.ops.mesh.primitive_cube_add()
    cube = bpy.context.active_object
    cube.select_set(True)
    bpy.context.view_layer.objects.active = cube
    redraw()


step(redraw)
step(redraw)


@step
def s_kept():
    C["rects"] = rects()
    check(f"the top bar, Status Line, panel toolbar and dock are on screen ({sorted(C['rects'])})",
          len(C["rects"]) == 4)
    C["kept"] = shot("kept")
    # what the bars keep between redraws, dropped: the next redraw finds everything again
    si._ids.clear()
    md._hole_row.clear()
    md._hole_kept.clear()
    redraw()


@step
def s_fresh():
    fresh = shot("fresh")
    same = {k: crop(C["kept"], r) == crop(fresh, r) for k, r in C["rects"].items()}
    check(f"the same pixels from kept icon ids and rows as from scratch {same}", all(same.values()))
    counts = C["counts"] = {"right": 0, "left": 0, "entries": 0, "sizes": 0, "preview gets": 0, "holes": []}
    real = {"right": sl.draw_right, "left": sl.draw_left, "entries": wsm.entries, "sizes": ms.menu_width_units,
            "collection": si._collection}

    def counted(key):
        def fn(*a, **k):
            counts[key] += 1
            return real[key](*a, **k)
        return fn

    sl.draw_right, sl.draw_left = counted("right"), counted("left")
    wsm.entries, ms.menu_width_units = counted("entries"), counted("sizes")
    pc = si._collection()

    class Gets:
        def get(self, key, default=None):
            counts["preview gets"] += 1
            return pc.get(key, default)

        def __getattr__(self, name):
            return getattr(pc, name)
    si._collection = lambda: Gets()

    def hole_check():
        area, region = bpy.context.area, bpy.context.region
        if region is None or region.type != 'WINDOW' or md.role(area) != 'STACK':
            return
        kept = dict(md._hole_row)
        old = old_list_hole(bpy.context, region, kept)
        new = md._list_hole(bpy.context, region)
        import gpu
        fb = gpu.state.active_framebuffer_get()
        y = region.height // 3
        listed = [px[0] for px in fb.read_color(0, y, region.width, 1, 4, 0, 'UBYTE').to_list()[0]]
        reds = md._reds(fb.read_color(0, y, region.width, 1, 4, 0, 'UBYTE'), region.width)
        counts["holes"].append((old, new, listed == reds))

    C["handle"] = bpy.types.SpaceProperties.draw_handler_add(hole_check, (), 'WINDOW', 'POST_PIXEL')

    def restore():
        sl.draw_right, sl.draw_left = real["right"], real["left"]
        wsm.entries, ms.menu_width_units = real["entries"], real["sizes"]
        si._collection = real["collection"]
        bpy.types.SpaceProperties.draw_handler_remove(C["handle"], 'WINDOW')
    C["restore"] = restore
    redraw()


@step
def s_count():
    C["restore"]()
    c = C["counts"]
    names = ms.menus_for_set(import_module(MODULE + ".preferences").get().menu_set)
    check(f"the top bar redrew ({c['left']} left, {c['right']} right)", c["left"] >= 1 and c["right"] >= 1)
    check(f"one workspace list per top bar redraw ({c['entries']} lists, {c['right']} redraws)",
          c["entries"] <= c["right"])
    check(f"each menu sized once per redraw ({c['sizes']} sizes, {len(names)} menus, {c['left']} redraws)",
          c['sizes'] <= len(names) * c["left"])
    check(f"the glyphs' icons need no preview lookup once shown ({c['preview gets']} lookups)",
          c["preview gets"] == 0)
    holes = c["holes"]
    check(f"the dock found the Layer Editor list where the per-pixel lists found it {holes[:2]}",
          holes and all(old == new and old is not None and same for old, new, same in holes))


run()
