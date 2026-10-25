# Step 212 — Blender 5.x test pass 3 (Issue #118)

Source: `docs/steps/step_210_remaining.md` NB16 — the last full 5.x run was step 200 (`docs/compat_5x.md`); steps 202–211
had never run on 5.x.

## 계획 (delegated)

- Build the zip once with 4.5, run the full headless suite per version in its own sandbox (`ALLSET_SANDBOX=v501` …), two
  Blenders at a time (slot rule): 5.0.1 + 5.2.3 first, then 5.1.2 alongside the GUI runs.
- GUI per version: the GUI files of the changed modules (steps 203–211) + two smoke files (`step5_layout`,
  `step60_switch`).
- Static scan of steps 202–211 for known 5.x traps (`Action.fcurves`, `Bone.select`, GN inputs written dict-style) while
  the first pair ran: only `FCurve.select` (exists on 5.x); the 205 deformers already used `compat.gn_input_*`.
- Order: the per-version GUI runs and the 5.1.2 headless run waited for slots, not for each other's results.
- The table goes in `docs/compat_5x.md` under 「step 212」 (the instruction's 「step 211」 table = this pass; numbered by
  the step that ran it, delegated).

## 한 것

| 차이 | 버전 | 대응 |
|---|---|---|
| `FunctionNodeCompare` keeps only the current data type's two sockets (4.5–5.1: every type's A / B, INT at index 2 / 3) → Morph / Jiggle node groups failed with IndexError | 5.2 | `compat.compare_inputs(node)` (sockets by identifier `A_INT` / `B_INT` …, else the first two), used by `deformers_205b.GN.compare` |
| A test wrote `Bone.select` (gone in 5.x) | 5.0+ | `test_step203_list` uses the kit shim `channel_box.set_bone_selected` |
| In `-b` a just-read home file / scripted edits aren't `bpy.data.is_dirty` (4.5–5.1: the home file reads as modified), so `cmds.file(new=True)` raised nothing in the headless case | 5.2 `-b` only | `test_step208_cmds` measures `is_dirty` after New and skips the Unsaved-changes rows only then; the GUI file `gui_step208_script_editor` checks the rule on every version (passes) |

## 검증

| Blender | 헤드리스 첫 실행 | 헤드리스 (수정 뒤) | GUI (10 파일) |
|---|---|---|---|
| 4.5.4 | (step 211 2032 / 2032) | **2032 / 2032** | (step 211 related 160 / 160) |
| 5.0.1 | 2031 / 2032 | touched files 63 / 63 | **88 / 88** |
| 5.1.2 | **2032 / 2032** | touched files 63 / 63 | **88 / 88** |
| 5.2.3 | 2022 / 2032 | **2032 / 2032** | **88 / 88** |

Touched files = `step203_list, step205_deform*, step208_cmds, step118_compat` (+ `step169` on 5.2.3: 76 / 76). The step 211
Outliner order compensation (unstable `qsort` rotation) holds on all three 5.x versions (`gui_step211_fix_batch` 10 / 10).

## 남은 것

- 5.0.1 / 5.1.2 full headless with the final zip: only the touched files were rerun (the change is the 5.2 Compare
  branch and two tests); the next full 5.x pass is the next audit / release prep.
- 5.x GUI beyond the steps 203–211 files: release prep (full GUI suite per version).
