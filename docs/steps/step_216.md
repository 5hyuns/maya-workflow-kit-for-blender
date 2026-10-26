# Step 216 — maya.cmds look-alike 3 (Issue #122)

Source: `docs/steps/step_208.md` 「Left」 + `docs/steps/step_210_remaining.md` U2 (28 functions, Script Editor History
0 / 13). Maya truth: `research/maya/re/cmds_201.md` 「step 216」 (mayapy, 14 new cases `c216_*` in
`research/scripts/cmds_201/cases.py`, data `tests/maya201_cmds_data.py`).

## 계획 (delegated)

- Lanes: (A) mayapy cases ∥ (C) Script Editor History options; then (B1) `command_line/cmds_rig.py` ∥ (B2)
  `command_line/cmds_misc.py` against A's data; main = stubs registered in `cmds_shim.py` first (so the two lanes
  never edit the same file), wiring, DEVIATIONS, tests. Sequential only: B needs A's ground truth.

## 한 것

- **mayapy** (14 cases, the 23 old ones unchanged): constraint nodes are named after the constrained object at
  creation (`pSphere1_parentConstraint1`; a rename doesn't rename them, a repeated command returns the same node),
  `W<i>` weight aliases, removing the last target deletes the node; `joint` takes world positions and parents under
  the selected joint (or the selected mesh transform); `connectAttr` returns Maya's message text; `makeIdentity
  -apply` also freezes children; `currentUnit` pal rescales the playback range; `shadingNode` makes no shading group
  and selects the new node; `polyExtrudeFacet` → `['polyExtrudeFace1']`. The constraint DAG nodes are left out of the
  mayapy scene snapshot.
- **`cmds_rig.py`**: `makeIdentity` (= `freeze.freeze` / `freeze.reset`), `parentConstraint` / `pointConstraint` /
  `orientConstraint` / `scaleConstraint` / `aimConstraint` (one Blender constraint per target with influence
  w_i / Σw, Child Of for parent / maintain offset, aim = Track To in the space of a hidden world-up empty; node names /
  weights in the object ID prop `allset_cmds_nodes`; q / e / w / rm / targetList / weightAliasList / offset / n /
  skip flags, RuntimeError on driven channels), `joint` (kit skeleton bones, Maya names, parent rules, radius /
  jointOrient as bone props), `connectAttr` / `disconnectAttr` / `isConnected` / `listConnections` /
  `connectionInfo` (step 213 `cn` drivers; texture → material through `cmds_misc.connect_texture`), and
  `intercept` (getAttr / setAttr / xform / listRelatives / ls / select / delete / objExists see joints and
  constraint nodes, constrained channels read evaluated values).
- **`cmds_misc.py`**: `nodeType` / `objectType` (DAG, shapes, plugs, materials, file nodes, sets, shading groups, time1,
  creation / extrusion nodes, constraints, joints; `inherited` chains), `attributeQuery`, `currentUnit` (scene length
  unit / rotation / fps, ranges rescaled to whole frames), `sets` (`operators/sets.py`, Maya numbering and query order),
  `shadingNode` (kit materials; `file` = a fake-user node group with an Image Texture node — delegated),
  `polyExtrudeFacet` (kit extrusion with Maya face ids + step 65 record), `polyEvaluate`, `exactWorldBoundingBox`,
  `listHistory`, `camera`; it extends the shim's ls / select / getAttr / setAttr / objExists for non-DAG nodes.
- Shim / kit edits: `cmds_shim.move` takes `-os` with `-r`; `_guarded` calls `cmds_rig.intercept`; `freeze.freeze`
  carries a child's pivot offset into its parent's new frame when only rotate / scale is frozen (Maya; also GUI Freeze).
- **Script Editor History** (13 items, `preferences.se_*`, factory states from the Maya capture): Echo All Commands
  (the kit's Python call for every menu / shelf / marking command, `marking/modal.run_action` → `runner.echo_action`),
  Line numbers in errors, Show Stack Trace (`<maya console>` frames, kit frames dropped), Suppress Command Results /
  Info / Warning / Error, History Output Show Both / MEL / Python; Batch Render Messages / Suppress Stack Window /
  Duplicate Variable Messages stored only. Script Editor editor menu 32 / 59 → 45 / 59.

## 검증

- `test_step208_cmds`: **37 / 37 cases match mayapy** (with DEVIATIONS, each with its reason: constrained channels
  keep the object's own values under Blender constraints; joints are skeleton armatures; frozen parent pivot in
  `delta_location`; whole frames for pal; Z-up bounding boxes; no particleCloud1 / standardSurface1; camera levelled).
- `test_step216_history` 10 / 10; related headless (`-k step208_cmds,step216,step10,step130,step114`) 167 / 168 — the
  one failure was an intermittent Blender crash (EXCEPTION_ACCESS_VIOLATION in python311 GC) in
  `test_step216_history`; 4 reruns pass (1 crash in 5 runs). Full headless **2111 / 2111** (4.5.4).
- GUI: `-k step216_script,step208_script,step105,step213_editors,step60_switch,step49_layout` **61 / 61**; shot
  `tmp/shots216/gui_step216_history.png` checked (Show Stack Trace on: `# Error: ... line 2`, traceback lines, the
  echoed Create > Cube call).

## 남은 것

- Intermittent python311 crash seen once in `test_step216_history` (headless, text.run_script path) — watch it.
- Constraint channels: Blender keeps the object's own values under constraints (Maya's channels show the result); aim
  with mo and world-up object types other than vector / scene / none raise "not supported"; several orient / parent
  targets blend through the constraint stack (only point is measured).
- Script Editor: echo prints Blender Python calls, not Maya runTimeCommand names; Maya's exact error / trace layout is
  [K] (GUI Maya not checked); component commands outside `run_action` aren't echoed.
- `currentUnit -t` doesn't re-time keys; extrusion side-face order = bmesh's; `allset_cmds_history` isn't cleared by
  Delete History.
- Per the user's 2026-10-26 product principle (`docs/user_decisions.md`), the maya.cmds look-alike stops here.
