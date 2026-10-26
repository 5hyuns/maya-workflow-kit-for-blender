# Step 221 — Quaternion bones: Euler in the Channel Box, keys with S (Issue #131)

## 한 것 (decision 4, docs/strategy/DECISIONS7.md)
- `src/allset/rotation_display.py` (shared with the step 222 FBX curve rebuild): a QUATERNION / AXIS_ANGLE node shows
  Rotate X / Y / Z = its rotation as an XYZ Euler compatible with the last value shown (kit state, never in the file);
  typing writes the quaternion back (sign kept continuous), and the typed numbers come back exactly while the rotation
  is unchanged. `euler_curve(quats)` = the same compat chain over a sequence.
- `ui/channel_box`: `has_channel` ROT is true for every node with a rotation mode (Maya: rotation channels are always
  Rotate X / Y / Z, maya2026_anim.md L19); `get_value` / `set_value` / `keyframe` / `fcurve` / `channel_fcurves` go
  through the helper for non-Euler nodes; a key on Rotate X / Y / Z keys all 4 `rotation_quaternion` (or axis-angle)
  components. S / Shift+E / Auto Key / Channel Box keys therefore key quaternion rigs. The "Rotation mode QUATERNION"
  rows + Rotate Order XYZ button no longer show (the operator stays); the bone keeps its rotation mode.
- Graph Editor already names the curves "Rotate W / X / Y / Z" (step 150 kit outliner).
- Not in this step: kit FBX import converting to Euler (step 223), an explicit Convert Rotation to Euler button
  (optional in decision 4).

## 검증 (속도 우선: 이 기능만)
- `-k step221,step55`: 13 / 13. `test_step221_quaternion`: 2000 random typed triples through the float32 quaternion
  ≤ 0.005 deg (worst 0.003; the Channel Box keeps typed values exactly), slerp 0→170 deg shows no jump; generated Rigify
  human: 212 visible controls (174 quaternion) all show Rotate X / Y / Z, typed 30 / 270 / −45 come back within 0.002,
  S at frames 1 / 10 makes 4 rotation_quaternion curves with the right values, Graph Editor labels "Rotate …", the kit
  S operator + Ctrl+Z leaves no curves; axis-angle and object quaternions too.
- GUI not run (speed rule) — manual check: Channel Box on a Rigify control (Rotate X / Y / Z rows, MMB drag, typing).
