# Step 129 — viewport lane (#8, #9, #10, #13, #24)

## 계획

- #10 panel toolbar: Maya 2022's buttons and their behaviour come from `createModelPanelBar.mel` (which button is an
  `iconTextCheckBox` toggle, which an `iconTextButton` command; also `checkable` in
  `research/maya/screens/top113/_top113.json`) and `updateModelPanelBar.mel` (callbacks). Every toggle must turn off
  on a second click, every command must act, the rest is greyed with a notice.
  - Wireframe / Smooth Shade All / Use All Lights were radio items (the Shading / Lighting menu kind): a second
    click set the same mode again. Maya's toolbar callbacks: Wireframe off = smoothShaded, Smooth Shade All off =
    wireframe, Use All Lights off = default lights. `panel_set(toggle=True)` maps the "off" click through
    `panel_menus.TOGGLE_OFF`; the menus stay radio lists.
  - Lock Camera was bound to Blender's `lock_camera` (Lock Camera to View) — the opposite meaning. Maya's
    `changeCameraLockStatus` locks the camera so navigation can't move it: the kit locks the looked-through camera's
    location / rotation channels. Measured (GUI probe): with `lock_camera` on, Blender's camera-view navigation keeps
    locked channels (0.0 movement), moves an unlocked camera (0.90) and, without `lock_camera`, leaves the camera
    view (PERSP).
  - Camera buttons act on the camera the view looks through and are disabled in Blender's persp / ortho views (no
    camera object; Maya disables Lock Camera there too, `updateCameraGroup`).
- #9: F / A / Shift+F in a camera view called Blender's `view_selected`, which leaves the camera view. Now
  `operators/view.frame_camera` moves the camera with Maya's fit (0.95 of the camera frame at the render resolution,
  orientation kept; ortho cameras change `ortho_scale`; a locked camera stays). Tumbling a camera view moves the
  camera: the kit turns on the view's Lock Camera to View when it enters a camera view (Panels > Perspective /
  Orthographic camera, Look Through Selected) and before Alt+LMB tumble.
- #8: Blender's quad view is already Maya's layout (measured: top-left top, top-right persp, bottom-left front,
  bottom-right side). The bug: a Space tap over the top panel leaves a single *top* view and Single Perspective did
  nothing (already single). `view.ensure_persp` turns an ortho single view (or the four view's persp panel) back
  into the area's last persp view (shared with the hotbox's persp memory, else Maya's Home persp);
  `toggle_quad_view` remembers the persp panel before leaving the four view.
- #13: the UV Editor checker button / Textures > Checker Map assigned a new checker material on every click. Now
  `allset.checker_toggle`: object-level material slots (`link = 'OBJECT'`, the mesh's materials untouched) with a
  checker material, the previous slot state in the object property `allset_checker_prev`; a second click puts it
  back. The button is drawn pressed while any object shows the checker (Maya `textureWindowDisplayCheckered`).
  UV > Assign Checker Shader stays a real assignment.
- #24: `allset.ipr_toggle` (and Renderer > Viewport 2.0) restore the shading the view had before Rendered
  (`panel_menus.enter_rendered` / `leave_rendered`, per space).

## 결과 — panel toolbar, every button clicked twice (GUI, `tests/gui/gui_step129_panel_toolbar.py`)

Viewport looking through camera1 with pCube1 selected; simulated clicks on the drawn buttons.

| Button | Maya kind | Blender target | 1st click | 2nd click |
|---|---|---|---|---|
| Select Camera | command | select the looked-through camera | pCube1 → camera1 selected | no change (command) |
| Lock Camera | toggle | camera lock_location / lock_rotation | locked | unlocked (start) |
| Camera Attributes | command | greyed (notice) | — | — |
| Bookmarks | command | greyed | — | — |
| Image Plane | command | `allset.create(IMAGE_PLANE)` | imagePlane1 | imagePlane2 (Maya toggles an existing plane's display — not done) |
| 2D Pan/Zoom | toggle | greyed | — | — |
| Grease Pencil | command | Annotate tool | tool → annotate | no change |
| Grid | toggle | Maya grid (`maya_grid.toggle`) | off | on (start) |
| Film Gate | toggle | camera `show_sensor` | on | off |
| Resolution Gate | toggle | greyed (Blender's camera frame is always the resolution gate) | — | — |
| Gate Mask | toggle | camera `show_passepartout` | off | on |
| Field Chart | toggle | greyed | — | — |
| Safe Action | toggle | camera `show_safe_areas` (Blender draws action + title together) | on | off |
| Safe Title | toggle | camera `show_safe_areas` | on | off |
| Wireframe | toggle | shading WIREFRAME / off = SOLID | WIREFRAME | SOLID |
| Smooth Shade All | toggle | shading SOLID / off = WIREFRAME | WIREFRAME | SOLID |
| Use Default Material | toggle | color_type SINGLE | SINGLE | MATERIAL |
| Wireframe on Shaded | toggle | overlay show_wireframes | on | off |
| Textured | toggle | color_type TEXTURE | TEXTURE | MATERIAL |
| Use All Lights | toggle | Material Preview + scene lights / off = Solid studio | MATERIAL | SOLID |
| Shadows | toggle | shading show_shadows | on | off |
| SSAO | toggle | shading show_cavity | on | off |
| Motion Blur | toggle | greyed | — | — |
| Multisample AA | toggle | greyed (Blender: a preference) | — | — |
| Depth of Field | toggle | shading use_dof | on | off |
| Isolate Select | toggle | local view (state = `space.local_view`) | isolated | back |
| X-Ray | toggle | shading show_xray | on | off |
| X-Ray Active Components | toggle | greyed | — | — |
| X-Ray Joints | toggle | overlay show_xray_bone | on | off |
| Exposure icon | command | exposure 0 ↔ last value | 1.0 → 0 | 1.0 |
| Gamma icon | command | gamma 1 ↔ last value | 1.4 → 1 | 1.4 |
| Colour management | toggle | view transform ↔ Raw | AgX → Raw | AgX |

33/33 GUI checks pass (before: Select Camera / Grid reported no change, Wireframe / Smooth Shade All / Use All
Lights didn't come back — tests/gui/audit128/gui_toggle_roundtrip.py; Grid was a probe artefact: it tracked
`show_floor`, not the Maya grid).

## 검증

- headless `tests/test_step129_viewport.py` (7): toolbar round trips, Maya toggle off states, camera buttons need a
  camera view, Select Camera, IPR from Wireframe / Material / Solid, F in a camera view (0.95 fill, centred,
  orientation kept, locked camera stays), UV checker on / off.
- GUI `gui_step129_panel_toolbar.py` (33), `gui_step129_views.py` (12): four view panels, Space tap → top →
  Single Perspective = persp with the same rotation, Four View from a single top view, F in camera1's view (camera
  view kept, box centred), Alt+LMB moves camera1, locked camera doesn't move (tumble and F), IPR from Wireframe,
  UV checker button off → on → off.
- Regression GUI: step17, step37, step113, step104 (31 pass). Full headless suite: see the commit.

## 남은 것

- Image Plane button creates a free image plane each click (Maya: imports one for the camera, then toggles its
  display); Camera Attributes / Bookmarks / 2D Pan/Zoom / Resolution Gate / Field Chart / Motion Blur / MSAA /
  X-Ray Active Components stay greyed.
- Shadows / SSAO act on Solid shading only (Blender's Material Preview has no per-view switch).
- F in a camera view fits the render frame (Maya fits the panel with the camera's fit / overscan) [delegated].
