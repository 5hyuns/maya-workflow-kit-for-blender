"""In a real UI on every supported Blender: which theme colour an Image Editor header draws its text in (the one the
kit's shelf tabs follow); the shelf tab row on the Light and the Dark theme (screenshots); the Range Slider's Animation
Preferences > Keying popover draws Blender's keying settings."""

import os
import sys
import tempfile
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, screenshot, setup, step, win, load_maya_layout  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def shot(name):
    path = os.path.join(SHOTS or tempfile.gettempdir(), name)
    screenshot(path)
    return path


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


def theme_preset(word):
    for d in bpy.utils.preset_paths("interface_theme"):
        for f in sorted(os.listdir(d)):
            if word in f.lower() and f.endswith(".xml"):
                return os.path.join(d, f)
    return None


def count_colour(path, rect, rgb):
    """Pixels of the screenshot ``path`` inside the window rectangle ``rect`` (x, y, w, h) close to ``rgb``."""
    import numpy as np
    img = bpy.data.images.load(path, check_existing=False)
    try:
        w, h = img.size
        px = np.empty(w * h * 4, np.float32)
        img.pixels.foreach_get(px)
        px = px.reshape(h, w, 4)[..., :3]
        x, y, rw, rh = rect
        part = px[max(0, y):y + rh, max(0, x):x + rw]
        near = np.all(np.abs(part - np.array(rgb[:3], np.float32)) < 0.3, axis=-1)
        return int(near.sum())
    finally:
        bpy.data.images.remove(img)


@step
def s_setup():
    setup()


@step
def s_header_colours():
    # the factory Timeline becomes an Image Editor; its header text: red in the editor text colour, blue in the
    # separate header text colour where the theme has one
    area = next(a for a in win().screen.areas if a.type == 'DOPESHEET_EDITOR')
    C["area_type"] = (area, area.ui_type)
    area.ui_type = 'IMAGE_EDITOR'
    sp = bpy.context.preferences.themes[0].image_editor.space
    sp.text = sp.text_hi = (1.0, 0.0, 0.0)
    if hasattr(sp, "header_text"):
        sp.header_text = sp.header_text_hi = (0.0, 0.0, 1.0)
    # Blender draws header text in the separate header colour where the theme has one, else in the editor's text colour
    C["expected"] = (0.0, 0.0, 1.0) if hasattr(sp, "header_text") else (1.0, 0.0, 0.0)

    def label(self, _context):                 # a plain header label (menus draw in the menu widget colours)
        self.layout.label(text="WWWWWWWWWWWWWWWW")
    C["label"] = label
    bpy.types.IMAGE_HT_header.append(label)
    redraw()


@step
def s_wait():
    redraw()


@step
def s_header_shot():
    area, _t = C["area_type"]
    header = next(r for r in area.regions if r.type == 'HEADER')
    path = shot("gui_shelf_theme_header_colours.png")
    rect = (header.x, header.y, header.width, header.height)
    red = count_colour(path, rect, (1.0, 0.0, 0.0))
    blue = count_colour(path, rect, (0.0, 0.0, 1.0))
    exp = tuple(round(c, 2) for c in C["expected"])
    ours = red if exp == (1.0, 0.0, 0.0) else blue
    other = blue if exp == (1.0, 0.0, 0.0) else red
    check(f"the Image Editor header text is drawn in {exp}: {red} red / {blue} blue pixels",
          ours > 20 and other < ours // 10)
    bpy.types.IMAGE_HT_header.remove(C["label"])
    bpy.ops.preferences.reset_default_theme()
    area.ui_type = C["area_type"][1]


@step
def s_maya():
    load_maya_layout()


@step
def s_maya_ready():
    bpy.ops.allset.keymap_activate()
    redraw()


def theme_steps(word):
    @step
    def s_theme():
        path = theme_preset(word)
        check(f"Blender ships a {word} theme preset ({path})", path is not None)
        bpy.ops.script.execute_preset(filepath=path, menu_idname="USERPREF_MT_interface_theme_presets")
        redraw()

    @step
    def s_theme_wait():
        redraw()

    @step
    def s_theme_shot():
        sp = import_module(MODULE + ".ui.shelf_paint")
        shelf = import_module(MODULE + ".ui.shelf")
        row = shelf.shelf_row_area(win().screen)
        strip = shelf.strip_area(win().screen)
        base = sp._theme_colour(bpy.context)
        current, other, glyph = sp._text_colours(bpy.context)
        path = shot(f"gui_shelf_theme_{word}.png")
        rects = [(a.x, a.y, a.width, a.height) for a in (strip, row) if a is not None]
        luma = lambda c: 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]   # noqa: E731
        check(f"{word} theme: shelf tabs {tuple(round(c, 2) for c in current[:3])} / other "
              f"{tuple(round(c, 2) for c in other[:3])} on {tuple(round(c, 2) for c in base[:3])} "
              f"(rows {rects}, {os.path.basename(path)})", abs(luma(other) - luma(base)) > 0.3)


theme_steps("light")
theme_steps("dark")


@step
def s_keying_menu():
    bpy.ops.preferences.reset_default_theme()
    panel = bpy.types.TIME_PT_keyframing_settings        # the keying set rows (5.3: inside the Keyframing popover)
    C["draws"], C["errors"] = 0, []
    draw = panel.draw

    def record(self, context):
        C["draws"] += 1
        try:
            draw(self, context)
        except Exception as ex:
            C["errors"].append(repr(ex))
            raise
    panel.draw = record
    C["restore"] = (panel, draw)
    # the Range Slider's Animation Preferences menu, opened over the middle of the screen
    area = next(a for a in win().screen.areas if a.type == 'DOPESHEET_EDITOR' and a.spaces.active.mode == 'TIMELINE')
    region = next(r for r in area.regions if r.type == 'WINDOW')
    view = max((a for a in win().screen.areas if a.type == 'VIEW_3D'), key=lambda a: a.width * a.height)
    x, y = view.x + view.width // 2, view.y + view.height // 2
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.wm.call_menu(name="ALLSET_MT_anim_preferences")
    # Blender opens a called menu with its first item (Playback) under the mouse: Keying is the next row
    from sim import scale
    C["keying_xy"] = (x + 20, y - round(20 * scale()))


@step
def s_keying_hover():
    ev('MOUSEMOVE', 'NOTHING', x=C["keying_xy"][0], y=C["keying_xy"][1])


@step
def s_keying_click():
    ev('LEFTMOUSE', 'PRESS')
    ev('LEFTMOUSE', 'RELEASE')


@step
def s_keying_wait():
    redraw()


@step
def s_keying_shot():
    shot("gui_shelf_theme_keying.png")
    check(f"Animation Preferences > Keying opens Blender's keying settings ({C['draws']} draws, errors "
          f"{C['errors']})", C["draws"] > 0 and not C["errors"])
    panel, draw = C["restore"]
    panel.draw = draw
    ev('ESC', 'PRESS')
    ev('ESC', 'RELEASE')


run()
