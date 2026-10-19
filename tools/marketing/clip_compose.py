"""Clip compositing and encoding (step 123): frames + timeline.json from tools/marketing/clips.py -> MP4 / GIF / trailer.

    python tools/marketing/clip_compose.py [--only NAME,...] [--no-trailer] [--no-gif]

Each output frame (1920 x 1080, 30 fps) = the window picture scaled to 85 % on the marketing canvas
(docs/distribution/marketing/style.md) + a caption band below it (clip title, what happens now, key chips) + the
mouse cursor (drawn here: event simulation never moves the OS cursor), click ripples and a held-button ring. Frames are
piped raw into ffmpeg (no PNG sequence on disk):
- docs/distribution/marketing/clips/<nn>_<name>.mp4: H.264 High, yuv420p, 30 fps, +faststart, no audio (store preview,
  references.md: ≤ 8 MB);
- docs/distribution/marketing/gif/<nn>_<name>.gif: 960 px, palette per clip (palettegen stats_mode=diff), ≤ 5 MB
  (README / social only, never extensions.blender.org);
- docs/distribution/marketing/clips/00_trailer.mp4: key visual title card (the store poster = first frame) -> a part of
  every clip -> end card (headline, download placeholder), crossfades, no music, ≤ 20 MB.
ffmpeg: PATH, or $FFMPEG, or the hermes build named in the step 123 request.
"""

import argparse
import collections
import itertools
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from compose import ROOT, font, rgb, rounded, shadow, text_w, vertical_gradient  # noqa: E402

HERE = Path(__file__).resolve().parent
FRAMES = ROOT / "tmp" / "marketing" / "clips"
OUT = ROOT / "docs" / "distribution" / "marketing"
CONTENT = json.loads((HERE / "content.json").read_text(encoding="utf-8"))
W, H, FPS = 1920, 1080, 30
SHOT = (144, 22, 1632, 918)          # x, y, w, h of the window picture (85 %, style.md)
BAND_Y = SHOT[1] + SHOT[3]            # caption band below it
LIMIT_MP4, LIMIT_TRAILER, LIMIT_GIF = 8e6, 20e6, 5e6
FFMPEG_FALLBACK = Path("C:/Users/ohnsk/AppData/Local/hermes/tools/ffmpeg-9.0.1-win32-x64/bin/ffmpeg.exe")


def ffmpeg():
    exe = os.environ.get("FFMPEG") or shutil.which("ffmpeg") or (str(FFMPEG_FALLBACK) if FFMPEG_FALLBACK.exists()
                                                                    else None)
    if not exe:
        sys.exit("ffmpeg not found (PATH, $FFMPEG)")
    return exe


# --------------------------------------------------------------------------------------------- drawing
_BG = None


def background():
    global _BG
    if _BG is None:
        _BG = vertical_gradient((W, H), rgb("grey-900"), rgb("grey-950")).convert("RGBA")
        shadow(_BG, (SHOT[0], SHOT[1], SHOT[0] + SHOT[2], SHOT[1] + SHOT[3]), 10, 28, 150)
    return _BG


def window_picture(path, logo):
    img = Image.open(path).convert("RGB")
    if logo:   # no Blender logo in the pictures (extensions.blender.org terms 2.2), like shots.hide_logo
        x, y, w, h = logo
        img.paste(img.getpixel((x + w, y + 1)), (x, y, x + w, y + h))
    return img.resize(SHOT[2:], Image.LANCZOS)


def chip(draw, right, cy, text):
    f = font("font-semibold", 28)
    tw = text_w(draw, text, f)
    pad_x, h = 18, 50
    x0 = right - tw - 2 * pad_x
    draw.rounded_rectangle((x0, cy - h // 2, right, cy + h // 2), 10, fill=rgb("accent"))
    draw.text((x0 + pad_x, cy), text, font=f, fill=rgb("on-accent"), anchor="lm")
    return x0


def base_frame(img, title, caption, chips):
    canvas = background().copy()
    canvas.alpha_composite(rounded(img, 10), SHOT[:2])
    d = ImageDraw.Draw(canvas)
    x = SHOT[0]
    d.rectangle((x, BAND_Y + 26, x + 5, BAND_Y + 26 + 46), fill=rgb("accent"))
    d.text((x + 24, BAND_Y + 20), title, font=font("font-semibold", 40), fill=rgb("text-strong"))
    if caption:
        d.text((x + 24, BAND_Y + 74), caption, font=font("font-regular", 28), fill=rgb("text"))
    right = SHOT[0] + SHOT[2]
    brand = "Allset for Maya Users"
    bf = font("font-medium", 20)
    d.text((right - text_w(d, brand, bf), BAND_Y + 100), brand, font=bf, fill=rgb("text-muted"))
    r = right
    for c in reversed(chips):
        r = chip(d, r, BAND_Y + 52, c) - 12
    return canvas


ARROW = [(0, 0), (0, 22), (5.5, 17), (9.5, 26), (13, 24.5), (9, 16), (16, 16)]   # kit-drawn pointer, 26 px tall


def to_canvas(p):
    s = SHOT[2] / W
    return SHOT[0] + p[0] * s, SHOT[1] + p[1] * s


def overlay(frame, pos, ripples, down):
    d = ImageDraw.Draw(frame, "RGBA")
    cx, cy = to_canvas(pos)
    for age in ripples:                       # click: an amber ring that grows and fades out in 0.4 s
        t = min(age / 0.4, 1.0)
        r = 10 + 26 * t
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=rgb("accent", int(255 * (1 - t))), width=4)
    if down:                                  # a button held: a small solid ring at the tip
        d.ellipse((cx - 13, cy - 13, cx + 13, cy + 13), outline=rgb("accent", 230), width=4)
    pts = [(cx + x, cy + y) for x, y in ARROW]
    d.polygon(pts, fill=(255, 255, 255, 255))
    d.line(pts + [pts[0]], fill=(0, 0, 0, 255), width=2, joint="curve")
    return frame


def ease(t):
    return t * t * (3 - 2 * t)


# --------------------------------------------------------------------------------------------- clip frames
def clip_info(name):
    return next(c for c in CONTENT["clips"] if c["name"] == name)


def clip_frames(name, start=0.0, end=None):
    """RGB frames of a clip between ``start`` and ``end`` seconds (timeline time)."""
    folder = FRAMES / name
    tl = json.loads((folder / "timeline.json").read_text(encoding="utf-8"))
    entries = tl["entries"]
    title = clip_info(name)["title"]
    t0, spans = 0.0, []
    for e in entries:
        spans.append((t0, t0 + e["dur"], e))
        t0 += e["dur"]
    total = t0
    end = total if end is None else min(end, total)
    clicks = [(s, e["to"]) for s, _x, e in spans if e["click"]]
    cache = {}
    n = int(round((end - start) * FPS))
    k = 0
    for i in range(n):
        t = start + i / FPS
        while k < len(spans) - 1 and t >= spans[k][1]:
            k += 1
        s0, s1, e = spans[k]
        key = (e["img"], e["caption"], tuple(e["chips"]))
        if key not in cache:
            cache.clear()
            img = window_picture(folder / e["img"], tl.get("logo"))
            cache[key] = base_frame(img, title, e["caption"], e["chips"])
        u = ease(min(max((t - s0) / max(s1 - s0, 1e-6), 0.0), 1.0))
        pos = (e["from"][0] + (e["to"][0] - e["from"][0]) * u, e["from"][1] + (e["to"][1] - e["from"][1]) * u)
        ripples = [t - cs for cs, _p in clicks if 0 <= t - cs < 0.4]
        frame = overlay(cache[key].copy(), pos, ripples, bool(e["down"]))
        yield frame.convert("RGB")


def encode(frames, out, crf=20):
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [ffmpeg(), "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", str(crf), "-profile:v", "high",
           "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an", str(out)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    count = 0
    for f in frames:
        proc.stdin.write(f.tobytes())
        count += 1
    proc.stdin.close()
    if proc.wait():
        sys.exit(f"ffmpeg failed for {out}")
    return count


def gif(mp4, out):
    out.parent.mkdir(parents=True, exist_ok=True)
    for fps, colours, dither in ((15, 192, "sierra2_4a"), (12, 160, "bayer:bayer_scale=4"),
                                 (10, 128, "bayer:bayer_scale=3")):
        vf = (f"fps={fps},scale=960:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors={colours}:stats_mode=diff[p];"
              f"[b][p]paletteuse=dither={dither}:diff_mode=rectangle")
        subprocess.run([ffmpeg(), "-y", "-loglevel", "error", "-i", str(mp4), "-filter_complex", vf, "-loop", "0",
                        str(out)], check=True, stdin=subprocess.DEVNULL)
        if out.stat().st_size <= LIMIT_GIF:
            return fps
    return fps


def poster(frames, out):
    """Save the first frame (the store's video poster) for review."""
    first = next(frames)
    out.parent.mkdir(parents=True, exist_ok=True)
    first.save(out)


# --------------------------------------------------------------------------------------------- trailer
def end_card():
    tr = CONTENT["trailer"]
    canvas = vertical_gradient((W, H), rgb("grey-850"), rgb("grey-950")).convert("RGBA")
    d = ImageDraw.Draw(canvas)
    icon = Image.open(OUT / "icon_256.png").convert("RGBA").resize((168, 168), Image.LANCZOS)
    canvas.alpha_composite(icon, ((W - 168) // 2, 190))
    cx = W // 2
    d.text((cx, 400), "Allset", font=font("font-bold", 120), fill=rgb("text-strong"), anchor="mt")
    d.text((cx, 540), "for Maya Users", font=font("font-medium", 44), fill=rgb("accent"), anchor="mt")
    d.text((cx, 650), tr["end_headline"], font=font("font-semibold", 46), fill=rgb("text-strong"), anchor="mt")
    d.text((cx, 728), tr["end_line"], font=font("font-regular", 32), fill=rgb("text"), anchor="mt")
    f = font("font-semibold", 32)
    tw = text_w(d, tr["download"], f)
    d.rounded_rectangle((cx - tw / 2 - 28, 820, cx + tw / 2 + 28, 884), 12, fill=rgb("accent"))
    d.text((cx, 852), tr["download"], font=f, fill=rgb("on-accent"), anchor="mm")
    return canvas.convert("RGB")


def still(img, seconds):
    for _ in range(int(round(seconds * FPS))):
        yield img


def crossfade(segments, n=8):
    """Concatenate frame generators; the last ``n`` frames of a segment blend into the first ``n`` of the next."""
    tail = []
    for seg in segments:
        it = iter(seg)
        if tail:
            head = list(itertools.islice(it, len(tail)))
            m = len(head)
            for j in range(m):
                yield Image.blend(tail[j], head[j], (j + 1) / (m + 1))
            yield from tail[m:]
        buf = collections.deque()
        for f in it:
            buf.append(f)
            if len(buf) > n:
                yield buf.popleft()
        tail = list(buf)
    yield from tail


def trailer():
    tr = CONTENT["trailer"]
    title = Image.open(OUT / f"{tr['title_card']}.png").convert("RGB").resize((W, H))
    segs = [still(title, tr["title_seconds"])]
    for c in CONTENT["clips"]:
        a, b = c["trailer"]
        segs.append(clip_frames(c["name"], a, b))
    segs.append(still(end_card(), tr["end_seconds"]))
    return crossfade(segs)


# --------------------------------------------------------------------------------------------- main
def mb(path):
    return path.stat().st_size / 1e6


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--only", default="")
    ap.add_argument("--no-trailer", action="store_true")
    ap.add_argument("--no-gif", action="store_true")
    args = ap.parse_args(argv)
    only = [n for n in args.only.split(",") if n]
    ok = True
    report = []
    for c in CONTENT["clips"]:
        if only and c["name"] not in only:
            continue
        if not (FRAMES / c["name"] / "timeline.json").exists():
            print("missing frames:", c["name"])
            ok = False
            continue
        mp4 = OUT / "clips" / f"{c['file']}.mp4"
        n = encode(clip_frames(c["name"]), mp4)
        poster(clip_frames(c["name"]), ROOT / "tmp" / "marketing" / "posters" / f"{c['file']}.png")
        row = {"file": mp4.relative_to(ROOT).as_posix(), "seconds": round(n / FPS, 2), "MB": round(mb(mp4), 2),
               "ok": mb(mp4) * 1e6 <= LIMIT_MP4}
        report.append(row)
        if not args.no_gif:
            g = OUT / "gif" / f"{c['file']}.gif"
            fps = gif(mp4, g)
            report.append({"file": g.relative_to(ROOT).as_posix(), "fps": fps, "MB": round(mb(g), 2),
                           "ok": mb(g) * 1e6 <= LIMIT_GIF})
    if not args.no_trailer and not only:
        mp4 = OUT / "clips" / f"{CONTENT['trailer']['file']}.mp4"
        n = encode(trailer(), mp4, crf=22)
        poster(trailer(), ROOT / "tmp" / "marketing" / "posters" / "00_trailer.png")
        sec = n / FPS
        report.append({"file": mp4.relative_to(ROOT).as_posix(), "seconds": round(sec, 2), "MB": round(mb(mp4), 2),
                       "ok": mb(mp4) * 1e6 <= LIMIT_TRAILER and 30 <= sec <= 45})
    for r in report:
        print("PASS" if r["ok"] else "FAIL", json.dumps(r))
        ok &= r["ok"]
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
