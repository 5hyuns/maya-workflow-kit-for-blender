"""In a real UI: the mouse wheel over the 3D View zooms (dollies) the view in Maya mode, in Blender's own layout,
in the Maya layout and in edit mode with the Move tool."""

import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, ev, run, step, setup, load_maya_layout, win  # noqa: E402

S = {}


def main_view():
    return max((a for a in win().screen.areas if a.type == 'VIEW_3D'), key=lambda a: a.width * a.height)


def rv3d():
    return main_view().spaces.active.region_3d


def window_region():
    return next(r for r in main_view().regions if r.type == 'WINDOW')


def park():
    r = window_region()
    ev('MOUSEMOVE', 'NOTHING', x=r.x + r.width // 2, y=r.y + r.height // 2)


def wheel_pair(tag):
    """Two steps: record the distance and wheel, then check the distance changed."""
    def s_wheel():
        park()
        S[tag] = rv3d().view_distance
        for _ in range(3):
            ev(S["type"], 'PRESS')

    def s_check():
        before, after = S[tag], rv3d().view_distance
        print("WHEEL", tag, S["type"], before, after, flush=True)
        check(f"{tag}: {S['type']} changes the view distance ({before:.3f} -> {after:.3f})",
              abs(after - before) > 1e-4)
    return s_wheel, s_check


@step
def s_setup():
    setup()


def to_edit_move():
    ob = bpy.context.view_layer.objects.active or next(o for o in bpy.context.scene.objects if o.type == 'MESH')
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    with bpy.context.temp_override(window=win(), area=main_view(), region=window_region()):
        bpy.ops.object.mode_set(mode='EDIT')
    park()
    ev('W', 'PRESS')
    ev('W', 'RELEASE')


for layout in ("blender layout", "maya layout", "maya layout, edit mode, Move tool"):
    if layout == "maya layout":
        step(lambda: load_maya_layout())
        step(lambda: None)
    if layout.endswith("Move tool"):
        step(lambda: bpy.ops.mesh.primitive_cube_add() if not any(o.type == 'MESH' for o in bpy.context.scene.objects) else None)
        step(to_edit_move)
        step(lambda: None)
    for t in ('WHEELUPMOUSE', 'WHEELDOWNMOUSE'):
        step((lambda t=t: S.__setitem__("type", t)))
        a, b = wheel_pair(f"{layout} {t}")
        step(a)
        step(b)


run()
