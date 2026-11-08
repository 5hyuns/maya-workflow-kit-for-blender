"""#310: Windows > Settings/Preferences > Shelf Editor in a real UI: the editor opens as its own window at its
size (not a copy of the whole 3D View), the main layout is the same afterwards, a new shelf made in the editor is
in shelves.json after Save, and closing the window leaves the layout as it was. Screenshots: gui_issue310_main.png,
gui_issue310_shelf_editor.png (the editor window)."""

import json
import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, run, step, setup, screenshot, win, load_maya_layout  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}
TOL = 40       # split borders and the UI scale move the carved size by a few pixels
KIND = "marked:SHELF_EDITOR"


def mod(name):
    return import_module(f"{MODULE}.{name}")


def layout():
    return sorted((a.type, a.x, a.y, a.width, a.height) for a in win().screen.areas)


def editor_window():
    return next((w for w in bpy.context.window_manager.windows if w not in C["before"]), None)


@step
def s_setup():
    setup()
    load_maya_layout()


for _i in range(8):       # the layout settles (the kit fits its columns once after loading)
    step(lambda: None)


@step
def s_open():
    main = win()
    C["layout"] = layout()
    C["before"] = set(bpy.context.window_manager.windows[:])
    area = max((a for a in main.screen.areas if a.type == 'VIEW_3D'), key=lambda a: a.width * a.height)
    C["area"] = (area.width, area.height)
    check("the Shelf Editor opens only at its own size", KIND in mod("ui.window_places").STRICT)
    with bpy.context.temp_override(window=main, area=area):
        bpy.ops.allset.shelf_editor_open()
    wp = mod("ui.window_places")
    rect = wp.target_in_window(KIND, main, area)
    C["want"] = rect[2:] if rect else None


for _i in range(12):      # the place is carved one split per tick, then the window opens and the pieces close
    step(lambda: None)


@step
def s_check_open():
    w = editor_window()
    check("Shelf Editor window opened", w is not None)
    if w is None:
        return
    got = (w.width, w.height)
    want = C["want"]
    print("ISSUE310 want", want, "got", got, "3D View", C["area"], flush=True)
    check(f"the window has the editor's size {got} (want {want})",
          want is not None and abs(got[0] - want[0]) <= TOL and abs(got[1] - want[1]) <= TOL)
    check(f"not a copy of the whole 3D View {got} vs {C['area']}",
          got[0] < C["area"][0] - TOL or got[1] < C["area"][1] - TOL)
    check("the editor has a draft", mod("ui.shelf_editor")._draft is not None)
    check(f"main layout as before ({len(layout())} areas)", layout() == C["layout"])
    if SHOTS:
        screenshot(os.path.join(SHOTS, "gui_issue310_main.png"))
        with bpy.context.temp_override(window=w):
            bpy.ops.screen.screenshot(filepath=os.path.join(SHOTS, "gui_issue310_shelf_editor.png"))


@step
def s_add_and_save():
    w = editor_window()
    area = max(w.screen.areas, key=lambda a: a.width * a.height)
    with bpy.context.temp_override(window=w, area=area):
        bpy.ops.allset.shelf_editor_add_shelf('EXEC_DEFAULT', name="GuiShelf310")
        bpy.ops.allset.shelf_editor_save()
    path = mod("ui.shelf").store_path()
    data = json.load(open(path, encoding="utf-8")) if os.path.isfile(path) else {}
    names = [item.get("name") for item in data.get("shelves", [])]
    check(f"the new shelf is saved ({names})", "GuiShelf310" in names)


@step
def s_close():
    w = editor_window()
    with bpy.context.temp_override(window=w):
        bpy.ops.wm.window_close()


@step
def s_after_close():
    check("the editor window is closed", editor_window() is None)
    check("main layout as before", layout() == C["layout"])


run()
