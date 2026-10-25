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
