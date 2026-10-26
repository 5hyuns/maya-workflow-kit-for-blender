# Step 225 — Animating a received rig: clips and motion trail (Issue #135)

Chain 5 of the animation chain (L19 was step 221): L24 Game Exporter clips, L21 Motion Trail Editor (Maya 2026 menus:
no "Create Editable Motion Trail"). Blender engines underneath (motion paths, actions / NLA); the Time Editor is not
rebuilt (user principle: Maya look, Blender engine).

## 계획

Two independent parts (game exporter / motion trail, separate modules); both small enough for the main session,
measured first:
- Maya Game Exporter (mayapy, `research/scripts/maya_anim225/game_exporter.py`, `$M/others/gameFbxExporter*.mel`):
  `gameFbxExporter` factory values; new clip = playback range, empty name, export on; unique names count up a trailing
  number keeping zeros; one file = file name (+ .fbx) with a take per clip; a file per clip = file name as prefix + clip
  name. Maya's files also hold the plug-in's `Take 001`, and the per-clip loop never clears the take list, so a later
  clip file repeats the earlier clips (measured: hero_run.fbx = Take 001, walk, run).
- Maya Motion Trail Editor (`$P/maya/app/motiontrail/MotionTrailEditor_res.py`, defaults in
  `MotionTrailPreferences.py:357-556`): 22 settings with factory values.
- Blender: the FBX writer makes a take per NLA strip, starting every take at time 0, and the same take name on two
  objects is written twice with the same ids; motion paths keep at least one frame before / after the current frame.

## 한 것

- `operators/game_exporter.py` (new): `Scene.allset_game_exporter` (Maya's fields + clip list), window
  `allset.game_exporter` (File > Game Exporter): Model / Animation Clips tabs, Export All / Selection, clip list with
  add (playback range) / delete, single file / file per clip, Export Settings mapped to the kit's Maya FBX preset
  (Skinning = armatures, Smoothing Groups, Tangents, Triangulate, Embed Media, Cameras / Lights, Up Axis), path + file
  name with a file preview. Clips are temporary NLA tracks during the write; `finalize_takes` merges same-named takes
  and moves each take to Maya's clip frames (keys and LocalTime / ReferenceTime by clip start / fps). Delegated: no
  `Take 001`, no repeated clips in later clip files; Blend Shapes / Move to Origin greyed (Blender always writes shape
  keys; Move to Origin not done).
- `operators/fbx_rig.py`: the step 222 rig rewrite now handles every take (`curve_nodes_all`, `channel_keys_all`) —
  a clip file has several takes.
- `operators/motion_trail.py` (new): `Scene.allset_motion_trail` (Maya's 22 settings), window
  `allset.motion_trail_editor` (Visualize > Motion Trail Editor, Windows > Animation Editors > Motion Trail Editor):
  Create Motion Trail (selected objects or pose bones; Maya's warnings for no animation / an existing trail), Delete
  Selected / All, Reset Settings, Save Settings as Default (add-on option settings), Update time range to match time
  slider. `to_blender` / `from_blender` map Path + Pre / Post Frames (0 = the whole Time Slider), Increment, key /
  frame numbers, Trail Thickness and Draw Mode Constant / Past/Future colours to Blender motion paths; the rest greyed
  with an info mark.
- Menus: File > Game Exporter, Visualize > Motion Trail Editor; Game Exporter notice says what differs.

## 검증 (속도 우선: 이 기능만)

- `test_step225_anim` 13 / 13: Game Exporter factory = Maya node (17 fields); new clip = playback range (preview range
  too); unique names (walk1, run10, run100, take0011, a010); file names = Maya (anim.fbx / hero_walk.fbx, hero_run.fbx,
  unchecked clips skipped); single file takes walk 1-10 / run 11-24 (= Maya minus Take 001), keys at frames 1 / 11;
  clip files one take each; two animated objects -> one take per clip; Maya's path / file name errors; motion trail
  factory = Maya; Create on the Time Slider 1-24, step 1, thickness 2; no-animation warning; Delete Selected; 9 option
  cases round trip through Blender; Reset / Save as Default; menu items.
- Related headless `-k step225,step222,step223,step138,step102,step101,step54,step166,enable_disable,step130,step147,
  step175` 128 / 128 (after rewording one notice for `test_step54`).
- GUI `gui_step225_anim` 3 / 3 (no other GUI file matches `anim`): Game Exporter (Animation Clips tab, walk / run,
  hero.fbx preview) and Motion Trail Editor shots checked; Create Motion Trail draws a path.

## 남은 것

- Editable trail (drag a key on the trail) not done — ATTACH_PLAN L21 (c) separate step.
- Motion Trail Editor window is taller than a 900 px window at UI 1.25 (the greyed colours are at the bottom, it
  scrolls); the info marks have no tooltip text (reasons are in `motion_trail.NO_BLENDER`).
- Game Exporter: Move to Origin, presets, Model tab "file per root" naming not checked against Maya.
