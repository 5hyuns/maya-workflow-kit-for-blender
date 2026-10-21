# Step 131 — lane HYPER: Hypershade window in Maya's layout (#25)

Issue #25: the kit's Hypershade (step 67 / 105: one Shader Editor window with a "Hypershade" sidebar tab holding
Browser / Create / Property Editor) does not look like Maya 2022's Hypershade.

## 계획

### Maya reference (measured)

- Capture: `research/scripts/maya_hypershade131/` (launch.ps1 + userSetup.py + hypershade131.py, MAYA_APP_DIR in
  `tmp/maya_app_hyper131`, factory prefs). Scene: pSphere1 with blinn1 (file1 + place2dTexture1 on its Color), pCube1
  with lambert1. Windows > Rendering Editors > Hypershade opens at 1444 x 904; the script resizes it to 1440 x 900,
  grabs it (`hypershade_default_*.png`, `hypershade_graph_*.png` after "Input and Output Connections"), dumps tab bars,
  buttons with tooltips and item views into `_hypershade131.json`, quits. Spec: `research/maya/re/hypershade131.md`.
- Layout (window px, y down; splitters from pixel runs on `hypershade_graph_screen.png`):

  | panel | rect | share |
  |---|---|---|
  | menu bar File … Help | 0, 0, 1440 × 24 | full width |
  | Browser | 0, 24, 987 × 237 | 68.5 % wide, 27.1 % of the body tall |
  | Material Viewer | 987, 24, 453 × 383 | right column 31.5 %, 43.7 % of the body |
  | Create | 0, 261, 414 × 639 | 41.9 % of the left block |
  | Graph (node editor) | 414, 261, 573 × 639 | rest |
  | Property Editor | 987, 407, 453 × 493 | rest of the right column |

### Design

1. **One window, real areas.** `allset.hypershade` duplicates the largest area into a new window (as before) and
   then splits that window from a timer (one split per tick: area rects update one tick after a split, CLAUDE.md
   step 49), pointers looked up with `live_refs` each tick (#36). The splits come from the bpy-free
   `ui/hypershade_layout.py` (`plan` = Maya's shares, `simulate` = Blender's split rules, headless test):
   1. HORIZONTAL top strip one header high = **menu bar** (a Shader Editor whose header draws only the Maya
      Hypershade menus);
   2. VERTICAL right 31.5 % = right column → HORIZONTAL top 43.7 % = **Material Viewer**, rest **Property Editor**;
   3. HORIZONTAL top 27.1 % of the left block = **Browser**;
   4. VERTICAL left 41.9 % = **Create**; the remaining area = **Graph** (Shader Editor).
2. **Panes = Properties editors on the Tool tab** (step 106 / 116 mechanism: the Tool tab draws VIEW_3D "Tool"
   panels; one kit panel `ALLSET_PT_hypershade_pane` draws by pane). Marker in the hidden tab flags so it survives
   save / reload: Tool + `show_properties_world` + `show_properties_texture` (two maya_dock role flags, so
   `maya_dock.role` = None and `tool_dock.is_dock` = False) + one pane flag (`render` Browser, `output` Create,
   `view_layer` Material Viewer, `scene` Property Editor). `dock_tabs._hidden` also hides Blender's tool panels
   there. Header and navigation bar hidden (as `maya_dock.set_role`).
3. **Menu strip / Graph recognition.** A screen is a Hypershade when it has a pane; its Shader Editors = the strip
   (lowest one) and the Graph (tallest). `NODE_HT_header`'s own draw is swapped (`own_draw.swap`): strip = Maya
   menus only; Graph = Maya graph toolbar (`editor_chrome.ICONS["Hypershade"]`, Maya tooltips from the capture;
   buttons without a Blender counterpart greyed with a notice) + Blender's node menus folded in "Blender". The
   `draw_collapsible` override stays for other Shader Editors (step 105). A POST_PIXEL handler draws Maya's
   "Untitled_1" tab at the top-left of the Graph (node editors have no tool header region to hold a tab row).
4. **Panes' content.** Browser = Maya toolbar row (view as icons / list / swatch sizes / sort / reverse + search
   field), the 10 Maya tabs (Bake Sets / Projects / Asset Nodes greyed with a notice), swatch grid. Create =
   search field, category column (Favorites / Maya: Surface, Volumetric, Displacement, 2D Textures, 3D Textures,
   Env Textures, Other Textures, Lights, Utilities, Image Planes, Glow, Rendering) + Maya node list (Maya order from
   the capture; types Blender can build run `hs_create` / `hs_node` / `create`, others greyed), "Create | Bins"
   tabs at the bottom (Bins greyed). Material Viewer = renderer (scene engine) / shape (`preview_render_type`,
   Maya's Shader Ball = SHADERBALL) / environment (`use_preview_world`) row + `template_preview`. Property Editor =
   Maya's node tab + "blinn: [name] Presets" row + the AE material sections (as before).
5. **Current material across panes.** `show()` finds the Hypershade Graph of the window when called from a pane
   (it used `context.space_data`, which is now a Properties editor). Graph toolbar / View menu Frame All / Frame
   Selected run in the Graph area (`allset.hs_graph`), not in the strip they are clicked in.
6. **Opening again.** From inside the Hypershade (its Window menu) nothing new opens; from elsewhere an open
   Hypershade window is closed (timer) and a fresh one opened — Blender can't raise a window, Maya brings its
   Hypershade to the front (delegated).
7. **Removed:** the Shader Editor sidebar tab "Hypershade" (the panes replace it; one place like Maya) (delegated).

### Can't match (reasons)

- Window title: Blender titles every window with the file name (no Python API) — the layout is the recognition.
- Panels are areas, not dockable Maya panels: no per-panel title bar / float / close buttons (Blender areas can be
  resized, swapped, joined with Blender's own area gestures).
- Material Viewer renders with the scene's engine through Blender's material preview (EEVEE / Cycles; Workbench has
  no material preview); it is a preview image, not a tumbling viewport; Maya's "Interior1 Color" HDR choice =
  Blender's preview World toggle only.
- Graph tabs: Blender's node editor shows one material tree; "Untitled_1" is a drawn tab, "+" / more tabs don't exist.
- Create favourites / Bins, Arnold category: no Blender counterpart (greyed with a notice).

### Verification

- headless `tests/test_step131_hypershade.py`: `hypershade_layout` simulate == Maya rects; pane flags round trip;
  `draw_*` content (tabs incl. greyed ones, Create categories, viewer controls), current material from a pane.
- GUI `tests/gui/gui_step131_hypershade.py`: opens Windows > Rendering Editors > Hypershade, checks the new window's
  six areas, their roles and normalized rects vs Maya (`hypershade_layout.compare` ≤ 0.04), screenshot; side by side
  with the Maya capture in `tmp/hyper131/`.
- updated: test_step67_render, test_step105_maya_windows, gui_step67_render, gui_step105_windows,
  gui_step129_timers; test_enable_disable.

## 한 일

- Maya capture: `research/maya/screens/hypershade131/` (2 screen grabs + Qt grabs, `_hypershade131.json`), spec
  `research/maya/re/hypershade131.md`, scripts `research/scripts/maya_hypershade131/`. Maya started by launch.ps1
  quit by itself (`cmds.quit`). Note: this lane's worktree could not write into the main checkout, so the research
  files sit in the worktree's untracked `research/` (copy them to the main `research/` when merging).
- `src/allset/ui/hypershade_layout.py` (bpy-free): `MAYA_RECTS`, `shares`, `plan`, `simulate`, `compare`.
- `src/allset/ui/hypershade.py`: `allset.hypershade` opens a window and `build_later` splits it (pointers via
  live_refs, one split per 0.02 s tick, then pane types / markers); `pane` / `set_pane` / `is_hypershade` /
  `graph_area` / `menu_area`; `ALLSET_PT_hypershade_pane` (Browser toolbar + 10 tabs + filter, Create categories →
  Hypershade Create menu paths via `menu_sets.draw_item`, Material Viewer, Property Editor); `allset.hs_graph`
  (network selection in Python + node view / hide ops in the Graph); `NODE_HT_header` own draw swapped
  (`own_draw`); `draw_graph_tab` POST_PIXEL; the sidebar tab panels were removed (delegated, 「계획」 7).
- `editor_chrome.ICONS["Hypershade"]` (graph toolbar, Maya tooltips) + notices for the greyed buttons;
  `editor_menu_map`: View > Frame All / Frame Selected, Graph > Input / Output / Input and Output Connections →
  `allset.hs_graph`, Window > Material Viewer… → `allset.hypershade`.
- `dock_tabs._hidden` and `tool_settings.in_dock` leave Hypershade panes alone.
- Menu strip height (measured): an area shorter than its header collapses the header to 1 px and shows the main
  region, so the strip is `max(header, 26 × UI scale) + 3` px.

## 검증

- headless `python tests/run.py -k step131,step67,step105,step101,step104,enable_disable,step34,step116,step106,step114,step130`
  → 102 passed, 0 failed (14 files).
- GUI `python tests/gui/run.py -k step131` → 7 passed (proportions vs Maya within 0.6 % of the window, e.g.
  Browser 0.0058, Viewer 0.0053); `-k step67_render,step105_windows,step129_timers` → 30 passed;
  `ALLSET_SWEEP_ONLY=m67_ ... -k manual_sweep` → 24 passed.
- Side by side: `tmp/hyper131/hypershade_side_by_side.png` (Maya 1440 × 900 left, kit window 963 × 675 scaled right).

## Maya 와 다른 점 (이유)

- Window title stays Blender's (file name); panels have no Maya title-bar float / close buttons (Blender areas;
  the title row is a drawn label).
- Material Viewer = Blender's material preview image of the scene engine (EEVEE / Cycles), not a tumbling GL view;
  renderer is shown, not chosen (changing it would change the scene's engine); environment = preview World toggle;
  Blender's default shape is Sphere (Maya: Shader Ball — the shape menu has Shader Ball).
- Graph: one material tree, a drawn "Untitled_1" tab (no more tabs); Clear / Add / Remove selected, Rearrange,
  custom attribute view, attribute filter, restore tab are greyed with notices; grid icons and the filter field are
  not drawn (their tooltips weren't captured).
- Browser: Bake Sets / Projects / Asset Nodes tabs and Show greyed; at small window sizes the swatch name row scrolls
  below the area (the Browser is only 27 % of the window like Maya).
- Create: a category shows only its own list (Maya scrolls one long list); Displacement items and Bins greyed.
