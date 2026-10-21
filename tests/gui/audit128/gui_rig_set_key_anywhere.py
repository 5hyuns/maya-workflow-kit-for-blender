"""Audit 128 (rig/anim lane) repro: Maya's S (SetKey, Maya) is a global hotkey -- it keys every
keyable channel of the selection wherever the mouse is. In the kit S is only bound in the 3D View keymaps
("Object Mode" / "Pose"), so with the mouse over the Channel Box (IC "User Interface" S = anim.keyframe_insert_button
on the Scene proxy field) or over the Time Slider (IC Dopesheet S = action.keyframe_insert, existing curves only) a
never-keyed pCube1 gets no key.  flagged the Channel Box case as .
Each check PASSES once S keys the selection there too."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sim import MODULE, check, dock_area, ev, find_button, run, setup, step, tap, win, load_maya_layout  # noqa: E402

GUI_TIMEOUT = 200
C = {}


def mod(name):
    return import_module(MODULE + name)


def v3d():
    area = max((a for a in win().screen.areas if a.type == 'VIEW_3D'), key=lambda a: a.width * a.height)
    return area, next(r for r in area.regions if r.type == 'WINDOW')


def timeline():
    for area in win().screen.areas:
        if area.type == 'DOPESHEET_EDITOR' and area.spaces.active.mode == 'TIMELINE':
            return area, next(r for r in area.regions if r.type == 'WINDOW')
    return None, None


def outliner():
    for area in win().screen.areas:
        if area.type == 'OUTLINER':
            return area, next(r for r in area.regions if r.type == 'WINDOW')
    return None, None


def cube():
    return bpy.data.objects.get(C.get("ob", ""))


def curves():
    ob = cube()
    fcs = mod(".compat").id_fcurves(ob) if ob is not None and ob.animation_data else []
    return sorted({f"{fc.data_path}[{fc.array_index}]" for fc in fcs})


def scene_curves():
    ad = bpy.context.scene.animation_data
    if ad is None:
        return []
    return [f"{fc.data_path}" for fc in mod(".compat").id_fcurves(bpy.context.scene)]


def dock():
    area = dock_area()
    return area, next(r for r in area.regions if r.type == 'WINDOW')


@step
def s_setup():
    setup()
    bpy.ops.allset.make_maya(open_layout=False)
    load_maya_layout()


@step
def s_scene():
    bpy.ops.allset.keymap_activate()
    area, region = v3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.allset.create(kind='CUBE')
    C["ob"] = bpy.context.active_object.name
    bpy.context.scene.frame_set(1)
    bpy.context.window_manager.allset_dock = 'CHANNEL_BOX'
    for a in win().screen.areas:
        a.tag_redraw()


@step
def s_wait():
    for a in win().screen.areas:
        a.tag_redraw()


step(find_button(dock, lambda path, cmd: "allset_cb" in path and "tx" in path, C, "tx", step_px=6, x_frac=0.75))


@step
def s_hover_cb():
    check(f"found the Channel Box Translate X field ({C.get('tx')})", C.get("tx") is not None)
    if C.get("tx"):
        ev('MOUSEMOVE', 'NOTHING', x=C["tx"][0], y=C["tx"][1])


@step
def s_s_over_cb():
    if C.get("tx"):
        tap('S')


@step
def s_cb_result():
    got = curves()
    check(f"S with the mouse over the Channel Box keys pCube1 like Maya (curves {got}, Scene curves "
          f"{scene_curves()})", len(got) >= 9 and not scene_curves())
    ob = cube()
    if ob is not None:
        ob.animation_data_clear()
    area, region = timeline()
    if region is not None:
        ev('MOUSEMOVE', 'NOTHING', x=region.x + region.width // 2, y=region.y + region.height // 2)


@step
def s_s_over_timeline():
    tap('S')


@step
def s_timeline_result():
    got = curves()
    check(f"S with the mouse over the Time Slider keys pCube1 like Maya (curves {got}, frame "
          f"{bpy.context.scene.frame_current})", len(got) >= 9)
    ob = cube()
    if ob is not None:
        ob.animation_data_clear()
    area, region = outliner()
    if region is not None:
        ev('MOUSEMOVE', 'NOTHING', x=region.x + region.width // 2, y=region.y + region.height // 3)


@step
def s_s_over_outliner():
    tap('S')


@step
def s_outliner_result():
    got = curves()
    check(f"S with the mouse over the Outliner keys pCube1 like Maya (curves {got})", len(got) >= 9)
    area, region = v3d()
    ev('MOUSEMOVE', 'NOTHING', x=region.x + region.width // 2, y=region.y + region.height // 2)
    cube().animation_data_clear()


@step
def s_s_over_view():
    tap('S')


@step
def s_view_result():
    got = curves()
    check(f"control: S over the viewport keys pCube1 (curves {got})", len(got) >= 9)


run()
