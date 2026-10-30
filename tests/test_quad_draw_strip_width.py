"""Quad Draw Tab + middle-drag strip width: the preview strip shape and the Tab hint."""
from importlib import import_module
import kit
q = import_module(kit.MODULE + '.operators.quad_draw')


def _segments(segs):
    return [(segs[i], segs[i + 1]) for i in range(0, len(segs), 2)]


def test_width_preview_is_three_quads_of_the_width_above_the_point():
    segs = q.width_preview((100, 50), 20)
    lines = _segments(segs)
    # 4 rungs across the strip and 2 x 3 side edges
    assert len(lines) == 10
    xs = [p[0] for p in segs]
    ys = [p[1] for p in segs]
    assert abs(min(xs) - 90) < 1e-6 and abs(max(xs) - 110) < 1e-6
    assert abs(min(ys) - 50) < 1e-6 and abs(max(ys) - 110) < 1e-6
    rungs = [(a, b) for a, b in lines if abs(a[1] - b[1]) < 1e-6]
    assert sorted(round(a[1]) for a, _b in rungs) == [50, 70, 90, 110]
    assert all(abs(abs(a[0] - b[0]) - 20) < 1e-6 for a, b in rungs)


def test_width_preview_matches_the_strip_a_stroke_makes():
    pairs = q.strip_pairs([(0, 0), (0, 90)], 30)
    segs = q.width_preview((0, 0), 30)
    corners = {tuple(round(c, 6) for c in p) for pair in pairs for p in pair}
    assert {tuple(round(c, 6) for c in p) for p in segs} == corners


def test_width_preview_scales_with_the_width():
    for width in (1, 7, 64):
        xs = [p[0] for p in q.width_preview((0, 0), width)]
        assert abs((max(xs) - min(xs)) - width) < 1e-6


def test_tab_hint_names_the_width_drag():
    assert "middle-drag" in q.TAB_HINT and "strip width" in q.TAB_HINT
