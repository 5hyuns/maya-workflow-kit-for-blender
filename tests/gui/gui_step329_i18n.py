"""Translations (#197) in a real UI: with Blender's interface language set to Japanese, then Simplified Chinese, the
Maya menu bar shows translated menu names, each sized by the label Blender actually draws (no truncation), a Maya
menu shows translated rows with the hotkey column and option boxes, and English comes back with the language.
Screenshots go to ALLSET_GUI_SHOTS when set. The language is changed in this sandbox session only (never saved).
"""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, load_maya_layout, run, screenshot, setup, step, tap, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def mod(name):
    return import_module(MODULE + name)


def shot(name):
    if SHOTS:
        screenshot(os.path.join(SHOTS, name + ".png"))


def redraw():
    mod(".ui.status_line").redraw_top_bars()
    for a in win().screen.areas:
        a.tag_redraw()


def set_language(locale):
    view = bpy.context.preferences.view
    config = os.path.normcase(os.path.abspath(bpy.utils.user_resource('CONFIG')))
    assert os.sep + "tmp" + os.sep in config, config        # sandbox preferences only
    view.language = locale
    view.use_translate_interface = True
    view.use_translate_tooltips = True
    redraw()


def bar_check(locale):
    import blf
    sl = mod(".ui.status_line")
    ms = mod(".ui.menu_sets")
    names, n = sl.shown_menus(win())
    check(f"{locale}: menu bar drawn ({n} of {len(names)} menus)", n > 0)
    prefs = bpy.context.preferences
    scale = prefs.system.ui_scale or 1.0
    with bpy.context.temp_override(window=win()):
        widths, _fixed, _more = sl.menu_bar_widths(bpy.context, list(names), False)
    blf.size(0, prefs.ui_styles[0].widget.points * scale)
    short = []
    translated = 0
    for name, w in zip(names[:n], widths):
        label = getattr(bpy.types, ms.menu_idname(name)).bl_label
        shown = bpy.app.translations.pgettext_iface(label)
        translated += shown != label
        if w < blf.dimensions(0, shown)[0] + 4 * scale:
            short.append((label, shown, w))
    check(f"{locale}: menu names translated ({translated} of {n})", translated >= n - 1)
    check(f"{locale}: every menu button is wider than its translated label ({short})", not short)
    ja = mod(".i18n").LANGUAGES[locale]
    _rows, texts = mod(".ui.option_click").rows("File")
    save_as = texts["File/Save Scene As..."]
    check(f"{locale}: File > Save Scene As... row = {save_as!r}", save_as.startswith(ja["Save Scene As..."]))


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_wait():
    redraw()


@step
def s_ja():
    set_language('ja_JP')


@step
def s_ja_draw():
    redraw()


@step
def s_ja_check():
    bar_check('ja_JP')
    shot("gui_step329_ja_bar")


@step
def s_ja_menu():
    area, region = view3d()
    ev('MOUSEMOVE', 'NOTHING', x=region.x + region.width // 3, y=region.y + region.height - 40)
    with bpy.context.temp_override(window=win(), area=area, region=region, space_data=area.spaces.active):
        bpy.ops.wm.call_menu(name=mod(".ui.menu_sets").menu_idname("mainEditMeshMenu"))


@step
def s_ja_menu_shot():
    shot("gui_step329_ja_edit_mesh")


@step
def s_ja_menu_close():
    tap('ESC')
    area, region = view3d()
    ev('MOUSEMOVE', 'NOTHING', x=region.x + region.width // 2, y=region.y + region.height // 2)


@step
def s_zh():
    set_language('zh_HANS')


@step
def s_zh_draw():
    redraw()


@step
def s_zh_check():
    bar_check('zh_HANS')
    shot("gui_step329_zh_bar")


@step
def s_en():
    set_language('en_US')


@step
def s_en_draw():
    redraw()


@step
def s_en_check():
    sl = mod(".ui.status_line")
    names, n = sl.shown_menus(win())
    check(f"English again: menu bar shows {n} menus", n > 0)
    _rows, texts = mod(".ui.option_click").rows("File")
    check("English again: File > Save Scene As...", texts["File/Save Scene As..."].startswith("Save Scene As..."))
    shot("gui_step329_en_bar")


run()
