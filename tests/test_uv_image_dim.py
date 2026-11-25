"""UV Editor > Image > Dim: a toggle (off by default) that draws the UV Editor's image at (1 - Dimming) of its
brightness, Dimming 0.5 by default and kept in 0 - 1; its option box is the Image Dim Options; the toolbar's Dim
button toggles the same setting. Image > Unfiltered is greyed with a notice (Blender always draws the image
unfiltered)."""

from importlib import import_module

import bpy

import kit

dim = import_module(kit.MODULE + ".ui.uv_image_dim")
menu_map = import_module(kit.MODULE + ".ui.menu_map")
notices = import_module(kit.MODULE + ".ui.notices")
icons = import_module(kit.MODULE + ".ui.editor_icon_data")
option_box = import_module(kit.MODULE + ".ui.menu_option_box")

PATH = "UV Editor/Image/Dim"


def test_defaults():
    wm = bpy.context.window_manager
    assert wm.allset_uv_image_dim is False
    assert abs(wm.allset_uv_image_dimming - 0.5) < 1e-6


def test_menu_item_toggles_dim():
    wm = bpy.context.window_manager
    assert menu_map.MAP[PATH] == "allset.uv_image_dim", menu_map.MAP.get(PATH)
    assert bpy.ops.allset.uv_image_dim('EXEC_DEFAULT') == {'FINISHED'}
    assert wm.allset_uv_image_dim is True
    assert bpy.ops.allset.uv_image_dim('EXEC_DEFAULT') == {'FINISHED'}
    assert wm.allset_uv_image_dim is False


def test_option_box_opens_the_operator_window():
    assert option_box.option_kind(PATH) == "dialog", option_box.option_kind(PATH)


def test_dimming_range():
    wm = bpy.context.window_manager
    wm.allset_uv_image_dimming = 1.7
    assert abs(wm.allset_uv_image_dimming - 1.0) < 1e-6
    wm.allset_uv_image_dimming = -0.3
    assert wm.allset_uv_image_dimming == 0.0
    wm.allset_uv_image_dimming = 0.5


def test_brightness_left():
    """The overlay alpha leaves (1 - Dimming) of the image's brightness: none at 0, all gone at 1."""
    assert dim.overlay_alpha(0.0) == 0.0
    assert dim.overlay_alpha(1.0) == 1.0
    a = [dim.overlay_alpha(d / 10) for d in range(11)]
    assert all(x <= y for x, y in zip(a, a[1:])), a


def test_udim_tiles():
    img = bpy.data.images.new("dim_udim", 4, 4, tiled=True)
    img.tiles.new(tile_number=1002)
    img.tiles.new(tile_number=1011)
    assert sorted(dim._tiles(img)) == [(0, 0), (0, 1), (1, 0)], dim._tiles(img)
    flat = bpy.data.images.new("dim_flat", 4, 4)
    assert dim._tiles(flat) == [(0, 0)]


def test_toolbar_button_toggles_the_same_setting():
    row = [r for r in icons.UV_ICONS if isinstance(r, tuple) and r[0] == "image_dim"]
    assert row and row[0][2] == ("prop", "window_manager.allset_uv_image_dim", {}), row
    assert "image_dim" not in icons.NOTICES


def test_unfiltered_notice():
    path = "UV Editor/Image/Unfiltered"
    assert path not in menu_map.MAP
    n = notices.greyed_notice(path)
    assert n is not None and "unfiltered" in n[1], n
