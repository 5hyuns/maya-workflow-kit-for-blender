# Release notes 0.12.0 (GitHub release)

Text for the GitHub release of v0.12.0. Full list: the 0.12.0 section of `CHANGELOG.md`.

---

**0.12.0 — Universal Manipulator, Graph Editor tangent handles and sculpting brushes, editable motion trails, Stepped Preview, camera Overscan, and the fixes from your reports** (Blender 5.2 LTS)

Install it over 0.11.0 (or 0.8.0 – 0.10.0) as usual; shelves, hotkeys, scenes and the kit's settings are kept.
(Removing the kit before installing deletes them: use Export Settings first.)
Supported: Blender 5.2 LTS. Other versions are not tested: the extension still installs on Blender 5.0 and 5.1,
but they may have problems. For Blender 4.5 LTS keep using 0.6.2.

## New

- Universal Manipulator (Ctrl+T in Object Mode): a box around the selection with corner scale, edge rotate, centre
  move, and box lengths you can click and type (#318).
- Graph Editor tangent handles like Maya: in Maya mode a non-weighted tangent is drawn at a fixed length on screen
  and dragging it only turns it; a weighted tangent sits at its real end. A preference turns it off (#296).
- Graph Editor Sculpting Tools: Grab, Smooth, Smear and Key Reducer brushes; Curves > Clamp Curves and Offset
  Curves; List > Bookmarks.
- Keys > Remove Key in the Graph Editor and Dope Sheet: Unsnapped, Before / After Current Frame, Outside Selected
  Range and Ripple Delete.
- Motion trails: drag a key marker to move that key, or pick keys and move them with the Move manipulator.
- Playback: Looping Once / Oscillate, and Enable Stepped Preview (shows every curve stepped without changing the
  keys).
- Camera Overscan in the Attribute Editor: a view looking through the camera fits the camera's frame (#313).
- Camera and Aim rigs draw their aim line in the Maya layout views (#299).
- Tooltips the kit builds on hover follow the interface language and are in the translation template (#317).
- The Range Slider fills the timeline header (#319).

## Fixed

- Joints are no longer drawn far too large in a scene shown in metres: Radius and Joint Size are centimetres in
  every scene unit (#311, #320).
- A Radius typed in the Channel Box goes to every selected joint and redraws at once; Stick / Wire bone display
  draws lines (#320).
- Kit-drawn panels (Graph Editor list, Time Slider, Range Slider) follow the Blender theme (#312).
- Channel Box: a clicked channel shows its highlight at once (#316); the right-click menu opens left of the Channel
  Box (#315).
- Your own translation file now wins over Blender's translation in the kit's menus, shelf and Channel Box (#317).
- Graph Editor tangent buttons without the Maya icon row show the kit's tangent pictures (#319).
- Delete Keys / Cut Keys windows delete exactly the selected keys.

## Changed

- Bevel: a tip where two bevelled edges meet, a corner of three bevelled edges whose angles differ a lot, and an
  acute corner in Fraction mode come closer to Maya's shape. The three-edge corner is an approximation and still
  differs from Maya (#213).

## Known differences

- Universal Manipulator: the rotate speed and the point that stays fixed when you type a length may feel a little
  different from Maya. In component modes Ctrl+T stays Blender's Transform tool.
- The known differences listed in `CHANGELOG.md` still apply.

## Thank you

Thanks for the reports and ideas: @meggaimg70-a11y (#296), @DAI3rd (#299, #315, #316, #317), @pixelkeyblade18
(#311), @Scorpy-laz (#312, #313), @psokk (#318), @swarnava05 (#319) and @AlEuf01 (#320). Please keep telling us what
breaks or feels off in real work.

Maya Workflow Kit is a free, personal open-source project: no paid version, no donations requested, and no commercial
goal behind it.

Autodesk and Maya are registered trademarks or trademarks of Autodesk, Inc. This extension is not affiliated with or
endorsed by Autodesk, Inc.
