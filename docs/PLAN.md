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
| 10 | M3-b | Custom marking menu engine + hotbox | Modal + GPU radial (flick, nested, linear list); Space hold hotbox (`space` binding's hold part) | W+ | H (hit-test math), G, S, M | `maya/hotkeys_and_menus.md`, api_limits #4–#5 |
| 11 | M4-a | Concept operators | Freeze Transforms (keep pivot), Reset, Center Pivot, Delete History (apply modifiers), Maya naming on create | P/W | H (matrices, names) | `maya/concepts.md` §4–§5, §13–§14 |
| 12 | M4-b | Outliner, Attribute Editor, Layer Editor | UIList DAG outliner with shape toggle; AE node tabs (sidebar + `prop_tabs_enum`); display layers over collections | W | H, S | `maya/attribute_editor.md`, `maya/channel_box.md` §3, api_limits #2–#3 |
| 13 | M5 | Shelf and menu sets | Shelf (header/panel/Asset Shelf), menu set hotkeys F2–F6 (switching itself done in step 7) | W | H, S | `maya/shelves.json`, `maya/menus.json`, api_limits #11 |
| 14 | — | Release | Legacy zip check, user docs, limitations page | P | H | decision 3 |

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
