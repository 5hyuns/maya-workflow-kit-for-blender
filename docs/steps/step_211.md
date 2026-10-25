# Step 211 — Audit 16 fix batch (Issue #117)

Sources: `docs/steps/step_210.md` 「메인 GUI 관찰」 G1–G2, `step_210_remaining.md` NB13 / NB15, `step_210_quant.md`
§2 / §7 #5. Maya data: `research/maya/re/naming_211.md` (mayapy + GUI Maya).

## 계획 (delegated)

Lanes: (a) Maya measurements (mayapy numbering / paste / startup cameras, GUI Maya paste + bookmarks — one Maya at a
time) → (b) names + paste code; (c) Light Linking menu, nHair option boxes, AE tab row (independent, small); (d)
Outliner order (design below). Sequential only where (b) needed (a)'s numbers. Done in the main loop (each lane a
handful of files; the Blender / Maya process limit allowed one measurement at a time anyway).

Outliner order — options weighed (Blender's Outliner is C; Python can't insert rows above its object rows):
1. Drawn camera rows (step 99): stay after Blender's rows — the audit finding itself.
2. Shift Blender's rows by repainting them 4 rows lower: every click / drag / rename / RMB would hit the wrong row.
3. A separate strip area for the cameras: layout surgery (template, fit, tear-off Outliner windows).
4. **Real hidden camera objects persp / top / front / side** in a new Maya scene (chosen): Blender's own rows, so
   click / select / rename work; a click makes persp the lead (Channel Box shows `persp`, Visibility off) like Maya.
   Costs handled: `hide_render`, kit Export All leaves them out (`startup_cameras.excluded`), Edit > Delete refuses
   them with Maya's message, the render persp camera (step 137) is the startup persp.
   Ordering needs Sort Alphabetically off — and there Blender sorts each list with an unstable `qsort` (all rows
   compare equal); on Windows a 2–8 row list shows rotated left by one (measured, naming_211.md "Blender side").
   `ui/outliner_order.py` links each sibling list pre-rotated so the rows show creation order.

## 한 것

1. **Light Linking (NB13)** — `ui/menu_map.py`: Windows > Relationship Editors > Light Linking is Maya's submenu
   (startup/WindowMenu.mel:597-612) Light-Centric / Object-Centric → `allset.light_linking_editor` in that mode (the
   step 179 editor of Lighting/Shading > Light Linking Editor), no longer the Properties Object tab.
2. **Names (NB15)** — mayapy: set / display layer / anim layer / character and GUI Maya: bookmark nodes all count one
   past the highest (N1–N5). `operators/sets.py next_name`, `ui/layer_editor.py next_layer_name`,
   `operators/anim_layers.py unique_name`, `operators/character_sets.py next_name`, `operators/bookmarks.py next_name`
   use `naming.next_number`; `naming.py` docstring updated. Bookmarks keep the kit's `bookmark<N>` label (Maya's node
   is `timeSliderBookmark<N>` with an empty name; delegated).
   **Ctrl+V** (`operators/global_keys4.py`) = Maya pasteScene: every pasted object `pasted__<name>` (shape numbered
   with its transform), the top nodes under a new `group` / `group1` … at the origin, only the group selected
   (P1–P3, mayapy + GUI Maya). A clashing name counts up (`pasted__pCube2`) — Maya repeats the short name under
   the new group, Blender names are global (delegated).
3. **Outliner (G2)** — `operators/startup_cameras.py`: `first_start.new_maya_scene` gives the scene Maya's startup
   cameras (values C2, Y-up → Z-up, × `maya_unit()`, hidden, not rendered); `ui/maya_outliner.setup` and the template
   (`tools/make_startup.py`, regenerated) turn Sort Alphabetically off; `ui/outliner_order.py` (0.25 s timer,
   Windows, Maya Outliner shown, one scene collection, no Blender modal / edit mode / local view) numbers objects
   (`allset_dag_order`) and links them so Blender shows persp, top, front, side, then creation order, children in
   creation order (only the top list is rotated by Blender — child lists draw in link order, measured);
   `ui/outliner_sets.py` draws only cameras the scene lacks (other files keep step 99's rows). Re-parenting (P,
   Shift+P, Outliner LMB / MMB drops) puts the node last among its new siblings like Maya (`parenting._to_end`);
   an Outliner MMB drop between rows renumbers that sibling list (`outliner_order.place`) instead of step 82's
   link-order model, which stays for Outliners with collection rows.
4. **AE (G1)** — `ui/attribute_editor.py draw_tab_strip`: one left-aligned row of tabs at their text width
   (`tab_window`); a dock too narrow shows the tabs around the current one with ◀ ▶ (previous / next tab — Qt's
   arrows only scroll; delegated). The dock width fit (step 142) re-checked with `ALLSET_FIT_WARP=1`: AE 600 px at
   1.25 (= rule), five tabs fit (523 / 545 px), Select / Load Attributes / Copy Tab one row (the dogfood shot had the
   Channel Box width because dogfood sessions don't fit the dock).
5. **nHair option boxes (quant §2)** — `operators/option_windows.find_path`: a `menu_map.TWINS` path uses its
   source's window, so nHair > Modify Curves > Bend / Curl / Scale Curvature ❒ open the Curves windows.

## 검증

- mayapy / GUI Maya measurements: `research/maya/re/naming_211.md` (N1–N5, P1–P4, C1–C3).
- Headless `tests/test_step211_fix_batch.py` **13 / 13** (menu, names vs mayapy sequences, paste names / group /
  selection / world position, startup camera values / hidden / order / delete refusal / export exclusion / state
  kept, rotation rule round trip, sync with children and a kit set, AE tab window, nHair windows); updated
  `test_step90_global_keys` (paste), `test_step96_sets` / `test_step187_character_sets` (max + 1).
- GUI `tests/gui/gui_step211_fix_batch.py` **10 / 10** at 1.25: rows clicked top-down = persp, top, front, side,
  pCube1, pSphere1 (before the order fix the same scan read persp, top, front, pCube1, pSphere1, side — exactly the
  CRT short sort of that link order); drawn rows default sets + set1 after 6 Blender rows; AE dock 600 px, tabs one
  row, bottom buttons one row (shots `tmp/shots211/`, looked at).
- `python tools/menu_count.py --options`: unique 804 / 1319 (Light Linking = 2 leaves), window 176 → **179**,
  generic 28 → **25**.
- First full headless run 2030 / 2031 (test_step5 expected an empty new scene → now the four startup cameras);
  related GUI + smoke first run 139 / 156 — old-behaviour expectations updated (step 5, 90 paste, 96 / 99 row
  positions, 137 render persp = startup persp) and one real conflict fixed: step 82's MMB reorder was undone by the
  order timer → `outliner_order.place` / `to_end`; child lists turned out not to be rotated (top list only).
- Final: headless full **2032 / 2032**; GUI related + smoke (step 211, 11, 129 switch, 137 render, 142 ui, 170, 179,
  180, 187, 203 outliner, 31 / 49 / 5 layout, 60 switch, 82 outliner drag, 90, 96, 99) **160 / 160**; dogfood
  **48 / 48**, console 0 (shot 01 / 05: persp top front side first; 11: unfitted narrow dock = ◀ pCubeShape1 ▶).

## 남은 것

- Files not made by the kit's New Scene (Blender files, files opened from disk) have no startup cameras: the drawn
  camera rows still follow the objects there (delegated). A Maya-mode command to add them could come later.
- Outliner order compensation needs one scene collection; objects spread over several collections keep Blender's
  (rotated) order. Re-parenting keeps an object's creation rank (Maya appends it to the new parent's children).
- Ctrl+V: materials and other non-object data aren't renamed `pasted__`.
- Blender 5.x: same `qsort` in 5.0.1 source; run the step 211 GUI file on 5.x in step 212.
