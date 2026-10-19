# Marketing kit — Allset for Maya Users

Everything here is made from real Allset sessions in Blender (GUI Blender, clean sandbox, Maya theme, Maya's factory
viewport background #5c5c5c) with the licensed models of `CREDITS.md`. Copy: `copy.md`. Visual system: `style.md`.
Media standard and platform research: `references.md` (step 121), `research/marketing_refs/platform_rules_123.md`
(not tracked). Nothing has been published (decision 11).

**GIFs are not uploaded to extensions.blender.org.** The store gallery takes JPEG / PNG / WebP images and MP4 videos
only (`references.md` §1), and its moderation guideline discourages heavy GIFs in the description. The store gets the
MP4s in `clips/` (upload order and captions: `docs/distribution/listing.md` part C); the GIFs in `gif/` are for the
GitHub README, social posts and links from the description.

## Files

| File | Use | Size | MB |
|---|---|---|---|
| `clips/00_trailer.mp4` | Store gallery item 1 (first frame = key visual title card = the store's poster); YouTube; 80.lv pitch | 1920 × 1080, 38.8 s, 30 fps, H.264, no audio | 3.97 |
| `clips/01_hotbox.mp4` | Store gallery 2; X / Reddit video | 1920 × 1080, 7.4 s, 30 fps | 0.65 |
| `clips/02_marking_menu.mp4` | Store gallery 3 | 1920 × 1080, 6.8 s | 0.41 |
| `clips/03_channel_box_keys.mp4` | Store gallery 4 | 1920 × 1080, 8.9 s | 0.70 |
| `clips/04_navigation.mp4` | Store gallery 5 | 1920 × 1080, 8.7 s | 1.30 |
| `clips/05_pivot_snap.mp4` | Store gallery 6 | 1920 × 1080, 7.4 s | 0.54 |
| `clips/06_rigging.mp4` | Store gallery 7 | 1920 × 1080, 8.6 s | 0.70 |
| `clips/07_switch.mp4` | Store gallery 8; r/blender lead video | 1920 × 1080, 6.1 s | 0.63 |
| `gif/01_hotbox.gif` … `gif/07_switch.gif` | GitHub README (`README_marketing.md`), social, description links — **not the store** | 960 × 540, 15 fps, looping | 1.02 – 4.91 (all ≤ 5) |
| `kit/readme_hero.png` | GitHub README top banner | 1920 × 720 | 0.42 |
| `kit/social_preview.png` | GitHub repository social preview (Settings → Social preview; GitHub: PNG/JPG/GIF < 1 MB, 1280 × 640) | 1280 × 640 | 0.23 |
| `kit/x_card.png` | X post image (≤ 5 MB) | 1600 × 900 | 0.36 |
| `kit/reddit_before_after.png` | Reddit / BlenderArtists image: Maya mode next to plain Blender | 1920 × 1080 | 0.57 |
| `kit/reddit_square.png` | Reddit / Instagram-style square | 1080 × 1080 | 0.37 |
| `kit/youtube_thumbnail.png` | YouTube thumbnail for the trailer (16:9, ≤ 2 MB) | 1280 × 720 | 0.34 |
| `key_visual.png` | Store featured image (also `../media/featured.png`), og:image, trailer title card | 1920 × 1080 | 0.67 |
| `key_visual_square.png` | Square social card | 1080 × 1080 | 0.38 |
| `icon_256.png` | Store icon (also `../media/icon.png`) | 256 × 256 | 0.01 |
| `screens/01–10_*.png` | Captioned feature stills (step 122); `03`, `04` = store gallery 9–10 | 1920 × 1080 | 0.54 – 1.04 |
| `README_marketing.md` | Draft of the README top with the GIFs | – | – |
| `posts.md` | Post drafts (r/blender, r/Maya, X, BlenderArtists, 80.lv) + each platform's rules | – | – |

Size limits checked by the scripts: store clips ≤ 8 MB, trailer ≤ 20 MB and 30–45 s (`references.md` §5), GIF ≤ 5 MB,
GitHub social preview < 1 MB, YouTube thumbnail ≤ 2 MB, X image ≤ 5 MB.

## Regenerate

```
python tools/marketing/make_clips.py            # build + sandbox + one GUI Blender per clip -> clips/, gif/, trailer
python tools/marketing/make_clips.py --only rigging --no-build   # one clip again (then clip_compose.py for the trailer)
python tools/marketing/clip_compose.py          # re-encode from tmp/marketing/clips/ (no Blender)
python tools/marketing/kit.py                   # kit/ images (needs tmp/marketing/raw from make_marketing.py and the switch clip frames)
python tools/marketing/make_marketing.py        # step 122 stills, key visuals, icon
```

How the clips are made (`docs/steps/step_123.md`): `tools/marketing/clips.py` drives a GUI Blender with
`--enable-event-simulate` — one action per timer tick, a `screen.screenshot` before each action — and writes a timeline
(duration, cursor path, caption, key chips per picture). `clip_compose.py` draws the cursor (event simulation never
moves the OS cursor), click ripples, the key chips ("Space (hold)", "Alt + LMB drag", …) and the caption band, and pipes
30 fps frames into ffmpeg (`libx264 -crf 20 -pix_fmt yuv420p -movflags +faststart`); GIFs use a per-clip palette
(`palettegen stats_mode=diff` + `paletteuse`). ffmpeg comes from PATH, `$FFMPEG`, or
`C:/Users/ohnsk/AppData/Local/hermes/tools/ffmpeg-9.0.1-win32-x64/bin`.

## Placeholders to fill before publishing

- Trailer end card and posts: "Get it on extensions.blender.org/add-ons/allset" — the listing URL once it is live
  (`content.json` → `trailer.download`; rerun `clip_compose.py`).
- `posts.md`: `<listing URL>`, `<GitHub URL>`, `<YouTube URL>`.
