"""#334: the kit never moves a kit window. The place timer only reads a window's rect (a window dragged to another
monitor keeps its place there), and the file is written once the window stands still, not on every tick of a drag.
The real window: tests/gui/gui_issue334_window_move.py."""

from importlib import import_module

import kit

wp = import_module(kit.MODULE + ".ui.window_places")

KIND = "editor:FCURVES"


class _Win:
    def __init__(self, x, y, w, h):
        self.x, self.y, self.width, self.height = x, y, w, h


def _reset():
    wp._places.clear()
    wp._tracked.clear()
    wp._last.clear()
    wp._state.update(loaded=True, dirty=False)


def test_settled_is_the_same_rect_twice():
    wp._last.clear()
    assert not wp.settled(1, (0, 0, 10, 10))          # the first look: it may be moving
    assert wp.settled(1, (0, 0, 10, 10))
    assert not wp.settled(1, (5, 0, 10, 10))          # moved since the last look
    assert wp.settled(1, (5, 0, 10, 10))
    assert not wp.settled(1, (5, 0, 12, 10))          # resized
    wp._last.clear()


def test_tick_remembers_every_rect_and_writes_once_the_window_stands_still():
    saves = []
    orig_save, orig_window = wp.save, wp.live_refs.window
    fake = _Win(100, 100, 640, 480)
    live = {7: fake}

    def fake_save():
        saves.append({k: list(v) for k, v in wp._places.items()})
        wp._state["dirty"] = False

    wp.save = fake_save
    wp.live_refs.window = lambda ptr: live.get(ptr)
    try:
        _reset()
        wp._tracked[7] = KIND
        wp.remember(KIND, (100, 100, 640, 480))
        assert wp._tick() == wp.TICK
        assert saves == [], "the first look at a window writes nothing yet"
        wp._tick()
        assert len(saves) == 1 and saves[-1][KIND] == [100, 100, 640, 480]
        # dragged to a second monitor: the rect changes tick after tick -> remembered at once, nothing written
        for x in (900, 1700, 2500, 2600):
            fake.x = x
            wp._tick()
            assert wp.place(KIND) == [x, 100, 640, 480]
            assert len(saves) == 1, "no disk write while the window moves"
        wp._tick()                                      # it stands still: one write, the new place
        assert len(saves) == 2 and saves[-1][KIND] == [2600, 100, 640, 480]
        wp._tick()
        assert len(saves) == 2, "nothing to write while nothing changes"
        # closed on the other monitor: that place stays remembered, the window is no longer tracked
        live.clear()
        assert wp._tick() is None
        assert 7 not in wp._tracked and 7 not in wp._last
        assert wp.place(KIND) == [2600, 100, 640, 480]
        # the place of a window that was closed right after a move is written at that tick (nothing moves then)
        live[8] = _Win(10, 20, 300, 200)
        wp._tracked[8] = "render_settings"
        wp._tick()
        live.clear()
        wp._tick()
        assert saves[-1]["render_settings"] == [10, 20, 300, 200]
    finally:
        wp.save, wp.live_refs.window = orig_save, orig_window
        _reset()


def test_a_place_on_another_monitor_is_kept_and_fitted_only_when_reopening():
    _reset()
    wp.remember(KIND, (2600, 100, 640, 480))
    assert wp.place(KIND) == [2600, 100, 640, 480], "remembered as it is, not clamped"
    # reopening can only put the window over the Blender window it opens from: fitted into that area then
    class _W:
        x, y = 0, 0

    class _A:
        x, y, width, height = 0, 0, 1600, 900
    assert wp.target_in_window(KIND, _W, _A) == (960, 100, 640, 480)
    assert wp.place(KIND) == [2600, 100, 640, 480], "fitting is for the new window; the remembered place stays"
    _reset()
