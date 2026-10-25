# Step 197 — Small Maya polish batch (backlog #5, Issue #104)

Six small items from the step 192 dogfood + blindspots. Ran in order on the main line: each item is a few lines in
different files, and the parallel limit (≤ 2 lanes) would only have meant waiting on foreground agents.

## 한 것

1. **In-view message / In-View Editor under the hotbox** — `marking/draw.menu_up()` (= `ACTIVE` non-empty);
   `ui/view_message.draw` and `ui/in_view.draw_box` skip their draw while a marking menu or the hotbox is up (Maya's
   hotbox covers them). Dogfood `07_hotbox.png`: nothing drawn over the hotbox any more.
2. **Result field kept `Undo: Group`** (step 182 / 192 G4) — `command_line/undo_text._new_command()` runs from `_add`
   (every new kit / registered UNDO command): a stale `Undo: …` / `Redo: …` is cleared; a command with a result writes
   it right after (`results.result`). `Result: …` text is never cleared by a scan. F8 (`allset.toggle_sel_mode`,
   UNDO only, never registered) names its step via `undo_text.operator_step`. Delegated: a command without a result
   leaves the field empty (Maya clears it for commands that return nothing).
3. **AE tabs / menus / buttons cut** — `attribute_editor.wrap_rows(context, labels, equal=, extra_units=)` packs
   labels into rows by measured width (`blf` text + 1 widget unit of margin, + 1 unit for a menu arrow) against
   `content_width` (region − panel margins − Maya tab strip): aligned rows (tabs, Select / Load Attributes / Copy Tab)
   need n × the widest label, natural rows (menu bar, Focus / Presets / Show / Hide) the sum. Replaces the old
   4 + 3 menu-bar split. Delegated: Maya's 460 px AE scrolls its tab bar; the kit wraps (no text cut at any dock
   width). Dogfood `11_attribute_editor.png` (UI 1.25, narrow dock): nothing elided. The estimate is slightly
   conservative (pCube1 / pCubeShape1 on separate rows).
4. **Mesh > Cleanup… was Blender's Clean Up submenu** (arrow + box) — now a Maya leaf: `allset.poly_cleanup`
   (`operators/poly_cleanup.py`, bmesh: 4-sided / >4-sided / concave / non-planar faces triangulated, lamina
   duplicates deleted, zero-length edges and zero-area faces collapsed, zero-map faces deleted, nonmanifold edges
   split; Select matching polygons = component mode with them selected; result = Maya component names) + Maya's
   "Cleanup Options" window (`operators/option_windows_197.py`, factory values from performPolyCleanup.mel:58-126,
   spec `research/maya/re/cleanup_197.md`). Factory values change nothing, like Maya. [U]: non-planar tolerance
   (1e-3 × face size) and Maya's nonmanifold repair.
5. **Stale "Blender has no character sets" notices** — removed (Relationship Editors > Character Sets, Graph Editor
   Show > Objects > Characters) or rewritten (CATEGORIES `Control` / `Key` now name HumanIK / controller tags /
   character mapping and point at Create Character Set). New: Windows > Relationship Editors > Character Sets =
   `allset.character_editor` (popup: the character sets, click = current, current set's members with remove ×,
   Add / Remove Selected, Create); Graph Editor Show > Objects > Characters = check item
   `WindowManager.allset_show_characters` → the kit Graph Editor outliner lists CHARACTER rows (keying set, member
   F-curves incl. subcharacters) first. Dope Sheet Show > Objects > Characters stays greyed (Blender's own channel
   list; new notice). `rg 'no character sets' src` = 0.
6. **Panel Show > NURBS CVs / NURBS Hulls** — measured in a GUI 4.5 (tmp/p197 probe): overlay `display_handle` NONE
   and `vertex_opacity` 0 change 0 px of a NURBS surface / curve hull or CVs in Edit Mode, and Blender has no other
   overlay flag for them, so a toggle would be fake. They stay greyed; the existing notice already says this (comment
   added with the measurement). Deviation from the issue's suggestion, delegated.

## 검증

- New `tests/test_step197_polish.py` 14 / 14 (undo text replaced / Redo / Result kept / F8; menu_up; Cleanup window
  factory values, factory = no change, select + triangulate + result names, lamina, zero-length edge, concave only;
  notices; Graph outliner CHARACTER rows; AE wrap).
- Headless full **1778 / 1778** (220 files). Updated old expectations: test_step54 (Character Sets notice gone),
  test_step150_menus (Graph Editor Characters no longer greyed).
- GUI: `-k step52,step72,step99,smoke,switch,enable` 51 / 51; `step150_outliner,step187,step176,step65_extrude`
  44 / 44; `step11_outliner_ae,step135_width,step142_ui,step116_dock` 43 / 43.
- `python tools/dogfood.py` 48 / 48, console 0; shots 07 (hotbox clean, result field empty) and 11 (AE, no cut text).
- `tools/menu_count.py`: unique 751 / 1318 (57.0 %, was 750), Graph Editor 155 / 229 (was 154), greyed without
  notice 0; `tools/menu_consistency.py` 0.

## 남은 것

- NURBS CVs / Hulls: only a kit-drawn overlay could show them in Object Mode; Blender can't hide them in Edit Mode.
- Dope Sheet Show > Objects > Characters: Blender's channel list can't take kit rows.
- AE wrap estimate is a little wide (could share rows at UI 1.25).
