"""Compare the kit's look with Maya 2022: side-by-side shots and theme colour ΔE.

    python tools/look_compare.py              # Blender shots + side-by-side images + ΔE table
    python tools/look_compare.py --no-shots   # only ΔE (theme vs research/maya/colors.json)

Maya side (not run here; research/ is untracked, decision 6): research/maya/screens/*.png and
research/maya/colors.json, made by research/scripts/maya_shots/shots.py inside Maya 2022 and
research/scripts/maya_colors.py (docs/steps/step_40.md).

1. Builds the extension and installs it into a clean sandbox (tmp/look_env), like
   tools/release_check.py, then runs tools/look_shots.py in a 1600x900 GUI Blender
   (same size as the Maya shots) -> tmp/look_env/shots/<name>.png.
2. Re-runs itself in `blender -b`: for every shot name present on both sides writes
   research/maya/screens/compare/<name>.png (Maya left, Blender right) and computes CIEDE2000
   between each Maya reference colour and the theme value the kit sets for it (theme/maya.xml
   applied over the factory theme) -> research/maya/screens/compare/delta_e.md.
"""

import json
import math
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAYA = ROOT / "research" / "maya"
COMPARE = MAYA / "screens" / "compare"
SANDBOX = ROOT / "tmp" / "look_env"
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
    ("viewport background bottom", "view_3d.space.gradients.gradient", "viewport.background_flat"),
    ("grid", "view_3d.grid", "viewport.displayColor.grid"),
    ("dormant wire", "view_3d.wire", "viewport.dormant_polymesh_wire"),
    ("lead selected (active)", "view_3d.object_active", "viewport.displayColor.lead"),
    ("other selected", "view_3d.object_selected", "viewport.displayColor.active"),
    ("component-mode wire", "view_3d.wire_edit", "viewport.displayColor.hilite"),
    ("vertex (unselected)", "view_3d.vertex", "viewport.displayColor.hiliteComponent"),
    ("vertex selected", "view_3d.vertex_select", "viewport.displayColor.polyVertex"),
    ("edge selected", "view_3d.edge_select", "viewport.displayColor.polyEdge"),
    ("face selected", "view_3d.face_select", "viewport.displayColor.polyFace"),
    ("manipulator X", "user_interface.axis_x", "viewport.manip_x"),
    ("manipulator Y", "user_interface.axis_y", "viewport.manip_y"),
    ("manipulator Z", "user_interface.axis_z", "viewport.manip_z"),
    ("manipulator active handle", "user_interface.gizmo_primary", "viewport.displayColor.manipCurrent"),
    ("time slider background", "dopesheet_editor.space.back", "viewport.time_slider_bg"),
    ("time slider key", "dopesheet_editor.keyframe", "viewport.time_slider_key"),
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
    L1, a1, b1 = lab(c1)
    L2, a2, b2 = lab(c2)
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
    import numpy as np

    bpy.ops.preferences.reset_default_theme()
    bpy.ops.script.execute_preset(filepath=str(ROOT / "src" / "maya_kit" / "theme" / "maya.xml"),
                                  menu_idname="USERPREF_MT_interface_theme_presets")
    theme = bpy.context.preferences.themes[0]
    colors = json.loads((MAYA / "colors.json").read_text())
    rows = []
    for label, path, key in PAIRS:
        owner = theme
        for p in path.split("."):
            owner = getattr(owner, p)
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
             f"Kit theme: src/maya_kit/theme/maya.xml over the factory theme. Viewport background type: `{gt}` "
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

    shots = Path(os.environ.get("MAYA_KIT_LOOK_SHOTS", SANDBOX / "shots"))
    made = 0
    for bpath in sorted(shots.glob("*.png")):
        mpath = MAYA / "screens" / bpath.name
        if bpath.stem == "00_first_start":
            mpath = MAYA / "screens" / "02_cube_selected_move.png"
        if not mpath.exists():
            continue
        imgs = []
        for p in (mpath, bpath):
            im = bpy.data.images.load(str(p))
            w, h = im.size
            a = np.empty(w * h * 4, dtype=np.float32)
            im.pixels.foreach_get(a)
            imgs.append(a.reshape(h, w, 4))
            bpy.data.images.remove(im)
        H = max(i.shape[0] for i in imgs)
        padded = []
        for i in imgs:
            if i.shape[0] < H:
                pad = np.zeros((H - i.shape[0], i.shape[1], 4), np.float32)
                pad[..., 3] = 1
                i = np.concatenate([pad, i], axis=0)
            padded.append(i)
        gap = np.ones((H, 8, 4), np.float32)
        out = np.concatenate([padded[0], gap, padded[1]], axis=1)
        im = bpy.data.images.new("cmp", out.shape[1], out.shape[0], alpha=False)
        im.pixels.foreach_set(out.ravel())
        im.filepath_raw = str(COMPARE / bpath.name)
        im.file_format = 'PNG'
        im.save()
        bpy.data.images.remove(im)
        made += 1
    print("look_compare:", made, "side-by-side images in", COMPARE.relative_to(ROOT))


# ---------------------------------------------------------------- outside
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
        env["MAYA_KIT_LOOK_SHOTS"] = str(shots)
        cmd = [blender, "--enable-event-simulate", "--window-geometry", "0", "0", "1600", "900",
               "--python", str(ROOT / "tools" / "look_shots.py"), "--", str(SANDBOX / "shots.json")]
        with open(SANDBOX / "shots.log", "w", encoding="utf-8", errors="replace") as fh:
            proc = subprocess.Popen(cmd, env=env, stdin=subprocess.DEVNULL, stdout=fh,
                                    stderr=subprocess.STDOUT)
            try:
                proc.wait(timeout=TIMEOUT)
            except subprocess.TimeoutExpired:
                proc.kill()  # only the Blender started here
        print("shots:", ", ".join(sorted(p.stem for p in shots.glob("*.png"))))
    env["MAYA_KIT_LOOK_SHOTS"] = str(shots)
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
