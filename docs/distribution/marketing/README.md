# Marketing kit — Maya Workflow Kit

Everything here is made from real kit sessions in Blender (GUI Blender, clean sandbox, **Blender's factory theme** —
step 142, #41: the kit ships no theme since step 130 and the generators never write one; Maya's flat #5c5c5c viewport
background is view / scene data, checked by `tools/marketing/bg_check.py`; step 125's gradient needed a theme) with the
licensed models of `CREDITS.md`. Name and lockup (step 125): "Maya Workflow Kit" + "for Maya users, in Blender"
(`style.md`, decision 12 revision). Copy: `copy.md`. Visual system: `style.md` (step 124: Maya logo teal + Autodesk Hello Yellow, one lockup rule, motion). Design
review: `design_review.md` (impeccable critique and what was fixed).
Media standard and platform research: `references.md` (step 121), `research/marketing_refs/platform_rules_123.md`
(not tracked). Nothing has been published (decision 11).

**GIFs are not uploaded to extensions.blender.org.** The store gallery takes JPEG / PNG / WebP images and MP4 videos
only (`references.md` §1), and its moderation guideline discourages heavy GIFs in the description. The store gets the
MP4s in `clips/` (upload order and captions: `docs/distribution/listing.md` part C); the GIFs in `gif/` are for the
GitHub README, social posts and links from the description.

## Files

| File | Use | Size | MB |
|---|---|---|---|
| `clips/00_trailer.mp4` | Store gallery item 1 (first frame = key visual title card = the store's poster); YouTube; 80.lv pitch | 1920 × 1080, 33.5 s, 30 fps, H.264, no audio | 11.59 |
| `clips/01_hotbox.mp4` | Store gallery 2; X / Reddit video | 1920 × 1080, 6.4 s, 30 fps | 3.92 |
| `clips/02_marking_menu.mp4` | Store gallery 3 | 1920 × 1080, 5.9 s | 2.82 |
| `clips/03_channel_box_keys.mp4` | Store gallery 4 | 1920 × 1080, 7.2 s | 3.66 |
| `clips/04_navigation.mp4` | Store gallery 5 | 1920 × 1080, 7.6 s | 3.24 |
| `clips/05_pivot_snap.mp4` | Store gallery 6 | 1920 × 1080, 6.1 s | 2.82 |
| `clips/06_rigging.mp4` | Store gallery 7 | 1920 × 1080, 7.0 s | 2.43 |
| `clips/07_switch.mp4` | Store gallery 8; r/blender lead video | 1920 × 1080, 5.6 s | 2.00 |
| `gif/01_hotbox.gif` … `gif/07_switch.gif` | GitHub README (`README_marketing.md`), social, description links — **not the store** | 960 or 800 px wide, 10 – 15 fps (stepped down per clip until ≤ 4 MB), looping | 0.54 – 3.97 (all ≤ 4) |
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

Size limits checked by the scripts: store clips ≤ 8 MB, trailer ≤ 20 MB and 30–45 s (`references.md` §5), GIF ≤ 4 MB (GitHub README), no near-static stretch ≥ 2 s in any clip,
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

Step 124 (`docs/steps/step_124.md`, `clip_compose.py` docstring): playback 1.35 × the recording, a virtual camera that
eases toward the operation point (cropped from the full-resolution window picture, so zoomed UI stays sharp), popping key
chips with a Hello Yellow press flash and a chip next to the cursor, yellow click pulses, sliding captions, a lockup
intro / outro per clip; the trailer's title card moves (its first frame is still the key visual = the store poster),
clips are joined by push / zoom-through transitions, and the end card animates in (CTA pill
"Free on extensions.blender.org", `content.json` `trailer.cta`). The script fails an output with a near-static run
≥ 2 s or over its size limit.

## Placeholders to fill before publishing

- Trailer end card: the CTA pill says "Free on extensions.blender.org" (`content.json` → `trailer.cta`; the full listing
  URL placeholder is `trailer.download`) — fine once the listing is live; rerun `clip_compose.py` if the text changes.
  Posts / copy: "extensions.blender.org" placeholder (the listing URL comes from the platform).
- `posts.md`: `<listing URL>`, `<YouTube URL>` (source link filled: https://github.com/5hyuns/maya-workflow-kit-for-blender, created private — make it public first).
