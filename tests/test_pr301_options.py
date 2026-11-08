"""#301: the marking menu options Quick Gestures and Submenu Return Ring (add-on preferences, off by default; with
them off the menus behave as before) and the In-View Editor's drag speed, title offset and middle drag (engine and
helpers, no bpy UI). GUI: tests/gui/gui_pr301_in_view.py."""

from importlib import import_module

import kit

engine = import_module(kit.MODULE + ".marking.engine")
mm = import_module(kit.MODULE + ".marking.menus")
modal = import_module(kit.MODULE + ".marking.modal")
preferences = import_module(kit.MODULE + ".preferences")
in_view = import_module(kit.MODULE + ".ui.in_view")
settings = import_module(kit.MODULE + ".ui.in_view_settings")
maya_patches = import_module(kit.MODULE + ".keymap.maya_patches")

B = (0.0, 0.0, 1400.0, 1200.0)
O = (700.0, 600.0)
R = engine.Params.radius
U = engine._UNIT


def measure(text):
    return 7.0 * len(text)


def _params(quick=False, guides=False):
    p = engine.Params()
    p.quick_gestures, p.submenu_guides = quick, guides
    return p


def _session(menu=mm.RMB_MESH, **opts):
    return engine.Session(menu, O, 0.0, measure, _params(**opts), None, B)


def _at(center, direction, dist):
    return (center[0] + U[direction][0] * dist, center[1] + U[direction][1] * dist)


def _label(s):
    return s.hover[0].label if s.hover[0] is not None else None


# --- defaults ---------------------------------------------------------------------------------------------------

def test_options_off_by_default():
    p = preferences.get()
    assert p.mm_quick_gestures is False and p.mm_submenu_guides is False
    assert p.hud_drag_sensitivity == 1.0 and (p.in_view_offset_x, p.in_view_offset_y) == (0.0, 0.0)
    assert engine.Params.quick_gestures is False and engine.Params.submenu_guides is False
    q = modal._params()
    assert q.quick_gestures is False and q.submenu_guides is False
    p.mm_quick_gestures = p.mm_submenu_guides = True
    try:
        q = modal._params()
        assert q.quick_gestures is True and q.submenu_guides is True, "the menus read the preferences"
        assert q.scaled(2.0).quick_gestures is True and q.scaled(2.0).anchor_r == 2 * q.anchor_r
    finally:
        p.mm_quick_gestures = p.mm_submenu_guides = False


def test_default_menu_shows_a_moment_after_the_press():
    s = _session()
    for i in range(1, 30):
        s.move(O[0], O[1] - 2 * i, 0.01 * i)
    assert s.visible(0.3), "options off: shown after the press delay even while the pointer moves"


# --- Quick Gestures ------------------------------------------------------------------------------------------

def test_quick_gestures_hidden_while_moving_shown_after_a_pause():
    s = _session(quick=True)
    for i in range(1, 30):
        s.move(O[0], O[1] - 2 * i, 0.01 * i)
    assert not s.visible(0.3), "the pointer keeps moving: still hidden"
    assert s.visible(0.29 + engine.Params.show_delay + 0.01), "a pause shows it"
    s.move(O[0], O[1] - 70, 0.5)
    assert s.visible(0.51), "once shown it stays"


def test_quick_gestures_mark_picks_radial_items_only():
    # a quick stroke down onto the first list row under the ring: the S item, not the row under the pointer
    origin = (500.0, 400.0)
    rows = [it for it in engine.Session(mm.SHIFT_EDGE, origin, 0.0, measure).layout.items if it.kind == "list"]
    x0, y0, x1, y1 = rows[0].rect
    end = (origin[0] + (x0 + x1) / 2, origin[1] + (y0 + y1) / 2)
    s = engine.Session(mm.SHIFT_EDGE, origin, 0.0, measure, _params(quick=True))
    for i in range(1, 6):
        s.move(origin[0] + (end[0] - origin[0]) * i / 6, origin[1] + (end[1] - origin[1]) * i / 6, 0.01 * i)
    res = s.release(*end, 0.07)
    assert res[0] == "RUN" and res[1].kind == "radial" and res[1].key == "S", res
    s = engine.Session(mm.SHIFT_EDGE, origin, 0.0, measure, _params())
    res = s.release(*end, 0.5)
    assert res[0] == "RUN" and res[1].label == rows[0].label, ("options off: the row", res)


def test_quick_gestures_zigzag_stays_hidden_and_names_the_route():
    s = _session(mm.SHIFT_EDGE, quick=True)
    for i in range(1, 8):
        s.move(*_at(O, "NE", 9 * i), 0.01 * i)
    assert len(s.stack) == 2 and not s.visible(0.08), "a hidden mark entered the submenu: it stays hidden"
    assert [name for _p, name in s.route] == [mm.SHIFT_EDGE.label, "Flip/Spin Edge"], s.route
    x, y = s.pos
    for i in range(1, 8):
        s.move(x - 8 * i, y, 0.08 + 0.01 * i)
    assert not s.visible(0.155), "still hidden until the release"
    res = s.release(x - 60, y, 0.16)
    assert res[0] == "RUN" and res[1].label == "Spin Backward", res


def test_quick_gestures_click_in_the_dead_zone_keeps_the_menu():
    s = _session(quick=True)
    s.move(O[0] + 3, O[1] + 2, 0.05)
    assert s.release(O[0] + 4, O[1] + 2, 0.1) is None and s.mode == "CLICK"
    assert s.visible(0.11)


# --- Submenu Return Ring ----------------------------------------------------------------------------------------

def _rest_near_the_parent(s):
    s.move(*_at(O, "N", R + 5), 0.2)
    assert len(s.stack) == 2 and "Target Weld Tool" in [it.label for it in s.layout.items]
    s.move(O[0] + 12, O[1] - 6, 0.35)      # near the press point, off the submenu's boxes: its S item by direction
    assert len(s.stack) == 2 and _label(s) == "Target Weld Tool"


def test_return_ring_off_by_default():
    s = _session(mm.SHIFT_EDGE)
    _rest_near_the_parent(s)
    assert s.tick(2.0) is False and len(s.stack) == 2 and s.dwell_progress(2.0) is None
    s.move(O[0] + 12, O[1] - 6, 2.5)
    assert len(s.stack) == 2, "options off: resting there changes nothing"


def test_return_ring_rest_goes_back():
    s = _session(mm.SHIFT_EDGE, guides=True)
    _rest_near_the_parent(s)
    assert s.anchors() == [(O, s.stack[1][1])]
    assert s.tick(0.6) is True and len(s.stack) == 2
    centre, progress = s.dwell_progress(0.6)
    assert centre == O and 0.3 < progress < 0.4, progress
    assert s.tick(1.1) is True and len(s.stack) == 1, "0.7 s of rest: the menu it opened from again"
    assert s.mode == "PRESS" and s.result is None and s.anchors() == []
    s.move(*_at(O, "W", R + 5), 1.2)
    res = s.release(*_at(O, "W", R + 5), 1.3)
    assert res[0] == "RUN" and res[1].label == s.stack[0][0].radial["W"].label, res


def test_return_ring_two_stroke_mark_still_reaches_the_item_behind_the_centre():
    s = _session(mm.SHIFT_EDGE, guides=True)
    s.move(*_at(O, "N", R + 5), 0.2)
    s.move(*O, 0.25)            # on the submenu's S box, which covers the press point
    assert s.dwell_progress(2.0) is None
    assert s.tick(2.0) is False and len(s.stack) == 2
    res = s.release(*O, 2.1)
    assert res[0] == "RUN" and res[1].label == "Target Weld Tool", res


# --- In-View Editor ---------------------------------------------------------------------------------------------

def test_in_view_drag_speed_and_offset_settings():
    assert settings.speed() == 1.0, "full speed by default: the rows drag at their own steps"
    try:
        settings.set_sensitivity(0.0)
        assert abs(settings.speed() - 0.02) < 1e-9
        settings.set_sensitivity(2.0)
        assert settings.get_sensitivity() == 1.0
        settings.set_offset(30.0, -12.5)
        assert settings.get_offset() == (30.0, -12.5)
    finally:
        settings.set_sensitivity(1.0)
        settings.set_offset(0.0, 0.0)


def test_in_view_pie_and_rows():
    import math
    cx, cy = 100.0, 100.0
    assert in_view.fan_fraction(cx, cy, cx + 10 * math.cos(math.radians(210)), cy + 10 * math.sin(math.radians(210))) \
        < 1e-6, "empty at eight o'clock"
    assert abs(in_view.fan_fraction(cx, cy, cx, cy + 10) - 1 / 3) < 1e-6, "twelve o'clock: a third, clockwise"
    assert abs(in_view.fan_fraction(cx, cy, cx + 10, cy) - 0.5833333) < 1e-6
    lay = {"title": (0.0, 80.0, 180.0, 96.0), "rows": [("a", 0.0, 64.0, 180.0, 80.0), ("b", 0.0, 48.0, 180.0, 64.0)]}
    fx, fy, fr = in_view.fan_circle(lay, 1.0)
    assert (fx, fy, fr) == (167.0, 88.0, 8.0)
    assert in_view.on_fan(lay, 1.0, fx, fy) and not in_view.on_title(lay, 1.0, fx, fy)
    assert in_view.on_title(lay, 1.0, 20.0, 90.0) and not in_view.on_title(lay, 1.0, 20.0, 70.0)
    assert in_view.row_at(lay, 20.0, 70.0) == 0 and in_view.row_at(lay, 20.0, 50.0) == 1
    assert in_view.row_at(lay, 20.0, 30.0) == -1

    class Spec:
        view_fields = ("keep_faces_together", "thickness", "divisions")

    class Rec:
        spec = Spec()
    assert in_view.first_number_row(Rec()) == 1, "switch rows are skipped"


def test_in_view_operators_and_middle_drag_binding():
    import bpy
    for op in (bpy.ops.allset.inview_fan, bpy.ops.allset.inview_move, bpy.ops.allset.inview_drag):
        assert op.get_rna_type() is not None
    kc = kit.maya_kc()
    mesh = [k for k in kc.keymaps["Mesh"].keymap_items if k.idname == "allset.inview_drag"]
    assert len(mesh) == 1 and (mesh[0].type, mesh[0].value, mesh[0].alt, mesh[0].ctrl, mesh[0].shift) == \
        ('MIDDLEMOUSE', 'PRESS', False, False, False) and mesh[0].properties.row == -1
    assert "allset.inview_drag" in maya_patches.PASS_THROUGH_FIRST
    for km in maya_patches.SLIDER_TOOL_KEYMAPS + ("Object Mode",):
        assert not [k for k in kc.keymaps[km].keymap_items if k.idname == "allset.inview_drag"], km
    # no 3D View in the background: nothing to drag, the Channel Box slider's press passes on
    assert in_view.mmb_drag(bpy.context, type("E", (), {"alt": False, "ctrl": False, "shift": False})()) is False
