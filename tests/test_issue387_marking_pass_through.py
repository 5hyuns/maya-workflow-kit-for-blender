"""#387: list rows that lie beyond a radial submenu item (Ctrl+RMB Convert Selection: To Shell under To Faces) can be
reached. Like Maya, a radial item's submenu opens when the pointer rests on it (about 0.1 s) while the menu is shown,
not as soon as a stroke passes it: a stroke that keeps moving goes over To Faces (or round it) to the list, a rest
on To Faces (its box, or beyond the ring in its direction) opens its submenu where the pointer is; a click on it opens
it at once. Engine only (no bpy UI). GUI: tests/gui/gui_issue387_marking_pass_through.py."""

import math
from importlib import import_module

import kit

engine = import_module(kit.MODULE + ".marking.engine")
mm = import_module(kit.MODULE + ".marking.menus")

B = (0.0, 0.0, 1400.0, 1200.0)
O = (700.0, 600.0)
P = engine.Params()
R = P.radius
SHOWN = P.show_delay + 0.05            # the menu is drawn by then


def measure(text):
    return 7.0 * len(text)


def _session(menu=mm.CTRL_CONVERT):
    return engine.Session(menu, O, 0.0, measure, None, None, B)


def _row(s, label, level=0):
    lay, (cx, cy) = s.stack[level]
    it = next(i for i in lay.items if i.label == label)
    return (cx + (it.rect[0] + it.rect[2]) / 2, cy + (it.rect[1] + it.rect[3]) / 2)


def _box(s, key, level=0):
    lay, (cx, cy) = s.stack[level]
    it = lay.radial[key]
    return (cx + (it.rect[0] + it.rect[2]) / 2, cy + (it.rect[1] + it.rect[3]) / 2)


def _label(s):
    return s.hover[0].label if s.hover[0] is not None else None


def _stroke(s, a, b, t, px=4.0, dt=0.016):
    """Moves from a to b, ``px`` pixels every ``dt`` s (about 250 px/s), ticking the menu timer on the way like the
    modal does; returns the time after the last move."""
    n = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) // px))
    for k in range(1, n + 1):
        t += dt
        s.move(a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n, t)
        s.tick(t)
    return t


def test_a_moving_stroke_passes_over_to_faces_to_the_list():
    s = _session()
    shell = _row(s, "To Shell")
    assert shell[1] < _box(s, "S")[1], "To Shell is beyond To Faces (y up)"
    t = _stroke(s, O, (O[0], O[1] - R), SHOWN)                # to the To Faces box, the menu shown
    assert len(s.stack) == 1 and _label(s) == "To Faces"
    t = _stroke(s, (O[0], O[1] - R), shell, t)                 # on through it to the list
    assert len(s.stack) == 1, "To Faces didn't open on the way"
    assert _label(s) == "To Shell", _label(s)
    res = s.release(*shell, t + 0.01)
    assert res is not None and res[0] == "RUN" and res[1].label == "To Shell", res


def test_a_quick_stroke_before_the_menu_shows_reaches_the_list():
    s = _session()
    shell = _row(s, "To Shell")
    t = _stroke(s, O, shell, 0.0, px=20.0, dt=0.01)
    assert len(s.stack) == 1 and _label(s) == "To Shell"
    res = s.release(*shell, t + 0.01)
    assert res[0] == "RUN" and res[1].label == "To Shell", res


def test_a_stroke_round_the_side_of_to_faces():
    """Down beside the To Faces box (through the SE sector beyond the ring) and into the list."""
    s = _session()
    lay, _c = s.stack[0]
    x1 = lay.radial["S"].rect[2] + 8                           # just right of the To Faces box
    shell = _row(s, "To Shell")
    t = _stroke(s, O, (O[0] + x1, O[1] - R - 20), SHOWN)
    t = _stroke(s, (O[0] + x1, O[1] - R - 20), (O[0] + x1, shell[1]), t)
    assert len(s.stack) == 1 and _label(s) == "To Shell", (len(s.stack), _label(s))


def test_a_rest_on_to_faces_opens_its_submenu_where_the_pointer_is():
    s = _session()
    p = (O[0], O[1] - R - 5)
    t = _stroke(s, O, p, SHOWN)
    assert len(s.stack) == 1
    s.tick(t + 0.06)
    assert len(s.stack) == 1, "a short rest doesn't open it"
    s.tick(t + P.open_dwell + 0.01)
    assert len(s.stack) == 2 and s.stack[1][1] == p, s.stack[-1][1]
    labels = sorted(it.label for it in s.layout.items)
    assert labels == ["To Contained Faces", "To Face Perimeter", "To Faces"], labels
    # the submenu's own S item, then release: Convert to Faces
    q = (p[0], p[1] - R - 5)
    t = _stroke(s, p, q, t + 0.2)
    res = s.release(*q, t + 0.01)
    assert res[0] == "RUN" and res[1].label == "To Faces", res


def test_small_jitter_keeps_the_rest():
    s = _session()
    p = (O[0], O[1] - R - 5)
    t = _stroke(s, O, p, SHOWN)
    for k in range(6):
        t += 0.02
        s.move(p[0] + (1.0 if k % 2 else -1.0), p[1], t)
        s.tick(t)
    s.tick(t + 0.01)
    assert len(s.stack) == 2, "a still hand opens it"


def test_a_rest_inside_the_box_before_the_ring():
    """The To Faces box reaches inside the ring (its centre is on it): resting on its inner half opens it too."""
    s = _session()
    lay, _c = s.stack[0]
    inner = lay.radial["S"].rect[3] - 3                         # 3 px into the box from its top (y up)
    p = (O[0], O[1] + inner)
    assert math.hypot(p[0] - O[0], p[1] - O[1]) < R
    t = _stroke(s, O, p, SHOWN)
    assert len(s.stack) == 1 and _label(s) == "To Faces"
    s.tick(t + P.open_dwell + 0.01)
    assert len(s.stack) == 2


def test_a_rest_inside_the_ring_off_the_box_does_not_open():
    s = _session()
    p = (O[0], O[1] - (R - P.ring_h / 2 - 4))                  # above the box, To Faces hovered by direction
    t = _stroke(s, O, p, SHOWN)
    assert _label(s) == "To Faces"
    s.tick(t + 1.0)
    assert len(s.stack) == 1


def test_no_rest_before_the_menu_is_shown():
    """A rest that starts before the menu is drawn counts from when it is drawn."""
    s = _session()
    p = (O[0], O[1] - R - 5)
    t = _stroke(s, O, p, 0.0, px=20.0, dt=0.01)
    assert t < P.show_delay
    s.tick(P.show_delay + 0.05)
    assert len(s.stack) == 1
    s.tick(P.show_delay + P.open_dwell + 0.01)
    assert len(s.stack) == 2


def test_click_mode_hover_passes_over_and_a_click_opens():
    s = _session()
    assert s.release(*O, 0.05) is None and s.mode == "CLICK"
    shell = _row(s, "To Shell")
    t = _stroke(s, O, shell, 0.3)
    assert len(s.stack) == 1 and _label(s) == "To Shell"
    # back on To Faces and a click: its submenu at once
    box = _box(s, "S")
    t = _stroke(s, shell, box, t)
    assert s.click(*box, t + 0.01) is None and len(s.stack) == 2


def _quick_release_on(s, key, t0, speed_dt):
    """A stroke from the press point to radial ``key``'s box (beyond the ring in its direction), released at once."""
    box = _box(s, key)
    a = math.atan2(box[1] - O[1], box[0] - O[0])
    end = (O[0] + (R + 12) * math.cos(a), O[1] + (R + 12) * math.sin(a))
    t = _stroke(s, O, end, t0, px=12.0, dt=speed_dt)
    return end, t


def test_a_stroke_released_at_once_on_a_radial_submenu_closes_the_menu():
    """Like Maya: a stroke that ends on a radial submenu item and lets go without a rest runs nothing and closes the
    menu, before and after the menu is drawn (it doesn't stay open in click mode)."""
    for key in ("S", "SE", "N", "E"):
        for t0, dt in ((0.0, 0.01), (SHOWN, 0.01)):
            s = _session()
            end, t = _quick_release_on(s, key, t0, dt)
            want = s.stack[0][0].radial[key].label
            assert len(s.stack) == 1 and _label(s) == want, (key, t0, len(s.stack), _label(s))
            res = s.release(*end, t + 0.01)
            assert res is not None and res[0] == "CANCEL", (key, t0, res)
            assert s.mode == "PRESS", (key, t0, s.mode)


def test_a_release_on_a_radial_submenu_that_did_not_open_closes_the_menu():
    """Resting where the item is hovered but its submenu doesn't open (inside the ring, off its box), then letting
    go: nothing runs and the menu closes, like Maya."""
    s = _session()
    p = (O[0], O[1] - (R - P.ring_h / 2 - 4))
    t = _stroke(s, O, p, SHOWN)
    s.tick(t + 1.0)
    assert len(s.stack) == 1 and _label(s) == "To Faces"
    res = s.release(*p, t + 1.01)
    assert res is not None and res[0] == "CANCEL", res


def test_a_quick_click_still_keeps_the_menu_in_click_mode():
    s = _session()
    s.move(O[0] + 2, O[1] - 1, 0.04)
    assert s.release(O[0] + 2, O[1] - 1, 0.08) is None and s.mode == "CLICK"
    # in click mode a click on To Faces opens it, a rest on it too
    box = _box(s, "S")
    t = _stroke(s, (O[0] + 2, O[1] - 1), box, 0.3)
    assert s.click(*box, t + 0.01) is None and len(s.stack) == 2


def test_a_rest_then_release_on_the_opened_submenu_centre_runs_nothing():
    """After a rest opened To Faces' submenu, letting go where it opened (its centre) runs nothing."""
    s = _session()
    p = (O[0], O[1] - R - 5)
    t = _stroke(s, O, p, SHOWN)
    s.tick(t + P.open_dwell + 0.01)
    assert len(s.stack) == 2
    res = s.release(*p, t + P.open_dwell + 0.02)
    assert res is not None and res[0] == "CANCEL", res
