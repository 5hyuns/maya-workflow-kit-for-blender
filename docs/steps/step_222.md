# Step 222 — Rig FBX export matches Maya (joint orient as PreRotation) (Issue #132)

## 계획

Measured first (`tmp/p222/exp1.py`, kit export args, Blender 4.5): the armature is written as a `Null` (Lcl Rotation
−90 X, Lcl Scaling 100 — `bake_space_transform` does not reach armatures), LimbNode translations in metres under it,
the rest orientation (and the current frame's pose) in `Lcl Rotation`, no PreRotation. Maya 2026 writes joints with
jointOrient → `PreRotation`, rotate 0 at rest, translations in cm, no extra node (research/maya/re/maya2026_engine_fbx.md
L11-2). Decision 3: rewrite Blender's file with the bundled `io_scene_fbx.parse_fbx` / `encode_bin`.

Known / assumed / unknown (know-your-unknowns, short):
- Known: E2 + M2 (DECISIONS7 §3) — PreRotation + Pre⁻¹·R(t) curves open in Maya 2026 with jointOrient set, rotate 0,
  world positions equal. The rest must come from the **rest pose**, not the file's Lcl values (= the current frame).
- Assumption (riskiest): folding the Null (rotation R_N, uniform scale s) into the root joints keeps every world
  matrix — roots t' = T_N + R_N·(s·t), R' = R_N·R; every joint translation (default + curves) × s; bone world matrices
  in the bind pose / cluster TransformLink lose the scale (rotation part ÷ s). Checked by evaluating the written FBX
  (T·Pre·R·S chain) against Blender, and once in mayapy 2026.
- Unknown: armatures whose object itself is animated (the Null has curves) — then the Null stays (only PreRotation is
  applied); InheritType 2 (segmentScaleCompensate) — not written (Blender bones inherit scale fully, delegated).

Choices (delegated):
1. Rest values = a second, silent export of the same objects with every armature at `pose_position = 'REST'`,
   `bake_anim` off, into a temp file: the writer's own axis / bone-axis conventions, no re-derivation.
2. Kit Maya FBX preset for rigs: `primary_bone_axis='X'`, `secondary_bone_axis='-Y'` (Maya joints point X down the
   bone), `use_armature_deform_only=True` (Maya exports joints, not the kit's control bones / custom-shape controls —
   decision 1), `bake_anim_simplify_factor=0` (a key per frame like Maya Bake; also gives every channel the same key
   times so roots can be re-composed). Constraint-driven motion is baked by the writer's per-frame sampling.
3. Module `operators/fbx_rig.py` (pure tree maths + parse / encode); `file_io._write` calls it after an FBX export
   with Maya conversion when armatures were written; import fails → export without the rewrite and a warning line.

Verify: headless — export a rig with an animated root + skinned mesh, read the written file, evaluate joint world
matrices per frame from the FBX values (no Null, PreRotation = rest orientation, Lcl Rotation 0 at the rest pose,
cm) = Blender's within 1e-4 cm; mayapy 2026 imports it once (jointOrient / rotate / world positions / skinned vertex
positions per frame vs Blender) — numbers recorded here. Unity / Unreal: not installed on this PC → documented.

## 한 것
- `operators/fbx_rig.py`: mutable copy of the parsed tree (`Elem`), `Index` (models, OO parents, curve nodes),
  `fold_null` (armature Null with constant curves → roots: t' = T_N + R_N·(s·t), R' = R_N·R, all joint translations
  × s, bind-pose PoseNode / cluster TransformLink lose the scale, cluster Transform = TransformLink⁻¹·mesh world, the
  Null + attribute + its constant curves removed), `apply_prerotation` (PreRotation = rest, RotationActive 1, Lcl
  Rotation default / keys = Pre⁻¹·R with compat Euler), `world_matrices` (T·Pre·R·S evaluator for tests).
- `file_io`: Maya FBX preset adds `primary_bone_axis='X'`, `secondary_bone_axis='-Y'`, `use_armature_deform_only`,
  `bake_anim_simplify_factor=0`; `rig_fbx_maya` runs a second export at the rest pose beside the user's file
  (`<name>.rest_pose.tmp.fbx`, deleted at once — nothing written elsewhere) and rewrites the file. Missing
  `io_scene_fbx` → plain export.
- Not done (delegated): InheritType 2 (segmentScaleCompensate; Blender bones inherit scale fully), an animated
  armature object keeps its Null (only PreRotation applied).

## 검증 (속도 우선: 이 기능만)
- Headless `test_step222_rig_fbx` 4 / 4: no Null, control bone (use_deform off) not written, spine Lcl Translation
  5.385 cm on X, PreRotation set, frame-1 rotate keys ≈ 0, PreRotation independent of the export frame, cluster
  TransformLink unit columns, joint world positions from the file vs Blender over frames 1–10: max 5.8e-6 cm.
  `-k step102,step138,file_io,step130_package,step130_no_exec,step222` 48 / 48.
- mayapy 2026 (`research/scripts/maya_fbx222/check.py` on `tmp/test_step222/rig222_world.fbx`): assemblies
  `body, root` (no skeleton Null), joint world position error 5.1e-6 cm and skinned vertex error 9.5e-7 cm over frames
  1–10, jointOrient root (0, −21.80, 90) / spine (0, 43.60, 0) / head (0, −21.80, 0), rotate at frame 1 ≈ 0.
- Unity / Unreal: not installed on this PC — not checked. GUI export through the File menu not run (speed rule;
  the same `allset.file_export_all` operator runs in the test).
