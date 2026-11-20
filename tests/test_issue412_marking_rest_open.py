"""#412: where a rest opens a radial submenu, like Maya: the highlighted radial item opens when its box lies on the
straight line from the menu centre to the pointer (the pointer is on the box or beyond it, seen from the centre).
So beyond a wide diagonal box a rest opens it also at a shallow angle, and a rest just off the box's outer corner
toward the next item does not; a rest before the box (nearer the centre) never opens it. Engine only."""

import math
from importlib import import_module

import kit

engine = import_module(kit.MODULE + ".marking.engine")
mm = import_module(kit.MODULE + ".marking.menus")

B = (0.0, 0.0, 1400.0, 1200.0)
O = (700.0, 600.0)
P = engine.Params()
SHOWN = P.show_delay + 0.05
ACT = ("wm.context_toggle", {})
LABELS = {"N": "To Edges", "NE": "Grow Selection", "E": "To UVs", "SE": "Edge Loop Utilities", "S": "To Faces",
          "SW": "Edge Ring Utilities", "W": "To Vertices", "NW": "Shrink Selection"}
MENU = mm.Sub(radial={k: (v, mm.Sub(radial={"N": (f"{v} N", ACT)})) for k, v in LABELS.items()})


def measure(text):
    return 7.0 * len(text)


def _rest(dx, dy):
    """A stroke from the centre to (dx, dy) (y up), then a rest there: (hovered label before, opened label or None)."""
    s = engine.Session(MENU, O, 0.0, measure, None, None, B)
    n = 12
    t = SHOWN
    for k in range(1, n + 1):
        t += 0.016
        s.move(O[0] + dx * k / n, O[1] + dy * k / n, t)
        s.tick(t)
    hovered = s.hover[0].label if s.hover[0] is not None else None
    s.tick(t + P.open_dwell + 0.02)
    s.tick(t + P.open_dwell + 0.2)
    return hovered, (s.via[-1].label if len(s.stack) > 1 else None)


def _rect(key):
    return engine.Layout(MENU, measure, P).radial[key].rect


def test_beyond_the_wide_diagonal_box_at_a_shallow_angle_opens_it():
    x0, y0, x1, y1 = _rect("SE")
    q = (x1 - 2.0, (y0 + y1) / 2)                  # inside the box, at its far end
    p = (q[0] * 1.3, q[1] * 1.3)
    assert math.degrees(math.atan2(-p[1], p[0])) < 22.5, "the shallow side, off the SE 45 degree sector"
    hovered, opened = _rest(*p)
    assert hovered == "Edge Loop Utilities", hovered
    assert opened == "Edge Loop Utilities", opened


def test_beyond_the_s_box_toward_the_diagonal_opens_s():
    x0, y0, x1, y1 = _rect("S")
    q = (x1 - 8.0, y0 + 1.0)                       # inside the box, near its outer corner toward SE
    p = (q[0] * 1.25, q[1] * 1.25)
    assert math.degrees(math.atan2(-p[1], p[0])) < 67.5, "in the SE 45 degree sector"
    hovered, opened = _rest(*p)
    assert hovered == "To Faces", hovered
    assert opened == "To Faces", opened


def test_off_the_diagonal_box_corner_does_not_open():
    """Just past the SE box's outer corner on the S side: SE is still highlighted, but the box is not on the way
    from the centre, so nothing opens."""
    x0, y0, x1, y1 = _rect("SE")
    a = math.atan2(-y0, x0) + math.radians(2.0)    # 2 degrees steeper than the corner (y up: y0 is the outer side)
    p = (100.0 * math.cos(a), -100.0 * math.sin(a))
    hovered, opened = _rest(*p)
    assert hovered == "Edge Loop Utilities", hovered
    assert opened is None, opened


def test_before_the_box_does_not_open():
    """Between the centre and the SE box at a shallow angle, highlighted but short of the box: nothing opens."""
    x0, y0, x1, y1 = _rect("SE")
    p = (x0 + 25.0, y1 + 2.0)                      # just above the box's inner side (y up), short of it
    hovered, opened = _rest(*p)
    assert hovered == "Edge Loop Utilities", hovered
    assert opened is None, opened


def test_on_the_box_and_straight_out_still_open():
    for key, label in (("E", "To UVs"), ("S", "To Faces"), ("N", "To Edges")):
        x0, y0, x1, y1 = _rect(key)
        c = ((x0 + x1) / 2, (y0 + y1) / 2)
        assert _rest(*c)[1] == label, key
        assert _rest(c[0] * 3, c[1] * 3)[1] == label, key


def test_straight_through_the_diagonal_corner_does_not_open():
    """Along the diagonal itself the line only grazes the SE box's outer corner: nothing opens."""
    x0, y0, x1, y1 = _rect("SE")
    hovered, opened = _rest(x0 * 2.5, y0 * 2.5)
    assert hovered == "Edge Loop Utilities", hovered
    assert opened is None, opened


def _jitter(d):
    """A rest on the E box with the pointer going d px right and back every 0.04 s: did the submenu open?"""
    s = engine.Session(MENU, O, 0.0, measure, None, None, B)
    x0, y0, x1, y1 = _rect("E")
    c = (O[0] + (x0 + x1) / 2, O[1])
    t = SHOWN
    s.move(*c, t)
    for k in range(12):
        t += 0.04
        s.move(c[0] + (d if k % 2 == 0 else 0), c[1], t)
        s.tick(t)
    return len(s.stack) > 1


def test_a_rest_allows_two_px_of_shake_not_three():
    assert _jitter(1) and _jitter(2)
    assert not _jitter(3) and not _jitter(4)
