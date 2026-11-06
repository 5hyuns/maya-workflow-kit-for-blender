"""#324: Delete over the Outliner and over the viewport takes a Boolean result's hidden inputs with it, like Maya;
Ctrl+Z brings the result and its inputs back."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, load_maya_layout, run, setup, step, view3d, win  # noqa: E402

C = {}


def wait(n=12):
    for _ in range(n):
        step(lambda: None)


def outliner():
    return max((a for a in win().screen.areas if a.type == 'OUTLINER'), key=lambda a: a.height)


def region():
    return next(r for r in outliner().regions if r.type == 'WINDOW')


def meshes():
    return sorted(o.name for o in bpy.data.objects if o.type == 'MESH')


def inputs():
    mark = import_module(MODULE + ".operators.mesh_maya").BOOL_INPUT
    return sorted(o.name for o in bpy.data.objects if o.get(mark) and not o.visible_get())


@step
def s_setup():
    setup()
    load_maya_layout()


def boolean():
    def s():
        bpy.context.window_manager.allset_construction_history = True
        made = []
        for x, y in ((0.0, 0.0), (0.5, 0.0), (0.0, 0.5)):
            bpy.ops.allset.create(kind='CUBE')
            ob = bpy.context.active_object
            ob.location.x, ob.location.y = x, y
            made.append(ob)
        for o in bpy.context.view_layer.objects:
            o.select_set(False)
        for o in made:
            o.select_set(True)
        bpy.context.view_layer.objects.active = made[-1]
        bpy.ops.allset.boolean('EXEC_DEFAULT', True, operation='DIFFERENCE')
        C["result"] = made[0].name
        C["all"] = sorted(o.name for o in made)
    step(s)
    wait(4)


boolean()


@step
def s_made():
    check(f"Boolean with history: one result, two hidden inputs ({meshes()}, {inputs()})",
          meshes() == C["all"] and len(inputs()) == 2)
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    C["probe"] = [region().y + region().height - int(round(20 * bpy.context.preferences.system.ui_scale) * (i + 0.5))
                  for i in range(16)]
    C["row"] = None


def probe(i):
    def s_click():
        if C["row"] is not None:
            return
        r = region()
        x, y = r.x + int(r.width * 0.35), C["probe"][i]
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
        ev('LEFTMOUSE', 'PRESS', x=x, y=y)
        ev('LEFTMOUSE', 'RELEASE', x=x, y=y)

    def s_look():
        sel = [o.name for o in bpy.context.view_layer.objects if o.select_get()]
        if C["row"] is None and sel == [C["result"]]:
            C["row"] = C["probe"][i]
    step(s_click)
    step(s_look)


for _i in range(16):
    probe(_i)


def key_over(where, key, **mods):
    def s():
        x, y = where()
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
        ev(key, 'PRESS', x=x, y=y, **mods)
        ev(key, 'RELEASE', x=x, y=y, **mods)
    wait(4)
    step(s)
    wait(6)


def over_outliner():
    r = region()
    return r.x + int(r.width * 0.35), C["row"]


def over_view():
    _a, r = view3d()
    return r.x + r.width // 2, r.y + r.height // 2


@step
def s_row():
    check(f"Outliner row of the result found ({C['row']})", C["row"] is not None)


key_over(over_outliner, 'DEL')


@step
def s_outliner_deleted():
    check(f"Delete over the Outliner removes the result and its hidden inputs ({meshes()})", meshes() == [])


key_over(over_view, 'Z', ctrl=True)


@step
def s_undone():
    check(f"Ctrl+Z brings the result and both hidden inputs back ({meshes()}, {inputs()})",
          meshes() == C["all"] and len(inputs()) == 2)
    for o in bpy.context.view_layer.objects:
        o.select_set(o.name == C["result"])
    bpy.context.view_layer.objects.active = bpy.data.objects[C["result"]]


key_over(over_view, 'DEL')


@step
def s_view_deleted():
    check(f"Delete over the viewport removes the result and its hidden inputs ({meshes()})", meshes() == [])


key_over(over_view, 'Z', ctrl=True)


@step
def s_undone2():
    check(f"Ctrl+Z after the viewport Delete brings all three back ({meshes()})", meshes() == C["all"])


run()
