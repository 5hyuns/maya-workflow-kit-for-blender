# blender-maya-kit

Make Blender 4.5 feel like Maya 2022 to a Maya user: keymap, interaction feel,
UI/UX layout and scene concepts, not just hotkeys. Shipped as one Blender 4.2+
extension (`maya_kit`).

## Where things are

| Path | What |
|---|---|
| `research/` | Evidence base. `README.md` = index + Maya→Blender table + milestones M1–M5. `maya/*`, `blender/*` hold the facts with file:line and [O]/[I]/[K]/[U] tags. Read the relevant file before implementing a feature. Not tracked in git (contains extracted Maya MEL text, see decision 6). |
| `docs/user_decisions.md` | Decisions already made (units, parenting, packaging, target version, no Maya assets, protect user config). Follow them. |
| `docs/PLAN.md` | Step-by-step plan: research table → steps, each with P/W/C verdict and how it is verified. |
| `docs/HANDOFF.md` | Current work and the next thing to do. Update at the end of every step. |
| `docs/steps/step_<n>.md` | Per step: plan (for complex designs), what was done, verification, what is left. |
| `docs/manual_checks.md` | Checklist for things headless tests can't prove (modal input, feel, visuals). |
| `src/maya_kit/` | The extension. `blender_manifest.toml`, `__init__.py` (registers sub-packages in order), `preferences.py`, `keymap/`, `operators/`, `ui/`, `theme/`, `app_template/`. |
| `tools/build.py` | Builds `dist/maya_kit-<ver>.zip` (extension, via `blender --command extension build`) and `dist/maya_kit-<ver>-legacy.zip`. |
| `tests/` | Headless harness `run.py`, in-Blender runner `_bootstrap.py`, helpers `kit.py`, tests `test_*.py`. |

## Rules

- **Never touch the user's real Blender settings** (`%APPDATA%/Blender Foundation`). Every Blender run uses `--factory-startup` and/or `BLENDER_USER_CONFIG` / `BLENDER_USER_SCRIPTS` / `BLENDER_USER_EXTENSIONS` pointed into `tmp/`. If you start a GUI Blender, kill only that PID afterwards.
- Run `blender --command ...` with stdin redirected (`< /dev/null`, `stdin=DEVNULL`); with a console stdin it hangs.
- Do not copy Maya MEL, icons or resource files into `src/` or `docs/`. Re-implement behaviour; cite `research/...:line` as the source.
- Cite evidence in code comments or step docs as `research/<file>:<line>` or `$S\...:line` (`$S` = `C:\Program Files\Blender Foundation\Blender 4.5\4.5\scripts`).
- Every sub-package has `register()` / `unregister()`; `unregister()` must undo everything (classes, props, keymap items via `keymap.add_item`, handlers, `.append()`ed draw funcs). `test_enable_disable.py` enforces this.
- Operator ids: `maya_kit.<name>`; class prefix `MAYAKIT_`.
- Complex designs (modal input, GPU hotbox, matrix math, keymap conflicts): write the plan in `docs/steps/step_<n>.md` 「계획」 first, then implement.
- Decisions made without asking are recorded in docs as `delegated`.
- Commit messages in English. No push (no remote). Don't stage `.serena/`, `.claude/`, `tmp/`, `dist/`.

## Testing

```
python tests/run.py              # build + install into tmp/test_env + run all tests/test_*.py
python tests/run.py -k enable    # only matching test files
python tests/run.py --no-build   # reuse dist/ zip
python tools/build.py            # build only
python tools/gen_keymap_mapping.py  # regenerate docs/keymap_mapping.md (exit 1 if an IC/KIT row is unbound)
python tests/gui/run.py [--shots DIR]  # GUI tests: simulated key/mouse events (a Blender window opens briefly)
python tools/make_startup.py     # regenerate app_template/MayaKit/startup.blend (headless)
python tools/make_theme.py       # regenerate theme/maya.xml from its colour table
python tools/gen_menu_data.py    # regenerate ui/menu_data.py (Maya menu structure) from research/maya/menus.json
python tools/gen_shelf_data.py   # regenerate ui/shelf_data.py (Maya factory shelves) from research/maya/shelves.json
```

- Each test file runs in its own `blender -b --factory-startup` process. The extension module is `bl_ext.user_default.maya_kit`; it is enabled automatically unless the test module sets `AUTO_ENABLE = False`.
- A test is a top-level `test_*` function that raises on failure. Shared helpers in `tests/kit.py` (`enable`, `disable`, `snapshot`, `diff`).
- Logs: `tmp/test_env/logs/<test>.log`. Results: `tmp/test_env/results/<test>.json`.
- Keymap work: patches go in `src/maya_kit/keymap/maya_patches.py` (record new bindings via `_add` so the shadowing test sees them); update the row status in `keymap/mapping.py`, then regenerate the mapping doc.
- GUI event tests (`tests/gui/gui_*.py`, helpers in `tests/gui/sim.py`): Blender runs with `--enable-event-simulate`; key events need a position (default 0,0 hits the status bar), the factory splash eats events until ESC, and simulated keys never reach the OS so `keystate.is_down` is replaced by the simulated state.
- Modal keys: Maya hold keys use a PRESS → modal (`operators/hold.py`), not PRESS/RELEASE keymap pairs, because the transform modal swallows RELEASE; new tap/hold keys subclass `taphold.TapHoldBinding`.
- Blender preferences (not scene data) the kit changes go through `prefs_preset.py` (backup in add-on prefs, restore on disable); `tests/kit.py` snapshots `preferences.inputs`/`view`, so a leak fails `test_enable_disable`.
- Generated binaries (`startup.blend`, `maya.xml`) are never edited by hand: change the generator and rerun it. Headless screen editing: `screen.area_split` works under a window/screen override (sizes appear after loading in a UI), but `screen.area_close` hangs and `screen.area_move` has no effect in `-b`.
- Simulated events don't update `event.mouse_prev_x`: modal operators track the previous mouse position themselves. `Region.active_panel_category` is read-only (headless and GUI), so a sidebar tab can't be preselected; GUI tests switch tabs with Ctrl+wheel over the tab strip.
- Keymap items that must win over a same-event item in the same keymap go in front (`_add(..., first=True)`) and must return PASS_THROUGH when they don't apply; list them in `maya_patches.PASS_THROUGH_FIRST`.
- Git Bash gotcha: `$PWD` is `/c/...`, which Blender's Python can't resolve — pass Windows paths (`cygpath -w`) in `BLENDER_USER_*` when launching Blender by hand.
- Headless gotcha: in `-b` the default keyconfig is not populated (research/blender/industry_compatible_vs_maya.md:14); build keyconfigs from data, don't read `keyconfigs.default`.
- UI: verify with a GUI screenshot. Interaction feel: add to `docs/manual_checks.md`.
- Maya menu items: map them in `ui/menu_map.py` (label path → operator / v3d / tool / menu); unmapped items draw greyed. `TOPBAR_HT_upper_bar.draw_left/right` are swapped by `ui/status_line.py` and must be restored on unregister (`tests/kit.py` snapshots them).
- GUI typing: hover the field (MOUSEMOVE) before clicking, then `ev('TEXTINPUT', 'PRESS', unicode=ch)`. The top bar/status bar are global areas (not in `screen.areas`): hover them to redraw. With `--factory-startup`, loading the MayaKit template reloads factory prefs, so re-activate the Maya keymap in GUI tests.
- Marking menus: data in `marking/menus.py` (Maya radial positions, checked against research JSON by `tests/test_step8_marking_menus.py`); pies are generated from it. Menu/pie items must not invoke operators that open their own popup (e.g. `transform.select_orientation`): use `wm.context_set_enum`/exec-style ops.
- Marking menu engine/hotbox: logic in `marking/engine.py` (no bpy, test it headless), GPU drawing in `marking/draw.py` (one handler per editor, draws only the region in `draw.ACTIVE`), modals in `marking/modal.py`. Pass the press position as `origin` when invoking `maya_kit.mm_engine` from another operator: a nested invoke's event is the window's latest state.
- Concepts (step 10): the Maya pivot is the object origin and `delta_location` holds the Maya pivot offset (Freeze → channels 0/0/1, pivot kept). Setting `matrix_basis`/`matrix_world` keeps deltas. Parent the Maya way with `operators/parenting.set_parent_maya` (parent inverse identity unless shear). Menu items Maya builds at run time go in `menu_map.EXTRA`.
- Sidebar dock (step 11): CB/LE and AE share the "Channel Box" sidebar tab; `WindowManager.maya_kit_dock` picks which panels poll. Outliner rows are a WM collection rebuilt from handlers (never write ID data in `draw`). To test "is this object in the view layer", use `select_set`'s RuntimeError — `view_layer.objects.get` misses objects linked since the last sync.
- Shelf (step 12): Status Line + Shelf live in the "Maya strip", an Image Editor whose `space.mask` is the Mask `.MayaKitStrip`; `ui/shelf.py` swaps `IMAGE_HT_header/tool_header.draw` (restored on unregister, snapshotted by `tests/kit.py`). Layout changes go in `tools/make_startup.py` (rerun it). A HORIZONTAL `area_split` gives the new area the top part.
- GUI traps (step 9): `screen.screenshot` shows the previous frame (take shots one tick later); setting `SpaceView3D.show_region_toolbar` inside an operator doesn't stick — set it from a `bpy.app.timers` callback.
