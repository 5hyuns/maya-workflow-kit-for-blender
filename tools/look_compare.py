"""Compare the kit's look with Maya 2022: side-by-side shots and theme colour ΔE.

    python tools/look_compare.py              # Blender shots + side-by-side images + ΔE table
    python tools/look_compare.py --no-shots   # only ΔE (theme vs research/maya/colors.json)

Maya side (not run here; research/ is untracked, decision 6): research/maya/screens/*.png and
research/maya/colors.json, made by research/scripts/maya_shots/shots.py inside Maya 2022 and
research/scripts/maya_colors.py (docs/steps/step_40.md).

1. Builds the extension and installs it into a clean sandbox (tmp/look_env), like
   tools/release_check.py, then runs tools/look_shots.py in a 1600x900 GUI Blender
   (same size as the Maya shots) -> tmp/look_env/shots/<name>.png.
2. Re-runs itself in `blender -b` and writes into research/maya/screens/compare/:
   - <name>.png: Maya left, Blender right, for every shot name present on both sides;
   - delta_e.md: CIEDE2000 between each Maya reference colour and the theme value the kit sets
     for it (theme/studio_grey.xml applied over the factory theme);
   - pixels.md: CIEDE2000 between the Maya screenshot samples (colors.json "ui_samples") and the
     rendered kit pixels at the matching kit points (look_data.KIT_POINTS);
   - rects.md: Maya widget rectangles (_maya_ui_dump.json) vs kit areas/regions (look_data.RECTS,
     ±10 px), plus the kit-only areas;
   - density.md: menu bar height, menu item and Channel Box row pitch vs Maya's metrics (step 44);
   - scene.md: pCube1's on-screen box in the kit vs Maya (camera parity, ±10 %);
   - crop_<name>.png: the same UI element cut from both shots (look_data.CROPS).
   Kit geometry comes from tmp/look_env/shots/geometry.json (written by look_shots.py).
"""

import json
import math
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import look_data as L  # noqa: E402

MAYA = L.MAYA
COMPARE = L.COMPARE
SANDBOX = ROOT / "tmp" / ("look_env_" + os.environ["ALLSET_LOOK_TAG"] if os.environ.get("ALLSET_LOOK_TAG") else "look_env")
TIMEOUT = 300

# (label, theme path, Maya colour key in colors.json) -- key "a.b" walks the json
PAIRS = (
    ("panel background", "properties.space.back", "ui_palette_qt.active.Window"),
    ("menu bar (top bar)", "topbar.space.header", "ui_samples.menu_bar_bg"),
    ("button", "user_interface.wcol_regular.inner", "ui_palette_qt.active.Button"),
    ("button text", "user_interface.wcol_regular.text", "ui_palette_qt.active.ButtonText"),
    ("selection highlight", "user_interface.wcol_regular.inner_sel", "ui_palette_qt.active.Highlight"),
    ("text field", "user_interface.wcol_text.inner", "ui_palette_qt.active.Base"),
    ("number field (CB value)", "user_interface.wcol_num.inner", "ui_samples.cb_field"),
    ("menu / popup body", "user_interface.wcol_menu_back.inner", "ui_samples.menu_popup_bg"),
    ("menu item hover", "user_interface.wcol_menu_item.inner_sel", "ui_palette_qt.active.Highlight"),
    ("list (Outliner) background", "outliner.space.back", "ui_samples.outliner_list_bg"),
    ("list row selected", "outliner.selected_highlight", "ui_samples.outliner_row_selected"),
    ("tab inactive", "user_interface.wcol_tab.inner", "ui_samples.shelf_tab_inactive"),
    ("tab active", "user_interface.wcol_tab.inner_sel", "ui_samples.shelf_tab_active"),
    ("label text", "properties.space.text", "ui_palette_qt.active.WindowText"),
    ("viewport background (flat)", "view_3d.space.gradients.high_gradient", "viewport.background_flat"),
    ("gradient bottom (Alt+B only)", "view_3d.space.gradients.gradient", "viewport.background_gradient_bottom"),
    ("grid", "view_3d.grid", "viewport.displayColor.grid"),
    ("dormant wire", "view_3d.wire", "viewport.dormant_polymesh_wire"),
    ("lead selected (active)", "view_3d.object_active", "viewport.displayColor.lead"),
    ("other selected", "view_3d.object_selected", "viewport.displayColor.active"),
    ("component-mode wire", "view_3d.wire_edit", "viewport.displayColor.hilite"),
    ("vertex (unselected)", "view_3d.vertex", "viewport.displayColor.hiliteComponent"),
    ("vertex selected (as drawn)", "view_3d.vertex_select", "viewport.vertex_selected_rendered"),
    ("edge selected", "view_3d.edge_select", "viewport.displayColor.polyEdge"),
    ("edge selected (edge mode)", "view_3d.edge_mode_select", "viewport.displayColor.polyEdge"),
    ("face selected", "view_3d.face_select", "viewport.displayColor.polyFace"),
    ("face selected (face mode)", "view_3d.face_mode_select", "viewport.displayColor.polyFace"),
    ("manipulator X", "user_interface.axis_x", "viewport.manip_x"),
    ("manipulator Y", "user_interface.axis_y", "viewport.manip_y"),
    ("manipulator Z (as drawn)", "user_interface.axis_z", "viewport.manip_z_rendered"),
    ("manipulator active handle", "user_interface.gizmo_primary", "viewport.displayColor.manipCurrent"),
    ("manipulator hovered handle", "user_interface.gizmo_hi", "viewport.displayColor.manipCurrent"),
    ("Outliner lead row", "outliner.active", "ui_samples.outliner_row_selected"),
    ("Outliner selected name", "outliner.selected_object", "ui_palette_qt.active.HighlightedText"),
    ("Outliner lead name", "outliner.active_object", "ui_palette_qt.active.HighlightedText"),
    ("time slider background", "dopesheet_editor.space.back", "viewport.time_slider_bg"),
    ("time slider key", "dopesheet_editor.keyframe", "viewport.time_slider_key"),
    ("time slider current frame", "dopesheet_editor.frame_current", "viewport.time_slider_current_frame"),
)


# ---------------------------------------------------------------- colour maths
def _lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def lab(rgb):
    r, g, b = (_lin(c) for c in rgb[:3])
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883

    def f(t):
        return t ** (1 / 3) if t > 216 / 24389 else (24389 / 27 * t + 16) / 116
    fx, fy, fz = f(x), f(y), f(z)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


def de2000(c1, c2):
    """CIEDE2000 between two sRGB colours (0..1)."""
    return de2000_lab(lab(c1), lab(c2))


def de2000_lab(lab1, lab2):
    """CIEDE2000 between two CIELAB colours (Sharma, Wu, Dalal 2005)."""
    L1, a1, b1 = lab1
    L2, a2, b2 = lab2
    C1, C2 = math.hypot(a1, b1), math.hypot(a2, b2)
    Cm = (C1 + C2) / 2
    G = 0.5 * (1 - math.sqrt(Cm ** 7 / (Cm ** 7 + 25 ** 7)))
    a1p, a2p = (1 + G) * a1, (1 + G) * a2
    C1p, C2p = math.hypot(a1p, b1), math.hypot(a2p, b2)
    h1p = math.degrees(math.atan2(b1, a1p)) % 360
    h2p = math.degrees(math.atan2(b2, a2p)) % 360
    dLp, dCp = L2 - L1, C2p - C1p
    dh = 0 if C1p * C2p == 0 else (h2p - h1p if abs(h2p - h1p) <= 180 else
                                    h2p - h1p - 360 if h2p > h1p else h2p - h1p + 360)
    dHp = 2 * math.sqrt(C1p * C2p) * math.sin(math.radians(dh / 2))
    Lpm, Cpm = (L1 + L2) / 2, (C1p + C2p) / 2
    if C1p * C2p == 0:
        hpm = h1p + h2p
    elif abs(h1p - h2p) <= 180:
        hpm = (h1p + h2p) / 2
    else:
        hpm = (h1p + h2p + 360) / 2 if h1p + h2p < 360 else (h1p + h2p - 360) / 2
    T = (1 - 0.17 * math.cos(math.radians(hpm - 30)) + 0.24 * math.cos(math.radians(2 * hpm))
         + 0.32 * math.cos(math.radians(3 * hpm + 6)) - 0.20 * math.cos(math.radians(4 * hpm - 63)))
    dtheta = 30 * math.exp(-(((hpm - 275) / 25) ** 2))
    Rc = 2 * math.sqrt(Cpm ** 7 / (Cpm ** 7 + 25 ** 7))
    Sl = 1 + 0.015 * (Lpm - 50) ** 2 / math.sqrt(20 + (Lpm - 50) ** 2)
    Sc, Sh = 1 + 0.045 * Cpm, 1 + 0.015 * Cpm * T
    Rt = -math.sin(math.radians(2 * dtheta)) * Rc
    return math.sqrt((dLp / Sl) ** 2 + (dCp / Sc) ** 2 + (dHp / Sh) ** 2 + Rt * (dCp / Sc) * (dHp / Sh))


def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def rgb2hex(c):
    return "#%02x%02x%02x" % tuple(round(max(0.0, min(1.0, v)) * 255) for v in c[:3])


def maya_colour(colors, key):
    """Walk ``key`` ("viewport.displayColor.lead") through colors.json; keys may contain dots."""
    node, parts = colors, key.split(".")
    while parts:
        for n in range(len(parts), 0, -1):
            k = ".".join(parts[:n])
            if k in node:
                node, parts = node[k], parts[n:]
                break
        else:
            raise KeyError(key)
    return hex2rgb(node if isinstance(node, str) else node["hex"])


# ---------------------------------------------------------------- in Blender
def in_blender():
    import bpy

    bpy.ops.preferences.reset_default_theme()
    bpy.ops.script.execute_preset(filepath=str(ROOT / "src" / "allset" / "theme" / "studio_grey.xml"),
                                  menu_idname="USERPREF_MT_interface_theme_presets")
    theme = bpy.context.preferences.themes[0]
    # Blender 5.x keeps some 4.5 theme values elsewhere: apply the kit's own move table and read them there
    # (src/allset/theme MOVED, step 118)
    import importlib.util
    spec = importlib.util.spec_from_file_location("allset_theme_look", ROOT / "src" / "allset" / "theme" / "__init__.py")
    kit_theme = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(kit_theme)
    kit_theme._apply_moved(theme)
    moved = {old: new for new, old in kit_theme.MOVED}
    colors = json.loads((MAYA / "colors.json").read_text())
    rows = []
    for label, path, key in PAIRS:
        owner = theme
        if kit_theme._resolve(theme, path)[0] is None and path in moved:
            path = moved[path]
        try:
            for p in path.split("."):
                owner = getattr(owner, p)
        except AttributeError:   # a setting this Blender removed without a successor
            rows.append((label, path + " (not in this Blender)", key, "?", "?", None))
            continue
        kit = tuple(owner)[:3]
        try:
            ref = maya_colour(colors, key)
        except KeyError:
            rows.append((label, path, key, rgb2hex(kit), "?", None))
            continue
        rows.append((label, path, key, rgb2hex(kit), rgb2hex(ref), de2000(kit, ref)))
    gt = theme.view_3d.space.gradients.background_type
    COMPARE.mkdir(parents=True, exist_ok=True)
    lines = ["# Theme vs Maya 2022 colours (CIEDE2000)", "",
             "Generated by `python tools/look_compare.py`. Maya values: research/maya/colors.json.",
             f"Kit theme: src/allset/theme/studio_grey.xml over the factory theme. Viewport background type: `{gt}` "
             f"(Maya factory: flat, gradient {colors['viewport']['gradient_default_on']}).",
             "ΔE00 < 2: same to the eye · 2–5: close · > 5: visibly different.", "",
             "| element | theme path | kit | Maya | ΔE00 |", "|---|---|---|---|---|"]
    bad = 0
    for label, path, key, kit, ref, de in rows:
        mark = "?" if de is None else f"{de:.1f}" + (" ✗" if de > 5 else " ~" if de > 2 else "")
        bad += de is not None and de > 5
        lines.append(f"| {label} | `{path}` | {kit} | {ref} | {mark} |")
    lines += ["", f"{bad} of {len(rows)} pairs differ visibly (ΔE00 > 5)."]
    (COMPARE / "delta_e.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("look_compare:", f"{bad}/{len(rows)} theme pairs with ΔE00 > 5")

    shots = Path(os.environ.get("ALLSET_LOOK_SHOTS", SANDBOX / "shots"))
    made = 0
    for bpath in sorted(shots.glob("*.png")):
        mpath = MAYA / "screens" / bpath.name
        if bpath.stem == "00_first_start":
            mpath = MAYA / "screens" / "02_cube_selected_move.png"
        if mpath.exists():
            save_png(join(L.load_rgb(mpath), L.load_rgb(bpath), "side"), COMPARE / bpath.name)
            made += 1
    print("look_compare:", made, "side-by-side images in", COMPARE.relative_to(ROOT))
    gpath = shots / "geometry.json"
    if not gpath.exists():
        print("look_compare: no geometry.json, skipped pixels/rects/scene/crops")
        return
    geom = json.loads(gpath.read_text(encoding="utf-8"))
    imgs = {}

    def kit_img(shot):
        if shot not in imgs:
            imgs[shot] = L.load_rgb(shots / f"{shot}.png")
        return imgs[shot]

    pixel_table(colors, geom, kit_img)
    viewport_table(geom, kit_img)
    rect_table(geom)
    scene_table(geom)
    crops(geom, kit_img)
    density_table(geom, kit_img)
    grid_table(geom, kit_img)
    furniture_table(geom, kit_img)


def join(a, b, how):
    """Two images side by side (gap 8 px) or one over the other (gap 6 px), padded with black."""
    import numpy as np
    if how == "side":
        H = max(a.shape[0], b.shape[0])
        a, b = (np.pad(i, ((0, H - i.shape[0]), (0, 0), (0, 0))) for i in (a, b))
        return np.concatenate([a, np.ones((H, 8, 3), np.float32), b], axis=1)
    W = max(a.shape[1], b.shape[1])
    a, b = (np.pad(i, ((0, 0), (0, W - i.shape[1]), (0, 0))) for i in (a, b))
    return np.concatenate([a, np.ones((6, W, 3), np.float32), b], axis=0)


def save_png(rgb, path):
    import bpy
    import numpy as np
    h, w, _ = rgb.shape
    rgba = np.concatenate([rgb[::-1], np.ones((h, w, 1), np.float32)], axis=2)
    im = bpy.data.images.new("look_compare", w, h, alpha=False)
    im.pixels.foreach_set(rgba.astype(np.float32).ravel())
    im.filepath_raw = str(path)
    im.file_format = 'PNG'
    im.save()
    bpy.data.images.remove(im)


def mark(de, close=2, far=5):
    return f"{de:.1f}" + (" ✗" if de > far else " ~" if de > close else "")


def pixel_table(colors, geom, kit_img):
    samples = colors["ui_samples"]
    lines = ["# Rendered pixels: Maya 2022 screenshots vs kit (CIEDE2000)", "",
             "Generated by `python tools/look_compare.py`. Maya: research/maya/colors.json `ui_samples` "
             "(median 5x5); kit: the matching point in the kit shot (`tools/look_data.py` KIT_POINTS, median of "
             "the given radius).",
             "ΔE00 < 2 same · 2–5 close · > 5 visibly different · — the kit has no such element.", "",
             "| sample | Maya shot (x, y) | Maya | kit shot (x, y) | kit | ΔE00 | kit point |",
             "|---|---|---|---|---|---|---|"]
    n = bad = missing = 0
    for name, ref in samples.items():
        spec = L.KIT_POINTS.get(name)
        mshot = f"{ref['shot']} ({ref['xy'][0]}, {ref['xy'][1]})"
        if spec is None or spec[0] is None:
            missing += 1
            note = spec[1] if spec else "not mapped"
            lines.append(f"| {name} | {mshot} | {ref['hex']} | — | — | — | {note} |")
            continue
        shot, anchor, dx, dy, r, note = spec
        rects = geom["rects"].get(shot, {})
        if anchor not in rects:
            missing += 1
            lines.append(f"| {name} | {mshot} | {ref['hex']} | {shot} | ? | ? | anchor `{anchor}` not found |")
            continue
        x, y = (int(round(v)) for v in L.resolve(rects, anchor, dx, dy))
        kit = L.sample(kit_img(shot), x, y, r)
        de = de2000(kit, hex2rgb(ref["hex"]))
        n += 1
        bad += de > 5
        lines.append(f"| {name} | {mshot} | {ref['hex']} | {shot} ({x}, {y}) | {rgb2hex(kit)} | {mark(de)} | "
                     f"{note} |")
    lines += ["", f"{n} compared, {bad} visibly different (ΔE00 > 5), {missing} with no kit element."]
    (COMPARE / "pixels.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("look_compare:", f"pixels {bad}/{n} with ΔE00 > 5, {missing} missing in the kit")


def viewport_table(geom, kit_img):
    lines = ["# Rendered viewport elements: Maya 2022 vs kit (CIEDE2000)", "",
             "Generated by `python tools/look_compare.py` (`tools/look_data.py` VIEW_SAMPLES). \"best\": the pixel "
             "closest to the Maya colour in the Maya view and within ±r px of the kit's projected points; "
             "\"mean\": average colour (Maya stipples selected faces).",
             "Pass: ΔE00 < 5.", "",
             "| element | shot | Maya expects | Maya pixel (x, y) | kit pixel (x, y) | ΔE00 kit↔Maya |",
             "|---|---|---|---|---|---|"]
    ok = n = 0
    for label, shot, colour, key, r, mode, region in L.VIEW_SAMPLES:
        mpath = MAYA / "screens" / f"{shot}.png"
        kshot = region if mode == "best" and isinstance(region, str) else shot
        pts = geom.get("points", {}).get(kshot, {}).get(key)
        if not mpath.exists() or not pts:
            lines.append(f"| {label} | {shot} | {colour} | ? | kit points `{key}` missing | ✗ |")
            n += 1
            continue
        mimg, kimg = L.load_rgb(mpath), kit_img(kshot)
        if mode == "tint":
            # Selection colour only: the kit's fill (kit 07 vs the same point in kit 02, same view)
            # laid over Maya's base shading, against Maya 07. Base shading (Blender studio light vs
            # Maya default light) is a separate difference (docs/steps/step_43.md).
            base_shot, mreg, kit_base = region
            x, y = pts[0]
            kbox = (x - r, y - r // 2, 2 * r + 1, r + 1)
            k_sel, k_base = L.mean_colour(kimg, kbox), L.mean_colour(kit_img(kit_base), kbox)
            m = L.mean_colour(mimg, mreg)
            m_base = L.mean_colour(L.load_rgb(MAYA / "screens" / f"{base_shot}.png"), mreg)
            f = hex2rgb("#e4ac79")
            alpha = sum((k_sel[i] - k_base[i]) / (f[i] - k_base[i]) for i in range(3)) / 3
            k = tuple(m_base[i] + alpha * (f[i] - m_base[i]) for i in range(3))
            mtxt = f"{rgb2hex(m)} mean of {list(mreg)}"
            ktxt = f"alpha {alpha:.2f} -> {rgb2hex(k)} on Maya's base (raw kit mean {rgb2hex(k_sel)})"
            expect = "stipple #e4ac79 25 %"
        else:
            ref = hex2rgb(colour)
            # 64 closest by RGB distance, then the closest by CIEDE2000 (RGB distance prefers
            # darker anti-aliased edge pixels over a lighter but perceptually closer fill)
            mx, my, m = min(L.best_pixel(mimg, colour, L.MAYA_VIEW_RECT, keep=64),
                            key=lambda c: de2000(c[2], ref))
            cands = [c for px, py in pts
                     for c in (L.best_pixel(kimg, colour, (px - r, py - r, 2 * r + 1, 2 * r + 1), keep=64) or [])]
            kx, ky, k = min(cands, key=lambda c: de2000(c[2], ref))
            mtxt, ktxt, expect = f"{rgb2hex(m)} ({mx}, {my})", f"{rgb2hex(k)} ({kx}, {ky})", colour
        de = de2000(k, m)
        good = de < 5
        ok += good
        n += 1
        lines.append(f"| {label} | {shot} | {expect} | {mtxt} | {ktxt} | {de:.1f} {'✓' if good else '✗'} |")
    lines += ["", f"{ok} of {n} elements within ΔE00 5."]
    (COMPARE / "viewport.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("look_compare:", f"viewport {ok}/{n} elements within ΔE00 5")


def rect_table(geom, shot="11_channel_box"):
    widgets = L.maya_dump()["widgets"]
    rects = geom["rects"][shot]
    lines = ["# Layout rectangles: Maya 2022 widgets vs kit areas/regions", "",
             f"Generated by `python tools/look_compare.py` from shot `{shot}`. Maya: `_maya_ui_dump.json` "
             "widgets; kit: `geometry.json` anchors (screenshot pixels, origin top-left), [x, y, w, h].",
             f"Δ = kit − Maya; ✓ when every |Δ| ≤ {L.RECT_TOL} px.", "",
             "Axes = the axes within the tolerance.", "",
             "| element | Maya | kit anchor | kit | Δx | Δy | Δw | Δh | axes | |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    ok = total = 0
    for widget, anchor, label in L.RECTS:
        m, k = widgets.get(widget), rects.get(anchor)
        total += 1
        if m is None or k is None:
            lines.append(f"| {label} | {m} | `{anchor}` | {k} | | | | | | missing |")
            continue
        d = [round(k[i] - m[i]) for i in range(4)]
        good = all(abs(v) <= L.RECT_TOL for v in d)
        ok += good
        axes = " ".join(n for n, v in zip("xywh", d) if abs(v) <= L.RECT_TOL)
        lines.append(f"| {label} | {m} | `{anchor}` | {[round(v) for v in k]} | {d[0]} | {d[1]} | {d[2]} | "
                     f"{d[3]} | {axes} | {'✓' if good else '✗'} |")
    for anchor in L.KIT_ONLY:
        if anchor in rects:
            lines.append(f"| (kit only) | none | `{anchor}` | {[round(v) for v in rects[anchor]]} "
                         "| | | | | | ✗ extra |")
    lines += ["", f"{ok} of {total} Maya elements within ±{L.RECT_TOL} px."]
    (COMPARE / "rects.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("look_compare:", f"rects {ok}/{total} within ±{L.RECT_TOL} px")


def scene_table(geom):
    lines = ["# Scene parity: pCube1 on screen, Maya 2022 vs kit", "",
             "Generated by `python tools/look_compare.py`. Maya box: pixels of the wire colour in the Maya "
             "shot (`look_data.CUBE_FITS`); kit box: pCube1's projected bound box (`geometry.json`). "
             "Pass: width and height within ±10 %.", "",
             f"Maya pixel focal length {L.maya_f_px():.1f} px (35 mm lens, 36 mm aperture, "
             f"{L.MAYA_VIEW_RECT[2]} px wide view).", "",
             "| shot | Maya w×h (centre) | kit w×h (centre) | Δw | Δh | kit f_px / lens | |",
             "|---|---|---|---|---|---|---|"]
    ok = 0
    for shot in L.CUBE_FITS:
        m = L.maya_cube_bbox(shot)
        k = geom["cubes"].get(shot)
        if m is None or k is None:
            lines.append(f"| {shot} | {m} | {k} | | | | missing |")
            continue
        kb = k["bbox"]
        mw, mh = m[2] - m[0], m[3] - m[1]
        kw, kh = kb[2] - kb[0], kb[3] - kb[1]
        dw, dh = (kw - mw) / mw * 100, (kh - mh) / mh * 100
        good = abs(dw) <= 10 and abs(dh) <= 10
        ok += good
        lines.append(f"| {shot} | {mw}×{mh} ({(m[0] + m[2]) / 2:.0f}, {(m[1] + m[3]) / 2:.0f}) | "
                     f"{kw:.0f}×{kh:.0f} ({(kb[0] + kb[2]) / 2:.0f}, {(kb[1] + kb[3]) / 2:.0f}) | {dw:+.1f} % | "
                     f"{dh:+.1f} % | {k['f_px']:.1f} / {k['lens']:.1f} mm | {'✓' if good else '✗'} |")
    lines += ["", f"{ok} of {len(L.CUBE_FITS)} shots within ±10 %. Centres differ by the view position "
              "(the kit view is centred in its own region)."]
    (COMPARE / "scene.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("look_compare:", f"scene {ok}/{len(L.CUBE_FITS)} cube boxes within ±10 %")


def density_table(geom, kit_img):
    """Menu bar height, menu item pitch and Channel Box row pitch, measured in both shots (step 44)."""
    widgets = L.maya_dump()["widgets"]
    rects = geom["rects"].get("11_channel_box", {})
    maya_menu = L.load_rgb(MAYA / "screens" / "12_create_menu.png")
    maya_cb = L.load_rgb(MAYA / "screens" / "11_channel_box.png")
    got = {}
    # Menu bar: Maya's QMenuBar widget, the kit's top bar (global area above all editors).
    got["menu bar height"] = (widgets["menuBar"][3], rects.get("topbar", [0, 0, 0, None])[3], "")
    menus = {}
    for who, img in (("maya", maya_menu), ("kit", kit_img("12_create_menu"))):
        menus[who] = r = L.colour_area(img, L.MENU_BG[who], L.MENU_SEARCH)
        menus[who + "_pitch"] = L.line_pitch(img, [r[0], r[1], r[2] * 0.6, r[3]]) if r else (None, 0, 0)
    got["menu item pitch"] = (menus["maya_pitch"][0], menus["kit_pitch"][0],
                              f"Create menu at {menus['maya']} / {menus['kit']}; lines {menus['maya_pitch'][1]} / "
                              f"{menus['kit_pitch'][1]}, at the pitch {menus['maya_pitch'][2]} / {menus['kit_pitch'][2]}")
    bar_h = rects.get("topbar", [0, 0, 0, 0])[3]
    menu_rects = geom["rects"].get("12_create_menu", {})
    got["menu top - menu bar bottom"] = (
        menus["maya"][1] - widgets["menuBar"][3] if menus["maya"] else None,
        menus["kit"][1] - menu_rects.get("topbar", [0, 0, 0, bar_h])[3] if menus["kit"] else None,
        "Create menu opened from the menu bar")
    shelf = rects.get("shelf")
    shelf_win = rects.get("shelf.WINDOW")
    got["shelf height"] = (widgets["Shelf"][3], shelf[3] if shelf else None, "tab row + icon row")
    got["shelf icon"] = (32, min(32, shelf_win[3] - 4) if shelf_win else None,
                         "ui/shelf.py icon_rect at the shot's scale 1.0 (Maya 32x32 icons in 35x34 buttons)")
    m = widgets["ChannelBoxLayerEditor"]
    mp = L.line_pitch(maya_cb, [m[0], m[1], m[2] * 0.68, m[3] * 0.5])
    k = rects.get("view3d.UI")
    kp = L.line_pitch(kit_img("11_channel_box"), [k[0] + 10, k[1], k[2] * 0.45, k[3]]) if k else (None, 0, 0)
    got["Channel Box row pitch"] = (mp[0], kp[0], f"label column; lines {mp[1]} / {kp[1]}, at the pitch {mp[2]} / {kp[2]}")
    lines = ["# Density: Maya 2022 vs kit (pixels)", "",
             "Generated by `python tools/look_compare.py` (step 44). Pitch = most common distance between text "
             "line centres in the element (`look_data.line_pitch`). Target: Maya's Qt metrics "
             "(research/maya/colors.json metrics, dpr 1.0).", "",
             "| element | target | Maya shot | kit | |", "|---|---|---|---|---|"]
    ok = 0
    for name, target, tol in L.DENSITY:
        maya, kit, note = got[name]
        good = kit is not None and abs(kit - target) <= tol
        ok += good
        lines.append(f"| {name} | {target} ±{tol} | {maya} | {kit} | {'✓' if good else '✗'} {note} |")
    lines += ["", f"{ok} of {len(L.DENSITY)} within tolerance."]
    (COMPARE / "density.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("look_compare:", f"density {ok}/{len(L.DENSITY)}")


def grid_table(geom, kit_img, shot="01_layout_empty"):
    """Maya grid (step 45): rendered colour on the projected grid lines and the grid's corners."""
    pts = geom.get("points", {}).get(shot, {})
    lines = ["# Maya grid: Maya 2022 vs kit (shot 01)", "",
             "Generated by `python tools/look_compare.py` (step 45). Kit points: the Maya grid's lines and corners "
             "projected with the view's own matrices (`look_shots.record_grid`, `ui/maya_grid.py`). Line points: "
             "the pixel closest to the grid colour within ±1 px, ΔE00 against the Maya grid pixel. Corners: a "
             "grid-colour pixel (ΔE00 < 5) within ±1 px of the projected corner, and background 4 px further out "
             "(the grid ends there: 12 units).", ""]
    if not pts.get("grid.corners"):
        (COMPARE / "grid.md").write_text("\n".join(lines + ["kit grid points missing"]) + "\n", encoding="utf-8")
        print("look_compare: grid points missing")
        return
    colors = L.maya_colors()
    gref = hex2rgb(colors["viewport"]["displayColor.grid"]["hex"])
    bg = hex2rgb("#5c5c5c")
    mimg, kimg = L.load_rgb(MAYA / "screens" / f"{shot}.png"), kit_img(shot)
    mx, my, m = min(L.best_pixel(mimg, rgb2hex(gref), L.MAYA_VIEW_RECT, keep=64), key=lambda c: de2000(c[2], gref))
    lines += [f"Maya grid pixel {rgb2hex(m)} ({mx}, {my}), Maya value {rgb2hex(gref)}.", "",
              "| lines | points | ΔE00 < 5 | median ΔE00 | |", "|---|---|---|---|---|"]
    ok_all = True
    for kind in ("minor", "major", "axis"):
        des = []
        for x, y in pts.get(f"grid.{kind}", []):
            c = L.best_pixel(kimg, rgb2hex(gref), (round(x) - 1, round(y) - 1, 3, 3))
            if c:
                des.append(de2000(c[2], m))
        des.sort()
        good = sum(d < 5 for d in des)
        ok = bool(des) and good >= 0.95 * len(des)
        ok_all &= ok
        med = des[len(des) // 2] if des else float("nan")
        lines.append(f"| {kind} | {len(des)} | {good} | {med:.1f} | {'✓' if ok else '✗'} |")
    cx, cy = pts["grid.centre"][0]
    lines += ["", "| corner | projected (x, y) | grid pixel ±1 px | ΔE00 | 4 px outside | |", "|---|---|---|---|---|---|"]
    corners_ok = 0
    for i, (x, y) in enumerate(pts["grid.corners"]):
        c = L.best_pixel(kimg, rgb2hex(gref), (round(x) - 1, round(y) - 1, 3, 3))
        de = de2000(c[2], m) if c else 99.0
        dx, dy = x - cx, y - cy
        n = max((dx * dx + dy * dy) ** 0.5, 1e-6)
        ox, oy = round(x + 4 * dx / n), round(y + 4 * dy / n)
        out = L.sample(kimg, ox, oy, r=0)
        out_de = de2000(out, bg)
        good = de < 5 and out_de < 2
        corners_ok += good
        lines.append(f"| {i} | ({x:.1f}, {y:.1f}) | {rgb2hex(c[2]) if c else '-'} ({c[0] if c else '-'}, "
                     f"{c[1] if c else '-'}) | {de:.1f} | {rgb2hex(out)} (ΔE {out_de:.1f} to background) | "
                     f"{'✓' if good else '✗'} |")
    ms = geom.get("grid_ms")
    lines += ["", f"Corners {corners_ok} of 4; lines {'✓' if ok_all else '✗'}. Grid draw time (GUI, mean of the last "
              f"draws): {ms:.3f} ms." if ms is not None else ""]
    (COMPARE / "grid.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("look_compare:", f"grid lines {'ok' if ok_all else 'FAIL'}, corners {corners_ok}/4, draw {ms} ms")


def furniture_table(geom, kit_img, shot="01_layout_empty"):
    """View furniture (step 46): ViewCube, camera label and axis triad position vs Maya, no Blender text info."""
    view = geom["rects"].get(shot, {}).get("view3d.visible")
    lines = ["# View furniture: Maya 2022 vs kit (shot 01)", "",
             "Generated by `python tools/look_compare.py` (step 46). Each element is found by pixels in both shots "
             "(`look_data.FURNITURE`) and measured from its view corner: ViewCube = inset from the right and the top, "
             "label = centre offset from the view centre and bottom inset, triad = inset from the left and the bottom. "
             f"✓ when the insets are within ±{L.FURNITURE_TOL} px (sizes listed).", "",
             "| element | Maya rect | Maya (dx, dy, w, h) | kit rect | kit (dx, dy, w, h) | |", "|---|---|---|---|---|---|"]
    if view is None:
        (COMPARE / "furniture.md").write_text("\n".join(lines + ["kit view rect missing"]) + "\n", encoding="utf-8")
        return
    mimg, kimg = L.load_rgb(MAYA / "screens" / f"{shot}.png"), kit_img(shot)
    ok = 0
    for name, corner, box, test in L.FURNITURE:
        m = L.furniture_box(mimg, L.MAYA_VIEW_RECT, corner, box, test)
        k = L.furniture_box(kimg, view, corner, box, test)
        mo = L.corner_offsets(m, L.MAYA_VIEW_RECT, corner) if m else None
        ko = L.corner_offsets(k, view, corner) if k else None
        good = bool(mo and ko) and all(abs(ko[i] - mo[i]) <= L.FURNITURE_TOL for i in (0, 1))
        if name == "axis triad":
            good = None                      # outline differs by design (Blender axes); origin row below
        ok += bool(good)
        def fmt(o):
            return "(%.0f, %.0f, %d, %d)" % o
        mark = "(outline only)" if good is None else ('✓' if good else '✗')
        lines.append(f"| {name} | {m} | {fmt(mo) if mo else '-'} | {k} | {fmt(ko) if ko else '-'} | {mark} |")
    # axis triad origin (the kit shows Blender's axes, so its outline differs from Maya's; the origin is
    # what sits at the same place)
    mt, kt = (L.furniture_box(img, v, "bottom-left", (0, -90, 90, 90), "saturated")
              for img, v in ((mimg, L.MAYA_VIEW_RECT), (kimg, view)))
    mo = L.triad_origin(mimg, mt) if mt else None
    ko = L.triad_origin(kimg, kt) if kt else None
    if mo and ko:
        md = (mo[0] - L.MAYA_VIEW_RECT[0], L.MAYA_VIEW_RECT[1] + L.MAYA_VIEW_RECT[3] - mo[1])
        kd = (ko[0] - view[0], view[1] + view[3] - ko[1])
        good = all(abs(kd[i] - md[i]) <= L.FURNITURE_TOL for i in (0, 1))
        lines.append(f"| axis triad origin | {mo} | ({md[0]:.0f}, {md[1]:.0f}) | {ko} | ({kd[0]:.0f}, {kd[1]:.0f}) | "
                     f"{'✓' if good else '✗'} |")
        ok += good
    tx, ty, tw, th = L.TEXT_INFO_BOX
    sub = kimg[int(view[1]) + ty:int(view[1]) + ty + th, int(view[0]) + tx:int(view[0]) + tx + tw]
    text_px = int((sub.mean(axis=2) * 255 > 180).sum())
    lines += ["", f"{ok} of 3 (ViewCube, label, triad origin) within ±{L.FURNITURE_TOL} px. Blender text info (top left of the "
              f"view, box {list(L.TEXT_INFO_BOX)}): {text_px} bright pixels ({'✓ none' if text_px == 0 else '✗'})."]
    (COMPARE / "furniture.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("look_compare:", f"furniture {ok}/3, text info pixels {text_px}")


def crops(geom, kit_img):
    widgets = L.maya_dump()["widgets"]
    made = 0

    def cut(img, r):
        x, y, w, h = (int(round(v)) for v in r)
        return img[max(0, y):y + h, max(0, x):x + w]

    for name, shot, widget, anchor, how in L.CROPS:
        m = widgets.get(widget)
        k = geom["rects"].get(shot, {}).get(anchor)
        mpath = MAYA / "screens" / f"{shot}.png"
        if m is None or k is None or not mpath.exists():
            continue
        save_png(join(cut(L.load_rgb(mpath), m), cut(kit_img(shot), k), how), COMPARE / f"crop_{name}.png")
        made += 1
    print("look_compare:", made, "crop images")


# ---------------------------------------------------------------- outside
def gui_run(blender, env, script, name, args):
    """One GUI Blender (1600x900) in the sandbox running tools/<script>; returns its checks."""
    result = SANDBOX / f"{name}.json"
    if result.exists():
        result.unlink()
    cmd = [blender, *args, "--window-geometry", "0", "0", "1600", "900",
           "--python", str(ROOT / "tools" / script), "--", str(result)]
    with open(SANDBOX / f"{name}.log", "w", encoding="utf-8", errors="replace") as fh:
        proc = subprocess.Popen(cmd, env=env, stdin=subprocess.DEVNULL, stdout=fh,
                                stderr=subprocess.STDOUT)
        try:
            proc.wait(timeout=TIMEOUT)
        except subprocess.TimeoutExpired:
            proc.kill()  # only the Blender started here
    if not result.exists():
        return [{"name": f"{script} wrote no results (see tmp/look_env/{name}.log)", "ok": False}]
    return json.loads(result.read_text(encoding="utf-8"))


def main(argv):
    sys.path.insert(0, str(ROOT / "tools"))
    import build
    import release_check
    blender = os.environ.get("BLENDER", build.DEFAULT_BLENDER)
    env = os.environ.copy()
    shots = SANDBOX / "shots"
    if "--no-shots" not in argv:
        release_check.SANDBOX = SANDBOX
        zip_path = build.main(["--blender", blender])
        env = release_check.sandbox_env()
        rc, out = release_check.run([blender, "--command", "extension", "install-file", "-r",
                                     release_check.REPO_ID, "--enable", str(zip_path)], env)
        if rc:
            print(out[-3000:])
            return 1
        shots.mkdir(parents=True, exist_ok=True)
        env["ALLSET_LOOK_SHOTS"] = str(shots)
        checks = gui_run(blender, env, "look_shots.py", "shots", ["--enable-event-simulate"])
        print("shots:", ", ".join(sorted(p.stem for p in shots.glob("*.png"))))
        # Second start in the same config: Maya layout without a file (docs/steps/step_42.md)
        checks += gui_run(blender, env, "look_second_start.py", "second_start", [])
        for c in checks:
            print("look_compare:", "PASS" if c["ok"] else "FAIL", c["name"])
    env["ALLSET_LOOK_SHOTS"] = str(shots)
    r = subprocess.run([blender, "-b", "--factory-startup", "--python-exit-code", "1",
                        "--python", __file__], env=env, stdin=subprocess.DEVNULL,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    for line in r.stdout.splitlines():
        if line.startswith("look_compare"):
            print(line)
    if r.returncode:
        sys.stderr.write(r.stdout[-3000:] + r.stderr[-3000:])
    return r.returncode


if __name__ == "__main__":
    try:
        import bpy  # noqa: F401
    except ImportError:
        sys.exit(main(sys.argv[1:]))
    in_blender()
