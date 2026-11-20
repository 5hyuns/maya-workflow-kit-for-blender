"""#414: a marking menu released right after the press runs nothing, like Maya, also when the stroke is on a radial
leaf item; a little later the same stroke runs it. A quick click in the centre still keeps the menu up (click mode),
and a quick mark that ends on a list row still picks the radial item of its direction. The Quick Gestures option
keeps its own fast marks. Engine only."""

from importlib import import_module

import kit

engine = import_module(kit.MODULE + ".marking.engine")
mm = import_module(kit.MODULE + ".marking.menus")

B = (0.0, 0.0, 1400.0, 1200.0)
O = (700.0, 600.0)
P = engine.Params()
ACT = ("wm.context_toggle", {})
MENU = mm.Sub(radial={k: (f"Item {k}", ACT) for k in ("N", "NE", "E", "SE", "S", "SW", "W", "NW")})
LIST_MENU = mm.Sub(radial={"S": ("Down", ACT), "E": ("Right", ACT)}, items=[("Row A", ACT), ("Row B", ACT)])


def measure(text):
    return 7.0 * len(text)


def _session(menu=MENU, params=None):
    return engine.Session(menu, O, 0.0, measure, params, None, B)


def _stroke_release(s, dx, dy, t_release):
    s.move(O[0] + dx, O[1] + dy, 0.02)
    return s.release(O[0] + dx, O[1] + dy, t_release)


def test_a_release_right_after_the_press_runs_nothing():
    for t in (0.06, 0.095):
        for dx, dy in ((18, 0), (0, -18), (60, 0), (-13, 13)):
            s = _session()
            res = _stroke_release(s, dx, dy, t)
            assert res == ("CANCEL", None, False), (t, dx, dy, res)


def test_a_little_later_the_same_stroke_runs_the_item():
    for t in (0.105, P.mark_time, 0.16, 0.4):
        s = _session()
        res = _stroke_release(s, 18, 0, t)
        assert res is not None and res[0] == "RUN" and res[1].label == "Item E", (t, res)


def test_a_quick_click_in_the_centre_still_keeps_the_menu_up():
    for t in (0.03, 0.06, 0.12):
        s = _session()
        assert s.release(O[0] + 2, O[1], t) is None and s.mode == "CLICK", t


def test_a_quick_mark_onto_a_list_row_still_picks_its_direction():
    s = _session(LIST_MENU)
    row = next(it for it in s.layout.items if it.kind == "list")
    end = ((row.rect[0] + row.rect[2]) / 2, (row.rect[1] + row.rect[3]) / 2)
    s.move(O[0] + end[0] / 2, O[1] + end[1] / 2, 0.05)
    res = s.release(O[0] + end[0], O[1] + end[1], (P.quick_none_time + P.mark_time) / 2)
    assert res is not None and res[0] == "RUN" and res[1].label == "Down", res


def test_quick_gestures_option_keeps_its_fast_marks():
    p = engine.Params()
    p.quick_gestures = True
    s = _session(params=p)
    for i in range(1, 6):
        s.move(O[0] + 12 * i, O[1], 0.01 * i)
    res = s.release(O[0] + 60, O[1], 0.06)
    assert res is not None and res[0] == "RUN" and res[1].label == "Item E", res
