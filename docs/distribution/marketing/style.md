# Visual system — Allset marketing images (steps 122, 124)

Tokens live in `tools/marketing/style.json` (three layers: primitive → semantic → component, the structure of the
ui-ux-pro-max design-system skill); `tools/marketing/compose.py` reads them, so a change there changes every image,
clip and kit file. Step 124 reworked colour, lockup and motion after the impeccable critique
(`design_review.md`). Reference set: `references.md` §5.

## Colour

Maya greys for the surfaces, **Maya logo teal** as the one brand accent, Autodesk's brand colours only where an action
happens. Step 122's amber #ffb547 is gone: it sat 15.5 ΔE00 from Blender's orange (#e87d0d) next to Blender-orange
glyphs in every shot, so the brand read as "Blender add-on" (user feedback 10-20, critique P1).

| Token | Value | Use |
|---|---|---|
| `grey-950` / `grey-900` | #1e1e1e / #252525 | canvas gradient (bottom / top) |
| `grey-850` | #2b2b2b | key visual top, surfaces (Maya Base) |
| `grey-800` / `grey-700` | #373737 / #444444 | icon tile, rules (Maya Midlight / Window) |
| `grey-600` | #5c5c5c | the viewport — Maya's factory background (step 120) |
| `grey-500` | #808080 | muted text (footers) |
| `grey-200` | #c8c8c8 | caption line, brand name in the band (Maya Text) |
| `grey-050` | #eeeeee | titles, "Allset" (Maya ButtonText) |
| **`teal-500`** = `accent` | **#00bcbb** | "for Maya Users", title tick, callouts, chips, icon item, glow |
| `teal-600` = `accent-strong` | #149b9a | secondary teal (pressed / small marks) |
| `teal-800` = `accent-deep` | #008b8d | background glow behind the screens |
| `adsk-yellow` = `highlight` | #ffff00 | **action moments only**: click pulse, key-press flash, the CTA pill |
| `adsk-black` = `on-accent` / `on-highlight` / `outline` | #000000 | text on teal / yellow, the 2 px edge round callouts |

Selection colours in the shots stay what they are (kit Maya theme: selected white, lead green #43ffa3, highlight blue
#5285a6) — the teal is none of them (ΔE00 26.3 vs #43ffa3, 23.1 vs #5285a6, 49.7 vs Blender orange #e87d0d; Hello Yellow 41.3), so a callout never reads as a UI state.

### Where the values come from (colour values only)

- **Maya logo teal** — pixels of this PC's Maya 2022 install, measured with Pillow (`tmp/color124/px.py`, px2.py;
  saturated opaque pixels, sorted by brightness). Every sample is hue 180°:
  - `icons/MayaEDUStartupImage.png` (startup image): most frequent bright bins #00b8b8 / #00bcbc, p50 #009c9e,
    p10 #007777 → `teal-500` #00bcbb (the bright face), `teal-800` #008b8d (the shade).
  - `icons/mayaico.png`: most frequent #149898, p50 #138b8b → `teal-600` #149b9a.
  - `bin/maya.exe` icon (32 px, extracted with System.Drawing): p50 #00a9a9, p90 #4babae — same hue.
  - `icons/hsMaya.png`: #006464 – #007878 (dark face).
- **Autodesk brand** — <https://brand.autodesk.com/brand-system/color> (read 2026-10-20): primary Autodesk Black #000000,
  Autodesk White #FFFFFF, **Hello Yellow #FFFF00** ("a highlight for emphasis", not on white); secondary Warm Slate
  #D5D5CB, Slate #666666; tertiary Dawn / Dusk / Twilight / Morning for functional cues only. We take Hello Yellow (as
  their guide uses it: a highlight) and Black (ink on the accents). No Autodesk White pairing with yellow.

### Trademark note (delegated)

- Only **colour values** are used. No Maya or Autodesk logo, M symbol, icon, splash image or wordmark appears in any
  file; the icons / splash were read for pixel values only and are not in the repository.
- Every material keeps the notice "not affiliated with or endorsed by Autodesk" (listing.md B, README_marketing.md,
  posts.md, CREDITS.md) and the "for Maya Users" referential form with Allset first (Autodesk trademark guidelines:
  a third-party name may say it is *for* an Autodesk product, it may not lead with it).
- **Fallback palette `maya-ui`** (in `style.json`, `ALLSET_MARKETING_PALETTE=maya-ui python tools/make_listing_media.py`
  and `tools/marketing/make_clips.py --no-record` regenerate everything): if a store review reads the logo teal as an
  implied affiliation, switch to Maya 2022's **UI** colours only — accent `blue-300` #8fb7d3 (light tint of Maya's
  highlight blue #5285a6, `research/maya/colors.json`), highlight `green-400` #43ffa3 (Maya lead selection), ink
  black. Nothing else changes.

### Contrast (WCAG 2.x, computed)

| Pair | Ratio | Use |
|---|---|---|
| teal #00bcbb on #252525 / #1e1e1e / #2b2b2b | 6.50 / 7.07 / 6.01 | "for Maya Users", tick (AA, AAA ≥ 18 pt) |
| black on teal | 8.91 | chips, callout labels (AAA) |
| black on Hello Yellow | 19.56 | CTA pill, flashing chip |
| teal on viewport #5c5c5c | 2.84 | callout strokes over the UI → 2 px black edge each side (edge ≥ 3:1 both ways) |
| #eeeeee / #c8c8c8 on #252525 | 13.21 / 9.16 | titles / caption lines |
| #808080 on #252525 | 3.88 | footers only (≥ 24 px, large text AA) |
| fallback: #8fb7d3 on #252525, black on #8fb7d3, black on #43ffa3 | 7.21 / 9.88 / 16.07 | `maya-ui` palette |

## Type

Inter (SIL OFL 1.1, `research/marketing_assets/font_inter/`, fetched by `tools/marketing/fetch_assets.py`). One family.

### Lockup (step 124)

"Allset" Bold N px + "for Maya Users" SemiBold **0.66 N** (`component.lockup.for_ratio`) in teal, drawn only by
`compose.lockup()` so every format uses the same rule:

- **Two lines** (key visuals, kit cards, trailer end card): one left edge, "for Maya Users" right under the name. Its
  cap height is 66 % of the name's (measured ink: name 88 px / line 77 px at N = 120 — the descender of "y" makes the
  ink taller), its width is 1.7 × the name's, so the two read as one unit and "for Maya Users" is legible at gallery
  size. Step 122 had 132 / 46 px (ink ratio 2.2 – 2.9).
- **One line** (title band brand mark, YouTube thumbnail, Reddit before / after, clip band): same sizes on one
  baseline, gap 0.3 N.
- Allset always comes first (brand), "for Maya Users" always the teal part.

| Role | Weight / size (1920 × 1080) |
|---|---|
| Screen title | SemiBold 56 px |
| Screen line | Regular 28 px |
| Brand mark (band, right) | one-line lockup, N = 26 (Allset #c8c8c8, for Maya Users teal) |
| Callout label | SemiBold 24 px, black on teal |
| Key visual lockup | N = 120 (square 100) |
| Key visual tagline | Regular 34 px (square 30) |
| Footer | Medium 24 px, muted |

Words in images: a title of ≤ 6 words and one line of ≤ 12 words (references.md §5.3). No paragraphs.

## Layout

- Canvas 1920 × 1080, vertical gradient #252525 → #1e1e1e. Margin 144 px left / right (7.5 %), 8 px spacing unit.
- **Title band** = top 162 px: a 6 px teal tick, title and line left-aligned at x = 172, one-line lockup right-aligned.
  Never over the UI.
- **Shot** = the real 1920 × 1080 Blender window scaled to 1632 × 918 (85 %), radius 10 px, soft shadow (blur 28,
  alpha 150), placed at (144, 162).
- **Callouts**: a 4 px teal rounded box with a 2 px black edge on both sides (padding 6) + a teal pill label
  (SemiBold 24, black) joined by a 4 px arrow (black-edged); at most two per screen.
- **Key visual** (1920 × 1080, also the store featured image / og:image): lockup + tagline + footer on the left third;
  two real screens on the right, turned ~14°; a soft deep-teal glow behind them. **Square** (1080 × 1080): text on top,
  one turned screen bleeding off the bottom-right.
- **Icon** (256 × 256): a rounded #373737 tile with a radial marking menu — eight grey items round a white centre, one
  teal item with the gesture line to it. Kit-made, no Maya mark.
- **Kit cards** reuse the same lockup; on the Reddit before / after only the Maya side carries the accent (teal frame
  + filled pill), the Blender side is a grey outline pill.

## Motion (clips, GIF, trailer — step 124)

`tools/marketing/clip_compose.py` (details in its docstring):

- Speed ≈ 1.35 × the recorded time (`content.json` `speed`), a caption still stays ≥ 1.2 s.
- A virtual camera (Ken Burns) eases in toward the operation point (cursor / clicks, looked ahead and smoothed) and
  back out to the whole window when the action spans it; cursor and pulses follow the camera.
- Key chips pop in (scale + fade), the pressed key flashes Hello Yellow; clicks pulse a yellow ring; captions slide.
- Per clip a short lockup intro and outro; trailer = moving key-visual title card (its first frame = the poster =
  the key visual), push transitions, animated end card with the yellow CTA pill.
- No near-static stretch ≥ 2 s (mean frame difference < 0.5 / 255), checked by the script. GIF ≤ 4 MB (GitHub README).

## Scenes

- Real Allset session (GUI Blender 4.5, clean sandbox, Maya theme, Material Preview with the world hidden so the
  viewport shows Maya's #5c5c5c), 1920 × 1080 window at this PC's 125 % UI scale.
- Licensed models only (`CREDITS.md`): a Poly Haven workbench, Kenney's rigged character, Quaternius' RobotExpressive.
- Bones are shown only in the rigging shot; import helpers (empties) are hidden; glTF quaternion channels converted
  to Rotate X / Y / Z so the Channel Box reads like Maya's.
- The Blender logo in the top-left corner is painted over (extensions.blender.org terms 2.2).
