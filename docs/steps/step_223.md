# Step 223 — Rig FBX import and IK/FK switch (Issue #133)

ATTACH_PLAN L12 + L14, decision 4 D (DECISIONS7). Maya 2026 ground truth: `research/scripts/maya_rig223/make.py`,
`solver.py` (mayapy 2026, not tracked like the rest of research/); test data `tests/maya223/*.fbx` (Maya-exported,
Maya FBX defaults), `tests/maya223_rig_data.py`.

## 계획

Lanes: (A) FBX import post-process, (B) IK/FK commands — no shared files except `menu_map` / `notices`; both need
the one Maya process for ground truth, so the Maya runs were sequential. Done in the main session (small enough).

Measured first:
- Blender's FBX reader keys bones at the union of key times with **linear** interpolation
  (`$S/addons_core/io_scene_fbx/import_fbx.py:710-735, 851-890`): mid-key poses off up to 2.9-3.5 cm on the test rig.
  This is also the [U] 0.27 cm of DECISIONS7 §3 (step 222 round trip).
- Maya 2026 `auto` tangents (FBX flags cubic | auto, no slopes) = Blender **Auto Clamped + Continuous Acceleration**
  curve smoothing, within 4e-5 deg on six Maya curves (`tmp/p223/tan.py`). Other Maya tangents are written as user
  slopes (value / second) — free handles at 1/3 of the span; a key's left slope sits on the previous key unless the key
  is auto.
- With `bake_space_transform` the reader bakes the conversion into a skinned mesh but leaves it on the armature object
  (mesh 100 x too small = first_hour #37).
- Maya IK: the solver writes the solution into the joints' rotate; Ik Blend 0 uses those rotate values. Set IK/FK Key
  keys handle translate / rotate / scale / visibility (out step) / poleVector / offset / roll / twist / ikBlend (in auto,
  out clamped), chain joints' rotate + preferredAngle (out step), root translate, and adds a connected ikBlend to the
  chain joints. Enable IK Solver = global toggle (factory off) setting Ik Blend of the selected handles (or handles of
  selected joints) keeping the rotations; nothing selected = error. Move IK to FK = handle to the FK end joint.

## 한 것

- `operators/fbx_rig_import.py` (new): for each imported armature, from the file itself (bundled `parse_fbx`):
  Maya channel curves rebuilt with their tangents (scratch F-curves evaluated by Blender), bone correction C read at the
  earliest key frame (where the reader is exact), pose basis = K . (T . Pre . R . S) . C. Rotation: Maya curves copied
  1:1 into `rotation_euler` with the permuted Euler order (Maya xyz -> Blender YXZ for bone Y = joint X) when the rest
  matches PreRotation and C is a signed permutation, else keyed every frame as continuous XYZ Euler (decision 4 D:
  never quaternion). Translation copied 1:1 when the map is a scaled signed permutation, else per frame (a Maya root with
  jointOrient: per frame). Conversion moved into the bones (armature object identity), skinned meshes unparented with
  rotate 0 / scale 1, Time Slider = file TimeSpan, armature named `skeletonN`.
- `file_io`: rig files are read without `bake_space_transform`; `after_import` runs the fix and bakes the conversion of
  the other objects with `bake_conversion`.
- `operators/ik_fk.py` (new): Ik Blend = handle custom property `ikBlend` (0-1, default 1) driving the IK constraint
  Influence; the chain joints get a driven `ikBlend` (Maya's connection). `allset.ik_fk_key` (Set IK/FK Key: writes the
  solved pose into the bone channels, keys handle loc / rot / scale / hide_viewport (constant) / ikBlend (Maya clamped
  out slope), chain rotations, root location, preferred angle if stored; Maya auto = Auto Clamped + Continuous
  Acceleration), `allset.ik_solver_toggle` (Enable IK Solver), `allset.move_ik_to_fk`. `skin.create_ik` adds Ik Blend;
  Enable / Disable Selected IK Handles and Bake Simulation write Ik Blend through `ik_fk.set_blend`.
- Menus: Key > IK/FK Keys > Set IK/FK Key / Enable IK Solver / Move IK to FK mapped; notices for Connect to IK/FK
  (driver / Set Driven Key) and Skeleton > Enable IK/FK Control (always on in Blender).

## 검증 (속도 우선: 이 기능만)

- `test_step223_rig_fbx_import` 6 / 6: Maya rig joint world positions frames 1-24 max **1.2e-5 cm** (Blender reader
  alone 3.5 cm); every Maya rotate curve = one Blender Euler curve, values equal per frame (1e-3 deg), key frames equal
  to Maya's own import; quaternion-interpolated spine (Maya resample) pose 1e-3; skeleton identity, mesh unparented,
  range 1-24; skin vertices vs Maya skinCluster max 0.0101 cm (10 cm body); kit step 222 FBX round trip **1.3e-5 cm**
  (the 0.27 cm [U] is gone — it was the reader's linear sampling).
- `test_step223_ik_fk` 7 / 7: Ik Blend row + driver, joint ikBlend like Maya (shoulder, elbow); pose at blend 1 and
  after switching to 0 + shoulder rz 30 equal mayapy within 2e-3; Set IK/FK Key channel set (Maya's minus pole /
  offset / roll / twist / preferredAngle), Ik Blend at frame 5 = Maya 0.44582 within 1e-4, visibility step; Enable IK
  Solver on / off / via a joint / error text; Move IK to FK = spec (6.99, 3.88, 0.25) and mayapy (6, 0, 2); undo.
- Related headless `-k step223,step58,step159,step217,step140,step138,step102,step222,step130,step101,step54,step166,
  step147,enable_disable,step110,step208,step216` **233 / 233**.
- GUI `gui_step223_ik_fk` 6 / 6 (no existing GUI file matches fbx / ik): Channel Box shows Ik Blend last like Maya
  (shot checked), the three menu items run from their Maya paths, one undo step.

## 남은 것

- Not keyed / not mapped (delegated): handle Pole Vector X/Y/Z, Offset, Roll, Twist (no Blender channels); Connect to
  IK/FK (notice); the Enable IK Solver menu check mark isn't drawn (session state only, not Maya's saved optionVar);
  Ik Blend between 0 and 1 blends matrices (Blender) — only 0 / 1 checked against Maya.
- Old files' IK handles get Ik Blend when an IK/FK command or Bake touches them, not on load.
- Rig import: weighted tangents read as non-weighted; a root joint under another node is left to Blender's reader;
  segment scale compensate / scale animation mapped by nearest axis only; skin 0.01 cm residual not chased.
- Kit-wide: Maya auto = Auto Clamped + Continuous Acceleration could replace the step 70 Auto mapping
  (`time_keys.TANGENTS`) — for Release prep / a later step.
