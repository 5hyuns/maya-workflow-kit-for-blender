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
4. **Units consistency** (B2) — done in step 21: a Maya length of 1 = one scene display unit for every creation
   path (`units.maya_unit()`, decision 8); MayaKit template views at Maya's persp / clip in cm.
5. **Maya naming of copies** (D) — done in step 19: Ctrl+D = `maya_kit.duplicate` (pCube2 / pCubeShape2, subtree, in place).
6. **Timeline** (S, D) — done in step 20: `.` `,` Alt+`.` Alt+`,`, timeline view = playback range, Range Slider
   fields in the Timeline header (animation 1–200, playback 1–120). Still open: Maya key ticks (W), range drag bar.
7. **Shift+drag manipulator duplicate / extrude** (B4, research row "높음") — object duplicate done in step 22
   (`maya_kit.manip_duplicate` in front of the gizmo tweak); Smart Extrude on faces/edges next.
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

## 재점검 2차 (step 23, 2026-10-17)

Evidence: `docs/steps/step_23.md` (tests, dogfood, audit session screenshots), collection of every step's 「남은 것」,
`docs/manual_checks.md` and a blindspot pass against research/maya/*. Verdicts are delegated.

### Implementation rate — research/README.md mapping table (33 rows)

| Group | Done | Partial | Not started | Not possible (C) |
|---|---|---|---|---|
| 조작 / 단축키 (13) | 9 (+1/2/3 fixed in step 15) | 4 — selection modifiers outside the 3D View (Outliner/Graph Ctrl = toggle), D/Insert (no edit-mode Insert, pivot orientation), pick-walk (objects only), Shift+drag manipulator (objects done step 22, Smart Extrude not) | 0 | 0 |
| UI (9) | 5 | 4 — layout (narrow Blender Outliner on the left, names cut; quad→single header), Maya Outliner (no drag reparent / sets / keyboard nav), timeline (Range fields done step 20; no key ticks / drag bar), menu sets (no F2–F6) | 0 | 0 |
| 개념 (11) | 9 (+naming step 19, cm step 21) | 0 | 0 | 2 — separate rotate/scale pivots, Y-up |
| **Total (33)** | **23 (70 %)** | **8 (24 %)** | **0** | **2 (6 %)** |

Audit 1 → 2: 21/8/2/2 → 23/8/0/2. Keymap rows (`docs/keymap_mapping.md`, 468): implemented 51 → **79**, IC 8 → 6,
planned 26 → **13** (Home, 0, Alt+5, PgUp/PgDn, + = -, F2–F6), not applicable 10, macOS-only 68, unreviewed 306 → **292**.
Manual checks: 99 open, none ticked (needs a person with real input devices).

### New findings (audit session, step_23.md)

- Delete in component mode opens Blender's Delete menu (Maya deletes the selected components).
- MayaKit layout (cm): no grid lines visible, and X-hold grid snap moved a copy from 10.44 cm to 0 cm.
- Left Outliner too narrow (names cut); hold-menu toggles show no state; timeline current-frame box covers a number.

### Blindspots (not in any doc before; checked missing in code)

1. MMB drag = last-picked manipulator handle (`manipsRememberActiveHandle`, research/maya/interaction.md:104, :27). High.
2. Material assignment: Lighting/Shading > Assign New / Existing Material greyed (no `menu_map` entry), RMB menu has no
   material items (research/maya/hotkeys_and_menus.md:252). Only the shelf works. Medium-high.
3. Ctrl+Alt+LMB box zoom (interaction.md:43) unbound. Medium.
4. Per-viewport panel menu bar (View/Shading/Lighting/Show/Renderer/Panels, ui_layout.md:243-245). Medium.
5. Wireframe on shaded for the selection on by default in Maya (interaction.md:179, defaults.json:139). Medium.
6. File > Set Project / Project Window greyed, no substitute documented (menus.md:41-42). Medium.
7. T = Show Manipulator, Y = last tool (interaction.md:95-96). Low-medium.
8. Ctrl+Shift+X Multi-Cut / Ctrl+Shift+Q Quad Draw unbound (keymap_mapping). Low-medium.

### Remaining work, by priority

Priority = how often a Maya user hits it in the first hour × how wrong it feels.

1. **Component Delete** (new): Delete/Backspace in edit mode deletes by component type without a menu.
2. **cm grid and grid snap** (new): visible Maya grid (1 cm lines, 5 cm major) and X-snap to whole grid units in the
   MayaKit layout; check Maya Units too.
3. **Smart Extrude** + Shift+drag side effects (Shift+click without drag, cancelled drag leaves a copy, light gizmos).
4. **Manipulator size and view keys**: `=` / `-` (dogfood's only failure), PgUp/PgDn, `0`, Home, Alt+5 — runtime
   pref changes via `prefs_preset`.
5. **MMB = last handle** on the Move/Rotate/Scale tools (blindspot 1).
6. **Material assignment** (blindspot 2): Assign New/Existing Material menus + RMB items.
7. **Selection feel** (B6–B8): component marquee select-through, pre-selection highlight, undo steps (needs
   `tests/kit.py` to snapshot `prefs.edit`).
8. **Layout polish**: Outliner width / Maya DAG rows, quad→single header, hold-menu toggle state.
9. Medium: menu correctness (Increment and Save, Export Selection, Return in 3D View), menu-set F2–F6, component
   pick-walk, Outliner drag reparent, Status Line input line, Channel Box multi-object SHAPES/INPUTS, box zoom, viewport
   panel menus, wireframe-on-shaded default, Set Project, T/Y tools, timeline key ticks.
10. Low: see the step docs' 「남은 것」 (marking menu editor, shelf reorder, AE extra templates, text size, light
    intensity, lens FOV, AE "2 c", names unique only per sibling in Maya, ...), 292 unreviewed keymap rows.
11. Not possible / out of scope (kept documented): Y-up, separate pivots, MMB on fields, MEL, history nodes,
    menu option boxes / tear-off, Extensions platform listing.

Risks the manual checks guard (most likely real bugs, not feel): real OS key paths (X released mid-drag, Alt+Tab with a
key held — GUI tests replace `keystate.is_down`), keymap persistence with saved prefs (all tests use
`--factory-startup`), global `z` in text fields, stray copies from Shift+drag, Outliner rebuild speed with many objects.

## 재점검 3차 (step 32, 2026-10-17)

Evidence: `docs/steps/step_32.md` (tests, dogfood, audit-3 session screenshots). Collected every step's 「남은 것」,
`docs/manual_checks.md`, and ran a blindspot pass against research/maya/*. A read-only subagent did the collection; the
"missing" claims were re-checked by grep. Verdicts are delegated.

### Implementation rate — research/README.md mapping table (33 rows)

| Group | Done | Partial | Not started | Not possible (C) |
|---|---|---|---|---|
| 조작 / 단축키 (13) | 10 (+Shift+drag manipulator: Smart Extrude step 26) | 3 — selection modifiers outside the 3D View (Outliner/Graph Ctrl = toggle, no marquee XOR), D/Insert (no edit-mode Insert, no pivot orientation), pick-walk (objects only) | 0 | 0 |
| UI (9) | 6 (+layout step 31) | 3 — Maya Outliner (no drag reparent / sets / keyboard nav), timeline (no key ticks / range drag bar), menu sets (no F2–F6) | 0 | 0 |
| 개념 (11) | 9 | 0 | 0 | 2 — separate rotate/scale pivots, Y-up |
| **Total (33)** | **25 (76 %)** | **6 (18 %)** | **0** | **2 (6 %)** |

Audits 1 → 2 → 3: 21/8/2/2 → 23/8/0/2 → 25/6/0/2. Keymap rows (`docs/keymap_mapping.md`, 468): implemented 79 → **88**, IC 6 → 8,
planned 13 → **5** (F2–F6), not applicable 10, macOS-only 68, unreviewed 292 → **289**. Manual checks: 115 open, none ticked.

### New findings (audit-3 session, step_32.md)

- RMB marking menu: the root list (now with the material items) goes below the viewport even when the menu opens on a centred
  object. Step 29 only keeps submenus inside the region.
- The AE material tab labels every Principled material "standardSurface" (Lambert/Blinn/Phong made by the kit too).
- Ctrl+Alt+LMB drag box-selects instead of box-zooming (audit-2 blindspot 3, still open).
- `invoke_search_popup` (Shift+T) leaks 5 memory blocks at exit. This is Blender's problem (reproduced without the kit); kept.

### Blindspots (re-checked by grep in src/maya_kit)

1. **Menu dead ends** (High–Medium):
   - Windows > General / Modeling / Animation / Rendering / Relationship Editors have no children: Maya builds them at run time, and
     `menu_map` maps only Workspaces / UI Elements / Preferences / Playblast / Output Window.
   - UV > UV Editor, Planar, Best Plane and Normal-Based are greyed.
   - Edit > Ungroup has no operator.
   - Display > Heads Up Display > Poly Count is missing (no `show_stats` anywhere).
   - File > Increment and Save is a plain Save As (`menu_map.py:59`), and Export Selection opens the whole export menu (`:64`).
2. **Symmetry** (Medium-high for modellers): no Status Line symmetry or Move tool option. The only grep hit is the menu item
   `Edit Mesh/Symmetrize`.
3. **Alt+Shift drag locks tumble/track to one axis** (interaction.md:46): not implemented, not in any doc. Low-medium.
4. **K hold = scrub time in the viewport, Ctrl+T = Universal Manipulator key, Graph Editor 1/2/3 view keys**: unreviewed keymap rows
   that animators and modellers use. Low-medium.
5. **No in-view messages** on mode or soft-select toggles (interaction.md:30). Low.

### Remaining work, by priority

1. **Marking menu stays on screen**: keep the RMB / Shift+RMB root list inside the visible region; check the hotbox near the
   top edge (step_17.md:67).
2. **Menu dead ends** (blindspot 1): Windows editors, UV Editor / Planar, Ungroup, HUD Poly Count, Increment and Save,
   Export Selection.
3. **Key batch**: Ctrl+Alt+LMB box zoom, Ctrl+T, Y (last tool), Ctrl+Shift+X Multi-Cut, Ctrl+Shift+Q Quad Draw, Return in the
   3D View, and F2–F6 menu sets (decide the IC F1–F4 view-key clash).
4. **Symmetry** (blindspot 2).
5. **Per-viewport panel menu bar** (View / Shading / Lighting / Show / Renderer / Panels, ui_layout.md:243-245).
6. **Channel Box**: SHAPES/INPUTS for a multi-object selection, `+=`/`-=`/`*=` relative entry; AE material type label.
7. **Component pick-walk** (arrow keys in edit mode) and Alt+Shift axis-locked navigation.
8. Medium: Outliner drag reparent / sets, edit-mode Insert + pivot orientation, pre-selection for edges/faces/objects and
   under Move/Rotate/Scale, Status Line input line, timeline key ticks, K scrub, Graph Editor keys, Shift+Q / Alt+Q menus,
   AE "2 c" length fields.
9. Low: marking menu editor, shelf reorder, AE extra templates, in-view messages, curve/armature edit-mode keys, Ctrl+5,
   289 unreviewed keymap rows.
10. Not possible / out of scope (kept documented): Y-up, separate pivots, MMB on fields, MEL, history nodes, option boxes /
    tear-off, timeline frame box over numbers, Extensions platform listing. (5 cm major grid lines: done by the kit's own
    grid in step 45, `ui/maya_grid.py`.)

Risks the manual checks guard: real OS key paths (keys released mid-drag, Alt+Tab with a key held), keymap persistence with
saved prefs, select-through X-ray flag left on after an aborted drag, Outliner rebuild speed with many objects. A hand
pass over the 115 manual checks is still the biggest unverified area.

## Maya 동일화 계획 (step 40, 2026-10-17)

Request: "켜면 누가 봐도 Maya" — colours, layout, feel; better than paid add-ons. Evidence: `docs/steps/step_40.md`;
Maya 2022.4 factory screenshots and values measured in a running Maya (`research/maya/screens/`, `research/maya/colors.json`);
side-by-side shots and the theme ΔE00 table (`python tools/look_compare.py` → `research/maya/screens/compare/`);
rival add-ons (`research/competitors.md`); blindspot pass (18 findings, step_40.md 「blindspot」). Verdicts are delegated.

### What a Maya user sees first (compare/00–16, measured)

| Area | Maya 2022 factory [O] | Kit now | Gap |
|---|---|---|---|
| First start | Maya UI at once | keymap only; layout = 2 buttons, theme = 1 more button (opt-in); Blender splash | High |
| Viewport background | flat #5c5c5c, gradient off | theme gradient #889db3→#0d0d0d (from the user's own Maya prefs) | ΔE 27 |
| Grid | finite 12 units, line every 5 / 5 divisions, #404040, axes same grey, thicker | infinite fading floor, red/green axis lines | High |
| Selection | lead green #43ffa3 / others white, wire drawn over shaded objects | colours fixed this step; Blender outline only, no wire | High |
| Components | object wire #64dcff, vertices #c800c8 / selected yellow, edges & faces #e4ac79 + translucent face fill | Blender black / orange (+ `*_mode_select` yellow) | ΔE 12–77 |
| Manipulator | X #e60000 Y #00e600 Z #4a92ff, yellow active, centre square + plane squares | Blender axis colours, thin arrows; axis colours also tint grid lines | ΔE 3–15 |
| Viewport furniture | ViewCube top right, axis triad bottom left, "persp" bottom centre | navigate gizmo + zoom/pan buttons, "User Perspective (1) Collection" text | High |
| Density / font | Segoe UI 11 px, CB rows 16 px, menu items 20 px, flat square widgets | Inter ~14 px, rows 25 px, rounded (0.4) embossed widgets | High |
| Layout | Toolbox 40 px · Outliner 260 · view · right dock tabs CB/LE 260 / AE 460 / MTK; Time Slider, Range Slider, Help+Command rows | extra right column (Blender Outliner + Properties), Blender toolbar inside the view, tool header row, Range fields inside the timeline header | High |
| Shelf / Status Line | 32 px coloured icons, tab row #373737 | Blender monochrome 20 px icons | Medium-high |
| Hotbox / RMB menu | all menu-set rows, "Maya" centre, zone lines; RMB list "pCube1..." under the ring | current set only, squeezed by the sidebar; list beside the ring, other items | Medium |

Theme ΔE00 after the lead/selected fix: 11 of 31 pairs > 5 (`delta_e.md`). Colours are cheap; the furniture, density and
first-start path are what make it read as Blender.

### Rivals (research/competitors.md)

- Everyone has: Alt navigation, QWER, Blender pies called marking menus, a Maya theme, a button shelf, quad view.
- Nobody has (the kit already does most): Channel Box, AE, Maya Outliner, real flick marking menus, Space hotbox, menu sets,
  Status Line, hold X/C/V/D, Maya-exact Freeze/Delete History/cm units, Smart Duplicate, pick-walk, maya.cmds line.
- Top complaints: breaks on every Blender update, keymap conflicts, breaks other editors, destructive install (deletes add-ons),
  online licence checks. → The kit's edge is depth + safety; it still loses on **first impression** (a rival's theme pack
  looks more Maya at first glance than the kit with its theme off).

### Next steps, by priority (backlog.json, step 41+)

Order (dependencies in brackets):
1. Comparison fidelity — same camera/state in `look_shots.py`, rendered-pixel ΔE at the colors.json sample points, region
   rectangles vs `_maya_ui_dump.json`, crop comparisons. Every later item is verified with it.
2. First-start path — decide template `userpref.blend` vs one-click "Make Blender Maya" (+ revert all), kit-made splash.
   Changing decision 3 is recorded as a delegated amendment in `docs/user_decisions.md`.
3. Theme v2 colours (viewport, components incl. `*_mode_select`, manipulator, Outliner, tabs, current frame, preselect).
4. Widget feel — flat widgets, density (`ui_scale` preset), Segoe UI on Windows (system font, not shipped).
5. Maya grid (own GPU grid, X-snap parity) [after 3]. 6. ViewCube / axis triad / camera labels, Blender overlays hidden.
7. Selected-object wireframe [after 3]. 8. Layout parity (dock columns, mode-independent toolbox, sidebar tabs, bottom rows) — done step 49.
9. Editor chrome: Channel Box / Layer Editor, Outliner, Time Slider — done step 50. 10. Menus (option boxes, open under the menu bar),
   shelf / Status Line icons (kit-made). 11. Hotbox / RMB fidelity (②: seen only when invoked).
12. Rivals (③): Blender 5.x compatibility check (target stays 4.5, decision 4) + safe-install assertions.

Later candidates (not in this backlog): W/E/R tool kept across modes and manipulator centre/plane handles (②),
HUD / in-view messages / Alt+B background cycle (②), import from the user's Maya prefs — parse only, never execute MEL
(③, decisions 5–6).

Done criteria for ①: theme rows and rendered-pixel samples ΔE00 < 2 (viewport elements < 5), region rectangles ±10 px of
the Maya widget geometry, per-crop checks (row pitch ±1 px, menu/label text and order equal), all tests at ui_scale 1.0
(and 0.8 once item 4 lands). A green ΔE table alone does not prove the screen reads as Maya: chrome and layout (8–10) do.

Delegated decisions (step 40):
- D1 Maya reference = factory prefs (clean `MAYA_APP_DIR`), not the user's customised prefs; the theme's gradient was from
  the latter and is replaced.
- D2 Global preference changes (ui_scale, font, mini axis) stay opt-in presets with backup/restore (CLAUDE.md prefs_preset
  rule); the automatic path is the MayaKit template's own `userpref.blend` only if the item-2 prototype shows it keeps the
  user's add-ons; either way decision 3 gets a delegated amendment.
- D3 No Maya icons/images/fonts are shipped; shelf/toolbox icons are kit-made, Segoe UI is used only as an installed system font.

## Maya 워크플로우 계획 (step 48, 2026-10-17)

Request (user, verbatim): 「모델링, 애니메이션, 리깅, FX 등등 Maya의 고유한 워크플로우를 분석하고 그 워크플로우가 들어가게 해줘.」
Evidence: a real Maya 2022 run walking 47 workflow steps with the commands Maya's menus run (`research/scripts/maya_workflows/wf.py`,
log `research/maya/workflows/_maya_run.json`, shots `research/maya/workflows/shots/`, captured from Maya's own widgets only); per
discipline `research/maya/workflows/{modeling,uv,animation,rigging,fx,render,scene}.md` (hand order, kit now with file:line, gap table
with frequency × break scores, concept decisions, GUI follow-along scenarios); a blindspot pass and a brainstorm (`docs/steps/step_48.md`).
Verdicts are delegated.

### Where the flow breaks today (top rows, score = daily frequency 1–5 × break 1–5)

| Discipline | Gap (kit now) | Score |
|---|---|---|
| Rigging / animation | Channel Box, Outliner, AE only see objects: on a rig in pose mode they show the armature (`ui/channel_box.py:62-73`), bones fall into "Rotation mode QUATERNION" | 25 |
| Rigging | Joint Tool = `object.armature_add` (one 1 BU bone, not click-to-place, no `maya_unit()`, `ui/menu_map.py:294`); Paint Skin Weights / Bind Skin / IK are bare Blender ops with Maya selection order wrong | 20 |
| Modeling | construction history edited later in Channel Box INPUTS / In-View Editor (only modifiers are INPUTS; edit-mode ops = one Adjust Last Operation) | 20 |
| Modeling | Target Weld missing, Modeling Toolkit greyed (`menu_map.py:385`) | 20 / 16 |
| UV | no UV Toolkit, no UV component (F12), Cut/Sew/Unfold/Layout keys missing, 3D Cut and Sew greyed (`shelf_data.py:94`) | 20 |
| Render | Hypershade = a bare Shader Editor window (`menu_map.py:92`), no material browser; Light Editor greyed; Render menu lost its items (`menu_data.py:49`) | 20 / 16 / 15 |
| FX | simulation defaults in metres on 1 cm objects (cloth collision 0.015 m > a 1 cm plane, rigid margin 0.04 m, field empty 1 m); nParticles Create Emitter greyed, shelf Emitter = Emit from Object | 20 / 15 |
| Animation | no K time drag (K = knife), timeline body LMB doesn't scrub, Graph Editor has no tangent buttons, RMB Key Selected / Time Slider menu are Blender's | 16 / 15 / 15 / 12 |
| Scene | no Set Project / Project Window, Ctrl+Alt+S names files differently from the menu's Maya Increment and Save, Create Reference = `wm.link` (no namespace), sets invisible in the Outliner | 16 / 12 / 12 / 8 |

Already right (don't redo): Playblast uses the playback range (measured), Channel Box keying/breakdown/mute/lock/hide and driven
state, smooth preview 1/2/3, Smart Duplicate/Extrude, symmetry, Maya parenting, X/C/V snaps, Delete History / Freeze / Center Pivot,
materials assignment (step 29), Increment and Save menu with Maya's rule (step 34).

### Concept decisions (delegated, step 48)

- W1 **Maya joint = a bone** in one armature per skeleton (`skeleton1`, bones `joint1…`, rotation mode XYZ); pose mode counts as
  "joints selected": Channel Box / Outliner / AE work on the active and selected pose bones. Bone Y (not Maya X) points down the bone:
  told in the UI, not converted.
- W2 **Construction history**: modifiers stay the lasting history; the kit's own last modeling op shows as one INPUTS row editable
  afterwards (undo + run again with new values). Notice: "Edit-mode operations have no history in Blender: only the last one can be
  changed." (PLAN 「Not possible」 history nodes stays.)
- W3 **Not in Blender → near substitute + notice** (one shared mechanism, step 54): Animation Layers → NLA, Character Sets → Keying
  Sets, Quick Select Sets → collections, ghosting → animation snapshot, buffer curves → ghost curves, Time Editor/Trax → NLA, Node Editor
  (DG) → none (drivers / Shader Editor), Hypergraph → Outliner, Light Editor → kit light list, HumanIK / Quick Rig → Rigify (shipped
  in `addons_core`), Texel Density → kit operator, Namespace → `ns:` name prefix, Reference → link + library override, Set Project →
  kit project root in add-on prefs (+ `//` relative paths), nucleus → kit nucleus settings on the Scene.
- W4 **Simulation scale** (amends decision 8 for simulations, recorded as decision 10): Maya's nucleus defaults are `spaceScale` 1.0
  with gravity 9.8 in a cm scene (measured with mayapy, step 48): Maya simulates one scene unit as one metre, so a 1 cm cube falls
  like a 1 m one. The kit reproduces what the Maya user sees: kit FX create paths scale gravity and sim lengths by `maya_unit()`
  (gravity 9.8 × maya_unit / Space Scale m/s², collision distances, particle sizes and domains in Maya units); a kit
  "Space Scale" (default 1, Maya's) keeps the same meaning. The "one unit = one metre" reading of Space Scale 1 is Maya documentation [K];
  the values were measured.
- W5 **Create paths outside `maya_kit.create`** (armature, empties/fields, text, image, quick effects, lights) go through `maya_unit()`;
  light power × `maya_unit()²` for point/spot/area (inverse-square in metres) with a "no No-Decay in Blender" notice.
- W6 **Maya workspaces** (Animation, Rigging, UV Editing, Rendering) are generated by `tools/make_startup.py` once step 49 (layout
  parity) has the dock columns; hotbox workspace switches use them instead of Blender's own (left out of 54–67: own step later).

### Implementation steps (backlog.json → steps 54–67, after the queued look steps 49–53)

Priority = score × dependency. Each step: one session; plan first in `step_<n>.md` when modal / keymap / matrix; evidence =
`research/maya/workflows/<discipline>.md` sections; verification = headless tests + a GUI test that repeats the Maya hand order of the
discipline file with the expected result (`tests/gui/`, ui_scale 1.0 and 0.8) + `docs/manual_checks.md` + dogfood 47/47.

| # | Step | Depends on |
|---|---|---|
| 54 | Workflow foundation: Maya-unit create paths incl. fields/effectors (W5), light power, the shared "not in Blender" notice (W3) | — |
| 55 | Joints selected = pose bones in Channel Box / Outliner / AE (W1) + constraint weight rows | 54 (notices) |
| 56 | Time Slider and key feel: LMB scrub, K time drag, Maya Time Slider RMB menu, S (all keyable) / Key Selected, Delete / Breakdown / Copy-Paste keys, MMB time-drag notice | 50 |
| 57 | Joint Tool (click to place), Orient / Mirror Joint, pose pick-walk, P in pose mode | 55 |
| 58 | IK Handle + Pole Vector, Bind Skin in Maya selection order, Paint Skin Weights setup + influence list, Copy / Mirror weights | 57 |
| 59 | Pivot concept (D/Insert keep translate, pivot orientation, Bake / Reset / Match Pivots), all snaps (X absolute grid, V pivot, step snap, Snap Align Objects, Snap Together, Make Live), Maya-shaped Move/Scale manipulator (user request 2026-10-18, docs/steps/step_59.md) | 10, 22, 25, 28 |
| 60 | Switch to / back from the Maya skin at any time, complete revert (user request 2026-10-18) | 42 |
| 61 | Distribution options research and decision, no publishing (user request 2026-10-18) | 13 |
| 62 | Set Driven Key window, pose-mode Constrain menu, Add Attribute, Blend Shape (join_shapes), Quick Rig / HumanIK notice (Rigify) | 55, 58 |
| 63 | Modeling Toolkit dock (third dock), soft select radius in Maya units, Separate / Combine / Mirror with Maya meaning | 49 |
| 64 | Target Weld tool, Crease tool, Multi-Cut feel (Ctrl edge loop, snap step) | — |
| 65 | Extrude manipulator (Python GizmoGroup) + In-View Editor + last-op INPUTS row (W2) | — |
| 66 | UV workflow: UV Editor entry (edit + sync), UV Toolkit panel, UV marking menu, Cut / Sew / Unfold / Layout keys, Texel Density | 49, 52 |
| 67 | Hypershade window (material browser + Shader Editor + AE), kit Light Editor, Render menu restored, Render View Keep Image, AE map button | 54 |
| 68 | FX: Maya simulation scale (W4), kit nucleus section, nParticles emitter / Emit from Object, nCloth on all selected, nCache | 54 |
| 69 | Scene management: Set Project / Project Window, Ctrl+Alt+S = Maya increment, Create Reference + namespace prefix + Reference Editor | 54, 50 |
| 70 | Graph Editor tangent toolbar + Shift+S tangent menu, G, Auto Key semantics, Playblast player + options | 56, 52 |

Order (delegated, after the step 48 review): score × dependency — rigging / animation core first (25, 20), then modeling (20),
UV (20), render (20), FX scale (20), scene (16), Graph Editor (15). Option boxes (□) in these steps are `invoke_props_dialog`
popups (the 「Not possible」 option boxes stay); new manipulators are Python GizmoGroups (the C transform gizmo can't be extended).
Every key binding goes through `maya_patches._add` (shadows recorded) + `keymap/mapping.py` row status + `tools/gen_keymap_mapping.py`;
new marking menus get their Maya positions in research JSON and a `test_step8`-style check.

### Left out of steps 54–67 (score, reason) — later candidates

- UV: 3D Cut and Sew modal tool (20, own modal step after 63), UV checker (12), Optimize / Straighten (9), UV display keys (9).
- Modeling: Quad Draw Make Live (12), Bevel immediate options (8), Insert pivot in edit mode (8), Delete History in edit mode (5),
  Match Transformations (6).
- Animation: buffer curves (4), Maya Animation / Rigging / UV workspaces (W6, after 49 — own step), ghosting (snapshot substitute, 9),
  Time Editor / Trax (NLA notice only, via 54).
- Rigging: Spline IK (8), Component Editor weight table (12), Shape Editor (9), Node Editor (impossible, notice via 54).
- FX: 3D fluid container (10), Bifrost → quick_liquid (10), MASH network (15: no MASH in `menus.json`, needs menu data + generator
  first), nConstraint (8).
- Render: Render Settings window and 960×540 template resolution (8), Light Linking (6), Tab node add in the Shader Editor (8).
- Scene: Outliner Sets (8), Hypergraph Hierarchy (6).

## 재점검 4차 (step 71, 2026-10-18)

Evidence: `docs/steps/step_71.md` (tests, dogfood, audit-4 session screenshots). Collected the mapping table, PLAN, every
「남은 것」 of steps 33–70, `docs/manual_checks.md` and `docs/keymap_mapping.md`, and ran a blindspot pass against research/maya/*.
A read-only subagent did the collection; its counts and "missing" claims were re-checked by grep. Verdicts are delegated.

### Implementation rate — research/README.md mapping table (33 rows)

| Group | Done | Partial | Not started | Not possible (C) |
|---|---|---|---|---|
| 조작 / 단축키 (13) | 11 (+pick-walk: components step 39, joints step 57) | 2 — selection modifiers outside the 3D View (Outliner Ctrl = toggle, no marquee XOR; API limit), D/Insert (no edit-mode Insert) | 0 | 0 |
| UI (9) | 7 (+menu sets F2–F6 step 35) | 2 — Maya Outliner (no drag reparent with Maya parenting, no Sets), timeline (no key ticks, Range Slider bar not draggable, no once/oscillate) | 0 | 0 |
| 개념 (11) | 9 | 0 | 0 | 2 — separate rotate/scale pivots, Y-up |
| **Total (33)** | **27 (82 %)** | **4 (12 %)** | **0** | **2 (6 %)** |

Audits 1 → 2 → 3 → 4: 21/8/2/2 → 23/8/0/2 → 25/6/0/2 → 27/4/0/2. Keymap rows (`docs/keymap_mapping.md`, 468): implemented
88 → **113**, IC 8 → **10**, planned 5 → **0**, not applicable 10, macOS-only 68, unreviewed 289 → **267** (global 98, Time Editor 36,
Node Editor 36, Hypershade 25, UV 17, sculpt 15, other 40). Manual checks: **287 open, none ticked** (115 at audit 3) — the hand pass
is the largest unverified area.

Audit-3 backlog: items 1–7 closed (steps 33–39); from item 8 pivot orientation (59), K scrub (56), Graph Editor G/D/tangents (70)
closed; still open: Outliner drag reparent / Sets, edit-mode Insert, pre-selection beyond vertices + select tools, Status Line input
line, timeline key ticks, Graph Editor 1/2/3, Shift+Q / Alt+Q. Item 9 (low) mostly open: in-view messages, marking menu editor,
shelf reorder.

### New findings (audit-4 session, step_71.md)

- **F2–F6 don't repaint the top bar.** F3 sets `riggingMenuSet`, but the Maya menu bar still reads "Modeling" 0.8 s later
  (`a4_05_menuset_f3.png`): `maya_kit.menu_set` tags only `window.screen.areas`, and the top bar is a global area that isn't in
  that list. gui_step35 hid this by hovering the top bar before its shot.
- **No key ticks on the Time Slider**: keys at 1 and 12 show nothing on the ruler (`a4_03_keys_timeline.png`; Maya draws red ticks).
- Everything else in the session behaved: Ctrl+D / Ctrl+G / z z, S (10 channels, red CB fields), 3 / 1 smooth preview (1 hides the
  preview modifier and keeps its level, by design), Shift+RMB marking menu, Space hotbox, Ctrl+Alt+LMB box zoom, F11 + Ctrl+E
  (polyExtrudeFace1 in-view editor + CB INPUTS), face pick-walk, Hypershade window. Console errors 0.

### Blindspots (not implemented and not listed as left out; re-checked by grep in src/maya_kit)

1. **Selection priority** (research/maya/interaction.md:74: handles 10, joints 9, curves 4, meshes 2): no code or doc. Medium
   (animators/riggers click controls in front of meshes).
2. **Status Line Input Line + Construction History toggle** (research/maya/ui_layout.md:208-211: absolute/relative transform,
   rename, select by name). Medium.
3. Backtick tweak-mode hold (interaction.md:114; IC `object.transfer_mode` answers, `keymap_mapping.md:443`). Low–Medium.
4. Ctrl+Alt+←/→ Spin Edge: mapped in the menu (`menu_map.py:283-284`), no key. Low–Medium.
5. Shift+G repeat at mouse position (interaction.md:208; planned in audit 1, then dropped). Low.
6. Alt+arrow nudge, Ctrl+Shift+C camera from view, `\` 2D pan/zoom, selection masks reset on new scene. Low.

### Remaining work, by priority (backlog.json, step 72+)

1. **Menu bar repaint + in-view messages**: F2–F6 repaint the top bar; Maya in-view messages on mode / soft select / symmetry toggles.
2. **Time Slider key ticks + Range Slider drag** (step_56.md:26, step_50.md:67).
3. **Pre-selection highlight** for edges / faces / objects and under Move/Rotate/Scale (step 30 left it vertex + select tools only).
4. **Status Line Input Line** (blindspot 2).
5. **Selection priority** (blindspot 1). Done in step 76.
6. **Edit-mode Insert / D pivot** (PLAN 「Left out」, mapping row D/Insert). Done in step 77: mesh Insert toggles the
   D cursor pivot edit, a turned pivot becomes the "Maya Pivot" Move axis; mapping row D/Insert Partial → **Done**
   (조작 / 단축키 12 / 1 / 0 / 0; total 28 / 3 / 0 / 2 = 85 %, with the step 73 timeline still counted Partial).
7. **Key batch**: Graph Editor 1/2/3, Shift+Q / Alt+Q menus, Ctrl+Alt+←/→ Spin Edge, Shift+G, Ctrl+Shift+C. Done in step 78 (keymap 구현 113 → 122).
8. **3D Cut and Sew UV tool** (score 20, the highest Left-out item; x/s/d keys). Done in step 79 — the audit-4 backlog (steps 72–79) is closed.
9. Later (Left-out lists + step 33–70 「남은 것」, `docs/steps/step_71.md`): Outliner Sets / drag reparent, Hypershade Textures /
   Lights tabs, Maya Animation / Rigging / UV workspaces, Spline IK, Component Editor, Shape Editor, MASH / fluids, Reference
   Unload/Replace, ViewCube edges, shelf reorder, 5.x GUI run, the 287 manual checks.
10. Not possible / out of scope (kept): Y-up, separate pivots, MMB on fields, MEL, history nodes beyond the kit extrude record.

## 재점검 5차 (step 80, 2026-10-18)

Evidence: `docs/steps/step_80.md` (tests, dogfood, audit-5 session screenshots). Collected the mapping table, PLAN, every
「남은 것」 of steps 72–79, `docs/manual_checks.md` and `docs/keymap_mapping.md`, and ran a blindspot pass against
research/maya/*. A read-only subagent did the collection; its "missing" claims were re-checked by grep. Verdicts are delegated.

### Implementation rate — research/README.md mapping table (33 rows)

| Group | Done | Partial | Not started | Not possible (C) |
|---|---|---|---|---|
| 조작 / 단축키 (13) | 12 (+D/Insert step 77) | 1 — selection modifiers outside the 3D View (Outliner / UV / Graph Ctrl = toggle, no marquee XOR; **Dope Sheet, NLA, Node Editor not patched at all**) | 0 | 0 |
| UI (9) | 7 | 2 — Maya Outliner (drag in the Outliner = Blender parenting, no Sets), timeline (step 73 ticks + Range Slider drag done; Shift-range key drag / scale open; Once / Oscillate = Blender limit) | 0 | 0 |
| 개념 (11) | 9 | 0 | 0 | 2 — separate rotate/scale pivots, Y-up |
| **Total (33)** | **28 (85 %)** | **3 (9 %)** | **0** | **2 (6 %)** |

Audits 1 → 5: 21/8/2/2 → 23/8/0/2 → 25/6/0/2 → 27/4/0/2 → 28/3/0/2. Keymap rows (`docs/keymap_mapping.md`, 468): implemented
113 → **125**, IC 10, not applicable 10 → **11** (polyCutUV Shift+D, step 79), macOS-only 68, unreviewed 267 → **254**
(global 93, Node Editor 36, Time Editor 36, Hypershade 25, UV 17, sculpt 15, other 32). Generator bug: the `Shift+\` row
(FrameTimeSliderBookmark) breaks the table (backslash before the pipe). Manual checks: **320 open, none ticked** (287 at audit 4).

Audit-4 backlog: items 1–8 all closed (steps 72–79). Audit-4 blindspots: selection priority (76), Status Line input line (75),
Spin Edge / Shift+G / Ctrl+Shift+C (78) closed; backtick tweak, Alt+arrow nudge, `\` pan/zoom, masks reset on new scene open.

### New findings (audit-5 session, step_80.md)

- **The MayaKit persp view is twice as wide-angle as Maya's.** The template sets the Blender viewport lens to 35
  (`tools/make_startup.py:37`, `MAYA_LENS`), but Blender measures the viewport lens on a 72 mm sensor (step 41: tan(fov/2) =
  36 / lens): horizontal FOV 2·atan(36/35) = 91.6°, Maya's persp (35 mm on a 36 mm film back) 54.4°; a Blender lens of 70 gives
  the same angle. Step 41 flagged it (step_41.md:52, lens 50 then) and nothing fixed it. Visible as a tiny pCube1 and strong
  perspective in every session shot, and Ctrl+Shift+C makes a camera with Focal Length 17.5 instead of Maya's 35.
- Session 15 of 16 checks; the failure was the session's own (the Move manipulator covering the whole 1 cm cube, where
  pre-selection yields by design, step 74; a first run also clicked a cube hidden under the test circle). Everything from steps 72–79 behaved: selection priority,
  F3 top bar repaint, F8 in-view message, edit-mode Insert, 3D Cut and Sew drag (1 → 2 shells), S twice → red ticks at 1 / 12,
  Input Line Abs X 20, Alt+Q menu, Ctrl+Shift+C, Space hotbox. Console errors 0.

### Blindspots (not implemented and not listed as left out; re-checked by grep in src/maya_kit)

1. **Dope Sheet / NLA / Node Editor selection modifiers** (research/maya/interaction.md:69-71): no rules in
   `maya_patches.SELECT_RULES`; IC has no Ctrl / Ctrl+Shift click there.
2. **Insert-key family**: Alt+I InsertKey, Ctrl+Shift+W/E/R InsertKeyTranslate/Rotate/Scale, `i` Insert Key tool
   (keymap_mapping.md:201, :467-470; research/maya/hotkeys_and_menus.md:158). No code, no doc.
3. **Key nudge / select next key**: Shift+( / ), Ctrl+Alt+, / . (keymap_mapping.md:219-220, :476-477).
4. **Manipulator Ctrl+LMB on an axis = move in the other two axes' plane, Shift+MMB = automatic axis** (interaction.md:104, :106);
   listed in step_28.md:60-61, dropped from later lists; `ui/manipulator.py` has no Ctrl handling.
5. Alt+A cycle display / X-ray, Alt+P persp ↔ ortho (keymap_mapping.md:213, :133). Low–Medium.
6. Tool Settings "Reset Tool" (research/maya/ui_layout.md:267-268). Low.

### Remaining work, by priority (backlog.json, step 81+)

1. **Maya persp field of view** (new finding): template lens 70, camera from view, look_compare.
2. **Outliner drag = Maya parenting** (mapping row 90). — done step 82 (MMB drag onto / between / empty, LMB drop redone the Maya way; Sets still open).
3. **Insert / nudge key batch** (blindspots 2–3). — done step 83 (Alt+I, Ctrl+Shift+W/E/R shape-keeping insert, Shift+( / ) nudge, Ctrl+Alt+, / . select key).
4. **Time Slider Shift-range key drag / scale** (mapping row 92; step_56.md:113, step_73.md:121).
5. **Manipulator Ctrl+LMB plane / Shift+MMB auto axis** (blindspot 4).
6. **Dope Sheet / NLA / Node Editor selection modifiers** (blindspot 1; mapping row 72).
7. **View key batch**: Alt+A, Alt+P, Alt+arrow nudge, backtick tweak, `\` pan/zoom + the `Shift+\` table row.
8. **Manual checks → GUI tests sweep**: 320 open checks, none ticked; turn the automatable ones of steps 59–79 into GUI tests.
9. Later: Left-out items (MASH 15, UV checker 12, Component Editor 12, Quad Draw Make Live 12, fluids / Bifrost 10, Straighten 9,
   UV display keys 9, ghosting 9, Shape Editor 9, Spline IK 8, Render Settings 960×540 8, Outliner Sets 8), step 72–79 「남은 것」
   (Shift+Q check marks, Cut and Sew tool menu, pivot RMB menu, Stacked view), Maya Animation / Rigging / UV workspaces,
   5.x GUI run, distribution decision 11.
10. Not possible / out of scope (kept): Y-up, separate pivots, MMB on fields, MEL, history beyond the kit extrude record,
    playback Once / Oscillate.
