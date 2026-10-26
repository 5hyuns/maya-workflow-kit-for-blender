# Merge protocol: real-time transforms, joint modes and paint weights

Date: 2026-10-26. Target: `master`. Source: `Bug-Fixes-RealtimeTransforms-JointMode-PaintWeights`.

## Inputs and procedure

- Target before merge: `d5546fa8165b567fb2fa1f80d304f147c50fbd00`.
- Source: `2e8dcde202989f34428025992c9b0cb1116ac049`.
- Common ancestor: `13d2153331f1de52092e43369cc1cd8fc122beeb`.
- The working tree was clean. `git fetch origin` confirmed local `master` matched `origin/master`.
- The target had 63 commits and the source one commit since their common ancestor.
- Created `codex/merge-realtime-joints-weights` from `master`, then ran
  `git merge --no-ff --no-commit Bug-Fixes-RealtimeTransforms-JointMode-PaintWeights`.
- Reviewed both sides of each conflict and the overlapping files that Git merged automatically.
  No whole-file “ours” or “theirs” replacement was used.
- Tested the candidate before updating `master`. The source branch is retained; remote publishing is separate.

## Conflict resolutions

| File / conflict | Resolution | Reason |
| --- | --- | --- |
| `src/allset/operators/__init__.py`: operator imports/classes | Kept all target additions (cleanup, graph, skin/constraints, animation, pins/deformers, UV, curves, references and lights), then added `weight_paint` and its classes before the class-registration factory. | Both sets of features must register; selecting either whole side would drop the other set. |
| `src/allset/operators/__init__.py`: unregister block | Kept every target handler/property cleanup and included `weight_paint.unregister_props()`. Its registration call also remains. | The added weight state must be removed when disabling, alongside the newer target features. |
| `src/allset/ui/__init__.py`: module list | Retained the complete target list, including its newer editors, and appended `armature_mode_pulse`. Kept the source's import. | All UI modules register once; the existing reversed unregister loop removes the pulse before earlier UI modules. |
| `src/allset/ui/channel_box.py`: `ALLSET_PT_channel_box.body` | Clear the area's stale `_last` scrolling range first, then use the target's `wrap_rows` menu layout and `units = 1.0 + len(rows)`. | Early-return views must release virtual scrolling, while narrow docks still need wrapped menus and correct height accounting. |

The automatic merges retained the target's newer graph/render key bindings, time-slider sizing,
Channel Box animation-layer states and constraint/skin support, alongside the source's joint and paint-tool changes.
The source's manifest version `0.5.2` is retained; this merge does not publish a release.

## Integration corrections found during validation

1. Moved the seven incoming `src/allset/tests/blender_*.py` scripts to `tests/integration/` and updated their imports.
   These scripts deliberately manipulate test import paths and isolated preferences, so shipping them caused the
   existing extension package scan to fail. The package rules remain enforced.
2. Moved `MAYA_JOINT_WORKFLOW.md` and `PAINT_SKIN_WEIGHTS.md` to `docs/`, updated their test paths, and retained their
   contents. They are documentation, not the package's enumerated CC0 artwork assets.
3. Added `tests/integration/run.py`: builds/installs in `tmp/integration_env`, runs each script in a separate factory
   Blender process, checks GUI result files, enforces timeouts, and uses the repository's two-process Blender slot
   limit. GUI outputs now use `ALLSET_INTEGRATION_OUTPUT` or a repository-local `tmp/` fallback instead of `/tmp`.
4. Updated `SelectNone` in `keymap/mapping.py` and the corresponding mapping documentation to `allset.select_none`.
   Updated the Object/Pose Alt+D assertions in the existing tests. Added a check that the mapping matches the generated
   shortcut to the joint integration test; its behavioral assertions still check cleared bones, active object and modes.
5. Updated the Channel Box scrolling test's mock context to include a window and verify that scrolling clears a stale
   hover target. The clamping assertions remain.
6. Reworded one internal “Allset” comment to “the kit” to satisfy the existing product-name scan.
7. Marked the weight-paint exit operator's internal `tool` enum `HIDDEN`. The existing undo/HUD test caught that
   its visible enum exposed Blender's Adjust Last Operation panel after Q/W/E/R. This retains `REGISTER` and `UNDO`
   while following the kit's established hidden-property convention.

## Validation

Validation is performed on the installed **Blender 5.2.2 LTS**, build `d13f752e3b9c`, using Blender's bundled Python.
All harnesses create isolated configuration, scripts and extension directories under `tmp/` before launching Blender.

| Check | Result |
| --- | --- |
| Extension build / manifest validation | Passed; `dist/maya-workflow-kit-0.5.2.zip` contains no test scripts or Markdown documentation. |
| Python parsing and Git whitespace/conflict checks | Passed for all extension Python files; no unmerged paths or conflict markers. |
| Full headless suite, with corrected files rerun | **2,053 passed, 58 failed across 252 files**. All remaining failures reproduced on the original target with the same final error message after normalizing checkout paths. |
| Focused regression reruns | **108/108**, then **15/15** scrolling/undo checks, **8/8** Hotkey Editor checks and **8/8** lighting checks. These replace earlier results for the same files in the headless total above. |
| Incoming integration scripts, final run | **7/7 passed**: Channel Box wheel events, viewport joint picking, joint workflow, paint exit/weight preservation, real Q/W/E/R events, weight operations and all paint-workspace pages. |
| Existing affected GUI suite | **21 passed, 3 failed across 4 files**. The same three failures reproduced on the original target. |

The first full headless run reported 2,039 passes and 65 failures, including one Blender
`EXCEPTION_ACCESS_VIOLATION` in `test_step214_lights` without a result file. Its separate rerun passed all eight
tests, including Cycles/EEVEE rendering. The crash's cause is undetermined; it is recorded rather than treated as
a proven pre-existing issue. Six other initial failures were resolved by the integration corrections above.

Remaining baseline failures:

| Tests | Count | Reason |
| --- | ---: | --- |
| `test_keymap_maya`, `test_step107_keys`, `test_step108_menu_hotkeys` | 3 | Missing private hotkey/menu reference JSON. |
| `test_step155_uv_shells` | 13 | Missing private UV-shell reference JSON. |
| `test_step156_curves_maya` | 10 | Missing private curve reference JSON. |
| `test_step181_surfaces_math`, `test_step181_surfaces_ops` | 19 | Missing private surface reference JSON. |
| `test_step196_misc_windows` | 12 | Missing private option-window reference JSON. |
| `test_step213_connection::test_compound_and_unit_conversion` | 1 | Blender returns `0.2499999850988388`; the existing test requires `0.25` within `1e-9`. Identical on the original target. |
| GUI `gui_step148_cb` | 2 | Cannot locate Rotate Z at this machine's default UI scale (`2.50`); the following step cannot unpack that missing coordinate. Identical on the original target. |
| GUI `gui_step58_skin` | 1 | The fixed-coordinate influence-list click leaves `joint3` selected instead of `joint2`. Identical on the original target; the remaining painting assertions pass. |

Evidence retained locally (ignored by Git): `tmp/test_env`, `tmp/merge_targeted_env`, `tmp/merge_fix_env`,
`tmp/merge_hotkey_env`, `tmp/merge_lights_env`, `tmp/integration_env`, and `tmp/merge_gui_env` contain logs/results.
`tmp/merge-validation-summary.json` records the latest headless result for each file. The archived original target
and comparison logs are under `tmp/master_baseline/` (headless `test_env` / `merge_baseline_extra_env`,
GUI `merge_gui_baseline_env`).

No remaining test failure unique to this merge was observed. This is not a guarantee for untested Blender versions
or interaction paths; the baseline failures and initial lighting crash limit the validation claim.

### Reproduce

```powershell
$py = 'C:\Program Files\Blender Foundation\Blender 5.2\5.2\python\bin\python.exe'
$blender = 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe'
& $py tests/run.py --blender $blender
& $py tests/integration/run.py --blender $blender
$env:ALLSET_SANDBOX = 'merge_gui_env'
& $py tests/gui/run.py --no-build --blender $blender -k 'step57_joints,step58_skin,step6_channel_box,step148_cb'
```

The full suite expects private reference data under `research/maya/`; those files are not in this checkout.
Other Blender versions and subjective interaction feel are outside this validation run.
