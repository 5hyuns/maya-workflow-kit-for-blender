# Implementation plan

Source: `research/README.md` (table "Maya → Blender 대응표", milestones M1–M5) and
`research/blender/api_limits.md` (P/W/C matrix). Decisions: `docs/user_decisions.md`.

Verdicts: **P** possible with the Python API · **W** workaround / compromise · **C** needs C++ (not done; documented).
Verification: **H** headless test in `tests/` · **S** GUI screenshot checked by eye · **M** `docs/manual_checks.md` item.

## Steps

| # | Milestone | Step | Items (research table rows) | Verdict | Verify | Evidence |
|---|---|---|---|---|---|---|
| 1 | — | Project skeleton | git, docs, extension skeleton, build script, headless harness, enable/disable clean test | P | H | `blender/ui_architecture.md` §12 |
| 2 | M1-a | Maya keyconfig generator | Patch IC data → "Maya" keyconfig via `keyconfig_init_from_data`; selection modifiers (shift toggle / ctrl deselect / ctrl+shift add, click and marquee); 4/5/6/7 shading, F8–F12 components, Ctrl+G, arrows pick-walk, Shift+H/Alt+H, `.`/`,` keys, +/- gizmo size, Space remap slot | P | H (bindings by name), S (keymap prefs) | `blender/industry_compatible_vs_maya.md` §0–§2, api_limits #16, `maya/hotkeys_default.json` |
| 3 | M1-b | Hold / tap framework | Hold-only: X grid, C curve, V point, J step snap, B soft select (+ radius drag); tap-vs-hold (A tap = frame all) as PRESS/RELEASE pairs + modal | P/W | H (keymap pairs, state toggles), M (feel) | `maya/interaction.md` §0, §5, §6; README 핵심 발견 1 |
| 4 | M1-c | Camera and view feel | Alt+LMB/MMB/RMB details (COI tumble, zoom direction, no zoom-to-mouse, ortho tumble lock), F/A/Shift+F/Shift+A framing, view undo `[` `]` stack | P/W | H (prefs values, view stack), M (feel) | `maya/interaction.md` §1, §8; IC-vs-Maya §2 |
| 5 | M1-d | Display and component toggles | 4/5/6/7 operators, 1/2/3 smooth preview (Subsurf viewport levels), F8–F12 mode ops, isolate/hide variants | P | H, S | `maya/interaction.md` §7, §11 |
| 6 | M1-e | Hierarchy and pivot | Ctrl+G group = Empty at origin, pick-walk ops, P parent **Maya mode** (keep world, parent inverse = identity; Blender mode as option), D/Insert pivot edit (Affect Only Origins / cursor) | P (group, walk, parent) / W (pivot) | H (matrices), M (pivot feel) | `maya/concepts.md` §6–§7, api_limits #7, decision 2 |
| 7 | M2-a | Layout, theme, units | App template `startup.blend` stored in `app_template/`, install/remove buttons; Maya grey theme preset; units option (cm display default; "1 BU = 1 cm" opt-in) | P | H (files copied/removed, unit settings), S | `maya/ui_layout.md` §2, `maya/workspaces.json`, `blender/ui_architecture.md` §2, decisions 1 & 3 |
| 8 | M2-b | Channel Box | Panel (TRS, visibility, custom props, shapes/inputs), channel selection rows, viewport MMB virtual slider, key/lock menu | P (panel, viewport MMB) / W (multi-select rows) / C (MMB on field) | H (values, slider math), S, M | `maya/channel_box.md`, api_limits #1 |
| 9 | M2-c | Status line, command line, time/range | TOPBAR append status line; Python command line; range slider fields; timeline theme/overdraw | P / W | H, S | `maya/ui_layout.md` §4.2, §4.10–4.12, api_limits #10, #12–#14 |
| 10 | M3-a | Marking menus (pie) | RMB / Shift+RMB / Ctrl+RMB pies per mode from `marking_menus.json` | W | H (menus registered, bindings), S, M | `maya/marking_menus.json`, api_limits #5 |
| 11 | M3-b | Custom marking menu engine + hotbox | Modal + GPU radial (flick, nested, linear list); Space hold hotbox, tap = maximize pane | W+ | H (hit-test math), S, M | `maya/hotkeys_and_menus.md`, api_limits #4–#5 |
| 12 | M4-a | Concept operators | Freeze Transforms (keep pivot), Reset, Center Pivot, Delete History (apply modifiers), Maya naming on create | P/W | H (matrices, names) | `maya/concepts.md` §4–§5, §13–§14 |
| 13 | M4-b | Outliner, Attribute Editor, Layer Editor | UIList DAG outliner with shape toggle; AE node tabs (sidebar + `prop_tabs_enum`); display layers over collections | W | H, S | `maya/attribute_editor.md`, `maya/channel_box.md` §3, api_limits #2–#3 |
| 14 | M5 | Shelf and menu sets | Shelf (header/panel/Asset Shelf), menu set switching of top menus | W | H, S | `maya/shelves.json`, `maya/menus.json`, api_limits #11 |
| 15 | — | Release | Legacy zip check, user docs, limitations page | P | H | decision 3 |

## Not possible (C) — documented, not implemented

Y-up world (IO axis conversion only), MMB-drag on UI fields, extending the built-in
transform gizmo, new region/editor types, Outliner tree drawing, timeline key drawing,
separate rotate/scale pivots, MEL. Source: `research/blender/api_limits.md` "Things that
are C-only". Decision 5: work around without forking; list what can't be done.

## Ordering notes (delegated)

- Steps 2–6 (M1) first: the keymap is what a Maya user touches every second, and later
  steps (marking menus, Channel Box MMB) bind keys through the same generator.
- Keymap strategy: a full "Maya" keyconfig generated from IC data for global behaviour,
  plus `keymap.add_item` overlays in the add-on keyconfig for feature-owned bindings, so
  that disabling the extension removes them (`tests/test_enable_disable.py`).
