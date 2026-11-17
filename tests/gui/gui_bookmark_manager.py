"""Time Slider Bookmarks in a real UI: two bookmarks -> Visualize > Time Slider Bookmarks > Bookmark Manager opens a
kit window with one marked area -> a bookmark's name typed over in its row renames it (range and colour kept) -> the
Show Bookmarks button in the top bar hides them -> Edit (the dialog opens filled with the bookmark at the current
time; Return keeps it as it was). Shots with ``--shots``."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, load_maya_layout, px, run, setup, step, tap, win  # noqa: E402

GUI_TIMEOUT = 200
SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}
BLUE = (0.1, 0.2, 0.9)


def mod(name):
    return import_module(MODULE + name)


def shot(name, window=None):
    if SHOTS:
        with bpy.context.temp_override(window=window or win()):
            bpy.ops.screen.screenshot(filepath=os.path.join(SHOTS, name))


def redraw():
    for w in bpy.context.window_manager.windows:
        for a in w.screen.areas:
            a.tag_redraw()


def again(fn, cond, limit=40):
    C.setdefault(fn.__name__, 0)
    if not cond() and C[fn.__name__] < limit:
        C[fn.__name__] += 1
        import sim
        sim._steps.insert(0, fn)
        redraw()
        return True
    return False


def bm_area():
    mw = mod(".ui.marked_window")
    w = mw.find_window(bpy.context, "BOOKMARK_MANAGER")
    if w is None:
        return None, None, None
    area = next(a for a in w.screen.areas if mw.kind_of(a) == "BOOKMARK_MANAGER")
    return w, area, next(r for r in area.regions if r.type == 'WINDOW')


def mev(type, value, x, y, **kw):
    C["w"].event_simulate(type=type, value=value, x=int(x), y=int(y), **kw)


def at(x, y_from_top):
    """Window px of a Manager point given in px from its region's top left at UI scale 1.25 (read off a shot)."""
    _w, _area, region = bm_area()
    return region.x + px(x), region.y + region.height - px(y_from_top)


def click(key):
    x, y = C[key]
    mev('LEFTMOUSE', 'PRESS', x, y)
    mev('LEFTMOUSE', 'RELEASE', x, y)


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_scene():
    bm = mod(".operators.bookmarks")
    sc = bpy.context.scene
    sc.timeline_markers.clear()
    sc.frame_start, sc.frame_end = 1, 120
    bm.create(bpy.context, "walk", 10, 30, BLUE)
    bm.create(bpy.context, "run", 50, 70)
    sc.frame_current = 20
    area = max((a for a in win().screen.areas if a.type == 'VIEW_3D'), key=lambda a: a.width * a.height)
    region = next(r for r in area.regions if r.type == 'WINDOW')
    with bpy.context.temp_override(window=win(), area=area, region=region):
        C["open"] = bpy.ops.allset.menu_item(item="Visualize/Time Slider Bookmarks/Bookmark Manager")


@step
def s_open():
    if again(s_open, lambda: bm_area()[0] is not None):
        return
    w, area, _region = bm_area()
    check(f"Bookmark Manager opens a kit window ({C['open']})", w is not None)
    C["w"] = w
    check("one marked area, no Blender header", w is not None and len(w.screen.areas) == 1
          and not area.spaces.active.show_region_header)


@step
def s_hover_name():
    shot("gui_bookmark_manager_open.png", C["w"])
    C["name"] = at(230, 66)           # the first row's name field (rows in start order: walk first)
    mev('MOUSEMOVE', 'NOTHING', *C["name"])


@step
def s_click_name():
    click("name")


@step
def s_type():
    x, y = C["name"]
    mev('A', 'PRESS', x, y, ctrl=True)
    mev('A', 'RELEASE', x, y, ctrl=True)
    for ch in "jog":
        mev('TEXTINPUT', 'PRESS', x, y, unicode=ch)


@step
def s_enter():
    x, y = C["name"]
    mev('RET', 'PRESS', x, y)
    mev('RET', 'RELEASE', x, y)


@step
def s_renamed():
    bm = mod(".operators.bookmarks")
    sc = bpy.context.scene
    m = sc.timeline_markers.get("jog")
    check(f"the first row (walk) is renamed in place ({[x.name for x in sc.timeline_markers]})",
          m is not None and "walk" not in sc.timeline_markers)
    check("its range and colour stay", m is not None and bm.bookmark_range(sc, m) == (10, 30)
          and all(abs(a - b) < 1e-4 for a, b in zip(bm.color(m), BLUE)))
    C["show"] = at(107, 21)           # the eye toggle right of the top bar's three frame buttons
    mev('MOUSEMOVE', 'NOTHING', *C["show"])


@step
def s_click_show():
    C["shown_before"] = mod(".preferences").get().show_time_slider_bookmarks
    click("show")


@step
def s_hidden():
    prefs = mod(".preferences").get()
    check("clicking the eye button turns Show Bookmarks off", C["shown_before"] and not prefs.show_time_slider_bookmarks)
    check("the Time Slider then draws no bookmarks", mod(".operators.bookmarks").shown(bpy.context) == [])
    shot("gui_bookmark_manager_hidden.png", C["w"])
    prefs.show_time_slider_bookmarks = True
    sc = bpy.context.scene
    sc.frame_current = 20
    area = max((a for a in win().screen.areas if a.type == 'VIEW_3D'), key=lambda a: a.width * a.height)
    region = next(r for r in area.regions if r.type == 'WINDOW')
    C["mouse"] = (region.x + region.width // 2, region.y + region.height // 2)
    win().event_simulate(type='MOUSEMOVE', value='NOTHING', x=C["mouse"][0], y=C["mouse"][1])
    with bpy.context.temp_override(window=win(), area=area, region=region):
        C["edit"] = bpy.ops.allset.bookmark_edit('INVOKE_DEFAULT')


@step
def s_edit_shot():
    shot("gui_bookmark_manager_edit.png")


@step
def s_edit_confirm():
    x, y = C["mouse"]
    win().event_simulate(type='RET', value='PRESS', x=x, y=y)
    win().event_simulate(type='RET', value='RELEASE', x=x, y=y)


@step
def s_edited():
    bm = mod(".operators.bookmarks")
    sc = bpy.context.scene
    m = sc.timeline_markers.get("jog")
    check(f"Edit opens its dialog on the bookmark at the current time ({C['edit']})", C["edit"] == {'RUNNING_MODAL'})
    check("confirming the filled dialog keeps the bookmark as it was",
          m is not None and bm.bookmark_range(sc, m) == (10, 30)
          and all(abs(a - b) < 1e-4 for a, b in zip(bm.color(m), BLUE)))
    tap('ESC')


run()
