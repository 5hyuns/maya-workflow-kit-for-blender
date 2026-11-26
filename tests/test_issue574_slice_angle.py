"""Multi-Cut slice with Shift (GitHub #574): the line's screen angle rounds to the nearest 10 degrees and keeps its
length; without Shift the end is the mouse."""

import math
from importlib import import_module

import kit

mc = import_module(kit.MODULE + ".operators.multi_cut")


def _angle(start, end):
    return math.degrees(math.atan2(end[1] - start[1], end[0] - start[0]))


def test_shift_rounds_to_ten_degrees():
    start = (100.0, 100.0)
    for deg, want in ((3, 0), (7, 10), (14, 10), (16, 20), (44, 40), (46, 50), (86, 90), (136, 140), (174, 170),
                      (-33, -30), (200, -160)):
        t = math.radians(deg)
        end = (start[0] + 250 * math.cos(t), start[1] + 250 * math.sin(t))
        got = mc.slice_end(start, end, True)
        a = _angle(start, got)
        if abs((a - want + 180) % 360 - 180) > 1e-6:
            raise AssertionError((deg, want, a))
        if abs(math.dist(start, got) - 250) > 1e-6:
            raise AssertionError(("length", deg, math.dist(start, got)))


def test_without_shift_the_end_is_the_mouse():
    if mc.slice_end((0, 0), (37.0, 11.0), False) != (37.0, 11.0):
        raise AssertionError("moved without Shift")
    if mc.slice_end((5, 5), (5, 5), True) != (5, 5):
        raise AssertionError("zero-length line moved")


def test_multi_cut_tool_uses_the_knife_pointer():
    tool = import_module(kit.MODULE + ".ui.mesh_tools").ALLSET_TL_multi_cut
    if tool.bl_cursor != 'KNIFE':
        raise AssertionError(tool.bl_cursor)
