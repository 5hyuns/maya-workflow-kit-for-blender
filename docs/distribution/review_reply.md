# Reply to the extensions.blender.org review — draft (step 130, GitHub #40)

Draft for the user to post on the review thread after uploading 0.2.1. Commit references are in the 0.2.1 changelog.
Facts behind each answer: `docs/steps/step_130.md`,
`docs/user_decisions.md` 13, `docs/distribution/extensions_audit.md` "첫 심사 결과와 대응".

---

Hello, and thank you for the detailed review. Version 0.2.1 addresses every point. Point by point:

### 1. "Using exec and eval are not allowed. Should be removed."

Removed. The package contains no `exec`, `eval`, `compile(..., 'exec')` or `bpy.utils.execfile` any more.

- The Python Command Line, the Script Editor and Python shelf buttons now write the user's code into a Text datablock
  and run it with Blender's own `bpy.ops.text.run_script` — the same path as *Text Editor > Run Script*. The Text stays
  visible in the file, so the user can see exactly what ran. (see the 0.2.1 changelog)
- The keymap no longer loads Blender's bundled Industry Compatible keymap file with `execfile`. The keymap data is now a static Python data file in the package (generated once
  from Blender's preset by a development tool, never executed at run time). (see the 0.2.1 changelog)
- A test scans every Python file of the source and of the built zip (tokenized, so only code counts, not comments) and
  fails on any of these calls: `tests/test_step130_package_scan.py`.

### 2. "Manually modifying sys paths or modules is not allowed. Should be removed as well."

Removed. There is no access to `sys.path`, `sys.modules`, `sys.meta_path`, `builtins`, `__builtins__` or
`importlib.util` anywhere in the package.

- The `__import__` hook that answered `import maya.cmds` inside the Command Line is gone. Instead, before a script runs,
  its `import maya.cmds` line is rewritten in the visible Text to a plain import of the add-on's own `cmds` submodule.
  (see the 0.2.1 changelog)
- The one `sys.modules` lookup (Render Settings) is now a direct import. (see the 0.2.1 changelog)
- Covered by the same scan test.

### 3. "Modifying theme XML file is not allowed. ... Everything related to theme should be removed. You can recommend a theme in description on the website."

Removed completely: the theme files (`theme/*.xml`), the theme package, and every place that applied, backed up or
restored a theme. The add-on now draws with the user's current theme. (see the 0.2.1 changelog)

The description and the website have a "Recommended setup" section that suggests installing a dark grey theme of the
user's choice from *Get Extensions > Themes*, as you suggested. The scan test fails on theme XML files, a `theme`
package, `rna_xml` or any write to `preferences.themes`.

### 4. "Remove user_disabling. Add-on should uninstall normally without additional functions. Everything that is registered should be unregistered. No modifications should be made with add-on that requires additional steps to be unmade."

Done. `user_disabling` and the extra disable/remove handling are gone; disabling or removing the add-on is a plain
`unregister()`. We also removed every change that outlived the add-on, so there is nothing left to restore:

- **Application template**: the add-on no longer copies a layout template into the user's scripts folder. The Maya
  layout is appended as workspaces to the currently open file from the add-on's own bundled `.blend` (ordinary file
  data the user can delete or not save). (see the 0.2.1 changelog)
- **Preferences**: the add-on no longer writes any Blender preference (navigation, undo steps, region overlap, auto
  keying, UI scale, font, splash, ...) and never calls `save_userpref`. The only remaining `save_userpref` is the
  operator behind Maya's own *File > Save Preferences* menu item, which runs only when the user clicks it. The values
  Maya users usually want are listed in "Recommended setup" for users to set themselves. (see the 0.2.1 changelog)
- **Keymap**: the add-on no longer switches the active keyconfig. All Maya-style keys are add-on keymap items in
  `wm.keyconfigs.addon`, which are removed on unregister. While Maya mode is on, the active keyconfig's own items in the
  same keymaps are switched off **in memory only** (Blender does not save that state — measured by saving the preferences
  and restarting), and are switched back on when Maya mode is turned off or the add-on is disabled. (see the 0.2.1 changelog)
- **Snapshot / backup files** of preferences and theme are gone (nothing to back up). The only files written are the
  user's shelves in `extension_path_user` and Maya project folders the user creates.
- `unregister()` removes every class, keymap item, handler, timer, draw callback and msgbus subscription that
  `register()` added. A test installs the add-on into a clean config, turns Maya mode on, then disables and removes it,
  and compares the user preferences file, the keyconfig list, the active keyconfig, the config folder, handlers, timers
  and msgbus with the state before installing: `tests/test_step130_lifecycle.py` and `tests/test_step130_keymap_lifecycle.py` (see the 0.2.1 changelog).

### 5. "Remove all tags except User Interface."

Done: `tags = ["User Interface"]` in `blender_manifest.toml`. `blender --command extension validate` passes. (see the 0.2.1 changelog)

---

The listing description was updated to match (no theme, no preference changes, how scripts run, Recommended setup).
Thank you again — please let me know if anything else needs to change.
