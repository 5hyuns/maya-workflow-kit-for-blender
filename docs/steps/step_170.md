# Step 170 — Selection modifiers outside the 3D View

Backlog `backlog_164.json` #7 (재점검 11차 `step_163_remaining.md` §3 #5, README 대응표 "Shift 클릭=토글, Ctrl=해제,
Ctrl+Shift=추가" 행): Outliner / Graph Editor / Dope Sheet / UV Editor kept Blender's modifiers (Ctrl = toggle, no
XOR box, Outliner Shift not a range).

## 계획

1. Measure in a GUI Maya with QTest (`research/scripts/maya_sel170/`, method of `graph_editor_keys.md`): click and
   marquee × plain / Shift / Ctrl / Ctrl+Shift, two starting selections, per editor → `research/maya/re/select_mods_170.md`.
2. Keymap props where Blender has the option (Outliner `extend` / `extend_range`, Graph Ctrl = plain); elsewhere a
   first-place PASS_THROUGH operator that snapshots the selection and, after Blender's own item ran, writes the
   Maya result from (before, after) with pure set rules (`operators/select_2d.py` `RULES`) — no own picking or box
   drawing (delegated: Blender keeps its pick distances, tweak-to-move and box drawing).
3. Tests: headless per-editor tables (4 variants, measured Maya results), keymap order / props, state read / write
   on real keys and UVs; GUI: Graph Editor clicks / boxes, Outliner range and Ctrl toggle, screenshots.

Measurement had to come first (the rules differ per editor: the Graph Editor keeps the selection on a click on a
selected key and treats Ctrl+click like a plain click). Lanes were not split into sub-agents: one keymap file and
one operator module (delegated).

## 한 것

- Maya measurement (`research/maya/re/select_mods_170.md`, 4 editors × click / marquee × 4 variants).
- `operators/select_2d.py`: `allset.select_2d_click(editor, rule)` (PASS_THROUGH, a 0 s timer applies the rule after
  Blender's click: KEEP / CTRL in the Graph Editor, ADD in Graph / Dope Sheet, DESELECT in the Dope Sheet, TOGGLE in
  the Outliner) and `allset.select_2d_box(editor)` (PASS_THROUGH before the Shift box, which runs as SET; when the box
  modal ends a timer toggles its catch against the selection before = XOR; cancelled boxes / tweaks are left alone).
  Key state = every F-curve key of the file (`compat.id_fcurves`), UV state = UV corners (or vertices with UV sync).
- `keymap/maya_patches.py`: Outliner click = replace / Shift range / Ctrl toggle / Ctrl+Shift add range; Graph Ctrl =
  plain; Shift box of Graph / Dope / UV = SET (+ XOR op); NLA keeps the step 2 toggle rule; select_2d items first
  (`SELECT_2D_CLICKS`, `SELECT_2D_BOXES`, `PASS_THROUGH_FIRST`).
- `research/README.md` row "Shift 클릭=토글 …" → Done.

## 검증

- `tests/test_step170_select_mods.py` 8 / 8: click tables (Graph 8, Dope 8, UV 4 rows) and marquee tables (3 editors
  × 4) equal the measured Maya results; rules leave an unchanged selection alone; keymap items first with the right
  rules; Outliner props + Ctrl toggle rule; key / UV state round trips.
- `test_keymap_maya` 11 / 11 (shadowing: the new items declare their own keymap, Screen and View2D as intended
  shadows), `test_step86_select_modifiers` updated (Dope Sheet Shift box = SET + XOR op).
- GUI `gui_step170_select_mods` 10 / 10: Graph click / click on a selected key keeps 1 + 10 / Ctrl+Shift adds, Shift
  marquee toggles (1 + 20), Ctrl marquee deselects, Outliner Shift+click range pA1..pA3, Ctrl toggles pA2 off / pA4
  on; `gui_step86_select_modifiers` 10 / 10. Screenshots checked: Outliner range, Graph Editor after Ctrl+box.
- Event simulation trap (measured): `Window.event_simulate` copies no modifier into the window's event state, so a
  simulated drag's CLICK_DRAG and a Ctrl CLICK carry no modifiers (the plain box ran; no CLICK was made). The GUI test
  drives those two cases through the same operators in the editor region (kit op invoke + Blender's box / click);
  the keymap side is covered headless. Real modifier drags: `docs/manual_checks.md`.

## 결과

- Headless full **1586 / 1586** (169: 1579 + 7 new test functions net). GUI step170 10 / 10 + step86 10 / 10.

## 남은 것

- Outliner range anchor = Blender's active row (Maya: the last plain click; a Ctrl+click moves Blender's anchor).
- Graph Editor Ctrl+click = plain click is measured with QTest only; real-hand check in `docs/manual_checks.md`.
- NLA / Node Editor not re-measured (step 86 rules stay).
