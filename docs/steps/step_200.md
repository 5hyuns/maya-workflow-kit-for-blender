# Step 200 — Blender 5.x test pass 2 (backlog #8, Issue #107)

## 계획

Blindspot NB4: the last full 5.x headless run was step 153 (docs/compat_5x.md:62). Steps 154–199 added
version-sensitive code. Run the full headless suite per version (`ALLSET_SANDBOX=<ver> python tests/run.py --no-build
--blender <exe>`, zip built once by 4.5 — the extension zip is version-independent), at most two Blenders at a time:
5.0.1 + 5.1.2 together, then 5.2.3; then GUI `-k step183,step186,step187` on 5.2.3. Fixes only through
`src/allset/compat.py` (feature checks), tests through `kit` helpers. Results go to a new section in
`docs/compat_5x.md`.

## 한 것

- Full headless on 5.0.1 + 5.1.2 together, then 5.2.3, then the final round (4.5.4 + 5.2.3, 5.0.1 + 5.1.2).
- Version fixes, all feature / version checks in `src/allset/compat.py`:
  - **5.2 Geometry Nodes modifier inputs** moved from ID properties (`md["Socket_1"]`) to
    `md.properties.inputs.Socket_1.value / .type / .attribute_name` — `compat.GN_INPUT_STRUCT`, `gn_input_get`,
    `gn_input_set`, `gn_input_attribute`; `operators/wire_deformer.py` uses them (Wire creation failed on 5.2.3).
  - **5.x menu bar lead** = 1.25 widget units instead of 1.48 (measured on 5.0.1 / 5.1.2 / 5.2.3 at UI 1.0 and 1.25)
    — `compat.MENU_BAR_LEAD_UNITS`, used by `ui/option_click.py` (❒ clicks in menu-bar menus).
  - **`Bone.select` gone in 5.x**: `rig_maya.py` (influence joints) and `skin_tools_199.picked_joints` read it
    directly → the existing shim `channel_box.bone_selected` (delegated: the shim stays in channel_box, CLAUDE.md
    step 55).
- Test fixes: Bone.select in two tests → `set_bone_selected`; the Cycles light-link probe makes the 5.0 World
  (always nodes, grey Background) black; `test_step102_file_io` writes into `tmp/<sandbox>/file_io` (parallel version
  runs raced on `tmp/file_io` — the 5.1.2 "USD" failure); `gui_step183_option_click` edge scan accepts a wider reading
  on 5.x only (neighbouring areas share the menu back colour; screenshots confirm the model; the ❒ cell check stays
  strict).

## 검증

- Headless full (226 files): **4.5.4 1844 / 1844, 5.0.1 1844 / 1844, 5.1.2 1844 / 1844, 5.2.3 1844 / 1844**
  (first run: 5.0.1 1841, 5.1.2 1840, 5.2.3 1834).
- GUI 5.2.3: `-k step183,step186,step187` 28 / 28 (no step186 GUI file), step183 at UI 1.0 24 / 24; 4.5 step183
  24 / 24.
- `docs/compat_5x.md`: new rows in the 5.0 / 5.2 tables and section 「step 200」.

## 남은 것

- 5.x GUI beyond step183 / 187 is not re-run (the full GUI suite is for release prep, user rule 10-23).
- `test_step138_file_io` still shares `tmp/file_io138` between sandboxes (its Maya fixtures live there); run it
  in one version at a time.
