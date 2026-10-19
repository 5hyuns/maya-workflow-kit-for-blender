# Listing media references and the Allset media standard (step 121)

User request (2026-10-19): 「Blender 상위 애드온(인기 많은 것)을 레퍼런스 삼아서 가자. Blender 보면 움직이는 이미지도 들어가던데?」

Fetched 2026-10-20. Every number below comes from a fetched page (URL in the row); "unknown" = not on the page.
Raw HTML, parsed JSON, ffprobe output, thumbnails and contact sheets are in `research/marketing_refs/` (not tracked:
third-party images): `extensions_top.{md,json}`, `superhive_competitors.{md,json}`, `videos_probe.json`,
`collage_extensions.png`, `collage_superhive.png`, `collage_competitors.png`, `thumbs/`, `review/`.
"Hero style" and "text on images" are judgements by eye from the downloaded images.

**Correction of the earlier plan:** `listing.md` part C said "no GIF" as if the store had no moving images. It does:
each extensions.blender.org preview slot takes an **MP4 video** (no GIF, no WebM), and some pages put GIFs (external
links) in the description body. Videos are what the popular third-party listings use.

## 1. Official rules of extensions.blender.org

The public docs pages have no media spec (checked: https://extensions.blender.org/about/ ,
https://developer.blender.org/docs/handbook/extensions/ ,
https://docs.blender.org/manual/en/latest/advanced/extensions/getting_started.html ,
https://developer.blender.org/docs/features/extensions/moderation/canned_responses/ ,
https://extensions.blender.org/terms-of-service/ ). The rules are in the upload form of the site's public source
(`infrastructure/extensions-website`, main @ 8415711, 2026-10-14; the form itself needs a login) and in the moderation
guideline. Base URL of the source: https://projects.blender.org/infrastructure/extensions-website/src/commit/8415711121ffe7a2be0051c5f02cc537169f7d04/

| Item | Rule (quote) | Source |
|---|---|---|
| Icon | "A 256 x 256 PNG icon representing this extension." PNG only; wider / taller than 256 is rejected | `extensions/templates/extensions/manage/update.html`, `extensions/forms.py`, `constants/base.py` |
| Featured image | "A JPEG, PNG or WebP image, at least 1920 x 1080 and with aspect ratio of 16:9." Also the page's `og:image` ("Shown by social networks when this extension is shared") | `update.html`, `extensions/models.py` |
| Previews | "Preview images are displayed in 16:9 ratio. At least one item is required for approval submission." Each slot: "A JPEG, PNG or WebP image, or an MP4 video." (`ALLOWED_PREVIEW_MIMETYPES` = jpg / jpeg / png / webp / video/mp4) | `extensions/templates/extensions/manage/components/add_previews.html`, `constants/base.py`, `extensions/forms.py` |
| Preview captions | `CharField(max_length=255)`, placeholder "Describe the preview"; shown as the gallery item's alt text | `extensions/models.py` (`Preview`) |
| Required before review | featured image, icon and ≥ 1 preview ("Require at least one preview image when requesting a review", "Make feature image and icon required too") | `extensions/forms.py` |
| Number of previews | no cap in the code (formset without `max_num`) | `extensions/forms.py` |
| Preview file size / video length | no limit in the code (the 200 MB `MAX_UPLOAD_SIZE_MB` is the extension zip's form); web-server limit unknown. Accepted in practice (this sample): up to 85.5 MB and 133.4 s, H.264 and HEVC | `files/forms.py`; `research/marketing_refs/videos_probe.json` |
| Video poster | the server takes the frame at `00:00:00.01` as the thumbnail — **the first frame is what visitors see** | `files/utils.py` (`extract_frame`), `files/tasks.py` |
| Thumbnails | 1920 × 1080 and 640 × 360, served as WebP | `constants/base.py` |
| Tagline | max 64 characters | `extensions/models.py`, `files/validators.py` |
| Moderation | "Check the overall quality of the images." / "Make sure there are no heavy image (.gif images in particular) on the image description, making the page massive to load." | https://developer.blender.org/docs/features/extensions/moderation/guidelines/ |

## 2. extensions.blender.org: top add-ons

Sources: downloads sort https://extensions.blender.org/add-ons/?sort_by=-download_count (top 20) and rating sort
https://extensions.blender.org/add-ons/?sort_by=-rating_sortkey (ranks 1–9 not in the top 20), plus references-overlays
(the GIF lead). Previews = gallery items (video / image). Videos: duration, resolution, size (ffprobe on the media URL).

| DL# | Rate# | Add-on | Downloads | Rating | Featured image | Previews (video/img) | Videos (first) | Text on previews | Description | Desc. moving images / links |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | – | [looptools](https://extensions.blender.org/add-ons/looptools/) | 2,264,762 | 5.0 (150) | none | 0 | – | – | 39 w stub | docs link |
| 2 | – | [extra-mesh-objects](https://extensions.blender.org/add-ons/extra-mesh-objects/) | 1,230,197 | 5.0 (31) | none (card = preview 1) | 1 (0/1) | – | none | 30 w stub | docs link |
| 3 | – | [bool-tool](https://extensions.blender.org/add-ons/bool-tool/) | 1,218,274 | 5.0 (64) | logo / tool icons | 3 (0/3) | – | none | 274 w, 2 headings | GitHub, donate |
| 4 | – | [extra-curve-objectes](https://extensions.blender.org/add-ons/extra-curve-objectes/) | 859,892 | 5.0 (23) | none | 0 | – | – | 33 w stub | docs link |
| 5 | – | [print3d-toolbox](https://extensions.blender.org/add-ons/print3d-toolbox/) | 656,684 | 5.0 (53) | photo (printed bunny) | 2 (0/2) | – | none (captions) | 85 w | Stanford bunny named |
| 6 | – | [mmd-tools](https://extensions.blender.org/add-ons/mmd-tools/) | 598,829 | 5.0 (57) | illustration | 1 (1/0) | 24.5 s 1920×1080 1.8 MB | none | 40 w | – |
| 7 | – | [antlandscape](https://extensions.blender.org/add-ons/antlandscape/) | 500,158 | 5.0 (28) | none | 0 | – | – | 31 w stub | docs link |
| 8 | – | [f2](https://extensions.blender.org/add-ons/f2/) | 422,894 | 5.0 (37) | none | 0 | – | – | 36 w stub | docs link |
| 9 | – | [cell-fracture](https://extensions.blender.org/add-ons/cell-fracture/) | 372,467 | 5.0 (16) | none | 0 | – | – | 33 w stub | docs link |
| 10 | – | [archimesh](https://extensions.blender.org/add-ons/archimesh/) | 326,517 | 4.0 (29) | none | 0 | – | – | 35 w stub | docs link |
| 11 | – | [boltfactory](https://extensions.blender.org/add-ons/boltfactory/) | 319,234 | 5.0 (26) | render | 2 (0/2) | – | none | 530 w, 6 headings | docs |
| 12 | – | [vrm](https://extensions.blender.org/add-ons/vrm/) | 317,630 | 5.0 (21) | UI screenshot | 1 (0/1) | – | none | 146 w, 4 headings | 9 GIF refs (own site) |
| 13 | – | [auto-mirror](https://extensions.blender.org/add-ons/auto-mirror/) | 309,231 | 5.0 (11) | none | 0 | – | – | 34 w stub | docs link |
| 14 | 2 | [mio3-uv](https://extensions.blender.org/add-ons/mio3-uv/) | 306,516 | 5.0 (130) | wordmark + tag grid | 2 (1/1) | 30.7 s 1280×720 15.4 MB | corner title | 659 w, 16 headings | docs site |
| 15 | 11 | [ucupaint](https://extensions.blender.org/add-ons/ucupaint/) | 304,414 | 5.0 (146) | wordmark on red | 10 (6/4) | 9.6–40 s, 720×720–1024×750, ≤ 1.6 MB | none (captions) | 310 w, 5 headings | artists credited in captions |
| 16 | – | [sapling-tree-gen](https://extensions.blender.org/add-ons/sapling-tree-gen/) | 286,502 | 4.0 (20) | none | 0 | – | – | 34 w stub | docs link |
| 17 | – | [measureit](https://extensions.blender.org/add-ons/measureit/) | 283,389 | 5.0 (26) | full UI screenshot | 1 (0/1) | – | none | 32 w stub | docs link |
| 18 | – | [copy-attributes-menu](https://extensions.blender.org/add-ons/copy-attributes-menu/) | 277,699 | 5.0 (26) | none | 0 | – | – | 34 w stub | docs link |
| 19 | – | [io-scene-max](https://extensions.blender.org/add-ons/io-scene-max/) | 260,703 | 5.0 (94) | 3ds Max logo over file browser | 3 (0/3) | – | none | 127 w | GitHub |
| 20 | 7 | [node-arrange](https://extensions.blender.org/add-ons/node-arrange/) | 252,679 | 5.0 (97) | before / after + arrow | 3 (0/3) | – | none | 58 w | – |
| – | 1 | [simple-deform-helper](https://extensions.blender.org/add-ons/simple-deform-helper/) | 110,018 | 5.0 (175) | text-heavy banner | 11 (11/0) | 61.6 s 2006×1080 48.2 MB; 23.3 s, 17.5 s 1336×720 6.1 MB … | lower-third title per video | 2059 w, 52 headings | 4 animated WebP (≈ 9 MB each, GitHub) |
| – | 3 | [placehelper](https://extensions.blender.org/add-ons/placehelper/) | 49,280 | 5.0 (107) | text-heavy banner | 8 (8/0) | 56.3 s, 15.9 s, 18.6 s at 2560×1720 | title bar + one subtitle line | 1022 w, 5 headings | – |
| – | 4 | [nd](https://extensions.blender.org/add-ons/nd/) | 111,208 | 5.0 (139) | logo on dark | 6 (0/6) | – | headline + one line per slide | 128 w | YouTube, docs |
| – | 5 | [synchronize-workspaces](https://extensions.blender.org/add-ons/synchronize-workspaces/) | 30,631 | 5.0 (84) | UI composite + logo | 2 (1/1) | 50.8 s 1280×720 6.1 MB | one title sentence | 95 w | Superhive link |
| – | 6 | [threemf-io](https://extensions.blender.org/add-ons/threemf-io/) | 107,369 | 5.0 (78) | text banner | 2 (1/1) | 53.2 s 1920×1080 27.2 MB | none | 529 w, 13 headings | credits section |
| – | 9 | [brushstroke-tools](https://extensions.blender.org/add-ons/brushstroke-tools/) | 129,211 | 5.0 (77) | render art + title lettering | 4 (1/3) | 123.9 s 1920×1080 85.5 MB | title on featured only | 586 w, 6 headings | Blender Studio assets credited, YouTube |
| – | – | [references-overlays](https://extensions.blender.org/add-ons/references-overlays/) | 34,397 | 5.0 (28) | title text over images | 4 (0/4) | – | title / one caption | 283 w, 9 headings | 5 GIFs (imgur 3.8–8.3 MB, one 61.7 MB) |

Patterns (27 add-ons):
- The download leaders are mostly former bundled add-ons: 9 of the top 20 have no media at all and a ~35-word stub —
  their downloads come from Blender's history, not the listing. **The useful references are the top-rated third-party
  listings.**
- Listings with media: 18/27. With ≥ 1 video: 8/18; video-only galleries: 3 (mmd-tools, placehelper 8, simple-deform-helper
  11). Top-rated additions: 5/6 have video.
- Preview count: median 2.5, max 11. Videos (30 probed): duration median 26.6 s (9.6–133.4 s), size median 6.3 MB (max
  85.5 MB), 25 H.264 / 5 HEVC.
- Featured image (18): text banner / title lettering 5, logo / wordmark 4, UI screenshot or composite 6, render / photo 3.
- Text on previews: mostly none; when there is any it is a title or one sentence (lower thirds, header bars, headline +
  one line). No paragraphs. Captions carry the explanation: 13/18.
- Description: median 210 words (30–2059); top-rated third-party ones 600–2000 words with headings and lists.
- Moving images in the description: 3/27 (references-overlays GIFs, vrm GIF refs, simple-deform-helper animated WebP),
  all hosted elsewhere; never in the gallery (GIF isn't accepted there). YouTube links: 2/27.
- Third-party art credited: 3/27 (ucupaint captions, brushstroke-tools, print3d-toolbox).

## 3. Superhive (ex Blender Market) bestsellers

Source: "Most Sales" sort https://superhivemarket.com/products?sort_sales=desc (page 1; the top 10 are all add-ons).
Video lengths = YouTube `lengthSeconds`.

| # | Product | Sales | Rating | Gallery (items / video / GIF) | Video (slot, length) | Hero image | Text on hero | Description | Moving media in description |
|---|---|---|---|---|---|---|---|---|---|
| 1 | [Auto-Rig Pro](https://superhivemarket.com/products/auto-rig-pro) | 70300+ | 5 (449) | 10 / 1 / 0 | slot 2, 320 s | title card + mascot | name + 3-word tagline | 1200 w, 15 headings | 24 GIFs |
| 2 | [Hard Ops / Boxcutter Bundle](https://superhivemarket.com/products/hard-ops--boxcutter-ultimate-bundle) | 48300+ | 5 (138) | 4 / 1 / 2 | slot 2, 29719 s (stream) | render + small logo | logo | 1389 w, 21 headings | 10 GIFs + 7 YouTube |
| 3 | [MACHIN3tools](https://superhivemarket.com/products/machin3tools) | 36300+ | 5 (131) | 10 / 1 / 0 | slot 2, 559 s | render + wordmark | wordmark + version | 278 w, 9 headings | 8 YouTube |
| 4 | [botaniq Trees](https://superhivemarket.com/products/botaniq-trees) | 31100+ | 5 (155) | 18 / 1 / 0 | slot 2, 84 s | render + logo + sale ribbon | logo + category + "30% OFF" | 567 w, 27 headings | 1 YouTube |
| 5 | [MESHmachine](https://superhivemarket.com/products/meshmachine) | 24000+ | 5 (110) | 13 / 1 / 0 | slot 2, 330 s | render + wordmark | wordmark + version | external iframe (unknown) | unknown |
| 6 | [UVPackmaster](https://superhivemarket.com/products/uvpackmaster) | 19900+ | 5 (89) | 24 / 1 / 7 | slot 2, 134 s | logo + result tiles + slogan | headline + subhead | 394 w, 12 headings | 7 GIFs (gallery) |
| 7 | [FLIP Fluids](https://superhivemarket.com/products/flipfluids) | 18800+ | 5 (106) | 16 / 1 / 0 | slot 2, 75 s | render + logo | logo + "ADDON FOR BLENDER" | 2267 w, 22 headings | 13 looping muted mp4 |
| 8 | [Poly Haven Asset Browser](https://superhivemarket.com/products/poly-haven-asset-browser) | 18700+ | 5 (54) | 8 / 0 / 0 | none | render collage | headline + 2 claims | 1968 w, 51 headings | 3 mp4 |
| 9 | [Simply Cloth](https://superhivemarket.com/products/simply-cloth) | 18700+ | 5 (187) | 10 / 1 / 0 | slot 2, 3072 s | title + result strip | title + author | 1963 w | 5 YouTube |
| 10 | [SimpleBake](https://superhivemarket.com/products/simplebake---simple-pbr-and-other-baking-in-blender-2) | 18200+ | 5 (253) | 2 / 1 / 0 | slot 2, 8086 s | illustration + logo | logo + "for Blender" | 1789 w, 16 headings | 1 GIF |

Patterns: **9/10 have a video, always gallery slot 2 after a still hero**; lengths 75–29719 s (median 330 s; only 3
under 3 min — the long ones are overviews / streams). 6/10 add moving images in the description or gallery (GIFs or
looping muted mp4). Hero: 7/10 render art + logo, 0/10 a plain UI screenshot; 10/10 carry the name, 9/10 one short line,
0/10 paragraphs. Gallery median 10 (2–24). Description median ≈ 1300 words, 9/10 headings + bullets, 8/10 docs links.

## 4. Competitors (Maya transition, marking / pie menus, keymaps)

| Product | Store | Price | Sales / downloads | Rating | Gallery (items / video) | Hero | Text on hero | "For Maya users" wording | Shows first |
|---|---|---|---|---|---|---|---|---|---|
| [Maya Config Pro V2.5](https://superhivemarket.com/products/maya-config-pro) | Superhive | $50 | 50+ | none shown | 8 / YouTube slot 2, 104 s | 3D Maya-like "M PRO" logo + UI strips | 8-line feature list | "for 3D artists migrating from Maya to Blender"; "helps Maya users quickly … adapt" | logo + add-on list |
| [Maya Config Lite](https://superhivemarket.com/products/maya-config-lite) | Superhive | $12 | 30+ | none shown | 6 / YouTube slot 2, 537 s | "M LITE" logo | headline + 1 line | "makes transitioning to Blender from Maya easy! … a Maya-like feel" | logo |
| [Maya Config Addon (discontinued)](https://formaffinity.gumroad.com/l/FKhQL) | Gumroad | PWYW $0 | not shown | 4.9 (752) | 1 / none | announcement banner | 3 lines | "Full Maya Config Addon with Hotkeys, Marking Menu, Quad Menu …" | discontinuation notice |
| [Maya Config Pro (Gumroad, unpublished)](https://formaffinity.gumroad.com/l/wDpgH) | Gumroad | $50 | not shown | 4.8 (65) | 4 / cover 1 = YouTube, 118 s | (video first) | – | "The Fastest way to Transition from Maya to Blender" | trailer |
| [Maya Shelf & Navigation](https://superhivemarket.com/products/maya-shelf--navigation) | Superhive | $8 | 100+ | 4 (5) | 1 / none | text logo (Maya-like M) | name | "facilitate the transition from Maya to Blender for Maya users" | logo, 8 GIFs in description |
| [Pie Menu Editor](https://superhivemarket.com/products/pie-menu-editor) | Superhive | $16 | 2400+ | 5 (63) | 6 / YouTube slot 2, 395 s (review) | UI collage + logo | logo | none | UI collage |
| [MARKING MENUS](https://superhivemarket.com/products/marking-menus) | Superhive | $10 | 20+ | none shown | 4 / none | blurred UI + title | headline | Alias, not Maya | title card |
| [Keymapper](https://superhivemarket.com/products/keymapper) | Superhive | $9.74 | 60+ | 5 (1) | 6 / none | pitch + UI | headline + 3 bullets | none | UI + pitch |
| [EMC Tools](https://relativitytheory.gumroad.com/l/emctools) | Gumroad | $5 | not shown | 4.6 (5) | 8 / none | line-art logo | none | not on the page | logo |
| [Origin Move like Maya](https://extensions.blender.org/add-ons/origin-move-like-maya/) | extensions | free | 10,033 dl | 13 reviews | 5 / mp4 27.0 s | title + gizmo | headline | "… gizmo like maya" | title card |
| [Maya Pivot](https://extensions.blender.org/add-ons/maya-pivot/) | extensions | free | 15,863 dl | 3 reviews | 2 / mp4 9.97 s | UI + "Maya-like 3D Cursor" + M-style icon | headline | "Implements a Maya-like pivot system in Blender" | UI + headline |

Patterns: 5/10 heroes imitate a Maya "M" logo; 3/10 show the real Blender UI; 5/10 have a video. Wording in the 7
Maya-specific pages: "Maya-like" 6/7, "Maya users" 3/7, "transition" 3/7, "migrating from Maya" 1/7. The paid Maya
transition products sell little (30+–100+); the largest Maya-transition audience is the free, discontinued Gumroad
Maya Config Addon (752 ratings). No other complete "Blender works like Maya" product was found besides the Form
Affinity family — none of them shows the whole Maya workflow (Channel Box, hotbox, Maya menus) in its first media.

## 5. The Allset media standard (delegated, from §1–§4)

1. **Featured image** (1920 × 1080 PNG, also the social card): the real Allset screen (Maya layout, Maya theme, Maya
   factory background #5c5c5c, `key_batch3.reset_background()`) as the picture, with the product name and **one** short
   line on a band — no paragraphs, no feature list (bestsellers 9/10 name + one line, 0/10 paragraphs). No Maya-like
   "M" logo and no Maya screenshot (decision 12 / trademark; 5/10 competitors do the M — we don't need it: our proof is
   the whole Maya UI working inside Blender, which no competitor shows first).
2. **Gallery = 10 items, 16:9, 1920 × 1080** (top-rated extensions max 11, Superhive median 10):
   - **#1 trailer MP4, 30–45 s** (extensions videos median 26.6 s; Superhive trailers 75–134 s are overviews we split
     into clips): silent, H.264, 30 fps, ≤ 20 MB, lower-third titles. **Its first frame is a title card** (the server's
     poster = frame at 0.01 s).
   - **#2–#7 six feature clips, MP4, 6–15 s each**, one feature per clip, ≤ 8 MB each (≈ the median 6.3 MB), a
     lower-third title on the first second, no audio needed. Topics follow the listing's six workflow groups (Navigate &
     Select, Hotbox & Marking Menus, Channel Box & Attribute Editor, Menu Sets & Shelves, Maya concepts, Option windows).
   - **#8–#10 three stills** (PNG/WebP): the screen with a headline (≤ 6 words) + at most one line (≤ 12 words) —
     the nd / UVPackmaster pattern: before / after "Blender ↔ Maya mode", the switch back to Blender, Blender 4.5–5.2.
   - **Every item gets a caption** (≤ 255 chars, the alt text; 13/18 extensions listings use them).
3. **English text in images**: titles only — headline ≤ 6 words, one optional line ≤ 12 words, set in one sans font,
   placed in a band (lower third / top bar), never over the part of the UI the clip demonstrates.
4. **Description** (`listing.md` part B): keep the structured ≈ 1,000-word form (top-rated third party 600–2000 words,
   Superhive median ≈ 1300; headings + bullets). **No GIFs in the extensions.blender.org description** (moderation:
   "no heavy image (.gif images in particular)"); GIFs go to the GitHub README / social posts (step 123), ≤ 5 MB each.
5. **Credits**: every scene is made in Blender by the kit (`allset.create` primitives, kit materials) → no third-party
   art to credit; captions say nothing about models. Maya wording follows the competitors' clearest form and our
   trademark notice: "for Maya users", "Maya-style", "works like Maya" (describing compatibility), never "Maya" as a
   product name.
6. **Order on the page**: featured image → trailer → clips in the B-section order → stills.

## 6. Next-step instructions (steps 122 and 123)

Both follow §5. Reference only (do not reuse as is): the aborted 10-19 attempt in `git stash list`
("step118 partial marketing (aborted by user, …)"): untracked files `tools/marketing/{compose,content,make_marketing,
shots}.py` — read with `git show 'stash@{0}^3':tools/marketing/shots.py`. They grabbed shots in a GUI session and
composited text with Pillow; take the session-driving ideas, not the layout (it predates this standard).

**Step 122 — copy, key visual, captioned stills** (writes `docs/distribution/marketing/copy.md`, `style.md`):
1. `copy.md`: tagline (≤ 64 chars, form field), featured-image line, a headline + one line per gallery item (§5.2,
   word limits §5.3), the 10 captions (≤ 255 chars), the README / social one-liners. English, plain, Maya terms as Maya
   users say them (Channel Box, hotbox, marking menu, shelf, option box). No claims the tests don't back.
2. `style.md`: font (one sans, sizes for 1920 × 1080 headline / line / lower third), band colours taken from the Maya theme
   (`src/allset/theme/studio_grey.xml`: header / panel greys, Maya selection highlight), margins, safe area (keep the demonstrated UI clear), logo use
   (Allset icon only).
3. Key visual = featured image (§5.1) and the three stills (§5.2 #8–#10): rendered by a tool in `tools/marketing/`
   from GUI shots of the real UI (`tools/listing_shots.py` session: Maya theme, `reset_background()`, UI scale 1.0 at
   1920 × 1080), text composited with Pillow from `copy.md`. Check every image by eye; ΔE not needed, but the viewport
   must read as Maya's #5c5c5c.
4. Update `listing.md` part C (file names, captions, order) and `tools/make_listing_media.py`.

**Step 123 — clips and marketing kit** (follows `copy.md` / `style.md`):
1. Six feature clips (§5.2 #2–#7, 6–15 s) + one 30–45 s trailer (#1, first frame = title card) recorded from a GUI
   Blender driven by event simulation (`--enable-event-simulate`, `tests/gui/sim.py` helpers) or input replay; frames
   via `screen.screenshot` per tick or Blender's own viewport render, encoded with ffmpeg (H.264, yuv420p, 30 fps,
   1920 × 1080, `-movflags +faststart`), titles burnt in from `copy.md`.
2. Size check (≤ 8 MB clip, ≤ 20 MB trailer), first-frame check (poster), look at every clip.
3. GIF versions of the clips for the GitHub README / social (≤ 5 MB, ≤ 960 px wide), not for the extensions
   description.
4. Kit folder `docs/distribution/marketing/kit/` (featured, stills, clips, GIFs, copy.md excerpt, icon) + `listing.md`
   part C upload table (slot order, captions).
