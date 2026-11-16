"""In a real UI: Weight Paint (where Paint Skin Weights paints) in Maya mode opens without Blender's brush asset
shelf under the views, on 5.2 and 5.3 alike (Maya has no brush strip there; Blender 5.3 opens the shelf the first time
a view is in Weight Paint). Back in Blender mode the shelf type has its own options again: a new file's view in
Weight Paint shows the shelf exactly when Blender itself does."""

import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, load_maya_layout, run, setup, step, win  # noqa: E402

C = {}
SHELF = "VIEW3D_AST_brush_weight_paint"
C["options"] = set(getattr(bpy.types, SHELF).bl_options)      # Blender's own, before Maya mode is on


def views():
    return [a for a in win().screen.areas if a.type == 'VIEW_3D']


def shelves():
    """[(view width, shelf flag, shelf region heights)] of the main window's 3D Views."""
    return [(a.width, a.spaces.active.show_region_asset_shelf,
             [r.height for r in a.regions if r.type in ('ASSET_SHELF', 'ASSET_SHELF_HEADER') and r.height > 1])
            for a in views()]


def weight_paint():
    area = max(views(), key=lambda a: a.width * a.height)
    region = next(r for r in area.regions if r.type == 'WINDOW')
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.object.mode_set(mode='WEIGHT_PAINT')


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_paint():
    area = max(views(), key=lambda a: a.width * a.height)
    region = next(r for r in area.regions if r.type == 'WINDOW')
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.allset.create(kind='CUBE')
    weight_paint()
    redraw()


step(redraw)


@step
def s_no_shelf():
    got = shelves()
    check(f"Maya mode: Weight Paint opens without the brush shelf under any view ({bpy.context.mode}, {got})",
          bpy.context.mode == 'PAINT_WEIGHT' and got and all(not heights for _w, _flag, heights in got))
    check(f"... the shelf type opens hidden in Maya mode ({sorted(getattr(bpy.types, SHELF).bl_options)})",
          'DEFAULT_VISIBLE' not in getattr(bpy.types, SHELF).bl_options)
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.allset.switch_mode(mode='BLENDER')


@step
def s_blender():
    now = set(getattr(bpy.types, SHELF).bl_options)
    check(f"Blender mode: the shelf type has Blender's own options again ({sorted(now)} vs {sorted(C['options'])})",
          now == C["options"])
    bpy.ops.wm.read_homefile()


@step
def s_blender_paint():
    ob = bpy.context.view_layer.objects.active
    if ob is None or ob.type != 'MESH':
        bpy.ops.mesh.primitive_cube_add()
    weight_paint()
    redraw()


step(redraw)


@step
def s_blender_shelf():
    got = shelves()
    want = 'DEFAULT_VISIBLE' in C["options"]
    check(f"Blender mode, a new file: Weight Paint shows the brush shelf exactly when Blender does ({want}, {got})",
          bpy.context.mode == 'PAINT_WEIGHT' and got and all(bool(heights) == want for _w, _flag, heights in got))


run()
