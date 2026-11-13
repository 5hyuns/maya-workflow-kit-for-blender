"""In the Maya layout, the kit rows that redraw on every frame and selection change draw the same pixels from what
they kept as from scratch: the shelf row, the Outliner's kit tree, the Range Slider in the timeline header and the
Time Slider (ruler + key ticks). A shelf redraw that changed nothing makes no new GPU batch (it made one per
rectangle on every redraw); an Outliner redraw that changed nothing makes no new glyph batch and works out no row
icon's shapes again."""

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
kit_icons = import_module(f"{MODULE}.ui.kit_icons")
layout = import_module(f"{MODULE}.ui.hypergraph_layout")


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
    getattr(tree, "_ICON_PARTS", {}).clear()
    getattr(kit_icons, "_quads", {}).clear()
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
    made = {"shelf": 0, "time slider": 0, "outliner glyph": 0, "outliner icon shapes": 0}

    def counted(*a, **k):
        space = getattr(bpy.context, "space_data", None)
        region = getattr(bpy.context, "region", None)
        if sys._getframe(1).f_code.co_name == "draw_texture":
            made["outliner glyph"] += 1
        elif shelf.is_shelf_row(space):
            made["shelf"] += 1
        elif space is not None and space.type == 'DOPESHEET_EDITOR' and getattr(region, "type", "") == 'WINDOW':
            made["time slider"] += 1
        return real(*a, **k)
    batch.batch_for_shader = counted
    real_shapes = layout.icon_shapes

    def shapes(kind):
        made["outliner icon shapes"] += 1
        return real_shapes(kind)
    layout.icon_shapes = shapes
    drew = C["outliner draws"] = [tree.STATS["draws"]]

    def restore():
        batch.batch_for_shader = real
        layout.icon_shapes = real_shapes
        drew.append(tree.STATS["draws"])
    C["restore"] = restore
    C["made"] = made
    redraw()


@step
def s_count():
    C["restore"]()
    drew = C["outliner draws"]
    check(f"the Outliner rows redrew ({drew[1] - drew[0]} redraws)", drew[1] > drew[0])
    check(f"a redraw that changed nothing makes no new shelf, Time Slider or Outliner glyph batch and works out no "
          f"row icon's shapes again {C['made']}",
          C["made"] == {"shelf": 0, "time slider": 0, "outliner glyph": 0, "outliner icon shapes": 0})
    # enough rows to scroll the Outliner
    me = bpy.data.meshes.new("rowShape")
    for i in range(80):
        ob = bpy.data.objects.new(f"row{i:02d}", me)
        bpy.context.scene.collection.objects.link(ob)
    redraw()


def outliner():
    area = next(a for a in win().screen.areas if a.type == 'OUTLINER' and tree.is_tree(a.spaces.active))
    return area, next(r for r in area.regions if r.type == 'WINDOW')


@step
def s_mouse_in():
    # the mouse enters the Outliner first: Blender redraws the area it enters (its header too)
    from sim import ev
    _area, region = outliner()
    ev('MOUSEMOVE', 'NOTHING', x=region.x + region.width // 2, y=region.y + region.height // 2)


step(lambda: None)


@step
def s_wheel():
    area, region = outliner()
    draws = C["draws"] = {"WINDOW": 0, "HEADER": 0}

    def counter(rt):
        def count():
            if bpy.context.area is not None and bpy.context.area.as_pointer() == area.as_pointer():
                draws[rt] += 1
        return count
    C["handles"] = [(bpy.types.SpaceOutliner.draw_handler_add(counter(rt), (), rt, 'POST_PIXEL'), rt)
                    for rt in ("WINDOW", "HEADER")]
    C["first"] = tree.SCROLL.get(area.as_pointer(), 0)
    from sim import ev
    ev('WHEELDOWNMOUSE', 'PRESS', x=region.x + region.width // 2, y=region.y + region.height // 2)


@step
def s_wheel_check():
    area, region = outliner()
    draws = dict(C["draws"])
    check(f"the wheel scrolls the kit rows ({C['first']} -> {tree.SCROLL.get(area.as_pointer(), 0)})",
          tree.SCROLL.get(area.as_pointer(), 0) > C["first"])
    check(f"the scroll redrew the rows {draws}", draws["WINDOW"] >= 1)
    C["scrolled"] = shot("scrolled")
    area.tag_redraw()                  # a full redraw (Blender rebuilds its own tree first)


@step
def s_wheel_same():
    full = shot("scrolled_full")
    area, region = outliner()
    r = (region.x, region.y, region.width, region.height)
    check("a scroll draws the same rows as a full Outliner redraw", crop(C["scrolled"], r) == crop(full, r))


step(lambda: None)            # what the screenshot redraws settles


@step
def s_hover():
    _area, region = outliner()
    C["draws"].update(WINDOW=0, HEADER=0)
    from sim import ev
    ev('MOUSEMOVE', 'NOTHING', x=region.x + region.width // 2, y=region.y + region.height // 2 + 40)   # another row


@step
def s_hover_check():
    draws = dict(C["draws"])
    check(f"a hover over another row redraws the rows, not the Outliner header {draws}",
          draws["WINDOW"] >= 1 and draws["HEADER"] == 0)
    for h, rt in C["handles"]:
        bpy.types.SpaceOutliner.draw_handler_remove(h, rt)


run()
