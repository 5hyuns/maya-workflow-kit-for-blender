"""Issue #402: in a real UI, Skin > Mirror Skin Weights' option box (in object mode and while painting skin weights)
opens the Mirror Skin Weights Options window and mirrors nothing until its Mirror button; Mirror with Direction
"Positive to negative" off copies the -X side onto +X."""

import os
import sys
from importlib import import_module

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, load_maya_layout, run, screenshot, setup, step, tap, win  # noqa: E402

GUI_TIMEOUT = 200
PATH = "Skin/Mirror Skin Weights"
C = {}
SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")


def mod(name):
    return import_module(MODULE + name)


def main_view():
    toolbox = mod(".ui.toolbox")
    areas = [a for a in win().screen.areas if a.type == 'VIEW_3D' and not toolbox.is_toolbox(a.spaces.active)]
    area = max(areas, key=lambda a: a.width * a.height)
    return area, next(r for r in area.regions if r.type == 'WINDOW')


def override():
    area, r = main_view()
    return bpy.context.temp_override(window=win(), area=area, region=r)


def grid():
    return bpy.data.objects["grid"]


def snapshot():
    g = grid()
    return [sorted((g.vertex_groups[e.group].name, round(e.weight, 5)) for e in v.groups) for v in g.data.vertices]


def weight(v, name):
    g = grid()
    idx = g.vertex_groups[name].index
    return next((e.weight for e in v.groups if e.group == idx), 0.0)


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_scene():
    joints = mod(".operators.joints")
    k = mod(".operators.units").maya_unit()
    with override():
        arm = joints.new_skeleton(bpy.context)
        root = joints.add_joint(arm, Vector((0, 0, 0)), None, length=0.5 * k)
        left = joints.add_joint(arm, Vector((k, 0, 0)), root, length=0.5 * k)
        right = joints.add_joint(arm, Vector((-k, 0, 0)), root, length=0.5 * k)
        eb = arm.data.edit_bones
        eb[left].name, eb[right].name, eb[root].name = "jointL", "jointR", "joint1"
        joints.finish(bpy.context, arm, ["joint1", "jointL", "jointR"])
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.mesh.primitive_grid_add(x_subdivisions=8, y_subdivisions=2, size=3.0 * k)
        g = bpy.context.active_object
        g.name = "grid"
        for ob in (arm, g):
            ob.select_set(True)
        bpy.context.view_layer.objects.active = g
        bpy.ops.allset.bind_skin()
        for v in g.data.vertices:
            for vg in g.vertex_groups:
                vg.remove([v.index])
            g.vertex_groups["jointL" if v.co.x > 1e-9 else "joint1"].add([v.index], 1.0, 'REPLACE')
        bpy.ops.object.select_all(action='DESELECT')
        g.select_set(True)
        bpy.context.view_layer.objects.active = g
        bpy.ops.allset.frame(selected=False)
    C["start"] = snapshot()
    _a, r = main_view()
    ev('MOUSEMOVE', 'NOTHING', x=r.x + r.width // 2, y=r.y + r.height // 2)


def _open(label):
    @step
    def s_open():
        with override():
            res = bpy.ops.allset.menu_option_box('INVOKE_DEFAULT', item=PATH)
        check(f"{label}: the option box opens ({res})", res in ({'FINISHED'}, {'RUNNING_MODAL'}))
        check(f"{label}: the option box is Maya's Mirror Skin Weights Options window",
              mod(".ui.menu_sets").option_kind(PATH) == "window")

    @step
    def s_wait():
        pass

    @step
    def s_untouched():
        check(f"{label} ({bpy.context.mode}): opening the options mirrors nothing", snapshot() == C["start"])
        if SHOTS:
            screenshot(os.path.join(SHOTS, f"gui_issue402_{label}.png"))
        tap('ESC')
    s_open.__name__, s_wait.__name__, s_untouched.__name__ = (f"s_{label}_open", f"s_{label}_wait",
                                                               f"s_{label}_untouched")


_open("object")


@step
def s_paint():
    with override():
        bpy.ops.allset.paint_skin_weights()
    check(f"painting ({bpy.context.mode})", bpy.context.mode == 'PAINT_WEIGHT')


_open("painting")


@step
def s_mirror_back():
    ow = mod(".operators.option_windows")
    with override():
        res = ow.run(ow.find_path(PATH), bpy.context, {"positive_to_negative": False})
    check(f"Mirror, Direction off ({res})", isinstance(res, set) and 'FINISHED' in res)
    g = grid()
    plus = [v for v in g.data.vertices if v.co.x > 1e-9]
    check("-X is copied onto +X", plus and all(abs(weight(v, "joint1") - 1.0) < 1e-4 and weight(v, "jointL") < 1e-4
                                               for v in plus))


run()
