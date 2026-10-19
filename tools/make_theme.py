"""Generate the Maya grey theme presets src/allset/theme/studio_grey*.xml.

    python tools/make_theme.py      # re-runs itself in `blender -b --factory-startup` of every Blender:
                                    # 4.5 -> studio_grey.xml, each portable 5.x minor -> studio_grey_<5.m>.xml

Blender 5.0 rewrote the theme ( "테마 차이", tools/theme_diff.py): this is the one place
that branches per version (step 119). A 5.x file = factory 5.x theme + the same table (paths only 4.5 has are
skipped) + every 5.0-moved value copied from the 4.5 file (src/allset/theme MOVED, Blender's official migration
table) + the 5.x-only keys below (FIVE_X), so no Blender default colour is left where Maya has one.

Resets Blender's theme to the factory default, applies the colour table below
and writes the theme with Blender's own preset writer (`rna_xml.xml_file_write`
with the map of USERPREF_MT_interface_theme_presets, $S\\startup\\bl_ui\\
space_userpref.py:933-943). Applying it through `script.execute_preset`
resets to the default first, so the result is always "Blender default + this
table".

Evidence tags:
  [O-pref] user's Maya 2022 prefs, ~/Documents/maya/2022/prefs/Maya
           (displayRGBColor values) and Maya (displayViewportGradient 1)
  [O-mel]  Maya 2022 scripts/others/Maya (flat bg default 0.36)
  [O-res]   (welcome.qss bg #535353)
        known Maya 2022 look; the UI palette is compiled into Maya
           (,310 ), so these are approximations.
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "src" / "allset" / "theme" / "studio_grey.xml"


def rgb(v):
    """'#rrggbb' -> (r, g, b) floats."""
    v = v.lstrip("#")
    return tuple(int(v[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def grey(f):
    return (f, f, f)


PANEL = rgb("#444444")        #  Maya panel background
BUTTON = rgb("#5d5d5d")       #  Maya button
FIELD = rgb("#2b2b2b")        #  Maya text/number field; = timeSliderBackground 0.168627 [O-pref]
SELECT = rgb("#5285a6")       #  Maya selection highlight blue
TEXT = rgb("#eeeeee")         # 
TEXT_DIM = rgb("#bbbbbb")     # 
MENU = rgb("#535353")         # [O-res] welcome bg #535353, used for menus/popups
OUTLINER_BG = rgb("#373737")  #  Maya Outliner list (colors.json ui_samples.outliner_list_bg, step 43)
TAB_OFF = rgb("#373737")      #  unselected shelf tab / tab row (ui_samples.shelf_tab_inactive)
TAB_ON = rgb("#444444")       #  selected shelf tab (ui_samples.shelf_tab_active)
SEL_TEXT = rgb("#ffffff")     #  Qt HighlightedText (colors.json ui_palette_qt)

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
    # -displayGradient false, displayRGBColor background 0.36;  "viewport",
    # ). The earlier gradient came from the user's own Maya prefs [O-pref].
    ("view_3d.space.gradients.background_type", 'SINGLE_COLOR'),
    ("view_3d.space.gradients.high_gradient", (0.36, 0.36, 0.36)),     # background (flat)
    ("view_3d.space.gradients.gradient", (0.052, 0.052, 0.052)),        # backgroundBottom (Alt+B)
    # Grid: displayColor grid = colorIndex 2 (0.25 grey), changed with the flat background or the
    # grid (was 0.36) would vanish into it ( blindspot 3).
    ("view_3d.grid", (0.25, 0.25, 0.25, 1.0)),
    ("view_3d.wire", (0.0, 0.016, 0.376)),           #  dormant mesh wire: dark blue
    # Maya lead (last selected = Blender active) is light green, other selected white: displayColor
    # lead 19 / active 16 ( "viewport", screens/04_wire_selected_lead.png) 
    ("view_3d.object_selected", (1.0, 1.0, 1.0)),
    ("view_3d.object_active", (0.263, 1.0, 0.639)),
    # Components ( "viewport" displayColor, ) :
    # component-mode wire = hilite 18, unselected vertex = hiliteComponent 9, selected vertex =
    # polyVertex 17, selected edge/face = polyEdge/polyFace 21. Maya stipples selected faces
    # (25 % of the pixels) -> the same average colour as a uniform fill of effective alpha 0.25.
    # checked in look_compare (viewport.md, face mode): face_select alone draws ~0.19 whatever its
    # alpha (0.25 and 0.33 both gave 0.19-0.20) and face_mode_select is painted on top (0.25 -> 0.41
    # total) -> face_mode_select 0.07 for an effective 0.25. Step 44: that base (02)
    # had the Move manipulator over the sample; against 03 (same view, no manipulator) 0.07 gives an
    # effective 0.07, and the fill rises ~0.86 per unit of alpha (probe) -> 0.28.
    ("view_3d.wire_edit", rgb("#64dcff")),
    ("view_3d.vertex", rgb("#c800c8")),
    ("view_3d.vertex_select", rgb("#fdff88")),       # drawn pale yellow, not colorIndex 17 (08 shot)
    ("view_3d.edge_select", rgb("#e4ac79")),
    ("view_3d.edge_mode_select", rgb("#e4ac79")),
    ("view_3d.face_select", (*rgb("#e4ac79"), 0.25)),
    ("view_3d.face_mode_select", (*rgb("#e4ac79"), 0.28)),
    # Manipulator: transformX/Y (0.9 red / green); Z as drawn = pure blue (Move/Scale axis pixels
    # in 02/06; displayRGBColor transformZ 0.29/0.57/1 is not what VP2 draws). Active/hovered
    # handle = manipCurrent 17 (yellow) . Blender's axis colours also paint the grid axis
    # lines: the Allset template hides those (step 43).
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
    ("dopesheet_editor.frame_current", (0.78, 0.78, 0.78)),             # timeSliderCurrentFrame 
    # Graph Editor grid [O-pref]
    ("graph_editor.grid", (0.325, 0.325, 0.325)),                       # graphEditorGrid
    # No shading outside the playback range: the kit keeps Maya's playback range in Blender's preview range
    # (step 20), and Blender shades everything outside it in this colour (brown #a14d0066 by default); Maya's
    # Graph Editor / Dope Sheet show the frames outside it unshaded (, step 104).
    ("graph_editor.preview_range", (0.0, 0.0, 0.0, 0.0)),
    ("dopesheet_editor.preview_range", (0.0, 0.0, 0.0, 0.0)),
    # Outliner
    ("outliner.space.back", OUTLINER_BG),
    ("outliner.selected_highlight", SELECT),
    ("outliner.active", SELECT),                     #  the lead row is the same blue (step 41 pixels)
    ("outliner.selected_object", SEL_TEXT),          #  selected names are white, not orange
    ("outliner.active_object", SEL_TEXT),
    #  Maya's Outliner list is one flat colour (): no
    # Blender alternating row stripes (step 99)
    ("outliner.row_alternate", (1.0, 1.0, 1.0, 0.0)),
)

# Widget shape: Maya 2022's Qt style is "adskdarkflatui" (
# ui_style; screens/11b_channel_box_crop.png, 12_create_menu.png): square, flat, no bevel, no emboss line,
# no menu drop shadow. Blender's default is rounded (0.2-0.4) with a 15 % emboss and a 50 % menu shadow.
ROUNDNESS = 0.0
SHAPE = (
    ("user_interface.widget_emboss", (0.0, 0.0, 0.0, 0.0)),
    ("user_interface.menu_shadow_fac", 0.0),
    ("user_interface.menu_shadow_width", 0),
    ("user_interface.panel_roundness", 0.0),
)

# Blender 5.x keys with no 4.5 counterpart (tools/theme_diff.py "added" minus the MOVED targets). Values follow
# the 4.5 look of the same thing (step 119). Widget outline_sel and the new wcol_curve are filled in apply_5x.
FIVE_X = (
    # Blender 5.x splits major grid lines out of view_3d.grid; Maya draws one grid colour (displayColor grid 2)
    ("view_3d.grid_major", (0.25, 0.25, 0.25, 1.0)),
    ("user_interface.panel_active", SELECT),                  #  Maya selection highlight
    ("user_interface.panel_outline", (0.0, 0.0, 0.0, 0.0)),   # flat Maya panels: no outline (step 44)
    ("regions.scrubbing.text", TEXT_DIM),                     # Time Slider numbers, as the 4.5 Dope Sheet text
)
# 5.x-only keys left at Blender's value on purpose (no Maya counterpart / not drawn in a Maya workflow):
KEEP_FACTORY_5X = {
    "user_interface.link": "hyperlink text (Preferences, tooltips): Maya has none",
    "user_interface.axis_w": "quaternion W colour: Maya has no W channel",
    "view_3d.grid_axis_brightness": "axis colour strength on grid axis lines: the Allset views hide them",
    "view_3d.gp_wire_edit": "Grease Pencil edit wire: Maya has no Grease Pencil",
    "node_editor.node_outline": "node outline in node editors (Hypershade keeps the Blender node look)",
    "preferences.match": "search match highlight in Preferences",
    "common.anim.scene_strip_range": "Sequencer scene strip range",
    "dopesheet_editor.anim_interpolation_constant": "Dope Sheet interpolation line (5.2), like 4.5 interpolation_line",
    "dopesheet_editor.anim_interpolation_linear": "Dope Sheet interpolation line (5.2), like 4.5 interpolation_line",
    "dopesheet_editor.anim_interpolation_other": "Dope Sheet interpolation line (5.2), like 4.5 interpolation_line",
}

# Editors whose generic space colours get the Maya panel grey.
EDITORS = ("view_3d", "graph_editor", "dopesheet_editor", "nla_editor", "image_editor",
           "sequence_editor", "properties", "text_editor", "node_editor", "outliner",
           "info", "file_browser", "console", "clip_editor", "topbar", "statusbar",
           "spreadsheet", "preferences")


def blenders():
    """(version, exe): Blender 4.5 first (the 5.x files copy moved values from its file), then each portable 5.x."""
    sys.path.insert(0, str(ROOT / "tools"))
    import build
    out = [("4.5", os.environ.get("BLENDER", build.DEFAULT_BLENDER))]
    portable = Path(os.environ.get("ALLSET_BLENDERS", r"C:\Users\ohnsk\AppData\Local\allset_blenders"))
    for d in sorted(portable.glob("blender-5.*-windows-x64")):
        out.append((d.name.split("-")[1], str(d / "blender.exe")))
    return out


def run_outside_blender():
    import subprocess
    sys.path.insert(0, str(ROOT / "tools"))
    import build
    for _ver, exe in blenders():
        r = subprocess.run([exe, "-b", "--factory-startup", "--python-exit-code", "1", "--python", __file__],
                           env=build.sandbox_env(), stdin=subprocess.DEVNULL,
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        for line in r.stdout.splitlines():
            if line.startswith("make_theme"):
                print(line)
        if r.returncode:
            sys.stderr.write(r.stdout[-3000:] + r.stderr[-3000:])
            return r.returncode
    return 0


LEGACY_OK = set()   # 4.5 paths a 5.x Blender lacks (their values come through MOVED instead)


def _set(owner, path, value):
    *parents, attr = path.split(".")
    try:
        for p in parents:
            owner = getattr(owner, p)
        current = getattr(owner, attr)  # AttributeError = path drifted: fail loudly
    except AttributeError:
        if path in LEGACY_OK:
            return
        raise
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
    for prop in ui.bl_rna.properties:
        if prop.identifier.startswith("wcol_") and prop.identifier != "wcol_state":
            w = getattr(ui, prop.identifier)
            w.roundness = ROUNDNESS
            w.show_shaded = False
    for path, value in SHAPE:
        _set(theme, path, value)
    for editor in EDITORS:
        space = getattr(theme, editor).space
        for attr in ("back", "header", "button"):
            if hasattr(space, attr):
                _set(space, attr, PANEL)
        for attr in ("text", "header_text", "button_text"):
            if hasattr(space, attr):
                _set(space, attr, TEXT_DIM if attr == "text" else TEXT)
        # Region tab strips (sidebar tabs): Maya's dock tab strip / tabs (ui_samples
        # dock_side_tab_strip #373737, layer_tab_active #444444) 
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


def out_path(version):
    """studio_grey.xml for 4.5, studio_grey_<major>.<minor>.xml for later Blenders (compat.theme_file picks it)."""
    major, minor = version[:2]
    return OUT if (major, minor) == (4, 5) else OUT.with_name(f"studio_grey_{major}.{minor}.xml")


def moved_table():
    """MOVED of src/allset/theme (Blender's 5.0 migration table), read from its source."""
    src = (ROOT / "src" / "allset" / "theme" / "__init__.py").read_text(encoding="utf-8")
    start = src.index("_ANIM = (")
    end = src.index("\n)\n", src.index("MOVED = (")) + 3
    ns = {}
    exec(src[start:end], ns)
    return ns["MOVED"]


def _xml_value(root, path):
    *parts, attr = path.split(".")
    node = root
    for part in parts:
        prop = next((c for c in node.childNodes if c.nodeType == c.ELEMENT_NODE and c.tagName == part), None)
        node = next((c for c in prop.childNodes if c.nodeType == c.ELEMENT_NODE), None) if prop else None
        if node is None:
            return ""
    return node.getAttribute(attr)


def apply_5x(theme):
    """Moved values from the 4.5 file, then the 5.x-only keys."""
    import xml.dom.minidom
    root = xml.dom.minidom.parse(str(OUT)).getElementsByTagName("Theme")[0]
    for new, old in moved_table():
        value = _xml_value(root, old)
        if not value:
            raise LookupError(f"{old} not in {OUT.name} (needed for {new})")
        *parents, name = new.split(".")
        owner = theme
        for p in parents:
            owner = getattr(owner, p)
        current = getattr(owner, name)
        if isinstance(current, (int, float)):
            setattr(owner, name, type(current)(float(value)))
            continue
        h = value.lstrip("#")
        col = [int(h[k:k + 2], 16) / 255 for k in range(0, min(len(h), 2 * len(current)), 2)]
        if len(col) < len(current):
            col.append(current[3])
        setattr(owner, name, col)
    ui = theme.user_interface
    for prop in ui.bl_rna.properties:
        if prop.identifier.startswith("wcol_"):
            w = getattr(ui, prop.identifier)
            if hasattr(w, "outline_sel"):
                w.outline_sel = w.outline     # 4.5 drew a selected widget with its normal outline
    if hasattr(ui, "wcol_curve"):
        for attr in ("inner", "inner_sel", "item", "text", "text_sel", "outline"):
            setattr(ui.wcol_curve, attr, getattr(ui.wcol_regular, attr))
        ui.wcol_curve.outline_sel = ui.wcol_regular.outline
    for path, value in FIVE_X:   # some exist from a later minor on (grid_major: 5.2)
        *parents, name = path.split(".")
        owner = theme
        for p in parents:
            owner = getattr(owner, p, None)
        if owner is not None and hasattr(owner, name):
            _set(theme, path, value)


def main():
    import bpy
    try:
        import rna_xml
    except ImportError:   # Blender 5.x
        import _rna_xml as rna_xml
    from bl_ui.space_userpref import USERPREF_MT_interface_theme_presets as presets

    out = out_path(bpy.app.version)
    later = out != OUT
    if later:
        LEGACY_OK.update(old for _new, old in moved_table())
        # also merged into a moved value: graph_editor.preview_range -> common.anim.preview_range (same value)
        LEGACY_OK.add("graph_editor.preview_range")
    bpy.ops.preferences.reset_default_theme()
    theme = bpy.context.preferences.themes[0]
    if later:
        # every key this Blender shares with 4.5 takes the 4.5 file's value (the loader skips the rest), so the
        # colours Blender itself changed in 5.x (node headers, list outlines ...) look as in 4.5 too
        rna_xml.xml_file_run(bpy.context.preferences, str(OUT), (("themes[0]", "Theme"), ("ui_styles[0]", "ThemeStyle")),
                             secure_types=presets.preset_xml_secure_types)
    apply_table(theme)
    if later:
        apply_5x(theme)
    out.parent.mkdir(parents=True, exist_ok=True)
    rna_xml.xml_file_write(bpy.context, str(out), presets.preset_xml_map)
    print(f"make_theme: Blender {bpy.app.version_string}: wrote {out.relative_to(ROOT)} ({out.stat().st_size} bytes)")


if __name__ == "__main__":
    try:
        import bpy  # noqa: F401
    except ImportError:
        sys.exit(run_outside_blender())
    main()
