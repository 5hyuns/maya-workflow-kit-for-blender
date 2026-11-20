"""#411: the centre of a marking menu where nothing is highlighted or picked is 10 px, like Maya: a pointer 10 px
or nearer from the press point highlights nothing, a little farther highlights the item of its direction and a
release there runs it. A quick press and release that stays inside it still keeps the menu up (click mode).
Engine only."""

import math
from importlib import import_module

import kit

engine = import_module(kit.MODULE + ".marking.engine")
mm = import_module(kit.MODULE + ".marking.menus")

B = (0.0, 0.0, 1400.0, 1200.0)
O = (700.0, 600.0)
SHOWN = engine.Params().show_delay + 0.05
ACT = ("wm.context_toggle", {})
MENU = mm.Sub(radial={k: (f"Item {k}", ACT) for k in ("N", "NE", "E", "SE", "S", "SW", "W", "NW")})


def measure(text):
    return 7.0 * len(text)


def _session():
    return engine.Session(MENU, O, 0.0, measure, None, None, B)


def _hover(dx, dy):
    s = _session()
    s.move(O[0] + dx, O[1] + dy, SHOWN)
    return s.hover[0].label if s.hover[0] is not None else None


def test_ten_px_highlights_nothing():
    for dx, dy in ((10, 0), (0, -10), (-10, 0), (0, 10), (7, 7), (-7, -7), (9, 2), (8, -4)):
        assert _hover(dx, dy) is None, (dx, dy, _hover(dx, dy))


def test_just_past_ten_px_highlights_the_direction():
    for dx, dy, want in ((11, 0, "Item E"), (0, -11, "Item S"), (-11, 0, "Item W"), (0, 11, "Item N"),
                         (8, 8, "Item NE"), (-8, -8, "Item SW"), (9, -5, "Item SE"), (11, 1, "Item E")):
        assert _hover(dx, dy) == want, (dx, dy, _hover(dx, dy))


def test_a_release_just_past_ten_px_runs_the_item():
    s = _session()
    s.move(O[0] + 5, O[1], 0.1)
    res = s.release(O[0] + 11, O[1], SHOWN)
    assert res is not None and res[0] == "RUN" and res[1].label == "Item E", res


def test_a_release_at_ten_px_runs_nothing():
    s = _session()
    s.move(O[0] + 5, O[1], 0.1)
    res = s.release(O[0] + 10, O[1], SHOWN + 0.2)
    assert res == ("CANCEL", None, False), res


def test_a_quick_click_in_the_centre_keeps_the_menu_up():
    s = _session()
    assert s.release(O[0] + 3, O[1] + 2, 0.12) is None and s.mode == "CLICK"


def test_scaled_params_keep_the_zone_in_proportion():
    p = engine.Params().scaled(2.0)
    s = engine.Session(MENU, O, 0.0, measure, p, None, B)
    s.move(O[0] + 20, O[1], SHOWN)
    assert s.hover[0] is None
    s.move(O[0] + 22, O[1], SHOWN + 0.01)
    assert s.hover[0] is not None and s.hover[0].label == "Item E"
    assert math.isclose(p.dead, 2.0 * engine.Params().dead)
