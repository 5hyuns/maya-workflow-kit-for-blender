"""Which radial item a marking menu highlights off its boxes, like Maya: the item whose box centre lies in the
direction nearest to the pointer's (so the sectors follow the boxes: a wide diagonal box takes more of the side next
to it, the N / S items more of the diagonals beside them), and in a menu with few items every direction outside the
dead zone has one. Boxes still win where the pointer is on one. Engine only."""

import math
from importlib import import_module

import kit

engine = import_module(kit.MODULE + ".marking.engine")
mm = import_module(kit.MODULE + ".marking.menus")

B = (0.0, 0.0, 1400.0, 1200.0)
O = (700.0, 600.0)
SHOWN = engine.Params().show_delay + 0.05


def measure(text):
    return 7.0 * len(text)


def _session(menu=mm.CTRL_CONVERT):
    return engine.Session(menu, O, 0.0, measure, None, None, B)


def _at(s, dx, dy, t=SHOWN):
    """Hover after a jump to the point (dx, dy) from the press point (y up); asserts it is on no box."""
    lay = s.layout
    assert lay.hit(dx, dy, rects_only=True)[0] is None, (dx, dy, "is on a box")
    s.move(O[0] + dx, O[1] + dy, t)
    return s.hover[0].label if s.hover[0] is not None else None


def _polar(deg, r):
    return r * math.cos(math.radians(deg)), r * math.sin(math.radians(deg))


def test_between_s_and_the_wide_se_box_the_s_item_wins():
    """Ctrl+RMB: 54 degrees below east, past the boxes, is To Faces (S), not Edge Loop Utilities (SE)."""
    s = _session()
    assert _at(s, 55.0, -75.0) == "To Faces"
    s = _session()
    assert _at(s, *_polar(-60.0, 90.0)) == "To Faces"


def test_just_below_east_the_wide_se_item_wins():
    """8 degrees below east, beside the To UVs box: Edge Loop Utilities' wide box lies nearer that way."""
    s = _session()
    assert _at(s, *_polar(-8.0, 100.0)) == "Edge Loop Utilities"
    s = _session()
    assert _at(s, *_polar(-3.0, 160.0)) == "To UVs"


def test_the_se_diagonal_itself_stays_se():
    s = _session()
    assert _at(s, *_polar(-45.0, 100.0)) == "Edge Loop Utilities"


def test_a_menu_with_few_items_has_one_in_every_direction():
    menu = mm.Sub(radial={"N": ("Up", ("wm.context_toggle", {})), "E": ("Right", ("wm.context_toggle", {})),
                          "S": ("Down", ("wm.context_toggle", {}))})
    s = _session(menu)
    assert _at(s, -60.0, -60.0) == "Down"        # SW: nearest to S
    s = _session(menu)
    assert _at(s, -60.0, 60.0) == "Up"           # NW: nearest to N
    s = _session(menu)
    assert _at(s, -80.0, 0.0) == "Up"            # W: as near to N as to S, the first in N, E, S order
    res = s.release(O[0] - 80.0, O[1], SHOWN + 0.05)
    assert res is not None and res[0] == "RUN" and res[1].label == "Up", res


def test_the_dead_zone_has_no_item():
    s = _session()
    assert _at(s, 5.0, -5.0) is None
