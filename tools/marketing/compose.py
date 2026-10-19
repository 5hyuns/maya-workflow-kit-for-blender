"""Marketing images (step 122): captioned feature screens, key visuals and the icon, composited with Pillow from the
GUI shots of tools/marketing/shots.py and the copy in tools/marketing/content.json.

    python tools/marketing/compose.py [--only NAME,...]

Inputs: tmp/marketing/raw/<name>.png + meta.json (1920 x 1080 window shots, rects in top-down window pixels),
tools/marketing/style.json (tokens, docs/distribution/marketing/style.md), tools/marketing/content.json (copy from
docs/distribution/marketing/copy.md), the Inter font from  (tools/marketing/
fetch_assets.py). Outputs: docs/distribution/marketing/screens/<n>_<name>.png, key_visual.png, key_visual_square.png,
icon_256.png. Pure Pillow (no numpy) so it runs with any Python that has Pillow.
"""

import argparse
import json
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
RAW = ROOT / "tmp" / "marketing" / "raw"
OUT = ROOT / "docs" / "distribution" / "marketing"
FONTS = ROOT / "research" / "marketing_assets" / "font_inter"

STYLE = json.loads((HERE / "style.json").read_text(encoding="utf-8"))
P, S = STYLE["primitive"], STYLE["semantic"]


def colour(token):
    """Hex of a semantic or primitive token (or a raw hex)."""
    token = S.get(token, token)
    return P.get(token, token)


def rgb(token, alpha=None):
    h = colour(token).lstrip("#")
    c = tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    return c if alpha is None else (*c, alpha)


_FONT_CACHE = {}


def font(key, size):
    name = P.get(key, key)
    k = (name, size)
    if k not in _FONT_CACHE:
        hits = list(FONTS.rglob(name))
        if not hits:
            sys.exit(f"font {name} not found under {FONTS} (run tools/marketing/fetch_assets.py)")
        _FONT_CACHE[k] = ImageFont.truetype(str(hits[0]), size)
    return _FONT_CACHE[k]


def text_w(draw, text, fnt):
    return draw.textlength(text, font=fnt)


def vertical_gradient(size, top, bottom):
    w, h = size
    img = Image.new("RGB", (1, h))
    for y in range(h):
        t = y / max(1, h - 1)
        img.putpixel((0, y), tuple(round(a + (b - a) * t) for a, b in zip(top, bottom)))
    return img.resize((w, h))


def rounded(img, radius):
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, img.size[0] - 1, img.size[1] - 1), radius, fill=255)
    out = img.convert("RGBA")
    out.putalpha(mask)
    return out


def shadow(canvas, box, radius, blur, alpha):
    x0, y0, x1, y1 = box
    pad = blur * 3
    sh = Image.new("RGBA", (x1 - x0 + 2 * pad, y1 - y0 + 2 * pad), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((pad, pad + blur // 2, pad + x1 - x0, pad + y1 - y0 + blur // 2), radius,
                                         fill=(0, 0, 0, alpha))
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    canvas.alpha_composite(sh, (x0 - pad, y0 - pad))


def arrow(draw, start, end, col, width, head):
    draw.line((start, end), fill=col, width=width)
    ang = math.atan2(end[1] - start[1], end[0] - start[0])
    for s in (-1, 1):
        a = ang + math.pi + s * math.radians(28)
        draw.line((end, (end[0] + head * math.cos(a), end[1] + head * math.sin(a))), fill=col, width=width)


# --------------------------------------------------------------------------------------------- feature screens
def screen(name, title, line, callouts, out_path):
    st = STYLE["component"]["screen"]
    band = STYLE["component"]["band"]
    co = STYLE["component"]["callout"]
    W, H = st["canvas"]
    canvas = vertical_gradient((W, H), rgb("canvas-bg"), rgb("canvas-bg-2")).convert("RGBA")
    draw = ImageDraw.Draw(canvas)

    # title band: accent tick, title, one line; brand at the right
    mx = st["margin_x"]
    tfont, lfont = font(band["title_font"], band["title_size"]), font(band["line_font"], band["line_size"])
    ty = band["title_y"]
    draw.rounded_rectangle((mx, ty + 6, mx + band["tick_w"], ty + 6 + band["tick_h"] + band["line_gap"]
                            + band["line_size"]), 3, fill=rgb(band["tick_color"]))
    tx = mx + band["tick_w"] + band["tick_gap"]
    draw.text((tx, ty), title, font=tfont, fill=rgb(band["title_color"]))
    draw.text((tx, ty + band["title_size"] + band["line_gap"]), line, font=lfont, fill=rgb(band["line_color"]))
    bfont = font(band["brand_font"], band["brand_size"])
    brand = "Allset for Maya Users"
    draw.text((W - mx - text_w(draw, brand, bfont), ty + 8), brand, font=bfont, fill=rgb(band["brand_color"]))

    # the shot, scaled into the frame below the band
    raw = Image.open(RAW / f"{name}.png").convert("RGB")
    sx, sy = st["shot_w"] / raw.width, st["shot_h"] / raw.height
    shot = raw.resize((st["shot_w"], st["shot_h"]), Image.LANCZOS)
    ox, oy = mx, st["band_h"]
    shadow(canvas, (ox, oy, ox + st["shot_w"], oy + st["shot_h"]), st["shot_radius"], st["shot_shadow_blur"],
           st["shot_shadow_alpha"])
    canvas.alpha_composite(rounded(shot, st["shot_radius"]), (ox, oy))

    # callouts: accent box around a UI rect + a label pill joined by an arrow
    lab_font = font(co["label_font"], co["label_size"])
    for c in callouts:
        x, y, w, h = c["rect"]
        p = co["pad"]
        box = (ox + x * sx - p, oy + y * sy - p, ox + (x + w) * sx + p, oy + (y + h) * sy + p)
        draw.rounded_rectangle(box, co["radius"], outline=rgb(co["stroke"]), width=co["stroke_w"])
        if not c.get("label"):
            continue
        tw = text_w(draw, c["label"], lab_font)
        lw, lh = tw + 2 * co["label_pad_x"], co["label_size"] + 2 * co["label_pad_y"]
        side = c.get("side", "right")
        gap = c.get("gap", 70)
        cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
        if side == "right":
            lx, ly = box[2] + gap, cy - lh / 2
            a0, a1 = (lx, cy), (box[2] + 4, cy)
        elif side == "left":
            lx, ly = box[0] - gap - lw, cy - lh / 2
            a0, a1 = (lx + lw, cy), (box[0] - 4, cy)
        elif side == "above":
            lx, ly = cx - lw / 2, box[1] - gap - lh
            a0, a1 = (cx, ly + lh), (cx, box[1] - 4)
        else:
            lx, ly = cx - lw / 2, box[3] + gap
            a0, a1 = (cx, ly), (cx, box[3] + 4)
        lx = min(max(lx, ox + 8), ox + st["shot_w"] - lw - 8)
        ly = min(max(ly, oy + 8), oy + st["shot_h"] - lh - 8)
        arrow(draw, a0, a1, rgb(co["stroke"]), co["arrow_w"], co["arrow_head"])
        draw.rounded_rectangle((lx, ly, lx + lw, ly + lh), co["label_radius"], fill=rgb(co["label_bg"]))
        draw.text((lx + co["label_pad_x"], ly + co["label_pad_y"] - 2), c["label"], font=lab_font,
                  fill=rgb(co["label_fg"]))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(out_path)
    return out_path


# --------------------------------------------------------------------------------------------- key visuals
def perspective_coeffs(src, dst):
    """Coefficients for Image.transform(PERSPECTIVE) mapping dst quad -> src quad (solve 8x8 by Gauss)."""
    rows, rhs = [], []
    for (x, y), (u, v) in zip(dst, src):
        rows.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); rhs.append(u)
        rows.append([0, 0, 0, x, y, 1, -v * x, -v * y]); rhs.append(v)
    n = 8
    m = [r + [b] for r, b in zip(rows, rhs)]
    for i in range(n):
        piv = max(range(i, n), key=lambda r: abs(m[r][i]))
        m[i], m[piv] = m[piv], m[i]
        for r in range(n):
            if r != i:
                f = m[r][i] / m[i][i]
                m[r] = [a - f * b for a, b in zip(m[r], m[i])]
    return [m[i][n] / m[i][i] for i in range(n)]


def tilted(img, width, tilt_deg, shrink=0.16, rise=0.06):
    """A screen turned about its vertical axis: the far (right) edge shorter, as a simple perspective."""
    w, h = img.size
    scale = width / w
    W, H = width, round(h * scale)
    k = math.sin(math.radians(tilt_deg)) * 2 * shrink / math.sin(math.radians(14))
    far = H * k / 2
    dst = [(0, 0), (W, far - H * rise), (W, H - far - H * rise), (0, H)]
    top = min(p[1] for p in dst)
    dst = [(x, y - top) for x, y in dst]
    out_h = round(max(p[1] for p in dst))
    coeffs = perspective_coeffs([(0, 0), (w, 0), (w, h), (0, h)], dst)
    src = rounded(img, 18)
    return src.transform((W, out_h), Image.PERSPECTIVE, coeffs, Image.BICUBIC)


def key_visual(content, shots, out_path, size=(1920, 1080), square=False):
    kv = STYLE["component"]["square" if square else "key_visual"]
    W, H = size
    canvas = vertical_gradient((W, H), rgb("grey-850"), rgb("grey-950")).convert("RGBA")
    # soft accent glow behind the screens
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gx, gy, gr = (W * 0.68, H * 0.5, H * 0.55) if not square else (W * 0.55, H * 0.68, W * 0.45)
    gd.ellipse((gx - gr, gy - gr, gx + gr, gy + gr), fill=rgb("accent", 46))
    canvas.alpha_composite(glow.filter(ImageFilter.GaussianBlur(160)))
    draw = ImageDraw.Draw(canvas)

    imgs = [Image.open(RAW / f"{n}.png").convert("RGB") for n in shots]
    if not square:
        # back screen, then front screen, staggered to the right
        placements = [(imgs[1], 1000, 940, 150), (imgs[0], 1160, 780, 390)]
        for img, wdt, x, y in placements:
            t = tilted(img, wdt, 14)
            shadow(canvas, (x, y, x + t.width, y + t.height), 18, 30, 170)
            canvas.alpha_composite(t, (x, y))
        tx = STYLE["component"]["key_visual"]["text_x"]
        ty = 300
    else:
        t = tilted(imgs[0], 1020, 12, shrink=0.12)
        x, y = 150, 600
        shadow(canvas, (x, y, x + t.width, y + t.height), 18, 30, 170)
        canvas.alpha_composite(t, (x, y))
        tx, ty = 96, 120
    name_f = font("font-bold", kv["name_size"])
    for_f = font("font-medium", kv["for_size"])
    tag_f = font("font-regular", kv["tagline_size"])
    draw.text((tx, ty), "Allset", font=name_f, fill=rgb("text-strong"))
    fy = ty + kv["name_size"] + 6
    draw.text((tx + 6, fy), "for Maya Users", font=for_f, fill=rgb("accent"))
    yy = fy + kv["for_size"] + 44
    for ln in content["key_visual_lines"]:
        draw.text((tx + 6, yy), ln, font=tag_f, fill=rgb("text"))
        yy += round(kv["tagline_size"] * 1.35)
    foot_f = font("font-medium", 24 if not square else 22)
    draw.text((tx + 6, yy + 28), content["key_visual_footer"], font=foot_f, fill=rgb("text-muted"))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(out_path)
    return out_path


def icon(out_path, size=256):
    """A radial marking menu: eight items round a centre, one in the accent (kit-made, no Maya mark)."""
    ss = 4
    N = size * ss
    img = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    r = STYLE["component"]["icon"]["radius"] * ss
    d.rounded_rectangle((0, 0, N - 1, N - 1), r, fill=rgb("grey-800"))
    d.rounded_rectangle((6 * ss, 6 * ss, N - 1 - 6 * ss, N - 1 - 6 * ss), r - 6 * ss, outline=rgb("grey-700"),
                        width=3 * ss)
    c = N / 2
    ring = N * 0.30
    pw, ph = N * 0.17, N * 0.085
    for i in range(8):
        a = math.radians(90 - i * 45)
        x, y = c + ring * math.cos(a), c - ring * math.sin(a)
        col = rgb("accent") if i == 1 else rgb("grey-300")
        d.rounded_rectangle((x - pw / 2, y - ph / 2, x + pw / 2, y + ph / 2), ph / 2, fill=col)
    # gesture line from the centre to the accent item
    a = math.radians(45)
    d.line(((c, c), (c + ring * 0.62 * math.cos(a), c - ring * 0.62 * math.sin(a))), fill=rgb("accent"),
           width=round(N * 0.028))
    cr = N * 0.06
    d.ellipse((c - cr, c - cr, c + cr, c + cr), fill=rgb("grey-050"))
    img = img.resize((size, size), Image.LANCZOS)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    return out_path


# --------------------------------------------------------------------------------------------- main
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--only", default="", help="comma-separated names (screens, key_visual, square, icon)")
    args = ap.parse_args(argv)
    only = {s for s in args.only.split(",") if s}
    content = json.loads((HERE / "content.json").read_text(encoding="utf-8"))
    meta = json.loads((RAW / "meta.json").read_text(encoding="utf-8")) if (RAW / "meta.json").exists() else {}
    made = []
    for i, sc in enumerate(content["screens"], 1):
        if only and sc["name"] not in only and "screens" not in only:
            continue
        if not (RAW / f"{sc['name']}.png").exists():
            print("missing shot:", sc["name"])
            continue
        callouts = []
        for c in sc.get("callouts", []):
            rect = meta.get(sc["name"], {}).get("rects", {}).get(c["rect"]) if isinstance(c["rect"], str) else c["rect"]
            if rect:
                callouts.append({**c, "rect": rect})
            else:
                print(f"{sc['name']}: no rect {c['rect']}")
        made.append(screen(sc["name"], sc["title"], sc["line"], callouts,
                           OUT / "screens" / f"{i:02d}_{sc['name']}.png"))
    if not only or "key_visual" in only:
        made.append(key_visual(content, content["key_visual_shots"], OUT / "key_visual.png"))
    if not only or "square" in only:
        made.append(key_visual(content, content["key_visual_shots"][:1], OUT / "key_visual_square.png",
                               size=tuple(STYLE["component"]["square"]["canvas"]), square=True))
    if not only or "icon" in only:
        made.append(icon(OUT / "icon_256.png"))
    for m in made:
        print("wrote", m.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
