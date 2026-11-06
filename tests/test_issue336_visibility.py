"""#336: h (Toggle Visibility) in a scene saved by an earlier kit version. An object hidden with h back then carries
a flag without a recorded selection; it must not join the toggle of another object (the report: h hid the picked
object and showed the old hidden one, back and forth). h with nothing selected still brings it back."""

from importlib import import_module

import bpy

import kit
from test_step16_undo_visibility import _scene, _select, _vis

visibility = import_module(kit.MODULE + ".operators.visibility")


def _hidden_by_an_earlier_version(ob):
    ob.hide_viewport = True
    ob.select_set(False)
    ob[visibility.KEPT] = True          # the flag an earlier version wrote: no selection recorded


def test_old_flag_stays_out_of_another_toggle():
    a, b, c = _scene()
    _hidden_by_an_earlier_version(a)
    _select(b)
    _vis('TOGGLE')
    assert b.hide_viewport and a.hide_viewport, "#336: h on b must not show a"
    assert not a.select_get()
    _vis('TOGGLE')                      # nothing visible selected: b comes back, a stays hidden
    assert not b.hide_viewport and b.select_get() and a.hide_viewport


def test_no_ping_pong_after_an_upgrade():
    # the report: hide one object, pick another, h, pick another, h: every hidden object stays hidden
    a, b, c = _scene()
    _hidden_by_an_earlier_version(a)
    _select(b)
    _vis('TOGGLE')
    _select(c)
    _vis('TOGGLE')
    assert a.hide_viewport and b.hide_viewport and c.hide_viewport
    assert not any(ob.visible_get() and ob.select_get() for ob in (a, b, c))


def test_old_flag_comes_back_with_nothing_selected():
    a, b, c = _scene()
    _hidden_by_an_earlier_version(a)
    _select()
    _vis('TOGGLE')
    assert not a.hide_viewport and a.select_get(), "h with nothing selected shows what h hid"
    assert visibility.KEPT not in a


def test_recorded_selection_still_rules():
    # the current rule (#322): a kept object belongs to the selection it was hidden from
    a, b, c = _scene()
    _select(a, b)
    _vis('TOGGLE')                      # a and b hidden, kept together
    assert a.hide_viewport and b.hide_viewport
    _select()
    _vis('TOGGLE')                      # both come back
    assert not a.hide_viewport and not b.hide_viewport and a.select_get() and b.select_get()
