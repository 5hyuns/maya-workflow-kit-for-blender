"""Duplicate Special > Instance in the Maya Outliner: by default the instance copy looks like any other row (like
Maya); with the add-on preference "Mark Instances in the Outliner" on, its row is drawn purple (screenshot) and the
tree draws without an error, also with the mouse over the row ("Instance of" tip)."""

import os
import sys
from importlib import import_module

import bpy
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, screenshot, setup, step, win, load_maya_layout  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def tree():
    return import_module(MODULE + ".ui.outliner_tree")


def prefs():
    return bpy.context.preferences.addons[MODULE].preferences


def outliner():
    area = next(a for a in win().screen.areas if a.type == 'OUTLINER')
    return area, next(r for r in area.regions if r.type == 'WINDOW')


def redraw_all():
    for area in win().screen.areas:
        area.tag_redraw()


def purple_pixels(name):
    """Pixels of the Outliner's row area that have the instance purple (red and blue well above green)."""
    path = os.path.join(SHOTS or bpy.app.tempdir, f"gui_outliner_instances_{name}.png")
    screenshot(path)
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    px = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(px)
    bpy.data.images.remove(img)
    px = px.reshape(h, w, 4)
    _area, r = outliner()
    box = px[r.y:r.y + r.height, r.x:r.x + r.width, :3]
    red, green, blue = box[..., 0], box[..., 1], box[..., 2]
    return int(np.count_nonzero((blue > 0.6) & (red > 0.45) & (green < red - 0.12) & (green < blue - 0.25)))


def instance_row():
    """Window (x, y) of the instance copy's row in the last tree draw, or None."""
    _area, r = outliner()
    for y0, y1, row in tree().DRAWN.get(r.as_pointer(), []):
        if row.ob == C["copy"]:
            return r.x + 60, r.y + (y0 + y1) // 2
    return None


@step
def s_setup():
    setup()
    load_maya_layout()
    me = bpy.data.meshes.new("pCubeShape1")
    me.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [], [(0, 1, 2)])
    ob = bpy.data.objects.new("pCube1", me)
    bpy.context.scene.collection.objects.link(ob)
    for o in bpy.context.scene.objects:
        o.select_set(False)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    area = max((a for a in win().screen.areas if a.type == 'VIEW_3D'), key=lambda a: a.width * a.height)
    region = next(r for r in area.regions if r.type == 'WINDOW')
    with bpy.context.temp_override(window=win(), area=area, region=region, space_data=area.spaces.active):
        bpy.ops.allset.duplicate_special(geometry_type='INSTANCE')
    C["copy"] = bpy.context.view_layer.objects.active.name
    for o in bpy.context.scene.objects:
        o.select_set(False)
    redraw_all()


@step
def s_wait():
    redraw_all()


@step
def s_default():
    C["off"] = purple_pixels("off")
    check(f"by default the instance copy {C['copy']} is drawn like other rows ({C['off']} purple pixels)",
          C["off"] < 20)
    prefs().outliner_instance_marks = True
    redraw_all()


@step
def s_on_wait():
    redraw_all()


@step
def s_on():
    on = purple_pixels("on")
    check(f"with the preference on its row is purple ({on} purple pixels)", on > 40)
    pos = instance_row()
    check(f"the instance row was drawn ({pos})", pos is not None)
    if pos is not None:
        ev('MOUSEMOVE', 'NOTHING', x=pos[0], y=pos[1])
    redraw_all()


@step
def s_hover():
    redraw_all()


@step
def s_check():
    check(f"the tree drew without an error, also with the tip ({tree()._state.get('draw_error')})",
          not tree()._state.get("draw_error"))
    prefs().outliner_instance_marks = False


run()
