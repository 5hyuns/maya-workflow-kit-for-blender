"""#325 (2D editors): Alt+LMB+MMB zooms the Node Editor, the NLA editor and the UV / Image Editor like their
Alt+RMB, whichever button comes first, like Maya. Letting go of LMB carries on panning only in the NLA editor (like
the Graph Editor / Dope Sheet); the Node and UV / Image Editors stop. Alt+RMB in the Node Editor zooms by the
left / right drag only; in the UV / Image Editor right / down = in, left / up = out. The rules, the modal fed with
stand-in events, and the keymap items."""

from importlib import import_module
from types import SimpleNamespace

import kit

view = import_module(kit.MODULE + ".operators.view")
shelf = import_module(kit.MODULE + ".ui.shelf")

L, M, R = 'LEFTMOUSE', 'MIDDLEMOUSE', 'RIGHTMOUSE'
WINDOW = SimpleNamespace(type='WINDOW')


def _editor(type, ui_mode=None, mask=None):
    return SimpleNamespace(type=type), SimpleNamespace(type=type, ui_mode=ui_mode, mask=mask)


def test_rules_per_editor():
    for (area, space), want in (
            (_editor('GRAPH_EDITOR', 'FCURVES'), ('AXES', True)),
            (_editor('DOPESHEET_EDITOR', 'DOPESHEET'), ('AXES', True)),
            (_editor('NLA_EDITOR'), ('AXES', True)),           # Trax: pans on after LMB is let go
            (_editor('NODE_EDITOR'), ('WIDTH', False)),        # stops; zoom by the sideways drag
            (_editor('IMAGE_EDITOR', 'UV'), ('DOLLY', False)),
            (_editor('IMAGE_EDITOR', 'VIEW'), ('DOLLY', False)),
            (_editor('DOPESHEET_EDITOR', 'TIMELINE'), None),
            (_editor('OUTLINER'), None), (_editor('SEQUENCE_EDITOR'), None)):
        assert view.nav2d_rule(area, WINDOW, space) == want, (area.type, space.ui_mode)
        assert view.nav2d_editor(area, WINDOW, space) is (want is not None)
    area, space = _editor('NODE_EDITOR')
    assert view.nav2d_rule(area, SimpleNamespace(type='UI'), space) is None, "sidebar / header keep theirs"


def test_kit_rows_keep_the_image_editor_pan():
    """The Shelf row and the Status Line strip are Image Editors drawn by the kit, not views to zoom."""
    for marker in (shelf.SHELF_MARKER, shelf.MARKER):
        area, space = _editor('IMAGE_EDITOR', 'VIEW', SimpleNamespace(name=marker))
        assert view.nav2d_rule(area, WINDOW, space) is None, marker


def test_modes_once_both_were_held():
    assert view.nav2d_mode({M}, lmb_pans=False, mmb_pans=False) == 'HOLD', "Node / UV: MMB alone stops"
    assert view.nav2d_mode({M}, lmb_pans=False, mmb_pans=True) == 'PAN', "NLA / Graph: MMB alone pans on"
    assert view.nav2d_mode({M}) == 'PAN', "a drag started with Alt+MMB pans"
    assert view.nav2d_mode({L, M}, lmb_pans=False, mmb_pans=False) == 'ZOOM'


def test_node_zoom_reads_the_sideways_drag_only():
    """Both axes by the same share of their size, from the left / right drag; up / down adds nothing."""
    assert view.nav2d_zoom_delta(10, 99, 40.0, 8.0, uniform=True) == (4.0, 0.8)
    assert view.nav2d_zoom_delta(0, 25, 40.0, 8.0, uniform=True) == (0.0, 0.0)
    assert view.nav2d_zoom_delta(-10, 0, 40.0, 8.0, invert=True, uniform=True) == (4.0, 0.8)


def test_uv_dolly_direction():
    f = view.dolly_2d_factor
    assert f(40, 0) > 1.0 and f(0, -40) > 1.0, "right / down = in"
    assert f(-40, 0) < 1.0 and f(0, 40) < 1.0, "left / up = out"
    assert abs(f(40, 40) - 1.0) < 1e-12, "right and up cancel"
    assert abs(f(40, -40) - f(80, 0)) < 1e-12, "right and down add up"
    assert f(0, 40, invert=True) > 1.0, "Invert Zoom Direction turns it round"


class _Op(SimpleNamespace):
    """Stand-in for the running operator with recorders for its zoom / pan / end."""

    def __init__(self, first, rule):
        super().__init__(_held=frozenset({first}), _lmb_pans=True, _mmb_pans=True, _pan_on=rule[1],
                         _mode='ZOOM' if first == R else view.nav2d_mode({first}), _last=(0, 0), _anchor=None,
                         _carry=[0.0, 0.0], zooms=[], pans=[], ended=0)

    def _zoom(self, context, dx, dy):
        self.zooms.append((dx, dy))

    def _pan(self, context, dx, dy):
        self.pans.append((dx, dy))

    def _end(self, context):
        self.ended += 1
        return {'FINISHED'}


def _ev(type, value='PRESS', x=0, y=0):
    return SimpleNamespace(type=type, value=value, mouse_x=x, mouse_y=y, mouse_region_x=x, mouse_region_y=y)


def walk(first, events, rule=('WIDTH', False)):
    op, out = _Op(first, rule), []
    for ev in events:
        res = view.ALLSET_OT_nav_2d.modal(op, None, ev)
        out.append(None if res == {'FINISHED'} else op._mode)
    return out, op


def test_node_and_uv_stop_when_either_button_is_let_go():
    out, op = walk(M, [_ev(L), _ev(L, 'RELEASE'), _ev(L), _ev(L, 'RELEASE'), _ev(M, 'RELEASE')])
    assert out == ['ZOOM', 'HOLD', 'ZOOM', 'HOLD', None] and op.ended == 1, out
    out, _op = walk(L, [_ev(M), _ev(M, 'RELEASE'), _ev(M), _ev(L, 'RELEASE'), _ev(M, 'RELEASE')])
    assert out == ['ZOOM', 'HOLD', 'ZOOM', 'HOLD', None], out
    out, op = walk(M, [_ev('MOUSEMOVE', 'NOTHING', 8, 0)])
    assert out == ['PAN'] and op.pans == [(8, 0)], "Alt+MMB alone still pans"


def test_nla_pans_on_after_lmb():
    out, _op = walk(M, [_ev(L), _ev(L, 'RELEASE'), _ev(M, 'RELEASE')], rule=('AXES', True))
    assert out == ['ZOOM', 'PAN', None], out


def test_held_view_does_nothing_on_moves():
    out, op = walk(M, [_ev(L, x=10, y=10), _ev('MOUSEMOVE', 'NOTHING', 18, 10), _ev(L, 'RELEASE', 18, 10),
                       _ev('MOUSEMOVE', 'NOTHING', 40, 40)])
    assert op.zooms == [(8, 0)] and not op.pans and out[-1] == 'HOLD', (op.zooms, op.pans, out)


def test_alt_rmb_zoom_in_the_node_editor():
    """Started with Alt+RMB: zooms until RMB is let go; the other buttons change nothing."""
    out, op = walk(R, [_ev('MOUSEMOVE', 'NOTHING', 8, 3), _ev(L), _ev(M), _ev('MOUSEMOVE', 'NOTHING', 16, 3),
                       _ev(L, 'RELEASE'), _ev(R, 'RELEASE')])
    assert out == ['ZOOM'] * 5 + [None] and op.zooms == [(8, 3), (8, 0)] and op.ended == 1, (out, op.zooms)


def test_alt_rmb_passes_on_where_blender_zooms():
    """Graph Editor / Dope Sheet / NLA keep Blender's own Alt+RMB zoom."""
    for type, mode in (('GRAPH_EDITOR', 'FCURVES'), ('DOPESHEET_EDITOR', 'DOPESHEET'), ('NLA_EDITOR', None)):
        area, space = _editor(type, mode)
        ctx = SimpleNamespace(area=area, region=WINDOW, space_data=space)
        assert view.ALLSET_OT_nav_2d.invoke(SimpleNamespace(), ctx, _ev(R)) == {'PASS_THROUGH'}, type


def _items(km_name, type):
    km = kit.maya_kc().keymaps[km_name]
    return [(k.idname, k.type, k.alt, k.shift, k.ctrl) for k in km.keymap_items if k.type == type]


def test_keymap_items():
    for button in (L, M):
        items = _items("Image", button)
        nav = items.index(("allset.nav_2d", button, True, False, False))
        pan = items.index(("image.view_pan", button, True, False, False))
        assert nav < pan, (button, items)
    items = _items("View2D", R)
    assert items.index(("allset.nav_2d", R, True, False, False)) < items.index(("view2d.zoom", R, True, False, False))
    assert [k[0] for k in _items("Image", R) if k[2]] == ["allset.dolly_2d"]
    kit.disable()
    try:
        import bpy
        kcs = bpy.context.window_manager.keyconfigs
        left = [k.idname for km in kcs.addon.keymaps for k in km.keymap_items if k.idname == "allset.nav_2d"]
        assert not left, left
    finally:
        kit.enable()
