"""Marketing kit images (step 123): GitHub README hero + social preview, X card, Reddit image, YouTube thumbnail.

    python tools/marketing/kit.py

Inputs: the step 122 GUI shots (tmp/marketing/raw/, tools/marketing/shots.py), the step 123 switch clip frames
(tmp/marketing/clips/switch/, tools/marketing/clips.py), copy from tools/marketing/content.json (copy.md), tokens from
style.json (style.md). Outputs in docs/distribution/marketing/kit/ (sizes from 
platform_rules_123.md: GitHub social preview 1280 x 640 < 1 MB, X image ≤ 5 MB, YouTube thumbnail 1280 x 720 ≤ 2 MB).
"""

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from compose import RAW, ROOT, font, lockup, rgb, rounded, shadow, text_w, tilted, vertical_gradient  # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = ROOT / "docs" / "distribution" / "marketing" / "kit"
CLIPS = ROOT / "tmp" / "marketing" / "clips"
CONTENT = json.loads((HERE / "content.json").read_text(encoding="utf-8"))
HEADLINE = CONTENT["trailer"]["end_headline"]
TAGLINE = "The whole Maya workflow in Blender, in one install."
LIMITS = {"social_preview.png": 1e6, "youtube_thumbnail.png": 2e6, "x_card.png": 5e6, "readme_hero.png": 5e6,
          "reddit_before_after.png": 20e6, "reddit_square.png": 20e6}


def shot(name):
    return Image.open(RAW / f"{name}.png").convert("RGB")


def clip_frame(clip, img):
    """A clip frame with the Blender logo painted over (as clip_compose.window_picture)."""
    tl = json.loads((CLIPS / clip / "timeline.json").read_text(encoding="utf-8"))
    im = Image.open(CLIPS / clip / img).convert("RGB")
    x, y, w, h = tl["logo"]
    im.paste(im.getpixel((x + w, y + 1)), (x, y, x + w, y + h))
    return im


def canvas(size, glow_at=None):
    W, H = size
    c = vertical_gradient((W, H), rgb("grey-850"), rgb("grey-950")).convert("RGBA")
    if glow_at:
        g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        gx, gy, gr = glow_at
        ImageDraw.Draw(g).ellipse((gx - gr, gy - gr, gx + gr, gy + gr), fill=rgb("accent-deep", 70))
        c.alpha_composite(g.filter(ImageFilter.GaussianBlur(gr * 0.3)))
    return c


def brand_block(d, x, y, s, lines, name_px=120):
    """The lockup (style.md), then ``lines``; ``s`` scales the 1920 x 1080 sizes of style.md."""
    box = lockup(d, x, y, round(name_px * s))
    y = box[3] + round(40 * s)
    for ln, size, col in lines:
        d.text((x + 4 * s, y), ln, font=font("font-regular" if col == "text" else "font-semibold", round(size * s)),
               fill=rgb(col))
        y += round(size * 1.4 * s)
    return y


def place_screen(c, img, width, x, y, tilt=12):
    t = tilted(img, width, tilt, shrink=0.12)
    shadow(c, (x, y, x + t.width, y + t.height), 16, 26, 170)
    c.alpha_composite(t, (x, y))


def flat_screen(c, img, box):
    x, y, w, h = box
    im = rounded(img.resize((w, h), Image.LANCZOS), 10)
    shadow(c, (x, y, x + w, y + h), 10, 24, 160)
    c.alpha_composite(im, (x, y))


def save(c, name):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    c.convert("RGB").save(path, optimize=True)
    return path


# --------------------------------------------------------------------------------------------- images
def wide(size, name, lines, screen="hero", screen_w=None, text_scale=1.15, text_y=0.20):
    """Text left, one turned real screen right (vertically centred): README hero, GitHub social preview, X card."""
    W, H = size
    s = H / 1080
    c = canvas(size, (W * 0.70, H * 0.52, H * 0.6))
    sw = screen_w or round(W * 0.56)
    t = tilted(shot(screen), sw, 12, shrink=0.12)
    x, y = W - sw - round(W * 0.03), (H - t.height) // 2
    shadow(c, (x, y, x + t.width, y + t.height), 16, 26, 170)
    c.alpha_composite(t, (x, y))
    d = ImageDraw.Draw(c)
    brand_block(d, round(W * 0.055), round(H * text_y), s * text_scale, lines)
    return save(c, name)


def before_after():
    """Reddit image: the same scene in Maya mode and in plain Blender, one click apart (switch clip frames)."""
    W, H = 1920, 1080
    c = canvas((W, H))
    d = ImageDraw.Draw(c)
    d.text((W // 2, 64), "One click between Maya mode and plain Blender", font=font("font-semibold", 56),
           fill=rgb("text-strong"), anchor="mt")
    d.text((W // 2, 140), "Same scene, same file. Allset changes nothing until you choose Maya.",
           font=font("font-regular", 30), fill=rgb("text"), anchor="mt")
    maya = clip_frame("switch", "f0000.png")
    blender = clip_frame("switch", "f0003.png")
    bw, bh = 864, 486
    for i, (im, label) in enumerate(((maya, "Maya mode"), (blender, "Blender mode"))):
        x = 72 + i * (bw + 48)
        if i == 0:   # the Maya side carries the accent: a frame and a filled pill; Blender's side stays grey
            d.rounded_rectangle((x - 8, 242, x + bw + 8, 250 + bh + 8), 16, outline=rgb("accent"), width=5)
        flat_screen(c, im, (x, 250, bw, bh))
        f = font("font-semibold", 30)
        tw = text_w(d, label, f)
        pill = (x + bw / 2 - tw / 2 - 22, 770, x + bw / 2 + tw / 2 + 22, 826)
        if i == 0:
            d.rounded_rectangle(pill, 10, fill=rgb("accent"))
        else:
            d.rounded_rectangle(pill, 10, outline=rgb("grey-500"), width=3)
        d.text((x + bw / 2, 798), label, font=f, fill=rgb("on-accent" if i == 0 else "text"), anchor="mm")
    probe = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    box = lockup(probe, 0, 0, 64, one_line=True)
    lockup(d, (W - (box[2] - box[0])) / 2, 880, 64, one_line=True)
    d.text((W // 2, 985), "Free and open-source extension for Blender 4.5 – 5.2", font=font("font-medium", 28),
           fill=rgb("text-muted"), anchor="mt")
    return save(c, "reddit_before_after.png")


def square():
    W = H = 1080
    c = canvas((W, H), (W * 0.55, H * 0.72, W * 0.45))
    d = ImageDraw.Draw(c)
    brand_block(d, 92, 96, 0.82, [("Hotbox, marking menus, Channel Box,", 34, "text"),
                                  ("and plain Blender one click away.", 34, "text")])
    place_screen(c, shot("hotbox"), 1040, 150, 560)
    return save(c, "reddit_square.png")


def youtube():
    """1280 x 720 thumbnail: three words big, the hotbox crop big (legible at 320 px)."""
    W, H = 1280, 720
    c = canvas((W, H), (W * 0.72, H * 0.5, H * 0.55))
    hb = shot("hotbox")
    meta = json.loads((RAW / "meta.json").read_text(encoding="utf-8"))
    vx, vy, vw, vh = meta["hotbox"]["rects"]["viewport"]
    crop = hb.crop((vx + vw * 0.08, vy + vh * 0.14, vx + vw * 0.90, vy + vh * 0.86))
    cw = 720
    flat_screen(c, crop, (W - cw - 32, 150, cw, round(cw * crop.height / crop.width)))
    d = ImageDraw.Draw(c)
    y = 150
    for ln, col in (("Blender,", "text-strong"), ("the Maya", "accent"), ("way.", "text-strong")):
        d.text((48, y), ln, font=font("font-bold", 84), fill=rgb(col))
        y += 100
    lockup(d, 52, y + 18, 40, one_line=True)
    d.text((52, y + 82), "free · open source", font=font("font-medium", 28), fill=rgb("text-muted"))
    return save(c, "youtube_thumbnail.png")


def main():
    out = [
        wide((1920, 720), "readme_hero.png", [(TAGLINE, 34, "text"), (HEADLINE, 34, "text-strong")], screen_w=1050),
        wide((1280, 640), "social_preview.png", [("The whole Maya workflow", 34, "text"),
                                                 ("in Blender, in one install.", 34, "text"),
                                                 ("Free · open source · Blender 4.5 – 5.2", 26, "text-muted")],
             screen_w=660, text_scale=1.05, text_y=0.17),
        wide((1600, 900), "x_card.png", [("The tutorial ends.", 44, "text-strong"),
                                         ("Your Channel Box comes back.", 44, "text-strong"),
                                         ("Maya workflow in Blender, one install.", 28, "text")],
             screen_w=860, text_scale=1.05, text_y=0.17),
        before_after(),
        square(),
        youtube(),
    ]
    ok = True
    for p in out:
        lim = LIMITS[p.name]
        size = p.stat().st_size
        print("PASS" if size <= lim else "FAIL", p.relative_to(ROOT).as_posix(), Image.open(p).size, f"{size / 1e6:.2f} MB")
        ok &= size <= lim
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
