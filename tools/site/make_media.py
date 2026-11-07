"""Web copies of marketing media for site/media.

    python tools/site/make_media.py                       # everything
    python tools/site/make_media.py webm:hotbox,rigging   # one group, some names
    groups: webm (clip at 1280 and 960 wide, trailer at 1280), mp4 (x264 fallback), posters (webp at 1280 and 640),
            stills (shot-*.jpg / .webp from the raw screenshots, og.png, icons); names = clip stems, "trailer",
            still names, "og", "icons"
"""
import json, os, shutil, subprocess, sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
BIN = Path(os.environ.get("LOCALAPPDATA", "")) / "hermes" / "tools" / "ffmpeg-9.0.1-win32-x64" / "bin"
FF, FP = str(BIN / "ffmpeg.exe"), str(BIN / "ffprobe.exe")
MK = ROOT / "docs/distribution/marketing"
OUT = ROOT / "site/media"
# what site/index.html and app.js use (#41: the full lists left 32 unused files in site/media)
CLIPS = {"hotbox": "01_hotbox", "channel_box_keys": "03_channel_box_keys", "navigation": "04_navigation",
         "pivot_snap": "05_pivot_snap", "rigging": "06_rigging"}
TRAILER = "00_trailer"
RAW = ["hero", "menus_shelves", "switch_before"]
VF = "scale=1280:-2:flags=lanczos"
VF_SMALL = "scale=960:-2:flags=lanczos"
LOG = []

def run(args):
    subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-y", *args],
                   check=True, stdin=subprocess.DEVNULL)

def mp4(src, dst, limit, crf=22):
    while True:
        run(["-i", str(src), "-an", "-vf", VF, "-c:v", "libx264", "-profile:v", "high",
             "-pix_fmt", "yuv420p", "-preset", "veryslow", "-tune", "animation", "-crf", str(crf),
             "-movflags", "+faststart", str(dst)])
        if dst.stat().st_size <= limit or crf >= 34:
            LOG.append((dst.name, f"x264 crf {crf}")); return
        crf += 1

def webm(src, dst, limit, crf, vf=VF):
    """VP9, constant quality, raised two steps at a time until the file is under ``limit`` bytes."""
    while True:
        run(["-i", str(src), "-an", "-vf", vf, "-c:v", "libvpx-vp9", "-crf", str(crf), "-b:v", "0",
             "-deadline", "good", "-cpu-used", "2", "-row-mt", "1", "-pix_fmt", "yuv420p", str(dst)])
        if dst.stat().st_size <= limit or crf >= 52:
            LOG.append((dst.name, f"vp9 crf {crf} {dst.stat().st_size} B")); return
        crf += 2

def poster(src, stem, t):
    """One frame as the poster: webp at 1280 (the page's poster) and at 640 (phones)."""
    png = OUT / f"_{stem}.png"
    run(["-ss", str(t), "-i", str(src), "-frames:v", "1", "-vf", VF, str(png)])
    im = Image.open(png).convert("RGB")
    im.save(OUT / f"{stem}.webp", quality=80, method=6)
    im.resize((640, 360), Image.LANCZOS).save(OUT / f"{stem}-640.webp", quality=78, method=6)
    LOG.append((f"{stem}.webp", f"poster @ {t}s + 640"))
    png.unlink()

def still(name):
    im = Image.open(ROOT / "tmp/marketing/raw" / f"{name}.png").convert("RGB")
    for w, sfx in ((1600, ""), (800, "-800")):
        r = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
        r.save(OUT / f"shot-{name}{sfx}.webp", quality=80, method=6)
        if sfx == "":
            r.save(OUT / f"shot-{name}.jpg", quality=82, optimize=True, progressive=True)

def probe(p):
    if p.suffix in (".mp4", ".webm"):
        o = json.loads(subprocess.check_output([FP, "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=width,height:format=duration", "-of", "json", str(p)],
            stdin=subprocess.DEVNULL))
        s = o["streams"][0]
        return s["width"], s["height"], round(float(o["format"]["duration"]), 3)
    with Image.open(p) as im:
        return im.width, im.height, None

def main():
    only = dict(a.split(":", 1) if ":" in a else (a, "") for a in sys.argv[1:])
    def wanted(group, name):
        if only and group not in only: return False
        names = set(n for n in only.get(group, "").split(",") if n)
        return not names or name in names
    for stem, clip in CLIPS.items():
        src = MK / "clips" / f"{clip}.mp4"
        if wanted("webm", stem):
            webm(src, OUT / f"{stem}.webm", 520_000, 38)
            webm(src, OUT / f"{stem}-540.webm", 300_000, 36, VF_SMALL)
        if wanted("mp4", stem): mp4(src, OUT / f"{stem}.mp4", 1_200_000)
        if wanted("posters", stem): poster(src, stem, 0.5)
    src = MK / "clips" / f"{TRAILER}.mp4"
    if wanted("webm", "trailer"): webm(src, OUT / "trailer.webm", 3_000_000, 34)
    if wanted("mp4", "trailer"): mp4(src, OUT / "trailer.mp4", 4_000_000)
    if wanted("posters", "trailer"): poster(src, "trailer", 0)
    for n in RAW:
        if wanted("stills", n): still(n)
    if wanted("stills", "og"):
        shutil.copyfile(MK / "kit/social_preview.png", OUT / "og.png")
    if wanted("stills", "icons"):
        master = Image.open(MK / "icon/icon_1024.png").convert("RGBA")        # icon master (link_a)
        master.resize((256, 256), Image.LANCZOS).save(OUT / "icon-256.png", optimize=True)
        master.resize((180, 180), Image.LANCZOS).save(OUT / "favicon-180.png", optimize=True)
        Image.open(MK / "icon/icon_32.png").convert("RGBA").save(OUT / "favicon-32.png", optimize=True)  # hand-hinted 32 px
    files, total = [], 0
    for p in sorted(OUT.iterdir()):
        if p.name == "media.json" or p.name.startswith("_") or p.suffix == ".json": continue   # *.webp.json = image provenance
        w, h, d = probe(p); b = p.stat().st_size; total += b
        e = {"path": f"media/{p.name}", "bytes": b, "width": w, "height": h}
        if d is not None: e["duration"] = d
        files.append(e)
    (OUT / "media.json").write_text(json.dumps({"files": files, "total_bytes": total,
        "count": len(files)}, indent=2), encoding="utf-8")
    for n, s in LOG: print(n, s)
    for e in files: print(f'{e["path"]:40} {e["bytes"]:>9} {e["width"]}x{e["height"]} {e.get("duration", "")}')
    print("total", total)

main()
