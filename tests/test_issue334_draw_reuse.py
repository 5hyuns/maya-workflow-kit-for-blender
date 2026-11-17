"""#334: while a window is dragged or resized, every region of every window redraws at each step. The kit's own
drawings (shelf row, Maya Outliner rows, dock tint and tab strip, Time Slider) keep the calls of their last full draw
and make them again at such a step: only when a window's rect changed since the region's previous draw a moment
ago, the region's size, UI scale and hover are the same and no animation plays. A draw that fails keeps nothing,
and once the windows stand still every area redraws in full."""

from importlib import import_module

import bpy

import kit

wm_ = import_module(kit.MODULE + ".ui.window_motion")
dr = import_module(kit.MODULE + ".ui.draw_replay")


class _Rects:
    """Window rects the module sees, set by the test."""

    def __init__(self):
        self.now = ((0, 0, 800, 600),)
        self.real = wm_.rects

    def __enter__(self):
        wm_.rects = lambda: self.now
        wm_.forget()
        return self

    def __exit__(self, *exc):
        wm_.rects = self.real
        wm_.forget()


def _draw(log, key, sig, value):
    """One draw of ``key``: the kept calls made again, else a full draw that records ``value`` through ``call``."""
    if dr.again(key, sig):
        return "again"
    with dr.recording(key, sig):
        dr.call(log.append, value)
    return "full"


def test_full_draw_unless_a_window_moved():
    log = []
    with _Rects() as r:
        key, sig = ("shelf", 1), (800, 60, 1.0, None)
        assert _draw(log, key, sig, "a") == "full"
        assert _draw(log, key, sig, "b") == "full", "the windows stand still: a redraw is a change, draw it"
        r.now = ((8, 0, 800, 600),)
        assert _draw(log, key, sig, "c") == "again", "a window moved: the last calls again"
        assert log == ["a", "b", "b"], log
        r.now = ((16, 0, 800, 600),)
        assert _draw(log, key, (800, 61, 1.0, None), "d") == "full", "the region's size changed"
        r.now = ((24, 0, 800, 600),)
        assert _draw(log, key, (800, 61, 1.0, 3), "e") == "full", "the hover changed"
        r.now = ((32, 0, 800, 600),)
        assert _draw(log, ("shelf", 2), sig, "f") == "full", "another region draws its own"
        r.now = ((32, 0, 800, 600), (900, 0, 400, 300))
        assert _draw(log, key, (800, 61, 1.0, 3), "g") == "full", "a window opened: what it shows may change here"
        assert log[-4:] == ["d", "e", "f", "g"], log


def test_not_after_a_pause_or_while_playing():
    log = []
    with _Rects() as r:
        key, sig = ("outliner", 1), (300, 500, 1.0, None)
        _draw(log, key, sig, "a")
        wm_._seen[key] = (wm_._seen[key][0], wm_._seen[key][1] - 2 * wm_.RECENT)
        r.now = ((8, 0, 800, 600),)
        assert _draw(log, key, sig, "b") == "full", "the previous draw was long ago (a window shown again)"
        real = wm_._playing
        wm_._playing = lambda: True
        try:
            r.now = ((16, 0, 800, 600),)
            assert _draw(log, key, sig, "c") == "full", "an animation plays: the frame changes"
        finally:
            wm_._playing = real
        r.now = ((24, 0, 800, 600),)
        assert _draw(log, key, sig, "d") == "again"
        assert log == ["a", "b", "c", "c"], log


def test_a_failed_draw_keeps_nothing():
    log = []
    with _Rects() as r:
        key, sig = ("time slider", 1), (900, 40, 1.0)
        _draw(log, key, sig, "a")
        try:
            with dr.recording(key, sig):
                dr.call(log.append, "half")
                raise ReferenceError("freed")
        except ReferenceError:
            pass
        r.now = ((8, 0, 800, 600),)
        assert _draw(log, key, sig, "b") == "full", "the last draw failed: nothing to draw again"
        assert dr._lists == [], "no recording left running"


def test_nested_recordings_keep_their_own_calls():
    log = []
    with _Rects() as r:
        outer, inner, sig = ("dock draw", 1), ("dock draw", 2), (300, 600, 1.0)
        assert not dr.again(outer, sig) and not dr.again(inner, sig)
        with dr.recording(outer, sig):
            dr.call(log.append, 1)
            with dr.recording(inner, sig):
                dr.call(log.append, 2)
            dr.call(log.append, 3)
        r.now = ((8, 0, 800, 600),)
        del log[:]
        assert dr.again(outer, sig) and log == [1, 2, 3], log
        del log[:]
        assert dr.again(inner, sig) and log == [2], log


def test_settle_redraw_and_forget():
    log = []
    with _Rects() as r:
        key, sig = ("shelf", 1), (800, 60, 1.0, None)
        _draw(log, key, sig, "a")
        r.now = ((8, 0, 800, 600),)
        assert _draw(log, key, sig, "b") == "again"
        assert bpy.app.timers.is_registered(wm_._settle), "a redraw in full once the windows stand still"
        r.now = ((12, 0, 800, 600),)
        assert wm_._settle() == wm_.SETTLE, "the window still moves: check again"
        assert wm_._settle() is None, "the windows stood still for a tick: redraw and stop"
        r.now = ((16, 0, 800, 600),)
        _draw(log, key, sig, "c")
        wm_.forget()
        assert not bpy.app.timers.is_registered(wm_._settle) and not wm_._kept and not wm_._seen
