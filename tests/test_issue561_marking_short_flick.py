"""#561: a quick flick in the Ctrl+RMB convert marking menu converts the selection however short it is, once it leaves
the small dead zone around the press point: flick left = To Vertices, up = To Edges, right = To UVs, down = To Faces.
The flick's length and speed don't matter; a release right after the press still runs nothing, and a press-release
that stays in the dead zone keeps the menu up. Engine only."""

from importlib import import_module

import kit

engine = import_module(kit.MODULE + ".marking.engine")
mm = import_module(kit.MODULE + ".marking.menus")

B = (0.0, 0.0, 1400.0, 1200.0)
O = (700.0, 600.0)
STEP = {"N": (0, 1), "E": (1, 0), "W": (-1, 0), "S": (0, -1)}
WANT = {"W": "Select/Convert Selection/To Vertices", "N": "Select/Convert Selection/To Edges",
        "E": "Select/Convert Selection/To UVs"}


def _flick(menu, way, length, held=0.12, steps=3):
    dx, dy = STEP[way]
    s = engine.Session(menu, O, 100.0, lambda text: 7.0 * len(text), None, None, B)
    for i in range(1, steps):
        f = i / steps
        s.move(O[0] + length * f * dx, O[1] + length * f * dy, 100.0 + held * f)
    return s.release(O[0] + length * dx, O[1] + length * dy, 100.0 + held)


def test_short_flicks_convert_in_each_direction():
    for way, path in WANT.items():
        for length in (14, 20, 30, 45, 60, 80, 120, 200):
            res = _flick(mm.CTRL_CONVERT, way, length)
            assert res is not None and res[0] == "RUN", (way, length, res)
            assert path in str(res[1].action), (way, length, res[1].label, res[1].action)


def test_a_short_flick_down_converts_to_faces():
    """Down, the list lies right under To Faces: a short flick ends above it."""
    for length in (14, 20, 30, 45):
        res = _flick(mm.CTRL_CONVERT, "S", length)
        assert res is not None and res[0] == "RUN", (length, res)
        assert "Select/Convert Selection/To Faces" in str(res[1].action), (length, res[1].label)


def test_flick_speed_does_not_matter():
    for held in (0.105, 0.13, 0.14):
        for steps in (1, 2, 6):
            res = _flick(mm.CTRL_CONVERT, "W", 25, held=held, steps=steps)
            assert res is not None and res[0] == "RUN", (held, steps, res)


def test_a_release_right_after_the_press_still_runs_nothing():
    assert _flick(mm.CTRL_CONVERT, "W", 30, held=0.05) == ("CANCEL", None, False)


def test_a_press_release_in_the_dead_zone_keeps_the_menu_up():
    assert _flick(mm.CTRL_CONVERT, "W", 5, held=0.12) is None


def test_a_short_flick_never_runs_the_opposite_item():
    menu = mm.Sub(radial={"W": ("Sub", mm.Sub(radial={"E": ("Back", ("wm.context_toggle", {})),
                                                      "W": ("On", ("wm.context_toggle", {"data_path": "x"}))}))})
    for length in (20, 40, 60):
        res = _flick(menu, "W", length)
        assert res[0] == "RUN" and res[1].label == "On", (length, res)
