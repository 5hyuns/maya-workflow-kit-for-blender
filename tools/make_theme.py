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
OUTLINER_BG = rgb("#2b2b2b")  # [K] Maya Outliner list background

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
    ("wcol_tab", PANEL, BUTTON, TEXT_DIM, TEXT),
)

# Single values: (path from the Theme, value)
VALUES = (
    # 3D viewport background: gradient on, Maya defaults [O-pref]
    ("view_3d.space.gradients.background_type", 'LINEAR'),
    ("view_3d.space.gradients.high_gradient", (0.535, 0.617, 0.702)),   # backgroundTop
    ("view_3d.space.gradients.gradient", (0.052, 0.052, 0.052)),        # backgroundBottom
    ("view_3d.grid", (0.36, 0.36, 0.36, 1.0)),       # [K] grey grid (flat bg default 0.36 [O-mel])
    ("view_3d.wire", (0.0, 0.016, 0.376)),           # [K] dormant mesh wire: dark blue
    ("view_3d.object_selected", (0.263, 1.0, 0.639)),  # [K] selected: light green
    ("view_3d.object_active", (1.0, 1.0, 1.0)),      # [K] lead (last) selected: white
    ("view_3d.wire_edit", (0.0, 0.016, 0.376)),      # [K] component-mode wire
    # Timeline / Dope Sheet: time slider colours [O-pref]
    ("dopesheet_editor.space.back", (0.168627, 0.168627, 0.168627)),    # timeSliderBackground
    ("dopesheet_editor.keyframe", (1.0, 0.0, 0.0)),                     # timeSliderKey
    ("dopesheet_editor.keyframe_selected", (0.9, 0.9, 0.0)),            # timeSliderActiveKey
    ("dopesheet_editor.frame_current", (1.0, 0.0, 0.0)),                # [K] red current-time marker
    # Graph Editor grid [O-pref]
    ("graph_editor.grid", (0.325, 0.325, 0.325)),                       # graphEditorGrid
    # Outliner
    ("outliner.space.back", OUTLINER_BG),
    ("outliner.selected_highlight", SELECT),
    ("outliner.active", rgb("#6b9dc0")),             # [K] lighter blue for the lead item
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
