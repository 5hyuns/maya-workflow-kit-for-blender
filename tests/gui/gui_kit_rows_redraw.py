"""In the Maya layout, the kit rows that redraw on every frame and selection change draw the same pixels from what
they kept as from scratch: the shelf row, the Outliner's kit tree, the Range Slider in the timeline header and the
Time Slider (ruler + key ticks). A shelf redraw that changed nothing makes no new GPU batch (it made one per
rectangle on every redraw)."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, load_maya_layout, run, screenshot, setup, step, win  # noqa: E402

C = {}
shelf = import_module(f"{MODULE}.ui.shelf")
ts = import_module(f"{MODULE}.ui.time_slider")
tree = import_module(f"{MODULE}.ui.outliner_tree")
rb = import_module(f"{MODULE}.ui.range_bar")


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


def rects():
    """Window rects (x, y, w, h) of the shelf row, the Outliner, the timeline header and the Time Slider."""
    out = {}
    for a in win().screen.areas:
        for r in a.regions:
            if r.width < 2 or r.height < 2:
                continue
            kind = (a.type, r.type)
            if kind == ('IMAGE_EDITOR', 'WINDOW') and shelf.is_shelf_row(a.spaces.active) or kind in (
                    ('OUTLINER', 'WINDOW'), ('DOPESHEET_EDITOR', 'HEADER'), ('DOPESHEET_EDITOR', 'WINDOW')):
                out[f"{a.type}:{r.type}:{a.x}:{a.y}"] = (r.x, r.y, r.width, r.height)
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
    path = os.path.join(bpy.app.tempdir, f"gui_kit_rows_{name}.png")
    screenshot(path)
    return pixels(path)


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_scene():
    sc = bpy.context.scene
    bpy.ops.mesh.primitive_cube_add()
    cube = bpy.context.active_object
    for f in (1, 12, 30, 61):
        cube.location.x = f * 0.1
        cube.keyframe_insert("location", frame=f)
    bpy.ops.mesh.primitive_uv_sphere_add(location=(3, 0, 0))
    cube.select_set(True)
    bpy.context.view_layer.objects.active = cube
    sc.frame_set(12)
    redraw()


step(redraw)
step(redraw)


@step
def s_kept():
    C["rects"] = rects()
    check("the shelf row, Outliner, timeline header and Time Slider are on screen", len(C["rects"]) >= 4)
    C["kept"] = shot("kept")
    # what the rows keep between redraws, dropped: the next redraw makes everything again
    shelf._SHELF_BATCHES.clear()
    ts._TRIS.clear()
    tree._by_name["key"] = None
    rb._gaps.clear()
    redraw()


@step
def s_fresh():
    fresh = shot("fresh")
    same = {k: crop(C["kept"], r) == crop(fresh, r) for k, r in C["rects"].items()}
    check(f"the same pixels from kept batches and names as from scratch {same}", all(same.values()))
    drawn = [len(v) for v in tree.SEEN.values()]
    check(f"the Outliner drew its rows without an error (rows {drawn})",
          any(drawn) and not tree._state.get("draw_error"))
    check("the Range Slider found its gap", any(rb._bars.values()))
    batch = import_module("gpu_extras.batch")
    real = batch.batch_for_shader
    made = {"shelf": 0, "time slider": 0}

    def counted(*a, **k):
        space = getattr(bpy.context, "space_data", None)
        region = getattr(bpy.context, "region", None)
        if shelf.is_shelf_row(space):
            made["shelf"] += 1
        elif space is not None and space.type == 'DOPESHEET_EDITOR' and getattr(region, "type", "") == 'WINDOW':
            made["time slider"] += 1
        return real(*a, **k)
    batch.batch_for_shader = counted
    C["restore"] = lambda: setattr(batch, "batch_for_shader", real)
    C["made"] = made
    redraw()


@step
def s_count():
    C["restore"]()
    check(f"a redraw that changed nothing makes no new shelf or Time Slider batch {C['made']}",
          C["made"] == {"shelf": 0, "time slider": 0})


run()
