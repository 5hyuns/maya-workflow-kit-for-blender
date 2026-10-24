# Step 152 lane B — default light, Test Resolution, Batch Render (#101)

Spec: research/maya/re/default_light_152.md (mayapy measurements; raw data in the lane worktree tmp/m152/).

## Done

- **Default light** (`operators/default_light.py`): Maya Software lights a scene without light nodes with a white
  directional light of intensity 1, camera space direction = view axis turned 25 deg up then 25 deg left, no
  shadows; any light node (hidden, ambient, outside defaultLightSet) turns it off. The kit adds a Sun `defaultLight`
  (strength pi = Maya intensity 1, `lights.power_factor`), parented to the render camera (local Euler XYZ -25 / -25 /
  0 deg), marked `allset_default_light`, for its own renders only, and removes object + data afterwards: EXEC right
  away, INVOKE from a 0.2 s timer once `is_job_running('RENDER')` is False. undo_post / redo_post / load_post remove
  stray marked lights. Kit Outliner, defaultLightSet rows and the Light Editor skip it.
- **Enable Default Light**: `Scene.allset_default_light` (default on, saved with the file), Render Settings > Common
  > Render Options (`ui/render_settings.py`).
- **Test Resolution** (`operators/render_batch.py`, `ALLSET_MT_test_resolution`): Maya's submenu labels and checks;
  choice = add-on preference `test_resolution` (Maya optionVar), applied to Render Current Frame / Render Sequence for
  the duration of the render (percentage x Blender's own scale; Camera Panel = the followed 3D View's size).
- **Batch Render / Cancel / Show**: copy of the open file (`save_as_mainfile(copy=True)`, persp camera + default light
  in it) in Blender's temp folder, `blender -b <copy> -o <out> -a` (`-f <current>` when the output name has no `#`),
  output = the scene's render path made absolute (project images folder while it is Blender's default; an untitled
  scene's `//` = the project's scenes folder). Cancel terminates the process; Show loads the newest image of the
  output into a new Image Editor window. Shelf "Batch Render" button runs it too.

## Decisions (delegated)

- The default light is only for kit renders (Render menu, shelf, Status Line, Render View button), not Blender's own
  `render.render`: `render_pre` of a UI render runs on the render job's thread, where adding / removing objects is
  unsafe [K], and Maya mode binds no F12 (IC renders on Ctrl+Alt+Enter only).
- Added to the scene for the render and parented to the camera (follows an animated camera in Render Sequence),
  rather than a permanent hidden light: no data is left in the file between renders.
- Test Resolution is a preference (Maya optionVar), applied temporarily: Render Settings and batch renders keep the
  Render Settings size, like Maya.
- Batch Render renders a copy, so the open file needs no save and keeps its unsaved state (Maya also renders a temp
  copy of the scene [K]).

## Verification

- `python tests/run.py -k step152_render,step137,step67,step105,step101,step54,enable_disable,step140,step103,step109,step130,step61`
  -> 162 passed, 0 failed, 19 files (step 147 / 99 files don't exist on this branch's base).
- `python tests/gui/run.py -k step137_render` -> 8 passed (INVOKE render: defaultLight present while the job ran,
  cube lit, none left afterwards).
- Brightness, fresh Maya Workflow Kit scene, same view as Maya: kit x 0.8 = 77.2 / 65.6 / 10.4 vs Maya 76.8 / 65.1 /
  10.0 (EEVEE, no world). Raw kit values are 1.25 x Maya's (lambert1 Diffuse 0.8 not carried, step 100); the
  template's grey world adds ~6.5 / 255.

## Left

- The kit lambert1 is 25 % brighter than Maya's under every light (Diffuse 0.8, step 100) and the template world adds
  ambient light Maya has no equivalent of — both outside this lane.
- Batch Render's option box (Maya batch options) and a GUI shot of the Render Options row are not done.
