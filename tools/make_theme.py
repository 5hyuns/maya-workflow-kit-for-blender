"""Generate the Maya grey theme preset src/maya_kit/theme/maya.xml.

    python tools/make_theme.py      # re-runs itself in `blender -b --factory-startup`

Resets Blender's theme to the factory default, applies the colour table below
and writes the theme with Blender's own preset writer (`rna_xml.xml_file_write`
with the map of USERPREF_MT_interface_theme_presets, $S\\startup\\bl_ui\\
space_userpref.py:933-943). Applying it through `script.execute_preset`
resets to the default first, so the result is always "Blender default + this
table".

Evidence tags (docs/steps/step_5.md 「테마」):
  [O-pref] user's Maya 2022 prefs, ~/Documents/maya/2022/prefs/userRGBColors2.mel
           (displayRGBColor values) and userPrefs.mel (displayViewportGradient 1)
  [O-mel]  Maya 2022 scripts/others/cycleBackgroundColor.mel:29 (flat bg default 0.36)
  [O-res]  research/maya/ui_layout.md:303 (welcome.qss bg #535353)
  [K]      known Maya 2022 look; the UI palette is compiled into Maya
           (research/maya/ui_layout.md:303,310 [U]), so these are approximations.
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "src" / "maya_kit" / "theme" / "maya.xml"


def rgb(v):
    """'#rrggbb' -> (r, g, b) floats."""
    v = v.lstrip("#")
    return tuple(int(v[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def grey(f):
    return (f, f, f)


PANEL = rgb("#444444")        # [K] Maya panel background
BUTTON = rgb("#5d5d5d")       # [K] Maya button
FIELD = rgb("#2b2b2b")        # [K] Maya text/number field; = timeSliderBackground 0.168627 [O-pref]
SELECT = rgb("#5285a6")       # [K] Maya selection highlight blue
TEXT = rgb("#eeeeee")         # [K]
TEXT_DIM = rgb("#bbbbbb")     # [K]
MENU = rgb("#535353")         # [O-res] welcome bg #535353, used for menus/popups
OUTLINER_BG = rgb("#373737")  # [O] Maya Outliner list (colors.json ui_samples.outliner_list_bg, step 43)
TAB_OFF = rgb("#373737")      # [O] unselected shelf tab / tab row (ui_samples.shelf_tab_inactive)
TAB_ON = rgb("#444444")       # [O] selected shelf tab (ui_samples.shelf_tab_active)
SEL_TEXT = rgb("#ffffff")     # [O] Qt HighlightedText (colors.json ui_palette_qt)

# Widget colour sets: (path, inner, inner_sel, text, text_sel)
WIDGETS = (
    ("wcol_regular", BUTTON, SELECT, TEXT, TEXT),
    ("wcol_tool", BUTTON, SELECT, TEXT, TEXT),
    ("wcol_toolbar_item", PANEL, SELECT, TEXT, TEXT),
    ("wcol_radio", BUTTON, SELECT, TEXT, TEXT),
    ("wcol_toggle", BUTTON, SELECT, TEXT, TEXT),
    ("wcol_option", FIELD, SELECT, TEXT, TEXT),
    ("wcol_text", FIELD, FIELD, TEXT, TEXT),
    ("wcol_num", FIELD, FIELD, TEXT, TEXT),
    ("wcol_numslider", FIELD, FIELD, TEXT, TEXT),
    ("wcol_box", PANEL, BUTTON, TEXT, TEXT),
    ("wcol_menu", BUTTON, SELECT, TEXT, TEXT),
    ("wcol_pulldown", PANEL, SELECT, TEXT, TEXT),
    ("wcol_menu_back", MENU, MENU, TEXT, TEXT),
    ("wcol_pie_menu", MENU, SELECT, TEXT, TEXT),
    ("wcol_tooltip", FIELD, FIELD, TEXT, TEXT),
    ("wcol_menu_item", MENU, SELECT, TEXT, TEXT),
    ("wcol_list_item", OUTLINER_BG, SELECT, TEXT, TEXT),
    ("wcol_tab", TAB_OFF, TAB_ON, TEXT_DIM, TEXT),
)

# Single values: (path from the Theme, value)
VALUES = (
    # 3D viewport background: Maya 2022 factory = flat 0.36 grey, gradient off (displayPref
    # -displayGradient false, displayRGBColor background 0.36; research/maya/colors.json "viewport",
    # docs/steps/step_40.md). The earlier gradient came from the user's own Maya prefs [O-pref].
    ("view_3d.space.gradients.background_type", 'SINGLE_COLOR'),
    ("view_3d.space.gradients.high_gradient", (0.36, 0.36, 0.36)),     # background (flat)
    ("view_3d.space.gradients.gradient", (0.052, 0.052, 0.052)),        # backgroundBottom (Alt+B)
    # Grid: displayColor grid = colorIndex 2 (0.25 grey), changed with the flat background or the
    # grid (was 0.36) would vanish into it (step_40.md blindspot 3).
    ("view_3d.grid", (0.25, 0.25, 0.25, 1.0)),
    ("view_3d.wire", (0.0, 0.016, 0.376)),           # [K] dormant mesh wire: dark blue
    # Maya lead (last selected = Blender active) is light green, other selected white: displayColor
    # lead 19 / active 16 (research/maya/colors.json "viewport", screens/04_wire_selected_lead.png) [O]
    ("view_3d.object_selected", (1.0, 1.0, 1.0)),
    ("view_3d.object_active", (0.263, 1.0, 0.639)),
    # Components (research/maya/colors.json "viewport" displayColor, docs/steps/step_43.md) [O]:
    # component-mode wire = hilite 18, unselected vertex = hiliteComponent 9, selected vertex =
    # polyVertex 17, selected edge/face = polyEdge/polyFace 21. Maya stipples selected faces
    # (25 % of the pixels) -> the same average colour as a uniform fill of effective alpha 0.25.
    # Measured in look_compare (viewport.md, face mode): face_select alone draws ~0.19 whatever its
    # alpha (0.25 and 0.33 both gave 0.19-0.20) and face_mode_select is painted on top (0.25 -> 0.41
    # total) -> face_mode_select 0.07 for an effective 0.25 (docs/steps/step_43.md).
    ("view_3d.wire_edit", rgb("#64dcff")),
    ("view_3d.vertex", rgb("#c800c8")),
    ("view_3d.vertex_select", rgb("#fdff88")),       # drawn pale yellow, not colorIndex 17 (08 shot)
    ("view_3d.edge_select", rgb("#e4ac79")),
    ("view_3d.edge_mode_select", rgb("#e4ac79")),
    ("view_3d.face_select", (*rgb("#e4ac79"), 0.25)),
    ("view_3d.face_mode_select", (*rgb("#e4ac79"), 0.07)),
    # Manipulator: transformX/Y (0.9 red / green); Z as drawn = pure blue (Move/Scale axis pixels
    # in 02/06; displayRGBColor transformZ 0.29/0.57/1 is not what VP2 draws). Active/hovered
    # handle = manipCurrent 17 (yellow) [O]. Blender's axis colours also paint the grid axis
    # lines: the MayaKit template hides those (step 43).
    ("user_interface.axis_x", rgb("#e60000")),
    ("user_interface.axis_y", rgb("#00e600")),
    ("user_interface.axis_z", rgb("#0000ff")),
    ("user_interface.gizmo_primary", rgb("#ffff00")),
    ("user_interface.gizmo_hi", rgb("#ffff00")),
    # 3D View header, tool header, toolbar and sidebar are opaque panels in Maya (panel menu bar /
    # icon bar / Tool Box / Channel Box dock = #444444, colors.json ui_samples); Blender draws them
    # see-through over the view by default (header alpha 0.7, regions 0) (step 41 pixels.md).
    ("view_3d.space.header", (*PANEL, 1.0)),
    ("view_3d.space.button", (*PANEL, 1.0)),
    # Timeline / Dope Sheet: time slider colours [O-pref]
    ("dopesheet_editor.space.back", (0.168627, 0.168627, 0.168627)),    # timeSliderBackground
    ("dopesheet_editor.keyframe", (1.0, 0.0, 0.0)),                     # timeSliderKey
    ("dopesheet_editor.keyframe_selected", (0.9, 0.9, 0.0)),            # timeSliderActiveKey
    ("dopesheet_editor.frame_current", (0.78, 0.78, 0.78)),             # timeSliderCurrentFrame [O]
    # Graph Editor grid [O-pref]
    ("graph_editor.grid", (0.325, 0.325, 0.325)),                       # graphEditorGrid
    # Outliner
    ("outliner.space.back", OUTLINER_BG),
    ("outliner.selected_highlight", SELECT),
    ("outliner.active", SELECT),                     # [O] the lead row is the same blue (step 41 pixels)
    ("outliner.selected_object", SEL_TEXT),          # [O] selected names are white, not orange
    ("outliner.active_object", SEL_TEXT),
)

# Editors whose generic space colours get the Maya panel grey.
EDITORS = ("view_3d", "graph_editor", "dopesheet_editor", "nla_editor", "image_editor",
           "sequence_editor", "properties", "text_editor", "node_editor", "outliner",
           "info", "file_browser", "console", "clip_editor", "topbar", "statusbar",
           "spreadsheet", "preferences")


def run_outside_blender():
    import subprocess
    sys.path.insert(0, str(ROOT / "tools"))
    import build
    r = subprocess.run([os.environ.get("BLENDER", build.DEFAULT_BLENDER), "-b", "--factory-startup",
                        "--python-exit-code", "1", "--python", __file__],
                       env=build.sandbox_env(), stdin=subprocess.DEVNULL,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    for line in r.stdout.splitlines():
        if line.startswith("make_theme"):
            print(line)
    if r.returncode:
        sys.stderr.write(r.stdout[-3000:] + r.stderr[-3000:])
    return r.returncode


def _set(owner, path, value):
    *parents, attr = path.split(".")
    for p in parents:
        owner = getattr(owner, p)
    current = getattr(owner, attr)  # AttributeError = path drifted: fail loudly
    if isinstance(value, tuple) and hasattr(current, "__len__") and len(current) == 4 and len(value) == 3:
        value = (*value, current[3])
    setattr(owner, attr, value)


def apply_table(theme):
    ui = theme.user_interface
    for name, inner, inner_sel, text, text_sel in WIDGETS:
        w = getattr(ui, name)
        _set(w, "inner", inner)
        _set(w, "inner_sel", inner_sel)
        _set(w, "text", text)
        _set(w, "text_sel", text_sel)
    for editor in EDITORS:
        space = getattr(theme, editor).space
        for attr in ("back", "header", "button"):
            if hasattr(space, attr):
                _set(space, attr, PANEL)
        for attr in ("text", "header_text", "button_text"):
            if hasattr(space, attr):
                _set(space, attr, TEXT_DIM if attr == "text" else TEXT)
        # Region tab strips (sidebar tabs): Maya's dock tab strip / tabs (ui_samples
        # dock_side_tab_strip #373737, layer_tab_active #444444) [O]
        if hasattr(space, "tab_back"):
            _set(space, "tab_back", TAB_OFF)
            _set(space, "tab_active", TAB_ON)
            _set(space, "tab_inactive", TAB_OFF)
            _set(space, "tab_outline", rgb("#2b2b2b"))
        if hasattr(space, "panelcolors"):
            _set(space.panelcolors, "header", BUTTON)
            _set(space.panelcolors, "back", PANEL)
    for path, value in VALUES:
        _set(theme, path, value)


def main():
    import bpy
    import rna_xml
    from bl_ui.space_userpref import USERPREF_MT_interface_theme_presets as presets

    bpy.ops.preferences.reset_default_theme()
    apply_table(bpy.context.preferences.themes[0])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    rna_xml.xml_file_write(bpy.context, str(OUT), presets.preset_xml_map)
    print(f"make_theme: wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    try:
        import bpy  # noqa: F401
    except ImportError:
        sys.exit(run_outside_blender())
    main()
