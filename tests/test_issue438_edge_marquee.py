"""#438: an edge marquee picks every edge it touches. The screen clipping and the select modes; the drag itself:
tests/gui/gui_issue438_edge_marquee.py."""
from importlib import import_module

import kit

em = import_module(kit.MODULE + ".operators.edge_marquee")

RECT = (10.0, 10.0, 20.0, 20.0)


def _touch(a, b):
    ok, u0, u1 = em.touching([a], [b], RECT)
    return bool(ok[0]), round(float(u0[0]), 4), round(float(u1[0]), 4)


def test_inside_and_across():
    assert _touch((12, 12), (18, 18)) == (True, 0.0, 1.0)          # wholly inside
    assert _touch((0, 15), (30, 15)) == (True, 0.3333, 0.6667)     # across both sides
    assert _touch((15, 15), (15, 40)) == (True, 0.0, 0.2)          # one end inside
    assert _touch((0, 0), (30, 30)) == (True, 0.3333, 0.6667)      # through two corners' sides


def test_outside():
    assert _touch((0, 0), (5, 30))[0] is False                     # left of the box
    assert _touch((0, 25), (30, 25))[0] is False                   # above it, level
    assert _touch((0, 25), (25, 50))[0] is False                   # diagonal past the corner
    assert _touch((21, 0), (21, 30))[0] is False                   # vertical, just right of it


def test_on_the_border_counts():
    assert _touch((20, 0), (20, 30))[0] is True
    assert _touch((0, 10), (5, 10))[0] is False


def test_modes():
    assert em.click_mode(False, False) == 'SET'
    assert em.click_mode(True, False) == 'XOR'
    assert em.click_mode(False, True) == 'SUB'
    assert em.click_mode(True, True) == 'ADD'
    assert [em.combine(s, h, 'SET') for s, h in ((0, 0), (0, 1), (1, 0), (1, 1))] == [False, True, False, True]
    assert [em.combine(s, h, 'ADD') for s, h in ((0, 0), (0, 1), (1, 0), (1, 1))] == [False, True, True, True]
    assert [em.combine(s, h, 'SUB') for s, h in ((0, 0), (0, 1), (1, 0), (1, 1))] == [False, False, True, False]
    assert [em.combine(s, h, 'XOR') for s, h in ((0, 0), (0, 1), (1, 0), (1, 1))] == [False, True, True, False]
