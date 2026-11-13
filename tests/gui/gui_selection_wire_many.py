"""In a real UI: 900 selected objects among 3,000 (chains of five, so 1,500 get the wire through the hierarchy
highlight) keep the Maya selection wire light. One redraw of the view with the wire costs under 150 ms more than
without it (asking each highlighted object for its children looked through all 3,000 objects every time: about a
second a redraw), the wire is drawn for every highlighted object, and a second set of redraws reads no bound box
again."""

import os
import sys
import time
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, run, step, setup, win, load_maya_layout  # noqa: E402

GUI_TIMEOUT = 300
C = {}


def area3d():
    return max((a for a in win().screen.areas if a.type == 'VIEW_3D'), key=lambda a: a.width * a.height)


def region3d():
    return next(r for r in area3d().regions if r.type == 'WINDOW')


def prefs():
    return bpy.context.preferences.addons[MODULE].preferences


def frame_ms(n=10):
    with bpy.context.temp_override(window=win(), area=area3d(), region=region3d()):
        bpy.ops.wm.redraw_timer(type='DRAW', iterations=3)
        t = time.perf_counter()
        bpy.ops.wm.redraw_timer(type='DRAW', iterations=n)
    return (time.perf_counter() - t) / n * 1000.0


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_scene():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    me = bpy.data.meshes.new("box")
    me.from_pydata([(x, y, z) for x in (-.2, .2) for y in (-.2, .2) for z in (-.2, .2)], [],
                   [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)])
    coll = bpy.context.scene.collection
    obs, parent = [], None
    for i in range(3000):
        ob = bpy.data.objects.new(f"o{i:04d}", me)
        coll.objects.link(ob)
        if i % 5:
            ob.parent = parent
            ob.location = (0.5, 0, 0)
        else:
            ob.location = ((i // 5) % 30 - 15.0, (i // 150) - 10.0, 0)
        obs.append(ob)
        parent = ob
    bpy.context.view_layer.update()
    for i, ob in enumerate(obs):
        ob.select_set(i % 10 < 3)
    bpy.context.view_layer.objects.active = obs[0]
    with bpy.context.temp_override(window=win(), area=area3d(), region=region3d()):
        bpy.ops.view3d.view_all()
    prefs().maya_selection_wire = False
    area3d().tag_redraw()


@step
def s_time_off():
    C["off"] = frame_ms()
    prefs().maya_selection_wire = True
    area3d().tag_redraw()


@step
def s_time_on():
    sw = import_module(MODULE + ".ui.selection_wire")
    C["on"] = frame_ms()
    with bpy.context.temp_override(window=win(), area=area3d(), region=region3d()):
        drawn = sw.highlighted(bpy.context)
    extra = C["on"] - C["off"]
    print("GUI selection wire many", len(drawn), C["off"], C["on"], extra)
    check(f"{len(drawn)} highlighted objects: redraw {C['off']:.1f} -> {C['on']:.1f} ms with the selection wire "
          f"(+{extra:.1f} ms, < 150)", len(drawn) == 1500 and extra < 150.0)
    check(f"the wire is drawn for each of them ({len(sw._batches)} batches, handler kept, {sw.frame_ms():.2f} ms)",
          len(sw._batches) >= 1500 and sw._handle and sw.frame_ms() > 0)
    real, reads = sw._bounds, []
    sw._bounds = lambda *a: reads.append(1) or real(*a)
    try:
        frame_ms(3)
    finally:
        sw._bounds = real
    check(f"redraws with nothing changed read no bound box again ({len(reads)} reads)", not reads)


run()
