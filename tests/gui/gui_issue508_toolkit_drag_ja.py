"""In a real UI (#508): with the interface in Japanese, the UV Toolkit's selection style row reads ドラッグ for Drag
(the drag selection style), while Fields / Solvers > Drag keeps 抵抗 (screenshot of the UV Toolkit). The language is
switched in this sandbox only and put back at the end."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, run, setup, step, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def mod(name):
    return import_module(sys.modules["sim"].MODULE + name)


def uv_window():
    for w in bpy.context.window_manager.windows:
        for a in w.screen.areas:
            if a.ui_type == 'UV':
                return w, a, next(r for r in a.regions if r.type == 'WINDOW')
    return None, None, None


def shot(name, window=None):
    if SHOTS:
        with bpy.context.temp_override(window=window or win()):
            bpy.ops.screen.screenshot(filepath=os.path.join(SHOTS, name))


@step
def s_setup():
    C["x"], C["y"] = setup()
    view = bpy.context.preferences.view
    C["lang"] = (view.language, view.use_translate_interface)
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.mesh.primitive_grid_add(x_subdivisions=4, y_subdivisions=4, size=2.0)
        mod(".marking.modal").run_action(bpy.context, mod(".ui.menu_map").MAP["UV/UV Editor"])


@step
def s_wait_uv_window():
    import sim
    C.setdefault("wait_uv", 0)
    if uv_window()[1] is None and C["wait_uv"] < 15:
        C["wait_uv"] += 1
        sim._steps.insert(0, s_wait_uv_window)


@step
def s_japanese():
    items = {it.identifier for it in bpy.context.preferences.view.bl_rna.properties["language"].enum_items}
    C["ja"] = "ja_JP" in items
    if C["ja"]:
        view = bpy.context.preferences.view
        view.language, view.use_translate_interface = "ja_JP", True
    for w in bpy.context.window_manager.windows:
        for a in w.screen.areas:
            a.tag_redraw()


@step
def s_look():
    i18n = mod(".i18n")
    if not C["ja"]:
        check("ja_JP not in this build: skipped", True)
        return
    check("the toolkit row's Drag reads ドラッグ",
          bpy.app.translations.pgettext_iface("Drag", i18n.CTX_SELECT_STYLE) == "ドラッグ")
    check("Fields / Solvers > Drag keeps 抵抗 (the kit draws menu items itself)", i18n.iface("Drag") == "抵抗")
    shot("gui_issue508_uv_toolkit_ja.png", uv_window()[0])
    C["ctx"] = i18n.CTX_SELECT_STYLE
    i18n.CTX_SELECT_STYLE = "*"              # the row without its context (as a plain label), for comparison
    uv_window()[1].tag_redraw()


@step
def s_plain_row():
    if C.get("ja"):
        shot("gui_issue508_uv_toolkit_ja_plain_ctx.png", uv_window()[0])
        mod(".i18n").CTX_SELECT_STYLE = C["ctx"]


@step
def s_end():
    view = bpy.context.preferences.view
    view.language, view.use_translate_interface = C["lang"]
    check("UV Editor still open", uv_window()[1] is not None)


run()
