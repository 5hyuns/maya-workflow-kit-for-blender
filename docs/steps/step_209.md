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
