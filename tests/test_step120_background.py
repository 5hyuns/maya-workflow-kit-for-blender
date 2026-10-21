"""Step 120 / 130: Maya's viewport background — Alt+B cycle (rule and colours measured in Maya 2022,
research/maya/screens/bg120/_bg120.json), every view at once, flat colours only per view (the kit never edits the
user's theme, step 130 #40), Ctrl+B stays Maya's Bevel, Windows > Settings/Preferences > Color Settings."""

import json
from importlib import import_module
from pathlib import Path

import bpy

import kit

kb3 = import_module(kit.MODULE + ".operators.key_batch3")
menu_map = import_module(kit.MODULE + ".ui.menu_map")
menu_sets = import_module(kit.MODULE + ".ui.menu_sets")
notices = import_module(kit.MODULE + ".ui.notices")

ROOT = Path(__file__).resolve().parents[1]
COLORS = ROOT / "research" / "maya" / "colors.json"


def _views():
    return [space for _area, space in kb3.view_spaces()]


def _display(sh):
    return kb3.linear_to_srgb(sh.background_color[0])


def _theme_state():
    t = bpy.context.preferences.themes[0]
    gr = t.view_3d.space.gradients
    return kit._struct_hash(t), gr.background_type, tuple(gr.high_gradient), tuple(gr.gradient)


def test_maya_rule_flat_colours():
    # cycleBackgroundColor.mel: 0 -> 0.36; < 0.5 -> 0.631; else (Maya: gradient) -> black here
    assert [kb3.next_state(s) for s in kb3.CYCLE] == ["LIGHT", "BLACK", "GREY"]
    assert kb3.next_state(0.2) == "LIGHT" and kb3.next_state(0.7) == "BLACK" and kb3.next_state(0.0) == "GREY"
    assert not hasattr(kb3, "theme_gradients") and not hasattr(kb3, "set_gradient")


def test_values_match_maya_measurement():
    if not COLORS.exists():   # research/ is not tracked: present on the measuring PC
        return
    viewport = json.loads(COLORS.read_text(encoding="utf-8"))["viewport"]
    assert tuple(viewport["background_flat"]["rgb"]) == (kb3.FLAT,) * 3
    bg120 = ROOT / "research" / "maya" / "screens" / "bg120" / "_bg120.json"
    if bg120.exists():
        states = json.loads(bg120.read_text())["states"]
        assert [round(s["background"][0], 3) for s in states] == [0.36, 0.631, 0.631, 0.0, 0.36]


def test_cycle_every_view_per_view_colour():
    views = _views()
    assert views, "factory startup has 3D views"
    before = _theme_state()
    sh = views[0].shading
    for v in views:
        v.shading.background_type = 'THEME'      # the user's theme background = Maya's factory starting point
    assert kb3.cycle_background(sh) == "LIGHT"
    assert all(v.shading.background_type == 'VIEWPORT' and abs(_display(v.shading) - 0.631) < 1e-4 for v in views)
    assert kb3.cycle_background(sh) == "BLACK"
    assert all(v.shading.background_type == 'VIEWPORT' and v.shading.background_color[0] == 0.0 for v in views)
    assert kb3.cycle_background(sh) == "GREY"
    assert all(v.shading.background_type == 'VIEWPORT' and abs(_display(v.shading) - 0.36) < 1e-4 for v in views)
    assert kb3.cycle_background(sh) == "LIGHT"
    assert _theme_state() == before, "Alt+B never writes the theme"


def test_reset_is_maya_flat_grey_and_keeps_theme():
    before = _theme_state()
    kb3.reset_background()
    assert all(v.shading.background_type == 'VIEWPORT' and abs(_display(v.shading) - 0.36) < 1e-4 for v in _views())
    assert _theme_state() == before


def test_color_settings_operator():
    before = _theme_state()
    assert bpy.ops.allset.color_settings(background=(0.2, 0.3, 0.4)) == {'FINISHED'}
    sh = _views()[0].shading
    assert sh.background_type == 'VIEWPORT'
    assert abs(kb3.linear_to_srgb(sh.background_color[2]) - 0.4) < 1e-4
    assert bpy.ops.allset.color_settings(background=(0.36, 0.36, 0.36)) == {'FINISHED'}
    assert sh.background_type == 'VIEWPORT' and abs(_display(sh) - 0.36) < 1e-4
    props = {p.identifier for p in bpy.ops.allset.color_settings.get_rna_type().properties}
    assert "gradient" not in props and "background" in props
    assert _theme_state() == before


def test_keys_alt_b_cycles_ctrl_b_bevels():
    kc = bpy.context.window_manager.keyconfigs.active
    km = kc.keymaps["3D View"]
    alt_b = [k for k in km.keymap_items if k.type == 'B' and k.alt and not k.ctrl and not k.shift and k.active]
    assert [k.idname for k in alt_b] == ["allset.cycle_background"]
    assert not [k for km in kc.keymaps for k in km.keymap_items if k.idname == "allset.cycle_background" and k.ctrl]
    mesh = [k.idname for k in kc.keymaps["Mesh"].keymap_items if k.type == 'B' and k.ctrl and not k.alt]
    assert mesh == ["allset.bevel"]      # Maya Ctrl+B = BevelPolygon (hotkeys_default.json, hotkeySetup.mel:385)


def test_settings_preferences_menu():
    kids = [it[0] for it in menu_map.CHILDREN["Windows/Settings/Preferences"] if it[0] != "-"]
    assert kids == ["Preferences", "Hotkey Editor", "Color Settings", "Marking Menu Editor", "Shelf Editor",
                    "Panel Editor", "Plug-in Manager"]
    assert menu_map.MAP["Windows/Settings/Preferences/Color Settings"] == "allset.color_settings"
    assert "Windows/Settings/Preferences" not in menu_map.MAP       # a submenu now, not a leaf
    for label in ("Marking Menu Editor", "Shelf Editor", "Panel Editor"):
        assert f"Windows/Settings/Preferences/{label}" in notices.NOTICES
    paths = {p for p, _it in menu_sets.iter_items()} if hasattr(menu_sets, "iter_items") else set()
    if paths:
        assert "Windows/Settings/Preferences/Color Settings" in paths
