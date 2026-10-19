# Visual system — Allset marketing images (step 122)

Tokens live in `tools/marketing/style.json` (three layers: primitive → semantic → component, the structure of the
ui-ux-pro-max design-system skill); `tools/marketing/compose.py` reads them, so a change there changes every image.
Claude Design was not reachable in this session (connector auth error), so the system was set with that skill and the
kit's own colours. Reference set: `docs/distribution/marketing/references.md` §5.

## Colour

The kit's Maya-like greys (Maya 2022 UI palette measured in `research/maya/colors.json` `ui_palette_qt`, the kit theme
`src/allset/theme/studio_grey.xml`) and **one** accent.

| Token | Value | Use |
|---|---|---|
| `grey-950` / `grey-900` | #1e1e1e / #252525 | canvas gradient (bottom / top) |
| `grey-850` | #2b2b2b | key visual top, surfaces (Maya Base) |
| `grey-800` / `grey-700` | #373737 / #444444 | icon tile, rules (Maya Midlight / Window) |
| `grey-600` | #5c5c5c | the viewport — Maya's factory background (step 120) |
| `grey-500` | #808080 | muted text (brand mark in the band, footers) |
| `grey-200` | #c8c8c8 | caption line (Maya Text) |
| `grey-050` | #eeeeee | titles, product name (Maya ButtonText) |
| **`amber-400`** | **#ffb547** | the accent: title tick, callouts, "for Maya Users", icon item |

The accent is warm so it never reads as a UI state in the shots (Maya / kit selection is white, lead green #43ffa3,
highlight blue #5285a6). WCAG contrast (computed): amber on #252525 8.7:1, #1e1e1e text on amber 9.5:1, #c8c8c8 on #252525 9.2:1.

## Type

Inter (SIL OFL 1.1, `research/marketing_assets/font_inter/`, fetched by `tools/marketing/fetch_assets.py`). One family.

| Role | Weight / size (1920 × 1080) |
|---|---|
| Screen title | SemiBold 56 px |
| Screen line | Regular 28 px |
| Brand mark (band, right) | Medium 22 px, muted |
| Callout label | SemiBold 24 px, on the accent |
| Key visual name "Allset" | Bold 132 px (square 104) |
| "for Maya Users" | Medium 46 px, accent (square 38) |
| Key visual tagline | Regular 34 px (square 30) |
| Footer | Medium 24 px, muted |

Words in images: a title of ≤ 6 words and one line of ≤ 12 words (references.md §5.3). No paragraphs.

## Layout

- Canvas 1920 × 1080, vertical gradient #252525 → #1e1e1e. Margin 144 px left / right (7.5 %), 8 px spacing unit.
- **Title band** = top 162 px: a 6 px amber tick, title and line left-aligned at x = 172, brand "Allset for Maya Users"
  right-aligned. Never over the UI.
- **Shot** = the real 1920 × 1080 Blender window scaled to 1632 × 918 (85 %), radius 10 px, soft shadow (blur 28,
  alpha 150), placed at (144, 162) — it fills the frame below the band to the bottom edge.
- **Callouts**: a 4 px amber rounded box around the UI part (padding 6) + an amber pill label (SemiBold 24, text
  #1e1e1e) joined by a 4 px arrow; label beside the box (left / right / above / below), kept inside the shot. At most
  two per screen; none where the picture explains itself (hotbox, marking menu, pivot menu).
- **Key visual** (1920 × 1080, also the store featured image / og:image): name + "for Maya Users" + tagline + footer on
  the left third; two real screens on the right, turned ~14° (simple perspective, the far edge shorter), back one
  higher and smaller, front one overlapping; a soft amber glow behind them. **Square** (1080 × 1080): text on top, one
  turned screen bleeding off the bottom-right.
- **Icon** (256 × 256): a rounded #373737 tile with a radial marking menu — eight grey items round a white centre, one
  amber item with the gesture line to it. Kit-made, no Maya mark.

## Scenes

- Real Allset session (GUI Blender 4.5, clean sandbox, Maya theme, Material Preview with the world hidden so the
  viewport shows Maya's #5c5c5c), 1920 × 1080 window at this PC's 125 % UI scale (legible when the gallery shows the
  images at half size).
- Licensed models only (`CREDITS.md`): a Poly Haven workbench (table, drill, toolbox, barrel, box, plant), Kenney's
  rigged character, Quaternius' RobotExpressive. Each feature uses the model that fits its workflow (drill =
  modeling / components / pivot, skinned character = rigging / marking menus, walking robot = animation).
- Bones are shown only in the rigging shot; import helpers (empties) are hidden; glTF quaternion channels converted
  to Rotate X / Y / Z so the Channel Box reads like Maya's.
- The Blender logo in the top-left corner is painted over (extensions.blender.org terms 2.2).
