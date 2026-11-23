"""#525: marking menu items show their command's picture left of the label, like Maya: on the radial boxes and in the
list under the ring (a list with a picture on any row keeps one picture column, the labels in one column). Only items
with a kit drawing of their command show one (``marking/icon_data``); the hotbox and Layouts without a menu path
draw none."""

from importlib import import_module

import kit

engine = import_module(kit.MODULE + ".marking.engine")
mm = import_module(kit.MODULE + ".marking.menus")
icons = import_module(kit.MODULE + ".marking.icons")
draw = import_module(kit.MODULE + ".marking.draw")
icon_data = import_module(kit.MODULE + ".marking.icon_data")


def measure(text):
    return 7.0 * len(text)


def _paths():
    out = {}
    for name, menu in mm.MENUS.items():
        for path, _label, action in mm.label_walk(menu, name):
            out[path] = action
    return out


def test_every_picture_belongs_to_an_item_and_draws():
    paths = _paths()
    missing = [p for p in icon_data.ICONS if p not in paths]
    assert not missing, missing
    assert len(icon_data.ICONS) > 100
    for pic in sorted(set(icon_data.ICONS.values()), key=repr):
        for n in (16, 20):
            px = icons.picture(pic, n)
            assert px.shape == (n, n, 4), (pic, px.shape)
            assert px[..., 3].max() > 0.5, ("an empty picture", pic)


def test_radial_box_and_list_rows_make_room_for_the_picture():
    p = engine.Params()
    lay = engine.Layout(mm.SHIFT_EDGE, measure, p, None, "SHIFT_EDGE")
    bevel = next(it for it in lay.radial.values() if it.label == "Bevel Edge")
    assert bevel.icon == icon_data.ICONS["SHIFT_EDGE/Bevel Edge"]
    assert bevel.icon_x == p.icon_pad and bevel.text_x == p.icon_pad + p.icon + p.icon_gap
    w = bevel.rect[2] - bevel.rect[0]
    plain = engine.Layout(mm.SHIFT_EDGE, measure, p, None, None)
    old = next(it for it in plain.radial.values() if it.label == "Bevel Edge")
    assert old.icon is None and old.text_x == p.ring_pad
    assert abs(w - (old.rect[2] - old.rect[0]) - (p.icon_pad + p.icon + p.icon_gap - p.ring_pad)) < 1e-6
    rows = [it for it in lay.items if it.kind == "list"]
    assert any(it.icon for it in rows) and any(it.icon is None for it in rows)
    assert {it.text_x for it in rows} == {p.list_icon_pad + p.icon + p.icon_gap}, "one label column"
    old_rows = [it for it in plain.items if it.kind == "list"]
    assert {it.text_x for it in old_rows} == {p.pad}
    grow = (rows[0].rect[2] - rows[0].rect[0]) - (old_rows[0].rect[2] - old_rows[0].rect[0])
    assert abs(grow - (p.list_icon_pad + p.icon + p.icon_gap - p.pad)) < 1e-6
    # the picture sits inside its box, clear of the text
    for it in [bevel] + [r for r in rows if r.icon]:
        assert it.icon_x + p.icon <= it.text_x
        assert it.rect[3] - it.rect[1] >= p.icon


def test_sizes_follow_the_ui_scale():
    p = engine.Params().scaled(1.5)
    assert p.icon == 24.0 and p.icon_gap == 7.5


def test_session_submenus_find_their_pictures():
    s = engine.Session(mm.SHIFT_EDGE, (500.0, 300.0), 0.0, measure)
    assert s.layout.path == "SHIFT_EDGE"
    item = next(it for it in s.layout.radial.values() if it.label == "Soften/Harden Edges")
    s._push(item, (500.0, 300.0))
    assert s.layout.path == "SHIFT_EDGE/Soften/Harden Edges"
    labels = {it.label for it in s.layout.items if it.icon}
    assert {"Harden Edge", "Soften Edge"} <= labels, labels


def test_menus_without_pictures():
    # Ctrl+RMB convert menu items have no command pictures (like Maya)
    s = engine.Session(mm.CTRL_CONVERT, (500.0, 300.0), 0.0, measure)
    assert not any(it.icon for it in s.layout.items)
    assert not any(p.startswith("CTRL_CONVERT/") for p in icon_data.ICONS)
    # a menu edited or made by the user keeps the pictures of the items it shares with the kit menu
    user = mm.MarkingMenu("SHIFT_EDGE", "Edge", "user", radial={"N": ("Bevel Edge", mm.SHIFT_EDGE.radial["E"][1])})
    s = engine.Session(user, (500.0, 300.0), 0.0, measure)
    assert s.layout.radial["N"].icon is not None


def test_redraw_bounds_hold_the_pictures():
    origin = (120.0, 80.0)
    s = engine.Session(mm.SHIFT_EDGE, (700.0, 500.0), 0.0, draw.measure, None, None, (0.0, 0.0, 1400.0, 1000.0))
    draw.ACTIVE.clear()
    draw.ACTIVE.update(session=s, origin=origin, window=0, region=0)
    try:
        box = draw.extent()
    finally:
        draw.ACTIVE.clear()
    n = round(s.params.icon)
    cx, cy = s.center
    shown = [it for it in s.layout.items if it.icon]
    assert shown
    for it in shown:
        x = round(cx + it.rect[0] + it.icon_x) + origin[0]
        y = round(cy + (it.rect[1] + it.rect[3]) / 2 - n / 2) + origin[1]
        assert box[0] <= x and x + n <= box[2] and box[1] <= y and y + n <= box[3], (it.label, box)
