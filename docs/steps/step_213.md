# Step 213 — Component, Shape and Connection Editors (Issue #119)

Source: `docs/steps/step_210_remaining.md` NB12 — Windows > General Editors > Component Editor opened Blender's
Spreadsheet (read-only, no skin weights), Shape Editor the Properties Data tab, Connection Editor the Drivers editor.
Maya spec: `research/maya/re/editors_213.md` (GUI Maya capture + mayapy).

## 계획 (delegated)

- Measure first (one Maya at a time): GUI Maya capture of the three windows (`research/scripts/maya_editors212/`
  `editors212.py` → `research/maya/screens/editors212/`: menu bars, widgets, tab bars, table / tree headers and rows,
  shots), pass 2 `actions212.py` (Polygons tab values, toolbar buttons — the Shape Editor buttons and the table cell
  edit can't be driven through Qt), mayapy `research/scripts/naming_211/editors213_mayapy.py` (blendShape create / Add
  Target naming / sculpt delta / weight blending, skinPercent -transformValue normalisation, connectAttr follow /
  break).
- Windows: one shared mechanism `ui/marked_window.py` — the Reference Editor's (step 209) Properties Tool tab marked by
  hidden tab flags, a distinct flag pair per kind (no overlap with the dock roles, Hypershade panes or the Reference
  Editor); `dock_tabs` / `tool_settings` skip them. Menu bars = capture data (`tools/gen_editor_menu_data.py` +
  `EDITORS_213` → `ui/editor_menu_data.py`), actions in `editor_menu_map`, greyed items with notices.
- Concepts: Component Editor = selected vertices' object-space positions (Maya units) and skin weights (vertex
  groups of the skeleton's bones, Hold = vertex group lock, Maya's proportional normalisation); Shape Editor = a mesh's
  Key datablock as the blendShape node (`blendShapeN`, as Deform > Blend Shape names it), key blocks = targets,
  Edit = the shape key edited in Edit Mode; Connection Editor = drivers with one `cn` variable (unit conversion like
  Maya's unitConversion nodes).
- Lanes: (1) main — capture, mayapy, generator + `marked_window`, Connection Editor, menu wiring, notices, GUI test;
  (2) Component Editor and (3) Shape Editor = two subagents in their own worktrees (separate files and `dist/`, so their
  test builds don't race), merged by the main session. Sequential only: the GUI capture before the mayapy run (one Maya
  process at a time).

## 한 것

- **Measurements** (`research/maya/re/editors_213.md`): capture of the three windows (menu bars, tabs, tables, shots in
  `research/maya/screens/editors212/`), Polygons tab = object-space positions, Smooth Skins = influences + Total + Hold,
  Shape Editor rows / columns, Add Target naming (`pCube2`, `pCube3`, a freed name reused), weight 1 + Edit on add,
  sculpt delta + linear weight, skinPercent proportional normalisation, connectAttr follow / break.
- **Windows** (`ui/marked_window.py`): `KINDS` flag pairs, `open_window` / `find_window` / `context_kind` / `close_later`
  / `allset.marked_window_close`; `dock_tabs` and `tool_settings` skip them. Windows > General Editors > Component
  Editor / Connection Editor and Windows > Animation Editors > Shape Editor open them (`menu_map`; the Sculpting shelf's
  Shape Editor button follows through `shelf_map`).
- **Component Editor** (`ui/component_editor.py`, lane CE): 8 Maya tabs (Smooth Skins / Polygons working), Hold row =
  vertex group lock, Hide Zero Columns, Total, 3 decimals, editable Scene proxies (undo), Maya's proportional
  normalisation (`normalize`), positions in Maya units, Auto Update (depsgraph → one 0 s timer while a window is open),
  Load Components / Close.
- **Shape Editor** (`ui/shape_editor.py`, lane SE): blendShape = the mesh's Key (`blendShapeN`), tree of node + target
  rows (visibility = mute, rename, weight field + slider, red Edit, Key), Create Blend Shape, Add Target (Maya naming,
  weight 1, Edit on), Add Selection as Target (Maya script: weight 0, no Edit), Edit (active shape key, one at a time),
  Key, Reset, Duplicate (`_Copy`, `_Copy1`), Flip, Mirror.
- **Connection Editor** (`ui/connection_editor.py`): Reload Left / Right, Outputs / from -> to / Inputs, two attribute
  lists (visibility, translate / rotate / scale compounds, custom attributes), Auto-connect pick (connect / break),
  Make / Break / swap / Clear All / Remove / Close; a connection = a driver with variable `cn` and Maya's unit
  conversion (translateX 3 cm → rotateX 3°); `connect` tags the source (a custom attribute written after the last
  evaluation made the driver invalid — measured).
- Menu bars: `tools/gen_editor_menu_data.py` `EDITORS_213` → `ui/editor_menu_data.py`; actions in `editor_menu_map`
  (Options checks as `("prop", ...)`), greyed items with notices (`notices.py`).

## 검증

- Headless: `test_step213_component` 13 / 13, `test_step213_shape` 11 / 11, `test_step213_connection` 5 / 5 (mayapy
  numbers: CE5 normalisation, SE5 naming, SE7 weight blending, CN3 follow / break), menu rules `test_step101` /
  `test_step166` / `test_step104` / `test_step54` pass, `test_enable_disable` / `test_step147_undo` pass; full headless:
  first run 2059 / 2061 (a Help path Maya doesn't have), fixed + the 7 affected files 78 / 78 → **2061 / 2061**.
- GUI `tests/gui/gui_step213_editors.py` 12 / 12 (each window opens from the Windows menu with one area, no Blender
  header, its Maya menus registered; Create Blend Shape + Add Target; a Connection Editor pick connects translate);
  related + smoke (`step209_reference`, `step116_dock`, `step5_layout`, `step60_switch`) 55 / 55 together.
  Shots looked at: `tmp/shots213/gui_step213_component_editor.png` (Smooth Skins joint1 / joint2 / Total, Hold off,
  vtx[0–3] 0.800 / 0.200 / 1.000), `gui_step213_shape_editor.png` (blendShape1 ▸ pCube2 1.000, red Edit),
  `gui_step213_connection_editor.png` (pCube1 → pSphere1 translate with X / Y / Z marked).
- `python tools/menu_count.py`: main menu unique 804 / 1319 (the three Windows items were counted as working before and
  now open the real editors); editor menu bars 676 / 952 → **720 / 1036** (Component Editor 13 / 23, Shape Editor
  18 / 30, Connection Editor 13 / 31).

## 남은 것

- Component Editor: the other six tabs (Springs, Particles, Weighted Deformer, Rigid Skins, BlendShape Deformers,
  AdvPolygons) are drawn disabled; the bottom value field / slider for selected cells (CE4) is missing; no cell
  selection model (Show Selected Columns / Objects greyed).
- Shape Editor: no in-between / combination targets (Blender has none), no multi-select of rows, no Merge / Rebuild.
- Connection Editor: only attributes with a Blender counterpart; Outputs / Inputs modes only swap the direction;
  Left / Right Display filters greyed.
- `research/maya/screens/editors212/` pass 2 couldn't press the Shape Editor toolbar buttons through Qt: the Add Target
  rules come from mayapy + the installed scripts.
