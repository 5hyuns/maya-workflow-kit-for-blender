"""#332: a radial submenu opened in place (RMB on a mesh: UV; Shift+RMB on edges: Merge/Collapse Edges) gives the
menu it opened from back. Moving the pointer back inside that menu's ring through an empty sector of the submenu
closes the submenu and the menu is there again (its own items win first, so one lying toward the parent stays
reachable); the same in click mode; nested submenus go back one level at a time; Esc closes only the open submenu
and the whole menu at the top level (engine, no bpy UI). GUI: tests/gui/gui_issue332_marking_back.py."""

from importlib import import_module

import kit

engine = import_module(kit.MODULE + ".marking.engine")
mm = import_module(kit.MODULE + ".marking.menus")

B = (0.0, 0.0, 1400.0, 1200.0)
O = (700.0, 600.0)
P = engine.Params()
R = P.radius
U = engine._UNIT


def measure(text):
    return 7.0 * len(text)


def _session(menu=mm.RMB_MESH):
    return engine.Session(menu, O, 0.0, measure, None, None, B)


def _at(center, direction, dist):
    return (center[0] + U[direction][0] * dist, center[1] + U[direction][1] * dist)


def _label(s):
    return s.hover[0].label if s.hover[0] is not None else None


def _row(s, label, level=0):
    lay, (cx, cy) = s.stack[level]
    it = next(i for i in lay.items if i.label == label)
    return it, (cx + (it.rect[0] + it.rect[2]) / 2, cy + (it.rect[1] + it.rect[3]) / 2)


def test_drag_back_inside_the_ring_closes_the_submenu():
    s = _session()
    s.move(*_at(O, "E", R + 5), 0.2)
    assert len(s.stack) == 2 and sorted(it.label for it in s.layout.items) == ["UV", "UV Shell"]
    # the submenu's dead zone / just inside the ring: still the submenu
    s.move(*_at(O, "E", R - 5), 0.3)
    assert len(s.stack) == 2 and _label(s) is None
    # well inside the ring, through the submenu's empty west sector: the object menu again, UV hovered, not reopened
    s.move(*_at(O, "E", R - 20), 0.4)
    assert len(s.stack) == 1 and _label(s) == "UV", (len(s.stack), _label(s))
    assert [lay for lay, _c, _h in s.layers()] == [s.stack[0][0]], "only the object menu is drawn"
    assert s.result is None, "the menu stays open"
    s.move(*O, 0.5)
    assert _label(s) is None
    s.move(*_at(O, "W", R + 5), 0.6)
    assert len(s.stack) == 1 and _label(s) == "Vertex"
    res = s.release(*_at(O, "W", R + 5), 0.7)
    assert res[0] == "RUN" and res[1].label == "Vertex", res
    # out again past the ring in the UV sector: the submenu opens once more
    s = _session()
    s.move(*_at(O, "E", R + 5), 0.2)
    s.move(*_at(O, "E", R - 20), 0.3)
    assert len(s.stack) == 1
    s.move(*_at(O, "E", R + 5), 0.4)
    assert len(s.stack) == 2 and s.center == _at(O, "E", R + 5)


def test_submenu_item_toward_the_parent_wins():
    s = _session(mm.SHIFT_EDGE)
    s.move(*_at(O, "N", R + 5), 0.2)
    assert len(s.stack) == 2 and "Target Weld Tool" in [it.label for it in s.layout.items]
    # back toward the press point: the submenu's own south item is there, so it stays open
    s.move(*_at(s.center, "S", 20), 0.3)
    assert len(s.stack) == 2 and _label(s) == "Target Weld Tool", (len(s.stack), _label(s))
    res = s.release(*_at(s.center, "S", 20), 0.4)
    assert res[0] == "RUN" and res[1].label == "Target Weld Tool", res


def test_submenu_opened_far_out_stays_until_the_ring():
    s = _session()
    s.move(*_at(O, "E", 150), 0.2)      # a fast stroke: the submenu opens where the pointer is
    assert len(s.stack) == 2 and s.center == _at(O, "E", 150)
    s.move(*_at(O, "E", 100), 0.3)
    assert len(s.stack) == 2 and _label(s) is None, "west of the submenu's centre, nothing there: still open"
    s.move(*_at(O, "E", 60), 0.4)
    assert len(s.stack) == 2
    s.move(*_at(O, "E", 40), 0.5)
    assert len(s.stack) == 1 and _label(s) == "UV"


def test_click_mode_back_and_pick():
    s = _session()
    assert s.release(*O, 0.1) is None and s.mode == "CLICK"
    s.move(*_at(O, "E", R + 25), 0.3)     # onto the UV box: the submenu opens on hover
    assert len(s.stack) == 2
    s.move(*_at(O, "E", R - 20), 0.4)
    assert len(s.stack) == 1 and s.result is None, "back inside the ring: the object menu again, still open"
    s.move(*_at(O, "W", R + 5), 0.5)
    res = s.click(*_at(O, "W", R + 5), 0.6)
    assert res[0] == "RUN" and res[1].label == "Vertex", res


def test_click_on_a_submenu_box_inside_the_ring():
    s = _session()
    s.release(*O, 0.1)
    s.move(*_at(O, "E", 30), 0.3)
    assert len(s.stack) == 1 and _label(s) == "UV", "inside the ring the box is hovered, not opened"
    assert s.click(*_at(O, "E", 30), 0.4) is None and len(s.stack) == 2 and s.center == _at(O, "E", 30)
    s.move(*_at(O, "E", 25), 0.5)
    assert len(s.stack) == 2, "a submenu that opened inside the ring doesn't close on the spot"
    s.move(*_at(O, "E", 10), 0.6)
    assert len(s.stack) == 1 and _label(s) is None, "near the centre: the object menu again"
    s.move(*_at(O, "W", R + 5), 0.7)
    res = s.click(*_at(O, "W", R + 5), 0.8)
    assert res[0] == "RUN" and res[1].label == "Vertex", res


def test_nested_submenus_go_back_one_level():
    s = _session(mm.OPT_MOVE)
    s.move(*_at(O, "SW", R + 5), 0.2)                 # Axis
    assert len(s.stack) == 2 and "Custom" in [it.label for it in s.layout.items]
    axis = s.center
    s.move(*_at(axis, "SW", R + 5), 0.3)              # Axis > Custom
    assert len(s.stack) == 3
    custom = s.center
    # north-east of Custom's centre (it has no NE item), 15 px from Axis's centre: Axis again, Custom hovered
    s.move(*_at(custom, "NE", 45), 0.4)
    assert len(s.stack) == 2 and _label(s) == "Custom", (len(s.stack), _label(s))
    # through Axis's empty east sector back inside the top menu's ring: the top menu, its south item hovered
    s.move(O[0] + 10, O[1] - 35, 0.5)
    assert len(s.stack) == 1 and _label(s) == "Select", (len(s.stack), _label(s))


def test_esc_closes_only_the_open_submenu():
    s = _session()
    s.move(*_at(O, "E", R + 5), 0.2)
    assert len(s.stack) == 2
    assert s.escape() is None and len(s.stack) == 1 and s.result is None
    assert _label(s) == "UV", "the item whose submenu closed is hovered, the submenu not reopened"
    s.move(*_at(O, "E", R + 8), 0.3)
    assert len(s.stack) == 1, "still on that item: it doesn't reopen"
    s.move(*_at(O, "N", R + 5), 0.4)
    assert len(s.stack) == 1 and _label(s) == "Edge"
    s.move(*_at(O, "E", R + 5), 0.5)
    assert len(s.stack) == 2, "after leaving the item, dragging onto it opens the submenu again"
    assert s.escape() is None and len(s.stack) == 1
    assert s.escape()[0] == "CANCEL", "Esc at the top menu closes it"
    # a list row's cascade closes the same way
    s = _session()
    paint, (px, py) = _row(s, "Paint")
    s.move(px, py, 0.2)
    assert len(s.stack) == 2
    assert s.escape() is None and len(s.stack) == 1 and s.hover[0] is paint
    s.move(px - 2, py, 0.3)
    assert len(s.stack) == 1
    _mat, (mx, my) = _row(s, "Material Attributes...")
    s.move(mx, my, 0.4)
    s.move(px, py, 0.5)
    assert len(s.stack) == 2 and s.layout.sub is paint.sub


def test_cascades_unchanged():
    # a list row's cascade still closes by hovering another row of its menu, not by the ring rule
    s = _session()
    paint, (px, py) = _row(s, "Paint")
    s.move(px, py, 0.2)
    assert len(s.stack) == 2 and s.openers[1] is paint
    s.move(px - 5, py, 0.3)
    assert len(s.stack) == 2 and s.hover[0] is paint
    mat, (mx, my) = _row(s, "Material Attributes...")
    s.move(mx, my, 0.4)
    assert len(s.stack) == 1 and s.hover[0] is mat
