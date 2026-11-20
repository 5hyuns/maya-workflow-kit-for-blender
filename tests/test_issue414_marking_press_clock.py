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


def test_a_busy_loop_still_runs_a_real_flick():
    """A flick released 0.105 s after the press, the press handled 60 ms late before the next beat."""
    press, handled = 99.905, 99.966
    release = press + 0.105
    est = modal.press_time(handled, (99.88, 99.90))
    res = _flick(est, release)
    assert res is not None and res[0] == "RUN" and res[1].label == "Item E", res
