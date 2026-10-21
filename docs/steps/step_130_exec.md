# Step 130 lane E — user code through Blender's Run Script (#40)

Plan: docs/steps/step_130.md 결정 1 (delegated).

## What was done

- `command_line/runner.py`: no `exec` / `eval` / `compile`, no `builtins` / `__import__` hook, no `importlib`.
  `run(source, name, persist, remember)`:
  1. `ast.parse` only to detect syntax errors (MEL hint as before) and to find statement positions;
  2. `prepare()` rewrites the text: `import maya.cmds as X` → `from <pkg>.command_line import cmds_shim as X`,
     `import maya.cmds` / `import maya` → `from <pkg>.command_line import maya_stub as maya`,
     `from maya import cmds [as X]` → `from <pkg>.command_line.maya_stub import cmds_shim as cmds|X`,
     `from maya.cmds import ...` → `from <pkg>.command_line.cmds_shim import ...` (any depth: inside `if` / `def`);
     a final expression `x` → `_allset_result = (x\n)`; one line in front: `from <pkg>.command_line import runner as
     _allset_runner; _allset_runner.bind(globals())`. `<pkg>` = the runner's `__package__` (no hard-coded repo name).
     Column offsets are UTF-8 byte offsets (ast), so the edit runs on the encoded source.
  3. `run_text()` writes the result into a new Text `.allset_command_line` (shelf: `.allset_shelf <label>`), runs
     `bpy.ops.text.run_script()` under `temp_override(edit_text=text)` with stdout captured, and removes the Text.
  4. `bind()` filled the run's `globals()` with the session names (`bpy`, `C`, `D`, `cmds`, `mc`, earlier variables)
     and kept the dictionary; after the run the runner reads `_allset_result` and copies the variables back into the
     session (also after an error, like Maya). Shelf runs (`persist=False`) keep nothing.
- `command_line/maya_stub.py` (new): the module `import maya` gets (`cmds` = `cmds_shim`).
- `ui/shelf.py` `run_script`: through `runner.run(..., persist=False, remember=False)`.
- `ui/shelf.py` `store_path` (#42): the legacy add-on build's fallback is `<add-on folder>/user_data/shelves.json`
  instead of `user_resource('CONFIG')/allset` — nothing is written to the user's Blender config. The extension build
  always uses `bpy.utils.extension_path_user` (unchanged). `tests/test_step61_distribution.py` now allows no
  `user_resource()` call at all.
- `ui/script_editor.py`: unchanged (it already called `runner.run`).
- `ui/render_settings.py` `registration_key`: the defining module's `classes` tuple is read from one of the class's
  own functions' `__globals__` (`_module_names`), not `sys.modules`.

Measured in Blender 4.5.4 (`tmp/lane_e/probe.py`, headless):
- `text.run_script` polls only with `edit_text` in context; `temp_override(edit_text=text)` is enough (no Text Editor
  area needed). Its bl_options are REGISTER + UNDO, but a nested Python `bpy.ops` call pushes no undo step, so the
  Command Line's own undo push stays one step per command.
- The run gets a fresh `__main__` dictionary (real `__builtins__`, no `bpy`); Blender does not clear it afterwards, so
  a kept reference can be read after the run.
- A Python error (also a SyntaxError) becomes an operator error report: a RuntimeError in the caller whose text is
  `Error: Python: Traceback ...\n<Type>: <message>\nLocation: ...`; the last non-`Location` line is the result line.
  The report is also printed to stdout (captured and forwarded to the console).

## Behaviour differences for users

- The traceback in the system console / Info log names the file `\.allset_command_line` (shelf: `\.allset_shelf
  <label>`) and line numbers are one higher than the typed line (the `bind` line in front).
- A Python error additionally appears as Blender's error report (status bar banner / Info editor with the
  traceback) — the Script Editor history already showed the error line, now the traceback is there too.
- `import maya.cmds` inside a string passed to `exec` by the user's own code, or `importlib.import_module("maya.cmds")`,
  is not rewritten (only import statements are). A real `maya` package on Blender's path (mayapy) is no longer
  preferred over the kit's `cmds` subset.
- `from __future__ import ...` in an entry fails (it is no longer the first line).
- Shelf scripts see `C` = `bpy.context` (was the operator's context — the same object while the button runs).
- Unchanged: `# Result: ... #` for a final expression, last printed line otherwise, MEL notice / hint, variables
  persist between Command Line / Script Editor entries, history, one undo step per command.

## Verification

- `tests/test_step7_top_ui.py`: runner results / errors / persistence, every `maya` import form (incl. nested and
  multi-name), `test_runner_uses_blenders_run_script` (prepared text, UTF-8 columns, multi-line expression, loop
  output, NameError text, temporary Text removed, variables kept after an error, shelf runs keep nothing).
- `tests/test_step114_guidelines.py`: shelf script check through `shelf.run_script` (no `exec` in the test either).
- `tests/test_step130_no_exec.py`: greps all of `src/allset` (code, comments, docstrings) for `exec(`, `execfile(`,
  `eval(`, `compile(..'exec'|'eval'|'single')`, `__import__`, `builtins`, `sys.path`, `sys.modules`, `importlib`.
  `keymap/ic_data.py` (`bpy.utils.execfile`, lane K) is listed in `PENDING_OTHER_LANES` and only printed — the main
  session empties that set after the merge.
