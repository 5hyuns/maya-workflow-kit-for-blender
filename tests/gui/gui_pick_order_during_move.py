"""Pick order in a real UI: a marquee in the Maya layout makes the last pick the lead in a "Select" undo step paired
with the box select's. A move started at once after the marquee (a middle drag in the same moment) runs while that
step is still to be pushed; the step must hold the state before the move: one Ctrl+Z after the move puts the objects
back and keeps the new lead, like Maya (undoing a move leaves the selection)."""

import os
import sys
from importlib import import_module

import bpy
from bpy_extras.view3d_utils import location_3d_to_region_2d
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, load_maya_layout, run, setup, step, tap, view3d, win  # noqa: E402

C = {"pushes": []}


def mod(name):
    return import_module(MODULE + "." + name)


def override():
    area, region = view3d()
    return bpy.context.temp_override(window=win(), area=area, region=region)


def xy(p):
    area, region = view3d()
    q = location_3d_to_region_2d(region, area.spaces.active.region_3d, Vector(p))
    return round(region.x + q.x), round(region.y + q.y)


def ob(name):
    return bpy.data.objects[name]


@step
def s_setup():
    C["mouse"] = setup()
    load_maya_layout()


@step
def s_scene():
    with override():
        for o in list(bpy.context.scene.objects):
            if o.type == 'MESH':
                bpy.data.objects.remove(o, do_unlink=True)
        for name, x in (("lead_a", -6.0), ("box_b", 3.0), ("box_c", 6.0)):
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, 0.0, 0.0))
            bpy.context.active_object.name = name
        bpy.ops.object.select_all(action='DESELECT')
    ob("lead_a").select_set(True)
    bpy.context.view_layer.objects.active = ob("lead_a")
    rv3d = view3d()[0].spaces.active.region_3d
    rv3d.view_location = (0.0, 0.0, 0.0)
    rv3d.view_distance = 30.0
    undo_pairs = mod("operators.undo_pairs")
    real = undo_pairs.push

    def push(scene, label, check=None):           # observe when the kit pushes its paired step
        C["pushes"].append((label, [op.bl_idname for op in win().modal_operators], ob("box_b").location.copy()))
        return real(scene, label, check)
    undo_pairs.push = push
    C["real_push"] = real
    ev('MOUSEMOVE', 'NOTHING', x=C["mouse"][0], y=C["mouse"][1])
    tap('W')


@step
def s_box_start():
    a, b = xy((1.5, 0.0, 1.5)), xy((7.5, 0.0, -1.5))
    C["box"] = (min(a[0], b[0]) - 10, max(a[1], b[1]) + 10, max(a[0], b[0]) + 10, min(a[1], b[1]) - 10)
    x0, y0, _x1, _y1 = C["box"]
    ev('MOUSEMOVE', 'NOTHING', x=x0, y=y0)


@step
def s_box_press():
    x0, y0, _x1, _y1 = C["box"]
    ev('LEFTMOUSE', 'PRESS', x=x0, y=y0)


for _i in range(1, 5):
    @step
    def s_box_move(i=_i):
        x0, y0, x1, y1 = C["box"]
        ev('MOUSEMOVE', 'NOTHING', x=x0 + (x1 - x0) * i // 4, y=y0 + (y1 - y0) * i // 4)


@step
def s_box_release_and_mmb():
    _x0, _y0, x1, y1 = C["box"]
    ev('LEFTMOUSE', 'RELEASE', x=x1, y=y1)
    C["before_move"] = {n: ob(n).location.copy() for n in ("box_b", "box_c")}
    ev('MIDDLEMOUSE', 'PRESS', x=x1, y=y1)          # the move starts at once


@step
def s_mmb_started():
    C["modal"] = [op.bl_idname for op in win().modal_operators]


for _i in range(1, 7):
    @step
    def s_mmb_move(i=_i):
        _x0, _y0, x1, y1 = C["box"]
        ev('MOUSEMOVE', 'NOTHING', x=x1 + 12 * i, y=y1)


@step
def s_mmb_release():
    _x0, _y0, x1, y1 = C["box"]
    ev('MIDDLEMOUSE', 'RELEASE', x=x1 + 72, y=y1)


@step
def s_settle():
    pass


@step
def s_moved():
    sel = sorted(o.name for o in bpy.context.selected_objects)
    lead = bpy.context.view_layer.objects.active
    moved = (ob("box_b").location - C["before_move"]["box_b"]).length > 1e-3
    check(f"the marquee picked the boxes ({sel}), the last pick leads ({lead.name if lead else None}), the middle "
          f"drag moved them ({moved}, modal at the start {C.get('modal')})",
          sel == ["box_b", "box_c"] and lead is not None and lead.name in sel and moved)
    pushed = [(label, ops, loc) for label, ops, loc in C["pushes"] if label == "Select"]
    print("PUSHES", [(l, o, tuple(round(v, 4) for v in loc)) for l, o, loc in C["pushes"]],
          "BEFORE", tuple(round(v, 4) for v in C["before_move"]["box_b"]),
          "AFTER", tuple(round(v, 4) for v in ob("box_b").location), flush=True)
    check(f"the lead's Select step holds the objects where they were before the move "
          f"({[tuple(round(v, 4) for v in loc) for _l, _o, loc in pushed]})",
          len(pushed) == 1 and (pushed[0][2] - C["before_move"]["box_b"]).length < 1e-4)
    ev('Z', 'PRESS', ctrl=True)
    ev('Z', 'RELEASE', ctrl=True)


@step
def s_undone():
    back = all((ob(n).location - loc).length < 1e-4 for n, loc in C["before_move"].items())
    lead = bpy.context.view_layer.objects.active
    check(f"one Ctrl+Z puts the moved objects back ({tuple(round(v, 3) for v in ob('box_b').location)} vs "
          f"{tuple(round(v, 3) for v in C['before_move']['box_b'])}) and keeps the lead "
          f"({lead.name if lead else None})", back and lead is not None and lead.name == "box_c")
    mod("operators.undo_pairs").push = C["real_push"]


run()
