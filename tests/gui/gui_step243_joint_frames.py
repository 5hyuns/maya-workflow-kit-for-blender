"""Step 243 (Issue #160) in a real UI, chain ③ (research/maya/re/joint_rig_2026_joint_math.md §3):
Joint Tool 3 clicks (a bent chain) -> W (Edit + Move) -> click joint2 -> W-drag: joint2 + joint3 move, every joint's
Maya frame stays (joint1's bone still reaches joint2 but its Maya X keeps its direction) -> the Channel Box shows
joint2's Translate -> Ctrl+Z / Shift+Z keep the frames -> D held + drag = Preserve Children (joint3 stays) ->
save + open keeps the frames."""

import os
import sys
import tempfile
from importlib import import_module

import bpy
from bpy_extras import view3d_utils

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from sim import MODULE, check, ev, load_maya_layout, run, screenshot, setup, step, tap, win  # noqa: E402
import maya2026_rig as rig  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def mod(name):
    return import_module(MODULE + name)


def shot(name):
    if SHOTS:
        screenshot(os.path.join(SHOTS, f"gui_step243_{name}.png"))


def main_view():
    toolbox = mod(".ui.toolbox")
    areas = [a for a in win().screen.areas if a.type == 'VIEW_3D' and not toolbox.is_toolbox(a.spaces.active)]
    area = max(areas, key=lambda a: a.width * a.height)
    return area, next(r for r in area.regions if r.type == 'WINDOW')


def screen_of(world):
    _a, r = main_view()
    p = view3d_utils.location_3d_to_region_2d(r, r.data, world)
    return int(r.x + p.x), int(r.y + p.y)


def at(f, g):
    _a, r = main_view()
    return r.x + int(r.width * f), r.y + int(r.height * g)


def rig_ob():
    return bpy.data.objects[C["rig"]]


def heads():
    ob = rig_ob()
    if ob.mode == 'EDIT':
        return {eb.name: ob.matrix_world @ eb.head for eb in ob.data.edit_bones}
    return {b.name: ob.matrix_world @ b.head_local for b in ob.data.bones}


def frames():
    ob = rig_ob()
    return {n: rig.joint_world(ob, n)[1] for n in C["names"]}


def frame_err(a, b):
    return max(max((a[n].col[i] - b[n].col[i]).length for i in range(3)) for n in a)


@step
def s_setup():
    setup()
    bpy.ops.allset.make_maya(open_layout=False)
    load_maya_layout()


@step
def s_clean():
    for ob in list(bpy.data.objects):
        if ob.type in {'MESH', 'ARMATURE'}:
            bpy.data.objects.remove(ob)
    area, region = main_view()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.allset.joint_tool('INVOKE_DEFAULT')


def click(name, p):
    @step
    def s_click():
        x, y = p()
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
        ev('LEFTMOUSE', 'PRESS', x=x, y=y)
        ev('LEFTMOUSE', 'RELEASE', x=x, y=y)
    s_click.__name__ = name


click("s_j1", lambda: at(0.40, 0.30))
click("s_j2", lambda: at(0.48, 0.50))
click("s_j3", lambda: at(0.42, 0.72))


@step
def s_w():
    tap('W')


@step
def s_placed():
    arms = [o for o in bpy.data.objects if o.type == 'ARMATURE']
    check(f"Joint Tool made one skeleton ({len(arms)})", len(arms) == 1)
    C["rig"] = arms[0].name
    C["names"] = [b.name for b in rig_ob().data.bones][:3]
    check(f"W: Edit mode ({bpy.context.mode})", bpy.context.mode == 'EDIT_ARMATURE')


def pick(name):
    @step
    def s_pick():
        j2 = C["names"][1]
        x, y = screen_of(heads()[j2])
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
        ev('LEFTMOUSE', 'PRESS', x=x, y=y)
        ev('LEFTMOUSE', 'RELEASE', x=x, y=y)
    s_pick.__name__ = name


def drag(prefix, dx):
    @step
    def s_press():
        C["h0"], C["f0"] = heads(), frames()
        j2 = C["names"][1]
        x, y = screen_of(C["h0"][j2])
        C["drag"] = (x, y)
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
        ev('LEFTMOUSE', 'PRESS', x=x, y=y)
    s_press.__name__ = f"{prefix}_press"
    for i in range(1, 6):
        @step
        def s_move(i=i):
            x, y = C["drag"]
            ev('MOUSEMOVE', 'NOTHING', x=x + dx * i, y=y)
        s_move.__name__ = f"{prefix}_move{i}"

    @step
    def s_release():
        x, y = C["drag"]
        ev('LEFTMOUSE', 'RELEASE', x=x + dx * 5, y=y)
    s_release.__name__ = f"{prefix}_release"

    @step
    def s_settle():
        pass                                   # the 0.05 s frame watch runs between ticks
    s_settle.__name__ = f"{prefix}_settle"


pick("s_pick_j2")
drag("s_w", 12)


@step
def s_moved():
    j1, j2, j3 = C["names"]
    h = heads()
    d2, d3 = h[j2] - C["h0"][j2], h[j3] - C["h0"][j3]
    check(f"W-drag moves joint2 ({d2.length:.3f}), joint3 follows ({(d2 - d3).length:.1e}), joint1 stays",
          d2.length > 1e-3 and (d2 - d3).length < 1e-5 and (h[j1] - C["h0"][j1]).length < 1e-6)
    err = frame_err(frames(), C["f0"])
    check(f"every joint keeps its Maya frame (Maya: jointOrient unchanged) ({err:.1e})", err < 1e-5)
    ob = rig_ob()
    eb1 = ob.data.edit_bones[j1]
    check("joint1's bone still reaches joint2", (ob.matrix_world @ eb1.tail - h[j2]).length < 1e-5)
    scene = bpy.context.scene
    je = mod(".operators.joint_edit")
    t = je.joint_translate(ob.data.edit_bones[j2])
    shown = mod(".ui.cb_entry").format_value(t.x, "LENGTH", scene)     # display units = Maya units
    check(f"Channel Box: joint2 Translate X = {scene.allset_joint_tx} (parent frame, Maya units; {shown})",
          scene.allset_joint_tx != "" and scene.allset_joint_tx == shown)
    C["h1"], C["f1"] = h, frames()
    check(f"Channel Box: Translate Y / Z no longer 0 (joint1's frame kept) ({scene.allset_joint_ty}, "
          f"{scene.allset_joint_tz})", (scene.allset_joint_ty, scene.allset_joint_tz) != ("0", "0"))


@step
def s_shot_w():
    shot("01_w_drag")                          # screen.screenshot shows the previous tick


@step
def s_undo():
    ev('Z', 'PRESS', ctrl=True)
    ev('Z', 'RELEASE', ctrl=True)


@step
def s_undone():
    j2 = C["names"][1]
    err = frame_err(frames(), C["f0"])
    check(f"Ctrl+Z: joint2 back, frames back ({(heads()[j2] - C['h0'][j2]).length:.1e}, {err:.1e})",
          (heads()[j2] - C["h0"][j2]).length < 1e-5 and err < 1e-5)
    ev('Z', 'PRESS', shift=True)
    ev('Z', 'RELEASE', shift=True)


@step
def s_redo_settle():
    pass


@step
def s_redone():
    j2 = C["names"][1]
    err = frame_err(frames(), C["f0"])
    check(f"Shift+Z: moved again with the Maya frames kept ({err:.1e})",
          (heads()[j2] - C["h1"][j2]).length < 1e-5 and err < 1e-5)
    x, y = screen_of(heads()[j2])
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('D', 'PRESS', x=x, y=y)


@step
def s_d_held():
    ts = bpy.context.scene.tool_settings
    ebs = rig_ob().data.edit_bones
    j2, j3 = C["names"][1:]
    check(f"D held: Preserve Children on, joint2 picked alone ({ts.use_transform_skip_children})",
          ts.use_transform_skip_children and ebs[j2].select_head and not ebs[j3].select)


drag("s_d", -10)


@step
def s_d_moved():
    j1, j2, j3 = C["names"]
    h = heads()
    err = frame_err(frames(), C["f0"])
    check(f"D + drag: joint2 moves ({(h[j2] - C['h0'][j2]).length:.3f}), joint3 and joint1 stay, frames kept ({err:.1e})",
          (h[j2] - C["h0"][j2]).length > 1e-3 and (h[j3] - C["h0"][j3]).length < 1e-6
          and (h[j1] - C["h0"][j1]).length < 1e-6 and err < 1e-5)
    shot("02_d_drag")
    x, y = C["drag"]
    ev('D', 'RELEASE', x=x, y=y)


@step
def s_d_released():
    ts = bpy.context.scene.tool_settings
    check("D released: Preserve Children off again", not ts.use_transform_skip_children)
    C["final"] = frames()
    path = os.path.join(tempfile.mkdtemp(prefix="allset243_"), "frames.blend")
    C["path"] = path
    area, region = main_view()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.wm.save_as_mainfile(filepath=path, copy=True)
    bpy.ops.wm.open_mainfile(filepath=path, load_ui=False)


@step
def s_reopened():
    err = frame_err(frames(), C["final"])
    check(f"save + open keeps the Maya frames ({err:.1e})", err < 1e-5)
    shot("03_reopened")


run()
