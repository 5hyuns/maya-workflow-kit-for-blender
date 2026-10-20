# Design review — impeccable critique of the step 122/123 marketing set (step 124)

Run 2026-10-20 with the impeccable skill (`/impeccable critique docs/distribution/marketing`), then fixed with the
colorize → typeset → layout → animate → polish passes listed at the end. User feedback that triggered it (10-20):
the accent read as Blender orange, "Allset" was much bigger than "for Maya Users", the videos were static.

> Step 125: the product is now **Maya Workflow Kit** with the line "for Maya users, in Blender" (user decision,
> `docs/user_decisions.md` 12 revision). This review is kept as written for the step 124 name "Allset for Maya Users";
> the 0.66 lockup rule carries over (`style.md`).

Method: dual-agent, as the skill requires — Assessment A (design review, a sub-agent that saw only the committed
HEAD 5173b5c assets and the request) and Assessment B (detector + mechanical measures, a separate sub-agent), then
synthesis here. The impeccable context step found no PRODUCT.md / DESIGN.md (the target is raster / video, not a web
surface); the brief, `style.md` and `copy.md` were used as context. Questions to the user were skipped: the user
delegated every decision for this step (`delegated`).

## Detector (Assessment B)

`impeccable detect --json docs/distribution/marketing` → exit 0, `[]`. **Nothing scanned**, not "passed": the folder
holds PNG / MP4 / GIF / Markdown and no markup (positive control: a scratch HTML page fired `side-tab` and
`gradient-text`; Markdown is not scanned). No browser overlay (no web page). The mechanical measures below replace it.

## Design health (Nielsen, Persuade mode; 7 and 10 n/a)

| # | Heuristic | Score | Key issue |
|---|---|---|---|
| 1 | Visibility of system status | 3 | key chips sit bottom-right, far from the action |
| 2 | Match system / real world | 3 | Maya's words and layout; the amber brand points at Blender |
| 3 | User control and freedom | 3 | the switch story is clear |
| 4 | Consistency and standards | 2 | "persp" drawn twice (07, 08), cut welcome text (10), caption "keyed channels in red" over green AE fields (03) |
| 5 | Error prevention | 3 | "nothing changes until you choose" early |
| 6 | Recognition over recall | 3 | the hotbox shot has no anchor |
| 7 | Flexibility and efficiency | n/a | marketing surface |
| 8 | Aesthetic and minimalist | 2 | the feature is 3–8 % of a full-UI frame; generic glow / tilt |
| 9 | Error recovery | 3 | "click Blender, everything comes back" |
| 10 | Help and documentation | n/a | marketing surface |
| **Total** | | **22 / 32** | acceptable, edge of good |

**Design specificity: half-specific.** The shots are unmistakably Maya (menu bar, factory shelves, Channel Box,
hotbox, persp/top/front/side, lead green); the brand layer was generic and its only colour said "Blender".

## Measured (Assessment B, HEAD)

| Check | Result |
|---|---|
| Accent #ffb547 vs Blender orange #e87d0d / #f5792a (ΔE00) | **15.5 / 18.7** — same orange family (hue 12–20° apart; the two Blender oranges are 5.9 apart) |
| Lockup cap height "Allset" : "for Maya Users" | **2.7 – 3.0 ×** (key visual 96 / 34 px), ink coverage 4.3 × |
| Contrast | text pairs ≥ 8 : 1; #808080 footers 3.6 – 4.2 (large text only); amber stroke on the #5c5c5c viewport 3.8 |
| Near-static frames (mean diff < 0.5/255) | clips 81 – 98 %; trailer 87 %, stretches ≥ 2 s at 0 s (2.7 s title card), 30.8 s (2.3 s), 35.1 s (3.7 s end card); 07_switch 2.3 s |
| GIF size | 04_navigation **4.68 MB** (> 4 MB for the README); others 0.98 – 3.73 MB |
| MP4 | H.264 High yuv420p 30 fps, 0.39 – 1.24 MB clips, trailer 3.79 MB / 38.8 s — within store limits |

## Priority issues and what step 124 did

| # | Sev | Issue (A + B agree) | Fix in step 124 | Pass |
|---|---|---|---|---|
| 1 | P1 | Accent amber reads as Blender orange; Maya / Blender chips in the before-after card share it | Maya logo teal #00bcbb (pixels of the Maya 2022 icons, hue 180°) as the one accent, Autodesk Hello Yellow #ffff00 only for action moments, Autodesk Black ink; Blender side of the before-after = grey outline pill; fallback palette `maya-ui` for a store objection (`style.md`) | colorize |
| 2 | P1 | "Allset" ≈ 3 × "for Maya Users"; the line that sells is a caption | one lockup rule everywhere (`compose.lockup`): "for Maya Users" SemiBold at 0.66 × the name, two lines on one edge or one line on one baseline; also the band brand mark, YouTube, Reddit, clip band, end card | typeset |
| 3 | P1 | Videos static and slow: fixed full-UI framing, plain dissolves, static title / end cards, chips far from the action | 1.35 × speed, Ken Burns camera toward the operation point, popping chips + chip at the cursor, yellow click pulse, caption slide, lockup intro / outro, moving title card (first frame = poster), push transitions, animated end card; script FAILs a static run ≥ 2 s; GIF ≤ 4 MB | animate |
| 4 | P2 | Broken details: "persp" twice in pose / paint shots (07, 08, rigging clip), welcome dialog body cut ("the Maya colou…") | kit bugs fixed in `src/` (`ui/view_furniture.py` hides the asset shelf header strip that kept stale pixels with Region Overlap off; `welcome.py` wraps by measured width) + tests; shots and the rigging clip re-recorded | polish |
| 5 | P2 | Hotbox hero not legible at thumbnail size (01, YouTube thumbnail) | **left** (see below) | layout |
| 6 | P3 | 05 and 09 are near-identical drill frames; back window of the key visual too keystoned to read | **left** | layout |

Also fixed in the polish pass: callout strokes get a 2 px black edge (teal on the #5c5c5c viewport is 2.8 : 1 alone),
the Time Slider callout arrow no longer covers the camera label (07, callout `at`), the switch label no longer covers
the Outliner's Cube row (10), the band brand mark is #c8c8c8 + teal instead of #808080, the end card's yellow glow is a
small halo (a wide one mixed with the teal into olive).

## Result after the fixes (measured)

| Check | Before | After |
|---|---|---|
| Accent ΔE00 vs Blender orange #e87d0d | 15.5 | 49.7 (teal), 41.3 (Hello Yellow) |
| Lockup cap height Allset : for Maya Users | 2.7 – 3.0 × | 1.5 × (for = 0.66 × the name size) |
| Longest near-static run, clips / trailer | 2.27 s / 3.70 s | ≤ 1.13 s / 0.70 s |
| Clip length (speed 1.35 ×) | 6.1 – 8.9 s | 5.6 – 7.6 s; trailer 38.8 → 33.5 s |
| Largest GIF | 4.68 MB | 3.97 MB (all ≤ 4) |
| "persp" drawn twice / welcome text cut | yes | no (kit fixed, shots and rigging clip re-recorded) |

## Left (not in this step's scope)

- 03: the caption says "keyed channels in red" but the AE draws Blender's green (animated, not on a key) fields — a
  kit colour question (Maya's AE keyed colour), not a marketing one.
- 07: the Channel Box shows the robot's quaternion rows (Rotation mode QUATERNION, yellow) and the Graph Editor
  header has a "Blender" menu — scene / kit choices for a later shot pass.
- Hotbox legibility at thumbnail size, 05 vs 09 variety, the key visual's back window (issues 5, 6).
- 06: "Bake Pivot Orientation" at the bottom of the pivot menu touches the viewport edge.

## Questions the review raised (recorded, not acted on)

- Should "for Maya Users" lead and "Allset" sign? — No: Autodesk's trademark guidance wants the own brand first and
  Maya only in the "for" reference (`extensions_audit.md`); the 0.66 lockup makes the reference readable instead.
  (Step 125: the user chose a name that leads with Maya, knowing this guidance — risk and fallback name in decision 12.)
- Would one 15 s "muscle memory" clip beat the 39 s tour? — Possibly for social; the store gallery keeps the tour +
  feature clips (`references.md` §5).
