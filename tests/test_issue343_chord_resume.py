"""#343: the Alt navigation follows the mouse buttons held, like Maya: LMB tumbles, MMB tracks, both dolly, and
letting go of one of the two carries on with the other one (the chord watcher's rules, no events needed)."""

from importlib import import_module
from types import SimpleNamespace

import kit

view = import_module(kit.MODULE + ".operators.view")

L, M = 'LEFTMOUSE', 'MIDDLEMOUSE'


def walk(start, events):
    """The navigation after each (button, value) event, starting with the buttons in ``start``."""
    held, out = frozenset(start), []
    for button, value in events:
        nxt = view.chord_held(held, button, value)
        if nxt is not None:
            held = nxt
        out.append(view.chord_mode(held))
    return out


def test_modes_of_the_held_buttons():
    assert view.chord_mode({L}) == 'TUMBLE'
    assert view.chord_mode({M}) == 'TRACK'
    assert view.chord_mode({L, M}) == 'DOLLY'
    assert view.chord_mode(set()) is None


def test_track_dolly_and_back_to_track():
    """The issue: Alt+MMB track, + LMB = dolly, - LMB = track again without letting go of MMB."""
    assert walk({M}, [(L, 'PRESS'), (L, 'RELEASE'), (M, 'RELEASE')]) == ['DOLLY', 'TRACK', None]


def test_other_orders():
    assert walk({L}, [(M, 'PRESS'), (M, 'RELEASE'), (L, 'RELEASE')]) == ['DOLLY', 'TUMBLE', None]
    assert walk({M}, [(L, 'PRESS'), (M, 'RELEASE'), (L, 'RELEASE')]) == ['DOLLY', 'TUMBLE', None]
    assert walk({L}, [(M, 'PRESS'), (L, 'RELEASE'), (M, 'RELEASE')]) == ['DOLLY', 'TRACK', None]


def test_second_button_again_and_again():
    events = [(L, 'PRESS'), (L, 'RELEASE')] * 3 + [(M, 'RELEASE')]
    assert walk({M}, events) == ['DOLLY', 'TRACK'] * 3 + [None]


def test_quick_second_press_counts_as_a_press():
    assert view.chord_held({M}, L, 'DOUBLE_CLICK') == {L, M}


def test_other_events_change_nothing():
    for button, value in ((L, 'PRESS'), (M, 'CLICK'), ('RIGHTMOUSE', 'PRESS'), ('LEFT_ALT', 'RELEASE'),
                          ('MOUSEMOVE', 'NOTHING'), (M, 'CLICK_DRAG')):
        assert view.chord_held({L}, button, value) is None, (button, value)
    assert view.chord_held({L}, M, 'RELEASE') is None, "a button that is not held cannot be let go"
    assert view.chord_held({L, M}, L, 'PRESS') is None


def _watch(held, events, running=("VIEW3D_OT_move",)):
    """Feed events to the watcher's modal with stand-ins; returns (results, navigations it started)."""
    started = []
    old = dict(view.CHORD_STARTS)
    view.CHORD_STARTS.update({mode: (lambda context, m=mode: started.append(m)) for mode in old})
    try:
        op = SimpleNamespace(held=set(held))
        context = SimpleNamespace(window=SimpleNamespace(
            modal_operators=[SimpleNamespace(bl_idname=n) for n in running]))
        out = [view.ALLSET_OT_nav_chord.modal(op, context, SimpleNamespace(type=t, value=v)) for t, v in events]
    finally:
        view.CHORD_STARTS.clear()
        view.CHORD_STARTS.update(old)
    return out, started


def test_watcher_starts_the_next_navigation_and_passes_the_event_on():
    out, started = _watch({M}, [('MOUSEMOVE', 'NOTHING'), (L, 'PRESS')])
    assert out == [{'PASS_THROUGH'}, {'FINISHED', 'PASS_THROUGH'}] and started == ['DOLLY'], (out, started)
    out, started = _watch({L, M}, [(L, 'RELEASE')], running=("ALLSET_OT_dolly",))
    assert out == [{'FINISHED', 'PASS_THROUGH'}] and started == ['TRACK'], (out, started)
    out, started = _watch({L, M}, [(M, 'RELEASE')], running=("VIEW3D_OT_zoom",))
    assert started == ['TUMBLE'], "through a camera the dolly is Blender's zoom"
    _out, started = _watch({M}, [(L, 'DOUBLE_CLICK')])
    assert started == ['DOLLY'], "a quick second press arrives as a double click"


def test_watcher_ends_without_starting():
    for held, event, running in (({M}, (M, 'RELEASE'), ("VIEW3D_OT_move",)),          # all let go
                                 ({L, M}, ('ESC', 'PRESS'), ("ALLSET_OT_dolly",)),       # cancelled
                                 ({M}, ('RIGHTMOUSE', 'PRESS'), ("VIEW3D_OT_move",)),
                                 ({M}, (L, 'PRESS'), ())):                               # nothing runs any more
        out, started = _watch(held, [event], running)
        assert out == [{'FINISHED', 'PASS_THROUGH'}] and not started, (held, event, out, started)


def test_every_mode_has_a_start():
    """Every navigation the watcher can switch to has a start, and it keeps watching while any of them runs."""
    assert set(view.CHORD_STARTS) == set(view.CHORD_MODES.values())
    assert {"VIEW3D_OT_rotate", "VIEW3D_OT_move", "VIEW3D_OT_zoom", "ALLSET_OT_dolly"} <= view.NAV_MODALS
