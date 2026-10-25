# Step 209 — Reference Editor (backlog #8, Issue #116)

Source: `docs/steps/step_201_remaining.md` §3 F4 / §8 #7, `research/maya/workflows/scene.md:30` (C.4: list with the
load check box, File Particulars, Reference menu), step 69 Create Reference (`operators/project.py:reference`).
New Maya measurements: `research/maya/re/refs_209.md` (mayapy `research/scripts/cmds_201/refs209_mayapy.py` →
`refs_209.json`; GUI capture of the Reference Editor window `research/scripts/maya_refs209/` →
`research/maya/screens/refs209/_refs209.json` + `reference_editor_win1.png`).

## 계획

Measured first (one Maya at a time: the GUI capture, then mayapy), then Blender probes (`tests/test_zz_probe209.py`,
removed after): every Maya rule has a Blender counterpart.

| Maya (mayapy / GUI) | Blender (probe 4.5) | kit |
|---|---|---|
| reference = `<ns>:` nodes + `<ns>RN` (second = ns prop1, node propRN1) | link + library override (step 69) | collection `ns` with `allset_reference` (path) + `allset_reference_node` |
| reload: source changes seen, edits kept; an edited attribute hides the source's change of it | `Library.reload()`: same (whole `location` array is one override op) | Reload = `Library.reload()` |
| unload: nodes gone, edits kept; load: back with edits | no unload | Unload = the `ns` layer collection excluded (overrides kept), Load = included (delegated) |
| replace: new file, edits re-applied by node name | — | Replace = record edits by source name (`override_library.properties` + values), remove, reference the new file under the same namespace, re-apply |
| import objects: nodes local, names keep `ns:`, reference node gone | `make_local(clear_liboverride=True)` keeps name and values | Import = every override ID in the reference made local, marker removed |
| remove: nodes and namespace gone | — | delete the overrides + collection, library removed when no other reference uses it |
| lock / unlock (no edits) | `is_system_override` True = not editable | Lock / Unlock |
| Clean Up Reference (unloaded: drop edits) | `override_library.reset()` | Clean Up |
| Export / Assign Offline File (.editMA = edits) | — | JSON of the recorded edits (`.json`), applied by source name |
| List Reference Edits | `operations_update()` then `properties` | Command Line result + a popup list |

Window: `allset.reference_editor` opens a new window whose one area is a Properties editor on the Tool tab marked
by hidden tab flags (like the Hypershade panes, step 131), drawn by `ALLSET_PT_reference_editor`: Maya's menu bar
(File / Reference / Proxy / View / Help from the capture, `ui/editor_menu_data.py`, actions in
`ui/editor_menu_map.py`), icon row, File Particulars (unresolved / resolved name, namespace, Reload, Read Only) and the
list (load check box, `<RN> <file>`, selected row). Main File menu: Reference Editor → this window, Export to Offline
File / Assign Offline File → the same commands (+2 main File items; the Reference Editor's own menus count as an
editor menu bar).
Sequential on purpose: the window and menus need the model's operators, and Blender runs share two slots.

## Done

- `operators/references.py`: Reload (`Library.reload`), Unload / Load / toggle (layer collection exclude), Import
  Objects from Reference (overrides → local in place, linked meshes copied per reference, materials local, library
  removed when unused), Remove, Duplicate (prop1 / propRN1), Replace + Recently Replaced Files (edits re-applied by
  source name), Lock / Unlock (`is_system_override`), Clean Up (`reset`, unloaded only like Maya), Select File
  Contents, Load / Unload Related, List Reference Edits (popup + result), Export / Assign Offline File (JSON).
- Create Reference now names the reference node Maya's way (`NODE`: propRN, propRN1) and keeps creation order.
- `ui/reference_editor.py`: File > Reference Editor = a new window, one Properties area on the Tool tab marked by
  `MARK` (world + physics + constraints flags: not a Maya dock role, not Tool Settings, not a Hypershade pane;
  `dock_tabs` / `tool_settings.in_dock` leave it alone); Maya's menu bar flat (`emboss = 'PULLDOWN_MENU'`), icon row,
  File Particulars (Unresolved / Resolved name, Reload, Read Only = lock, editable Namespace = renames `ns:` nodes,
  Sharing), list rows = load check box + "<node> <file>".
- Menus: the Reference Editor menu bar joins `ui/editor_menu_data.py` (from the GUI capture), 27 / 38 working
  (File 8 / 10, Reference 11 / 11); main File menu 24 → 26 / 30 (Reference Editor, Export to Offline File, Assign
  Offline File); notices for Save Reference Edits, List Unknown Edits, Proxy, View. Main menu total 939 → 941.

## Verification

- `tests/test_step209_references.py` 12 / 12: Maya names (prop / propRN, prop1 / propRN1), source edited in another
  Blender + Reload = source change seen and the override edit kept, Unload / Load keep edits, edits list + offline
  file export / Clean Up / assign, Lock / Read Only, Replace with B (edit applied by name, history), Import (local, no
  library left), Import leaves a second reference of the file alone, Remove / Duplicate, Select / Related / Namespace
  rename / save + reopen, menus mapped to real operators, pane flags unique.
- Full headless 2018 / 2018 (first run 2017 / 2018: `test_step69_scene` expected the old Outliner mapping — updated).
- GUI `gui_step209_reference_editor.py` 5 / 5 + shot checked (flat Maya menu bar, one icon row, File Particulars, list
  `propRN srcA.blend` checked / `propRN1` unchecked); related GUI + smoke (step105 windows, 106 / 129 Tool Settings,
  131 Hypershade, 116 dock, 69 scene, 60 switch, 49 layout, 209) 99 / 99 after the step-69 check was updated.

## Deviations (delegated)

- Unload keeps the data in memory (Blender has no unloaded reference state); Blender references `.blend` files only.
- Offline files are kit JSON (`.json`), not Maya `.editMA`.
- Recently Replaced Files keeps the last 10 paths on the namespace collection.

## Left

- Save Reference Edits (write into the source .blend), List Unknown Edits, Proxy and View menus: notices.
- The Maya search field above the list and nested references (a referenced file's own references) are not shown.
