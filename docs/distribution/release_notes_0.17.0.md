# Release notes 0.17.0 (GitHub release)

Text for the GitHub release of v0.17.0. Full list: the 0.17.0 section of `CHANGELOG.md`.

---

**0.17.0 — Blender 5.3 support and a big set of Maya behaviours from a contributor: an Outliner that pans and searches like Maya, Chamfer off that keeps the shape, camera gates and Field Chart, G that repeats modal tools, and more** (Blender 5.2 LTS and 5.3)

Hello everyone, and thank you. The kit now supports Blender 5.3 as well as 5.2 LTS, and every test and release
check runs on both. Many of the changes in this release come from @AlexBarbulescu, who sent them as pull requests
(#366, #372): we brought his work into the kit with him credited as co-author of those commits. The full thanks are
at the end of these notes.

Install it over 0.16.0 (or 0.8.0 – 0.15.0) as usual; shelves, hotkeys, scenes and the kit's settings are kept.
(Removing the kit before installing deletes them: use Export Settings first.)
Supported: Blender 5.2 LTS and 5.3. Other versions are not tested: the extension still installs on Blender 5.0 and
5.1, but they may have problems. For Blender 4.5 LTS keep using 0.6.2. Versions after 5.3 are not offered the
extension until they are tested.

## Blender 5.3

- The kit installs and runs on Blender 5.3: the Industry Compatible keymap data of 5.3, its Outliner sorting, its
  new Properties tab and the renamed text size are handled, and the Maya keys keep winning over 5.3's new Weight /
  Vertex Paint Alt+A pie and Grease Pencil Draw Ctrl+M / G (#360).
- Paint Skin Weights on 5.3 draws its brush panels, starts with a brush that sets the value, and its Value / Opacity
  follow the brush's shared settings; shelf tab text uses a readable colour on light themes; the Range Slider's
  Keying item opens the whole Keyframing popover.
- Help links open the Blender 5.3 manual, API and release notes on Blender 5.3 (the 5.2 pages on 5.2).
- In the Graph Editor, Blender 5.3 shows Translate curves in the scene's unit (centimetres in a Maya scene): the kit's
  keys, tangents, key drags, Scale Keys box and Sculpting Tools follow it.

## From @AlexBarbulescu's pull requests (#366, #372)

- Maya Outliner: Alt+middle-drag pans the rows both ways, so a deep joint chain can be seen (#365); the search field
  is a row under the menu bar, like Maya; right-click > Set Active Camera on a camera row.
- Bevel with Chamfer off keeps the original surface: the support edges stay on the original faces, the corners stay
  and the volume is unchanged (#368); like Maya, the step count is even.
- Center Pivot centres on the object's own geometry and all its children, like Maya.
- Panel toolbar: Resolution Gate and Film Gate, one at a time like Maya (turning a gate on also adds overscan around
  it, like Maya; the render size is written above the resolution gate), Field Chart, and Safe Action / Safe Title as
  separate toggles.
- G repeats a modal command started from a shelf, menu or marking menu (Knife: a fresh cut each time).
- Shift+double-click a vertex or face on another piece adds that piece's shell.
- Shelf: right-click a button for Open / Edit / Delete.
- File dialog: a folder pasted into the file name field opens that folder.
- With Show > Locators off, a selected group still shows its Move / Rotate / Scale manipulators and its contents'
  selection wire.
- Switching to Maya mode shows the Maya layout ready before its first frame (sizes, Outliner, icons, Time Slider)
  instead of settling over the first second.
- Fixed: Alt+RMB dolly no longer jumps the wrong way when the cursor wraps at the edge of the view or a pen tablet
  jumps; a window reopened at its remembered place no longer resizes the Outliner or the dock; the ViewCube's face
  names lie on their faces; in the right dock's tab stack a section header no longer takes the click meant for the
  tab beside it; Auto-Save Preferences keeps the option window values you saved.
- The grid stays behind meshes in Material Preview and EEVEE Rendered, like Maya, instead of showing through their
  seams.
- New preferences, all off by default because Maya has none of these: Blender's shading controls in the panel
  toolbar, camera / projection buttons under the ViewCube, a Material Preview HDRI, Blender's selectable / eye /
  render columns in the Maya Outliner, Tool Settings as a tab of the right dock, panel display settings kept across
  sessions, and Eevee / Cycles items in the panel Renderer menu.

## Also in this version

- Faster scene updates: the kit's update handlers share one pass over each update.
- The Channel Box and the kit's other watchers keep updating after File > Open and File > New.

## Known differences

- The known differences listed in `CHANGELOG.md` still apply.

## Thank you

Thanks to @AlexBarbulescu for the Blender 5.3 support and the many fixes and Maya behaviours in #366 and #372 (and
#364 before them): a large part of this release is his work. Thanks also to @tristratos for asking for Blender 5.3 (#360),
and to @cluckn0rris-ch (#365) and @invaderzod (#368) for the reports his changes answer.
Please keep telling us what breaks or feels off in real work.

Maya Workflow Kit is a free, personal open-source project: no paid version, no donations requested, and no commercial
goal behind it.
