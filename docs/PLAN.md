# Implementation plan

Source: `research/README.md` (table "Maya → Blender 대응표", milestones M1–M5) and
`research/blender/api_limits.md` (P/W/C matrix). Decisions: `docs/user_decisions.md`.

Verdicts: **P** possible with the Python API · **W** workaround / compromise · **C** needs C++ (not done; documented).
Verification: **H** headless test in `tests/` · **G** GUI simulated-event test in `tests/gui/` · **S** GUI screenshot checked by eye · **M** `docs/manual_checks.md` item.

## Steps

| # | Milestone | Step | Items (research table rows) | Verdict | Verify | Evidence |
|---|---|---|---|---|---|---|
| 1 | — | Project skeleton | git, docs, extension skeleton, build script, headless harness, enable/disable clean test | P | H | `blender/ui_architecture.md` §12 |
| 2 | M1-a | Maya keyconfig generator | Patch IC data → "Maya" keyconfig via `keyconfig_init_from_data`; selection modifiers (click and marquee; viewport, Outliner, UV, Graph); 4/5/6/7 shading (`maya_kit.display_mode`) + F8; Ctrl+G (`maya_kit.group`); Space freed, playback Alt+V; `docs/keymap_mapping.md` generator (468 Maya hotkeys). Shift+H/Alt+H, +/- → step 8; arrows → step 3; `.`/`,` → step 7 | P (Outliner/Graph Ctrl-deselect, non-3D marquee toggle: W) | H (bindings, conflicts, shadowing, mapping rows), S (keymap prefs) | `blender/industry_compatible_vs_maya.md` §0–§2, api_limits #16, `maya/hotkeys_default.json` |
| 3 | M1-b | Hold / tap framework | Hold modal (`maya_kit.hold`): X grid, C curve(edge), V point, J step snap, D pivot (Affect Only Origins), Insert toggle; tap/hold modal API (`maya_kit.tap_hold`, `TapHoldBinding`): A tap = frame all / hold+click = select menu, B tap = soft select / hold+LMB drag = radius; object-mode arrow pick-walk | P/W | H (state logic, keymaps), G (`tests/gui/` simulated key events), M (feel) | `maya/interaction.md` §0, §5, §6; README 핵심 발견 1 |
| 4 | M1-c | Camera, view, display keys | Maya navigation prefs preset (`prefs_preset.py`, backup/restore); Alt+LMB tumble with ortho lock; Shift+F / Shift+A frame in all views; view undo `[` `]` Alt+Z/Y (polled view-history stack); Space tap four views ↔ single, Ctrl+Space full screen; 1/2/3 smooth preview (Subsurf viewport); F7/F9/F10/F11 component modes | P/W | H, G, S | `maya/interaction.md` §1, §2, §7, §8, §10, §12 |
| 5 | M2-a | Layout, theme, units | App template `MayaKit` (`tools/make_startup.py` → startup.blend: Outliner left, persp viewport + sidebar, Layer Editor + Properties right, timeline; cm display, 1–120, empty scene), install/remove/open buttons; Maya theme (`tools/make_theme.py` → `theme/maya.xml`, apply/restore). "1 BU = 1 cm" opt-in units option still open | P | H, G, S | `maya/ui_layout.md` §2, `maya/workspaces.json`, `blender/ui_architecture.md` §2, decisions 1 & 3 |
| 6 | M2-b | Channel Box, Layer Editor | Sidebar "Channel Box": TRS/visibility proxies editing all selected, custom attrs, SHAPES, INPUTS (modifiers), channel selection, MMB virtual slider in front of tool MMB, Channels menu (key/breakdown/mute/delete/break/lock/hide/keyable/duplicate), state colours; Layer Editor = display layers on collections (V/P/T/R) | P (panel, viewport MMB) / W (multi-select rows) / C (MMB on field) | H (values, slider math), G, S, M | `maya/channel_box.md`, api_limits #1 |
| 7 | M2-c | Menu bar + menu sets, Status Line, command line, Help Line | Maya menu bar in TOPBAR (`draw_left/right` swapped, restored on disable): common menus + menu set dropdown (Modeling/Rigging/Animation/FX/Rendering) + set menus from `menus.json` (`tools/gen_menu_data.py`), mapped items run Blender operators, others greyed; Status Line in the main 3D View tool header (file, selection mode/masks, snap toggles shared with hold keys, render, editor toggles); Python command line + `cmds_shim` (maya.cmds subset, `import maya.cmds`), MEL notice; Help Line (tool help). Range slider, timeline look, `.` `,` keys → moved (see notes) | P / W | H, G, S, M | `maya/ui_layout.md` §4.1–4.2, §4.12–4.13, `maya/menus.json`, api_limits #10, #14 |
| 8 | M1-d | Remaining M1 keys and hierarchy | Isolate (Ctrl+1, Shift+I), H / Shift+H / Alt+H visibility, Alt+5 wire-on-shaded, PgUp/PgDn smooth level, 0, Ctrl+Shift+F, Home, +/- gizmo size, Ctrl+F9–F11 convert selection; P parent **Maya mode** (parent inverse = identity, decision 2), Shift+P; component pick-walk; edit-mode pivot (cursor); exact Outliner/Graph Ctrl-deselect | P / W (pivot) | H, G, M | `maya/interaction.md` §2, §4, §7, §11; `maya/concepts.md` §7 |
| 9 | M3-a | Marking menus (pie) | RMB / Shift+RMB / Ctrl+RMB pies per mode from `marking_menus.json`; W/E/R/A hold menus via `TapHoldBinding` | W (done in user step 8: `marking/`) | H, G, S, M | `maya/marking_menus.json`, api_limits #5 |
| 10 | M3-b | Custom marking menu engine + hotbox | Modal + GPU radial (flick, nested, linear list); Space hold hotbox (`space` binding's hold part) | W+ (done in user step 9: `marking/engine.py`, `modal.py`) | H (hit-test math), G, S, M | `maya/hotkeys_and_menus.md`, api_limits #4–#5 |
| 11 | M4-a | Concept operators | Freeze Transforms (keep pivot), Reset, Center Pivot, Delete History (apply modifiers), Maya naming on create; P / Shift+P Maya parenting (from row 8), Duplicate Special / with Transform, Maya Units option | P/W (done in user step 10: `operators/freeze.py`, `parenting.py`, `duplicate.py`, `history.py`, `create.py`, `units.py`) | H (matrices, names), G, S, M | `maya/concepts.md` §4–§5, §13–§14 |
| 12 | M4-b | Outliner, Attribute Editor, Layer Editor | UIList DAG outliner with shape toggle; AE node tabs (sidebar + `prop_tabs_enum`); display layers over collections | W (done in user step 11: `ui/outliner.py`, `ui/attribute_editor.py`, `ui/ae_layout.py`; layer editor in step 6) | H, G, S, M | `maya/attribute_editor.md`, `maya/channel_box.md` §3, api_limits #2–#3 |
| 13 | M5 | Shelf and menu sets | Shelf (header/panel/Asset Shelf), menu set hotkeys F2–F6 (switching itself done in step 7) | W (shelf done in user step 12: `ui/shelf.py` strip, `shelf_data`/`shelf_map`; F2–F6 keys open) | H, S | `maya/shelves.json`, `maya/menus.json`, api_limits #11 |
| 14 | — | Release | Legacy zip check, user docs, limitations page | P (done in user step 13: README, CHANGELOG, LICENSE, `tools/release_check.py`) | H, G, S | decision 3 |

## Ordering after step 7 (delegated)

- The user's step prompts number the next steps 8 = marking menus (row 9), 9 = hotbox
  (row 10), 10 = concepts (row 11). Rows keep their numbers here; step docs use the
  user's numbers.
- Step 7 leftovers (Range Slider, timeline look, `.` `,` Alt+`.` Alt+`,` key/frame
  stepping) join row 8 (remaining M1) in whichever step comes after the concepts step.

## Not possible (C) — documented, not implemented

Y-up world (IO axis conversion only), MMB-drag on UI fields, extending the built-in
transform gizmo, new region/editor types, Outliner tree drawing, timeline key drawing,
separate rotate/scale pivots, MEL. Source: `research/blender/api_limits.md` "Things that
are C-only". Decision 5: work around without forking; list what can't be done.

## Ordering notes (delegated)

- Steps 2–4 (M1) first: the keymap is what a Maya user touches every second, and later
  steps (marking menus, Channel Box MMB) bind keys through the same generator.
- Renumbered at step 4 (delegated) to follow the requested order 5 = layout, 6 = Channel
  Box, 7 = top UI. Old M1-d/M1-e items not done in steps 2–4 moved to step 8; marking
  menus/hotbox are now 9/10, concepts 11, Outliner/AE 12, shelf 13, release 14. Step
  docs 1–3 keep the old numbers in their text.
- Keymap strategy: a full "Maya" keyconfig generated from IC data for global behaviour,
  plus `keymap.add_item` overlays in the add-on keyconfig for feature-owned bindings, so
  that disabling the extension removes them (`tests/test_enable_disable.py`).

## 재점검 1차 (step 14, 2026-10-16)

Evidence: `docs/steps/step_14.md` (dogfood checks, screenshots, blindspot cards). All verdicts below are
delegated.

### Implementation rate — research/README.md mapping table (33 rows)

| Group | Done | Partial | Not started | Not possible (C) |
|---|---|---|---|---|
| 조작 / 단축키 (13) | 8 | 4 — selection modifiers outside the 3D View, 1/2/3 (faceted look, PgUp/PgDn), D/Insert (no edit-mode D, no pivot handle), pick-walk (no component walk) | 1 — Shift+drag manipulator = duplicate / extrude | 0 |
| UI (9) | 5 | 3 — layout (no Range Slider, timeline 0–250, narrow Outliner), Maya Outliner (no drag reparent), menu sets (no F2–F6) | 1 — timeline look + Range Slider | 0 (MMB on fields is C, the Channel Box row itself is done) |
| 개념 (11) | 8 | 1 — Maya naming (Ctrl+D / Shift+D copies get `.001`) | 0 | 2 — separate rotate/scale pivots, Y-up |
| **Total (33)** | **21 (64 %)** | **8 (24 %)** | **2 (6 %)** | **2 (6 %)** |

Keymap rows (`docs/keymap_mapping.md`, 468 Maya 2022 factory hotkeys): implemented 51, IC match 8,
planned 26, not applicable 9, macOS-only 68, **unreviewed 306**. The 25 `STEP` rows of `keymap/mapping.py`
(step 8 = PLAN row 8 "Remaining M1 keys", steps 7/13) were never built: the renumbering at user step 8
skipped PLAN row 8 (only P / Shift+P landed, in step 10).

### Remaining work, by priority

Priority = how often a Maya user hits it in the first hour × how wrong it feels. Sources: dogfood (D),
blindspot scout (B, cards in step_14.md), step docs (S).

1. **Data-loss bug — Delete History bakes the smooth-preview Subsurf** (B1): 3 then Alt+Shift+D
   subdivides the real mesh; 1 hides the first Subsurf even if it is the user's own.
2. **Daily Maya keys that do the wrong thing** (D, B3, B13) — step 16 did z / Shift+Z / Ctrl+Y, h-family,
   Ctrl+1, Ctrl+Shift+I; step 18 the mesh keys (D pivot, Ctrl+Shift+A, Alt+D, Ctrl+E, Ctrl+B, Shift+> <, Ctrl+F9–F11);
   still open: `z` = undo (now zoom border), Shift+Z /
   Ctrl+Y = redo, `h` toggle visibility, Shift+H / Alt+H (IC does the opposite), Ctrl+1 isolate,
   `+` `-` manipulator size, Shift+> / Shift+< grow / shrink, Ctrl+F9–F11 convert, PgUp/PgDn, `0`,
   Home, Ctrl+Shift+F, Ctrl+Shift+I; edit mode: D = annotate tool, Ctrl+Shift+A = deselect, Alt+D
   unbound; Ctrl+E / Ctrl+B only switch tools (B5).
3. **Framing and look** (D) — done: Maya fit for F / A / Shift+F / Shift+A / Ctrl+Shift+F (step 17),
   smooth shading of the preview (step 15), hotbox rows kept visible (step 17).
4. **Units consistency** (B2): Create/shelf cube = 1 BU (shows 100 cm), `cmds.polyCube()` = 1 cm.
   One rule for all creation paths.
5. **Maya naming of copies** (D) — done in step 19: Ctrl+D = `maya_kit.duplicate` (pCube2 / pCubeShape2, subtree, in place).
6. **Timeline** (S, D) — done in step 20: `.` `,` Alt+`.` Alt+`,`, timeline view = playback range, Range Slider
   fields in the Timeline header (animation 1–200, playback 1–120). Still open: Maya key ticks (W), range drag bar.
7. **Shift+drag manipulator duplicate / extrude** (B4, research row "높음", never planned) — complex
   design, plan first.
8. **Selection feel** (B6–B8): component marquee select-through (Maya `selectPrefUseDepth false`),
   pre-selection highlight (research), undo depth (32 steps vs Maya infinite) via `prefs_preset`.
9. **Menu correctness** (B11, B12): Increment and Save, Export Selection, Return in 3D View.
10. **Layout polish** (D): left Outliner width / Maya DAG rows in the main Outliner slot, quad → single
    header name.
11. Menu-set F2–F6 keys (replace IC F1–F4 view keys: keep ortho views reachable), Status Line input
    line, marking menu editor, shelf drag ordering, Outliner drag reparent, AE shading-group /
    texture tabs (S).
12. Review the 306 unreviewed keymap rows context by context as features are touched.
13. Hand checks: `docs/manual_checks.md` (84 open, need a person with real input devices).
14. Not possible / out of scope (kept documented): Y-up, separate pivots, MMB on fields, MEL,
    construction history nodes, Extensions platform listing (no remote).

Landmines for the key work (B9, B10): `tests/test_keymap_maya.py` pins IC idnames (`object.duplicate_move`,
`object.hide_view_set`) and raises KeyError for keymaps missing from `_STACKS`; `Frames`/`Screen` rows
check every keymap, so a global `Z` / `.` meets many conflicts; runtime changes to `prefs.view.gizmo_size`
or `prefs.edit.undo_steps` must go through `prefs_preset` and `tests/kit.py` must snapshot `prefs.edit`.
