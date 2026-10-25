# Step 208 — maya.cmds look-alike 2 (backlog #7, Issue #115)

Source: `docs/steps/step_201_remaining.md` §3 U2 / §8 #5 (carried over three audits), `src/allset/command_line/cmds_shim.py`
(17 functions). Maya measurements: `research/maya/re/cmds_201.md` / `cmds_201.json` (mayapy, 23 cases + 4 probes).

## Plan

1. One case file (`research/scripts/cmds_201/cases.py`) of plain `cmds` scripts that run unchanged in mayapy and in the
   kit's Command Line runner; mayapy dumps return values + a scene snapshot (names, channels, world translation,
   keys, time, playback range, history nodes) → `tests/maya201_cmds_data.py`.
2. Implement on the kit's own operations (parenting / group / duplicate / dag delete / create / channel_box keys) so a
   script gives what the menus give; split the shim into `cmds_dag.py`, `cmds_anim.py`, `cmds_file.py`.
3. Test = run every case through `runner.run` and compare with mayapy; differences that can't follow Maya listed with
   their reason. One Script Editor GUI test.
Mostly sequential on purpose: the implementation needed the measurement (the naming rule turned out different from the
kit's), and the Blender runs share the two slots; the full headless suite ran in its own sandbox while the GUI test
was written.

## Done

- New commands: `parent` (world kept, `-r`, `-w`; children selected), `group` (common parent / `-w` / `-p`, `-em` =
  `nullN`, `-n`), `duplicate` (`-n`, `-rr`, returns root + transforms below, Maya shape names), `spaceLocator` (`-n`,
  `-p` = pivot offset), `setKeyframe` (`-at` list, `-t` list / range, `-v`, `-bd`, node.attr, locked skipped),
  `cutKey` (`-at`, `-t`, `-cl`), `keyframe` (`-q -tc / -vc / -kc` with `-t` range, `-e` relative / absolute),
  `playbackOptions` (min / max = preview range, ast / aet = scene range, `-by`), `file` (`-new`, `-open`, `-rename`,
  `-save`, `-q -sn / -shn / -mf`, `-f`), `addAttr` (double / long / bool / string, min / max / dv / k).
- Extended: `delete` (hierarchy via `dag.delete_hierarchy`, `-ch`, creation node names), `rename` (Maya increment +
  shape rule), `objExists` (shapes, creation nodes, `node.attr`), `listRelatives` (shape first, `-ad` order, `-type`,
  `-ap`, shape → parent), `ls` (wildcards, shapes, `-type` incl. locator / light, `-s`), `xform` (`-m`, `-bb`,
  `-rp / -sp / -piv` query + set, `-cp`, `-ws -t` without the pivot offset, `-ws -m` with shear residual),
  `getAttr` / `setAttr` (`-time`, `-k`, `-cb`, `-type`, rotateOrder keeping values, worldMatrix / matrix,
  inheritsTransform, Maya min / max error).
- **Maya naming rule** (measured): one past the highest number, no gap filling — `naming.next_number` (all kit
  create paths, groups, joints, history nodes `prim_history._next_name`). Maya default camera names are taken for
  explicit names. Kit locators carry `create.LOCATOR_PROP` (shape `locatorShapeN`).
- `cmds.file` loads synchronously (`load_ui=False`: windows stay). In the UI the file read leaves the running
  script's context without a window, so every cmds call after it runs in the script's window
  (`cmds_shim._guarded`, `cmds_file.script_window`). The Script Editor's MEL / Python tabs survive File > New / Open
  (`script_editor._load_pre / _load_post`, Maya keeps its Script Editor input).
- Older tests that encoded gap filling (`test_step10`, `test_operators_step2`, `test_step141_keys`) now expect Maya's
  numbers (joint4–6 measured with mayapy); `test_step7` `ls` / `listRelatives` expect the shape like Maya.

## Verification

- `tests/test_step208_cmds.py` 7 / 7: 23 / 23 mayapy cases (170 return values, 66 nodes: names, channels, world
  translation, keys, time, playback, history nodes) with 7 listed deviations; naming rule, names / shapes, errors,
  keys + refresh, playback mapping, Script Editor tabs over a load.
- Related headless (step7 / 10 / 21 / operators_step2 / 141) pass; full headless 2006 / 2006 (first run 2005 / 2006,
  the one failure = joint gap-filling test, fixed after mayapy showed joint4–6).
- GUI: `tests/gui/gui_step208_script_editor.py` 9 / 9 (script typed into the Python tab, Ctrl+Enter: new scene, group /
  parent / locator / duplicate / keys / playback range, Script Editor window + tab kept; shot checked:
  `ctrl` Translate Y keyed red in the Channel Box, Time Slider 1–24, range 1 / 200); related GUI + smoke
  (step105 windows, 21 units, 7 top UI, 138 open / prompt, 60 switch, 49 layout, 208) 90 / 90.

## Deviations (delegated)

See `research/maya/re/cmds_201.md` §6: unique Blender names in duplicated hierarchies, shear, Blender re-evaluating
animated properties at once, `.ma` → `.blend`, `file -q -modified` True right after `file -new` inside a script,
`spaceLocator -p` as pivot offset, no animation clipboard for `cutKey`, `ls` order.

## Left

- Commands still missing that Maya scripts use: `makeIdentity`, constraints (`parentConstraint` ...), `joint`,
  `connectAttr`, `nodeType` / `objectType`, `attributeQuery`, `shadingNode` / `sets`, `currentUnit`, `polyExtrude*`.
- `keyframe -e` with `-option over / insert`; `setKeyframe -itt / -ott` tangents (accepted, ignored); `cutKey` clipboard.
- Script Editor result echo is still Blender reports (history pane).
