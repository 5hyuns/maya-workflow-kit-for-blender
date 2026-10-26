# Step 220 — User report #139: snapping does not move (Issue #139)

## 원인
Blender's `use_snap_translate / rotate / scale` ("Snapping > Affect") switch **every** snap mode off for that
transform, not only the increment. The kit's Step Snap Off (Tool Settings Move / Rotate / Scale, and Reset Tool,
`snap_align.set_step_snap`) cleared that flag, so after it Snap to Grid / Snap to Points on the Status Line showed on
(`status_line.snap_on` only reads `use_snap` + elements) while Move never snapped — the report's screenshot (edit mode,
Move manipulator, snap icons on). Scene carry (step 138) then copied the broken flag into every opened file.

## 한 것
- `snap_align.set_step_snap`: Step Snap state per tool kept in the scene ID property `allset_step_snap`; Off leaves the
  Affect flag on while any grid / point / curve / live snap is on, drops INCREMENT only when no other tool steps.
- `snap_align.heal_affect`: Status Line snap buttons, file load (`scene_carry`, which now also carries the Step Snap
  record) turn the Affect flags back on when a non-increment snap is on; X / C / V holds set them for the hold and
  restore them after (`hold.SnapGroup`).
- Delegated: a tool whose Step Snap is Off still gets the increment while another tool's Step Snap is on *and* a grid
  / point snap is on (Blender has one increment for all three transforms).

## 검증 (속도 우선: 이 기능만)
- Headless `-k step220,step3_hold,step25,step93,step138_carry,step59,step129_panel` 59 / 59 (`test_step220_snap` 6).
- GUI `gui_step220_snap` (Step Snap Off → Status Line Snap to Grid → Move arrow drag; object and edit-mode vertices
  land on whole Maya units): Blender 4.5.4 3 / 3, 5.2.3 3 / 3.
