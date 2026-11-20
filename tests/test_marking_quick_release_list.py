"""A stroke released very soon after the press is a mark, like Maya: it picks a radial item by its direction and never
the list row under the release point (Ctrl+RMB: a quick S then SE stroke ending on To Face Path runs nothing, as
To Faces is a submenu that did not open). A little later the row under the pointer runs. Engine only."""

from importlib import import_module

import kit

engine = import_module(kit.MODULE + ".marking.engine")
mm = import_module(kit.MODULE + ".marking.menus")

B = (0.0, 0.0, 1400.0, 1200.0)
O = (700.0, 600.0)
# S then SE (y up), ending on the first list row
PATH = [(0, -20), (0, -40), (0, -60), (14, -74), (28, -88), (42, -102)]


def measure(text):
    return 7.0 * len(text)


def _stroke(menu, release_t, path=PATH, every=0.012):
    s = engine.Session(menu, O, 0.0, measure, None, None, B)
    t = 0.0
    for dx, dy in path:
        t += every
        s.move(O[0] + dx, O[1] + dy, t)
    dx, dy = path[-1]
    return s, s.release(O[0] + dx, O[1] + dy, release_t)


def _row(s, label):
    return next(it for it in s.layout.items if it.label == label)


def test_the_end_point_is_on_the_to_face_path_row():
    s = engine.Session(mm.CTRL_CONVERT, O, 0.0, measure, None, None, B)
    r = _row(s, "To Face Path").rect
    assert r[0] <= PATH[-1][0] <= r[2] and r[1] <= PATH[-1][1] <= r[3], r


def test_a_quick_release_on_a_list_row_runs_nothing():
    _s, res = _stroke(mm.CTRL_CONVERT, 0.095)
    assert res is not None and res[0] == "CANCEL", res


def test_a_later_release_on_the_row_runs_it():
    _s, res = _stroke(mm.CTRL_CONVERT, 0.14)
    assert res is not None and res[0] == "RUN" and res[1].label == "To Face Path", res


def test_a_quick_release_on_a_row_picks_the_radial_item_of_the_mark():
    menu = mm.Sub(radial={"S": ("Down", ("wm.context_toggle", {})), "E": ("Right", ("wm.context_toggle", {}))},
                  items=[("Row A", ("wm.context_toggle", {})), ("Row B", ("wm.context_toggle", {}))])
    s = engine.Session(menu, O, 0.0, measure, None, None, B)
    r = _row(s, "Row A").rect
    end = (r[2] - 4.0, (r[1] + r[3]) / 2)
    path = [(end[0] * k / 5, end[1] * k / 5) for k in range(1, 6)]
    _s, res = _stroke(menu, 0.08, path)
    assert res is not None and res[0] == "RUN" and res[1].label == "Down", res
    _s, res = _stroke(menu, 0.16, path)
    assert res is not None and res[0] == "RUN" and res[1].label == "Row A", res
