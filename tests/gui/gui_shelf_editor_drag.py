"""Shelf Editor Drag in a real UI (Preferences > Shelf Editor Drag, off by default): a shelf with buttons A, B, C in
the Shelf Editor -> with the preference off no grips are drawn and the drag does nothing -> on, a real click on A's grip
picks A up, the mouse two rows down and a click drop it there (B, C, A) -> a second drag put back with Esc keeps the
order -> the clipboard text is the same all along. Shots with ``--shots``."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, load_maya_layout, run, setup, step  # noqa: E402

GUI_TIMEOUT = 200
SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}
CLIP = "clipboard text that must stay"
GRIP = (342, 103)        # A's grip in a shot of the editor at UI scale 1.25


def mod(name):
    return import_module(f"{MODULE}.{name}")


def editor():
    w = mod("ui.marked_window").find_window(bpy.context, "SHELF_EDITOR")
    if w is None:
        return None, None, None
    area = max(w.screen.areas, key=lambda a: a.width * a.height)
    return w, area, next(r for r in area.regions if r.type == 'WINDOW')


def labels():
    draft = mod("ui.shelf_editor_draft")
    return [b.get("label") for b in draft._draft_buttons(C["shelf"]) or []]


def ev(type, value, x, y):
    C["w"].event_simulate(type=type, value=value, x=int(x), y=int(y))


def again(fn, cond, limit=40):
    C.setdefault(fn.__name__, 0)
    if not cond() and C[fn.__name__] < limit:
        C[fn.__name__] += 1
        import sim
        sim._steps.insert(0, fn)
        return True
    return False


@step
def s_setup():
    setup()
    load_maya_layout()
    bpy.context.window_manager.clipboard = CLIP


for _i in range(6):
    step(lambda: None)


@step
def s_open():
    from sim import win
    main = win()
    area = max((a for a in main.screen.areas if a.type == 'VIEW_3D'), key=lambda a: a.width * a.height)
    with bpy.context.temp_override(window=main, area=area):
        bpy.ops.allset.shelf_editor_open()


@step
def s_wait_open():
    if again(s_wait_open, lambda: editor()[0] is not None):
        return
    w, area, region = editor()
    check("Shelf Editor window opened", w is not None)
    C["w"] = w
    with bpy.context.temp_override(window=w, area=area, region=region):
        bpy.ops.allset.shelf_editor_add_shelf('EXEC_DEFAULT', name="GuiDrag")
        for name in ("A", "B", "C"):
            bpy.ops.allset.shelf_editor_add_button()
            draft = mod("ui.shelf_editor_draft")
            C["shelf"] = bpy.context.window_manager.allset_se_shelf
            draft._draft_buttons(C["shelf"])[-1]["label"] = name
    C["x"], C["y"] = region.x + region.width // 3, region.y + region.height // 2
    ev('MOUSEMOVE', 'NOTHING', C["x"], C["y"])


def invoke_drag(index):
    w, area, region = editor()
    with bpy.context.temp_override(window=w, area=area, region=region):
        return bpy.ops.allset.shelf_editor_drag_button('INVOKE_DEFAULT', index=index)


@step
def s_off():
    prefs = mod("preferences").get()
    check("Shelf Editor Drag is off by default", prefs.shelf_editor_drag is False)
    check(f"off: the drag does nothing ({labels()})", invoke_drag(0) == {'CANCELLED'} and labels() == ["A", "B", "C"])
    if SHOTS:
        with bpy.context.temp_override(window=C["w"]):
            bpy.ops.screen.screenshot(filepath=os.path.join(SHOTS, "gui_shelf_editor_drag_off.png"))
    prefs.shelf_editor_drag = True


@step
def s_redrawn():
    pass


@step
def s_hover_grip():
    from sim import px
    if SHOTS:
        with bpy.context.temp_override(window=C["w"]):
            bpy.ops.screen.screenshot(filepath=os.path.join(SHOTS, "gui_shelf_editor_drag_on.png"))
    _w, _area, region = editor()
    # A's grip: the first Shelf Contents row, at its left edge (px from the region's top left at UI scale 1.25)
    C["x"], C["y"] = region.x + px(GRIP[0]), region.y + region.height - px(GRIP[1])
    ev('MOUSEMOVE', 'NOTHING', C["x"], C["y"])


@step
def s_click_grip():
    ev('LEFTMOUSE', 'PRESS', C["x"], C["y"])
    ev('LEFTMOUSE', 'RELEASE', C["x"], C["y"])


@step
def s_move():
    msg = bpy.context.window_manager.allset_se_message
    check(f"on: a click on A's grip picks it up ({msg!r})", msg.startswith("Click to drop"))
    row = mod("ui.shelf_editor_drag").row_px(bpy.context)
    ev('MOUSEMOVE', 'NOTHING', C["x"], C["y"] - row)
    ev('MOUSEMOVE', 'NOTHING', C["x"], C["y"] - 2 * row)


@step
def s_moving():
    check(f"A follows the mouse two rows down ({labels()})", labels() == ["B", "C", "A"])
    ev('LEFTMOUSE', 'PRESS', C["x"], C["y"] - 2 * mod("ui.shelf_editor_drag").row_px(bpy.context))
    ev('LEFTMOUSE', 'RELEASE', C["x"], C["y"] - 2 * mod("ui.shelf_editor_drag").row_px(bpy.context))


@step
def s_dropped():
    check(f"a click drops it there ({labels()})", labels() == ["B", "C", "A"])
    check("the dropped button is the selected one", bpy.context.window_manager.allset_se_index == 2)
    ev('MOUSEMOVE', 'NOTHING', C["x"], C["y"])
    C["again"] = invoke_drag(0)


@step
def s_move_again():
    row = mod("ui.shelf_editor_drag").row_px(bpy.context)
    ev('MOUSEMOVE', 'NOTHING', C["x"], C["y"] - row)


@step
def s_escape():
    C["mid"] = labels()
    ev('ESC', 'PRESS', C["x"], C["y"])
    ev('ESC', 'RELEASE', C["x"], C["y"])


@step
def s_put_back():
    check(f"the second drag moves B ({C['mid']})", C["again"] == {'RUNNING_MODAL'} and C["mid"] == ["C", "B", "A"])
    check(f"Esc puts it back ({labels()})", labels() == ["B", "C", "A"])
    check(f"the clipboard is untouched ({bpy.context.window_manager.clipboard!r})",
          bpy.context.window_manager.clipboard == CLIP)
    mod("preferences").get().shelf_editor_drag = False
    with bpy.context.temp_override(window=C["w"]):
        bpy.ops.allset.shelf_editor_cancel('EXEC_DEFAULT')


run()
