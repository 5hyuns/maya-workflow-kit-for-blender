"""#543: a quick flick in the Ctrl+RMB convert marking menu converts the selection, like Maya. The radial items there
are submenus (To Vertices, To Edges, To Faces, To UVs); a mark released before the menu is drawn goes into the submenu
where it crosses the item, and the rest of the stroke picks there, so a flick on past the item runs the submenu's item
in that direction (flick left = To Vertices). A mark that ends on the item, or a release once the menu is drawn, still
runs nothing. Engine only."""

from importlib import import_module

import kit

engine = import_module(kit.MODULE + ".marking.engine")
mm = import_module(kit.MODULE + ".marking.menus")

B = (0.0, 0.0, 1400.0, 1200.0)
O = (700.0, 600.0)
STEP = {"N": (0, 1), "S": (0, -1), "E": (1, 0), "W": (-1, 0)}


def _session(menu, t0=100.0):
    return engine.Session(menu, O, t0, lambda text: 7.0 * len(text), None, None, B)


def _flick(menu, way, held=0.13):
    dx, dy = STEP[way]
    s = _session(menu)
    s.move(O[0] + 90 * dx, O[1] + 90 * dy, 100.0 + held - 0.02)
    return s.release(O[0] + 190 * dx, O[1] + 190 * dy, 100.0 + held)


def test_a_flick_converts_in_each_direction():
    """Down, the list lies right under To Faces: a flick there converts while it is still a mark (a release a
    little later runs the list row under the pointer, like Maya)."""
    want = {"W": "Select/Convert Selection/To Vertices", "N": "Select/Convert Selection/To Edges",
            "S": "Select/Convert Selection/To Faces", "E": "Select/Convert Selection/To UVs"}
    for way, path in want.items():
        res = _flick(mm.CTRL_CONVERT, way, held=0.105 if way == "S" else 0.13)
        assert res is not None and res[0] == "RUN", (way, res)
        assert path in str(res[1].action), (way, res[1].label, res[1].action)


def test_a_flick_right_after_the_press_still_runs_nothing():
    assert _flick(mm.CTRL_CONVERT, "W", held=0.05) == ("CANCEL", None, False)


def test_a_mark_that_ends_on_the_item_runs_nothing():
    s = _session(mm.CTRL_CONVERT)
    r = s.layout.radial["W"].rect
    end = (O[0] + (r[0] + r[2]) / 2, O[1] + (r[1] + r[3]) / 2)
    s.move((O[0] + end[0]) / 2, end[1], 100.08)
    assert s.release(*end, 100.12) == ("CANCEL", None, False)


def test_a_drawn_menu_released_on_a_submenu_item_runs_nothing():
    s = _session(mm.CTRL_CONVERT)
    s.move(O[0] - 150, O[1], 100.30)            # the menu is drawn by now; the pointer keeps moving
    res = s.release(O[0] - 190, O[1], 100.31)
    assert res == ("CANCEL", None, False), res


def test_a_submenu_without_an_item_that_way_runs_nothing():
    menu = mm.Sub(radial={"W": ("Sub", mm.Sub(radial={"N": ("Only N", ("wm.context_toggle", {}))}))})
    assert _flick(menu, "W") == ("CANCEL", None, False)
