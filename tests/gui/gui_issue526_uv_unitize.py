"""#526: cube -> UV Editor, every face selected, Modify > Unitize from the menu: every face sits on the 0-1 square as
its own shell. A click on the stack in UV Face mode picks one face, and moving it leaves every other face in place,
like Maya. Shots: ALLSET_GUI_SHOTS (after Unitize, after the move)."""

import os
import sys
import tempfile
from importlib import import_module

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, ev, run, setup, step, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def mod(name):
    return import_module(sys.modules["sim"].MODULE + name)


def cube():
    return bpy.data.objects["Cube"]


def uv_window():
    for w in bpy.context.window_manager.windows:
        for a in w.screen.areas:
            if a.ui_type == 'UV':
                return w, a, next(r for r in a.regions if r.type == 'WINDOW')
    return None, None, None


def redraw_all():
    for w in bpy.context.window_manager.windows:
        for a in w.screen.areas:
            a.tag_redraw()


def uvs():
    bm = bmesh.from_edit_mesh(cube().data)
    uv = bm.loops.layers.uv.active
    return {(f.index, k): l[uv].uv.copy() for f in bm.faces for k, l in enumerate(f.loops)}


def shot(name):
    w, _a, _r = uv_window()
    if w is None:
        return
    path = os.path.join(C.setdefault("dir", SHOTS or tempfile.mkdtemp()), name)
    with bpy.context.temp_override(window=w):
        bpy.ops.screen.screenshot(filepath=path)


@step
def s_setup():
    setup()
    bpy.context.view_layer.objects.active = cube()
    cube().select_set(True)
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        C["open"] = mod(".marking.modal").run_action(bpy.context, mod(".ui.menu_map").MAP["UV/UV Editor"])


@step
def s_wait_uv_window():
    import sim
    C.setdefault("wait_uv", 0)
    if uv_window()[1] is None and C["wait_uv"] < 15:
        C["wait_uv"] += 1
        sim._steps.insert(0, s_wait_uv_window)


@step
def s_unitize():
    w, a, r = uv_window()
    check(f"UV Editor window open ({C['open']})", a is not None and cube().mode == 'EDIT')
    if a is None:
        return
    ts = bpy.context.scene.tool_settings
    ts.use_uv_select_sync = True
    with bpy.context.temp_override(window=w, area=a, region=r):
        bpy.ops.mesh.select_all(action='SELECT')
        got = mod(".marking.modal").run_action(bpy.context, mod(".ui.editor_menu_map").MAP["UV Editor/Modify/Unitize"])
        bpy.ops.image.view_all(fit_view=True)
    check(f"Modify > Unitize ran ({got})", got == {'FINISHED'})
    after = uvs()
    check("every face on the 0-1 square", all(-1e-6 <= p.x <= 1 + 1e-6 and -1e-6 <= p.y <= 1 + 1e-6
                                              for p in after.values()))
    redraw_all()


@step
def s_shot_unitized():
    shot("gui_issue526_uv_unitize.png")


@step
def s_uv_face_mode():
    w, a, r = uv_window()
    with bpy.context.temp_override(window=w, area=a, region=r):
        bpy.ops.allset.uv_component(mode='UV_FACE')
    ts = bpy.context.scene.tool_settings
    check(f"UV Face mode (sync {ts.use_uv_select_sync}, {ts.uv_select_mode})",
          not ts.use_uv_select_sync and ts.uv_select_mode == 'FACE')


@step
def s_click_stack():
    w, a, r = uv_window()
    x, y = r.view2d.view_to_region(0.5, 0.5, clip=False)
    x, y = r.x + int(x), r.y + int(y)
    C["before"] = uvs()
    w.event_simulate(type='MOUSEMOVE', value='NOTHING', x=x, y=y)
    w.event_simulate(type='LEFTMOUSE', value='PRESS', x=x, y=y)
    w.event_simulate(type='LEFTMOUSE', value='RELEASE', x=x, y=y)


@step
def s_move_picked():
    bm = bmesh.from_edit_mesh(cube().data)
    uv = bm.loops.layers.uv.active
    compat = mod(".compat")
    picked = sorted({f.index for f in bm.faces for l in f.loops if compat.uv_vert_selected(l, uv)})
    check(f"the click picks one face's UVs ({picked})", len(picked) == 1)
    w, a, r = uv_window()
    with bpy.context.temp_override(window=w, area=a, region=r):
        bpy.ops.transform.translate(value=(0.6, 0.4, 0.0))
    after = uvs()
    moved = sorted({k[0] for k, p in after.items() if (p - C["before"][k]).length > 1e-6})
    check(f"only that face moved ({moved})", moved == picked)
    redraw_all()


@step
def s_wait():
    pass


@step
def s_shot_moved():
    shot("gui_issue526_uv_unitize_moved.png")


run()
