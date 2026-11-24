"""In a real UI (#535): the UV Toolkit with every section open draws without an error, from
the top (Selection, Pinning, Select By Type) to the bottom (Arrange and Layout, UV Sets); screenshots while
scrolling down."""
import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, run, setup, step, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {"draws": 0, "errors": []}


def mod(name):
    return import_module(sys.modules["sim"].MODULE + name)


def uv_window():
    for w in bpy.context.window_manager.windows:
        for a in w.screen.areas:
            if a.ui_type == 'UV':
                return w, a, next(r for r in a.regions if r.type == 'WINDOW')
    return None, None, None


@step
def s_setup():
    setup()
    tk = mod(".ui.uv_toolkit")
    section, panel = tk._section, tk.ALLSET_PT_uv_toolkit
    tk._section = lambda layout, idname, label, default_closed=True: section(layout, idname, label, False)
    draw = panel.draw

    def counted(self, context):
        try:
            draw(self, context)
            if context.mode == 'EDIT_MESH':
                C["draws"] += 1
        except Exception as ex:      # noqa: BLE001 - the test reports any drawing error
            C["errors"].append(repr(ex))
            raise
    panel.draw = counted
    C["undo"] = (tk, section, panel, draw)
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.mesh.primitive_cube_add()
        mod(".marking.modal").run_action(bpy.context, mod(".ui.menu_map").MAP["UV/UV Editor"])


@step
def s_wait():
    import sim
    C.setdefault("w", 0)
    if uv_window()[1] is None and C["w"] < 15:
        C["w"] += 1
        sim._steps.insert(0, s_wait)


@step
def s_open():
    w, a, r = uv_window()
    check(f"UV > UV Editor opens a UV Editor window ({a is not None})", a is not None)
    if a is None:
        return
    a.spaces.active.show_region_ui = True
    for x in a.regions:
        x.tag_redraw()


def _shot(i):
    @step
    def s_shot():
        w, a, r = uv_window()
        ui = next(x for x in a.regions if x.type == 'UI')
        if SHOTS:
            with bpy.context.temp_override(window=w):
                bpy.ops.screen.screenshot(filepath=os.path.join(SHOTS, f"gui_issue535_uv_toolkit_{i}.png"))
        with bpy.context.temp_override(window=w, area=a, region=ui):
            for _ in range(12):
                bpy.ops.view2d.scroll_down()
        a.tag_redraw()
    return s_shot


for _i in range(6):
    _shot(_i)


@step
def s_check():
    tk, section, panel, draw = C["undo"]
    tk._section, panel.draw = section, draw
    check(f"the toolkit drew every section in edit mode ({C['draws']} draws)", C["draws"] > 0)
    check(f"no drawing error ({C['errors'][:2]})", not C["errors"])


run()
