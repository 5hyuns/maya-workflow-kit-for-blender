"""#414: the quick-release window counts from the press. Blender hands Python no press time, so the marking menu
estimates it: when the kit's heartbeat shows the frame before the press was slow (the press waited for it), the press
is taken to have come right after the last beat before that frame, so a real flick is not taken as too short and
still runs its item. With frames on time the press is when Blender handled it. Engine and clock only."""

from importlib import import_module

import kit

engine = import_module(kit.MODULE + ".marking.engine")
modal = import_module(kit.MODULE + ".marking.modal")
mm = import_module(kit.MODULE + ".marking.menus")

B = (0.0, 0.0, 1400.0, 1200.0)
O = (700.0, 600.0)
ACT = ("wm.context_toggle", {})
MENU = mm.Sub(radial={k: (f"Item {k}", ACT) for k in ("N", "NE", "E", "SE", "S", "SW", "W", "NW")})
BEAT = modal.BEAT


def _flick(t0, t_release):
    s = engine.Session(MENU, O, t0, lambda text: 7.0 * len(text), None, None, B)
    s.move(O[0] + 30, O[1], t_release - 0.01)
    return s.release(O[0] + 60, O[1], t_release)


def test_frames_on_time_the_press_is_when_it_was_handled():
    t = 100.0
    assert modal.press_time(t, (t - BEAT - 0.001, t - 0.001)) == t
    assert modal.press_time(t, (50.0, 51.0)) == t, "no recent beat: the press was handled at once"


def test_a_slow_frame_before_the_press_moves_it_back():
    # beats at 99.90 and 99.965 (a 65 ms frame), the press handled at 99.966
    t = 99.966
    est = modal.press_time(t, (99.90, 99.965))
    assert abs(est - 99.90) < 1e-9, est


def test_a_delayed_invoke_still_runs_a_real_flick():
    """A flick released 0.105 s after the press, whose press Blender handled 60 ms late."""
    press, handled = 99.905, 99.966
    release = press + 0.105
    est = modal.press_time(handled, (99.90, 99.965))
    res = _flick(est, release)
    assert res is not None and res[0] == "RUN" and res[1].label == "Item E", res
    res = _flick(handled, release)
    assert res == ("CANCEL", None, False), "counted from the late handling it would run nothing"


def test_a_busy_loop_since_the_last_beat_moves_the_press_back():
    """The press came while the loop was busy and is handled before the heartbeat runs again: beats on time until
    99.90, then nothing until the press is handled at 99.966. The press came after the last beat."""
    t = 99.966
    est = modal.press_time(t, (99.88, 99.90))
    assert abs(est - 99.90) < 1e-9, est


def test_a_heartbeat_not_running_leaves_the_press_as_handled():
    t = 100.0
    assert modal.press_time(t, (0.0, 0.0)) == t
    assert modal.press_time(t, (50.0, 51.0)) == t


def test_a_heartbeat_that_just_started_leaves_the_press_as_handled():
    """Only one beat so far (the other still 0), or a long pause before the latest beat: no slow frame to date the
    press back to, and an instant click stays a click (the menu stays open)."""
    t = 30000.0
    assert modal.press_time(t, (0.0, t - 0.01)) == t
    assert modal.press_time(t, (t - 5.0, t - 0.01)) == t
    s = engine.Session(MENU, O, modal.press_time(t, (0.0, t - 0.01)), lambda text: 7.0 * len(text), None, None, B)
    assert s.release(O[0], O[1], t + 0.002) is None and s.mode == "CLICK"


def test_a_busy_loop_still_runs_a_real_flick():
    """A flick released 0.105 s after the press, the press handled 60 ms late before the next beat."""
    press, handled = 99.905, 99.966
    release = press + 0.105
    est = modal.press_time(handled, (99.88, 99.90))
    res = _flick(est, release)
    assert res is not None and res[0] == "RUN" and res[1].label == "Item E", res


def test_a_quick_click_handled_with_its_press_after_a_slow_frame_stays_a_click():
    """Press and release both come in during a 0.3 s frame and are handled together after it: the press is dated
    back into the frame, but the click test counts how long the button was down (about the time between handling
    them), so the menu stays open. A release after a beat counts from the press time as before."""
    handled = 500.0
    beats = (499.68, 499.70)             # the last beats before a 0.3 s frame
    t0 = modal.press_time(handled, beats)
    assert abs(t0 - 499.70) < 1e-9, t0
    release = handled + 0.002
    held = modal.held_time(release, handled, beats[1], beats)
    assert abs(held - 0.002) < 1e-9, held
    s = engine.Session(MENU, O, t0, lambda text: 7.0 * len(text), None, None, B)
    assert s.release(O[0], O[1], release, held) is None and s.mode == "CLICK"
    s = engine.Session(MENU, O, t0, lambda text: 7.0 * len(text), None, None, B)
    assert s.release(O[0], O[1], release) == ("CANCEL", None, False), "counted from the dated-back press: closes"
    # a beat ran between the press and the release: the release came later, counted from the press time
    assert modal.held_time(release, handled, beats[1], (beats[1], handled + 0.001)) is None


def test_a_flick_handled_with_its_press_after_a_slow_frame_still_runs():
    """The held time only changes the quick-click test: a flick whose press and release were handled together
    still counts from the dated-back press for the quick-release window and runs its item."""
    handled = 500.0
    beats = (499.68, 499.70)
    t0 = modal.press_time(handled, beats)
    release = handled + 0.002
    s = engine.Session(MENU, O, t0, lambda text: 7.0 * len(text), None, None, B)
    s.move(O[0] + 30, O[1], release - 0.001)
    res = s.release(O[0] + 60, O[1], release, modal.held_time(release, handled, beats[1], beats))
    assert res is not None and res[0] == "RUN" and res[1].label == "Item E", res
