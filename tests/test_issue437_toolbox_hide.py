"""#437: the Tool Box check box (Preferences > UI Elements, Windows > UI Elements, the hotbox) shows or hides the
Tool Box itself, not only the Maya tool list in it."""

import bpy

import kit

MOD = kit.MODULE


def _mod(name):
    from importlib import import_module
    return import_module(MOD + name)


def test_prefs_row_runs_the_toggle():
    data = _mod(".ui.maya_prefs_data")
    rows = [row for _k, _l, _d, _t, sections in data.PAGES for _s, items in sections for row in items]
    tool_box = [row for row in rows if row[-1] == "Tool Box"]
    assert tool_box == [("op", "allset.toolbox_toggle", "Tool Box")], tool_box
    states = _mod(".ui.maya_prefs").OP_STATES
    for row in rows:
        if row[0] == "op":
            assert row[1] in states, row
            assert hasattr(bpy.ops.allset, row[1].split(".")[1]), row


def test_ui_elements_menu_lists_tool_box():
    import inspect
    src = inspect.getsource(_mod(".ui.menu_sets").ALLSET_MT_ui_elements.draw)
    assert "allset.toolbox_toggle" in src
    assert src.index("show_help_line") < src.index("allset.toolbox_toggle"), "Tool Box follows Help Line"


def test_hotbox_item_uses_the_toggle():
    import inspect
    src = inspect.getsource(_mod(".marking.modal").ALLSET_OT_hb_ui.execute)
    assert "toolbox_toggle" in src


def test_factory_screen_is_not_a_kit_layout():
    tl = _mod(".ui.toolbox_layouts")
    screen = bpy.context.window_manager.windows[0].screen
    assert not tl.kit_layout(screen)
    assert tl.toolbox_area(screen) is None
    assert tl.toolbox_shown(None) is False


def test_make_column_gives_a_toolbox_space():
    tl = _mod(".ui.toolbox_layouts")
    screen = bpy.context.window_manager.windows[0].screen
    area = next(a for a in screen.areas if a.type == 'VIEW_3D')
    space = area.spaces.active
    names = ("show_region_toolbar", "show_region_header", "show_region_tool_header", "show_region_ui", "show_gizmo",
             *[n for n in dir(space) if n.startswith("show_object_viewport_")])
    keep = {n: getattr(space, n) for n in names}
    overlays = space.overlay.show_overlays
    try:
        tl.make_column(space)
        assert _mod(".ui.toolbox").is_toolbox(space)
        assert tl.toolbox_area(screen) == area
        assert tl.kit_layout(screen)
        assert tl.toolbox_shown(screen)
        assert not space.overlay.show_overlays
    finally:
        for n, v in keep.items():
            setattr(space, n, v)
        space.overlay.show_overlays = overlays
    assert not _mod(".ui.toolbox").is_toolbox(space)


def test_toggle_does_nothing_in_background():
    with bpy.context.temp_override(window=bpy.context.window_manager.windows[0]):
        assert bpy.ops.allset.toolbox_toggle() == {'CANCELLED'}
