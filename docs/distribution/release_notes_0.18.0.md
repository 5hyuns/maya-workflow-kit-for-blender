# Release notes 0.18.0 (GitHub release)

Text for the GitHub release of v0.18.0. Full list: the 0.18.0 section of `CHANGELOG.md`.

---

**0.18.0 — Fixes for your reports: Extrude, Bend, the Hotkey Editor, the Time Slider and the four view; Maya's Distance Tool, sets that hold components and Channel Box multi-value typing; and a long list of Maya menu items from contributor @AlexBarbulescu** (Blender 5.2 LTS and 5.3)

Hello everyone, and thank you for the reports. This release fixes the issues opened since 0.17.0 and two older ones
we checked again (#292, #334), and makes playback in Maya mode lighter again (#344). @AlexBarbulescu sent another
big pull request (#376), and we brought it into the kit with him credited as co-author of those commits; a few parts
were changed to match Maya or became options that are off by default, and the reasons are in #376. Thank you, Alex!

Install it over 0.17.0 (or 0.8.0 – 0.16.0) as usual; shelves, hotkeys, scenes and the kit's settings are kept.
(Removing the kit before installing deletes them: use Export Settings first.)
Supported: Blender 5.2 LTS and 5.3. Other versions are not tested: the extension still installs on Blender 5.0 and
5.1, but they may have problems. For Blender 4.5 LTS keep using 0.6.2. Versions after 5.3 are not offered the
extension until they are tested.

## Fixed and new from your reports

- **Extrude (#377, #378):** extruding every face of a mesh (a plane with divisions, or Edit Mesh > Extrude on the
  object) keeps the old faces as the bottom, like Maya, so a plane becomes a closed slab and Thickness on an open
  shell (a tube, a box without a lid) gives a wall with both sides. No edges or vertices are left behind without
  faces any more.
- **A click after an extrusion (#380):** on Blender 5.3, after you changed an extrusion with its manipulator, a
  click on a face, edge or vertex selected nothing until you switched the component mode. A click selects again.
- **Nonlinear Bend (#379):** works like Maya's. Curvature is in degrees (180 rolls a plane into a full cylinder), the
  handle draws Maya's lines so you can see which way it bends, and a flat object bends instead of spinning. The
  Channel Box and the Attribute Editor show Envelope, Curvature, Low Bound and High Bound, and a bend on a lattice,
  curve or surface follows its handle too.
- **Hotkey Editor (#381):** like Maya, when you give a command a key that other kit commands use, the editor warns
  you (Return assigns, Esc cancels) and takes the key from them, so the new key works in the viewport right away.
  A command with two Maya hotkeys shows "Undo" and "Undo (2nd hotkey)", each changing only its own key, and the
  last tool (NonSacredTool) is one row for Object Mode and mesh Edit Mode.
- **Hotkeys you change stay (#363):** your changes to the kit's keys stay after switching Maya → Blender → Maya and
  after a restart in Blender mode; a Blender key changed in Blender mode stays changed too.
- **Distance Tool (#370):** Create > Measure Tools > Distance Tool works like Maya's: click two points and you get
  locator1, locator2 and distanceDimension1 in the Outliner, with the distance drawn in the view in the scene's Maya
  units. The number follows when you move a locator; X / C / V snap, a click on a locator measures from it, and
  deleting a locator deletes its dimension.
- **Sets with components (#373):** Create > Sets > Set and Quick Select Set hold vertices, edges and faces, like
  Maya. Selecting the set picks them again in the matching component mode, and the Outliner lists them by their
  Maya names (`pCube1.vtx[0:3]`).
- **Channel Box multi-value typing (#375):** drag down over the values, type a number and press Enter, and it goes
  into every selected channel of every selected object. The selected value cells are blue, and the editor shows
  the last value ready to be replaced: Enter writes it into all of them (on every OS), a click away writes only a
  value you changed, and Esc writes nothing.
- **Tool Settings in the four view (#367):** a double-click on a tool opens the Tool Settings as a floating window
  at the top left of the viewport, like Maya, and never inside one of the four panels; Space over a panel works
  with the window open or torn off, and switching to Blender closes it. The kit's other windows and docked panels
  never split a panel of the four view either, and the four view keeps its panel sizes to the pixel.
- **Delete History on a deformer (#369):** like Maya, the deformer goes together with its handle, its weights and
  the keys that drove it, so no keys are left behind; the mesh keeps the shape of the current frame. Like Maya, the
  Time Slider shows a deformer's keys (and a blendShape's weight keys) only for that node, so . and , and the Time
  Slider edits leave them alone when the mesh or the handle is selected.
- **Camera view dolly (#371):** Alt+RMB in a view that looks through a camera, or through a light with Look Through
  Selected, dollies with a left / right drag too, like in the perspective view.
- **F in a camera view (#374):** looking through a camera, F fills the whole view like Maya, also the room around a
  shown Resolution or Film Gate, instead of fitting the selection to the camera's frame.
- **Playback (#344):** while playing, only the viewports and the Time Slider are redrawn (no longer the Tool Box
  column and the shelf), the ViewCube and the Range Slider do less on each frame, and in the four view only the
  panel the mouse was last in is redrawn, like Maya's Playback > Update View: Active (Windows >
  Settings/Preferences > Preferences > Time Slider > Playback, or All for all four).
- **Time Slider numbers (#292):** the mouse wheel, a trackpad and the zoom keys no longer zoom or scroll the Time
  Slider, like Maya, so its numbers don't jump any more; the numbers also fit when the display scaling is turned
  up.
- **Dragging a window to another monitor (#334):** the kit no longer moves the mouse pointer while a window is
  dragged or resized, which could make the window jump on Windows.

## From @AlexBarbulescu's pull request (#376)

- Maya menu items that now work: Display > Hide / Show submenus with the by-type items, Visualize > Time Slider
  Bookmarks, Mesh > Booleans Slice / Hole Punch / Cut Out / Split Edges (also in the Shift+RMB marking menu),
  Set Range to > Sound Length, Heads Up Display > Current Frame / Focal Length / Scene Timecode and In-view
  Messages, Display > Animation > Joint Labels, Display > Show > All Components, Mesh > Clipboard Actions,
  Edit > Transfer Attribute Values, Edit > LOD, Modify > Convert > Displacement to Polygons and the Interactive
  Grooming Tools brushes.
- Outliner: Ctrl+D duplicates the selection (groups with their children), like Maya.
- Duplicate, Freeze Transformations and Delete History include a selected group that Show > Locators hides.
- The Channel Box typing above (#375).
- Changed to match Maya: HUD Focal Length reads like Maya's cameras; All Components works on every mesh; LOD
  selects the group it makes; Displacement to Polygons also copies a mesh without displacement, with a warning.
- New preferences, off by default because Maya has neither: Mark Instances in the Outliner (purple rows and a
  badge) and Freeze / Delete History Unshare Instances. By default, like Maya, Freeze leaves an instance as it is
  with a warning, and Delete History works on the shared mesh.

## Also in this version

- Extrude's Local Translate Z moves a vertex inside the extruded faces along its own normal, like Maya.
- Freeze Transformations on a group gives Maya's values: the group reads 0 / 0 / 1, each child's pivot is its
  place in the group's frame, cameras and lights inside are not frozen, and Reset Transformations, Unparent, Center
  Pivot and a pivot moved with D read like Maya afterwards. Nothing moves in the view.
- On Blender 5.x the Time Slider stays tall enough for its numbers at a UI scale above 1.0, and a narrow window
  keeps every Time Slider button in view.
- Graph Editor and Dope Sheet windows opened small start at frame 1.
- Blender 5.3: Weight Paint in Maya mode opens without 5.3's brush shelf under the views, like Maya's Paint Skin
  Weights.
- A tab stack the kit makes opens at the width its tab needs, so the Attribute Editor opened on Blender's own
  screen is no longer a narrow column, and Ctrl+A resizes it.
- Every string of the kit has a Japanese and Chinese translation.

## Known differences

- Sets hold mesh components; curve CVs and lattice points can't be put in a set yet.
- A bend on a lattice or a surface has no Envelope yet.
- Scrubbing the Time Slider still redraws every panel of the four view (Update View: Active applies while playing).
- The known differences listed in `CHANGELOG.md` still apply.

## Thank you

Thanks to everyone who reported these: @GUYVERZERO (#377, #379), @invaderzod (#378), @envwarby (#380, #381),
@whitethorn02-bit (#363), @XeonG (#367), @Fizkefaaz (#369, #370, #371), @talalbardouka-crypto (#373),
@polynaught (#375), @pixelkeyblade18 (#344), @skybluerob (#374), @lima-studio-creator (#292) and @GIBBETGAMES
(#334). Your clear steps, pictures and videos made each of them quick to find. And thanks again to
@AlexBarbulescu, for #376 and for his comment on #374 that led to the camera view F fix.
Please keep telling us what breaks or feels off in real work.

Maya Workflow Kit is a free, personal open-source project: no paid version, no donations requested, and no commercial
goal behind it.
