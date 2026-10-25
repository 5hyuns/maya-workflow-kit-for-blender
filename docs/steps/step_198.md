# Step 198 — Graph Editor depth 2 (backlog #6, Issue #105)

## 계획

Measured first (`research/maya/re/graph_editor_193.md`): Retime Tool in a GUI Maya (QTest drags), weighted /
non-weighted tangents, weight lock, buffer swap in mayapy.

Lanes (files owned by one lane each; prefs / registration / menu maps / notices done by the main line):

- **R (agent)** `operators/graph_retime.py`: pure `retime_map(markers, index, new_time)` (spec §1) + window modal
  `allset.retime_tool` in Graph Editors (double-click = marker, handle drag = retime with live preview, line drag below
  the handle = move marker, ✕ = delete, Esc / Q W E R T = leave), POST_PIXEL drawing (yellow lines, handle, ✕,
  bracket), pref `retime_snap_on_frame`. Tests `tests/test_step198_retime.py` (measured cases exact).
- **B (agent)** `operators/graph_buffers.py` (Snapshot / Swap / Show Buffer Curves: buffer stored on the Action as an
  ID property, drawn grey in Graph Editor POST_VIEW while pref `graph_show_buffers`) and `operators/graph_weights.py`
  (Weighted / Non-weighted Tangents, Default Tangent Weight via pref `default_tangent_weight`, Lock / Free Tangent
  Length; a `watch(context)` called from `ui/graph_view._tick` keeps non-weighted arms at Δt/3 and locked arms at
  their length after edits). Tests `tests/test_step198_curves.py` (mayapy values within 1e-4).
- **Main**: sidebar of Graph Editors in main panes (`ui/graph_view.hide_sidebars`), Select Unsnapped, Select Curve
  Nodes, Set Curve Colors..., Add Key Tool, Pin / Unpin Channel; menu maps, notices, option window for the Retime
  Tool, docs.

Order: measurement before lanes (the specs come from it); menu mapping after the lanes (needs their operator ids).

## 한 것

- **Measured first** (`research/maya/re/graph_editor_193.md`): Retime Tool in a GUI Maya 2022 with QTest drags
  (`research/scripts/maya_ge198/`, frame↔pixel from the key diamonds in a screen grab; `retimeHelper -moveFrame`
  moves no key, only the manipulator drag does), weighted / non-weighted tangents, weight lock, buffer swap
  (`research/scripts/graph_editor_198_mayapy.py`).
- **Retime Tool** (lane R, `operators/graph_retime.py`, `allset.retime_tool`): double-click = marker, handle drag =
  scale + ripple (measured cases exact), low line drag = move marker, ✕ = delete, Esc / Q W E R T end; Snap On Frame =
  pref `retime_snap_on_frame` (Maya factory off). Works in the Graph Editor and the Dope Sheet (main line). Delegated:
  a marker can't reach its neighbour (≥ 0.01 / 1 frame), handles x go through the same time map, action time (NLA
  offsets ignored), the tool ends CANCELLED (each drag pushed its own undo step).
- **Buffer curves** (lane B, `operators/graph_buffers.py`): Snapshot / Swap on the Action ID property
  `allset_buffers` (undoable, saved), View > Show Buffer Curves = pref `graph_show_buffers` (factory off) draws grey in
  Graph Editor POST_VIEW (GUI shot). Replaces Blender ghost curves in the kit menu / toolbar.
- **Tangent weights** (lane B, `operators/graph_weights.py`): Curves > Weighted / Non-weighted Tangents
  (`allset.curve_weights`; non-weighted = arms Δt/3 keeping the angle, Maya-equal within 1e-4), Default Tangent
  Weight = pref `default_tangent_weight` applied to curves the kit creates (`graph_key_menu.after_insert` →
  `graph_weights.apply_default`), Tangents > Lock / Free Tangent Length (`allset.tangent_weight_lock`), `watch()` from
  `ui/graph_view._tick` keeps non-weighted / locked arms after edits. Delegated: curves without a mark are weighted
  (Blender's nature); only FREE / ALIGNED arms are rewritten; an arm longer than its interval can't match Maya
  (Blender shortens it — measured gap 0.1 on Maya's ow = 6 case).
- **Main line**: Graph Editors in main panes close Blender's sidebar once per area (`graph_view.hide_sidebars`; N
  reopens it); Edit > Select Unsnapped (`allset.select_unsnapped`), Edit > Set Curve Colors... (`allset.curve_colors`
  popup, rules in pref `curve_color_rules`, user colours win, removing a rule restores the automatic colour), Keys >
  Add Key Tool (`allset.add_key_tool`: middle click = key at the frame and value under the mouse);
  `operators/graph_menu_198.py`. Dope Sheet twins mapped (`editor_menu_map._depth2`), toolbar buttons (retime, buffer
  snapshot / swap, lock / free tangent) wired, stale notices removed.

## 검증

- Headless: `test_step198_retime` 11, `test_step198_curves` 11, `test_step198_menu` 8 — all pass; full **1807 / 1807**
  (223 files; updated old expectations in test_step150_menus, test_step161_messages).
- GUI: `-k step198,step92,step150,step157` 42 / 42 (retime drag 15→20 = 1 5 12.5 20 25 35, Ctrl+Z one step; sidebar
  closed; buffer shot `step198_buffer.png`, swap brings the snapshot back); smoke `smoke,switch,enable,layout` 45 / 45.
- Maya values: retime cases exact; weighted conversion / non-weighted reset / weight lock within 1e-4 / 1e-5.
- `tools/menu_count.py`: Graph Editor **167 / 229** (was 155), Dope Sheet 139 / 181 (was 130); unique 751;
  `menu_consistency` 0.

## 남은 것

- Pin / Unpin Channel and List > Load / Add Selected Objects: need the kit outliner + Blender's only-selected filter +
  per-curve hide working together (not done; notices stay).
- Retime with Snap On Frame off: Maya's measured fractional drag moved nothing [U]; the kit retimes continuously.
- Buffer grey colour not measured from Maya; easing interpolations drawn straight.
