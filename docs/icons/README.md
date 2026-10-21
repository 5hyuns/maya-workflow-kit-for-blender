# Kit icon contact sheets (step 131, #23)

Every picture here is drawn by the kit's own code (numpy vector shapes, CC0 like the rest of the kit's assets) —
no Maya icon file is copied or traced (decision 6). The sheets are regenerated with

    python tools/icon_sheet.py

| Sheet | What | Drawn by |
|---|---|---|
| `shelf_<Shelf>.png` | every factory shelf button, 2x (64 px) and 1x (32 px), numbered in Maya's shelf order | `src/allset/ui/shelf_icons.py` |
| `status_line.png` | Status Line and menu-bar glyphs at 48 / 32 / 24 / 16 px | `src/allset/ui/status_icons.py` |
| `panel_toolbar.png` | viewport panel toolbar glyphs at 48 / 32 / 24 / 16 px | `src/allset/ui/panel_toolbar.py` |

Tool Box tools, quick-layout buttons, Layer Editor buttons and the kit's Outliner rows are drawn by
`src/allset/ui/kit_icons.py` (sheets of those are produced by its lane, see `docs/steps/step_131_toolbox.md`).

What each icon stands for, the Maya command behind it and the recognisability scores: `docs/steps/step_131_icons.md`
and the lane docs `docs/steps/step_131_{shelf,status,toolbox,menu}.md`. The side-by-side comparison with the Maya 2022
icons is kept in `tmp/` only and is never committed.
