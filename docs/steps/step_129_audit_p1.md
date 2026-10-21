# Step 129, lane A: audit P1 fixes #19, #20, #39 (+ #17, #18)

Fix batch for 0.2.1 (audit 128 issues). Each fix: cause confirmed, failing test first, fix, pass.
Tests: `tests/test_step129_audit_p1.py` (headless), `tests/gui/gui_step129_switch_template_blender.py`,
`gui_step129_rig_paint_normalize.py`, `gui_step129_component_mode_menus.py` (from the audit 128 repros).

## Maya measurement: component mode (Maya 2022 GUI)

The issues assumed what Maya does; it was measured instead. A GUI Maya 2022 session (factory prefs,
`MAYA_APP_DIR` in `tmp/`) made `pCube1` (Translate X 2), selected it, ran `SelectFacetMask` (F11), selected
`pCube1.f[1]`, then ran each menu runTimeCommand and recorded selection, hilite, transforms, face count, Translate X,
parent, `selectMode -q -o` and `listHistory -pdo` (script: `tmp/lane_a_maya/comp_gui/comp129.py`, result
`tmp/lane_a_maya/comp_out/_comp129.json` + `_history.txt`; mayapy standalone gave misleading results because the
GUI-only procs (MTselAll, changeSelectMode) don't exist there and no object is hilited).

| Menu item (rtc) | Maya 2022 in component mode |
|---|---|
| Select > All (`SelectAll`) | all 6 faces, still component mode |
| Select > Inverse (`InvertSelection`) | the other 5 faces |
| Select > Deselect All (`SelectNone`) | nothing selected, back to object mode (hilite cleared) |
| Select > Hierarchy | no change |
| Select > Similar | 4 faces (Maya criteria; not mapped in this step) |
| Edit > Delete (`doDelete`) | the face is deleted (5 faces) |
| Edit > Cut (`CutSelected`) | the face is deleted; warning "Highlighted items will not be exported..." |
| Edit > Group (`performGroup`) | an **empty** group `null1`, selected; pCube1 not parented |
| Edit > Duplicate / Duplicate Special | Error "No object(s) to duplicate", nothing changes |
| Edit > Duplicate with Transform | `pCube2` made, selection stays `pCube1.f[1]` in component mode |
| Edit > Parent / Unparent | Warning "Cannot parent components or objects in the underworld." + error, nothing |
| Modify > Freeze / Reset Transformations | runs `makeIdentity`, Translate X stays 2 (no effect) |
| Edit > Delete by Type > History (`delete -ch`) | history kept (`polyExtrudeFace1` stays) |

So #39's "Group / Freeze / Duplicate / Parent act on the owning objects", #17's "Ctrl+D duplicates the object" and
#18's "Delete History works in component mode" are **not** Maya behaviour; the kit now does what Maya does.

## #39 / #17 / #18 component mode

Cause: `menu_map` maps these items to object-mode operators and `ALLSET_OT_menu_item.execute` only had a rule table
for object mode (`OBJECT_MODE`), so in edit mode Blender's poll failed and `maya_warning()` printed
"select objects first". Ctrl+D in the Mesh keymap was IC's `mesh.duplicate_move` (copies faces + grab).

Fix: `menu_map.EDIT_MODE` (the table above as rules: `run` / `object` / `owner` / `warn` / `none`) and
`allset.component_command(item)` (`ui/menu_sets.py`, one undo step) that runs a rule; `allset.menu_item` sends
component-mode items there. Mesh Ctrl+D = `allset.component_command(item="Edit/Duplicate")` (Maya's warning).
Items Maya runs without effect report one INFO line ("works on objects; in component mode Maya leaves it alone
(F8 = object mode)") — delegated: Maya prints nothing, the line explains why nothing happened.

## #20 Paint Skin Weights normalization

Cause: `allset.paint_skin_weights` never touched `tool_settings.use_auto_normalize` (Blender factory: off), and the
dock's Flood was `paint.weight_set`, which ignores Auto Normalize (measured: active group set to 1, the other group
kept 1, sum 2).
Fix: entering Paint Skin Weights turns Auto Normalize on (Maya Bind Skin = normalizeWeights Interactive); the dock
shows it as "Normalize Weights (Interactive)"; Flood = `allset.flood_weights` = `paint.weight_set` then, with
normalization on, `vertex_group_normalize_all(BONE_DEFORM, lock_active=True)`. Delegated: the setting is Blender's
scene-wide tool setting, so entering the tool turns it on again after Skin > Normalize Weights > Disable (Maya keeps
it per skinCluster).

## #19 switch to Blender in the template file

Cause: `switch.leave_layout` only undoes a workspace that `enter_layout` appended (`PREV_KEY`); the template file's
own Maya workspace has none, so nothing changed. `set_mode(False)` never touched `preferences.app_template`, so
File > New kept loading the template.
Fix: `leave_layout` on a Maya workspace without `PREV_KEY` appends Blender's factory "Layout" workspace from the
embedded startup file (`workspace.append_activate(filepath="<startup.blend>")`, what Add Workspace > General uses;
measured on 4.5) once, marks it `allset_blender_layout`, and reuses it later. `enter_layout` goes back to the file's
own Maya workspace before appending another. The switch to Blender sets `preferences.app_template` (writable,
measured) to "" when it is the kit template, and the switch back to Maya restores it if this session cleared it.
No file is reloaded (the open file and its unsaved work stay). Headless: a `Window.workspace` assignment waits for
the event loop, so the screen is checked in the GUI test.

## Left

- Select > Similar / All by Type, Edit > Copy / Paste and Center Pivot in component mode: not changed (Similar's Maya
  criteria differ from Blender's).
- The Shift+D key (Duplicate with Transform) in component mode was not changed or checked; the menu item now does
  what Maya does (pCube2, component mode kept).
