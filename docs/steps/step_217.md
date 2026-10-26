# Step 217 — Anim chain fixes 1: Bake, joints, pick walk (Issue #128)

Basis: `docs/strategy/ATTACH_PLAN.md` rows L18, B1–B4, L20; `docs/strategy/DECISIONS7.md` decision 6;
Maya 2026 specs `research/maya/re/maya2026_joints.md`, `maya2026_anim.md` (L20), `maya2026_engine_fbx.md` (L18).

## 계획

Lanes (no two lanes edit the same lines; Blender processes ≤ 2 through `tools/blender_slots.py`):

| Lane | Files | Who |
|---|---|---|
| L18 Bake | new `operators/bake_maya.py`, `option_windows.py` (bake window), `menu_map.py` / `shelf_map.py` Bake rows, `tests/test_step217_bake.py` | sub-agent |
| L20 Pick walk + controller tags | `operators/joints.py` (walk section only), new `operators/controllers.py`, `preferences.py`, `menu_map.py` Control rows, `notices.py`, `tests/test_step217_pickwalk.py` (Rigify) | sub-agent |
| B1–B3 Joint Tool | `operators/joints.py` (tool section) | main, after L20 (same file) |
| B4 root joint in the Channel Box | `operators/joint_selection.py`, `ui/toolbox.py` | main |

### L18 Bake Simulation — Maya 2026 rules (mayapy, `research/scripts/maya_bake217/bake217*.py` → `.json`)

Measured with `bakeResults` and the menu's factory flags (cube `box` parent-constrained to a keyed locator, Time
Slider 1–10; sx key at 20, sz keys at 2.5 and 6):

1. Every keyable channel of a baked node gets a curve with a key on each sample (tx…sz **and visibility**), also
   channels nothing drives (ty constant 5, rx 0 …) — `default.curves`.
2. Samples = start, start + step, … ≤ end (step 2 on 1–10 → 1 3 5 7 9; 10 is not sampled) — `step2`.
3. Existing keys inside [start, end] that are not samples are removed (sz 2.5 / 6 gone) — every case.
4. Keep unbaked keys on: keys outside the range stay (sx 20); off: removed — `default` / `pok_off`. Constraints
   are never deleted by either.
5. Baking always disconnects the constraint from the baked channels (only `targetWeight` stays connected,
   `nodeState` 0): moving the driver afterwards no longer moves the node — both Disable implicit control on and
   off (`dic_off.pos_after_driver_moved`). The constraint node stays.
6. Disable implicit control = IK: baking the chain's joints without the handle sets `ikBlend` 0 when on
   (moving the handle afterwards changes nothing), keeps `ikBlend` 1 when off (the handle still drives); baking
   the handle too keys `ikBlend` instead (`bake217_ik.json`). Maya warns "<joint> cannot keep unbaked keys because
   it is controlled by ik."
7. Unroll Rotation on: rotation curves continuous (ry 0 … 350 in the test).

Kit translation (delegated where noted):
- `allset.bake_simulation` (menu Edit > Keys / Key > Bake Simulation, shelf, option window) — Blender's
  `nla.bake` (visual keying, current action, constraints kept, channel types LOCATION / ROTATION / SCALE / PROPS)
  then Maya's rules on the baked F-curves: remove in-range non-sample keys, Keep unbaked keys off = remove keys
  outside the range.
- Rule 5 = **mute** every non-IK constraint on a baked object / pose bone (Blender has no disconnect; a muted
  constraint is kept, shows in INPUTS as off, and the Channel Box no longer draws its channels blue).
- Rule 6 = an IK constraint (kit IK handle, step 58) whose chain has a baked bone and whose target empty is not
  baked gets influence 0 (step 159: ikBlend = influence) when Disable implicit control is on; untouched when off.
- Visibility (rule 1) is not baked: Maya visibility = `hide_viewport`, which nothing animates through a
  constraint (delegated).
- Result line: "Baked N node(s), frames a–b; constraints disconnected (muted): k".

### B1–B3 Joint Tool end (maya2026_joints.md §2–3)
- B1 finish selects the top of the branch just made (root of a new chain, or the existing joint clicked to branch
  from), active + only selection.
- B2 Enter = finish + Select tool (Q already, W/E/R their tools).
- B3 hit area = the drawn joint sphere: Blender draws an octahedral bone's joint point as a sphere of radius
  0.05 × the bone length (the incoming bone's length for a connected head) [I, Blender overlay_armature bone point
  shape]; screen radius = projected world radius, floor 5 px × UI scale (Maya click box, select_priority.RADIUS_PX).
  Stick display: the floor only.

### B4 (maya2026_joints.md §4)
When the automatic Pose mode (decision 16, `toolbox._auto_armature_tick`) enters Pose with no visible selected
bone, select the visible root bones (topmost bones not hidden by a collection) and make the last one active =
Maya Select > All lead = last root. Only when nothing was selected (delegated).

### L20 pick walk (decision 6)
- Armature with kit controller tags (`Bone["allset_controller"]`, parent `Bone["allset_controller_parent"]`):
  Maya rule — Up = controller parent, else DAG parent; Down = first tagged child, else first DAG child; Left/Right
  = controller siblings, else DAG siblings. No hidden skipping (Maya, M3/M4).
- Untagged armature + add-on pref `pick_walk_skip_hidden_collections` (default on): bones whose collections are all
  hidden are skipped — Up = nearest visible ancestor, Down = nearest visible descendants (depth-first, names
  sorted), Left/Right = visible siblings under the same visible ancestor. Bones hidden one by one (h) and objects
  are walked like Maya. Pref off = plain DAG (Maya).
- Control > Tag As Controller / Parent Controller (pose mode; Parent Controller = the lead is the parent).
- Measure on a generated Rigify human: % of visible controls whose Up lands on a hidden bone, before / after.

Order: L18 and L20 lanes run in parallel; B1–B3 wait for L20 (joints.py); B4 is independent.
