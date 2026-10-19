"""Step 120: Maya's viewport background — Alt+B cycle (rule and colours measured in Maya 2022,
research/maya/screens/bg120/_bg120.json), every view at once, the gradient in the kit's Maya theme only, Ctrl+B stays
Maya's Bevel, Windows > Settings/Preferences > Color Settings, and the factory background = Maya's flat 0.36."""

import json
import math
import xml.etree.ElementTree as ET
from importlib import import_module
from pathlib import Path

import bpy

import kit

kb3 = import_module(kit.MODULE + ".operators.key_batch3")
theme = import_module(kit.MODULE + ".theme")
menu_map = import_module(kit.MODULE + ".ui.menu_map")
menu_sets = import_module(kit.MODULE + ".ui.menu_sets")
notices = import_module(kit.MODULE + ".ui.notices")

ROOT = Path(__file__).resolve().parents[1]
COLORS = ROOT / "research" / "maya" / "colors.json"
THEME_DIR = ROOT / "src" / "allset" / "theme"


def _views():
    return [space for _area, space in kb3.view_spaces()]


def _lab(rgb):
    def lin(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(c) for c in rgb)
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883

    def f(t):
        return t ** (1 / 3) if t > 216 / 24389 else (24389 / 27 * t + 16) / 116
    return 116 * f(y) - 16, 500 * (f(x) - f(y)), 200 * (f(y) - f(z))


def _de76(a, b):
    return math.dist(_lab(a), _lab(b))     # ΔE76 ≥ ΔE00 for these near-greys: a stricter bound


def test_maya_rule():
    # cycleBackgroundColor.mel: gradient -> black; 0 -> 0.36; < 0.5 -> 0.631; else gradient
    assert [kb3.next_state(s) for s in kb3.CYCLE] == ["LIGHT", "GRADIENT", "BLACK", "GREY"]
    assert kb3.next_state(0.2) == "LIGHT" and kb3.next_state(0.7) == "GRADIENT" and kb3.next_state(0.0) == "GREY"
    assert kb3.next_state("LIGHT", gradient_ok=False) == "BLACK"
    assert kb3.next_state(0.7, gradient_ok=False) == "BLACK"


def test_values_match_maya_measurement():
    viewport = json.loads(COLORS.read_text(encoding="utf-8"))["viewport"]
    assert tuple(viewport["background_flat"]["rgb"]) == (kb3.FLAT,) * 3
    assert tuple(viewport["background_gradient_top"]["rgb"]) == kb3.GRADIENT_TOP
    assert tuple(viewport["background_gradient_bottom"]["rgb"]) == kb3.GRADIENT_BOTTOM
    assert viewport["gradient_default_on"] is False
    bg120 = ROOT / "research" / "maya" / "screens" / "bg120" / "_bg120.json"
    if bg120.exists():   # research/ is not tracked: present on the measuring PC
        states = json.loads(bg120.read_text())["states"]
        assert [round(s["background"][0], 3) for s in states] == [0.36, 0.631, 0.631, 0.0, 0.36]
        assert [s["gradient"] for s in states] == [False, False, True, False, False]


def test_cycle_every_view_with_maya_theme():
    views = _views()
    assert views, "factory startup has 3D views"
    theme.apply()
    try:
        gr = kb3.theme_gradients()
        assert gr.background_type == 'SINGLE_COLOR' and abs(gr.high_gradient[0] - 0.36) < 1e-3
        sh = views[0].shading
        for v in views:
            v.shading.background_type = 'THEME'
        assert kb3.cycle_background(sh) == "LIGHT"
        assert all(v.shading.background_type == 'VIEWPORT'
                   and abs(kb3.linear_to_srgb(v.shading.background_color[0]) - 0.631) < 1e-4 for v in views)
        assert kb3.cycle_background(sh) == "GRADIENT"
        assert gr.background_type == 'LINEAR' and all(v.shading.background_type == 'THEME' for v in views)
        # theme colours are stored as bytes: within 1/255
        assert all(abs(a - b) <= 1 / 255 for a, b in zip(gr.high_gradient, kb3.GRADIENT_TOP))
        assert all(abs(a - b) <= 1 / 255 for a, b in zip(gr.gradient, kb3.GRADIENT_BOTTOM))
        assert kb3.cycle_background(sh) == "BLACK"
        assert gr.background_type == 'SINGLE_COLOR' and abs(gr.high_gradient[0] - 0.36) < 1e-3
        assert all(v.shading.background_color[0] == 0.0 for v in views)
        assert kb3.cycle_background(sh) == "GREY"
        assert all(v.shading.background_type == 'THEME' for v in views)
    finally:
        theme.restore()


def test_user_theme_is_never_edited():
    gr = kb3.theme_gradients()
    before = (gr.background_type, tuple(gr.high_gradient), tuple(gr.gradient))
    sh = _views()[0].shading
    for _ in range(4):
        kb3.cycle_background(sh)
    assert (gr.background_type, tuple(gr.high_gradient), tuple(gr.gradient)) == before
    kb3.reset_background()
    assert all(v.shading.background_type == 'THEME' for v in _views())


def test_color_settings_operator():
    theme.apply()
    try:
        assert bpy.ops.allset.color_settings(background=(0.2, 0.3, 0.4)) == {'FINISHED'}
        sh = _views()[0].shading
        assert sh.background_type == 'VIEWPORT'
        assert abs(kb3.linear_to_srgb(sh.background_color[2]) - 0.4) < 1e-4
        assert bpy.ops.allset.color_settings(gradient=True, gradient_top=(0.9, 0.0, 0.0)) == {'FINISHED'}
        assert kb3.theme_gradients().background_type == 'LINEAR' and sh.background_type == 'THEME'
        assert abs(kb3.theme_gradients().high_gradient[0] - 0.9) <= 1 / 255
        assert bpy.ops.allset.color_settings(background=(0.36, 0.36, 0.36)) == {'FINISHED'}
        assert sh.background_type == 'THEME' and kb3.theme_gradients().background_type == 'SINGLE_COLOR'
    finally:
        theme.restore()


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


def test_factory_background_is_maya_flat():
    """Every Maya theme file (4.5 and each 5.x) draws Maya's factory viewport: flat 0.36, no gradient (ΔE ≤ 2)."""
    maya = tuple(json.loads(COLORS.read_text(encoding="utf-8"))["viewport"]["background_flat"]["rgb"])
    files = sorted(THEME_DIR.glob("studio_grey*.xml"))
    assert len(files) >= 4
    for f in files:
        root = ET.parse(f).getroot()
        grads = [e for e in root.iter() if e.tag == "ThemeGradientColors"]
        assert grads, f.name
        g = grads[0]     # the first is the 3D View's (rna_xml writes view_3d before the other editors)
        assert g.get("background_type") == "SINGLE_COLOR", f.name
        hi = g.get("high_gradient").lstrip("#")
        rgb = tuple(int(hi[i:i + 2], 16) / 255 for i in (0, 2, 4))
        assert _de76(rgb, maya) <= 2.0, (f.name, rgb)
