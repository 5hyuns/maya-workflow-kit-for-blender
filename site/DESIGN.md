---
name: Maya Workflow Kit (product site)
description: The whole Maya workflow in Blender, in one install. A one-page site built as a piece of Maya 2022's own UI.
colors:
  canvas: "#1e1e1e"
  base: "#2b2b2b"
  panel: "#373737"
  rule: "#444444"
  vp-top: "#889db3"
  vp-bottom: "#0d0d0d"
  text-strong: "#eeeeee"
  text: "#c8c8c8"
  text-muted: "#9a9a9a"
  teal: "#00bcbb"
  teal-hover: "#3fd6d5"
  teal-dim: "#005f61"
  yellow: "#ffff00"
  ink: "#000000"
typography:
  lockup-name:
    fontFamily: "Inter, system-ui, sans-serif"
    fontSize: "clamp(36px, 3.5vw, 56px)"
    fontWeight: 750
    lineHeight: 1
    letterSpacing: "-0.03em"
  lockup-line:
    fontFamily: "Inter, system-ui, sans-serif"
    fontSize: "calc(clamp(36px, 3.5vw, 56px) * 0.66)"
    fontWeight: 600
    lineHeight: 1.15
    letterSpacing: "-0.015em"
  headline:
    fontFamily: "Inter, system-ui, sans-serif"
    fontSize: "clamp(26px, 2.6vw, 38px)"
    fontWeight: 700
    lineHeight: 1.12
    letterSpacing: "-0.02em"
  title:
    fontFamily: "Inter, system-ui, sans-serif"
    fontSize: "19px"
    fontWeight: 650
  tagline:
    fontFamily: "Inter, system-ui, sans-serif"
    fontSize: "clamp(19px, 1.5vw, 22px)"
    fontWeight: 500
    lineHeight: 1.35
  body:
    fontFamily: "Inter, system-ui, sans-serif"
    fontSize: "17px"
    fontWeight: 400
    lineHeight: 1.6
    fontFeature: "\"cv11\", \"ss01\""
  ui-label:
    fontFamily: "Inter, system-ui, sans-serif"
    fontSize: "13px"
    fontWeight: 600
    lineHeight: 1.35
  code:
    fontFamily: "ui-monospace, Cascadia Mono, Consolas, monospace"
    fontSize: "0.92em"
    fontWeight: 500
    lineHeight: 1.4
rounded:
  ui: "3px"
  frame-sm: "4px"
  button: "5px"
  window: "6px"
spacing:
  pad-x: "clamp(20px, 4vw, 64px)"
  row: "12px"
  section: "clamp(56px, 7vw, 96px)"
components:
  button-press:
    backgroundColor: "{colors.yellow}"
    textColor: "{colors.ink}"
    rounded: "{rounded.button}"
    padding: "0 22px"
    height: "48px"
  button-quiet:
    backgroundColor: "{colors.base}"
    textColor: "{colors.text-strong}"
    rounded: "{rounded.button}"
    padding: "0 22px"
    height: "48px"
  shelf-tab:
    backgroundColor: "{colors.base}"
    textColor: "{colors.text}"
    padding: "10px 13px 9px"
  shelf-tab-selected:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.text-strong}"
  menubar-item:
    textColor: "{colors.text}"
    rounded: "{rounded.ui}"
    padding: "6px 10px"
  menubar-item-hover:
    backgroundColor: "{colors.teal-dim}"
    textColor: "{colors.text-strong}"
  toggle-option-pressed:
    backgroundColor: "{colors.teal}"
    textColor: "{colors.ink}"
    rounded: "{rounded.ui}"
    padding: "7px 16px"
  maya-window:
    backgroundColor: "{colors.panel}"
    rounded: "{rounded.window}"
---

# Design System: Maya Workflow Kit (product site)

## Overview

**Creative North Star: "The Maya Shelf"**

The page is a piece of Maya 2022's own interface, not a marketing page about it. Its chrome is Maya's: a sticky main menu bar, a shelf strip of tabs over a viewport, a Channel Box column of attribute rows, an option window for the install steps, Attribute Editor frames with disclosure triangles for the FAQ, and Maya's dotted tear-off line between sections. A Maya artist should recognise the furniture before reading a word.

Density is split on purpose: UI-sized labels (11.5–14 px) in the Maya fragments, large tight lockup type in the hero. Surfaces are Maya's flat greys separated by 1 px rules; colour is almost absent, so the one teal accent and the one yellow press moment carry all the emphasis. Real UI footage (clips, screenshots) is the imagery; nothing is illustrated.

The visual values are inherited from the product's marketing system (`docs/distribution/marketing/style.md`); this file records how they landed in the shipped site.

**Key Characteristics:**
- Maya 2022 greys as tonal layers, 1 px #444 rules as the only dividers.
- Maya logo teal as the single accent; Autodesk Hello Yellow only where the visitor presses (and for keyboard focus).
- One family, Inter, from 11.5 px UI labels to the 56 px lockup.
- Maya chrome devices: shelf tabs, Channel Box rows, option window title bar with the "::::" handle, dotted tear-off rule, disclosure triangles.
- Square-ish corners (3–6 px), soft low shadows only under window fragments and the press button.

## Colors

A near-monochrome Maya grey world with one cyan-teal voice and a single flash of yellow.

### Primary
- **Maya Logo Teal** (`teal`): links, the selected shelf tab's 3 px underline, Channel Box attribute names, step numbers, the FAQ disclosure triangles, the limits list dashes, the pressed Maya | Blender option (with black ink), the lockup's "for Maya users, in Blender" line, and text selection. Brightens to **Lit Teal** (`teal-hover`) on link hover; **Shadow Teal** (`teal-dim`) is the menu bar hover fill (white text on it, 6.4:1). The hero's glow is the deep teal #008b8d at 18 % alpha.

### Secondary
- **Hello Yellow** (`yellow`): the "Download the zip" button (black ink, 19.6:1), the skip link, and the 2 px keyboard focus ring. Nothing else.

### Neutral
- **Canvas** (`canvas`): page background, bottom of every gradient.
- **Maya Base** (`base`): menu bar (96 % alpha), shelf strip, viewport caption, tour band, FAQ frames, quiet button.
- **Maya Panel** (`panel`): window fragments (shelf + viewport block, install option window), selected shelf tab.
- **Rule Grey** (`rule`): every 1 px border and divider; also the scrollbar thumb.
- **Viewport Gradient** (`vp-top` to `vp-bottom`): background behind viewport media, Maya's Alt+B gradient. The closing band uses a darkened version (#3a4654 to canvas).
- **Button Text White** (`text-strong`): headings, the product name, Channel Box values, strong runs.
- **Maya Text** (`text`): body copy and inactive UI text.
- **Muted Text** (`text-muted`): meta lines, captions, credits, footer (5.9:1 on canvas).
- **Ink** (`ink`): text on teal and on yellow only.
- Local UI greys appear only inside Maya-fragment states: #323232 (tab hover), #333 (tab separators), #3a3a3a / #424242 (FAQ header rest / hover), #5a5a5a (dotted tear-off rule), #8a8a8a (handle dots).

### Named Rules
**The One Accent Rule.** Teal is the only hue that marks information. A second accent hue never appears in page chrome; selection colours inside screenshots are the product's, not the page's.

**The Press Moment Rule.** Yellow appears only where something is pressed or focused: the download button, the skip link, the focus ring. Never as a fill for decoration, never on a heading, never with white text.

**The Black Ink Rule.** Text on teal or yellow is #000000, never white.

## Typography

**Display Font:** Inter variable (self-hosted `fonts/InterVariable-latin.woff2`, weights 100–900, with system-ui fallback)
**Body Font:** Inter, same file, features `cv11` and `ss01`
**Label/Mono Font:** ui-monospace / Cascadia Mono / Consolas for code; menu paths use Inter 600 instead

**Character:** One neutral grotesque carries both the dense Maya UI labels and the large lockup, the way Maya's own UI uses one face throughout.

### Hierarchy
- **Lockup name** (750, clamp 36–56 px, line-height 1, -0.03em): "Maya Workflow Kit" in the hero; text-strong.
- **Lockup line** (600, 0.66 × the name, -0.015em): "for Maya users, in Blender", always right under or after the name, always teal.
- **Headline** (700, clamp 26–38 px, 1.12, -0.02em): section h2, balanced wrap. The closing title is the same role at clamp 26–40 px, max 18ch.
- **Title** (650, 19 px): install step h3, prefixed by its teal step number.
- **Tagline** (500, clamp 19–22 px, 1.35): one hero line in text-strong.
- **Body** (400, 17 px / 1.6; 16 px under 760 px): prose, max 66ch (`--measure`), pretty wrap.
- **UI label** (500–600, 12.5–14 px): shelf tabs (12.5), Channel Box rows (13), option window title (13.5), menu bar and captions (14), credits (11.5–12).

### Named Rules
**The Lockup Rule.** The name is one weight and one colour; "Maya" is never set apart. The teal line follows immediately at 0.66 × the name size, in the hero and in the footer (18 / 12 px).

**The Two Densities Rule.** Inside a Maya fragment, type is UI-sized (≤ 14 px) and tight; outside, it is reading-sized. Don't blend the two in one block.

## Layout

Full-bleed bands with a fluid horizontal inset (`pad-x`, 20–64 px). The hero is a two-column grid (36 / 64) with the copy left (max 34rem) and the Maya window fragment right; the Maya | Blender section reverses the weight (40 / 60). Below 1100 px both stack to one column; below 760 px the Channel Box column drops under the viewport, the install steps stack with horizontal rules, the menu bar scrolls sideways and loses its GitHub link.

Section rhythm is clamp 56–96 px vertical padding, with the dotted tear-off rule between the content sections and a 1 px rule band around the tour. Content widths cap at 66ch for prose, 56rem for FAQ frames, 1100 px for the option window and tour video. Media are 16:9. The sticky menu bar is 48 px; anchors scroll with a 64 px offset.

## Elevation & Depth

Depth is mostly tonal: canvas, base and panel greys stack like Maya's UI, separated by 1 px rules. Shadows exist only under objects that sit on the page like windows or a physical button, and they are soft, negative-spread and downward.

### Shadow Vocabulary
- **Window fragment** (`box-shadow: 0 18px 32px -18px rgba(0,0,0,.85), 0 2px 6px rgba(0,0,0,.3)`): the shelf + viewport block.
- **Screenshot frame** (`box-shadow: 0 16px 30px -20px #000`): the Maya | Blender switch frame.
- **Press button rest / lifted** (`0 6px 16px -8px rgba(0,0,0,.7)` / `0 10px 22px -10px rgba(0,0,0,.8)`): the yellow button; lifts 1 px on hover and focus, sinks 1 px on press.

### Named Rules
**The Tonal First Rule.** A new surface gets its depth from the grey it sits on and a 1 px rule. A shadow is added only if it is a window or a press target.

## Shapes

Square-ish, UI-scale corners: 3 px for small controls (menu items, toggle options, FAQ header), 4 px for small frames (toggle track, FAQ frame), 5 px for buttons, 6 px for window fragments and media frames. Every frame clips its content (`overflow: hidden`). Borders are 1 px Rule Grey; the only heavier strokes are the 3 px teal underline of the selected shelf tab and the 2 px yellow focus ring. Recurring silhouettes: the dotted-grid tear-off handle (4 px dot grid, #8a8a8a at 70 %), the right-pointing teal triangle that turns 90 degrees when a frame opens, and the 9 px teal dash before list items.

## Components

### Buttons
Two only, both 48 px tall with 5 px corners and 650 weight 16 px labels.
- **Press:** Hello Yellow fill, black ink, soft shadow; hover/focus lifts 1 px with a deeper shadow, active sinks 1 px (0.25 s, `cubic-bezier(.16, 1, .3, 1)`). Used for the download action only, at most twice per page (hero and close).
- **Quiet:** Maya Base fill, 1 px rule border, text-strong; hover turns the border teal.

### Menu bar
Sticky 48 px Maya main menu bar: Maya Base at 96 % alpha, 1 px bottom rule, 14 px items. Product name left (700), section links as 3 px-cornered items with a Shadow Teal hover fill, the GitHub link pushed right with a rule border.

### Shelf tabs (signature)
A tab strip inside the Maya Base shelf bar, led by the tear-off handle. Tabs are 12.5 px / 500, separated by #333 hairlines; hover lifts to #323232, the selected tab takes the Panel grey and a 3 px teal underline that scales in from the centre (0.35 s). Tabs switch by click, arrow keys and 1–6; the swap dims the viewport media to 25 % with a 6 px blur for 0.3 s.

### Channel Box column
A 17.5rem column right of the viewport: node name (600, text-strong) over a rule, then a two-column grid of rows, attribute names right-aligned in teal 600, values in text-strong, alternate rows tinted white at 2.5 %. Credits sit at the bottom in 11.5 px muted text.

### Option window
The install steps sit in a Panel-grey frame with a Maya Base title bar (handle + 13.5 px title). Steps are three columns divided by vertical rules, each with a teal step number before its title; stacked with horizontal rules on small screens.

### Toggle (Maya | Blender)
A Maya Base track with a rule border and 3 px padding; options are 14 px / 600 muted text, the pressed one teal with black ink, separated by a rule-coloured "|".

### Attribute Editor frames (FAQ)
`details` frames: Maya Base body, rule border, 4 px corners; the summary is a #3a3a3a header bar (hover #424242) with a teal triangle at the left that rotates 90 degrees on open (0.3 s).

## Do's and Don'ts

### Do:
- **Do** build new sections out of Maya chrome (shelf, Channel Box rows, option window, Attribute Editor frame, tear-off rule) before inventing a new container.
- **Do** keep solid dividers 1 px Rule Grey (#444444), section breaks as the 1 px dotted tear-off rule (#5a5a5a), and every corner between 3 and 6 px.
- **Do** put black ink on teal and yellow, and keep yellow to the press moment and keyboard focus.
- **Do** show the product with real UI footage in 16:9 frames, with the media credit next to the media.
- **Do** honour reduced motion: smooth scrolling and every transition switch off.

### Don't:
- **Don't** add a second accent hue to page chrome or style "Maya" apart from the rest of the product name.
- **Don't** use yellow for decoration, headings or large fills, or put white text on teal or yellow.
- **Don't** add shadows to flat bands, cards or text; depth comes from the grey layers.
- **Don't** go above 6 px corners in site chrome (the pill shapes of the marketing images belong to the image system, not to page controls).
