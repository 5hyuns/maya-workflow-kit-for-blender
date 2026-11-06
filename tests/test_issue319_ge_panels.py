"""#319: Maya's modular editor windows — the Graph Editor / Dope Sheet / UV Editor as a pane and as a floating
window.

A pane's Maya menu bar ends with the viewport's Panels menu (Panel ▸, Tear Off..., Tear Off Copy...) before the
kit's Blender menu; a floating editor window shows the kit's dotted handle instead and no Panels menu. Tear Off
leaves a 3D View in the pane, Tear Off Copy keeps the editor there. Docking a window splits the main window's
viewport on the chosen side by the window's size (10–45 % of the area), as the smaller part of the split, and
carries the editor's settings over. Headless: the window operators cancel without an error.
"""

import types
from importlib import import_module

import bpy

import kit


def _mod(name):
    return import_module(f"{kit.MODULE}.{name}")


class Rec:
    def __init__(self):
        self.log = []

    def menu(self, idname, text="", icon='NONE', **kw):
        self.log.append(("menu", idname, text))

    def operator(self, idname, text="", icon='NONE', **kw):
        self.log.append(("op", idname, text))
        return types.SimpleNamespace()

    def row(self, **kw):
        return self

    def __getattr__(self, name):
        return lambda *a, **k: types.SimpleNamespace()


def _ctx(space_type, **extra):
    space = types.SimpleNamespace(type=space_type, mode='FCURVES', ui_mode='DOPESHEET', use_normalization=False,
                                  use_auto_normalization=False,
                                  dopesheet=types.SimpleNamespace(show_only_selected=True))
    return types.SimpleNamespace(space_data=space, area=None, scene=bpy.context.scene,
                                 tool_settings=bpy.context.scene.tool_settings,
                                 preferences=bpy.context.preferences, **extra)


def _bar(editor, ctx):
    rec = Rec()
    _mod("ui.editor_chrome").draw_menus(rec, ctx, editor)
    return rec.log


def test_pane_bar_ends_with_panels_then_blender():
    data = _mod("ui.editor_menu_data")
    for editor, space_type in (("Graph Editor", 'GRAPH_EDITOR'), ("Dope Sheet", 'DOPESHEET_EDITOR'),
                               ("UV Editor", 'IMAGE_EDITOR')):
        log = _bar(editor, _ctx(space_type))
        menus = [t for kind, _i, t in log if kind == "menu"]
        titles = [title for title, _items in data.EDITORS[editor]]
        assert menus == titles + ["Panels", "Blender"], (editor, menus)
        idnames = [i for kind, i, _t in log if kind == "menu"]
        assert "ALLSET_MT_panel_panels" in idnames, idnames
        assert not any(i == "allset.dock_handle" for kind, i, _t in log if kind == "op"), log


def test_floating_window_bar_has_the_handle_and_no_panels_menu():
    ep = _mod("ui.editor_panels")
    # a window with one area that is not the first window = a floating kit window (ui/maya_dock.is_floating)
    window = types.SimpleNamespace(screen=types.SimpleNamespace(areas=[object()]))
    for editor, space_type in (("Graph Editor", 'GRAPH_EDITOR'), ("Dope Sheet", 'DOPESHEET_EDITOR'),
                               ("UV Editor", 'IMAGE_EDITOR')):
        area = types.SimpleNamespace(type=space_type, show_menus=True)
        ctx = _ctx(space_type, window=window)
        ctx.area = area
        assert ep.floating_editor(ctx) == editor
        assert not ep.is_pane(ctx)
        log = _bar(editor, ctx)
        menus = [t for kind, _i, t in log if kind == "menu"]
        assert "Panels" not in menus and menus[-1] == "Blender", menus
        assert any(i == "allset.dock_handle" for kind, i, _t in log if kind == "op"), log
    # an area of a window with several areas is a pane
    main = types.SimpleNamespace(screen=types.SimpleNamespace(areas=[object(), object()]))
    ctx = _ctx('GRAPH_EDITOR', window=main)
    ctx.area = types.SimpleNamespace(type='GRAPH_EDITOR', show_menus=True)
    assert ep.is_pane(ctx) and ep.floating_editor(ctx) is None
    # the handle's popup: the four sides
    rec = Rec()
    ep.draw_dock_items(rec)
    assert [t for _k, _i, t in rec.log] == ["Dock Bottom", "Dock Left", "Dock Right", "Dock Top"], rec.log
    assert all(i == "allset.editor_dock" for _k, i, _t in rec.log)


def test_split_puts_the_editor_on_the_asked_side_as_the_smaller_part():
    ep = _mod("ui.editor_panels")
    assert ep.split('BOTTOM', 200, 1000) == ('HORIZONTAL', 0.2)
    assert ep.split('TOP', 200, 1000) == ('HORIZONTAL', 0.8)
    assert ep.split('LEFT', 300, 1000) == ('VERTICAL', 0.3)
    assert ep.split('RIGHT', 300, 1000) == ('VERTICAL', 0.7)
    # never thinner than 10 % nor more than 45 % of the area: the new area of a split is the smaller part, so a
    # share over a half would land on the other side (and the main viewport stays the bigger part)
    assert ep.split('BOTTOM', 20, 1000) == ('HORIZONTAL', 0.1)
    assert ep.split('BOTTOM', 900, 1000)[1] == 0.45
    assert ep.split('RIGHT', 900, 1000)[1] == 0.55
    assert ep.split('LEFT', 50, 0)[1] == 0.45     # a zero-size area: no division error, clamped


def test_panels_menu_rows_tear_off_moves_and_copy_copies():
    data = _mod("ui.panel_menu_data")
    rows = {row[1]: row for row in data.PANELS if row[0] == "run"}
    assert rows["Tear Off..."][2] == "allset.panel_tear_off" and rows["Tear Off..."][3] == {"copy": False}
    assert rows["Tear Off Copy..."][2] == "allset.panel_tear_off" and rows["Tear Off Copy..."][3] == {}
    assert ("menu", "Panel", "ALLSET_MT_panel_panel") in data.PANELS
    # the Panel submenu lists the editors a pane can become (Maya Panels > Panel)
    names = [label for label, _t in data.PANEL_TYPES]
    for name in ("Graph Editor", "Dope Sheet", "UV Editor", "Outliner", "Model Panel"):
        assert name in names, names


def _two_areas():
    wm = bpy.context.window_manager
    window = wm.windows[0]
    areas = sorted(window.screen.areas, key=lambda a: a.width * a.height, reverse=True)
    assert len(areas) >= 2, [a.type for a in areas]
    return window, areas[0], areas[1]


def test_copy_settings_carries_the_editor_settings_over():
    ep = _mod("ui.editor_panels")
    window, a, b = _two_areas()
    with bpy.context.temp_override(window=window, screen=window.screen, area=a):
        a.ui_type = 'FCURVES'
    with bpy.context.temp_override(window=window, screen=window.screen, area=b):
        b.ui_type = 'FCURVES'
    src, dst = a.spaces.active, b.spaces.active
    src.show_cursor = not dst.show_cursor
    src.show_sliders = not dst.show_sliders
    src.dopesheet.show_only_selected = not dst.dopesheet.show_only_selected
    src.dopesheet.show_hidden = not dst.dopesheet.show_hidden
    src.pivot_point = 'CURSOR' if dst.pivot_point != 'CURSOR' else 'INDIVIDUAL_ORIGINS'
    ep.copy_settings(src, dst)
    assert dst.show_cursor == src.show_cursor and dst.show_sliders == src.show_sliders
    assert dst.dopesheet.show_only_selected == src.dopesheet.show_only_selected
    assert dst.dopesheet.show_hidden == src.dopesheet.show_hidden
    assert dst.pivot_point == src.pivot_point
    assert dst.type == 'GRAPH_EDITOR'            # read-only properties are left alone (no error)


def test_window_operators_cancel_headless():
    window, a, _b = _two_areas()
    with bpy.context.temp_override(window=window, screen=window.screen, area=a):
        a.ui_type = 'FCURVES'
        kind = a.ui_type
        assert bpy.ops.allset.panel_tear_off(copy=False) == {'CANCELLED'}
        assert a.ui_type == kind                   # the pane isn't turned into a 3D View when no window opened
        assert bpy.ops.allset.editor_dock(side='BOTTOM') == {'CANCELLED'}   # not a floating window
    ep = _mod("ui.editor_panels")
    assert ep.dock(bpy.context, window, 'BOTTOM') is False
