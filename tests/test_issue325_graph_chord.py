"""#325 (Graph Editor): Alt+LMB+MMB zooms the Graph Editor / Dope Sheet like Alt+RMB, whichever button comes first,
like Maya; letting go of LMB carries on with the MMB pan, letting go of MMB holds the view still. The rules of the
kit's 2D navigation modal, fed with stand-in events, and its keymap items."""

from importlib import import_module
from types import SimpleNamespace

import kit

view = import_module(kit.MODULE + ".operators.view")

L, M = 'LEFTMOUSE', 'MIDDLEMOUSE'


def test_modes_of_the_held_buttons():
    assert view.nav2d_mode({L, M}) == 'ZOOM'
    assert view.nav2d_mode({M}) == 'PAN'
    assert view.nav2d_mode({L}) == 'PAN', "a drag started with Alt+LMB alone pans as before"
    assert view.nav2d_mode({L}, lmb_pans=False) == 'HOLD'
    assert view.nav2d_mode({M}, lmb_pans=False) == 'PAN'
    assert view.nav2d_mode(set()) is None


def _area(type, ui_mode=None):
    return SimpleNamespace(type=type), SimpleNamespace(ui_mode=ui_mode)


def test_editors_it_applies_to():
    window = SimpleNamespace(type='WINDOW')
    for (area, space), want in ((_area('GRAPH_EDITOR', 'FCURVES'), True), (_area('GRAPH_EDITOR', 'DRIVERS'), True),
                                (_area('DOPESHEET_EDITOR', 'DOPESHEET'), True),
                                (_area('DOPESHEET_EDITOR', 'ACTION'), True),
                                (_area('DOPESHEET_EDITOR', 'TIMELINE'), False),     # the Time Slider
                                (_area('NLA_EDITOR'), False), (_area('IMAGE_EDITOR', 'UV'), False),
                                (_area('NODE_EDITOR'), False), (_area('OUTLINER'), False),
                                (_area('SEQUENCE_EDITOR'), False)):
        assert view.nav2d_editor(area, window, space) is want, (area.type, space.ui_mode)
    area, space = _area('GRAPH_EDITOR', 'FCURVES')
    assert not view.nav2d_editor(area, SimpleNamespace(type='CHANNELS'), space), "the channel list keeps its pan"
    assert not view.nav2d_editor(None, window, space) and not view.nav2d_editor(area, None, space)


def test_zoom_step_is_blenders_drag_rule():
    """Right / up = in, 1 % of the shown range per px on each axis; Invert Zoom Direction turns it round."""
    assert view.nav2d_zoom_delta(10, 0, 40.0, 8.0) == (4.0, 0.0)
    assert view.nav2d_zoom_delta(0, -5, 40.0, 8.0) == (0.0, -0.4)
    assert view.nav2d_zoom_delta(10, 5, 40.0, 8.0, invert=True) == (-4.0, -0.4)


class _Op(SimpleNamespace):
    """Stand-in for the running operator: the modal's state plus recorders for its zoom / end."""

    def __init__(self, first):
        super().__init__(_held=frozenset({first}), _lmb_pans=True, _mode=view.nav2d_mode({first}), _last=(0, 0),
                         _anchor=None, _carry=[0.0, 0.0], zooms=[], ended=0)

    def _zoom(self, context, dx, dy):
        self.zooms.append((dx, dy))

    def _end(self, context):
        self.ended += 1
        return {'FINISHED'}


def _ev(type, value='PRESS', x=0, y=0):
    return SimpleNamespace(type=type, value=value, mouse_x=x, mouse_y=y, mouse_region_x=x, mouse_region_y=y)


def walk(first, events):
    """Mode after each button event (None once the modal ended) and the operator."""
    op, out = _Op(first), []
    for ev in events:
        res = view.ALLSET_OT_nav_2d.modal(op, None, ev)
        out.append(None if res == {'FINISHED'} else op._mode)
    return out, op


def test_chord_either_order_zooms_and_letting_go_of_lmb_pans():
    out, op = walk(M, [_ev(L), _ev(L, 'RELEASE'), _ev(M, 'RELEASE')])
    assert out == ['ZOOM', 'PAN', None] and op.ended == 1, out
    out, op = walk(L, [_ev(M), _ev(L, 'RELEASE'), _ev(M, 'RELEASE')])
    assert out == ['ZOOM', 'PAN', None] and op.ended == 1, out


def test_letting_go_of_mmb_holds_the_view_until_mmb_comes_back():
    out, _op = walk(L, [_ev(M), _ev(M, 'RELEASE'), _ev(M), _ev(M, 'RELEASE'), _ev(L, 'RELEASE')])
    assert out == ['ZOOM', 'HOLD', 'ZOOM', 'HOLD', None], out
    out, _op = walk(M, [_ev(L), _ev(M, 'RELEASE'), _ev(L, 'RELEASE')])
    assert out == ['ZOOM', 'HOLD', None], "MMB first: once both were held, LMB alone holds the view too"


def test_again_and_again_and_quick_presses():
    out, _op = walk(M, [_ev(L), _ev(L, 'RELEASE')] * 3 + [_ev(M, 'RELEASE')])
    assert out == ['ZOOM', 'PAN'] * 3 + [None], out
    out, _op = walk(M, [_ev(L, 'DOUBLE_CLICK')])
    assert out == ['ZOOM'], "a quick second press arrives as a double click"


def test_moves_follow_the_mode():
    """Mouse steps go to the zoom with the step since the last event; a held view does nothing."""
    out, op = walk(L, [_ev(M, x=10, y=10), _ev('MOUSEMOVE', 'NOTHING', 18, 13), _ev('MOUSEMOVE', 'NOTHING', 20, 13),
                       _ev(M, 'RELEASE', 20, 13), _ev('MOUSEMOVE', 'NOTHING', 40, 40)])
    assert op.zooms == [(8, 3), (2, 0)] and out[-1] == 'HOLD', (op.zooms, out)
    assert op._anchor == (10, 10), "the zoom keeps the point the mouse was on when it started (Zoom to Mouse)"


def test_other_events_are_kept_from_the_editor():
    for ev in (_ev('RIGHTMOUSE'), _ev('LEFT_ALT', 'RELEASE'), _ev('A'), _ev(L, 'PRESS')):
        out, op = walk(L, [ev])
        assert out == ['PAN'] and op.ended == 0, (ev.type, ev.value, out)
    out, op = walk(L, [_ev(M), _ev('ESC')])
    assert out == ['ZOOM', None] and op.ended == 1, "Esc ends it where the view is, like Blender's pan / zoom"


def _items(km_name, type):
    km = kit.maya_kc().keymaps[km_name]
    return [(k.idname, k.type, k.alt, k.shift, k.ctrl) for k in km.keymap_items if k.type == type]


def test_keymap_items_go_first_in_view2d_and_leave_with_the_kit():
    for button in (L, M):
        items = _items("View2D", button)
        nav = items.index(("allset.nav_2d", button, True, False, False))
        pan = items.index(("view2d.pan", button, True, False, False))
        assert nav < pan, (button, items)
    patches = import_module(kit.MODULE + ".keymap.maya_patches")
    assert "allset.nav_2d" in patches.PASS_THROUGH_FIRST
    kit.disable()
    try:
        import bpy
        kcs = bpy.context.window_manager.keyconfigs
        left = [k.idname for km in kcs.addon.keymaps for k in km.keymap_items if k.idname == "allset.nav_2d"]
        assert not left, left
    finally:
        kit.enable()
    assert ("allset.nav_2d", L, True, False, False) in _items("View2D", L)
