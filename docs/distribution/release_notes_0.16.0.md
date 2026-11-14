# Release notes 0.16.0 (GitHub release)

Text for the GitHub release of v0.16.0. Full list: the 0.16.0 section of `CHANGELOG.md`.

---

**0.16.0 — A much faster Maya mode in big and rigged scenes, display layers that hold joints, Duplicate on joints, a ViewCube you can drag, Blue Pencil on the Time Slider, and the fixes from your reports** (Blender 5.2 LTS)

Install it over 0.15.0 (or 0.8.0 – 0.14.0) as usual; shelves, hotkeys, scenes and the kit's settings are kept.
(Removing the kit before installing deletes them: use Export Settings first.)
Supported: Blender 5.2 LTS. Other versions are not tested: the extension still installs on Blender 5.0 and 5.1,
but they may have problems. For Blender 4.5 LTS keep using 0.6.2.
Blender 5.3 is not supported yet.

## Faster in big and rigged scenes

This release is mostly about speed. With rigged characters or thousands of objects, Maya mode used to redo a lot of
work on every click, drag and frame, and you could feel it: playback fell behind Blender mode, clicks on joints
hesitated and big Outliners stuttered. That work is now done once and kept, or skipped when nothing changed. What you
see and what gets picked stay the same.

- **Playback and scrubbing with rigs.** Before, every rig control's shape was built again on every frame, so rigged
  characters played clearly slower in Maya mode than in Blender mode, most of all with the armatures shown. Now the
  controls, B-Bone and Envelope joints are drawn all at once, only the rigs whose pose changed are drawn again, and the
  four-view layout shares one build of the joints between its views. Playback with the armatures shown is much closer
  to Blender mode, and scrubbing the Time Slider keeps up better (#344).
- **Clicking joints.** Before, a click on a joint in a big rig could hold for a moment while the kit switched modes
  several times and looked through the whole scene. Now a click goes into Pose Mode in one go, updates the scene fewer
  times and checks only what a click can change, so picking joints and controls answers much faster.
- **Box selection over joints.** Before, letting go of a box could show Blender's own box result for a frame or two
  (the meshes picked, the joints dropped) before the final selection, a quick box over rig controls could end with only
  some of them, and a box over thousands of objects took a while to settle. Now the first frame after letting go
  already shows the final selection, a quick box picks the same joints as a slow one, and a box in a big scene settles
  much sooner.
- **Posing.** Before, dragging a rig control made the Channel Box, the Status Line, the Time Slider and every skeleton
  redo their work on each mouse step, so posing felt sluggish. Now a drag keeps what doesn't change, only the moved
  part of the rig (a hand, a foot, a finger) is drawn again, and other characters keep their joint lines. The Channel
  Box still shows the live values while you drag.
- **Many selected objects.** Before, with hundreds of objects selected, orbiting and playback slowed down, and with
  nearly every object of a big scene selected a single redraw could take seconds. Now the selection wireframe stays
  light even with thousands of objects selected, and Delete, Export Selection and Isolate on many objects are quicker
  too.
- **The Outliner in big scenes.** Before, the Maya Outliner of a scene with thousands of objects was slow to rebuild
  after a load, an undo or a rename, stuttered while you scrolled or moved the mouse over the rows, and piled up old
  rows during a long session. Now it rebuilds faster, scrolls smoothly and no longer piles up old rows, so long
  sessions in big scenes have fewer small pauses.
- **Graph Editor and Channel Box.** Before, with a keyed rig selected the Graph Editor redrew slowly, and panning or
  zooming many curves felt heavy. Now keys and tangents are read once per redraw, and a pan moves the drawing instead
  of building it again. The Channel Box stays quick with many picked joints, with controls that have many
  custom attributes and with long animation curves.
- **Edit Mode on big meshes.** Clicks and box selections stay quick with Maya's component colours: only the selection
  is read again, not the whole mesh.
- **Everyday UI.** The Time Slider, the Range Slider, the top bar, the Status Line, the shelf, the dock, the ViewCube
  and the marking menus do less on every redraw, and dragging the time to the left of frame 0 no longer updates the
  whole scene on every mouse move.

## New

- Display layers hold joints, like Maya: Create Layer from Selected and Add / Remove Selected Objects take a picked
  joint itself instead of the whole skeleton. Hiding the layer hides that joint and everything below it (the joints and
  the objects parented under them); Template draws them grey and Reference black, and neither can be picked in the
  view. Layers saved with earlier versions keep working (#355).
- A joint's Visibility off hides the joints and objects below it, like Maya, without changing their own Visibility
  (#355).
- Duplicate on joints, like Maya: Ctrl+D copies the picked joints with the joints below them, in place; Shift+D
  (Duplicate with Transform), Duplicate Special and Shift+drag on the manipulator copy picked joints too; a joint
  duplicated while posed keeps its pose. Duplicate Special's note about joint copies shows in the Command Line.
- Dragging the ViewCube tumbles the view like Alt+LMB, and when you look through a camera it turns the camera; a click
  still goes to that view (#357).
- Blue Pencil: drawn frames show as light blue marks on the Time Slider, Alt+< / Alt+> jump to the previous / next
  drawn frame, Ghost Previous / Ghost Next show the nearest drawings, and Tool Settings has Pencil, Line and Eraser
  (#357).
- Modify > Center Pivot works in component mode, like Maya: each edited object's pivot goes to the centre of its
  selected components and you are back in object mode (#356).
- Attribute Editor: Blender Modifiers... opens the object's whole Blender modifier stack in a floating window, Add
  Modifier included (#358).
- Maya Outliner: Display > Blender Collections shows the scene's collections, and Maya Outliner in that header goes
  back. The README FAQ explains how groups, collections and modifiers fit the Maya interface (#358, #359).

## Changed

- A new group (Ctrl+G) goes into the collection its members share (or the active collection), no longer into a set
  or display layer collection (#359).
- A display layer's Template and Reference reach every object below a member, as its visibility already did, and
  Select Objects picks every member, Template, Reference and hidden ones included.

## Fixed

- Four view: a panel that looks through a camera keeps that camera, with its zoom and offset, when Space switches
  between the four views and one view, and a new panel no longer takes over another panel's camera (#362).
- UV Editor: selected edges on a shell border show in the selection colour on top of the Texture Borders line (#361).

## Known differences

- Panels > Layouts > Single Perspective View keeps the camera the perspective panel looks through; Maya goes back to
  the persp camera.
- Blue Pencil frames can't be moved on the Time Slider yet (Shift+drag in Maya).
- In very big rigged scenes Maya mode still does more work than Blender mode: scrubbing, box selection over joints
  and moving or posing a rig stay heavier there.
- Scrubbing a very big scene is slower while a second Blender window (such as a floating editor) is open; close it
  when scrubbing feels heavy.
- The known differences listed in `CHANGELOG.md` still apply.

## Thank you

Thanks to @pixelkeyblade18 for the playback report and the follow-up details (#344), and for the reports and
questions: @flexioothe1 (#355), @jadelion-creator (#361), @talalbardouka-crypto (#362), and @andych56, @deuksooseo-ctrl,
@KRO1903 and @olivier899, whose questions in Discussions became #356 – #359.
Please keep telling us what breaks or feels off in real work.

Maya Workflow Kit is a free, personal open-source project: no paid version, no donations requested, and no commercial
goal behind it.
