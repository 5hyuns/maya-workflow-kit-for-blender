"""Joint Tool feedback while placing joints (#230), in a factory scene (metres) and in the Maya Workflow Kit layout
(cm scene): a press places the joint and, while the button is held, dragging moves it with the pointer (release fixes
it); while the tool runs a preview shows the placed joints, the bones between them and the next bone from the last
joint to the pointer; the preview is gone after Enter."""

import os
import sys
from importlib import import_module

import bpy
from bpy_extras import view3d_utils

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, load_maya_layout, run, screenshot, setup, step, tap, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def mod(name):
    return import_module(MODULE + name)


def shot(name):
    if SHOTS:
        screenshot(os.path.join(SHOTS, f"{C['tag']}_{name}.png"))


def main_view():
    toolbox = mod(".ui.toolbox")
    areas = [a for a in win().screen.areas if a.type == 'VIEW_3D' and not toolbox.is_toolbox(a.spaces.active)]
    area = max(areas, key=lambda a: a.width * a.height)
    return area, next(r for r in area.regions if r.type == 'WINDOW')


def at(f, g):
    _a, r = main_view()
    return r.x + int(r.width * f), r.y + int(r.height * g)


def running():
    return any(op.bl_idname == "ALLSET_OT_joint_tool" for op in win().modal_operators)


def preview_on():
    try:
        return bool(mod(".operators.joint_preview")._handles)
    except ImportError:
        return False


def skeleton():
    return next((o for o in bpy.data.objects if o.type == 'ARMATURE'), None)


def head_px(name):
    """Window position of joint ``name``'s head (edit bones while the tool runs)."""
    ob = skeleton()
    area, region = main_view()
    bones = ob.data.edit_bones if ob.mode == 'EDIT' else ob.data.bones
    b = bones[name]
    head = b.head if ob.mode == 'EDIT' else b.head_local
    p = view3d_utils.location_3d_to_region_2d(region, area.spaces.active.region_3d, ob.matrix_world @ head)
    return (region.x + p.x, region.y + p.y) if p is not None else None


def near(p, q, tol=3.0):
    return p is not None and abs(p[0] - q[0]) <= tol and abs(p[1] - q[1]) <= tol


def scene(tag, maya_layout):
    @step
    def prepare():
        C["tag"] = tag
        if maya_layout:
            load_maya_layout()
    prepare.__name__ = f"s_{tag}_prepare"

    @step
    def start():
        if not maya_layout:
            bpy.ops.allset.make_maya(open_layout=False)
        for ob in list(bpy.data.objects):
            if ob.type in {'MESH', 'ARMATURE'}:
                bpy.data.objects.remove(ob)
        area, region = main_view()
        with bpy.context.temp_override(window=win(), area=area, region=region):
            bpy.ops.allset.joint_tool('INVOKE_DEFAULT')
        ev('MOUSEMOVE', 'NOTHING', x=at(0.30, 0.30)[0], y=at(0.30, 0.30)[1])
    start.__name__ = f"s_{tag}_start"

    @step
    def hover0():
        check(f"{tag}: the tool runs", running())
        check(f"{tag}: the preview is drawn while the tool runs", preview_on())
        shot("0_hover")
    hover0.__name__ = f"s_{tag}_hover0"

    @step
    def press():
        x, y = at(0.30, 0.30)
        ev('LEFTMOUSE', 'PRESS', x=x, y=y)
    press.__name__ = f"s_{tag}_press"

    @step
    def pressed():
        shot("1_pressed")
        x, y = at(0.36, 0.33)
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    pressed.__name__ = f"s_{tag}_pressed"

    @step
    def drag():
        x, y = at(0.42, 0.36)
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    drag.__name__ = f"s_{tag}_drag"

    @step
    def dragged():
        ob = skeleton()
        check(f"{tag}: the press made a skeleton", ob is not None and len(ob.data.edit_bones) == 1)
        name = ob.data.edit_bones[0].name if ob is not None and ob.data.edit_bones else None
        C["first"] = name
        p = head_px(name) if name else None
        check(f"{tag}: while held, the joint follows the pointer ({p} vs {at(0.42, 0.36)})", near(p, at(0.42, 0.36)))
        shot("2_dragged")
        x, y = at(0.42, 0.36)
        ev('LEFTMOUSE', 'RELEASE', x=x, y=y)
    dragged.__name__ = f"s_{tag}_dragged"

    @step
    def released():
        p = head_px(C["first"]) if C.get("first") else None
        check(f"{tag}: release keeps the joint where it was dragged ({p})", near(p, at(0.42, 0.36)))
        x, y = at(0.55, 0.40)
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    released.__name__ = f"s_{tag}_released"

    @step
    def hover1():
        shot("3_hover_next")
        x, y = at(0.55, 0.40)
        ev('LEFTMOUSE', 'PRESS', x=x, y=y)
        ev('LEFTMOUSE', 'RELEASE', x=x, y=y)
    hover1.__name__ = f"s_{tag}_hover1"

    @step
    def second():
        ob = skeleton()
        names = [b.name for b in ob.data.edit_bones] if ob is not None else []
        check(f"{tag}: a click places the second joint ({names})", len(names) == 2)
        # dragging the second joint: its parent bone follows
        x, y = at(0.60, 0.55)
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
        ev('LEFTMOUSE', 'PRESS', x=x, y=y)
    second.__name__ = f"s_{tag}_second"

    @step
    def drag3():
        x, y = at(0.66, 0.62)
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    drag3.__name__ = f"s_{tag}_drag3"

    @step
    def dragged3():
        ob = skeleton()
        ebs = ob.data.edit_bones
        last = [b for b in ebs if not b.children]
        p = head_px(last[0].name) if last else None
        par = last[0].parent if last else None
        check(f"{tag}: the third joint follows the pointer ({p})", near(p, at(0.66, 0.62)))
        check(f"{tag}: the bone from the previous joint follows it",
              par is not None and (par.tail - last[0].head).length < 1e-5)
        shot("4_dragged_third")
        x, y = at(0.66, 0.62)
        ev('LEFTMOUSE', 'RELEASE', x=x, y=y)
        x, y = at(0.75, 0.50)
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    dragged3.__name__ = f"s_{tag}_dragged3"

    @step
    def hover3():
        shot("5_hover_fourth")
        x, y = at(0.75, 0.50)
        ev('LEFTMOUSE', 'PRESS', x=x, y=y)
        ev('LEFTMOUSE', 'RELEASE', x=x, y=y)
    hover3.__name__ = f"s_{tag}_hover3"

    @step
    def enter():
        shot("6_four_joints")
        x, y = at(0.5, 0.15)
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
        tap('RET')
    enter.__name__ = f"s_{tag}_enter"

    @step
    def done():
        ob = skeleton()
        check(f"{tag}: Enter ended the tool", not running())
        check(f"{tag}: the preview is gone after Enter", not preview_on())
        check(f"{tag}: four joints ({len(ob.data.bones) if ob else None})", ob is not None and len(ob.data.bones) == 4)
        check(f"{tag}: pose mode after Enter ({ob.mode if ob else None})", ob is not None and ob.mode == 'POSE')
        shot("7_after_enter")
    done.__name__ = f"s_{tag}_done"


@step
def s_setup():
    setup()


scene("factory", maya_layout=False)
scene("maya", maya_layout=True)


@step
def s_esc_cancels_preview():
    area, region = main_view()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.allset.joint_tool('INVOKE_DEFAULT')
    x, y = at(0.5, 0.5)
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)


@step
def s_esc():
    check("a second run draws the preview again", preview_on())
    tap('ESC')


@step
def s_esc_done():
    check("Esc with no joint ends the tool", not running())
    check("the preview is gone after Esc", not preview_on())


run()
