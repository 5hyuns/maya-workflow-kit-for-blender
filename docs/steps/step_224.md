# Step 224 — Paint Skin Weights: numeric weights, several skin clusters, remaining Tool Settings (Issue #134)

Rest of #126 (A3 numeric display, A4 several skin clusters, A7 Tool Settings fields); A1 / A2 / A5 / A6 were step 218.
Spec: `research/maya/re/maya2026_paint_skin_weights.md` §2 (frames, fields, ctx_defaults), §5 (numeric), §6 (skin
clusters). Decisions 5 and 7 (`docs/strategy/DECISIONS7.md`) followed as decided.

## 계획

Three parts, one file set (`ui/paint_weights.py`, `operators/weight_paint.py` are shared), so done in the main session
in order: fields + state props → numeric module → second-skin question / Skin Clusters list / export warning → tests.
- Numeric (decision 7): POST_PIXEL handler in every 3D View (not the Tool Box column), numpy projection of the
  evaluated (deformed) points, weights read only for the drawn vertices (`VertexGroup.weight`, cached), at most 2,000
  labels; more in view → only within 2 × brush radius of the pointer + Help Line note. Caches refresh after a depsgraph
  update, not while a weight paint stroke runs. The pointer comes from a first-place MOUSEMOVE item in "Weight Paint"
  (`allset.weight_numbers_hover`, PASS_THROUGH) — a `draw_cursor_add` callback gets no pointer position (tried: always
  None).
- Second skin (decision 5): Bind Skin on a mesh with a skin → Maya's question (title "Bind Skin Options", "There is
  already a skin cluster on <mesh>.\nDo you want to create another?"), Yes greyed, No, the Blender way (Add Influence /
  a hand-made second Armature modifier); nothing is bound (Maya's No cancels the bind).

## 한 것

- `operators/weight_paint.py` state: Maya frame defaults (Skin Clusters collapsed, Visualization open), `skin_cluster`,
  `normalize_mode` (Off / Interactive / Post over Auto Normalize + the mesh's normalize prop), `weight_type` (Skin Weight;
  DQ Blend Weight greyed: Blender has one dual-quaternion switch per Armature modifier), `min_value` / `max_value`
  (Flood clamps to them), numeric props (Show Numbers off, Decimal Places 2, Number Color yellow, Color Ramp off, 0 white
  → 1 black). Operators `allset.weight_skin_cluster`, `allset.weight_profile` (Gaussian / Soft / Solid = brush falloff;
  Square has no Blender brush → greyed).
- `ui/paint_weights.py`: Skin Clusters card lists every Armature modifier in stack order (read-only, the picked one
  filters the Influences list, a warning when there are several); Brush rows Profile / Weight Type / Normalize Weights,
  Opacity before Value like Maya, Min/Max value; Visualization > Numeric.
- `ui/weight_numbers.py` (new): the labels (module docstring), Help Line note through `command_line.draw_help_line`.
- `operators/skin.py`: `armature_modifiers`, `influences(mesh, mod)`, the question (`allset.skin_cluster_question`).
- `operators/file_io.py`: export warns when a mesh has several skins (`multi_skin_meshes`).

## 검증 (속도 우선: 이 기능만)

- `test_step224_paint` 9 / 9: 24 Tool Settings fields after the Maya reset = spec ctx_defaults (frames, Sort, Mode,
  operation, Profile, Weight Type, Normalize, Opacity, Value, Min/Max, numeric fields, Radius(U) 1 Maya unit, Reflection,
  X-Ray Joints); Normalize Off / Post / Interactive; Profile buttons; Flood Max 0.6; number format / ramp; 2,000 cap then
  brush-local; projection = `location_3d_to_region_2d`; second Bind Skin = CANCELLED with Maya's text, one skin, weights
  unchanged; two skins → list order, influence filter per skin, export warning list.
- Related headless `-k step224,step218_paint,step199_skin,step58,step140,step169,step101,step54,step166,keymap,
  enable_disable,step130,step138,step102,step223,step147,step129` 317 / 319 — the 2 failures (`test_step169_deform`
  Paint Weights option kind / Deform working share) fail the same on the step 223 commit (measured in a worktree):
  older than this step (likely step 219's Maya 2026 menus), left for Release prep.
- GUI `gui_step224_paint` 7 / 7 on a 19,842-vertex skinned sphere: whole mesh in view → 2,000 labels around the brush,
  Help Line "19842 vertices in view — zoom in …", steady draw 10–13 ms (cache refill frame 4–5 ms extra); zoomed in →
  78 / 78 labels, 1.1 ms; second Bind Skin opens the question (shots `tmp/gui_step224/*.png` checked: yellow 2-decimal
  labels, popup with Yes greyed). No other GUI file matches `paint` beyond `gui_step218_paint` (not rerun: speed rule).

## 남은 것

- Steady 2,000-label frame is 10–13 ms here, more than decision 7's 6.4 ms estimate (Python per-label loop); still under
  a 60 Hz frame. If a slower PC goes past 16 ms, expose the cap (decision 7's flip signal).
- Not done (delegated): Paint Select Add / Remove / Toggle row, Stroke Radius(L) (Blender brushes have one radius),
  Square / image profiles, Display "Multi-color feedback". Labels overlap when dense (Maya's do too).
- `test_step169_deform` 2 old failures (see above) for Release prep.
